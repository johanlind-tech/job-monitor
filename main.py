"""
Scraper pipeline — scrapes all sources, enriches with location and
employment type, upserts into the Supabase jobs table, queues matching
jobs for each active user, then sends email digests via SendGrid.
"""

import os
from datetime import date

# Debug: check which env vars Railway injects
print(f"[DEBUG] SUPABASE_URL present: {'SUPABASE_URL' in os.environ}")
print(f"[DEBUG] Env var names: {[k for k in sorted(os.environ.keys()) if not k.startswith('_')]}")

from db import (
    init_db, is_seen, mark_seen,
    fetch_active_user_preferences, batch_insert_queue_entries,
    fetch_digest_recipients, fetch_unsent_jobs_for_user, mark_queue_sent,
)
from scrapers import ALL_SCRAPERS
from config import SOURCE_COUNTRY
from filter import job_matches_user
from email_sender import send_digest
from location_parser import parse_location
from employment_type_parser import parse_employment_type


def enrich(job: dict) -> dict:
    """Add location, country and employment_type fields to a scraped job dict."""

    # ── Country ───────────────────────────────────────────────────────────
    source = job.get("source", "")
    job["country"] = SOURCE_COUNTRY.get(source, "SE")

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
    if new_jobs:
        user_prefs = fetch_active_user_preferences()
        if user_prefs:
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
                print("[INFO] New jobs found, but none matched any user preferences.")
        else:
            print("[INFO] No active users to queue for.")
    else:
        print("[INFO] No new jobs to queue.")

    # ── Digest delivery ──────────────────────────────────────────────────
    today_weekday = date.today().isoweekday()
    day_name = date.today().strftime("%A")
    recipients = fetch_digest_recipients(today_weekday)

    if not recipients:
        print(f"[INFO] No users scheduled for digest delivery on {day_name}.")
        return

    print(f"[INFO] Sending digests ({day_name}, {len(recipients)} eligible user(s))...")
    sent_count = 0
    skip_count = 0

    for user in recipients:
        user_id = user["user_id"]
        email = user["email"]

        jobs = fetch_unsent_jobs_for_user(user_id)
        if not jobs:
            print(f"[INFO]  → {email}: 0 jobs — skipped (empty queue)")
            skip_count += 1
            continue

        success = send_digest(jobs, email)
        if success:
            mark_queue_sent(user_id, [j["id"] for j in jobs])
            print(f"[INFO]  → {email}: {len(jobs)} jobs — sent")
            sent_count += 1
        else:
            print(f"[WARN]  → {email}: {len(jobs)} jobs — FAILED (will retry)")
            skip_count += 1

    print(f"[INFO] Digest delivery complete: {sent_count} sent, {skip_count} skipped")


if __name__ == "__main__":
    run()
