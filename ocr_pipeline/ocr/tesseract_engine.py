import os

import cv2
import numpy as np
import pytesseract
from imutils.object_detection import non_max_suppression

from ocr_pipeline.config import TESSERACT_CMD, EAST_MODEL_PATH


class TesseractEngine:
    """
    Wrapper around pytesseract with optional EAST-based region detection.

    Primary methods:
        extract_text(image, psm)           -> raw string
        extract_with_positions(image, psm) -> per-word bounding boxes + confidence

    Optional (requires frozen_east_text_detection.pb):
        detect_text_regions(image)         -> list of region dicts {x, y, w, h}
    """

    _LAYER_NAMES = ["feature_fusion/Conv_7/Sigmoid", "feature_fusion/concat_3"]
    _EAST_SIZE = 320  # EAST input must be a multiple of 32

    def __init__(self) -> None:
        if TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
        self._east_net = None

    # ── Public API ────────────────────────────────────────────────────────────

    def extract_text(self, image: np.ndarray, psm: int = 6) -> str:
        """Return raw OCR text. PSM 6 = single uniform block; PSM 3 = auto layout."""
        return pytesseract.image_to_string(image, lang="por", config=self._cfg(psm))

    def extract_with_positions(self, image: np.ndarray, psm: int = 6) -> list[dict]:
        """
        Return list of recognized words with bounding boxes and per-word confidence.

        Each dict: {text, confidence, x, y, w, h}
        confidence is in [0, 100]; words with conf <= 0 are discarded.
        """
        data = pytesseract.image_to_data(
            image, lang="por", config=self._cfg(psm), output_type=pytesseract.Output.DICT
        )
        results = []
        for i, word in enumerate(data["text"]):
            conf = int(data["conf"][i])
            if word.strip() and conf > 0:
                results.append({
                    "text": word,
                    "confidence": conf,
                    "x": data["left"][i],
                    "y": data["top"][i],
                    "w": data["width"][i],
                    "h": data["height"][i],
                })
        return results

    def detect_text_regions(
        self,
        image: np.ndarray,
        min_confidence: float = 0.5,
        merge_threshold: int = 150,
    ) -> list[dict]:
        """
        Use EAST model to locate text regions, merge nearby ones into clusters.

        Falls back to a single full-image region when the .pb model file is absent.
        Each region dict: {x, y, w, h} in original image coordinates.
        """
        if not self._load_east():
            h, w = image.shape[:2]
            return [{"x": 0, "y": 0, "w": w, "h": h}]

        H, W = image.shape[:2]
        size = self._EAST_SIZE

        img_resized = cv2.resize(image, (size, size))
        ratio_w, ratio_h = W / float(size), H / float(size)

        blob = cv2.dnn.blobFromImage(
            img_resized, 1.0, (size, size), (123.68, 116.78, 103.94), swapRB=True, crop=False
        )
        self._east_net.setInput(blob)
        scores, geometry = self._east_net.forward(self._LAYER_NAMES)

        boxes, confidences = self._decode_east(scores, geometry, min_confidence)
        if not boxes:
            return []

        detections = non_max_suppression(np.array(boxes), probs=confidences)

        scaled = []
        for (x0, y0, x1, y1) in detections:
            scaled.append([
                max(0, int(x0 * ratio_w)),
                max(0, int(y0 * ratio_h)),
                min(W, int(x1 * ratio_w)),
                min(H, int(y1 * ratio_h)),
            ])

        return self._merge_clusters(scaled, merge_threshold)

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _cfg(psm: int) -> str:
        return f"--oem 3 --psm {psm}"

    def _load_east(self) -> bool:
        if self._east_net is not None:
            return True
        path = EAST_MODEL_PATH
        if not os.path.exists(path):
            return False
        self._east_net = cv2.dnn.readNet(path)
        return True

    @staticmethod
    def _decode_east(scores, geometry, min_confidence: float):
        rows, cols = scores.shape[2:4]
        boxes, confidences = [], []

        for y in range(rows):
            sc = scores[0, 0, y]
            ang = geometry[0, 4, y]
            d0, d1, d2, d3 = (
                geometry[0, 0, y], geometry[0, 1, y],
                geometry[0, 2, y], geometry[0, 3, y],
            )
            for x in range(cols):
                if sc[x] < min_confidence:
                    continue
                ox, oy = x * 4.0, y * 4.0
                cos_a, sin_a = np.cos(ang[x]), np.sin(ang[x])
                h = d0[x] + d2[x]
                w = d1[x] + d3[x]
                end_x = int(ox + cos_a * d1[x] + sin_a * d2[x])
                end_y = int(oy - sin_a * d1[x] + cos_a * d2[x])
                boxes.append((int(end_x - w), int(end_y - h), end_x, end_y))
                confidences.append(float(sc[x]))

        return boxes, confidences

    @staticmethod
    def _edge_distance(b1: list, b2: list) -> float:
        """Minimum distance between the edges (not centres) of two bounding boxes."""
        dx = max(0, b2[0] - b1[2], b1[0] - b2[2])
        dy = max(0, b2[1] - b1[3], b1[1] - b2[3])
        if dx > 0 and dy > 0:
            return float(np.sqrt(dx ** 2 + dy ** 2))
        return float(max(dx, dy))

    def _merge_clusters(self, boxes: list, threshold: int) -> list[dict]:
        """
        Group bounding boxes whose edge-distance is below threshold,
        return one merged bounding rect per group.
        """ 
        if not boxes:
            return []

        merged = [False] * len(boxes)
        clusters = []

        for i in range(len(boxes)):
            if merged[i]:
                continue
            group = [i]
            merged[i] = True
            j = 0
            while j < len(group):
                for k in range(len(boxes)):
                    if not merged[k] and self._edge_distance(boxes[group[j]], boxes[k]) < threshold:
                        group.append(k)
                        merged[k] = True
                j += 1

            xs = [c for idx in group for c in (boxes[idx][0], boxes[idx][2])]
            ys = [c for idx in group for c in (boxes[idx][1], boxes[idx][3])]
            margin = 10
            clusters.append({
                "x": max(0, min(xs) - margin),
                "y": max(0, min(ys) - margin),
                "w": max(xs) - min(xs) + 2 * margin,
                "h": max(ys) - min(ys) + 2 * margin,
            })

        return clusters
