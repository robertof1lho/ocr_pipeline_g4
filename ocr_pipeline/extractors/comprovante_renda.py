from ocr_pipeline.llm.llm_client import LLMClient
from ocr_pipeline.models.comprovante_renda import ComprovanteRenda
from ocr_pipeline.ocr.tesseract_engine import TesseractEngine
from ocr_pipeline.preprocessor.image_processor import preprocess
from .base_extractor import BaseExtractor

_SCHEMA = {
    "nome_titular": "string",
    "cpf_titular": None,
    "tipo_documento": "holerite",    # holerite | extrato | declaracao_autonomo | beneficio_inss | outro
    "valor_bruto": 0.0,
    "valor_liquido": 0.0,
    "mes_referencia": "01",
    "ano_referencia": "2024",
    "empregador_nome": None,
    "empregador_cnpj": None,
}

_OPTIONAL = {"cpf_titular", "empregador_nome", "empregador_cnpj"}


class ComprovanteRendaExtractor(BaseExtractor):
    """
    Extrai campos de comprovantes de renda via OCR + LLM.

    O pipeline pode receber múltiplos comprovantes (um por membro da família).
    Cada instância extraída é acumulada pelo income_validator para calcular
    a renda familiar total.
    """

    def __init__(self) -> None:
        self._engine = TesseractEngine()
        self._llm = LLMClient()

    def extract(self, image_path: str) -> ComprovanteRenda:
        prep = preprocess(image_path)
        raw_text = self._engine.extract_text(prep["processed"], psm=3)
        fields = self._llm.extract_fields(raw_text, "Comprovante de Renda", _SCHEMA)
        cleaned = {k: v for k, v in fields.items() if v is not None or k in _OPTIONAL}
        return ComprovanteRenda(**cleaned)

    @property
    def raw_schema(self) -> dict:
        return _SCHEMA
