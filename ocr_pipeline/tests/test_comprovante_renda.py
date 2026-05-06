"""Testes do extrator de Comprovante de Renda e validador de renda familiar."""
import pytest

from ocr_pipeline.validators.income_validator import validate_income
from ocr_pipeline.validators.document_validator import validate_cpf
from ocr_pipeline.main import process_document, process_renda_familiar
from ocr_pipeline.config import SALARIO_MINIMO

SAMPLE_RENDA = "ocr_pipeline/tests/sample_docs/comprovante_renda_sample.jpg"


def test_renda_pcd_aprovada():
    limite = SALARIO_MINIMO * 3
    resultado = validate_income([limite - 100], "pcd")
    assert resultado["aprovado"] is True
    assert resultado["excedente"] == 0.0

def test_renda_pcd_reprovada():
    limite = SALARIO_MINIMO * 3
    resultado = validate_income([limite + 1], "pcd")
    assert resultado["aprovado"] is False
    assert resultado["excedente"] > 0

def test_renda_estudante_limite_maior():
    limite_pcd = SALARIO_MINIMO * 3
    resultado = validate_income([limite_pcd + 100], "estudante")
    assert resultado["aprovado"] is True

def test_renda_familiar_soma():
    resultado = validate_income([1000.0, 800.0, 500.0], "pcd")
    assert resultado["total"] == 2300.0

def test_cpf_valido():
    assert validate_cpf("529.982.247-25") is True

def test_cpf_invalido():
    assert validate_cpf("111.111.111-11") is False


@pytest.mark.integration
def test_renda_happy_path():
    result = process_document(SAMPLE_RENDA, "comprovante_renda", "pcd")
    assert result["status"] == "success"
    assert result["data"]["valor_bruto"] > 0
