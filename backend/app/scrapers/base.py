import hashlib
import re
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class BaseScraper(ABC):
    source_name: str = ""
    source_url: str = ""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

    @abstractmethod
    def scrape(self) -> list[Dict[str, Any]]:
        """
        Scrapes tenders from this source and returns a list of normalized tender dicts.
        """
        pass

    @staticmethod
    def compute_dedup_hash(
        tender_id: Optional[str],
        tender_reference: Optional[str],
        tender_url: Optional[str],
        source: str,
        title: str,
        organisation: Optional[str],
        published_date: Optional[str],
    ) -> str:
        """
        Calculates unique deduplication key following priority:
        1. Tender ID
        2. Tender reference number
        3. Canonical tender URL
        4. Hash(source + title + organisation + published_date)
        """
        t_id = (tender_id or "").strip()
        if t_id:
            return f"tid_{hashlib.sha256(t_id.lower().encode('utf-8')).hexdigest()[:32]}"

        t_ref = (tender_reference or "").strip()
        if t_ref:
            return f"ref_{hashlib.sha256(t_ref.lower().encode('utf-8')).hexdigest()[:32]}"

        t_url = (tender_url or "").strip()
        if t_url:
            canonical_url = re.sub(r"[?&]session=[^&]+", "", t_url)
            return f"url_{hashlib.sha256(canonical_url.lower().encode('utf-8')).hexdigest()[:32]}"

        # Fallback hash
        payload = f"{source.strip().lower()}|{(title or '').strip().lower()}|{(organisation or '').strip().lower()}|{(published_date or '').strip().lower()}"
        return f"hash_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:32]}"

    @staticmethod
    def clean_text(text: Optional[str]) -> str:
        if not text:
            return ""
        # Remove extra whitespace and special unicode artifacts
        cleaned = re.sub(r"\s+", " ", text).strip()
        cleaned = cleaned.replace("\xa0", " ").strip()
        return cleaned
