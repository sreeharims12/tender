import urllib.parse
from typing import List, Dict, Any
import httpx
from bs4 import BeautifulSoup

from backend.app.scrapers.base import BaseScraper
from backend.app.classifier import classify_tender


class ETendersKeralaScraper(BaseScraper):
    source_name = "Kerala e-Procurement Portal"
    source_url = "https://etenders.kerala.gov.in/nicgep/app"

    # Prioritize IT, Electronics, Education, and Tech-heavy organizations for fast & focused scraping
    PRIORITY_KEYWORDS = [
        "information technology", "it mission", "electronics", "keltron", "kdisc",
        "industrial training", "university", "science and technology", "police",
        "health", "transport", "sidco", "industr", "cochin", "calicut"
    ]

    def scrape(self) -> List[Dict[str, Any]]:
        tenders = []
        base_domain = "https://etenders.kerala.gov.in"
        org_page_url = f"{base_domain}/nicgep/app?page=FrontEndTendersByOrganisation&service=page"

        try:
            with httpx.Client(verify=False, timeout=15.0, headers=self.headers, follow_redirects=True) as client:
                # Step 1: Open public organisations page
                resp = client.get(org_page_url)
                if resp.status_code != 200:
                    return tenders

                soup = BeautifulSoup(resp.text, "html.parser")
                table = soup.find("table", {"id": "table"}) or soup.find("table", {"class": "list_table"})
                if not table:
                    return tenders

                org_links = []
                for row in table.find_all("tr"):
                    cols = [self.clean_text(c.text) for c in row.find_all(["td", "th"]) if self.clean_text(c.text)]
                    links = [a.get("href") for a in row.find_all("a") if a.get("href")]
                    if len(cols) >= 3 and links:
                        org_name = cols[1]
                        count_str = cols[2]
                        try:
                            count = int(count_str)
                        except ValueError:
                            count = 0
                        
                        if count > 0:
                            org_lower = org_name.lower()
                            is_priority = any(k in org_lower for k in self.PRIORITY_KEYWORDS)
                            org_links.append((org_name, count, links[0], is_priority))

                # Sort priority orgs first and limit to top 15 orgs per run for responsive performance
                org_links.sort(key=lambda x: (not x[3], -x[1]))
                target_orgs = org_links[:15]

                for org_name, count, href, _ in target_orgs:
                    try:
                        org_url = urllib.parse.urljoin(base_domain, href)
                        org_resp = client.get(org_url)
                        if org_resp.status_code != 200:
                            continue
                        
                        # Respect CAPTCHA check: if the page requires captcha, skip it
                        if "enter captcha" in org_resp.text.lower() and "refresh" in org_resp.text.lower() and not ("list_table" in org_resp.text):
                            continue

                        org_soup = BeautifulSoup(org_resp.text, "html.parser")
                        tender_table = org_soup.find("table", {"id": "table"}) or org_soup.find("table", {"class": "list_table"})
                        if not tender_table:
                            continue

                        for t_row in tender_table.find_all("tr"):
                            tds = [self.clean_text(c.text) for c in t_row.find_all(["td", "th"]) if self.clean_text(c.text)]
                            a_tag = t_row.find("a")
                            if not a_tag or len(tds) < 3:
                                continue

                            raw_title = self.clean_text(a_tag.text).strip("[]")
                            if not raw_title or "screen reader access" in raw_title.lower():
                                continue

                            tender_rel_url = a_tag.get("href")
                            full_tender_url = urllib.parse.urljoin(base_domain, tender_rel_url) if tender_rel_url else self.source_url

                            pub_date = tds[1] if len(tds) > 1 else ""
                            close_date = tds[2] if len(tds) > 2 else ""

                            # Classify IT relevance
                            classification = classify_tender(
                                title=raw_title,
                                organisation=org_name,
                                category="Government Procurement",
                            )

                            tenders.append({
                                "title": raw_title,
                                "organisation": org_name,
                                "source_name": self.source_name,
                                "source_url": self.source_url,
                                "tender_url": full_tender_url,
                                "document_url": None,
                                "tender_reference": None,
                                "tender_id": None,
                                "category": "General Goods & Services",
                                "description": f"Tender published by {org_name}. Details: {raw_title}",
                                "published_date": pub_date,
                                "closing_date": close_date,
                                "location": "Kerala",
                                "estimated_value": None,
                                "tender_type": "Open Tender",
                                "is_it_related": classification["is_it_related"],
                                "relevance_score": classification["relevance_score"],
                                "matched_keywords": classification["matched_keywords"],
                            })
                    except Exception:
                        continue

        except Exception as e:
            print(f"[ETendersKeralaScraper] Error: {e}")

        return tenders
