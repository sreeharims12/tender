#!/usr/bin/env python3
"""
Kerala IT Tender Monitoring System - Daily Automated Job
Runs all scrapers, deduplicates and classifies tenders, generates a daily
email digest of relevant IT tenders, and sends it via the Brevo API.
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Configure sys.path so imports work seamlessly from any directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")

for p in [BASE_DIR, BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Load environment variables (.env files if present)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BACKEND_DIR, ".env"))
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass

# Import core modules
try:
    from backend.app.database import engine, Base
    from backend.app.scraper_manager import scraper_manager
    from backend.app.email_service import generate_email_content, send_email_via_brevo
except ImportError:
    from app.database import engine, Base
    from app.scraper_manager import scraper_manager
    from app.email_service import generate_email_content, send_email_via_brevo

# Configure clean, high-visibility console logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("daily_job")


def run_daily_monitor(dry_run: bool = False, include_existing: bool = False) -> int:
    """
    Main execution workflow for the daily automated tender monitoring job.
    Returns 0 on success, 1 on failure.
    """
    try:
        # Ensure SQLite database schema exists
        Base.metadata.create_all(bind=engine)

        print("Starting daily tender monitoring...\n")

        # 1. Run all scrapers through the pipeline with deduplication and classification
        summary = scraper_manager.run_sync_pipeline(
            log_fn=print,
            include_existing_if_none=include_existing
        )

        total_scraped = summary.get("tenders_found", 0)
        duplicates = summary.get("duplicates", 0)
        relevant_tenders = summary.get("relevant_it_tenders", [])
        relevant_count = len(relevant_tenders)

        # 2. Output consolidated summary in requested log format
        print("--------------------------------------------------")
        print(f"Total tenders scraped: {total_scraped}")
        print(f"Duplicates removed: {duplicates}")
        print(f"Relevant IT tenders: {relevant_count}")
        print("--------------------------------------------------\n")

        # 3. Generate email report (plain text and responsive HTML)
        print("Generating email...")
        email_data = generate_email_content(
            relevant_tenders=relevant_tenders,
            report_date=datetime.now().strftime("%d %b %Y"),
            stats=summary
        )
        print("Email generated successfully.\n")

        # 4. Send email via Brevo API
        if dry_run:
            print("[DRY RUN] Skipping actual Brevo email delivery.")
            print(f"[DRY RUN] Subject: {email_data['subject']}")
            print(f"[DRY RUN] Plain-text preview:\n{email_data['text'][:400]}...")
        else:
            print("Sending email...")
            send_email_via_brevo(
                subject=email_data["subject"],
                html_content=email_data["html"],
                text_content=email_data["text"]
            )
            print("Email sent successfully.\n")

        print("Daily tender monitoring completed.")
        return 0

    except Exception as exc:
        print(f"\n[CRITICAL ERROR] Daily monitoring job failed: {str(exc)}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Run daily Kerala IT tender monitoring, classification, and email notification."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute scraping and report generation without sending email via Brevo."
    )
    parser.add_argument(
        "--include-existing",
        action="store_true",
        help="If no new IT tenders are found today, include currently active IT tenders in report."
    )

    args = parser.parse_args()
    exit_code = run_daily_monitor(
        dry_run=args.dry_run,
        include_existing=args.include_existing
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
