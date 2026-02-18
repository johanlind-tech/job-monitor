"""
Location enrichment — scans job text for Swedish city/municipality names
and maps them to official SCB municipality and län codes.

The lookup table is fetched once from Supabase at startup and cached in
memory for the lifetime of the process.
"""

import re
from db import fetch_swedish_locations

# ── In-memory cache ──────────────────────────────────────────────────────────

_location_lookup: dict | None = None  # municipality_name (lower) → row dict

# Common alternative spellings / English names that map to official names.
_ALIASES: dict[str, str] = {
    "gothenburg": "göteborg",
    "goeteborg": "göteborg",
    "malmo": "malmö",
    "umea": "umeå",
    "ostersund": "östersund",
    "gavle": "gävle",
    "vasteras": "västerås",
    "norrkoping": "norrköping",
    "linkoping": "linköping",
    "jonkoping": "jönköping",
    "sodertalje": "södertälje",
    "helsingborg": "helsingborg",
    "angelholm": "ängelholm",
    "hassleholm": "hässleholm",
    "ornskoldsvik": "örnsköldsvik",
    "lulea": "luleå",
    "sundsvall": "sundsvall",
    "boras": "borås",
    "karlskrona": "karlskrona",
}


def _ensure_lookup():
    """Build the lookup dict from Supabase (once)."""
    global _location_lookup
    if _location_lookup is not None:
        return

    rows = fetch_swedish_locations()
    _location_lookup = {}

    for row in rows:
        name_lower = row["municipality_name"].lower()
        _location_lookup[name_lower] = row

    # Register aliases that point to official names already in the lookup.
    for alias, official in _ALIASES.items():
        if official in _location_lookup and alias not in _location_lookup:
            _location_lookup[alias] = _location_lookup[official]


def parse_location(title: str, description: str | None = None) -> dict:
    """Scan *title* and *description* for a Swedish municipality name.

    Returns a dict with keys:
        municipality_code  – e.g. "0180" or None
        lan_code           – e.g. "01"  or None
        location_raw       – the matched text or None

    The first match wins (title is checked before description).  Longer
    names are tried first so that "Upplands Väsby" beats "Väsby".
    """
    _ensure_lookup()

    text = (title or "") + " " + (description or "")
    text_lower = text.lower()

    if not text_lower.strip():
        return {"municipality_code": None, "lan_code": None, "location_raw": None}

    # Sort candidate names longest-first so multi-word names match first.
    candidates = sorted(_location_lookup.keys(), key=len, reverse=True)

    for name in candidates:
        # Word-boundary match so "Lund" doesn't match inside "Grundskola".
        pattern = r"(?<![a-zåäöA-ZÅÄÖ])" + re.escape(name) + r"(?![a-zåäöA-ZÅÄÖ])"
        match = re.search(pattern, text_lower)
        if match:
            row = _location_lookup[name]
            # Pull the raw text from the original (preserving case).
            start, end = match.start(), match.end()
            raw = text[start:end]
            return {
                "municipality_code": row["municipality_code"],
                "lan_code": row["lan_code"],
                "location_raw": raw,
            }

    return {"municipality_code": None, "lan_code": None, "location_raw": None}
