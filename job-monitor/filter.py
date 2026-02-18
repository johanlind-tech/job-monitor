from config import KEYWORDS_INCLUDE, KEYWORDS_EXCLUDE


def matches(job: dict) -> bool:
    """Return True if job matches include keywords and has no exclude keywords."""
    text = f"{job.get('title', '')} {job.get('description', '')}".lower()

    has_include = any(kw.lower() in text for kw in KEYWORDS_INCLUDE)
    has_exclude = any(kw.lower() in text for kw in KEYWORDS_EXCLUDE)

    return has_include and not has_exclude
