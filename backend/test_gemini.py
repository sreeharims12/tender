import os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

models_to_try = [
    "gemini-flash-latest",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.8-flash"
]

test_prompt = """
You are a government tender classification expert.
Determine if the following tender is an IT / Software tender:
"Short Tender notice-For buying Air Conditioner for Principal Room, Software Lab, CAD lab, General Library"

Reply in valid JSON format:
{
  "is_it_software": false,
  "relevance_score": 0.0,
  "reason": "Procurement is for HVAC air conditioning equipment; Software Lab is merely the room location."
}
"""

for model_name in models_to_try:
    try:
        resp = client.models.generate_content(
            model=model_name,
            contents=test_prompt
        )
        print(f"=== {model_name} SUCCESS ===")
        print(resp.text)
        break
    except Exception as e:
        print(f"{model_name} failed: {e}")
