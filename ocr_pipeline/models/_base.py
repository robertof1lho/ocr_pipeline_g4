from datetime import date, datetime
from typing import Annotated, Optional

from pydantic import BeforeValidator


def _parse_br_date(v):
    """Accept date objects, ISO strings (YYYY-MM-DD), or Brazilian strings (DD/MM/YYYY)."""
    if v is None or isinstance(v, date):
        return v
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(v).strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Formato de data inválido: {v!r}. Use DD/MM/YYYY.")


BRDate = Annotated[Optional[date], BeforeValidator(_parse_br_date)]
