import os
import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import httpx

logger = logging.getLogger("email_service")


def format_tender_date(date_str: Optional[str]) -> str:
    if not date_str or date_str.strip().lower() in ["none", "null", ""]:
        return "Not specified"
    return date_str.strip()


def generate_email_content(
    relevant_tenders: List[Dict[str, Any]],
    report_date: Optional[str] = None,
    stats: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """
    Generates plain-text and HTML email content for the daily IT tender report.
    """
    if not report_date:
        report_date = datetime.now().strftime("%d %b %Y")

    total_count = len(relevant_tenders)
    subject = f"Kerala IT Tender Daily Report - {report_date}"

    # 1. Plain Text Version
    text_lines = [
        f"Subject: {subject}",
        "",
        "Hello,",
        "",
    ]

    if total_count == 0:
        text_lines.append("No new relevant IT/software tenders were found today (all previously found tenders were already notified).")
    else:
        text_lines.append(f"Here are the new relevant IT/software tenders discovered since your last report.\n\nTotal new relevant tenders: {total_count}")
        text_lines.append("\n" + "-" * 50 + "\n")

        for idx, t in enumerate(relevant_tenders, 1):
            title = t.get("title", "Untitled Tender")
            org = t.get("organisation") or "Not specified"
            ref = t.get("tender_reference") or t.get("tender_id") or "Not specified"
            pub_date = format_tender_date(t.get("published_date"))
            deadline = format_tender_date(t.get("closing_date"))
            source = t.get("source_name") or "Government Portal"
            tender_url = t.get("tender_url") or t.get("source_url") or "N/A"
            doc_url = t.get("document_url")

            text_lines.append(f"{idx}. {title}\n")
            text_lines.append(f"Organization: {org}")
            text_lines.append(f"Tender Reference: {ref}")
            text_lines.append(f"Published: {pub_date}")
            text_lines.append(f"Deadline: {deadline}")
            text_lines.append(f"Source: {source}\n")
            text_lines.append(f"Tender Link:\n{tender_url}")
            if doc_url:
                text_lines.append(f"Document / RFP Link:\n{doc_url}")
            text_lines.append("\n" + "-" * 50 + "\n")

    text_lines.extend([
        "",
        "Regards,",
        "Kerala IT Tender Monitoring System",
    ])
    text_content = "\n".join(text_lines)

    # 2. Modern HTML Version
    stats_html = ""
    if stats:
        sources_checked = stats.get("sources_checked", 6)
        total_scraped = stats.get("tenders_found", 0)
        duplicates = stats.get("duplicates", 0)
        stats_html = f"""
        <div style="background-color: #f1f5f9; border-radius: 8px; padding: 12px 16px; margin: 16px 0; font-size: 13px; color: #475569; display: flex; justify-content: space-between; flex-wrap: wrap;">
            <span><strong>Sources Scanned:</strong> {sources_checked}</span>
            <span>&bull;</span>
            <span><strong>Total Scraped:</strong> {total_scraped}</span>
            <span>&bull;</span>
            <span><strong>Duplicates Filtered:</strong> {duplicates}</span>
            <span>&bull;</span>
            <span><strong>New IT Tenders:</strong> <span style="color: #0284c7; font-weight: 700;">{total_count}</span></span>
        </div>
        """

    if total_count == 0:
        body_content = f"""
        <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 28px; text-align: center; margin-top: 20px;">
            <div style="font-size: 36px; margin-bottom: 12px;">✅</div>
            <h3 style="margin: 0 0 8px 0; color: #1e293b; font-size: 18px;">No new relevant IT/software tenders were found today.</h3>
            <p style="margin: 0; color: #64748b; font-size: 14px; line-height: 1.5;">
                All 6 monitored government portals were scanned. All non-IT tenders and previously notified tenders were filtered out.
            </p>
        </div>
        """
    else:
        cards = []
        for idx, t in enumerate(relevant_tenders, 1):
            title = t.get("title", "Untitled Tender")
            org = t.get("organisation") or "Not specified"
            ref = t.get("tender_reference") or t.get("tender_id") or "Not specified"
            pub_date = format_tender_date(t.get("published_date"))
            deadline = format_tender_date(t.get("closing_date"))
            source = t.get("source_name") or "Government Portal"
            tender_url = t.get("tender_url") or t.get("source_url") or "#"
            doc_url = t.get("document_url")

            # Matched keywords tags
            keywords = t.get("matched_keywords") or []
            if isinstance(keywords, str):
                import json
                try:
                    keywords = json.loads(keywords)
                except Exception:
                    keywords = []

            kw_tags_html = ""
            if keywords:
                tags = "".join([f'<span style="background-color: #e0f2fe; color: #0369a1; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; margin-right: 6px; display: inline-block;">{re.escape(k)}</span>' for k in keywords[:4]])
                kw_tags_html = f'<div style="margin-top: 10px;">{tags}</div>'

            doc_button_html = ""
            if doc_url:
                doc_button_html = f"""
                <a href="{doc_url}" style="background-color: #f8fafc; color: #334155; border: 1px solid #cbd5e1; text-decoration: none; padding: 8px 14px; border-radius: 6px; font-size: 13px; font-weight: 600; display: inline-block; margin-left: 8px;" target="_blank">
                    📄 View Notice / RFP
                </a>
                """

            card_html = f"""
            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 18px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                    <span style="background-color: #0284c7; color: #ffffff; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 12px; text-transform: uppercase;">
                        Tender #{idx}
                    </span>
                    <span style="background-color: #f1f5f9; color: #475569; font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px;">
                        {source}
                    </span>
                </div>
                <h3 style="margin: 8px 0 12px 0; color: #0f172a; font-size: 16px; line-height: 1.4;">
                    {title}
                </h3>
                
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 14px; font-size: 13px; color: #334155;">
                    <tr>
                        <td style="padding: 4px 0; width: 120px; color: #64748b; font-weight: 600;">Organization:</td>
                        <td style="padding: 4px 0;">{org}</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px 0; color: #64748b; font-weight: 600;">Reference:</td>
                        <td style="padding: 4px 0;"><code>{ref}</code></td>
                    </tr>
                    <tr>
                        <td style="padding: 4px 0; color: #64748b; font-weight: 600;">Published:</td>
                        <td style="padding: 4px 0;">{pub_date}</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px 0; color: #64748b; font-weight: 600;">Deadline:</td>
                        <td style="padding: 4px 0; color: #dc2626; font-weight: 600;">{deadline}</td>
                    </tr>
                </table>

                {kw_tags_html}

                <div style="margin-top: 14px; padding-top: 12px; border-top: 1px solid #f1f5f9;">
                    <a href="{tender_url}" style="background-color: #0284c7; color: #ffffff; text-decoration: none; padding: 8px 14px; border-radius: 6px; font-size: 13px; font-weight: 600; display: inline-block;" target="_blank">
                        🔗 Open Tender Portal
                    </a>
                    {doc_button_html}
                </div>
            </div>
            """
            cards.append(card_html)

        body_content = "".join(cards)

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px 12px; color: #1e293b;">
    <div style="max-width: 680px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 24px; color: #ffffff;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 11px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; background-color: #0284c7; padding: 3px 8px; border-radius: 4px;">
                    Daily Intelligence Report
                </span>
                <span style="font-size: 12px; color: #94a3b8;">
                    {report_date}
                </span>
            </div>
            <h1 style="margin: 12px 0 4px 0; font-size: 22px; font-weight: 700; letter-spacing: -0.02em;">
                Kerala IT Tender Daily Monitor
            </h1>
            <p style="margin: 0; font-size: 13px; color: #cbd5e1;">
                Automated Software &amp; IT Procurement Intelligence for Kerala Government Portals
            </p>
        </div>

        <!-- Content Area -->
        <div style="padding: 24px;">
            <p style="margin: 0 0 12px 0; font-size: 14px; color: #334155;">
                Hello,
            </p>
            <p style="margin: 0 0 16px 0; font-size: 14px; color: #334155;">
                {"Here are today's relevant IT/software tenders." if total_count > 0 else "The daily tender monitoring cycle has concluded."}
            </p>

            {stats_html}

            {body_content}
            
            <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 13px; color: #64748b;">
                Regards,<br>
                <strong style="color: #1e293b;">Kerala IT Tender Monitoring System</strong>
            </div>
        </div>

        <!-- Footer -->
        <div style="background-color: #f1f5f9; padding: 14px 24px; font-size: 11px; color: #64748b; text-align: center; border-top: 1px solid #e2e8f0;">
            This email was generated automatically by GitHub Actions using the Kerala IT Tender Monitoring System.<br>
            Sent directly via automated email notification.
        </div>
    </div>
</body>
</html>
"""

    return {
        "subject": subject,
        "text": text_content,
        "html": html_content,
        "total_count": str(total_count),
    }


def send_email_via_gmail_smtp(
    subject: str,
    html_content: str,
    text_content: str,
    to_email: Optional[str] = None,
    from_email: Optional[str] = None,
    app_password: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Sends email directly through Gmail SMTP server (smtp.gmail.com:587)
    using TLS and a Google App Password.
    Zero external website dependencies, zero IP block issues, lands straight in primary inbox.
    """
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.utils import formataddr

    from_email = from_email or os.getenv("EMAIL_FROM")
    to_email = to_email or os.getenv("EMAIL_TO")
    app_password = app_password or os.getenv("GMAIL_APP_PASSWORD") or os.getenv("SMTP_PASSWORD")

    missing = []
    if not from_email:
        missing.append("EMAIL_FROM")
    if not to_email:
        missing.append("EMAIL_TO")
    if not app_password:
        missing.append("GMAIL_APP_PASSWORD")

    if missing:
        raise ValueError(
            f"Missing required email configuration: {', '.join(missing)}. "
            "Please configure these as environment variables or GitHub Repository Secrets."
        )

    # Remove any spaces if user pasted 'abcd efgh ijkl mnop'
    clean_password = app_password.replace(" ", "").strip()
    clean_from = from_email.strip()
    recipients = [addr.strip() for addr in to_email.split(",") if addr.strip()]

    if not recipients:
        raise ValueError("No valid recipient email address specified in EMAIL_TO.")

    # Create MIME message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr(("Kerala IT Tender Monitor", clean_from))
    msg["To"] = ", ".join(recipients)

    part1 = MIMEText(text_content, "plain", "utf-8")
    part2 = MIMEText(html_content, "html", "utf-8")
    msg.attach(part1)
    msg.attach(part2)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30.0) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(clean_from, clean_password)
            server.sendmail(clean_from, recipients, msg.as_string())

        logger.info(f"Email sent successfully via Gmail SMTP to: {', '.join(recipients)}")
        return {"status": "success", "recipients": recipients, "provider": "gmail_smtp"}

    except smtplib.SMTPAuthenticationError as auth_err:
        err_detail = auth_err.smtp_error.decode("utf-8", errors="ignore") if hasattr(auth_err, "smtp_error") else str(auth_err)
        raise RuntimeError(
            "Gmail SMTP Authentication failed. Please verify that your GMAIL_APP_PASSWORD "
            "is the 16-character Google App Password generated from https://myaccount.google.com/apppasswords "
            f"(Error: {err_detail})"
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to send email via Gmail SMTP: {str(exc)}")


def send_email_via_brevo(
    subject: str,
    html_content: str,
    text_content: str,
    to_email: Optional[str] = None,
    from_email: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Sends transactional email using Brevo v3 API endpoint.
    Credentials are read from arguments or environment variables.
    """
    api_key = api_key or os.getenv("BREVO_API_KEY")
    to_email = to_email or os.getenv("EMAIL_TO")
    from_email = from_email or os.getenv("EMAIL_FROM")

    missing = []
    if not api_key:
        missing.append("BREVO_API_KEY")
    if not to_email:
        missing.append("EMAIL_TO")
    if not from_email:
        missing.append("EMAIL_FROM")

    if missing:
        raise ValueError(
            f"Missing required email configuration: {', '.join(missing)}. "
            "Please configure these as environment variables or GitHub Repository Secrets."
        )

    # Support multiple comma-separated recipients
    recipients = [{"email": addr.strip()} for addr in to_email.split(",") if addr.strip()]
    if not recipients:
        raise ValueError("No valid recipient email address specified in EMAIL_TO.")

    payload = {
        "sender": {
            "name": "Kerala IT Tender Monitor",
            "email": from_email.strip(),
        },
        "to": recipients,
        "subject": subject,
        "htmlContent": html_content,
        "textContent": text_content,
    }

    headers = {
        "accept": "application/json",
        "api-key": api_key.strip(),
        "content-type": "application/json",
    }

    url = "https://api.brevo.com/v3/smtp/email"

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code in [200, 201, 202]:
                data = resp.json()
                logger.info(f"Email sent successfully via Brevo. Message ID: {data.get('messageId')}")
                return data
            else:
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("message") or str(err_json)
                except Exception:
                    err_msg = resp.text[:200]
                raise RuntimeError(f"Brevo API error (HTTP {resp.status_code}): {err_msg}")
    except httpx.RequestError as exc:
        raise RuntimeError(f"Failed to connect to Brevo API: {exc}")


def send_email(
    subject: str,
    html_content: str,
    text_content: str,
    to_email: Optional[str] = None,
    from_email: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Sends email using direct Gmail SMTP (recommended) or Brevo API fallback.
    """
    if os.getenv("GMAIL_APP_PASSWORD") or os.getenv("SMTP_PASSWORD"):
        return send_email_via_gmail_smtp(subject, html_content, text_content, to_email, from_email)
    elif os.getenv("BREVO_API_KEY"):
        return send_email_via_brevo(subject, html_content, text_content, to_email, from_email)
    else:
        # Default to Gmail SMTP and validate credentials
        return send_email_via_gmail_smtp(subject, html_content, text_content, to_email, from_email)

