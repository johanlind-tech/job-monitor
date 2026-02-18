"""
Employment type detection — classifies a job as "interim", "permanent",
or None (unknown) based on keyword signals in the title and description.
"""

import re

# Patterns that signal an interim / consultant / fractional engagement.
_INTERIM_KEYWORDS: list[str] = [
    "interim",
    "fractional",
    "konsult",
    "uppdrag",
    "deltid",          # part-time as a role indicator
    "konsultuppdrag",
    "interimschef",
]

# Patterns that signal a permanent / full-time position.
_PERMANENT_KEYWORDS: list[str] = [
    "tillsvidare",
    "fast tjänst",
    "permanent",
    "heltid",          # full-time as a role indicator
    "tillsvidareanställning",
    "fast anställning",
]


def _has_keyword(text: str, keywords: list[str]) -> bool:
    """Return True if any keyword appears as a whole word in *text*."""
    for kw in keywords:
        pattern = r"(?<![a-zåäöA-ZÅÄÖ])" + re.escape(kw) + r"(?![a-zåäöA-ZÅÄÖ])"
        if re.search(pattern, text):
            return True
    return False


def parse_employment_type(
    title: str,
    description: str | None = None,
    *,
    api_employment_type: str | None = None,
) -> str | None:
    """Classify a job as ``"interim"``, ``"permanent"``, or ``None``.

    Parameters
    ----------
    title : str
        The job title.
    description : str | None
        Free-text job description (can be None).
    api_employment_type : str | None
        If the source API already provides a structured employment type
        (e.g. Platsbanken), pass it here.  It takes precedence over
        text-based detection.

    Returns
    -------
    str | None
        ``"interim"``, ``"permanent"``, or ``None`` if unclear.
    """
    # 1. Prefer the structured API value when available.
    if api_employment_type:
        normalized = api_employment_type.strip().lower()
        if normalized in ("interim", "konsult", "consultant", "temporary", "visstid"):
            return "interim"
        if normalized in ("permanent", "tillsvidare", "full-time", "heltid"):
            return "permanent"

    # 2. Fall back to text analysis.
    text = ((title or "") + " " + (description or "")).lower()

    is_interim = _has_keyword(text, _INTERIM_KEYWORDS)
    is_permanent = _has_keyword(text, _PERMANENT_KEYWORDS)

    # If both signals appear, prefer the title-level signal.
    if is_interim and is_permanent:
        title_lower = (title or "").lower()
        if _has_keyword(title_lower, _INTERIM_KEYWORDS):
            return "interim"
        if _has_keyword(title_lower, _PERMANENT_KEYWORDS):
            return "permanent"
        return None  # genuinely ambiguous

    if is_interim:
        return "interim"
    if is_permanent:
        return "permanent"

    return None
