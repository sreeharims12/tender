import urllib.request
import json
import sys

base_fastapi = "http://127.0.0.1:8000"
base_vite = "http://localhost:5173"

def fetch_json(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

print("=== 1. Testing Dashboard Stats ===")
stats = fetch_json(f"{base_fastapi}/api/stats")
print(f"Total Tenders: {stats['total_tenders']}")
print(f"IT Tenders: {stats['it_tenders']}")
print(f"New Tenders: {stats['new_tenders']}")
print(f"Last Scrape: {stats['last_scrape']}")

print("\n=== 2. Testing Sources & Organisations ===")
sources = fetch_json(f"{base_fastapi}/api/sources")
print(f"Sources ({len(sources['sources'])}): {sources['sources']}")
print(f"Organisations ({len(sources['organisations'])}): {sources['organisations'][:5]}...")

print("\n=== 3. Testing IT Tenders List (Default) ===")
it_list = fetch_json(f"{base_fastapi}/api/tenders?it_only=true&page=1&page_size=5")
print(f"IT Tenders count: {it_list['total']}, Returned on page 1: {len(it_list['items'])}")
sample = it_list["items"][0]
print(f"Sample IT Tender #{sample['id']}: {sample['title'][:65]}")
print(f"  Relevance Score: {sample['relevance_score']} | Matched Keywords: {sample['matched_keywords']}")

print("\n=== 4. Testing All Tenders List ===")
all_list = fetch_json(f"{base_fastapi}/api/tenders?it_only=false&page=1&page_size=5")
print(f"All Tenders total: {all_list['total']}")

print("\n=== 5. Testing Search Query: software ===")
search_res = fetch_json(f"{base_fastapi}/api/tenders?search=software&page=1&page_size=5")
print(f"Search matches for 'software': {search_res['total']}")
for it in search_res["items"][:3]:
    print(f"  - [{it['source_name']}] {it['title'][:70]}")

print("\n=== 6. Testing Tender Detail by ID ===")
detail = fetch_json(f"{base_fastapi}/api/tenders/{sample['id']}")
print(f"Detail Title: {detail['title'][:65]}")
print(f"Organisation: {detail['organisation']}")
print(f"Source Portal: {detail['source_name']} -> {detail['source_url']}")
print(f"Tender URL: {detail['tender_url']}")
print(f"Document / PDF URL: {detail['document_url']}")

print("\n=== 7. Testing Frontend Proxy on Vite (port 5173) ===")
vite_stats = fetch_json(f"{base_vite}/api/stats")
print(f"Vite Proxy connected successfully! Stats: {vite_stats}")

print("\n=== ALL 7 SYSTEM TESTS PASSED PERFECTLY! ===")
