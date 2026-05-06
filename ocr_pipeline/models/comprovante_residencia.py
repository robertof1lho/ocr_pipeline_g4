from typing import Literal, Optional

from pydantic import BaseModel

TipoDocResidencia = Literal["conta_luz", "conta_agua", "iptu", "outro"]


class ComprovanteResidencia(BaseModel):
    nome_titular: str
    cpf_titular: Optional[str] = None
    logradouro: str
    numero: str
    complemento: Optional[str] = None
    bairro: str
    municipio: str
    uf: str
    cep: str
    tipo_documento: TipoDocResidencia = "outro"
    mes_referencia: str
    ano_referencia: str

    # Preenchido pelo validador
    municipio_valido: Optional[bool] = None
