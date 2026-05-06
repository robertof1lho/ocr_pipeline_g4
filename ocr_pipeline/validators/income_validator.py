import logging

from ocr_pipeline.config import SALARIO_MINIMO

logger = logging.getLogger(__name__)

# Limite em salários mínimos por perfil, conforme Portaria 01/2024
_LIMITES_SM: dict[str, int] = {
    "pcd": 3,
    "estudante": 4,
    "idoso": 3,
}


def validate_income(rendas: list[float], perfil: str) -> dict:
    """
    Verifica se a renda familiar total está dentro do limite para o perfil.

    Args:
        rendas:  Lista de valores brutos (um por comprovante de renda familiar)
        perfil:  "pcd" | "estudante" | "idoso"

    Returns:
        {total, limite, aprovado, excedente, salario_minimo_referencia}
    """
    multiplicador = _LIMITES_SM.get(perfil)
    if multiplicador is None:
        logger.warning("Perfil desconhecido: %r. Usando limite de 3 SM.", perfil)
        multiplicador = 3

    total = sum(rendas)
    limite = SALARIO_MINIMO * multiplicador

    return {
        "total": round(total, 2),
        "limite": round(limite, 2),
        "aprovado": total <= limite,
        "excedente": round(max(0.0, total - limite), 2),
        "salario_minimo_referencia": SALARIO_MINIMO,
    }
