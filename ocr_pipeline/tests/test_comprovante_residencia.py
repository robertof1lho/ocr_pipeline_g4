"""Testes do extrator de Comprovante de Residência."""
import pytest

from ocr_pipeline.validators.address_validator import validate_guaruja_address
from ocr_pipeline.validators.document_validator import validate_cep_format
from ocr_pipeline.main import process_document

SAMPLE_RESIDENCIA = "ocr_pipeline/tests/sample_docs/comprovante_residencia_sample.jpg"


def test_cep_formato_valido():
    assert validate_cep_format("11430-000") is True
    assert validate_cep_format("11430000") is True

def test_cep_formato_invalido():
    assert validate_cep_format("1143-000") is False
    assert validate_cep_format("abcde-000") is False

def test_municipio_guaruja_fallback():
    # Se a API ViaCEP falhar, valida pelo nome do município
    assert validate_guaruja_address("00000-000", "Guarujá") is True
    assert validate_guaruja_address("00000-000", "São Paulo") is False


@pytest.mark.integration
def test_residencia_happy_path():
    result = process_document(SAMPLE_RESIDENCIA, "comprovante_residencia", "pcd")
    assert result["status"] == "success"
    assert result["validations"].get("endereco_guaruja") is True


@pytest.mark.integration
def test_residencia_cep_fora_guaruja():
    result = process_document(
        "ocr_pipeline/tests/sample_docs/comprovante_sp_capital.jpg",
        "comprovante_residencia",
        "pcd",
    )
    assert result["validations"].get("endereco_guaruja") is False
    assert result["status"] == "error"
