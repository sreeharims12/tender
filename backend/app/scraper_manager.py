import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

try:
    from backend.app.database import SessionLocal
    from backend.app.models import Tender
    from backend.app.scrapers.base import BaseScraper
    from backend.app.scrapers.etenders_kerala import ETendersKeralaScraper
    from backend.app.scrapers.ksitm import KSITMScraper
    from backend.app.scrapers.cdit import CDITScraper
    from backend.app.scrapers.industries import IndustriesScraper
    from backend.app.scrapers.sidco import SidcoScraper
    from backend.app.scrapers.kdisc import KDISCScraper
    from backend.app.classifier import classify_tender
except ImportError:
    from app.database import SessionLocal
    from app.models import Tender
    from app.scrapers.base import BaseScraper
    from app.scrapers.etenders_kerala import ETendersKeralaScraper
    from app.scrapers.ksitm import KSITMScraper
    from app.scrapers.cdit import CDITScraper
    from app.scrapers.industries import IndustriesScraper
    from app.scrapers.sidco import SidcoScraper
    from app.scrapers.kdisc import KDISCScraper
    from app.classifier import classify_tender


logger = logging.getLogger("scraper_manager")

STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scraper_state.json")


def _load_persisted_state() -> Dict[str, Any]:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_persisted_state(data: Dict[str, Any]):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


class ScraperManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ScraperManager, cls).__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        persisted = _load_persisted_state()
        self.status: str = "idle"
        self.sources_checked: int = persisted.get("sources_checked", 0)
        self.tenders_found: int = persisted.get("tenders_found", 0)
        self.it_tenders: int = persisted.get("it_tenders", 0)
        self.new_tenders: int = persisted.get("new_tenders", 0)
        self.duplicates: int = persisted.get("duplicates", 0)
        self.errors: int = persisted.get("errors", 0)
        self.current_source: Optional[str] = None
        self.started_at: Optional[str] = persisted.get("started_at")
        self.completed_at: Optional[str] = persisted.get("completed_at")
        self.last_scrape_time: str = persisted.get("last_scrape_time", datetime.now().strftime("%I:%M %p"))
        self.message: Optional[str] = persisted.get("message", "Ready to scrape")
        self.logs: List[str] = []
        self._lock = asyncio.Lock()
        self._executor = ThreadPoolExecutor(max_workers=3)


    def log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {msg}"
        self.logs.append(entry)
        if len(self.logs) > 100:
            self.logs.pop(0)
        logger.info(entry)

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "sources_checked": self.sources_checked,
            "tenders_found": self.tenders_found,
            "it_tenders": self.it_tenders,
            "new_tenders": self.new_tenders,
            "duplicates": self.duplicates,
            "errors": self.errors,
            "current_source": self.current_source,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "message": self.message,
            "logs": list(self.logs),
        }

    async def start_scraping(self) -> Dict[str, Any]:
        if self.status == "running":
            return {"status": "running", "message": "Scraping is already in progress"}

        self.status = "running"
        self.sources_checked = 0
        self.tenders_found = 0
        self.it_tenders = 0
        self.new_tenders = 0
        self.duplicates = 0
        self.errors = 0
        self.current_source = None
        self.started_at = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        self.completed_at = None
        self.message = "Starting scraper cycle..."
        self.logs = []
        self.log("Scraping workflow initialized.")

        # Run task in background
        asyncio.create_task(self._run_all_scrapers())
        return self.get_status()

    async def _run_all_scrapers(self):
        scrapers: List[BaseScraper] = [
            ETendersKeralaScraper(),
            KSITMScraper(),
            CDITScraper(),
            IndustriesScraper(),
            SidcoScraper(),
            KDISCScraper(),
        ]

        loop = asyncio.get_running_loop()

        try:
            for scraper in scrapers:
                self.current_source = scraper.source_name
                self.message = f"Scraping {scraper.source_name}..."
                self.log(f"Fetching public tenders from: {scraper.source_name}...")

                try:
                    # Run scraper in threadpool to keep asyncio loop responsive
                    scraped_items = await loop.run_in_executor(self._executor, scraper.scrape)
                    self.sources_checked += 1
                    source_found = len(scraped_items)
                    self.tenders_found += source_found
                    self.log(f"Extracted {source_found} raw tenders from {scraper.source_name}.")

                    # Process items: Deduplicate & persist
                    await loop.run_in_executor(self._executor, self._process_items, scraped_items)

                except Exception as e:
                    self.errors += 1
                    self.log(f"Error scraping {scraper.source_name}: {str(e)}")

            now_dt = datetime.now()
            self.status = "completed"
            self.current_source = None
            self.completed_at = now_dt.strftime("%Y-%m-%d %I:%M:%S %p")
            self.last_scrape_time = now_dt.strftime("%I:%M %p")
            self.message = f"Scraping completed. Found {self.tenders_found} tenders ({self.it_tenders} software-related, {self.new_tenders} new, {self.duplicates} duplicates)."
            self.log(self.message)
            _save_persisted_state({
                "sources_checked": self.sources_checked,
                "tenders_found": self.tenders_found,
                "it_tenders": self.it_tenders,
                "new_tenders": self.new_tenders,
                "duplicates": self.duplicates,
                "errors": self.errors,
                "started_at": self.started_at,
                "completed_at": self.completed_at,
                "last_scrape_time": self.last_scrape_time,
                "message": self.message,
            })

        except Exception as e:
            self.status = "error"
            self.message = f"Scraper execution error: {str(e)}"
            self.log(f"Fatal error: {str(e)}")

    def _process_items(self, items: List[Dict[str, Any]]):
        db = SessionLocal()
        try:
            for item in items:
                # Deduplication key calculation
                dedup_hash = BaseScraper.compute_dedup_hash(
                    tender_id=item.get("tender_id"),
                    tender_reference=item.get("tender_reference"),
                    tender_url=item.get("tender_url"),
                    source=item["source_name"],
                    title=item["title"],
                    organisation=item.get("organisation"),
                    published_date=item.get("published_date"),
                )

                # Check if already exists in DB
                existing = db.query(Tender).filter(Tender.dedup_hash == dedup_hash).first()
                if existing:
                    self.duplicates += 1
                    existing.scraped_at = datetime.now()
                    continue

                # Ensure classification
                is_it = item.get("is_it_related", False)

                score = item.get("relevance_score", 0.0)
                matched_kws = item.get("matched_keywords", [])

                if not matched_kws and not is_it:
                    c = classify_tender(
                        title=item["title"],
                        description=item.get("description", ""),
                        organisation=item.get("organisation", ""),
                        category=item.get("category", ""),
                    )
                    is_it = c["is_it_related"]
                    score = c["relevance_score"]
                    matched_kws = c["matched_keywords"]

                if is_it:
                    self.it_tenders += 1

                tender_record = Tender(
                    title=item["title"],
                    organisation=item.get("organisation"),
                    source_name=item["source_name"],
                    source_url=item["source_url"],
                    tender_url=item.get("tender_url"),
                    document_url=item.get("document_url"),
                    tender_reference=item.get("tender_reference"),
                    tender_id=item.get("tender_id"),
                    category=item.get("category"),
                    description=item.get("description"),
                    published_date=item.get("published_date"),
                    closing_date=item.get("closing_date"),
                    location=item.get("location", "Kerala"),
                    estimated_value=item.get("estimated_value"),
                    tender_type=item.get("tender_type", "Open Tender"),
                    is_it_related=is_it,
                    relevance_score=score,
                    matched_keywords=json.dumps(matched_kws),
                    scraped_at=datetime.utcnow(),
                    dedup_hash=dedup_hash,
                )
                db.add(tender_record)
                db.commit()
                self.new_tenders += 1

        except Exception as e:
            db.rollback()
            self.errors += 1
            self.log(f"Database error during item processing: {str(e)}")
        finally:
            db.close()

    def run_sync_pipeline(self, log_fn=None, include_existing_if_none: bool = False) -> Dict[str, Any]:
        """
        Synchronously runs all configured scrapers, applies deduplication,
        runs classification, updates the database, and returns the metrics
        and list of collected relevant IT tenders.
        """
        def _emit_log(msg: str):
            if log_fn:
                log_fn(msg)
            else:
                self.log(msg)

        scrapers: List[BaseScraper] = [
            ETendersKeralaScraper(),
            KSITMScraper(),
            CDITScraper(),
            IndustriesScraper(),
            SidcoScraper(),
            KDISCScraper(),
        ]

        total_scraped = 0
        duplicates_count = 0
        new_tenders_count = 0
        errors_count = 0
        sources_checked = 0
        new_it_tenders: List[Dict[str, Any]] = []
        all_active_it_tenders: List[Dict[str, Any]] = []

        db = SessionLocal()
        try:
            for scraper in scrapers:
                sources_checked += 1
                _emit_log(f"Starting scraper: {scraper.source_name}")
                try:
                    scraped_items = scraper.scrape()
                    count = len(scraped_items)
                    total_scraped += count
                    _emit_log(f"Completed scraper: {scraper.source_name}")
                    _emit_log(f"Tenders found: {count}\n")
                except Exception as e:
                    errors_count += 1
                    _emit_log(f"Failed scraper {scraper.source_name}: {str(e)}\n")
                    continue

                for item in scraped_items:
                    dedup_hash = BaseScraper.compute_dedup_hash(
                        tender_id=item.get("tender_id"),
                        tender_reference=item.get("tender_reference"),
                        tender_url=item.get("tender_url"),
                        source=item["source_name"],
                        title=item["title"],
                        organisation=item.get("organisation"),
                        published_date=item.get("published_date"),
                    )

                    existing = db.query(Tender).filter(Tender.dedup_hash == dedup_hash).first()
                    if existing:
                        duplicates_count += 1
                        existing.scraped_at = datetime.utcnow()
                        if existing.is_it_related:
                            item_dict = {
                                "id": existing.id,
                                "title": existing.title,
                                "organisation": existing.organisation,
                                "source_name": existing.source_name,
                                "source_url": existing.source_url,
                                "tender_url": existing.tender_url,
                                "document_url": existing.document_url,
                                "tender_reference": existing.tender_reference,
                                "tender_id": existing.tender_id,
                                "category": existing.category,
                                "description": existing.description,
                                "published_date": existing.published_date,
                                "closing_date": existing.closing_date,
                                "is_it_related": True,
                                "is_emailed": bool(existing.is_emailed),
                                "relevance_score": existing.relevance_score,
                                "matched_keywords": existing.keywords_list,
                            }
                            all_active_it_tenders.append(item_dict)
                            # Only include if NEVER emailed before
                            if not existing.is_emailed:
                                new_it_tenders.append(item_dict)
                        continue

                    # New tender: ensure classification
                    is_it = item.get("is_it_related", False)
                    score = item.get("relevance_score", 0.0)
                    matched_kws = item.get("matched_keywords", [])

                    if not matched_kws and not is_it:
                        c = classify_tender(
                            title=item["title"],
                            description=item.get("description", ""),
                            organisation=item.get("organisation", ""),
                            category=item.get("category", ""),
                        )
                        is_it = c["is_it_related"]
                        score = c["relevance_score"]
                        matched_kws = c["matched_keywords"]

                    tender_record = Tender(
                        title=item["title"],
                        organisation=item.get("organisation"),
                        source_name=item["source_name"],
                        source_url=item["source_url"],
                        tender_url=item.get("tender_url"),
                        document_url=item.get("document_url"),
                        tender_reference=item.get("tender_reference"),
                        tender_id=item.get("tender_id"),
                        category=item.get("category"),
                        description=item.get("description"),
                        published_date=item.get("published_date"),
                        closing_date=item.get("closing_date"),
                        location=item.get("location", "Kerala"),
                        estimated_value=item.get("estimated_value"),
                        tender_type=item.get("tender_type", "Open Tender"),
                        is_it_related=is_it,
                        is_emailed=False,
                        relevance_score=score,
                        matched_keywords=json.dumps(matched_kws),
                        scraped_at=datetime.utcnow(),
                        dedup_hash=dedup_hash,
                    )
                    db.add(tender_record)
                    db.commit()
                    new_tenders_count += 1

                    tender_dict = {
                        "id": tender_record.id,
                        "title": item["title"],
                        "organisation": item.get("organisation"),
                        "source_name": item["source_name"],
                        "source_url": item["source_url"],
                        "tender_url": item.get("tender_url"),
                        "document_url": item.get("document_url"),
                        "tender_reference": item.get("tender_reference"),
                        "tender_id": item.get("tender_id"),
                        "category": item.get("category"),
                        "description": item.get("description"),
                        "published_date": item.get("published_date"),
                        "closing_date": item.get("closing_date"),
                        "is_it_related": is_it,
                        "is_emailed": False,
                        "relevance_score": score,
                        "matched_keywords": matched_kws,
                    }

                    if is_it:
                        new_it_tenders.append(tender_dict)
                        all_active_it_tenders.append(tender_dict)

            # Persist state for UI dashboard
            now_dt = datetime.now()
            self.sources_checked = sources_checked
            self.tenders_found = total_scraped
            self.it_tenders = len(all_active_it_tenders)
            self.new_tenders = new_tenders_count
            self.duplicates = duplicates_count
            self.errors = errors_count
            self.last_scrape_time = now_dt.strftime("%I:%M %p")
            _save_persisted_state({
                "sources_checked": self.sources_checked,
                "tenders_found": self.tenders_found,
                "it_tenders": self.it_tenders,
                "new_tenders": self.new_tenders,
                "duplicates": self.duplicates,
                "errors": self.errors,
                "last_scrape_time": self.last_scrape_time,
                "completed_at": now_dt.strftime("%Y-%m-%d %I:%M:%S %p"),
                "message": f"Scraping completed. Found {total_scraped} tenders ({self.it_tenders} software-related).",
            })

            # Relevant tenders are strictly those NOT yet emailed
            relevant = new_it_tenders
            if include_existing_if_none and len(new_it_tenders) == 0:
                relevant = all_active_it_tenders

            return {
                "sources_checked": sources_checked,
                "tenders_found": total_scraped,
                "duplicates": duplicates_count,
                "new_tenders": new_tenders_count,
                "relevant_it_tenders": relevant,
                "new_it_tenders": new_it_tenders,
                "all_active_it_tenders": all_active_it_tenders,
                "errors": errors_count,
            }

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def mark_tenders_as_emailed(self, tender_ids: List[int]):
        """
        Marks the specified tender IDs as emailed in the SQLite database
        so they will NEVER be included in any future email reports.
        """
        if not tender_ids:
            return
        db = SessionLocal()
        try:
            db.query(Tender).filter(Tender.id.in_(tender_ids)).update(
                {Tender.is_emailed: True, Tender.emailed_at: datetime.utcnow()},
                synchronize_session=False
            )
            db.commit()
            logger.info(f"Marked {len(tender_ids)} tenders as emailed in database.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking tenders as emailed: {e}")
        finally:
            db.close()


scraper_manager = ScraperManager()


