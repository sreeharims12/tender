import os
import json
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

test_cases = [
    "AMC Tender Notification",
    "Submission of Bid for the Annual Maintenance Contract (AMC) of 13KVA Legrand Numeric UPS installed at upper basement floor at Carmel Towers, Vazhuthacaud",
    "Govt. Polytechnic College, Palakkad,- Short Tender notice-For buying Air Conditioner for Principal Room, Software Lab, CAD lab, General Library",
    "Selection of an End-to-End Custom Development, Implementation and Maintenance of Web Application and Citizen Portal"
]

for title in test_cases:
    prompt = f"""You are a strict procurement classifier for an IT/Software Tender Monitor.
Your objective is to identify ONLY IT and Software-related tenders (software development, web/mobile apps, cloud, APIs, ERP, data analytics, cybersecurity, or IT/software maintenance).
Electrical goods, HVAC, air conditioning, UPS/inverters/batteries, civil works, or general facility maintenance MUST be classified as FALSE.

Tender: "{title}"

Return ONLY a JSON object:
{{"is_it_related": bool, "relevance_score": float, "matched_keywords": list, "reason": str}}
"""
    try:
        resp = client.models.generate_content(model="gemini-3.5-flash-lite", contents=prompt)
        print("TENDER:", title[:60])
        print("RESPONSE:", resp.text.strip())
        print("-" * 50)
    except Exception as e:
        print("Error on", title[:30], ":", e)
