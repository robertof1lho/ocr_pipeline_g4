from ocr_pipeline.models.cipes import CIPES
from ocr_pipeline.ocr.tesseract_engine import TesseractEngine
from ocr_pipeline.preprocessor.image_processor import preprocess
from .base_extractor import BaseExtractor

# ---------------------------------------------------------------------------
# Regiões do cartão CIPES
# Valores em ratios relativos à altura/largura da imagem processada [0.0, 1.0]
# TODO: calibre estas coordenadas com o cartão CIPES real digitalizado
# ---------------------------------------------------------------------------
FIELD_REGIONS = {
    # campo:              (y_start, y_end, x_start, x_end)
    "numero_cadastro":    (0.00, 0.15, 0.00, 0.60),
    "nome_beneficiario":  (0.15, 0.35, 0.00, 0.75),
    "data_expedicao":     (0.55, 0.70, 0.00, 0.50),
    "validade":           (0.55, 0.70, 0.50, 1.00),
    "foto":               (0.10, 0.90, 0.75, 1.00),
}

_DATE_RE = r"\d{2}/\d{2}/\d{4}"
_NUMERO_RE = r"\d{5,15}"


class CIPESExtractor(BaseExtractor):
    """
    Extrai campos do cartão CIPES via OCR puro.

    Estratégia: crop por região → Tesseract → regex.
    A foto é detectada verificando se a região contém pixels não-brancos.
    """

    def __init__(self) -> None:
        self._engine = TesseractEngine()

    def extract(self, image_path: str) -> CIPES:
        prep = preprocess(image_path)
        img = prep["processed"]

        def ocr(region_key: str) -> str:
            roi = self.crop_roi(img, *FIELD_REGIONS[region_key])
            return self._engine.extract_text(roi, psm=6).strip()

        numero_text = ocr("numero_cadastro")
        numero = self.find_first(numero_text, _NUMERO_RE) or numero_text

        nome = ocr("nome_beneficiario")
        expedicao = self.find_first(ocr("data_expedicao"), _DATE_RE)
        validade = self.find_first(ocr("validade"), _DATE_RE)
        foto = _detect_photo(self.crop_roi(img, *FIELD_REGIONS["foto"]))

        return CIPES(
            numero_cadastro=numero,
            nome_beneficiario=nome,
            data_expedicao=expedicao,
            validade=validade,
            foto_presente=foto,
        )


def _detect_photo(roi) -> bool:
    """Heuristic: photo region has meaningful non-white pixel variance."""
    import numpy as np
    if roi.size == 0:
        return False
    return float(roi.std()) > 15.0
