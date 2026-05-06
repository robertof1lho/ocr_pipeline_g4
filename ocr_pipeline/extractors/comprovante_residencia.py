from ocr_pipeline.llm.llm_client import LLMClient
from ocr_pipeline.models.comprovante_residencia import ComprovanteResidencia
from ocr_pipeline.ocr.tesseract_engine import TesseractEngine
from ocr_pipeline.preprocessor.image_processor import preprocess
from .base_extractor import BaseExtractor

_SCHEMA = {
    "nome_titular": "string",
    "cpf_titular": None,
    "logradouro": "string",
    "numero": "string",
    "complemento": None,
    "bairro": "string",
    "municipio": "string",
    "uf": "SP",
    "cep": "00000-000",
    "tipo_documento": "conta_luz",   # conta_luz | conta_agua | iptu | outro
    "mes_referencia": "01",
    "ano_referencia": "2024",
}


class ComprovanteResidenciaExtractor(BaseExtractor):
    """
    Extrai campos de comprovantes de residência via OCR + LLM.

    Usa PSM 3 (layout automático) porque o formato varia por fornecedor
    (Light, Sabesp, IPTU, etc.).
    """

    def __init__(self) -> None:
        self._engine = TesseractEngine()
        self._llm = LLMClient()

    def extract(self, image_path: str) -> ComprovanteResidencia:
        prep = preprocess(image_path)
        raw_text = self._engine.extract_text(prep["processed"], psm=3)
        fields = self._llm.extract_fields(raw_text, "Comprovante de Residência", _SCHEMA)
        return ComprovanteResidencia(**{k: v for k, v in fields.items() if v is not None or _is_optional(k)})

    @property
    def raw_schema(self) -> dict:
        return _SCHEMA


def _is_optional(field: str) -> bool:
    return field in {"cpf_titular", "complemento"}
