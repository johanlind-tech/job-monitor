"""
Supabase-backed job store — replaces the old SQLite db.py.

Uses the service-role key so the scraper pipeline bypasses RLS.
"""

import os
from supabase import create_client, Client

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        _client = create_client(url, key)
    return _client


def init_db():
    """Verify connectivity (replaces the old SQLite init_db)."""
    client = _get_client()
    # Quick smoke test — will raise if creds are wrong
    client.table("jobs").select("id").limit(1).execute()
    print("[INFO] Supabase connection OK")


def is_seen(job_id: str) -> bool:
    """Return True if a job with this ID already exists in the jobs table."""
    client = _get_client()
    result = client.table("jobs").select("id").eq("id", job_id).execute()
    return len(result.data) > 0


def mark_seen(job: dict):
    """Upsert a job into the jobs table.

    Accepts the enriched job dict coming out of the pipeline.  Only the
    columns that exist in the jobs table are written; extra keys are ignored.
    """
    client = _get_client()
    row = {
        "id": job["id"],
        "title": job.get("title"),
        "company": job.get("company", ""),
        "url": job.get("url"),
        "source": job.get("source"),
        "country": job.get("country", "SE"),
        "municipality_code": job.get("municipality_code"),
        "lan_code": job.get("lan_code"),
        "location_raw": job.get("location_raw"),
        "employment_type": job.get("employment_type"),
    }
    client.table("jobs").upsert(row, on_conflict="id").execute()


def count_active_users() -> int:
    """Return the number of profiles with an active or trialing subscription."""
    client = _get_client()
    result = (
        client.table("profiles")
        .select("id", count="exact")
        .in_("subscription_status", ["active", "trialing"])
        .execute()
    )
    return result.count or 0


def fetch_swedish_locations() -> list[dict]:
    """Return all rows from swedish_locations (used by the location parser)."""
    client = _get_client()
    result = (
        client.table("swedish_locations")
        .select("municipality_code,municipality_name,lan_code,lan_name")
        .execute()
    )
    return result.data
