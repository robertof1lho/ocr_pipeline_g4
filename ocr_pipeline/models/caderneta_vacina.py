from typing import Literal, Optional

from pydantic import BaseModel, model_validator

from ._base import BRDate
from ocr_pipeline.config import CONFIDENCE_REVISAO_MANUAL

Dose = Literal["1a", "2a", "3a", "reforco", "unica"]


class Vacina(BaseModel):
    nome_vacina: str
    data_aplicacao: Optional[str] = None
    dose: Optional[str] = None
    lote: Optional[str] = None


class CadernetaVacina(BaseModel):
    nome_vacinado: str
    data_nascimento: BRDate = None
    vacinas: list[Vacina] = []
    confidence_score: float = 0.0
    requer_revisao_manual: bool = False

    @model_validator(mode="after")
    def set_revisao_flag(self):
        """Auto-flag for manual review when confidence is below threshold."""
        if self.confidence_score < CONFIDENCE_REVISAO_MANUAL:
            self.requer_revisao_manual = True
        return self
