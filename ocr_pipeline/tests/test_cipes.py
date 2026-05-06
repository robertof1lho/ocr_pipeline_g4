"""Testes do extrator CIPES."""
import pytest

from ocr_pipeline.main import process_document
from ocr_pipeline.validators.document_validator import validate_document_not_expired
from datetime import date

SAMPLE_CIPES = "ocr_pipeline/tests/sample_docs/cipes_sample.jpg"


def test_validade_futura():
    assert validate_document_not_expired(date(2099, 1, 1)) is True

def test_validade_vencida():
    assert validate_document_not_expired(date(2000, 1, 1)) is False


@pytest.mark.integration
def test_cipes_happy_path():
    result = process_document(SAMPLE_CIPES, "cipes", "pcd")
    assert result["status"] == "success"
    data = result["data"]
    assert data["numero_cadastro"] != ""
    assert data["nome_beneficiario"] != ""
