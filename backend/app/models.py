import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Index
try:
    from backend.app.database import Base
except ImportError:
    from app.database import Base



class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(Text, nullable=False, index=True)
    organisation = Column(String(255), nullable=True, index=True)
    source_name = Column(String(100), nullable=False, index=True)
    source_url = Column(Text, nullable=False)
    tender_url = Column(Text, nullable=True)
    document_url = Column(Text, nullable=True)
    tender_reference = Column(String(255), nullable=True, index=True)
    tender_id = Column(String(255), nullable=True, index=True)
    category = Column(String(255), nullable=True, index=True)
    description = Column(Text, nullable=True)
    published_date = Column(String(100), nullable=True, index=True)
    closing_date = Column(String(100), nullable=True, index=True)
    location = Column(String(255), nullable=True)
    estimated_value = Column(String(100), nullable=True)
    tender_type = Column(String(100), nullable=True)
    is_it_related = Column(Boolean, default=False, index=True)
    relevance_score = Column(Float, default=0.0, index=True)
    matched_keywords = Column(Text, nullable=True)  # JSON-encoded string
    scraped_at = Column(DateTime, default=datetime.now, index=True)
    dedup_hash = Column(String(64), nullable=True, unique=True, index=True)
    is_emailed = Column(Boolean, default=False, index=True)
    emailed_at = Column(DateTime, nullable=True, index=True)

    @property
    def keywords_list(self):
        if not self.matched_keywords:
            return []
        try:
            return json.loads(self.matched_keywords)
        except Exception:
            return []


def ensure_table_schema(db_engine):
    """
    Safely adds is_emailed and emailed_at columns to an existing SQLite table
    if they do not already exist.
    """
    from sqlalchemy import text
    with db_engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE tenders ADD COLUMN is_emailed BOOLEAN DEFAULT 0"))
            conn.commit()
        except Exception:
            pass

        try:
            conn.execute(text("ALTER TABLE tenders ADD COLUMN emailed_at DATETIME"))
            conn.commit()
        except Exception:
            pass

