import re
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger("date_utils")

try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None


def parse_closing_datetime(closing_str: Optional[str]) -> Optional[datetime]:
    """
    Robustly parses various Indian Government tender closing/deadline date formats into a datetime object.
    Supports formats like:
      - '08-Oct-2026 06:00 PM'
      - '29-06-2026'
      - '11.08.2025 at 05.00 pm'
      - '02.03.2023 at 02.00 p.m.'
      - '05.10.2026, 3.00 PM.'
      - '2026-10-15 17:00:00'
    """
    if not closing_str:
        return None

    clean = str(closing_str).strip()
    if clean.lower() in ["none", "null", "not specified", "n/a", "", "tender reference number"]:
        return None

    # Clean up punctuation and spacing around am/pm
    clean = clean.rstrip(".")
    clean = re.sub(r"\bat\b", " ", clean, flags=re.IGNORECASE)
    clean = clean.replace(",", " ")
    clean = re.sub(r"p\.\s*m\.?", "PM", clean, flags=re.IGNORECASE)
    clean = re.sub(r"a\.\s*m\.?", "AM", clean, flags=re.IGNORECASE)
    # Replace dots in times like 05.00 PM -> 05:00 PM
    clean = re.sub(r"(\d+)\s*\.\s*(\d{2})\s*(am|pm)", r"\1:\2 \3", clean, flags=re.IGNORECASE)
    # Normalize spaces
    clean = re.sub(r"\s+", " ", clean).strip()

    # Try python-dateutil first if available
    if date_parser:
        try:
            dt = date_parser.parse(clean, dayfirst=True, fuzzy=True)
            # If no time was specified in string, assume end of the day (23:59:59)
            if "AM" not in clean.upper() and "PM" not in clean.upper() and ":" not in clean:
                dt = dt.replace(hour=23, minute=59, second=59)
            return dt
        except Exception:
            pass

    # Standard fallback patterns
    formats = [
        "%d-%b-%Y %I:%M %p",
        "%d-%b-%Y %H:%M",
        "%d-%b-%Y",
        "%d-%m-%Y %I:%M %p",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y",
        "%d.%m.%Y %I:%M %p",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y",
        "%d/%m/%Y %I:%M %p",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(clean, fmt)
            if "%H" not in fmt and "%I" not in fmt:
                dt = dt.replace(hour=23, minute=59, second=59)
            return dt
        except ValueError:
            continue

    return None


def is_tender_active(closing_str: Optional[str], pub_str: Optional[str] = None) -> bool:
    """
    Determines whether a tender is currently active (not expired).
    - If closing_date is present and valid: checks if closing_datetime >= now.
    - If closing_date is missing: checks published_date (expires after 60 days).
    - If neither date is valid: returns False to prevent emailing stale records.
    """
    now = datetime.now()
    closing_dt = parse_closing_datetime(closing_str)

    if closing_dt:
        return closing_dt >= now

    # If closing date is completely absent or unspecified, fallback to publication date
    if pub_str:
        pub_dt = parse_closing_datetime(pub_str)
        if pub_dt:
            # Tenders without a closing date published over 60 days ago are considered expired
            return (now - pub_dt).days <= 60

    return False
