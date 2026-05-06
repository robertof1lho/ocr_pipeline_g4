from typing import Optional

from pydantic import BaseModel

from ._base import BRDate


class LaudoMedico(BaseModel):
    # Identificação
    nome_completo: str
    data_nascimento: BRDate
    sexo: str
    nome_mae: str
    nome_unidade_saude: str
    data_emissao: BRDate

    # Documentos
    numero_identidade: str
    orgao_emissor: Optional[str] = None
    uf: Optional[str] = None
    data_emissao_rg: BRDate = None

    # Endereço
    logradouro: str
    numero: str
    bairro: str
    cep: str
    telefone: Optional[str] = None

    # Laudo
    deficiencia_fisica: bool = False
    deficiencia_mental: bool = False
    deficiencia_visual: bool = False
    deficiencia_auditiva: bool = False
    deficiencia_multipla: bool = False
    descricao: Optional[str] = None
    cid10: str
    definitiva: bool = False
    temporaria: bool = False
    prazo_revisao: Optional[str] = None
    necessita_acompanhante: bool = False
    assinatura_medico_presente: bool = False
    crm_medico: Optional[str] = None

    # Preenchido pelo validador após extração
    cid10_valido: Optional[bool] = None
    crm_valido: Optional[bool] = None
    nome_medico: Optional[str] = None
    especialidade_medico: Optional[str] = None
