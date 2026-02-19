from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _make_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def _get(url: str) -> BeautifulSoup | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"[WARN] Failed to fetch {url}: {e}")
        return None


# ── CAPA ──────────────────────────────────────────────────────────────────────
def scrape_capa() -> list[dict]:
    soup = _get("https://www.capa.se/tjanster-uppdrag")
    if not soup:
        return []
    jobs = []
    for a in soup.select("a[href*='uppdrag'], a[href*='tjanst']"):
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not href or not title:
            continue
        if not href.startswith("http"):
            href = "https://www.capa.se" + href
        jobs.append({"id": _make_id(href), "title": title, "company": "CAPA", "url": href, "source": "capa"})
    return jobs


# ── INTERIM SEARCH ────────────────────────────────────────────────────────────
def scrape_interimsearch() -> list[dict]:
    soup = _get("https://www.interimsearch.com/publika-uppdrag/")
    if not soup:
        return []
    jobs = []
    for card in soup.select("article, .job, .uppdrag, .assignment"):
        a = card.find("a", href=True)
        title_el = card.find(["h2", "h3", "h4"])
        if not a or not title_el:
            continue
        href = a["href"]
        if not href.startswith("http"):
            href = "https://www.interimsearch.com" + href
        title = title_el.get_text(strip=True)
        jobs.append({"id": _make_id(href), "title": title, "company": "Interim Search", "url": href, "source": "interimsearch"})
    return jobs


# ── WISE ──────────────────────────────────────────────────────────────────────
def scrape_wise() -> list[dict]:
    soup = _get("https://www.wise.se/lediga-jobb/")
    if not soup:
        return []
    jobs = []
    for a in soup.select("a[href*='/jobb/'], a[href*='/job/'], a[href*='/lediga']"):
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not href or not title or len(title) < 5:
            continue
        if not href.startswith("http"):
            href = "https://www.wise.se" + href
        jobs.append({"id": _make_id(href), "title": title, "company": "Wise", "url": href, "source": "wise"})
    return jobs


# ── HEAD AGENT ────────────────────────────────────────────────────────────────
def scrape_headagent() -> list[dict]:
    soup = _get("https://www.headagent.se/uppdrag/")
    if not soup:
        return []
    jobs = []
    for a in soup.select("a[href*='uppdrag']"):
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not href or not title or len(title) < 5:
            continue
        if not href.startswith("http"):
            href = "https://www.headagent.se" + href
        jobs.append({"id": _make_id(href), "title": title, "company": "Head Agent", "url": href, "source": "headagent"})
    return jobs


# ── MICHAEL BERGLUND ──────────────────────────────────────────────────────────
def scrape_michaelberglund() -> list[dict]:
    soup = _get("https://michaelberglund.se/executive-search/")
    if not soup:
        return []
    jobs = []
    for a in soup.select("a[href*='search'], a[href*='jobb'], a[href*='uppdrag']"):
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not href or not title or len(title) < 5:
            continue
        if not href.startswith("http"):
            href = "https://michaelberglund.se" + href
        jobs.append({"id": _make_id(href), "title": title, "company": "Michael Berglund", "url": href, "source": "michaelberglund"})
    return jobs


# ── MASON ─────────────────────────────────────────────────────────────────────
def scrape_mason() -> list[dict]:
    soup = _get("https://mason.se/alla-case/")
    if not soup:
        return []
    jobs = []
    for a in soup.select("a[href*='case'], a[href*='jobb'], a[href*='uppdrag']"):
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not href or not title or len(title) < 5:
            continue
        if not href.startswith("http"):
            href = "https://mason.se" + href
        jobs.append({"id": _make_id(href), "title": title, "company": "Mason", "url": href, "source": "mason"})
    return jobs


# ── HAMMER & HANBORG ──────────────────────────────────────────────────────────
def scrape_hammerhanborg() -> list[dict]:
    soup = _get("https://jobb.hammerhanborg.se/jobs")
    if not soup:
        return []
    jobs = []
    for a in soup.select("a[href*='/jobs/']"):
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not href or not title or len(title) < 5:
            continue
        if not href.startswith("http"):
            href = "https://jobb.hammerhanborg.se" + href
        jobs.append({"id": _make_id(href), "title": title, "company": "Hammer & Hanborg", "url": href, "source": "hammerhanborg"})
    return jobs


# ── NOVARE ────────────────────────────────────────────────────────────────────
def scrape_novare() -> list[dict]:
    soup = _get("https://novare.se/executive-search/lediga-jobb/")
    if not soup:
        return []
    jobs = []
    for a in soup.select("a[href*='jobb'], a[href*='job'], a[href*='search']"):
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not href or not title or len(title) < 5:
            continue
        if not href.startswith("http"):
            href = "https://novare.se" + href
        jobs.append({"id": _make_id(href), "title": title, "company": "Novare", "url": href, "source": "novare"})
    return jobs


# ── PLATSBANKEN API ───────────────────────────────────────────────────────────

# Tracking parameters to strip from application URLs.
_TRACKING_PARAMS = {"pnty_src", "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"}


def _clean_apply_url(url: str) -> str:
    """Remove common tracking parameters from an application URL."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    cleaned = {k: v for k, v in params.items() if k not in _TRACKING_PARAMS}
    new_query = urlencode(cleaned, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


# Regex patterns to extract client company from headlines.
# Pattern A (most common): "Role till Company" / "Managing Director to LAPP"
_CLIENT_AFTER_RE = re.compile(
    r"(?:^|\s)(?:till|to|för|for|hos|at)\s+(.+)",
    re.IGNORECASE,
)
# Pattern B: "Company rekryterar Role" / "Company söker Role"
_CLIENT_BEFORE_RE = re.compile(
    r"^(.+?)\s+(?:rekryterar|söker|anställer|seeks|hiring|hires)\s+",
    re.IGNORECASE,
)


def _extract_client_company(headline: str) -> str | None:
    """Try to extract the client company name from a Platsbanken headline.

    Recruitment firms typically use patterns like:
    - "Role till Company" / "Role to Company" (company after role)
    - "Company rekryterar Role" / "Company söker Role" (company before role)

    Returns *None* when no pattern is detected.
    """
    # Try pattern A first (most common)
    m = _CLIENT_AFTER_RE.search(headline)
    if m:
        company = m.group(1).strip().rstrip("!.?")
        if len(company) >= 2:
            # Skip common false positives
            skip_words = {"oss", "en", "ett", "dig", "er", "dem", "vår", "ditt"}
            if company.lower() not in skip_words:
                return company

    # Try pattern B: "Company söker/rekryterar Role"
    m = _CLIENT_BEFORE_RE.search(headline)
    if m:
        company = m.group(1).strip().rstrip("!.?")
        if len(company) >= 2:
            return company

    return None


def scrape_platsbanken() -> list[dict]:
    """Uses the free JobTech/Platsbanken API — no scraping needed.

    When a recruitment firm posts on behalf of a client:
    - The client company is extracted from the headline (e.g. "VD till Acme"
      → company = "Acme") and used as the *company* field.
    - The application URL (pointing to the firm's own page) is used instead
      of the Platsbanken listing URL.
    - If the client company cannot be parsed, the employer name is kept.
    - Source remains "platsbanken" for all listings from this scraper.
    """
    from config import KEYWORDS_INCLUDE
    jobs = []
    seen_ids = set()

    for kw in KEYWORDS_INCLUDE[:10]:  # Limit API calls; main keywords only
        try:
            url = "https://jobsearch.api.jobtechdev.se/search"
            params = {
                "q": kw,
                "limit": 50,
                "offset": 0,
            }
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            for hit in data.get("hits", []):
                job_id = hit.get("id", "")
                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                # Extract structured employment type from the API response
                et_label = (
                    hit.get("employment_type", {}).get("label", "")
                    if isinstance(hit.get("employment_type"), dict)
                    else ""
                )

                employer_name = hit.get("employer", {}).get("name", "")
                headline = hit.get("headline", "")
                apply_url = (hit.get("application_details") or {}).get("url") or ""
                platsbanken_url = (
                    hit.get("webpage_url")
                    or f"https://arbetsformedlingen.se/platsbanken/annonser/{job_id}"
                )

                # ── Detect recruitment-firm postings ──────────────────
                # A recruitment firm typically has an external application URL
                # (not on arbetsformedlingen.se).  We check the *domain* of
                # the URL, not just the string, because tracking params like
                # ?pnty_src=arbetsformedlingen would cause false negatives.
                apply_domain = urlparse(apply_url).netloc.lower() if apply_url else ""
                is_agency = bool(
                    apply_url
                    and "arbetsformedlingen" not in apply_domain
                )

                if is_agency:
                    # Try to extract the real client company from the headline
                    client = _extract_client_company(headline)
                    company = client if client else employer_name
                    job_url = _clean_apply_url(apply_url)
                    source = "platsbanken"  # keep source as platsbanken
                else:
                    company = employer_name
                    job_url = platsbanken_url
                    source = "platsbanken"

                jobs.append({
                    "id": job_id,
                    "title": headline,
                    "company": company,
                    "url": job_url,
                    "description": hit.get("description", {}).get("text", "")[:500],
                    "source": source,
                    "api_employment_type": et_label,
                })
        except Exception as e:
            print(f"[WARN] Platsbanken API error for '{kw}': {e}")

    return jobs


# ── WES ──────────────────────────────────────────────────────────────────────
def scrape_wes() -> list[dict]:
    """Wes links to Intelliplan ATS. May have 0 jobs when none are public."""
    soup = _get("https://wesgroup.se/for-kandidater/")
    if not soup:
        return []
    jobs = []
    for a in soup.select("a[href*='intelliplan']"):
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not href or not title or len(title) < 5:
            continue
        # Skip generic links like "Registrera ditt CV"
        if "registrera" in title.lower() or "cv" in title.lower():
            continue
        jobs.append({"id": _make_id(href), "title": title, "company": "Wes", "url": href, "source": "wes"})
    return jobs


# ── STARDUST SEARCH ──────────────────────────────────────────────────────────
def scrape_stardust() -> list[dict]:
    soup = _get("https://stardust.teamtailor.com/jobs")
    if not soup:
        return []
    jobs = []
    for a in soup.select("a[href*='/jobs/']"):
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not href or not title or len(title) < 5:
            continue
        if not href.startswith("http"):
            href = "https://stardust.teamtailor.com" + href
        jobs.append({"id": _make_id(href), "title": title, "company": "Stardust Search", "url": href, "source": "stardust"})
    return jobs


# ── ACADEMIC SEARCH ──────────────────────────────────────────────────────────
def scrape_academicsearch() -> list[dict]:
    soup = _get("https://academicsearch.se/en/job-vacancies/")
    if not soup:
        return []
    jobs = []
    seen = set()
    for a in soup.select("a[href*='/en/job/']"):
        href = a.get("href", "")
        if not href or href in seen:
            continue
        seen.add(href)
        if not href.startswith("http"):
            href = "https://www.academicsearch.se" + href
        # Use the heading inside the link for a clean title
        heading = a.find(["h2", "h3", "h4", "h5", "strong"])
        title = heading.get_text(strip=True) if heading else a.get_text(strip=True)
        if not title or len(title) < 5:
            continue
        jobs.append({"id": _make_id(href), "title": title, "company": "Academic Search", "url": href, "source": "academicsearch"})
    return jobs


# ── SIGNPOST ─────────────────────────────────────────────────────────────────
def scrape_signpost() -> list[dict]:
    soup = _get("https://signpost.se/lediga-chefsjobb/")
    if not soup:
        return []
    jobs = []
    for a in soup.select("a[href*='/lediga-uppdrag/']"):
        href = a.get("href", "")
        if not href:
            continue
        if not href.startswith("http"):
            href = "https://signpost.se" + href
        # Title is in the heading inside the link (not the full text)
        heading = a.find(["h1", "h2", "h3", "h4", "h5"])
        title = heading.get_text(strip=True) if heading else a.get_text(strip=True)
        if not title or len(title) < 5:
            continue
        jobs.append({"id": _make_id(href), "title": title, "company": "Signpost", "url": href, "source": "signpost"})
    return jobs


# ── INHOUSE ──────────────────────────────────────────────────────────────────
def scrape_inhouse() -> list[dict]:
    soup = _get("https://inhouse.se/jobb/")
    if not soup:
        return []
    jobs = []
    seen = set()
    for a in soup.select("a[href*='/jobb/']"):
        href = a.get("href", "")
        if not href:
            continue
        if not href.startswith("http"):
            href = "https://www.inhouse.se" + href
        # Skip the main /jobb/ page link itself
        if href.rstrip("/") in ("https://www.inhouse.se/jobb", "https://inhouse.se/jobb"):
            continue
        if href in seen:
            continue
        seen.add(href)
        # Title from link text, or extract from URL slug
        title = a.get_text(strip=True)
        if not title or title.lower() in ("lediga jobb", "läs mer", ""):
            slug = href.rstrip("/").split("/")[-1]
            title = slug.replace("-", " ").title()
        if len(title) < 5:
            continue
        jobs.append({"id": _make_id(href), "title": title, "company": "Inhouse", "url": href, "source": "inhouse"})
    return jobs


# ── PEOPLEPROVIDE ────────────────────────────────────────────────────────────
def scrape_peopleprovide() -> list[dict]:
    soup = _get("https://career.peopleprovide.se/jobs")
    if not soup:
        return []
    jobs = []
    for a in soup.select("a[href*='/jobs/']"):
        href = a.get("href", "")
        if not href:
            continue
        if not href.startswith("http"):
            href = "https://career.peopleprovide.se" + href
        # Teamtailor: clean title is in span.text-block-base-link
        title_el = a.select_one("span.text-block-base-link, [class*='text-block-base']")
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        if not title or len(title) < 5:
            continue
        jobs.append({"id": _make_id(href), "title": title, "company": "PeopleProvide", "url": href, "source": "peopleprovide"})
    return jobs


# ── FUTURE VALUE REKRYTERING ─────────────────────────────────────────────────
def _scrape_futurevalue(url: str, source: str) -> list[dict]:
    """Shared scraper for FutureValue pages. Link text is 'Visa annons' so
    we extract the title from the URL slug instead."""
    soup = _get(url)
    if not soup:
        return []
    jobs = []
    seen = set()
    for a in soup.select("a[href*='/jobs/']"):
        href = a.get("href", "")
        if not href or href in seen:
            continue
        seen.add(href)
        if not href.startswith("http"):
            href = "https://futurevalue.se" + href
        # Extract title from URL slug: /jobs/3246-group-financial-controller/
        slug = href.rstrip("/").split("/")[-1]
        # Remove leading number prefix like "3246-"
        parts = slug.split("-", 1)
        title = parts[1].replace("-", " ").title() if len(parts) > 1 else slug.replace("-", " ").title()
        if len(title) < 5:
            continue
        jobs.append({"id": _make_id(href), "title": title, "company": "Future Value", "url": href, "source": source})
    return jobs


def scrape_futurevalue_rekrytering() -> list[dict]:
    return _scrape_futurevalue("https://futurevalue.se/publika-rekryteringar/", "futurevalue_rekrytering")


# ── FUTURE VALUE INTERIM ─────────────────────────────────────────────────────
def scrape_futurevalue_interim() -> list[dict]:
    return _scrape_futurevalue("https://futurevalue.se/publika-interimsuppdrag/", "futurevalue_interim")


# ── AVANTI REKRYTERING ───────────────────────────────────────────────────────
def scrape_avanti() -> list[dict]:
    soup = _get("https://avantirekrytering.se/publika-uppdrag/")
    if not soup:
        return []
    jobs = []
    seen = set()
    for a in soup.select("a[href*='/jobs/']"):
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not href or not title or len(title) < 5:
            continue
        if not href.startswith("http"):
            href = "https://avantirekrytering.se" + href
        # Skip generic "VISA TJÄNST" button links (duplicates of the title links)
        if title.upper() == "VISA TJÄNST":
            continue
        if href in seen:
            continue
        seen.add(href)
        jobs.append({"id": _make_id(href), "title": title, "company": "Avanti Rekrytering", "url": href, "source": "avanti"})
    return jobs


# ── POOLIA EXECUTIVE ─────────────────────────────────────────────────────────
def scrape_pooliaexecutive() -> list[dict]:
    soup = _get("https://pooliaexecutivesearch.teamtailor.com/jobs")
    if not soup:
        return []
    jobs = []
    for a in soup.select("a[href*='/jobs/']"):
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not href or not title or len(title) < 5:
            continue
        if not href.startswith("http"):
            href = "https://pooliaexecutivesearch.teamtailor.com" + href
        jobs.append({"id": _make_id(href), "title": title, "company": "Poolia Executive", "url": href, "source": "pooliaexecutive"})
    return jobs


# ── NIGEL WRIGHT ─────────────────────────────────────────────────────────────
def scrape_nigel_wright() -> list[dict]:
    try:
        r = requests.get(
            "https://www.nigelwright.com/se/vacancies",
            headers={**HEADERS, "Accept": "text/html,application/xhtml+xml"},
            timeout=15,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"[WARN] Failed to fetch nigelwright.com: {e}")
        return []
    jobs = []
    for a in soup.select("a[href*='/vacancy/'], a[href*='/vacancies/']"):
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not href or not title or len(title) < 5:
            continue
        if not href.startswith("http"):
            href = "https://www.nigelwright.com" + href
        jobs.append({"id": _make_id(href), "title": title, "company": "Nigel Wright", "url": href, "source": "nigel_wright"})
    return jobs


# ── GAZELLA ──────────────────────────────────────────────────────────────────
def scrape_gazella() -> list[dict]:
    soup = _get("https://gazella.se/jobb/")
    if not soup:
        return []
    jobs = []
    seen = set()
    for a in soup.select("a[href*='/jobb/']"):
        href = a.get("href", "")
        if not href:
            continue
        if not href.startswith("http"):
            href = "https://www.gazella.se" + href
        # Skip nav links and the main listing page
        normalized = href.rstrip("/")
        if normalized in ("https://www.gazella.se/jobb", "https://gazella.se/jobb"):
            continue
        if href in seen:
            continue
        seen.add(href)
        # Title is in the first bold <p> element inside the link
        bold_p = a.select_one("p.u-text-bold, [class*='u-text-bold']")
        title = bold_p.get_text(strip=True) if bold_p else a.get_text(strip=True)
        if not title or len(title) < 5:
            continue
        if title.lower() in ("lediga jobb", "se alla", "alla jobb"):
            continue
        jobs.append({"id": _make_id(href), "title": title, "company": "Gazella", "url": href, "source": "gazella"})
    return jobs


# ── ALUMNI ───────────────────────────────────────────────────────────────────
def scrape_alumni() -> list[dict]:
    soup = _get("https://alumniglobal.com/open-positions")
    if not soup:
        return []
    jobs = []
    for item in soup.select(".summary-item"):
        a = item.find("a", href=True)
        if not a:
            continue
        # Squarespace uses .summary-title for headings (not h2/h3)
        title_el = item.select_one(".summary-title")
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        href = a.get("href", "")
        if not href or not title or len(title) < 5:
            continue
        if not href.startswith("http"):
            href = "https://alumniglobal.com" + href
        jobs.append({"id": _make_id(href), "title": title, "company": "Alumni", "url": href, "source": "alumni"})
    return jobs


# ── PROPER PEOPLE ────────────────────────────────────────────────────────────
def scrape_properpeople() -> list[dict]:
    soup = _get("https://properpeople.teamtailor.com/jobs")
    if not soup:
        return []
    jobs = []
    for a in soup.select("a[href*='/jobs/']"):
        href = a.get("href", "")
        if not href:
            continue
        if not href.startswith("http"):
            href = "https://properpeople.teamtailor.com" + href
        # Teamtailor: clean title is in span.text-block-base-link
        title_el = a.select_one("span.text-block-base-link, [class*='text-block-base']")
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        if not title or len(title) < 5:
            continue
        jobs.append({"id": _make_id(href), "title": title, "company": "Proper People", "url": href, "source": "properpeople"})
    return jobs


# ── JOBWAY ───────────────────────────────────────────────────────────────────
def scrape_jobway() -> list[dict]:
    soup = _get("https://jobway.se/lediga-jobb/chef/")
    if not soup:
        return []
    jobs = []
    for item in soup.select(".e-loop-item"):
        a = item.find("a", href=True)
        title_el = item.find(["h2", "h3", "h4"])
        if not a:
            continue
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        href = a.get("href", "")
        if not href or not title or len(title) < 5:
            continue
        if not href.startswith("http"):
            href = "https://jobway.se" + href
        jobs.append({"id": _make_id(href), "title": title, "company": "Jobway", "url": href, "source": "jobway"})
    return jobs


# ── BEYOND RETAIL ────────────────────────────────────────────────────────────
def scrape_beyondretail() -> list[dict]:
    soup = _get("https://beyondretail.se/lediga-jobb/")
    if not soup:
        return []
    jobs = []
    seen = set()
    for a in soup.select("a[href*='/jobs/'], a[href*='/lediga-jobb/']"):
        href = a.get("href", "")
        if not href:
            continue
        if not href.startswith("http"):
            href = "https://beyondretail.se" + href
        # Skip the main listing page link itself
        if href.rstrip("/") == "https://beyondretail.se/lediga-jobb":
            continue
        if href in seen:
            continue
        seen.add(href)
        # Title is in .job-listing-position div
        pos_el = a.select_one(".job-listing-position")
        title = pos_el.get_text(strip=True) if pos_el else a.get_text(strip=True)
        if not title or len(title) < 5:
            continue
        jobs.append({"id": _make_id(href), "title": title, "company": "Beyond Retail", "url": href, "source": "beyondretail"})
    return jobs


# ── BØNES VIRIK ──────────────────────────────────────────────────────────────
def scrape_bonesvirik() -> list[dict]:
    soup = _get("https://bonesvirik.no/utlyste-stillinger/")
    if not soup:
        return []
    jobs = []
    seen = set()
    # Jobs are in article/card wrappers with apply.recman.no links
    for card in soup.select("article, .stilling, .job, .card, .listing, .vacancy"):
        a = card.find("a", href=lambda h: h and "apply.recman.no" in h)
        if not a:
            continue
        href = a.get("href", "")
        if not href or href in seen:
            continue
        seen.add(href)
        # Extract title from card text (company + role pattern)
        texts = [t.get_text(strip=True) for t in card.find_all(["h2", "h3", "h4", "strong", "b"])]
        title = " – ".join(t for t in texts if t and len(t) > 2 and t.lower() not in ("les mer om stillingen",))
        if not title:
            title = card.get_text(" ", strip=True)[:80]
        # Skip generic links
        if "registrer" in title.lower() or "logg inn" in title.lower():
            continue
        if len(title) < 5:
            continue
        jobs.append({"id": _make_id(href), "title": title, "company": "Bønes Virik", "url": href, "source": "bonesvirik"})
    return jobs


# ── VISINDI ──────────────────────────────────────────────────────────────────
def scrape_visindi() -> list[dict]:
    try:
        r = requests.get(
            "https://visindi.no/en/vacancies",
            headers={**HEADERS, "Accept": "text/html,application/xhtml+xml"},
            timeout=15,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"[WARN] Failed to fetch visindi.no: {e}")
        return []
    jobs = []
    for a in soup.select("a[href*='/vacancy/'], a[href*='/vacancies/']"):
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not href or not title or len(title) < 5:
            continue
        if not href.startswith("http"):
            href = "https://visindi.no" + href
        jobs.append({"id": _make_id(href), "title": title, "company": "Visindi", "url": href, "source": "visindi"})
    return jobs


# ── VINDEX ───────────────────────────────────────────────────────────────────
def scrape_vindex() -> list[dict]:
    try:
        r = requests.get(
            "https://vindex.se/jobb/",
            headers={**HEADERS, "Accept": "text/html,application/xhtml+xml"},
            timeout=15,
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"[WARN] Failed to fetch vindex.se: {e}")
        return []
    jobs = []
    for a in soup.select("a[href*='/jobb/']"):
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if not href or not title or len(title) < 5:
            continue
        if not href.startswith("http"):
            href = "https://vindex.se" + href
        # Skip the main listing page link itself
        if href.rstrip("/") == "https://vindex.se/jobb":
            continue
        jobs.append({"id": _make_id(href), "title": title, "company": "Vindex", "url": href, "source": "vindex"})
    return jobs


# ── REGISTRY ──────────────────────────────────────────────────────────────────
ALL_SCRAPERS = [
    scrape_capa,
    scrape_interimsearch,
    scrape_wise,
    scrape_headagent,
    scrape_michaelberglund,
    scrape_mason,
    scrape_hammerhanborg,
    scrape_novare,
    scrape_platsbanken,
    # New sources
    scrape_wes,
    scrape_stardust,
    scrape_academicsearch,
    scrape_signpost,
    scrape_inhouse,
    scrape_peopleprovide,
    scrape_futurevalue_rekrytering,
    scrape_futurevalue_interim,
    scrape_avanti,
    scrape_pooliaexecutive,
    scrape_nigel_wright,
    scrape_gazella,
    scrape_alumni,
    scrape_properpeople,
    scrape_jobway,
    scrape_beyondretail,
    scrape_bonesvirik,
    scrape_visindi,
    scrape_vindex,
]
