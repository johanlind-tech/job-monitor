"""
Scraper pipeline — scrapes all sources, enriches with location and
employment type, upserts into the Supabase jobs table, then queues
matching jobs for each active user.
"""

from db import (
    init_db, is_seen, mark_seen,
    fetch_active_user_preferences, batch_insert_queue_entries,
)
from scrapers import ALL_SCRAPERS
from filter import job_matches_user
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

    # ── Per-user queuing ─────────────────────────────────────────────────
    if not new_jobs:
        print("[INFO] No new jobs to queue.")
        return

    user_prefs = fetch_active_user_preferences()
    if not user_prefs:
        print("[INFO] No active users to queue for.")
        return

    queue_entries: list[dict] = []
    for prefs in user_prefs:
        user_id = prefs["user_id"]
        for job in new_jobs:
            if job_matches_user(job, prefs):
                queue_entries.append({"user_id": user_id, "job_id": job["id"]})

    if queue_entries:
        inserted = batch_insert_queue_entries(queue_entries)
        print(
            f"[INFO] Queued {len(new_jobs)} jobs for {len(user_prefs)} user(s) "
            f"({inserted} new queue entries)"
        )
    else:
        print(
            f"[INFO] {len(new_jobs)} new jobs found, but none matched "
            f"any of the {len(user_prefs)} user(s) preferences."
        )


if __name__ == "__main__":
    run()
