import urllib.parse
from typing import List, Dict, Any
import httpx
from bs4 import BeautifulSoup

from backend.app.scrapers.base import BaseScraper
from backend.app.classifier import classify_tender


class IndustriesScraper(BaseScraper):
    source_name = "Directorate of Industries & Commerce"
    source_url = "https://www.industry.kerala.gov.in/index.php/tender"

    def scrape(self) -> List[Dict[str, Any]]:
        tenders = []
        base_domain = "https://www.industry.kerala.gov.in"

        try:
            with httpx.Client(verify=False, timeout=12.0, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(self.source_url)
                if resp.status_code != 200:
                    return tenders

                soup = BeautifulSoup(resp.text, "html.parser")
                table = soup.find("table")
                if not table:
                    return tenders

                rows = table.find_all("tr")
                for row in rows[1:]:  # Skip header
                    cells = row.find_all(["td", "th"])
                    if len(cells) < 3:
                        continue

                    pub_date = self.clean_text(cells[0].text)
                    description = self.clean_text(cells[1].text)
                    if not description:
                        continue

                    closing_date = self.clean_text(cells[2].text) if len(cells) > 2 else ""

                    doc_url = None
                    if len(cells) >= 4:
                        a_tag = cells[3].find("a")
                        if a_tag and a_tag.get("href"):
                            doc_url = urllib.parse.urljoin(base_domain, a_tag.get("href"))

                    classification = classify_tender(
                        title=description,
                        description=description,
                        organisation="Directorate of Industries & Commerce, Kerala",
                        category="Commerce & Industry",
                    )

                    tenders.append({
                        "title": description,
                        "organisation": "Directorate of Industries & Commerce",
                        "source_name": self.source_name,
                        "source_url": self.source_url,
                        "tender_url": doc_url or self.source_url,
                        "document_url": doc_url,
                        "tender_reference": None,
                        "tender_id": None,
                        "category": "Government Procurement",
                        "description": description,
                        "published_date": pub_date,
                        "closing_date": closing_date,
                        "location": "Kerala",
                        "estimated_value": None,
                        "tender_type": "Quotation / Tender",
                        "is_it_related": classification["is_it_related"],
                        "relevance_score": classification["relevance_score"],
                        "matched_keywords": classification["matched_keywords"],
                    })

        except Exception as e:
            print(f"[IndustriesScraper] Error: {e}")

        return tenders
