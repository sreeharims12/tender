from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TenderBase(BaseModel):
    title: str
    organisation: Optional[str] = None
    source_name: str
    source_url: str
    tender_url: Optional[str] = None
    document_url: Optional[str] = None
    tender_reference: Optional[str] = None
    tender_id: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    published_date: Optional[str] = None
    closing_date: Optional[str] = None
    location: Optional[str] = None
    estimated_value: Optional[str] = None
    tender_type: Optional[str] = None
    is_it_related: bool = False
    relevance_score: float = 0.0
    matched_keywords: List[str] = []


class TenderOut(TenderBase):
    id: int
    scraped_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TenderListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[TenderOut]


class ScraperStatusResponse(BaseModel):
    status: str  # "idle" | "running" | "completed" | "error"
    sources_checked: int = 0
    tenders_found: int = 0
    it_tenders: int = 0
    new_tenders: int = 0
    duplicates: int = 0
    errors: int = 0
    current_source: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    message: Optional[str] = None
    logs: List[str] = []


class DashboardStatsResponse(BaseModel):
    total_tenders: int
    it_tenders: int
    new_tenders: int
    last_scrape: str
