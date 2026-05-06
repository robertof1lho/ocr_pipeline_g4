from ocr_pipeline.llm.llm_client import LLMClient
from ocr_pipeline.models.caderneta_vacina import CadernetaVacina
from ocr_pipeline.ocr.tesseract_engine import TesseractEngine
from ocr_pipeline.preprocessor.image_processor import preprocess
from .base_extractor import BaseExtractor

_SCHEMA = {
    "nome_vacinado": "string",
    "data_nascimento": "DD/MM/YYYY",
    "vacinas": [
        {
            "nome_vacina": "string",
            "data_aplicacao": "DD/MM/YYYY",
            "dose": "1a",            # 1a | 2a | 3a | reforco | unica
            "lote": None,
        }
    ],
}


class CadernetaVacinaExtractor(BaseExtractor):
    """
    Extrai campos da caderneta de vacinação via OCR + LLM.

    Documento de maior risco: combina texto impresso e manuscrito.
    O confidence_score é calculado a partir da confiança por-palavra do
    Tesseract e injetado no modelo — o model_validator seta
    requer_revisao_manual automaticamente se score < 0.6.
    """

    def __init__(self) -> None:
        self._engine = TesseractEngine()
        self._llm = LLMClient()

    def extract(self, image_path: str) -> CadernetaVacina:
        prep = preprocess(image_path)

        # Usa PSM 6 (bloco uniforme) — cadernetas têm layout tabular consistente
        positions = self._engine.extract_with_positions(prep["processed"], psm=6)
        raw_text = " ".join(w["text"] for w in positions)
        score = self.confidence_score(positions, threshold=60)

        fields = self._llm.extract_fields(raw_text, "Caderneta de Vacinação", _SCHEMA)

        return CadernetaVacina(
            nome_vacinado=fields.get("nome_vacinado", ""),
            data_nascimento=fields.get("data_nascimento"),
            vacinas=fields.get("vacinas", []),
            confidence_score=score,
            # requer_revisao_manual é setado pelo model_validator do Pydantic
        )
