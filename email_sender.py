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
    "platsbanken": "Platsbanken",
    "wes": "Wes",
    "stardust": "Stardust Search",
    "academicsearch": "Academic Search",
    "signpost": "Signpost",
    "inhouse": "Inhouse",
    "peopleprovide": "PeopleProvide",
    "futurevalue_rekrytering": "Future Value Rekrytering",
    "futurevalue_interim": "Future Value Interim",
    "avanti": "Avanti Rekrytering",
    "pooliaexecutive": "Poolia Executive",
    "nigel_wright": "Nigel Wright",
    "gazella": "Gazella",
    "alumni": "Alumni",
    "properpeople": "Proper People",
    "jobway": "Jobway",
    "beyondretail": "Beyond Retail",
    "bonesvirik": "Bønes Virik",
    "visindi": "Visindi",
    "vindex": "Vindex",
    "executive": "Executive",
    "cip": "CIP Search",
    "trib": "Trib",
    "mesh": "Mesh People",
    "brightpeople": "Bright People",
    "bondi": "Bondi",
    "basedonpeople": "Based on People",
    "bohmans": "Bohmans Bätverk",
    "addpeople": "AddPeople",
    "compasshrg": "Compass HRG",
    "levelrecruitment": "Level Recruitment",
    "performiq": "PerformIQ",
    "safemind": "SafeMind",
    "hays": "Hays",
    "people360": "People 360",
    "hudsonnordic": "Hudson Nordic",
    "humancapital": "Human Capital",
    "kornferry_interim": "Korn Ferry Interim",
    "kornferry": "Korn Ferry",
    "mercuriurval": "Mercuri Urval",
    "needo": "Needo",
    "andpartners": "&Partners",
}

# ── Brand colours ────────────────────────────────────────────────────────────
_BG = "#0F1219"           # deep navy background
_CARD_BG = "#161D2A"      # slightly lighter card surface
_BORDER = "#1F2738"       # subtle border
_GOLD = "#D4A044"         # primary gold accent
_GOLD_LIGHT = "#E5C266"   # lighter gold for gradients
_TEXT = "#EDEEE9"          # off-white primary text
_TEXT_MUTED = "#8A8D93"    # secondary / muted text
_LINK = "#D4A044"          # links use gold


def _build_html(jobs: list[dict]) -> str:
    """Build a premium branded HTML digest email."""
    by_source: dict[str, list[dict]] = {}
    for job in jobs:
        by_source.setdefault(job["source"], []).append(job)

    today = date.today().strftime("%d %b %Y")
    count = len(jobs)

    # ── Outer wrapper (dark background, centered) ────────────────────────
    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:{_BG};font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;">

<!-- Outer wrapper -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{_BG};">
<tr><td align="center" style="padding:24px 16px;">

<!-- Inner container (max 600px) -->
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

<!-- ═══ HEADER ═══ -->
<tr><td style="padding:32px 32px 24px;text-align:center;">
  <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto;">
  <tr>
    <td style="font-size:11px;font-weight:700;letter-spacing:3px;color:{_GOLD};font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;text-transform:uppercase;">
      &#9678; NORDIC EXECUTIVE LIST
    </td>
  </tr>
  </table>
</td></tr>

<!-- ═══ DIVIDER ═══ -->
<tr><td style="padding:0 32px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr><td style="border-top:1px solid {_BORDER};font-size:0;line-height:0;">&nbsp;</td></tr>
  </table>
</td></tr>

<!-- ═══ HEADLINE ═══ -->
<tr><td style="padding:28px 32px 8px;text-align:center;">
  <h1 style="margin:0;font-size:26px;font-weight:400;color:{_TEXT};font-family:Georgia,'Times New Roman',serif;line-height:1.3;">
    Your Daily Executive Briefing
  </h1>
</td></tr>
<tr><td style="padding:0 32px 28px;text-align:center;">
  <span style="display:inline-block;background-color:{_CARD_BG};border:1px solid {_BORDER};border-radius:20px;padding:6px 18px;font-size:13px;color:{_GOLD};letter-spacing:0.3px;">
    {count} new position{"s" if count != 1 else ""} &middot; {today}
  </span>
</td></tr>
"""

    # ── Job cards grouped by source (Platsbanken always last) ───────────
    sorted_sources = sorted(by_source.keys(), key=lambda s: (s == "platsbanken", s))
    for source in sorted_sources:
        source_jobs = by_source[source]
        label = SOURCE_LABELS.get(source, source.replace("_", " ").title())

        html += f"""\
<!-- Source: {label} -->
<tr><td style="padding:0 24px 4px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{_CARD_BG};border:1px solid {_BORDER};border-radius:8px;">

  <!-- Source header -->
  <tr><td style="padding:16px 20px 8px;">
    <table role="presentation" cellpadding="0" cellspacing="0"><tr>
      <td style="font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:{_TEXT_MUTED};">
        {label}
      </td>
      <td style="padding-left:10px;">
        <span style="display:inline-block;background-color:{_BORDER};border-radius:10px;padding:2px 8px;font-size:10px;color:{_TEXT_MUTED};">
          {len(source_jobs)}
        </span>
      </td>
    </tr></table>
  </td></tr>
"""

        for job in source_jobs:
            company = job.get("company", "")
            company_str = (
                f'<span style="color:{_TEXT_MUTED};font-weight:400;"> &mdash; {company}</span>'
                if company and company != label
                else ""
            )
            html += f"""\
  <!-- Job row -->
  <tr><td style="padding:6px 20px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td style="width:6px;vertical-align:top;padding-top:8px;">
        <div style="width:4px;height:4px;border-radius:2px;background-color:{_GOLD};"></div>
      </td>
      <td style="padding:2px 0 2px 10px;">
        <a href="{job["url"]}" style="color:{_TEXT};font-size:14px;font-weight:500;text-decoration:none;line-height:1.4;" target="_blank">{job["title"]}</a>
        {company_str}
      </td>
    </tr>
    </table>
  </td></tr>
"""

        html += """\
  <!-- Card bottom padding -->
  <tr><td style="padding:0 0 14px;"></td></tr>
  </table>
</td></tr>

<!-- Spacer between cards -->
<tr><td style="padding:0 0 8px;"></td></tr>
"""

    # ── CTA Button ───────────────────────────────────────────────────────
    html += f"""\
<!-- ═══ CTA ═══ -->
<tr><td style="padding:20px 32px 8px;text-align:center;">
  <a href="https://nordicexecutivelist.com/dashboard" style="display:inline-block;background:linear-gradient(135deg,{_GOLD},{_GOLD_LIGHT});color:{_BG};font-size:14px;font-weight:600;text-decoration:none;padding:12px 32px;border-radius:6px;letter-spacing:0.3px;" target="_blank">
    View on Dashboard
  </a>
</td></tr>

<!-- ═══ SECONDARY LINK ═══ -->
<tr><td style="padding:14px 32px 4px;text-align:center;">
  <span style="font-size:12px;color:{_TEXT_MUTED};">
    Not the right roles?&ensp;
    <a href="https://nordicexecutivelist.com/preferences" style="color:{_GOLD};text-decoration:underline;" target="_blank">Adjust preferences</a>
  </span>
</td></tr>

<!-- ═══ FOOTER DIVIDER ═══ -->
<tr><td style="padding:24px 32px 0;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr><td style="border-top:1px solid {_BORDER};font-size:0;line-height:0;">&nbsp;</td></tr>
  </table>
</td></tr>

<!-- ═══ FOOTER ═══ -->
<tr><td style="padding:20px 32px 32px;text-align:center;">
  <p style="margin:0 0 4px;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:{_TEXT_MUTED};font-weight:600;">
    Nordic Executive List
  </p>
  <p style="margin:0;font-size:11px;color:{_TEXT_MUTED};line-height:1.6;">
    Your personalized executive job digest
  </p>
</td></tr>

</table><!-- /inner container -->
</td></tr>
</table><!-- /outer wrapper -->
</body>
</html>
"""
    return html


def _build_empty_html() -> str:
    """Build a branded 'no new matches today' email."""
    today = date.today().strftime("%d %b %Y")
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:{_BG};font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;">

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{_BG};">
<tr><td align="center" style="padding:24px 16px;">

<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">

<!-- ═══ HEADER ═══ -->
<tr><td style="padding:32px 32px 24px;text-align:center;">
  <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto;">
  <tr>
    <td style="font-size:11px;font-weight:700;letter-spacing:3px;color:{_GOLD};font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;text-transform:uppercase;">
      &#9678; NORDIC EXECUTIVE LIST
    </td>
  </tr>
  </table>
</td></tr>

<!-- ═══ DIVIDER ═══ -->
<tr><td style="padding:0 32px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr><td style="border-top:1px solid {_BORDER};font-size:0;line-height:0;">&nbsp;</td></tr>
  </table>
</td></tr>

<!-- ═══ HEADLINE ═══ -->
<tr><td style="padding:28px 32px 8px;text-align:center;">
  <h1 style="margin:0;font-size:26px;font-weight:400;color:{_TEXT};font-family:Georgia,'Times New Roman',serif;line-height:1.3;">
    Your Daily Executive Briefing
  </h1>
</td></tr>
<tr><td style="padding:0 32px 28px;text-align:center;">
  <span style="display:inline-block;background-color:{_CARD_BG};border:1px solid {_BORDER};border-radius:20px;padding:6px 18px;font-size:13px;color:{_TEXT_MUTED};letter-spacing:0.3px;">
    {today}
  </span>
</td></tr>

<!-- ═══ EMPTY STATE ═══ -->
<tr><td style="padding:0 24px 12px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{_CARD_BG};border:1px solid {_BORDER};border-radius:8px;">
  <tr><td style="padding:32px 28px;text-align:center;">
    <p style="margin:0 0 12px;font-size:28px;line-height:1;">&#9734;</p>
    <p style="margin:0 0 8px;font-size:16px;color:{_TEXT};font-family:Georgia,'Times New Roman',serif;line-height:1.5;">
      A quiet day on the executive front.
    </p>
    <p style="margin:0;font-size:14px;color:{_TEXT_MUTED};line-height:1.5;">
      No new positions matched your criteria today.<br/>
      We&rsquo;ll be back tomorrow &mdash; fingers crossed!
    </p>
  </td></tr>
  </table>
</td></tr>

<!-- ═══ SECONDARY LINK ═══ -->
<tr><td style="padding:20px 32px 4px;text-align:center;">
  <span style="font-size:12px;color:{_TEXT_MUTED};">
    Want to see more roles?&ensp;
    <a href="https://nordicexecutivelist.com/preferences" style="color:{_GOLD};text-decoration:underline;" target="_blank">Broaden your preferences</a>
  </span>
</td></tr>

<!-- ═══ FOOTER DIVIDER ═══ -->
<tr><td style="padding:24px 32px 0;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr><td style="border-top:1px solid {_BORDER};font-size:0;line-height:0;">&nbsp;</td></tr>
  </table>
</td></tr>

<!-- ═══ FOOTER ═══ -->
<tr><td style="padding:20px 32px 32px;text-align:center;">
  <p style="margin:0 0 4px;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:{_TEXT_MUTED};font-weight:600;">
    Nordic Executive List
  </p>
  <p style="margin:0;font-size:11px;color:{_TEXT_MUTED};line-height:1.6;">
    Your personalized executive job digest
  </p>
</td></tr>

</table>
</td></tr>
</table>
</body>
</html>
"""


def send_digest(jobs: list[dict], recipient_email: str) -> bool:
    """Send an HTML digest email to a single user via SendGrid.

    Returns True on success, False on failure (so the caller can decide
    whether to mark the queue entries as sent).
    """

    api_key = os.environ.get("SENDGRID_API_KEY")
    if not api_key:
        print("[ERROR] SENDGRID_API_KEY environment variable not set.")
        return False

    from_email = os.environ.get("SENDGRID_FROM_EMAIL", "noreply@nordicexecutivelist.com")
    today = date.today().strftime("%d %b %Y")

    if jobs:
        subject = f"Your Executive Briefing — {today} ({len(jobs)} new)"
        html = _build_html(jobs)
    else:
        subject = f"Your Executive Briefing — {today}"
        html = _build_empty_html()

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
