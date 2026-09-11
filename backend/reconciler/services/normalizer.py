import re
from decimal import Decimal, InvalidOperation
from typing import Optional


NULL_LIKE_VALUES = {
    "",
    "N/A",
    "NA",
    "NULL",
    "NONE",
    "-",
}


def normalize_reference(value: object) -> str:
    """
    Convert reference variants such as:

        REC-001
        rec_001
        REC001
        001
         rec-001

    into a canonical lowercase key.

    The assignment explicitly calls for preserving the original
    reference while normalizing it for matching.
    """
    if value is None:
        return ""

    text = str(value).strip().lower()

    if not text:
        return ""

    return re.sub(r"[^a-z0-9]", "", text)


def safe_parse_decimal(value: object) -> Optional[Decimal]:
    """
    Safely parse dirty numeric values.

    Examples:
        "$1,250.50" -> Decimal("1250.50")
        "1,250.50"  -> Decimal("1250.50")
        "N/A"       -> None
        ""          -> None
        None        -> None
    """
    if value is None:
        return None

    text = str(value).strip()

    if text.upper() in NULL_LIKE_VALUES:
        return None

    cleaned = re.sub(r"[^0-9.\-]", "", text)

    if cleaned in {"", "-", ".", "-."}:
        return None

    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None
