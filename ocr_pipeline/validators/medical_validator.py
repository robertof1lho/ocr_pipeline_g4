import json
import logging
from pathlib import Path

from ocr_pipeline.validators.cfm_client import validar_medico_cfm

logger = logging.getLogger(__name__)

_CIDS_PATH = Path(__file__).parent / "cids_validos.json"


class MedicalValidator:
    """
    Valida CID-10 contra o Anexo da Portaria 01/2024 (local, sem API)
    e CRM via portal CFM (Playwright + reCAPTCHA).
    """

    def __init__(self) -> None:
        self._cids = self._load_cids()

    def validate_cid10(self, cid_code: str) -> dict:
        """
        Verifica se o CID-10 consta no Anexo Único da Portaria 01/2024.

        Returns:
            {valid, disease_name, requires_companion, validity_years}
        """
        code = cid_code.upper().strip()
        entry = self._cids.get(code)
        if not entry or code.startswith("_"):
            return {
                "valid": False,
                "disease_name": None,
                "requires_companion": False,
                "validity_years": None,
            }
        return {
            "valid": True,
            "disease_name": entry.get("nome"),
            "requires_companion": entry.get("acompanhante", False),
            "validity_years": entry.get("validade_anos"),
        }

    def validate_crm(self, crm_number: str, uf: str) -> dict:
        """
        Valida CRM via portal CFM usando Playwright para contornar o reCAPTCHA.

        Returns:
            {valid, doctor_name, specialty, situation}
        Latência esperada: 5–15s (browser init + captcha).
        """
        result = validar_medico_cfm({"crm": crm_number, "uf": uf})
        if not result:
            logger.warning("CFM não retornou resultado para CRM %s/%s", crm_number, uf)
            return {"valid": False, "doctor_name": None, "specialty": None, "situation": None}

        dados = result.get("dados") or []
        if not dados:
            return {"valid": False, "doctor_name": None, "specialty": None, "situation": None}

        medico = dados[0]
        situacao_raw = str(medico.get("situacaoMedico", "")).upper()
        return {
            "valid": True,
            "doctor_name": medico.get("nomeMedico"),
            "specialty": medico.get("especialidade"),
            "situation": "ativo" if situacao_raw == "A" else "inativo",
        }

    def _load_cids(self) -> dict:
        if not _CIDS_PATH.exists():
            logger.warning("cids_validos.json não encontrado em %s", _CIDS_PATH)
            return {}
        with open(_CIDS_PATH, encoding="utf-8") as f:
            return json.load(f)
