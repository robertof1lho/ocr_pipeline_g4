"""Testes do extrator de Caderneta de Vacina."""
import pytest

from ocr_pipeline.models.caderneta_vacina import CadernetaVacina
from ocr_pipeline.main import process_document

SAMPLE_VACINA = "ocr_pipeline/tests/sample_docs/caderneta_vacina_sample.jpg"


def test_revisao_manual_automatica_por_confidence():
    """model_validator deve setar requer_revisao_manual=True se score < 0.6."""
    caderneta = CadernetaVacina(
        nome_vacinado="Teste",
        vacinas=[],
        confidence_score=0.35,
    )
    assert caderneta.requer_revisao_manual is True

def test_sem_revisao_manual_alta_confidence():
    caderneta = CadernetaVacina(
        nome_vacinado="Teste",
        vacinas=[],
        confidence_score=0.85,
    )
    assert caderneta.requer_revisao_manual is False


@pytest.mark.integration
def test_caderneta_happy_path():
    result = process_document(SAMPLE_VACINA, "caderneta_vacina", "pcd")
    assert result["status"] in ("success", "manual_review")
    assert result["data"]["nome_vacinado"] != ""
    assert isinstance(result["data"]["vacinas"], list)

@pytest.mark.integration
def test_caderneta_baixa_qualidade_nao_bloqueia():
    """Baixo confidence gera manual_review mas não status=error."""
    result = process_document(
        "ocr_pipeline/tests/sample_docs/caderneta_manuscrita.jpg",
        "caderneta_vacina",
        "pcd",
    )
    assert result["status"] != "error" or "QUALITY" in str(result["errors"])
