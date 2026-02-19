"""
Job-matching filters.

* ``matches(job)`` — legacy global pre-filter (uses hardcoded config).
* ``job_matches_user(job, prefs)`` — per-user filter used at queue-
  insertion time. Checks all six preference dimensions.
"""

from config import KEYWORDS_INCLUDE, KEYWORDS_EXCLUDE


def matches(job: dict) -> bool:
    """Return True if job matches global include/exclude keywords."""
    text = f"{job.get('title', '')} {job.get('description', '')}".lower()

    has_include = any(kw.lower() in text for kw in KEYWORDS_INCLUDE)
    has_exclude = any(kw.lower() in text for kw in KEYWORDS_EXCLUDE)

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
    text = f"{job.get('title', '')} {job.get('description', '')}".lower()

    # 1a. Country ──────────────────────────────────────────────────────────
    countries = prefs.get("countries") or []
    if countries:
        job_country = job.get("country") or "SE"
        if job_country not in countries:
            return False

    # 1b. Source ───────────────────────────────────────────────────────────
    sources = prefs.get("sources_enabled") or []
    if sources and job.get("source") not in sources:
        return False

    # 2. Keyword include (at least one must match) ────────────────────────
    kw_inc = prefs.get("keywords_include") or []
    if kw_inc and not any(kw.lower() in text for kw in kw_inc):
        return False

    # 3. Keyword exclude (none may match) ─────────────────────────────────
    kw_exc = prefs.get("keywords_exclude") or []
    if kw_exc and any(kw.lower() in text for kw in kw_exc):
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
