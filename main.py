"""
Scraper pipeline — scrapes all sources, enriches with location and
employment type, and upserts into the Supabase jobs table.

Per-user filtering and queue insertion is stubbed out for now.
"""

from db import init_db, is_seen, mark_seen, count_active_users
from scrapers import ALL_SCRAPERS
from location_parser import parse_location
from employment_type_parser import parse_employment_type


def enrich(job: dict) -> dict:
    """Add location and employment_type fields to a scraped job dict."""

    # ── Location ─────────────────────────────────────────────────────────
    loc = parse_location(
        job.get("title", ""),
        job.get("description"),
    )
    job["municipality_code"] = loc["municipality_code"]
    job["lan_code"] = loc["lan_code"]
    job["location_raw"] = loc["location_raw"]

    # ── Employment type ──────────────────────────────────────────────────
    # Platsbanken API may provide a structured employment_type already.
    api_et = job.pop("api_employment_type", None)
    job["employment_type"] = parse_employment_type(
        job.get("title", ""),
        job.get("description"),
        api_employment_type=api_et,
    )

    return job


def run():
    init_db()
    user_count = count_active_users()

    new_jobs = []

    for scraper in ALL_SCRAPERS:
        source = scraper.__name__.replace("scrape_", "")
        print(f"[INFO] Scraping: {source}")
        try:
            jobs = scraper()
            print(f"[INFO] {source}: {len(jobs)} listings found")
            for job in jobs:
                if not job.get("id") or not job.get("title"):
                    continue
                if is_seen(job["id"]):
                    continue

                enrich(job)
                mark_seen(job)
                new_jobs.append(job)
        except Exception as e:
            print(f"[ERROR] {source}: {e}")

    print(f"[INFO] Total new jobs written to Supabase: {len(new_jobs)}")

    # ── Per-user queuing (stub) ──────────────────────────────────────────
    if new_jobs:
        print(f"[STUB] Would queue {len(new_jobs)} new jobs for {user_count} active user(s)")
    else:
        print("[INFO] No new jobs to queue.")


if __name__ == "__main__":
    run()
