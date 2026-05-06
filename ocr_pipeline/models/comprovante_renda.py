from typing import Literal, Optional

from pydantic import BaseModel, field_validator

TipoDocRenda = Literal["holerite", "extrato", "declaracao_autonomo", "beneficio_inss", "outro"]


class ComprovanteRenda(BaseModel):
    nome_titular: str
    cpf_titular: Optional[str] = None
    tipo_documento: TipoDocRenda = "outro"
    valor_bruto: float
    valor_liquido: float
    mes_referencia: str
    ano_referencia: str
    empregador_nome: Optional[str] = None
    empregador_cnpj: Optional[str] = None

    @field_validator("valor_bruto", "valor_liquido", mode="before")
    @classmethod
    def parse_valor(cls, v):
        """Accept 'R$ 1.234,56', '1234.56', or float."""
        if isinstance(v, (int, float)):
            return float(v)
        cleaned = (
            str(v)
            .replace("R$", "")
            .replace(" ", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )
        return float(cleaned)
