"""
Per-user email digest delivery via the SendGrid API.

Env vars required:
    SENDGRID_API_KEY      – SendGrid API key
    SENDGRID_FROM_EMAIL   – verified sender (default: noreply@nordicexecutivelist.com)
"""

import os
from datetime import date
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

# ── Source display names ─────────────────────────────────────────────────────

SOURCE_LABELS = {
    "capa": "CAPA",
    "interimsearch": "Interim Search",
    "wise": "Wise",
    "headagent": "Head Agent",
    "michaelberglund": "Michael Berglund",
    "mason": "Mason",
    "hammerhanborg": "Hammer & Hanborg",
    "novare": "Novare",
    "platsbanken": "Platsbanken (Arbetsförmedlingen)",
}


def _build_html(jobs: list[dict]) -> str:
    """Build the HTML body for a digest email."""
    # Group by source
    by_source: dict[str, list[dict]] = {}
    for job in jobs:
        by_source.setdefault(job["source"], []).append(job)

    today = date.today().strftime("%d %b %Y")

    parts = [
        '<html><body style="font-family: Arial, sans-serif; '
        'max-width: 700px; margin: auto; color: #333;">',
        f'<h2 style="color:#1a1a2e;">📋 Job Digest — {today}</h2>',
        f"<p>{len(jobs)} new matching position(s).</p>",
        "<hr>",
    ]

    for source, source_jobs in by_source.items():
        label = SOURCE_LABELS.get(source, source.title())
        parts.append(
            f'<h3 style="color:#444; border-bottom:1px solid #ddd; '
            f'padding-bottom:4px;">{label}</h3><ul>'
        )
        for job in source_jobs:
            company_str = (
                f" — {job['company']}"
                if job.get("company") and job["company"] != label
                else ""
            )
            parts.append(
                f'<li style="margin-bottom:8px;">'
                f'<a href="{job["url"]}" style="color:#0057b8; '
                f'font-weight:bold;">{job["title"]}</a>'
                f"{company_str}"
                f"</li>"
            )
        parts.append("</ul>")

    parts.append(
        "<hr>"
        '<p style="font-size:12px;color:#999;">'
        "Nordic Executive List · your personalized job digest"
        "</p>"
        "</body></html>"
    )
    return "".join(parts)


def send_digest(jobs: list[dict], recipient_email: str) -> bool:
    """Send an HTML digest email to a single user via SendGrid.

    Returns True on success, False on failure (so the caller can decide
    whether to mark the queue entries as sent).
    """
    if not jobs:
        return False

    api_key = os.environ.get("SENDGRID_API_KEY")
    if not api_key:
        print("[ERROR] SENDGRID_API_KEY environment variable not set.")
        return False

    from_email = os.environ.get("SENDGRID_FROM_EMAIL", "noreply@nordicexecutivelist.com")
    today = date.today().strftime("%d %b %Y")
    subject = f"📋 Job Digest — {today} ({len(jobs)} new)"

    html = _build_html(jobs)

    message = Mail(
        from_email=Email(from_email, "Nordic Executive List"),
        to_emails=To(recipient_email),
        subject=subject,
        html_content=Content("text/html", html),
    )

    try:
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        if response.status_code in (200, 201, 202):
            return True
        print(
            f"[WARN] SendGrid returned {response.status_code} "
            f"for {recipient_email}"
        )
        return False
    except Exception as e:
        print(f"[ERROR] SendGrid failed for {recipient_email}: {e}")
        return False
