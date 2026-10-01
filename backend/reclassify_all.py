import os
import sys
import json
import time

# Ensure unicode chars do not crash Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
for p in [ROOT_DIR, CURRENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)


from backend.app.database import SessionLocal
from backend.app.models import Tender
from backend.app.classifier import classify_tender

def reclassify_database():
    db = SessionLocal()
    try:
        tenders = db.query(Tender).all()
        total = len(tenders)
        print(f"Total tenders in database to reclassify: {total}")

        changed_to_false = 0
        retained_true = 0
        new_true = 0

        for i, t in enumerate(tenders, 1):
            old_is_it = t.is_it_related

            # Run new hybrid classifier (Tier 1 high-speed rules for complete DB sweep)
            res = classify_tender(
                title=t.title,
                description=t.description or "",
                organisation=t.organisation or "",
                category=t.category or "",
                allow_llm=False,
            )


            new_is_it = res["is_it_related"]
            t.is_it_related = new_is_it
            t.relevance_score = res["relevance_score"]
            t.matched_keywords = json.dumps(res.get("matched_keywords", []))

            if old_is_it and not new_is_it:
                changed_to_false += 1
                if changed_to_false <= 8:
                    print(f"  [Removed False Positive #{t.id}]: {t.title[:65]}...")
            elif old_is_it and new_is_it:
                retained_true += 1
            elif not old_is_it and new_is_it:
                new_true += 1

            if i % 50 == 0 or i == total:
                db.commit()
                print(f"Processed {i}/{total} tenders...")

        db.commit()

        final_it_count = db.query(Tender).filter(Tender.is_it_related == True).count()
        print("\n=== Reclassification Summary ===")
        print(f"Total tenders: {total}")
        print(f"Purged False Positives (Electrical, HVAC, Physical): {changed_to_false}")
        print(f"Verified True IT Software Tenders: {final_it_count}")
        print("Database successfully updated with precision classifications!")

    except Exception as e:
        db.rollback()
        print(f"Error during reclassification: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reclassify_database()
