import logging
from typing import Literal

from ocr_pipeline.config import LOG_LEVEL
from ocr_pipeline.extractors.caderneta_vacina import CadernetaVacinaExtractor
from ocr_pipeline.extractors.cipes import CIPESExtractor
from ocr_pipeline.extractors.comprovante_residencia import ComprovanteResidenciaExtractor
from ocr_pipeline.extractors.comprovante_renda import ComprovanteRendaExtractor
from ocr_pipeline.extractors.declaracao_matricula import DeclaracaoMatriculaExtractor
from ocr_pipeline.extractors.laudo_medico import LaudoMedicoExtractor
from ocr_pipeline.ocr.tesseract_engine import TesseractEngine
from ocr_pipeline.preprocessor.image_processor import preprocess
from ocr_pipeline.validators.address_validator import validate_guaruja_address
from ocr_pipeline.validators.income_validator import validate_income
from ocr_pipeline.validators.medical_validator import MedicalValidator

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

DocumentType = Literal[
    "laudo_medico",
    "cipes",
    "comprovante_residencia",
    "comprovante_renda",
    "declaracao_matricula",
    "caderneta_vacina",
]

PerfilUsuario = Literal["estudante", "pcd", "idoso"]

_EXTRACTORS = {
    "laudo_medico": LaudoMedicoExtractor,
    "cipes": CIPESExtractor,
    "comprovante_residencia": ComprovanteResidenciaExtractor,
    "comprovante_renda": ComprovanteRendaExtractor,
    "declaracao_matricula": DeclaracaoMatriculaExtractor,
    "caderneta_vacina": CadernetaVacinaExtractor,
}

_medical_validator = MedicalValidator()
_ocr_engine = TesseractEngine()


def process_document(
    image_path: str,
    document_type: DocumentType,
    perfil_usuario: PerfilUsuario,
) -> dict:
    """
    Pipeline completo: pré-processamento → OCR → extração → validação.

    Returns:
        {
            status:       "success" | "error" | "manual_review",
            document_type: str,
            data:          dict,        # campos extraídos e validados
            validations:   dict,        # resultado de cada validação
            errors:        list[str],   # erros encontrados
            raw_text:      str,         # texto bruto OCR (auditoria LGPD)
        }
    """
    result: dict = {
        "status": "error",
        "document_type": document_type,
        "data": {},
        "validations": {},
        "errors": [],
        "raw_text": "",
    }

    # ── 1. Pré-processamento + verificação de qualidade ───────────────────────
    try:
        prep = preprocess(image_path)
    except ValueError as exc:
        result["errors"].append(str(exc))
        return result

    # ── 2. Texto bruto para auditoria (sempre persiste, mesmo em falha) ───────
    try:
        result["raw_text"] = _ocr_engine.extract_text(prep["processed"], psm=3)
    except Exception as exc:
        logger.warning("Falha ao extrair raw_text: %s", exc)

    # ── 3. Extração específica por tipo de documento ──────────────────────────
    extractor_cls = _EXTRACTORS.get(document_type)
    if extractor_cls is None:
        result["errors"].append(f"UNKNOWN_DOCUMENT_TYPE: {document_type}")
        return result

    try:
        extracted = extractor_cls().extract(image_path)
        result["data"] = extracted.model_dump()
    except Exception as exc:
        logger.exception("Falha na extração de %s", document_type)
        result["errors"].append(f"EXTRACTION_FAILED: {exc}")
        return result

    # ── 4. Validações por tipo ────────────────────────────────────────────────
    validations: dict = {}

    if document_type == "laudo_medico":
        cid = result["data"].get("cid10", "")
        crm = result["data"].get("crm_medico", "")
        uf = result["data"].get("uf", "")
        cep = result["data"].get("cep", "")
        municipio = result["data"].get("bairro", "")  # fallback when municipio absent

        if cid:
            cid_result = _medical_validator.validate_cid10(cid)
            validations["cid10"] = cid_result
            result["data"]["cid10_valido"] = cid_result["valid"]
            result["data"]["necessita_acompanhante"] = cid_result.get("requires_companion", False)

        if crm:
            crm_result = _medical_validator.validate_crm(crm, uf)
            validations["crm"] = crm_result
            result["data"]["crm_valido"] = crm_result["valid"]
            result["data"]["nome_medico"] = crm_result.get("doctor_name")
            result["data"]["especialidade_medico"] = crm_result.get("specialty")

        validations["endereco_guaruja"] = validate_guaruja_address(cep, municipio)

    elif document_type == "comprovante_residencia":
        cep = result["data"].get("cep", "")
        municipio = result["data"].get("municipio", "")
        validations["endereco_guaruja"] = validate_guaruja_address(cep, municipio)
        result["data"]["municipio_valido"] = validations["endereco_guaruja"]

    elif document_type == "comprovante_renda":
        valor_bruto = result["data"].get("valor_bruto", 0.0)
        validations["renda"] = validate_income([valor_bruto], perfil_usuario)

    elif document_type == "caderneta_vacina":
        score = result["data"].get("confidence_score", 0.0)
        validations["ocr_confidence"] = score
        if result["data"].get("requer_revisao_manual"):
            result["status"] = "manual_review"
            result["validations"] = validations
            return result

    # ── 5. Determina status final ─────────────────────────────────────────────
    result["validations"] = validations

    failed = [k for k, v in validations.items() if v is False]
    if failed:
        result["errors"].extend(f"VALIDATION_FAILED: {k}" for k in failed)
        result["status"] = "error"
    else:
        result["status"] = "success"

    return result


def process_renda_familiar(
    image_paths: list[str],
    perfil_usuario: PerfilUsuario,
) -> dict:
    """
    Processa múltiplos comprovantes de renda (um por membro da família)
    e valida a renda familiar total contra o limite do perfil.
    """
    extractor = ComprovanteRendaExtractor()
    rendas: list[float] = []
    documentos: list[dict] = []
    errors: list[str] = []

    for path in image_paths:
        try:
            extracted = extractor.extract(path)
            rendas.append(extracted.valor_bruto)
            documentos.append(extracted.model_dump())
        except Exception as exc:
            errors.append(f"EXTRACTION_FAILED ({path}): {exc}")

    validacao_renda = validate_income(rendas, perfil_usuario)

    return {
        "status": "success" if not errors and validacao_renda["aprovado"] else "error",
        "documentos": documentos,
        "validacao_renda": validacao_renda,
        "errors": errors,
    }
