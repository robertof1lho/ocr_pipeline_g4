import cv2
import numpy as np

from ocr_pipeline.config import MIN_IMAGE_QUALITY


def preprocess(image_path: str) -> dict:
    """
    Full preprocessing pipeline for a document image file.

    Returns dict with keys:
        processed     - binarized, deskewed grayscale image (np.ndarray)
        inverted      - inverted version (white text on black)
        bgr           - BGR version of processed (for EAST detector)
        quality_score - float in [0, 1]

    Raises ValueError with code IMAGE_NOT_FOUND or IMAGE_QUALITY_TOO_LOW.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"IMAGE_NOT_FOUND: {image_path}")
    return _pipeline(img)


def preprocess_array(image: np.ndarray) -> dict:
    """Same pipeline accepting a numpy array (BGR or grayscale)."""
    if image is None or image.size == 0:
        raise ValueError("IMAGE_NOT_FOUND: empty array")
    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return _pipeline(image)


def _pipeline(img: np.ndarray) -> dict:
    # Scale up small images to at least 1500px on the longest side (~300 DPI equivalent)
    h, w = img.shape[:2]
    if max(h, w) < 1500:
        scale = 1500 / max(h, w)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)

    # Coarse threshold before adaptive pass
    _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)

    # Adaptive threshold handles uneven illumination across the document
    adaptive = cv2.adaptiveThreshold(
        thresh, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 1
    )

    # Otsu on top of adaptive smooths out remaining noise
    blur = cv2.GaussianBlur(adaptive, (1, 1), 2)
    _, otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Morphological cleanup: dilate fills tiny gaps, erode removes isolated specks
    dilated = cv2.dilate(otsu, np.ones((1, 1), np.uint8))
    processed = cv2.erode(dilated, np.ones((2, 2), np.uint8))

    processed = _deskew(processed)

    quality = _quality_score(processed)
    if quality < MIN_IMAGE_QUALITY:
        raise ValueError("IMAGE_QUALITY_TOO_LOW")

    return {
        "processed": processed,
        "inverted": 255 - processed,
        "bgr": cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR),
        "quality_score": quality,
    }


def _quality_score(gray_image: np.ndarray) -> float:
    """Laplacian variance as sharpness proxy, normalized to [0, 1]."""
    lap_var = cv2.Laplacian(gray_image, cv2.CV_64F).var()
    return float(min(lap_var / 500.0, 1.0))


def _deskew(image: np.ndarray) -> np.ndarray:
    """Correct slight rotation using minAreaRect on foreground (dark) pixels."""
    coords = np.column_stack(np.where(image < 128))
    if len(coords) < 100:
        return image

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Skip sub-pixel corrections to avoid unnecessary interpolation degradation
    if abs(angle) < 0.5:
        return image

    h, w = image.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
