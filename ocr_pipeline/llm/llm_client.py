import json
import logging
import re
import time

from openai import OpenAI

from ocr_pipeline.config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL_NAME

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Você é um extrator de informações de documentos brasileiros. "
    "Retorne APENAS JSON válido, sem markdown, sem explicações adicionais. "
    "Use null para campos não encontrados — nunca invente valores. "
    "Normalize datas para o formato DD/MM/YYYY. "
    "Normalize valores monetários para float sem símbolo de moeda (ex: 1234.56)."
)

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class LLMClient:
    """
    OpenAI-compatible client for structured field extraction from OCR text.

    Provedor configurado exclusivamente via variáveis de ambiente:
        LLM_BASE_URL   — endpoint da API (NVIDIA, Groq, OpenRouter, Ollama…)
        LLM_API_KEY    — chave do provedor
        LLM_MODEL_NAME — identificador do modelo

    Trocar de provedor = mudar apenas o .env, sem alterar código.
    """

    def __init__(self) -> None:
        self._client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)

    def extract_fields(
        self,
        raw_text: str,
        document_type: str,
        output_schema: dict,
    ) -> dict:
        """
        Send OCR text to the LLM and return a structured dict matching output_schema.

        Args:
            raw_text:      Raw string from Tesseract
            document_type: Human-readable document name for the prompt context
            output_schema: Dict of {field_name: example_value} defining expected output

        Returns:
            Parsed dict with the extracted fields.

        Raises:
            RuntimeError with code LLM_PARSE_FAILED after 3 failed attempts.
        """
        schema_str = json.dumps(output_schema, ensure_ascii=False, indent=2)
        user_message = (
            f"Tipo de documento: {document_type}\n\n"
            f"Texto extraído por OCR:\n{raw_text}\n\n"
            f"Retorne um JSON com exatamente estes campos:\n{schema_str}"
        )

        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = self._client.chat.completions.create(
                    model=LLM_MODEL_NAME,
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0,
                )
                content = _strip_markdown_fence(response.choices[0].message.content)
                return json.loads(content)

            except json.JSONDecodeError as exc:
                last_error = exc
                logger.warning(
                    "LLM retornou JSON inválido (tentativa %d/3): %s", attempt + 1, exc
                )
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Falha na requisição LLM (tentativa %d/3): %s", attempt + 1, exc
                )

            if attempt < 2:
                time.sleep(2 ** attempt)  # 1s, 2s antes das tentativas 2 e 3

        raise RuntimeError(f"LLM_PARSE_FAILED: {last_error}")


def _strip_markdown_fence(text: str) -> str:
    """Remove ```json ... ``` wrappers that some models add despite instructions."""
    return _FENCE_RE.sub("", text).strip()
