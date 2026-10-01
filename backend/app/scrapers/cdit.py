import re
import urllib.parse
from typing import List, Dict, Any
import httpx
from bs4 import BeautifulSoup

from backend.app.scrapers.base import BaseScraper
from backend.app.classifier import classify_tender


class CDITScraper(BaseScraper):
    source_name = "C-DIT"
    source_url = "https://cdit.kerala.gov.in/?page_id=2538"

    def scrape(self) -> List[Dict[str, Any]]:
        tenders = []
        base_domain = "https://cdit.kerala.gov.in"

        try:
            with httpx.Client(verify=False, timeout=12.0, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(self.source_url)
                if resp.status_code != 200:
                    return tenders

                soup = BeautifulSoup(resp.text, "html.parser")
                tables = soup.find_all("table")
                if not tables:
                    return tenders

                # Table 0 contains main tenders
                main_table = tables[0]
                rows = main_table.find_all("tr")
                for row in rows[1:]:  # Skip header row
                    cells = row.find_all(["td", "th"])
                    if len(cells) < 3:
                        continue

                    pub_date = self.clean_text(cells[0].text)
                    particulars = self.clean_text(cells[1].text)
                    if not particulars:
                        continue

                    last_date = self.clean_text(cells[2].text) if len(cells) > 2 else ""

                    # Extract details / PDF link
                    doc_url = None
                    if len(cells) >= 4:
                        link_tag = cells[3].find("a")
                        if link_tag and link_tag.get("href"):
                            doc_url = urllib.parse.urljoin(base_domain, link_tag.get("href"))

                    # Extract Tender Reference / Number
                    tender_ref = None
                    ref_match = re.search(r"Tender\s*(?:No\.?|Notice\s*No\.?)\s*[:\-]?\s*([^\s\n,]+(?:\s+[^\s\n,]+){0,2})", particulars, re.IGNORECASE)
                    if ref_match:
                        tender_ref = ref_match.group(1).strip()

                    # Extract Title / Description
                    desc_match = re.search(r"Description\s*:\s*([^.\n]+)", particulars, re.IGNORECASE)
                    if desc_match:
                        title = desc_match.group(1).strip()
                    else:
                        title = particulars[:180]

                    classification = classify_tender(
                        title=title,
                        description=particulars,
                        organisation="Centre for Development of Imaging Technology (C-DIT)",
                        category="Media & Imaging Technology",
                    )


                    tenders.append({
                        "title": title,
                        "organisation": "Centre for Development of Imaging Technology (C-DIT)",
                        "source_name": self.source_name,
                        "source_url": self.source_url,
                        "tender_url": doc_url or self.source_url,
                        "document_url": doc_url,
                        "tender_reference": tender_ref,
                        "tender_id": tender_ref,
                        "category": "Electronics & IT Services",
                        "description": particulars,
                        "published_date": pub_date,
                        "closing_date": last_date,
                        "location": "Thiruvananthapuram, Kerala",
                        "estimated_value": None,
                        "tender_type": "Tender / Quotation",
                        "is_it_related": classification["is_it_related"],
                        "relevance_score": classification["relevance_score"],
                        "matched_keywords": classification["matched_keywords"],
                    })

        except Exception as e:
            print(f"[CDITScraper] Error: {e}")

        return tenders
