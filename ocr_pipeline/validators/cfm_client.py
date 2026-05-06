import json
import requests
from playwright.sync_api import sync_playwright


def validar_medico_cfm(dados_entrada: dict, headless: bool = True) -> dict | None:
    """
    Valida um médico via portal CFM (Conselho Federal de Medicina).

    Usa Playwright para obter token reCAPTCHA invisível antes de chamar
    a API REST — sem esse token, a API retorna 403.

    Args:
        dados_entrada: dict com chaves opcionais:
            nome_do_medico, uf, crm, municipio,
            tipo_de_inscricao, situacao, detalhe_situacao, especialidade
        headless: False útil para depuração local do fluxo de captcha

    Returns:
        JSON da API CFM ou None em caso de falha.
    """
    url_portal = "https://portal.cfm.org.br/busca-medicos"
    api_endpoint = "https://portal.cfm.org.br/api_rest_php/api/v2/medicos/buscar_medicos"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.goto(url_portal, wait_until="networkidle")

        if dados_entrada.get("nome_do_medico"):
            page.fill("#nome", dados_entrada["nome_do_medico"])
        if dados_entrada.get("uf"):
            page.select_option("#uf", value=dados_entrada["uf"])
        if dados_entrada.get("crm"):
            page.fill("#crm", str(dados_entrada["crm"]))

        captcha_token = None
        try:
            page.locator("button.btnPesquisar").click()
            page.wait_for_function(
                "document.getElementById('g-recaptcha-response').value.length > 0",
                timeout=45000,
            )
            captcha_token = page.evaluate(
                "document.getElementById('g-recaptcha-response').value"
            )
        except Exception as e:
            print(f"Erro ao obter token reCAPTCHA: {e}")
            browser.close()
            return None

        session = requests.Session()
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Origin": "https://portal.cfm.org.br",
            "Referer": "https://portal.cfm.org.br/busca-medicos",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            "X-Requested-With": "XMLHttpRequest",
        }
        payload = [{
            "useCaptchav2": True,
            "captcha": captcha_token,
            "medico": {
                "nome": dados_entrada.get("nome_do_medico", ""),
                "ufMedico": dados_entrada.get("uf", ""),
                "crmMedico": dados_entrada.get("crm", ""),
                "municipioMedico": dados_entrada.get("municipio", ""),
                "tipoInscricaoMedico": dados_entrada.get("tipo_de_inscricao", ""),
                "situacaoMedico": dados_entrada.get("situacao", ""),
                "detalheSituacaoMedico": dados_entrada.get("detalhe_situacao", ""),
                "especialidadeMedico": dados_entrada.get("especialidade", ""),
                "areaAtuacaoMedico": "",
            },
            "page": 1,
            "pageNumber": 1,
            "pageSize": 10,
        }]

        res = session.post(api_endpoint, json=payload, headers=headers)
        browser.close()

        if res.status_code == 200:
            return res.json()

        print(f"Erro na API CFM {res.status_code}: {res.text}")
        return None


if __name__ == "__main__":
    resultado = validar_medico_cfm({"nome_do_medico": "mauricio", "uf": ""})
    if resultado:
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
