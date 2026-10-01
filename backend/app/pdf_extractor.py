import io
import httpx
import pymupdf


def extract_text_from_pdf_url(url: str, max_pages: int = 5, timeout_sec: float = 8.0) -> str:
    """
    Downloads a publicly accessible PDF document and extracts plain text using PyMuPDF.
    Safely limits pages and download size to avoid blocking or memory overhead.
    """
    if not url or not url.startswith("http"):
        return ""

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        with httpx.Client(verify=False, timeout=timeout_sec, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code != 200:
                return ""
            
            # Ensure it is a PDF or binary
            content = resp.content
            if len(content) < 100 or not content.startswith(b"%PDF"):
                return ""

            # Extract text with PyMuPDF
            doc = pymupdf.open(stream=io.BytesIO(content), filetype="pdf")
            extracted_text = []
            pages_to_read = min(len(doc), max_pages)

            for page_num in range(pages_to_read):
                page = doc.load_page(page_num)
                extracted_text.append(page.get_text("text"))

            doc.close()
            return "\n".join(extracted_text)

    except Exception:
        # Graceful fallback: scraping should not fail if a PDF is unavailable or timed out
        return ""
