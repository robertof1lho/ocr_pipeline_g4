"""Testes do extrator de Declaração de Matrícula."""
import pytest

from ocr_pipeline.main import process_document

SAMPLE_MATRICULA = "ocr_pipeline/tests/sample_docs/declaracao_matricula_sample.jpg"


@pytest.mark.integration
def test_matricula_happy_path():
    result = process_document(SAMPLE_MATRICULA, "declaracao_matricula", "estudante")
    assert result["status"] == "success"
    data = result["data"]
    assert data["nome_aluno"] != ""
    assert data["nome_instituicao"] != ""
    assert data["tipo_escola"] in ("publica", "particular")
    assert data["turno"] in ("manha", "tarde", "noite", "integral")

@pytest.mark.integration
def test_matricula_sem_assinatura():
    result = process_document(
        "ocr_pipeline/tests/sample_docs/declaracao_sem_assinatura.jpg",
        "declaracao_matricula",
        "estudante",
    )
    assert result["data"]["assinatura_presente"] is False
