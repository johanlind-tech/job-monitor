"""
Job-matching filters.

* ``matches(job)`` — legacy global pre-filter (uses hardcoded config).
* ``job_matches_user(job, prefs)`` — per-user filter used at queue-
  insertion time. Checks all six preference dimensions.
"""

import re
from functools import lru_cache

from config import KEYWORDS_INCLUDE, KEYWORDS_EXCLUDE


@lru_cache(maxsize=512)
def _word_re(keyword: str) -> re.Pattern:
    """Compile a case-insensitive whole-word regex for *keyword*.

    Uses \\b (word boundary) so that e.g. "VD" matches "VD" and "VD,"
    but NOT "avdelning".  For multi-word phrases like "Vice President"
    each space becomes \\s+, so "Vice  President" still matches.
    """
    escaped = re.escape(keyword)
    # Allow flexible whitespace inside multi-word phrases
    pattern = r"\s+".join(escaped.split(r"\ "))
    return re.compile(rf"\b{pattern}\b", re.IGNORECASE)


def _kw_in_text(keyword: str, text: str) -> bool:
    """Return True if *keyword* appears as a whole word in *text*."""
    return _word_re(keyword).search(text) is not None


def matches(job: dict) -> bool:
    """Return True if job matches global include/exclude keywords."""
    text = f"{job.get('title', '')} {job.get('description', '')}"

    has_include = any(_kw_in_text(kw, text) for kw in KEYWORDS_INCLUDE)
    has_exclude = any(_kw_in_text(kw, text) for kw in KEYWORDS_EXCLUDE)

    return has_include and not has_exclude


# ── Per-user matching ────────────────────────────────────────────────────────


def job_matches_user(job: dict, prefs: dict) -> bool:
    """Return True if *job* matches a single user's preference set.

    Checks (in order, short-circuiting on first failure):
        1. source ∈ sources_enabled
        2. At least one keyword_include in title+description
        3. No keyword_exclude in title+description
        4. Region (län) filter — empty list = all pass
        5. Municipality filter — empty list = all pass
        6. Employment-type filter

    Jobs with unknown (``None``) location or employment type are **not**
    rejected — they pass through because the data simply could not be
    parsed, and the job may still be relevant.
    """
    # Build searchable text once (title always present; description may be absent)
    text = f"{job.get('title', '')} {job.get('description', '')}"

    # 1a. Country ──────────────────────────────────────────────────────────
    countries = prefs.get("countries") or ["SE"]  # default to Sweden only
    job_country = job.get("country") or "SE"
    if job_country not in countries:
        return False

    # 1b. Source ───────────────────────────────────────────────────────────
    sources = prefs.get("sources_enabled") or []
    if sources and job.get("source") not in sources:
        return False

    # 2. Keyword include (at least one must match, whole-word) ──────────
    kw_inc = prefs.get("keywords_include") or []
    if kw_inc and not any(_kw_in_text(kw, text) for kw in kw_inc):
        return False

    # 3. Keyword exclude (none may match, whole-word) ───────────────────
    kw_exc = prefs.get("keywords_exclude") or []
    if kw_exc and any(_kw_in_text(kw, text) for kw in kw_exc):
        return False

    # 4. Region (län) filter ──────────────────────────────────────────────
    regions = prefs.get("regions") or []
    if regions:
        lan_code = job.get("lan_code")
        if lan_code is not None and lan_code not in regions:
            return False

    # 5. Municipality filter ──────────────────────────────────────────────
    municipalities = prefs.get("municipalities") or []
    if municipalities:
        muni_code = job.get("municipality_code")
        if muni_code is not None and muni_code not in municipalities:
            return False

    # 6. Employment type ──────────────────────────────────────────────────
    emp_types = prefs.get("employment_types") or []
    if emp_types:
        et = job.get("employment_type")
        if et is not None and et not in emp_types:
            return False

    return True
