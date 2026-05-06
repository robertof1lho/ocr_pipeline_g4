from ocr_pipeline.models.laudo_medico import LaudoMedico
from ocr_pipeline.ocr.tesseract_engine import TesseractEngine
from ocr_pipeline.preprocessor.image_processor import preprocess
from .base_extractor import BaseExtractor

# ---------------------------------------------------------------------------
# Regiões do formulário padrão da Prefeitura de Guarujá (Laudo PCD)
# Valores em ratios relativos à altura/largura da imagem processada [0.0, 1.0]
# TODO: calibre estas coordenadas com o formulário real escaneado
# ---------------------------------------------------------------------------
FIELD_REGIONS = {
    # campo:              (y_start, y_end, x_start, x_end)
    "nome_completo":      (0.05, 0.11, 0.00, 1.00),
    "data_nascimento":    (0.11, 0.16, 0.00, 0.40),
    "sexo":               (0.11, 0.16, 0.40, 0.60),
    "nome_mae":           (0.16, 0.21, 0.00, 1.00),
    "nome_unidade_saude": (0.21, 0.26, 0.00, 0.70),
    "data_emissao":       (0.21, 0.26, 0.70, 1.00),
    "numero_identidade":  (0.26, 0.32, 0.00, 0.35),
    "orgao_emissor":      (0.26, 0.32, 0.35, 0.55),
    "uf_rg":              (0.26, 0.32, 0.55, 0.65),
    "data_emissao_rg":    (0.26, 0.32, 0.65, 1.00),
    "logradouro":         (0.32, 0.37, 0.00, 0.70),
    "numero_endereco":    (0.32, 0.37, 0.70, 0.85),
    "bairro":             (0.37, 0.42, 0.00, 0.50),
    "cep":                (0.37, 0.42, 0.50, 0.75),
    "telefone":           (0.37, 0.42, 0.75, 1.00),
    "checkboxes_def":     (0.48, 0.58, 0.00, 1.00),
    "descricao":          (0.58, 0.66, 0.00, 1.00),
    "cid10":              (0.66, 0.71, 0.00, 0.30),
    "definitiva_temp":    (0.71, 0.76, 0.00, 1.00),
    "prazo_revisao":      (0.76, 0.81, 0.00, 0.50),
    "acompanhante":       (0.76, 0.81, 0.50, 1.00),
    "assinatura_crm":     (0.88, 1.00, 0.00, 1.00),
}


class LaudoMedicoExtractor(BaseExtractor):
    """
    Extrai campos do Laudo Médico PCD da Prefeitura de Guarujá via OCR puro.

    Estratégia: crop por região relativa → Tesseract PSM 6 → regex por campo.
    Não usa LLM — o formulário tem layout fixo e padronizado.
    """

    _DATE_RE = r"\d{2}/\d{2}/\d{4}"
    _CEP_RE = r"\d{5}-?\d{3}"
    _FONE_RE = r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}"
    _CID_RE = r"[A-Z]\d{2}(?:\.\d)?"
    _CRM_RE = r"(?:CRM\s?)?\d{4,6}"

    def __init__(self) -> None:
        self._engine = TesseractEngine()

    def extract(self, image_path: str) -> LaudoMedico:
        prep = preprocess(image_path)
        img = prep["processed"]

        def ocr(region_key: str, psm: int = 6) -> str:
            roi = self.crop_roi(img, *FIELD_REGIONS[region_key])
            return self._engine.extract_text(roi, psm=psm).strip()

        nome = ocr("nome_completo")
        data_nasc_raw = self.find_first(ocr("data_nascimento"), self._DATE_RE)
        nome_mae = ocr("nome_mae")
        unidade = ocr("nome_unidade_saude")
        data_emissao_raw = self.find_first(ocr("data_emissao"), self._DATE_RE)

        identidade_text = ocr("numero_identidade")
        orgao = ocr("orgao_emissor") or None
        uf_rg = self.find_first(ocr("uf_rg"), r"[A-Z]{2}") or None
        data_rg_raw = self.find_first(ocr("data_emissao_rg"), self._DATE_RE)

        logradouro = ocr("logradouro")
        numero_end = ocr("numero_endereco")
        bairro = ocr("bairro")
        cep = self.find_first(ocr("cep"), self._CEP_RE) or ""
        telefone = self.find_first(ocr("telefone"), self._FONE_RE)

        checkboxes_text = ocr("checkboxes_def")
        def_fisica = self.checkbox_marked(checkboxes_text, "Física")
        def_mental = self.checkbox_marked(checkboxes_text, "Mental")
        def_visual = self.checkbox_marked(checkboxes_text, "Visual")
        def_auditiva = self.checkbox_marked(checkboxes_text, "Auditiva")
        def_multipla = self.checkbox_marked(checkboxes_text, "Múltipla")

        descricao = ocr("descricao") or None
        cid10 = self.find_first(ocr("cid10"), self._CID_RE) or ""

        def_temp_text = ocr("definitiva_temp")
        definitiva = self.checkbox_marked(def_temp_text, "Definitiva")
        temporaria = self.checkbox_marked(def_temp_text, "Temporária")

        prazo = ocr("prazo_revisao") or None
        acompanhante_text = ocr("acompanhante")
        necessita_acompanhante = self.checkbox_marked(acompanhante_text, "Sim")

        assinatura_text = ocr("assinatura_crm")
        assinatura_presente = len(assinatura_text.strip()) > 5
        crm = self.find_first(assinatura_text, self._CRM_RE)

        return LaudoMedico(
            nome_completo=nome,
            data_nascimento=data_nasc_raw,
            sexo=_extract_sexo(ocr("sexo")),
            nome_mae=nome_mae,
            nome_unidade_saude=unidade,
            data_emissao=data_emissao_raw,
            numero_identidade=identidade_text,
            orgao_emissor=orgao,
            uf=uf_rg,
            data_emissao_rg=data_rg_raw,
            logradouro=logradouro,
            numero=numero_end,
            bairro=bairro,
            cep=cep,
            telefone=telefone,
            deficiencia_fisica=def_fisica,
            deficiencia_mental=def_mental,
            deficiencia_visual=def_visual,
            deficiencia_auditiva=def_auditiva,
            deficiencia_multipla=def_multipla,
            descricao=descricao,
            cid10=cid10,
            definitiva=definitiva,
            temporaria=temporaria,
            prazo_revisao=prazo,
            necessita_acompanhante=necessita_acompanhante,
            assinatura_medico_presente=assinatura_presente,
            crm_medico=crm,
        )


def _extract_sexo(text: str) -> str:
    t = text.upper()
    if "FEMININO" in t or " F " in t:
        return "F"
    if "MASCULINO" in t or " M " in t:
        return "M"
    # fallback: primeiro caractere que seja M ou F isolado
    import re
    match = re.search(r"\b([MF])\b", t)
    return match.group(1) if match else ""
