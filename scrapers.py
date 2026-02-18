import hashlib
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
def scrape_platsbanken() -> list[dict]:
    """Uses the free JobTech/Platsbanken API — no scraping needed."""
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

                jobs.append({
                    "id": job_id,
                    "title": hit.get("headline", ""),
                    "company": hit.get("employer", {}).get("name", ""),
                    "url": hit.get("webpage_url") or f"https://arbetsformedlingen.se/platsbanken/annonser/{job_id}",
                    "description": hit.get("description", {}).get("text", "")[:500],
                    "source": "platsbanken",
                    "api_employment_type": et_label,
                })
        except Exception as e:
            print(f"[WARN] Platsbanken API error for '{kw}': {e}")

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
]
