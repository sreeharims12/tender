# Kerala IT Tender Monitoring System

A functional, modern MVP web application that collects publicly available IT/software-related tenders from selected Kerala Government portals and displays them in a searchable, filterable dashboard.

---

## 1. System Architecture

- **Frontend**: React + Vite + Tailwind CSS + Lucide Icons + TanStack Table (`@tanstack/react-table`) + Axios
- **Backend API**: Python + FastAPI + SQLAlchemy + SQLite
- **Web Scraping**: `httpx`, `BeautifulSoup4`, and PyMuPDF (`fitz` / `pymupdf`) for text extraction from publicly accessible PDF documents.
- **Deduplication Engine**: Multi-tier priority hashing:
  1. `tender_id`
  2. `tender_reference`
  3. Canonical `tender_url`
  4. Hash: `source_name + title + organisation + published_date`
- **Software-Only Precision Classifier (Two-Tier Hybrid)**:
  - **Strict Software-Only Scope**: Tailored exclusively to **Software Development & Software Services** (Web/Mobile App development, Portals, Cloud hosting, APIs, ERP/CRM, Cybersecurity software/VAPT, AI/Data Science, Digitization & Software Maintenance).
  - **Hardware & Electronics Exclusion**: Hard exclusions filter out all physical computing hardware (laptops, desktops, workstations, monitors, tablets), peripherals (printers, scanners, toners, cartridges), storage media (external SSD/HDD), security & surveillance electronics (CCTV, biometric attendance machines, facial recognition devices), audio-visual equipment (podcast sets, PA systems, displays, LED walls), and structured network cabling.
  - **Gemini AI Verification**: Powered by Google Gemini LLM (`gemini-3.5-flash-lite`) for semantic edge-case validation.



---

## 2. Monitored Kerala Government Sources

| Priority | Source Name | Public URL | Scraper Status |
| :--- | :--- | :--- | :--- |
| **Very High** | Kerala e-Procurement Portal | [https://etenders.kerala.gov.in/](https://etenders.kerala.gov.in/) | Active (Public Org Listings, Zero CAPTCHA) |
| **High** | Kerala State IT Mission (KSITM) | [https://itmission.kerala.gov.in/tenders](https://itmission.kerala.gov.in/tenders) | Active (Direct Notices & PDF attachments) |
| **High** | C-DIT | [https://cdit.kerala.gov.in/?page_id=2538](https://cdit.kerala.gov.in/?page_id=2538) | Active (Official tender listings & details) |
| **Medium** | Directorate of Industries & Commerce | [https://www.industry.kerala.gov.in/index.php/tender](https://www.industry.kerala.gov.in/index.php/tender) | Active (Public tender table) |
| **Medium** | Kerala SIDCO | [https://www.keralasidco.com/](https://www.keralasidco.com/) | Active (SIDCO procurement section) |
| **Medium** | K-DISC | [https://kdisc.kerala.gov.in/en/latest/](https://kdisc.kerala.gov.in/en/latest/) | Active (Bid notifications & documents) |

> **CAPTCHA Compliance Policy**: Under no circumstances does this application solve, automate, or bypass CAPTCHAs. Only publicly accessible tender listings, organisation pages, individual tender pages, and publicly accessible documents are collected. Any CAPTCHA-protected operation is skipped.

---

## 3. Setup and Installation

### Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: v18 or higher (with npm)

---

### Step 1: Create and Activate Python Virtual Environment (venv)

Open your terminal in the project root directory (`c:\Users\User\Documents\Work\Tenders`):

#### 1. Create the virtual environment:
```bash
python -m venv venv
```

#### 2. Activate the virtual environment:
- **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
  *(If you get a script execution policy restriction, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

- **Windows (Command Prompt / CMD)**:
  ```cmd
  venv\Scripts\activate.bat
  ```

- **Linux / macOS**:
  ```bash
  source venv/bin/activate
  ```

---

### Step 2: Install Backend Dependencies

With the virtual environment activated, install the required Python packages:

```bash
# From workspace root:
pip install -r backend/requirements.txt
```

*(Or if you are already inside the `backend/` directory: `pip install -r requirements.txt`)*

---

### Step 3: Install Frontend Dependencies

In a separate terminal or after backend installation:

```bash
cd frontend
npm install
cd ..
```

---

## 4. Running the Application

### Option A: Standard Development Mode (Recommended)

Run backend and frontend concurrently in two terminals:

#### Terminal 1 — Start the Backend (FastAPI):
- **If you are inside the `backend/` folder:**
  ```powershell
  python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
  # or simply:
  python run.py
  ```

- **If you are in the workspace root directory (`Tenders`):**
  ```powershell
  python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
  # or simply:
  python run.py
  ```
- API is live at: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Interactive Swagger Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)


#### Terminal 2 — Start the Frontend (Vite):
```bash
cd frontend
npm run dev
```
- Web Dashboard is live at: [http://localhost:5173](http://localhost:5173)

---

### Option B: Single-Port Production Mode

You can also build the React frontend once and have FastAPI serve both the API and the UI on a single port:

```bash
# 1. Build the frontend
cd frontend
npm run build
cd ..

# 2. Start FastAPI
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser — the entire React dashboard is served directly from port 8000!

---

## 5. Troubleshooting: Port Conflict (`[WinError 10013]`)

If you see:
`ERROR: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions`

This happens when port `8000` is already in use by another running process or restricted by Windows permissions.

### Solution 1: Use an Alternate Port (e.g. 8001 or 8080)
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload
```
*(If you change the port, update the proxy port in `frontend/vite.config.js` to match, or open `http://127.0.0.1:8001/` directly).*

### Solution 2: Identify and Terminate the Process Using Port 8000
In PowerShell:
```powershell
# Find PID occupying port 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess

# Stop the process by PID
Stop-Process -Id <PID> -Force
```

---

## 6. API Endpoints Reference

- `GET /api/stats`: Top KPI cards (Total Tenders, IT Tenders, New Tenders, Last Scrape)
- `GET /api/tenders`: Search, filter by source, organisation, category, IT-only toggle, sort, and paginate
- `GET /api/tenders/{id}`: Detailed tender record with matched keywords and relevance score
- `POST /api/scrape`: Asynchronously trigger background scraping across all 6 sources
- `GET /api/scrape/status`: Real-time status, counts (found, IT, new, duplicates, errors), and execution logs
- `GET /api/sources`: Unique list of sources and organisations for frontend dropdowns

---

## 7. Daily Automated Tender Monitoring (GitHub Actions & Brevo)

The system includes a fully automated daily cron workflow powered by **GitHub Actions** and the **Brevo API**. It operates completely independently without requiring a local machine, dev server, or React frontend to be running.

### Key Specifications

- **Workflow Name**: `Daily Tender Monitor` ([`.github/workflows/daily-tender-monitor.yml`](.github/workflows/daily-tender-monitor.yml))
- **Daily Execution Time**: Every day at **08:00 AM IST** (Indian Standard Time, `Asia/Kolkata`), which translates to **02:30 AM UTC** (`cron: '30 2 * * *'`).
- **Entry Script**: [`daily_job.py`](daily_job.py) (can be executed directly from CLI or GitHub Actions).

### Execution Pipeline

```text
GitHub Actions Cron (8:00 AM IST)
              ↓
  Checkout & Setup Python 3.11
              ↓
  Restore SQLite DB Cache (actions/cache@v4)
              ↓
  Run daily_job.py
      ├─► Scrapes all 6 Kerala government portals
      ├─► Runs precision IT/software classifier (Heuristic + Gemini AI)
      ├─► Deduplicates records against database
      ├─► Formats responsive HTML & text daily digest
      └─► Sends transactional email via Brevo REST API
```

### Manual Trigger (`workflow_dispatch`)

You can test or run the workflow on demand without waiting for the scheduled time:
1. In your GitHub repository, navigate to the **Actions** tab.
2. In the left sidebar, click on **Daily Tender Monitor**.
3. Click the **Run workflow** dropdown on the right.
4. (Optional) Check *Dry run* to test scraping without sending emails.
5. Click **Run workflow**.

### Required GitHub Secrets

Configure these secrets under **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Secret Name | Description | Example / Format |
| :--- | :--- | :--- |
| `EMAIL_FROM` | Your sender Gmail address | `yourname@gmail.com` |
| `EMAIL_TO` | Recipient email address(es) (comma-separated for multiple) | `mssreehari143@gmail.com` |
| `GMAIL_APP_PASSWORD` | 16-character Google App Password (from [Google App Passwords](https://myaccount.google.com/apppasswords)) | `abcd efgh ijkl mnop` |
| `GEMINI_API_KEY` | Google Gemini API key for semantic edge-case validation | `AIzaSy...` |
| `BREVO_API_KEY` *(Optional)* | Optional fallback if using Brevo instead of direct Gmail | `xkeysib-...` |

### Email Generation & Delivery

- **Generation**: [`backend/app/email_service.py`](backend/app/email_service.py) builds both a mobile-responsive, card-styled HTML email and a plain-text fallback. If no new relevant tenders are published that day, a clean notification stating *"No relevant IT/software tenders were found today"* is sent.
- **Delivery**: Uses Python's built-in `smtplib` to connect directly to Google's official mail server (`smtp.gmail.com:587`) using TLS and your Google App Password. No external third-party services required, no IP blocking, and emails land straight in your Primary inbox.


### Database Persistence on GitHub Actions

GitHub Actions runners are ephemeral. To ensure tender deduplication works seamlessly across daily runs:
- The workflow utilizes **`actions/cache@v4`** on `backend/tenders.db`.
- Before each run, the previous SQLite database snapshot is restored.
- At the end of the run, the updated database is automatically cached for the next day.
- If the cache is missed (e.g., initial run), SQLite creates a fresh database automatically without errors.

### Local Testing Command

You can run and test the daily monitoring pipeline locally at any time:

```bash
# Dry run: scrapes, classifies, and previews email without sending via Brevo
python daily_job.py --dry-run

# Force include active tenders in preview even if no new tenders were found
python daily_job.py --dry-run --include-existing

# Live run: sends actual email to EMAIL_TO via Brevo
python daily_job.py
```
