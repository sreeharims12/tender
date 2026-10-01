import urllib.parse
from typing import List, Dict, Any
import httpx
from bs4 import BeautifulSoup

from backend.app.scrapers.base import BaseScraper
from backend.app.classifier import classify_tender


class KDISCScraper(BaseScraper):
    source_name = "K-DISC"
    source_url = "https://kdisc.kerala.gov.in/en/latest/"

    def scrape(self) -> List[Dict[str, Any]]:
        tenders = []
        base_domain = "https://kdisc.kerala.gov.in"

        try:
            with httpx.Client(verify=False, timeout=10.0, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(self.source_url)
                if resp.status_code != 200:
                    return tenders

                soup = BeautifulSoup(resp.text, "html.parser")
                matched_links = []
                for a in soup.find_all("a", href=True):
                    txt = self.clean_text(a.text)
                    href = a["href"]
                    combined = (txt + " " + href).lower()
                    if any(term in combined for term in ["tender", "bid", "eoi", "quotation", "rfp", "procurement"]):
                        if len(txt) > 5 and not any(skip in txt.lower() for skip in ["etenders.kerala.gov.in", "read more", "home", "contact"]):
                            matched_links.append((txt, href))

                seen_urls = set()
                for title, href in matched_links[:30]:  # Keep responsive
                    full_url = urllib.parse.urljoin(base_domain, href)
                    if full_url in seen_urls:
                        continue
                    seen_urls.add(full_url)

                    doc_url = full_url if full_url.lower().endswith(".pdf") else None

                    classification = classify_tender(
                        title=title,
                        description=f"Kerala Development and Innovation Strategic Council (K-DISC): {title}",
                        organisation="K-DISC (Kerala Development and Innovation Strategic Council)",
                        category="Innovation & Strategic Technology",
                    )

                    tenders.append({
                        "title": title,
                        "organisation": "K-DISC (Kerala Development and Innovation Strategic Council)",
                        "source_name": self.source_name,
                        "source_url": self.source_url,
                        "tender_url": full_url,
                        "document_url": doc_url,
                        "tender_reference": None,
                        "tender_id": None,
                        "category": "Technology & Innovation",
                        "description": f"K-DISC Tender Notice: {title}",
                        "published_date": None,
                        "closing_date": None,
                        "location": "Thiruvananthapuram, Kerala",
                        "estimated_value": None,
                        "tender_type": "Tender / EOI",
                        "is_it_related": classification["is_it_related"],
                        "relevance_score": classification["relevance_score"],
                        "matched_keywords": classification["matched_keywords"],
                    })

        except Exception as e:
            print(f"[KDISCScraper] Error: {e}")

        return tenders
