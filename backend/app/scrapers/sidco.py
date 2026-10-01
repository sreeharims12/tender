import urllib.parse
from typing import List, Dict, Any
import httpx
from bs4 import BeautifulSoup

from backend.app.scrapers.base import BaseScraper
from backend.app.classifier import classify_tender


class SidcoScraper(BaseScraper):
    source_name = "Kerala SIDCO"
    source_url = "https://www.keralasidco.com/"

    def scrape(self) -> List[Dict[str, Any]]:
        tenders = []
        base_domain = "https://etenders.kerala.gov.in"
        org_page_url = f"{base_domain}/nicgep/app?page=FrontEndTendersByOrganisation&service=page"

        try:
            with httpx.Client(verify=False, timeout=12.0, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(org_page_url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    table = soup.find("table", {"id": "table"}) or soup.find("table", {"class": "list_table"})
                    if table:
                        sidco_link = None
                        for row in table.find_all("tr"):
                            row_text = row.text.lower()
                            if "sidco" in row_text or "small industries development corporation" in row_text:
                                a = row.find("a")
                                if a and a.get("href"):
                                    sidco_link = a["href"]
                                    break

                        if sidco_link:
                            full_url = urllib.parse.urljoin(base_domain, sidco_link)
                            resp2 = client.get(full_url)
                            if resp2.status_code == 200 and not ("enter captcha" in resp2.text.lower() and not "list_table" in resp2.text):
                                soup2 = BeautifulSoup(resp2.text, "html.parser")
                                t2 = soup2.find("table", {"id": "table"}) or soup2.find("table", {"class": "list_table"})
                                if t2:
                                    for t_row in t2.find_all("tr"):
                                        tds = [self.clean_text(c.text) for c in t_row.find_all(["td", "th"]) if self.clean_text(c.text)]
                                        a_tag = t_row.find("a")
                                        if not a_tag or len(tds) < 3:
                                            continue

                                        raw_title = self.clean_text(a_tag.text).strip("[]")
                                        if not raw_title or "screen reader access" in raw_title.lower():
                                            continue

                                        pub_date = tds[1] if len(tds) > 1 else ""
                                        close_date = tds[2] if len(tds) > 2 else ""

                                        classification = classify_tender(
                                            title=raw_title,
                                            organisation="Kerala SIDCO",
                                            category="Small Industries Development",
                                        )

                                        tenders.append({
                                            "title": raw_title,
                                            "organisation": "Kerala SIDCO (Small Industries Development Corporation)",
                                            "source_name": self.source_name,
                                            "source_url": self.source_url,
                                            "tender_url": urllib.parse.urljoin(base_domain, a_tag.get("href")),
                                            "document_url": None,
                                            "tender_reference": None,
                                            "tender_id": None,
                                            "category": "Industrial & Goods",
                                            "description": f"Kerala SIDCO Tender: {raw_title}",
                                            "published_date": pub_date,
                                            "closing_date": close_date,
                                            "location": "Kerala",
                                            "estimated_value": None,
                                            "tender_type": "Open Tender",
                                            "is_it_related": classification["is_it_related"],
                                            "relevance_score": classification["relevance_score"],
                                            "matched_keywords": classification["matched_keywords"],
                                        })
        except Exception as e:
            print(f"[SidcoScraper] Error: {e}")

        return tenders
