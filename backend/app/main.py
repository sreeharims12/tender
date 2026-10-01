import os
import sys
import json
from typing import Optional
from datetime import datetime

# Automatically configure sys.path so commands work from workspace root OR inside backend/
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(BACKEND_DIR)

for p in [ROOT_DIR, BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

try:
    from backend.app.database import engine, Base, get_db
    from backend.app.models import Tender
    from backend.app.schemas import (
        TenderOut,
        TenderListResponse,
        ScraperStatusResponse,
        DashboardStatsResponse,
    )
    from backend.app.scraper_manager import scraper_manager
except ImportError:
    from app.database import engine, Base, get_db
    from app.models import Tender
    from app.schemas import (
        TenderOut,
        TenderListResponse,
        ScraperStatusResponse,
        DashboardStatsResponse,
    )
    from app.scraper_manager import scraper_manager


# Ensure SQLite schema is created
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Kerala IT Tender Monitoring System API",
    version="1.0.0",
    description="Backend API for scraping, classifying, and monitoring Kerala Government IT Tenders",
)

# Enable CORS for React frontend (Vite default ports)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_tenders = db.query(Tender).count()
    it_tenders = db.query(Tender).filter(Tender.is_it_related == True).count()
    
    # New tenders in the current/last scraping cycle
    status = scraper_manager.get_status()
    new_tenders = status.get("new_tenders", 0)

    # Last scrape timestamp: prioritize the actual scraper execution time
    if getattr(scraper_manager, "last_scrape_time", None):
        last_scrape = scraper_manager.last_scrape_time
    elif status.get("completed_at"):
        parts = status["completed_at"].split()
        last_scrape = f"{parts[-2]} {parts[-1]}" if len(parts) >= 2 else status["completed_at"]
    else:
        latest_tender = db.query(Tender).order_by(desc(Tender.scraped_at)).first()
        if latest_tender and latest_tender.scraped_at:
            last_scrape = latest_tender.scraped_at.strftime("%I:%M %p")
        else:
            last_scrape = datetime.now().strftime("%I:%M %p")


    return DashboardStatsResponse(
        total_tenders=total_tenders,
        it_tenders=it_tenders,
        new_tenders=new_tenders,
        last_scrape=last_scrape,
    )


@app.get("/api/sources")
def get_sources_and_organisations(db: Session = Depends(get_db)):
    sources = [s[0] for s in db.query(Tender.source_name).distinct().all() if s[0]]
    organisations = [o[0] for o in db.query(Tender.organisation).distinct().all() if o[0]]
    categories = [c[0] for c in db.query(Tender.category).distinct().all() if c[0]]
    return {
        "sources": sorted(sources),
        "organisations": sorted(organisations),
        "categories": sorted(categories),
    }


@app.get("/api/tenders", response_model=TenderListResponse)
def get_tenders(
    search: Optional[str] = Query(None, description="Search across title, organisation, and description"),
    source: Optional[str] = Query(None, description="Filter by source name"),
    organisation: Optional[str] = Query(None, description="Filter by publishing organisation"),
    category: Optional[str] = Query(None, description="Filter by tender category"),
    it_only: bool = Query(True, description="Filter by IT-related tenders only (default: True)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(15, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("scraped_at", description="Sort column (scraped_at, relevance_score, closing_date, title)"),
    sort_order: str = Query("desc", description="Sort direction (asc, desc)"),
    db: Session = Depends(get_db),
):
    query = db.query(Tender)

    # IT Related filter
    if it_only:
        query = query.filter(Tender.is_it_related == True)

    # Search filter
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Tender.title.ilike(search_pattern),
                Tender.organisation.ilike(search_pattern),
                Tender.description.ilike(search_pattern),
                Tender.tender_reference.ilike(search_pattern),
            )
        )

    # Source filter
    if source and source != "All Sources":
        query = query.filter(Tender.source_name == source)

    # Organisation filter
    if organisation and organisation != "All Organisations":
        query = query.filter(Tender.organisation == organisation)

    # Category filter
    if category and category != "All Categories":
        query = query.filter(Tender.category == category)

    total = query.count()

    # Sorting
    sort_col = getattr(Tender, sort_by, Tender.scraped_at)
    if sort_order.lower() == "asc":
        query = query.order_by(asc(sort_col))
    else:
        query = query.order_by(desc(sort_col))

    # Pagination
    offset = (page - 1) * page_size
    records = query.offset(offset).limit(page_size).all()

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    # Convert matched_keywords JSON string to list
    items = []
    for r in records:
        kw_list = []
        if r.matched_keywords:
            try:
                kw_list = json.loads(r.matched_keywords)
            except Exception:
                kw_list = []

        item_dict = {
            "id": r.id,
            "title": r.title,
            "organisation": r.organisation,
            "source_name": r.source_name,
            "source_url": r.source_url,
            "tender_url": r.tender_url,
            "document_url": r.document_url,
            "tender_reference": r.tender_reference,
            "tender_id": r.tender_id,
            "category": r.category,
            "description": r.description,
            "published_date": r.published_date,
            "closing_date": r.closing_date,
            "location": r.location,
            "estimated_value": r.estimated_value,
            "tender_type": r.tender_type,
            "is_it_related": r.is_it_related,
            "relevance_score": r.relevance_score,
            "matched_keywords": kw_list,
            "scraped_at": r.scraped_at,
        }
        items.append(TenderOut(**item_dict))

    return TenderListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items,
    )


@app.get("/api/tenders/{tender_id}", response_model=TenderOut)
def get_tender_detail(tender_id: int, db: Session = Depends(get_db)):
    r = db.query(Tender).filter(Tender.id == tender_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Tender not found")

    kw_list = []
    if r.matched_keywords:
        try:
            kw_list = json.loads(r.matched_keywords)
        except Exception:
            kw_list = []

    return TenderOut(
        id=r.id,
        title=r.title,
        organisation=r.organisation,
        source_name=r.source_name,
        source_url=r.source_url,
        tender_url=r.tender_url,
        document_url=r.document_url,
        tender_reference=r.tender_reference,
        tender_id=r.tender_id,
        category=r.category,
        description=r.description,
        published_date=r.published_date,
        closing_date=r.closing_date,
        location=r.location,
        estimated_value=r.estimated_value,
        tender_type=r.tender_type,
        is_it_related=r.is_it_related,
        relevance_score=r.relevance_score,
        matched_keywords=kw_list,
        scraped_at=r.scraped_at,
    )


@app.post("/api/scrape", response_model=ScraperStatusResponse)
async def trigger_scraper():
    status = await scraper_manager.start_scraping()
    return ScraperStatusResponse(**status)


@app.get("/api/scrape/status", response_model=ScraperStatusResponse)
def get_scraper_status():
    status = scraper_manager.get_status()
    return ScraperStatusResponse(**status)


# Mount built frontend dist for seamless single-port web app access
import os
from fastapi.staticfiles import StaticFiles

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")

if os.path.exists(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

