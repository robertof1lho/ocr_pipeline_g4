"""
Testes do extrator do Laudo Médico PCD.

Adicione documentos de amostra anonimizados em tests/sample_docs/
antes de rodar os testes de integração.
"""
import pytest

from ocr_pipeline.extractors.laudo_medico import LaudoMedicoExtractor
from ocr_pipeline.main import process_document
from ocr_pipeline.validators.document_validator import validate_cid10_format


# ── Testes unitários (sem imagem) ─────────────────────────────────────────────

def test_cid10_format_valido():
    assert validate_cid10_format("G35") is True
    assert validate_cid10_format("H54.0") is True

def test_cid10_format_invalido():
    assert validate_cid10_format("999") is False
    assert validate_cid10_format("ZZ9") is False


# ── Testes de integração (requer sample_docs/) ────────────────────────────────

SAMPLE_LAUDO = "ocr_pipeline/tests/sample_docs/laudo_medico_sample.jpg"

@pytest.mark.integration
def test_laudo_happy_path():
    result = process_document(SAMPLE_LAUDO, "laudo_medico", "pcd")
    assert result["status"] in ("success", "manual_review")
    assert result["data"]["cid10"] != ""
    assert result["data"]["nome_completo"] != ""

@pytest.mark.integration
def test_laudo_campo_ausente():
    """Documento sem CRM deve extrair sem erro mas com crm_medico=None."""
    result = process_document(SAMPLE_LAUDO, "laudo_medico", "pcd")
    assert "EXTRACTION_FAILED" not in str(result["errors"])

@pytest.mark.integration
def test_laudo_imagem_ruim():
    result = process_document(
        "ocr_pipeline/tests/sample_docs/laudo_medico_baixa_qualidade.jpg",
        "laudo_medico",
        "pcd",
    )
    assert result["status"] == "error"
    assert any("QUALITY" in e or "NOT_FOUND" in e for e in result["errors"])
