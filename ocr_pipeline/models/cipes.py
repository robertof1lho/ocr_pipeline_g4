from pydantic import BaseModel

from ._base import BRDate


class CIPES(BaseModel):
    numero_cadastro: str
    nome_beneficiario: str
    data_expedicao: BRDate
    validade: BRDate
    foto_presente: bool = False
