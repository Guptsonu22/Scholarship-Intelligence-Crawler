# Scholarship Intelligence Crawler for Indian Students

**EDXSO AI Engineer Intern Assignment 2**  
*Authentic scholarship opportunity discovery, deterministic extraction, verifiable confidence scoring, and lifecycle change detection.*

---

## Architecture Overview

- **Backend**: FastAPI (Python 3.12+)
- **Database**: SQLite (persistent local storage under `data/scholarships.db`)
- **Frontend**: React + TypeScript + Vite
- **Crawling & Discovery**: Requests, BeautifulSoup4, SSRF Security Guard, Robots.txt Policy Manager, Domain Throttling
- **Extraction Engine**: Deterministic DOM parser, Indian date parser, monetary benefit parser, page classifier (`SCHOLARSHIP_DETAIL`, `LISTING`, `APPLICATION_PORTAL`, `GENERIC_PAGE`), and field-level evidence tracker
- **Validation**: Pydantic v2
- **Testing**: Pytest (59 automated tests covering extraction, dates, amounts, page assessors, discovery, security, and endpoints)

---

## Project Structure

```
├── .env.example                     # Environment template
├── .gitignore                       # Git exclusion rules
├── README.md                        # Setup and run instructions
├── data/                            # Persistent SQLite database storage
├── docs/
│   └── architecture.md              # Detailed architecture documentation
├── frontend/                        # React + TypeScript + Vite application
│   ├── src/
│   │   ├── App.tsx                  # Dashboard interface & evidence inspector
│   │   ├── App.css                  # UI styling
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
└── backend/                         # FastAPI backend service
    ├── requirements.txt             # Python dependencies
    ├── pyproject.toml               # Pytest configuration
    ├── app/
    │   ├── main.py                  # FastAPI application entrypoint
    │   ├── core/config.py           # Configuration & environment variables
    │   ├── db/
    │   │   ├── database.py          # SQLite engine & session factory
    │   │   ├── models.py            # Models (Scholarship, FieldEvidence, CandidateURL, etc.)
    │   │   └── init_db.py           # Table initialization & safe migrations
    │   ├── api/routes/
    │   │   ├── health.py            # GET /api/health
    │   │   ├── discovery.py         # /api/discovery/sources, /run, /candidates
    │   │   ├── crawl.py             # /api/crawl/runs, /run, /candidates/{id}
    │   │   ├── scholarships.py      # /api/scholarships, /{id}, /{id}/evidence
    │   │   └── extraction.py        # /api/extraction/run, /runs
    │   ├── models/schemas.py        # Pydantic request/response schemas
    │   └── services/
    │       ├── discovery/           # Candidate discovery & URL normalization
    │       ├── crawling/            # Ethical HTTP crawler, SSRF guard & robots.txt
    │       ├── extraction/          # Deterministic field extraction & evidence engine
    │       └── verification/        # Source classifier with explainable reasons
    └── tests/                       # Automated backend tests (59 tests)
```

---

## Windows PowerShell Setup & Run Instructions

### Prerequisites
- Python 3.12+ (Python 3.14 supported)
- Node.js 18+ and npm

### 1. Backend Setup & Virtual Environment

```powershell
# Create and activate virtual environment
python -m venv backend/.venv
.\backend\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Run Automated Tests

Execute the 59-test pytest suite validating field extraction, date parsing, amounts, page classification, evidence linking, security, and APIs:

```powershell
$env:PYTHONPATH="backend;backend/app"
.\backend\.venv\Scripts\python.exe -m pytest backend/tests
```

### 3. Start the Backend API

```powershell
$env:PYTHONPATH="backend;backend/app"
.\backend\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Health Endpoint**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- **Scholarships API**: [http://127.0.0.1:8000/api/scholarships](http://127.0.0.1:8000/api/scholarships)
- **API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 4. Run Discovery & Extraction via PowerShell

```powershell
# 1. Trigger candidate discovery across seed sources
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/discovery/run" -Method Post -ContentType "application/json" -Body '{"max_seeds": 3, "respect_robots": false}'

# 2. Trigger deterministic extraction on candidates
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/extraction/run" -Method Post -ContentType "application/json" -Body '{"max_candidates": 10}'

# 3. List extracted structured scholarships
(Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/scholarships").items | Format-Table id, name, provider, closing_date, amount_benefit

# 4. Inspect field-level evidence for scholarship #1
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/scholarships/1/evidence" | Format-Table field_name, extracted_value, html_selector
```

### 5. Start the Frontend Dashboard

```powershell
cd frontend
npm install
npm run dev
```

- **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)

---

## Phase 3 Implementation Summary

- [x] **Structured Schema**: `Scholarship` model storing stable ID, name, provider, dates, amounts, eligibility, categories, documents, and lifecycle status.
- [x] **Field-Level Traceable Evidence**: `FieldEvidence` table capturing verbatim source text snippets, DOM selectors, source URLs, content hashes, and timestamps.
- [x] **Page Assessment Engine**: Distinguishes `SCHOLARSHIP_DETAIL` from `SCHOLARSHIP_LISTING`, `APPLICATION_PORTAL`, `GENERIC_PAGE`, and `INSUFFICIENT_EVIDENCE`.
- [x] **Zero Hallucination Policy**: Missing values remain strictly null/None and display as *"Not specified"*. No invented dates or amounts.
- [x] **Deterministic Parsers**: Indian date parser, monetary/benefit expression parser, education level and reservation category extractors.
- [x] **Interactive Evidence Explorer**: Frontend modal displaying full verbatim textual snippets and DOM selector provenance for every extracted attribute.
- [x] **59/59 Automated Tests**: Comprehensive pytest suite passing with zero failures.
