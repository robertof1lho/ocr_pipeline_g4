from typing import Literal, Optional

from pydantic import BaseModel

from ._base import BRDate

TipoEscola = Literal["publica", "particular"]
Turno = Literal["manha", "tarde", "noite", "integral"]


class DeclaracaoMatricula(BaseModel):
    nome_aluno: str
    data_nascimento: BRDate
    nome_instituicao: str
    cnpj_instituicao: Optional[str] = None
    tipo_escola: TipoEscola
    serie_ano: str
    turno: Turno
    ano_letivo: str
    data_emissao: BRDate
    assinatura_presente: bool = False
