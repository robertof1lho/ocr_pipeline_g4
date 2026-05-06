from ocr_pipeline.llm.llm_client import LLMClient
from ocr_pipeline.models.declaracao_matricula import DeclaracaoMatricula
from ocr_pipeline.ocr.tesseract_engine import TesseractEngine
from ocr_pipeline.preprocessor.image_processor import preprocess
from .base_extractor import BaseExtractor

_SCHEMA = {
    "nome_aluno": "string",
    "data_nascimento": "DD/MM/YYYY",
    "nome_instituicao": "string",
    "cnpj_instituicao": None,
    "tipo_escola": "publica",        # publica | particular
    "serie_ano": "1º Ano",
    "turno": "manha",                # manha | tarde | noite | integral
    "ano_letivo": "2024",
    "data_emissao": "DD/MM/YYYY",
    "assinatura_presente": True,
}

_OPTIONAL = {"cnpj_instituicao"}


class DeclaracaoMatriculaExtractor(BaseExtractor):
    """
    Extrai campos de declarações de matrícula escolar via OCR + LLM.

    O layout varia por instituição, portanto PSM 3 (detecção automática
    de colunas e blocos) é preferível ao PSM 6.
    """

    def __init__(self) -> None:
        self._engine = TesseractEngine()
        self._llm = LLMClient()

    def extract(self, image_path: str) -> DeclaracaoMatricula:
        prep = preprocess(image_path)
        raw_text = self._engine.extract_text(prep["processed"], psm=3)
        fields = self._llm.extract_fields(raw_text, "Declaração de Matrícula Escolar", _SCHEMA)
        cleaned = {k: v for k, v in fields.items() if v is not None or k in _OPTIONAL}
        return DeclaracaoMatricula(**cleaned)

    @property
    def raw_schema(self) -> dict:
        return _SCHEMA
