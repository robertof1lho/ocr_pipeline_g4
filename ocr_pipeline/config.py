import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "tesseract")
EAST_MODEL_PATH: str = os.getenv("EAST_MODEL_PATH", "frozen_east_text_detection.pb")

LLM_BASE_URL: str | None = os.getenv("LLM_BASE_URL")
LLM_API_KEY: str | None = os.getenv("LLM_API_KEY")
LLM_MODEL_NAME: str | None = os.getenv("LLM_MODEL_NAME")

SALARIO_MINIMO: float = float(os.getenv("SALARIO_MINIMO", "1518.00"))

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

MIN_IMAGE_QUALITY: float = 0.4
CONFIDENCE_REVISAO_MANUAL: float = 0.6
