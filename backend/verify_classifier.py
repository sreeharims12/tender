import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.classifier import classify_tender

tenders_to_test = [
    ("Govt. Polytechnic College, Palakkad,- Short Tender notice-For buying Air Conditioner for Principal Room, Software Lab, CAD lab, General Library", "Directorate of Industries & Commerce"),
    ("Submission of Bid for the Annual Maintenance Contract (AMC) of 13KVA Legrand Numeric UPS installed at upper basement floor at Carmel Towers, Vazhuthacaud", "K-DISC"),
    ("AMC Tender Notification", "K-DISC"),
    ("Software for COPA Trade", "Department of Industrial Training"),
    ("Selection of an End-to-End Custom Development, Implementation and Maintenance of Web Application and Citizen Portal", "Kerala e-Procurement Portal")
]

for title, org in tenders_to_test:
    res = classify_tender(title=title, description=title, organisation=org)
    print(f"TENDER: {title[:60]}")
    print(f"  -> IS_IT_RELATED: {res['is_it_related']}")
    print(f"  -> SCORE: {res['relevance_score']}")
    print(f"  -> KEYWORDS: {res['matched_keywords']}")
    print(f"  -> REASON: {res.get('reason')}")
    print("-" * 60)
