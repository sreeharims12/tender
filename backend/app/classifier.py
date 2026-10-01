import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

logger = logging.getLogger("classifier")

# Initialize Gemini Client if key is available
_gemini_client = None
if GEMINI_API_KEY:
    try:
        from google import genai
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("Gemini GenAI client initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not initialize Gemini Client: {e}")

# In-memory cache for LLM classification results
_CLASSIFICATION_CACHE: Dict[str, Dict[str, Any]] = {}

# Comprehensive Exclusion List: Hardware, Electronics, Networking Physical, Civil, Vehicles, Supplies
HARDWARE_AND_PHYSICAL_EXCLUSIONS = [
    # 1. Computing Hardware & Peripherals (Laptops, Desktops, Servers, Monitors, Tablets)
    re.compile(r"\b(?:laptops?|desktops?|monitors?|i[3579]\s*desktop|i[3579]\s*laptop|all-?in-?one\s*pc|workstations?|tablets?|ipads?|smartphones?|mobile\s*phones?)\b", re.IGNORECASE),
    re.compile(r"\b(?:printers?|scanners?|photocopiers?|toners?|cartridges?|printer\s*toner|ink\s*refill|headsets?|webcams?|projectors?|speakerphones?)\b", re.IGNORECASE),
    re.compile(r"\b(?:hard\s*disks?|hard\s*discs?|external\s*ssd|external\s*hdd|\b\d+\s*tb\s*surveillance\b|storage\s*drives?|pen\s*drives?|flash\s*drives?)\b", re.IGNORECASE),
    
    # 2. Electronics, CCTV, Displays & Audio-Visual
    re.compile(r"\b(?:cctv|bullet\s*cameras?|surveillance\s*cameras?|ip\s*cameras?|security\s*cameras?|dvr\b|nvr\b)\b", re.IGNORECASE),
    re.compile(r"\b(?:biometrics?|face\s*recognition\s*system|fingerprint\s*(?:reader|scanner)|access\s*control\s*(?:system|reader))\b", re.IGNORECASE),
    re.compile(r"\b(?:interactive\s*flat\s*panels?|interactive\s*display|led\s*standee|dled\s*display|holobox|led\s*immersive\s*display|tv\s*panel)\b", re.IGNORECASE),
    re.compile(r"\b(?:podcast\s*set|studio\s*floor|pa\s*systems?|audio\s*systems?|sound\s*systems?|video\s*documentation|photo\s*documentation|multi\s*camera\s*video)\b", re.IGNORECASE),
    re.compile(r"\b(?:led\s*wall|lighting\s*arrangements?|flood\s*light|low\s*mast|mini\s*mast|high\s*mast|street\s*light|solar\s*(?:pv|installation|panel))\b", re.IGNORECASE),

    # 3. Networking Physical Equipment & Structured Cabling
    re.compile(r"\b(?:structured\s*cabling|cabling\s*work|networking\s*\(structured|patch\s*cords?|network\s*racks?|network\s*switches?|wi-?fi\s*access\s*points?)\b", re.IGNORECASE),
    re.compile(r"\b(?:poles?\s*for\s*cctv|electrical\s*items?\s*for\s*cctv|optical\s*fiber\s*cables?|ofc\s*cable)\b", re.IGNORECASE),

    # 4. HVAC, Power Backup & Heavy Electrical
    re.compile(r"\b(?:air\s*condition(?:er|ing)?|split\s*ac|cassette\s*ac|hvac|ductable|air\s*cooler|chillers?|refrigerat(?:or|ion))\b", re.IGNORECASE),
    re.compile(r"\b(?:ups\b|kva\b|\b13kva\b|battery|batteries|inverter|generator|dg\s*set|diesel\s*generator|transformer|substation|high\s*tension|switchgear|panel\s*board|epabx)\b", re.IGNORECASE),
    re.compile(r"\b(?:electrical\s*(?:wiring|work|services|cables?|fittings?)|electrification)\b", re.IGNORECASE),

    # 5. Civil, Construction, Furniture & Physical Supplies
    re.compile(r"\b(?:construction\s*of\s*new\s*building|building\s*construction|civil\s*works?|carpentry|painting|plumbing|masonry|roofing|waterproofing|floor\s*tiles|polycarbonate)\b", re.IGNORECASE),
    re.compile(r"\b(?:furniture|chairs?|revolving\s*chairs?|tables?|steel\s*almirah|cupboards?|security\s*cabin)\b", re.IGNORECASE),
    re.compile(r"\b(?:stationery|paper|question\s*papers?|carton\s*boxes?|tissue\s*paper|bags?|chemicals?|import\s*permit|booklets?|printing\s*and\s*supply|printing\s*of)\b", re.IGNORECASE),
    re.compile(r"\b(?:wet\s*lease|vehicles?|car\s*hire|bus|diesel|petrol|fuel\s*supply|waste\s*management|sanitary\s*napkins?|cleaning|security\s*guard|fire\s*extinguisher)\b", re.IGNORECASE),
    re.compile(r"\b(?:borehole|drilling|soil\s*testing|landslide|timber|auction\s*notice)\b", re.IGNORECASE),
]

# Core Software Procurement Patterns (Pure Software, Applications, Cloud, e-Governance, Computerisation)
SOFTWARE_DEVELOPMENT_PATTERNS = [
    # Custom Software & Web/Mobile Development
    ("software development", 0.70, re.compile(r"\b(?:software\s*development|application\s*development|custom\s*(?:software\s*)?development|software\s*solutions?)\b", re.IGNORECASE)),
    ("web application", 0.70, re.compile(r"\b(?:web\s*applications?|web\s*portals?|citizen\s*portals?|portal\s*development|website\s*development)\b", re.IGNORECASE)),
    ("mobile application", 0.70, re.compile(r"\b(?:mobile\s*applications?|mobile\s*portals?|web\s*&\s*mobile\s*portal|android\s*app|ios\s*app)\b", re.IGNORECASE)),
    
    # Government Specific Terminology: Computerisation & e-Governance
    ("computerisation / e-governance", 0.70, re.compile(r"\b(?:computeris(?:ation|ed)|computeriz(?:ation|ed)|e-?governance(?:\s*solution)?|e-?office|workflow\s*automation|citizen\s*service\s*portal|online\s*application\s*(?:system|portal))\b", re.IGNORECASE)),
    ("management information system", 0.65, re.compile(r"\b(?:management\s*information\s*system|mis\s*portal|hmis|decision\s*support\s*system|gis\s*(?:portal|application|mapping))\b", re.IGNORECASE)),

    # Cloud Services & SaaS
    ("cloud services", 0.65, re.compile(r"\b(?:cloud\s*services?|cloud\s*computing|cloud\s*hosting|saas|paas|meity\s*empanelled\s*cloud|state\s*data\s*centre\s*hosting)\b", re.IGNORECASE)),
    
    # Cybersecurity Software & Audits
    ("cybersecurity", 0.65, re.compile(r"\b(?:cyber\s*security\s*software|cybersecurity\s*software|security\s*audit\s*of\s*(?:new\s*version\s*of\s*)?[a-z0-9\-_\s]*web\s*application|vulnerability\s*assessment|vapt|cert-?in\s*audit)\b", re.IGNORECASE)),
    
    # Artificial Intelligence & Data Analytics Software
    ("artificial intelligence", 0.65, re.compile(r"\b(?:artificial\s*intelligence|machine\s*learning|deep\s*learning|data\s*analytics|data\s*science)\b", re.IGNORECASE)),
    
    # Enterprise Software & Integrations
    ("API integration", 0.60, re.compile(r"\b(?:api\s*integration|apis?|payment\s*gateway\s*integration)\b", re.IGNORECASE)),
    ("ERP / CRM", 0.60, re.compile(r"\b(?:erp\s*implementation|erp\s*software|crm\s*software)\b", re.IGNORECASE)),
    
    # Software Maintenance & Specific Software Products
    ("software maintenance", 0.60, re.compile(r"\b(?:software\s*maintenance|application\s*maintenance|portal\s*maintenance|amc\s*of\s*web\s*portal|operation\s*and\s*maintenance\s*of\s*software|software\s*for\s*copa)\b", re.IGNORECASE)),
    ("antivirus software", 0.60, re.compile(r"\b(?:antivirus\s*software|software\s*licenses?)\b", re.IGNORECASE)),
    ("digitization software", 0.55, re.compile(r"\b(?:digitization\s*and\s*implementation\s*of\s*dmr|electronic\s*document\s*management|edms)\b", re.IGNORECASE)),
]


def _clean_destination_rooms(text: str) -> str:
    """
    Masks destination room or department cell names (e.g. 'Software Lab', 'Computer Lab',
    'CAD Lab', 'Computerisation Cell') when mentioned as physical delivery locations.
    """
    cleaned = re.sub(
        r"(?:for|in|at)\s+(?:the\s+)?(?:software\s*lab|computer\s*(?:lab|centre|center|section)|cad\s*lab|computeris(?:ation|ed)\s*(?:cell|lab|branch|section))",
        " [room_location] ",
        text,
        flags=re.IGNORECASE
    )
    cleaned = re.sub(
        r"\b(?:software\s*lab|cad\s*lab|computer\s*lab|computeris(?:ation|ed)\s*(?:cell|lab|branch|section))\b",
        " [room_location] ",
        cleaned,
        flags=re.IGNORECASE
    )
    return cleaned


def _classify_with_gemini(title: str, description: str, organisation: str) -> Optional[Dict[str, Any]]:
    """
    Uses Gemini LLM for precise semantic evaluation to strictly confirm software-only tenders.
    """
    if not _gemini_client:
        return None

    cache_key = f"{title.strip().lower()}|{(description or '').strip().lower()[:100]}"
    if cache_key in _CLASSIFICATION_CACHE:
        return _CLASSIFICATION_CACHE[cache_key]

    prompt = f"""You are an elite, highly strict procurement classifier for a Government Tender Monitoring System in Kerala, India.
Your mission is to identify ONLY pure Software Development, E-Governance, Computerisation (Software/MIS/Databases), Web/Mobile Applications, Cloud Hosting, and Software Cybersecurity tenders.

UNDERSTAND GOVERNMENT PROCUREMENT TERMINOLOGY:
Government tenders frequently use terms like "Computerisation", "e-Governance", "MIS", "e-Office", or "Digitisation" rather than modern corporate jargon like "custom software development".
Apply these strict procurement distinctions:
1. "Computerisation / Computerization":
   - ACCEPT IF: It is for software development, database design, digitizing administrative workflows, web/online application portals, or Management Information Systems (MIS).
   - REJECT IF: It is merely the physical supply/procurement of desktop computers, laptops, printers, or UPS for an office (even if titled "for computerisation of office").
2. "e-Governance / Citizen Portals":
   - ACCEPT: Online public service portals (G2C/G2B/G2G), grievance redressal portals, citizen service delivery, workflow automation.
3. "MIS / HMIS / GIS":
   - ACCEPT: Management Information Systems, Hospital Management Systems, Web-GIS mapping and analysis software.
4. "Security Audits & Cloud":
   - ACCEPT: Cert-In empaneled security audit of web applications/portals, VAPT, MeitY-empanelled CSP cloud hosting.
5. "Software Support & O&M":
   - ACCEPT: Annual Maintenance Contract (AMC) or Operation & Maintenance (O&M) of software applications, portals, and websites.

STRICT INCLUSION RULES (is_it_related = true):
- Software Development, Web Applications, Portals, Websites, Mobile Apps (Android/iOS)
- Government Computerisation (Software, digital records automation, online processing systems)
- e-Governance Solutions, Citizen Service Delivery Platforms, e-Office / Workflow Automation
- Management Information Systems (MIS), Decision Support Systems (DSS), HMIS, Web-GIS
- Cloud Services, Cloud Computing, SaaS, PaaS, Cloud Hosting (e.g., MeitY-empanelled CSP, AWS, Azure, SDC)
- APIs, Payment Gateway Integration, System Integration (software-level)
- Artificial Intelligence (AI), Machine Learning (ML), Data Analytics
- Cybersecurity Software, Application Security Audits (VAPT, Cert-In audit of web/mobile apps)
- Software Maintenance (AMC / O&M of Web Portals / Applications), Software Licenses / Antivirus
- Digitization & Electronic Document Management Systems (EDMS / DMR)

STRICT REJECTION RULES (is_it_related = false):
- Physical Hardware Procurement: Laptops, Desktops, All-in-One PCs, Workstations, Monitors, Tablets, Servers
- Office Peripherals: Printers, Scanners, Photocopiers, Toners, Cartridges, Projectors, Headsets
- Storage Devices: External HDDs, SSDs, Flash Drives
- Electronics & Surveillance: CCTV cameras, DVR/NVR, Biometric attendance machines, Access control, Smart cards, RFID readers, Interactive flat panels (IFP), LED standees, Video walls, Audio/Video equipment
- Physical Networking: Structured cabling, LAN wiring, Fiber optic cables (OFC), Patch cords, Network racks, Wi-Fi routers
- Electrical & HVAC: Air conditioners (AC), UPS, Batteries, Inverters, Generators, Solar panels, Electrical wiring, Lighting
- Civil, Facilities & Supplies: Civil construction, Furniture, Paper, Printing of books/stationery, Cleaning, Security guards, Vehicles

Tender Details:
Title: {title}
Description: {description}
Organisation: {organisation}

Return strictly a valid JSON object:
{{
  "is_it_related": boolean,
  "relevance_score": float (between 0.0 and 1.0),
  "matched_keywords": list of matched software/e-governance keywords (if true),
  "reason": "1-sentence concise explanation of why this was accepted or rejected"
}}
"""
    try:
        response = _gemini_client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

        result = json.loads(text)
        res_dict = {
            "is_it_related": bool(result.get("is_it_related", False)),
            "relevance_score": float(result.get("relevance_score", 0.0)),
            "matched_keywords": list(result.get("matched_keywords", [])),
            "reason": str(result.get("reason", "")),
        }
        _CLASSIFICATION_CACHE[cache_key] = res_dict
        return res_dict
    except Exception as e:
        logger.warning(f"Gemini classification error (falling back to rules): {e}")
        return None


def classify_tender(
    title: str,
    description: Optional[str] = "",
    work_description: Optional[str] = "",
    category: Optional[str] = "",
    organisation: Optional[str] = "",
    pdf_text: Optional[str] = "",
    allow_llm: bool = True,
) -> Dict[str, Any]:
    """
    Software-Only Precision Classifier:
    1. Hard Exclusion of all physical hardware, electronics, networking cabling, civil, and supplies (Tier 1).
    2. Explicit Positive Match for Software Development / Cloud / Apps / Cybersecurity / Data (Tier 1).
    3. Gemini Semantic Verification for ambiguous edge cases (Tier 2).
    """
    title_text = title or ""
    full_context = f"{title_text} {description or ''} {work_description or ''} {category or ''}"

    # Step 1: Detect explicit Hard Exclusions (Hardware, Electronics, Cabling, HVAC, Civil, Supplies)
    has_hardware_or_physical = any(pattern.search(full_context) for pattern in HARDWARE_AND_PHYSICAL_EXCLUSIONS)

    # Clean out room names (e.g. 'Air conditioner for software lab' -> 'software lab' is masked)
    cleaned_context = _clean_destination_rooms(full_context)

    # Step 2: Detect positive software keywords
    positive_matches = set()
    raw_score = 0.0
    for kw_name, weight, pattern in SOFTWARE_DEVELOPMENT_PATTERNS:
        if pattern.search(cleaned_context):
            positive_matches.add(kw_name)
            raw_score += weight

    # Check for direct software development / application phrases
    has_software_match = len(positive_matches) > 0

    # TIER 1 - INSTANT REJECTIONS:
    # A) If it procures hardware, electronics, cabling, or civil work, REJECT unless it is explicitly
    #    custom software development (e.g. building software WITH minimal supporting infrastructure).
    if has_hardware_or_physical:
        # Check if it is a pure software contract that merely mentions hardware as secondary
        is_primarily_software_contract = bool(
            re.search(r"\b(?:custom\s*development|web\s*application|citizen\s*portal|portal\s*development|web\s*&\s*mobile\s*portal|software\s*development)\b", cleaned_context, re.IGNORECASE)
            and not re.search(r"\b(?:supply\s*of|procurement\s*of|buying|hiring\s*of)\s+(?:laptop|desktop|printer|cctv|biometric|scanner|hardware|led|display)\b", cleaned_context, re.IGNORECASE)
        )
        if not is_primarily_software_contract:
            return {
                "is_it_related": False,
                "relevance_score": 0.0,
                "matched_keywords": [],
                "reason": "Excluded: Procurement is for hardware, electronics, physical networking, civil, or non-software supplies.",
            }

    # B) If no positive software keywords match, REJECT immediately
    if not has_software_match:
        return {
            "is_it_related": False,
            "relevance_score": 0.0,
            "matched_keywords": [],
            "reason": "No software development, application, cloud, or software service keywords identified.",
        }

    # TIER 1 - INSTANT ACCEPTANCE:
    # If high-confidence software terms exist with ZERO hardware/physical conflicts
    if has_software_match and not has_hardware_or_physical:
        final_score = min(0.99, max(0.60, round(raw_score, 2)))
        return {
            "is_it_related": True,
            "relevance_score": final_score,
            "matched_keywords": sorted(list(positive_matches)),
            "reason": "Direct match for pure software development, web/mobile application, cloud, or cybersecurity services.",
        }

    # TIER 2 - BORDERLINE / AMBIGUOUS (Call Gemini)
    if allow_llm and _gemini_client:
        llm_result = _classify_with_gemini(
            title=title_text,
            description=f"{description or ''} {work_description or ''}",
            organisation=organisation or "",
        )
        if llm_result is not None:
            return llm_result

    # Fallback if LLM is offline:
    if has_hardware_or_physical:
        return {
            "is_it_related": False,
            "relevance_score": 0.0,
            "matched_keywords": [],
            "reason": "Excluded: Hardware, electronics, or physical infrastructure.",
        }

    return {
        "is_it_related": has_software_match,
        "relevance_score": min(0.99, max(0.50, round(raw_score, 2))),
        "matched_keywords": sorted(list(positive_matches)),
        "reason": "Classified as software development.",
    }
