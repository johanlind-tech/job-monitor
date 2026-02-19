"""
Supabase-backed job store — replaces the old SQLite db.py.

Uses the service-role key so the scraper pipeline bypasses RLS.
"""

import os
from datetime import datetime, timezone
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


# ── Per-user queuing ─────────────────────────────────────────────────────────


def fetch_active_user_preferences() -> list[dict]:
    """Fetch preferences for all users with an active or trialing subscription.

    Returns a list of dicts, each containing:
        user_id, keywords_include, keywords_exclude, sources_enabled,
        regions, municipalities, employment_types
    """
    client = _get_client()
    result = (
        client.table("user_preferences")
        .select(
            "user_id, keywords_include, keywords_exclude, "
            "sources_enabled, regions, municipalities, employment_types, "
            "profiles!inner(subscription_status)"
        )
        .in_("profiles.subscription_status", ["active", "trialing"])
        .execute()
    )
    # Flatten: drop the nested profiles object from each row
    prefs = []
    for row in result.data:
        row.pop("profiles", None)
        prefs.append(row)
    return prefs


def batch_insert_queue_entries(entries: list[dict]) -> int:
    """Insert queue entries into user_job_queue (idempotent).

    Parameters
    ----------
    entries : list[dict]
        Each dict must have keys ``user_id`` and ``job_id``.

    Returns
    -------
    int
        Number of rows actually inserted (duplicates are silently skipped).
    """
    if not entries:
        return 0
    client = _get_client()
    rows = [{"user_id": e["user_id"], "job_id": e["job_id"]} for e in entries]
    result = (
        client.table("user_job_queue")
        .upsert(rows, on_conflict="user_id,job_id", ignore_duplicates=True)
        .execute()
    )
    return len(result.data)


# ── Digest delivery ──────────────────────────────────────────────────────────


def fetch_digest_recipients(today_weekday: int) -> list[dict]:
    """Return users who should receive a digest today.

    Parameters
    ----------
    today_weekday : int
        ISO weekday (1 = Monday … 7 = Sunday).

    Returns
    -------
    list[dict]
        Each dict has keys ``user_id`` (str) and ``email`` (str).
    """
    client = _get_client()
    result = (
        client.table("user_preferences")
        .select(
            "user_id, delivery_days, "
            "profiles!inner(email, subscription_status)"
        )
        .in_("profiles.subscription_status", ["active", "trialing"])
        .contains("delivery_days", [today_weekday])
        .execute()
    )
    recipients = []
    for row in result.data:
        email = row.get("profiles", {}).get("email")
        if email:
            recipients.append({"user_id": row["user_id"], "email": email})
    return recipients


def fetch_unsent_jobs_for_user(user_id: str) -> list[dict]:
    """Return all queued-but-unsent jobs for a user, with full job details.

    Returns a list of dicts with keys: id, title, company, url, source.
    """
    client = _get_client()
    result = (
        client.table("user_job_queue")
        .select("job_id, jobs(id, title, company, url, source)")
        .eq("user_id", user_id)
        .is_("sent_at", "null")
        .execute()
    )
    # Flatten the nested jobs object
    jobs = []
    for row in result.data:
        job = row.get("jobs")
        if job:
            jobs.append(job)
    return jobs


def mark_queue_sent(user_id: str, job_ids: list[str]):
    """Set sent_at = now() for the given user + job_id combinations."""
    if not job_ids:
        return
    client = _get_client()
    now = datetime.now(timezone.utc).isoformat()
    (
        client.table("user_job_queue")
        .update({"sent_at": now})
        .eq("user_id", user_id)
        .in_("job_id", job_ids)
        .is_("sent_at", "null")
        .execute()
    )
