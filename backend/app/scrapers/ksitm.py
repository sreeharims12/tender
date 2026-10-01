import urllib.parse
from typing import List, Dict, Any
import httpx
from bs4 import BeautifulSoup

from backend.app.scrapers.base import BaseScraper
from backend.app.classifier import classify_tender
from backend.app.pdf_extractor import extract_text_from_pdf_url


class KSITMScraper(BaseScraper):
    source_name = "Kerala State IT Mission (KSITM)"
    source_url = "https://itmission.kerala.gov.in/tenders"

    def scrape(self) -> List[Dict[str, Any]]:
        tenders = []
        base_domain = "https://itmission.kerala.gov.in"

        try:
            with httpx.Client(verify=False, timeout=10.0, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(self.source_url)
                if resp.status_code != 200:
                    return tenders

                soup = BeautifulSoup(resp.text, "html.parser")
                table = soup.find("table")
                if not table:
                    return tenders

                rows = table.find_all("tr")
                for row in rows[1:]:  # Skip header row
                    cells = row.find_all(["td", "th"])
                    if len(cells) < 3:
                        continue

                    details_cell = cells[1]
                    title = self.clean_text(details_cell.text)
                    if not title:
                        continue

                    tender_link = details_cell.find("a")
                    tender_url = urllib.parse.urljoin(base_domain, tender_link.get("href")) if tender_link else self.source_url

                    last_date = self.clean_text(cells[2].text)

                    doc_url = None
                    if len(cells) >= 4:
                        doc_link = cells[3].find("a")
                        if doc_link and doc_link.get("href"):
                            doc_url = urllib.parse.urljoin(base_domain, doc_link.get("href"))

                    # Quick preliminary classification
                    classification = classify_tender(
                        title=title,
                        description=title,
                        organisation="Kerala State Information Technology Mission (KSITM)",
                        category="Information Technology",
                    )

                    # Only inspect PDF if borderline and doc is available
                    if not classification["is_it_related"] and doc_url and doc_url.lower().endswith(".pdf"):
                        # Short timeout to avoid stalling
                        pdf_text = extract_text_from_pdf_url(doc_url, max_pages=1, timeout_sec=2.0)
                        if pdf_text:
                            classification = classify_tender(
                                title=title,
                                description=title,
                                organisation="Kerala State Information Technology Mission (KSITM)",
                                category="Information Technology",
                                pdf_text=pdf_text,
                            )

                    tenders.append({
                        "title": title,
                        "organisation": "Kerala State IT Mission (KSITM)",
                        "source_name": self.source_name,
                        "source_url": self.source_url,
                        "tender_url": tender_url,
                        "document_url": doc_url,
                        "tender_reference": None,
                        "tender_id": None,
                        "category": "IT & Telecom",
                        "description": f"KSITM Tender: {title}",
                        "published_date": None,
                        "closing_date": last_date,
                        "location": "Thiruvananthapuram, Kerala",
                        "estimated_value": None,
                        "tender_type": "Quotation / Tender",
                        "is_it_related": classification["is_it_related"],
                        "relevance_score": classification["relevance_score"],
                        "matched_keywords": classification["matched_keywords"],
                    })

        except Exception as e:
            print(f"[KSITMScraper] Error: {e}")

        return tenders
