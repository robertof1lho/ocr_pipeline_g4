import logging

import requests

logger = logging.getLogger(__name__)

_VIACEP = "https://viacep.com.br/ws/{cep}/json/"
_TIMEOUT = 5


def validate_guaruja_address(cep: str, municipio: str = "") -> bool:
    """
    Consulta a API ViaCEP para confirmar que o CEP pertence a Guarujá, SP.

    Se o CEP não bater, tenta confirmar pelo nome do município extraído
    do documento como fallback.
    """
    cep_clean = cep.replace("-", "").replace(" ", "").strip()
    if len(cep_clean) != 8 or not cep_clean.isdigit():
        logger.warning("CEP inválido: %r", cep)
        return False

    try:
        r = requests.get(_VIACEP.format(cep=cep_clean), timeout=_TIMEOUT)
        r.raise_for_status()
        data = r.json()

        if data.get("erro"):
            return _municipio_is_guaruja(municipio)

        localidade = data.get("localidade", "")
        uf = data.get("uf", "")
        return _municipio_is_guaruja(localidade) and uf.upper() == "SP"

    except requests.RequestException as exc:
        logger.warning("Falha ao consultar ViaCEP: %s. Validando pelo município.", exc)
        return _municipio_is_guaruja(municipio)


def _municipio_is_guaruja(municipio: str) -> bool:
    normalized = municipio.upper().strip()
    return "GUARUJ" in normalized  # cobre "Guarujá" e "GUARUJÁ" independente de acento
