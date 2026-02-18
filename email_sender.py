import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date
from config import EMAIL_SENDER, EMAIL_RECIPIENT, EMAIL_SUBJECT


def send_digest(jobs: list[dict]):
    if not jobs:
        print("[INFO] No new matching jobs today. No email sent.")
        return

    password = os.environ.get("GMAIL_APP_PASSWORD")
    if not password:
        raise ValueError("GMAIL_APP_PASSWORD environment variable not set.")

    # Group by source
    by_source = {}
    for job in jobs:
        by_source.setdefault(job["source"], []).append(job)

    # Build HTML
    today = date.today().strftime("%d %b %Y")
    html_parts = [f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 700px; margin: auto; color: #333;">
    <h2 style="color:#1a1a2e;">📋 Job Digest — {today}</h2>
    <p>{len(jobs)} new matching position(s) found today.</p>
    <hr>
    """]

    source_labels = {
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

    for source, source_jobs in by_source.items():
        label = source_labels.get(source, source.title())
        html_parts.append(f'<h3 style="color:#444; border-bottom:1px solid #ddd; padding-bottom:4px;">{label}</h3><ul>')
        for job in source_jobs:
            company_str = f" — {job['company']}" if job.get("company") and job["company"] != label else ""
            html_parts.append(
                f'<li style="margin-bottom:8px;">'
                f'<a href="{job["url"]}" style="color:#0057b8; font-weight:bold;">{job["title"]}</a>'
                f'{company_str}'
                f'</li>'
            )
        html_parts.append("</ul>")

    html_parts.append("<hr><p style='font-size:12px;color:#999;'>Job Monitor · runs daily via GitHub Actions</p></body></html>")
    html = "".join(html_parts)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{EMAIL_SUBJECT} — {today} ({len(jobs)} new)"
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECIPIENT
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, password)
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())

    print(f"[INFO] Email sent with {len(jobs)} jobs.")
