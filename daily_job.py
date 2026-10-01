#!/usr/bin/env python3
"""
Kerala IT Tender Monitoring System - Daily Automated Job
Runs all scrapers, deduplicates and classifies tenders, generates a daily
email digest of relevant IT tenders, and sends it via direct Gmail SMTP (or Brevo).
Stamps emailed tenders in SQLite so already-sent tenders are NEVER repeated.
"""

import os
import sys
import time
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
    from backend.app.models import ensure_table_schema
    from backend.app.scraper_manager import scraper_manager
    from backend.app.email_service import generate_email_content, send_email
except ImportError:
    from app.database import engine, Base
    from app.models import ensure_table_schema
    from app.scraper_manager import scraper_manager
    from app.email_service import generate_email_content, send_email

# Configure clean, high-visibility console logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("daily_job")


def run_single_cycle(dry_run: bool = False, include_existing: bool = False, cycle_label: str = "") -> int:
    """
    Executes a single scrape -> deduplicate -> classify -> email cycle.
    Marks sent tenders as is_emailed = True so they are never repeated in future emails.
    """
    label_prefix = f"[{cycle_label}] " if cycle_label else ""
    print(f"\n{label_prefix}Starting tender monitoring cycle...\n")

    summary = scraper_manager.run_sync_pipeline(
        log_fn=print,
        include_existing_if_none=include_existing
    )

    total_scraped = summary.get("tenders_found", 0)
    duplicates = summary.get("duplicates", 0)
    relevant_tenders = summary.get("relevant_it_tenders", [])
    relevant_count = len(relevant_tenders)

    print("--------------------------------------------------")
    print(f"Total tenders scraped: {total_scraped}")
    print(f"Duplicates removed: {duplicates}")
    print(f"New Relevant IT tenders: {relevant_count}")
    print("--------------------------------------------------\n")

    print("Generating email...")
    email_data = generate_email_content(
        relevant_tenders=relevant_tenders,
        report_date=datetime.now().strftime("%d %b %Y"),
        stats=summary
    )
    print("Email generated successfully.\n")

    tender_ids = [t["id"] for t in relevant_tenders if t.get("id")]

    if dry_run:
        print("[DRY RUN] Skipping actual email delivery.")
        print(f"[DRY RUN] Subject: {email_data['subject']}")
        print(f"[DRY RUN] Plain-text preview:\n{email_data['text'][:400]}...")
    else:
        print("Sending email...")
        send_email(
            subject=email_data["subject"],
            html_content=email_data["html"],
            text_content=email_data["text"]
        )
        print("Email sent successfully.\n")

        # Mark sent tenders in SQLite database so they will NEVER be emailed again!
        if tender_ids:
            scraper_manager.mark_tenders_as_emailed(tender_ids)
            print(f"Marked {len(tender_ids)} tenders as sent in database.")

    print(f"{label_prefix}Tender monitoring cycle completed.")
    return 0


def run_daily_monitor(
    dry_run: bool = False,
    include_existing: bool = False,
    test_two_runs: bool = False,
    delay_seconds: int = 300,
) -> int:
    """
    Main entry point supporting standard single-run monitoring or
    a 2-run test cycle with 5-minute gap.
    """
    try:
        # Ensure SQLite database schema and new columns exist
        Base.metadata.create_all(bind=engine)
        ensure_table_schema(engine)

        if test_two_runs:
            print("============================================================")
            print("Starting 2-Run Test Cycle with 5-Minute Gap")
            print("Run #1 will email active tenders & mark them as sent.")
            print("Run #2 will verify that no duplicate tenders are emailed.")
            print("============================================================\n")

            # Run 1:
            ret1 = run_single_cycle(dry_run=dry_run, include_existing=include_existing, cycle_label="RUN 1/2")
            if ret1 != 0:
                return ret1

            # Wait delay_seconds (default 300 = 5 minutes)
            print("\n============================================================")
            print(f"Run #1 complete! Waiting {delay_seconds} seconds (5 minutes) before Run #2...")
            print("============================================================")

            remaining = delay_seconds
            while remaining > 0:
                mins, secs = divmod(remaining, 60)
                print(f"Countdown: {mins:02d}m {secs:02d}s remaining until Run #2...", end="\r", flush=True)
                step = min(15, remaining)
                time.sleep(step)
                remaining -= step

            print("\nCountdown complete! Launching Run #2...\n")

            # Run 2: (include_existing=False to strictly test sent tender exclusion)
            ret2 = run_single_cycle(dry_run=dry_run, include_existing=False, cycle_label="RUN 2/2")
            if ret2 != 0:
                return ret2

            print("\n============================================================")
            print("Two-run test cycle completed successfully! Halting workflow.")
            print("============================================================\n")
            return 0
        else:
            return run_single_cycle(dry_run=dry_run, include_existing=include_existing)

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
        help="Execute scraping and report generation without sending email via Brevo/Gmail."
    )
    parser.add_argument(
        "--include-existing",
        action="store_true",
        help="Include currently active unnotified tenders even if previously seen."
    )
    parser.add_argument(
        "--test-two-runs",
        action="store_true",
        help="Execute Run #1, wait 5 minutes, execute Run #2 to test deduplication, then halt."
    )
    parser.add_argument(
        "--delay-seconds",
        type=int,
        default=300,
        help="Delay in seconds between Run #1 and Run #2 in test mode (default: 300)."
    )

    args = parser.parse_args()
    exit_code = run_daily_monitor(
        dry_run=args.dry_run,
        include_existing=args.include_existing,
        test_two_runs=args.test_two_runs,
        delay_seconds=args.delay_seconds,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
