import re
from abc import ABC, abstractmethod

import numpy as np
from pydantic import BaseModel


class BaseExtractor(ABC):
    """
    Interface padrão para todos os extratores de documento.

    Subclasses implementam extract() e usam os helpers abaixo para
    operações comuns: crop por região relativa, busca por regex,
    e localização de palavras próximas a uma coordenada.
    """

    @abstractmethod
    def extract(self, image_path: str) -> BaseModel:
        """Run the full extraction pipeline and return a validated Pydantic model."""

    # ── Crop helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def crop_roi(
        image: np.ndarray,
        y_start: float,
        y_end: float,
        x_start: float = 0.0,
        x_end: float = 1.0,
    ) -> np.ndarray:
        """
        Crop a region of interest using ratios of the image dimensions.

        All parameters are in [0, 1] relative to image height/width.
        This keeps extractors resolution-independent.
        """
        h, w = image.shape[:2]
        return image[int(h * y_start):int(h * y_end), int(w * x_start):int(w * x_end)]

    # ── Regex helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def find_first(text: str, pattern: str, default: str | None = None) -> str | None:
        """Return the first regex match in text, or default if no match."""
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(0) if match else default

    @staticmethod
    def find_all(text: str, pattern: str) -> list[str]:
        """Return all regex matches in text."""
        return re.findall(pattern, text, re.IGNORECASE)

    @staticmethod
    def extract_after_label(text: str, label: str, pattern: str) -> str | None:
        """
        Find `label` in text, then extract the first `pattern` match after it.

        Example:
            extract_after_label(text, "CID 10", r"[A-Z]\\d{2}")
            → "G35"
        """
        idx = text.upper().find(label.upper())
        if idx == -1:
            return None
        return BaseExtractor.find_first(text[idx + len(label):], pattern)

    # ── Position-based helpers ────────────────────────────────────────────────

    @staticmethod
    def words_in_band(
        positions: list[dict],
        y_center: int,
        band_height: int = 20,
    ) -> list[str]:
        """
        Return words whose vertical center falls within band_height pixels of y_center.
        Useful for extracting a full line of text by approximate Y coordinate.
        """
        return [
            w["text"]
            for w in positions
            if abs((w["y"] + w["h"] // 2) - y_center) <= band_height
        ]

    @staticmethod
    def words_in_region(
        positions: list[dict],
        x0: int,
        y0: int,
        x1: int,
        y1: int,
    ) -> list[str]:
        """Return words whose bounding box overlaps the given rectangle."""
        return [
            w["text"]
            for w in positions
            if w["x"] >= x0 and w["y"] >= y0 and (w["x"] + w["w"]) <= x1 and (w["y"] + w["h"]) <= y1
        ]

    @staticmethod
    def confidence_score(positions: list[dict], threshold: int = 60) -> float:
        """
        Fraction of words with confidence >= threshold.
        Used by caderneta_vacina to decide if manual review is needed.
        """
        if not positions:
            return 0.0
        high_conf = sum(1 for w in positions if w["confidence"] >= threshold)
        return high_conf / len(positions)

    # ── Checkbox detection ────────────────────────────────────────────────────

    @staticmethod
    def checkbox_marked(text: str, label: str, window: int = 60) -> bool:
        """
        Heuristic: returns True if 'X', 'x' or '✓' appears within `window`
        characters after `label` in the OCR text.
        """
        idx = text.upper().find(label.upper())
        if idx == -1:
            return False
        snippet = text[idx: idx + len(label) + window]
        return bool(re.search(r"[Xx✓✗]", snippet))
