# Scholarship Intelligence Crawler for Indian Students

**EDXSO AI Engineer Intern Assignment 2**  
*Authentic scholarship opportunity discovery, deterministic extraction, verifiable confidence scoring, and lifecycle change detection.*

---

## Architecture Overview

- **Backend**: FastAPI (Python 3.12+)
- **Database**: SQLite (persistent local storage under `data/scholarships.db`)
- **Frontend**: React + TypeScript + Vite
- **Crawling & Discovery**: Requests, BeautifulSoup4, SSRF Security Guard, Robots.txt Policy Manager, Domain Throttling
- **Validation**: Pydantic v2
- **Testing**: Pytest (38 automated tests covering discovery, security, classifiers, and endpoints)

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
│   │   ├── App.tsx                  # Dashboard interface & live candidate explorer
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
    │   │   ├── models.py            # SQLAlchemy models (SeedSource, CandidateURL, CrawlAttempt, etc.)
    │   │   └── init_db.py           # Table initialization & default seeds
    │   ├── api/routes/
    │   │   ├── health.py            # GET /api/health
    │   │   ├── discovery.py         # /api/discovery/sources, /run, /candidates
    │   │   └── crawl.py             # /api/crawl/runs, /run, /candidates/{id}
    │   ├── models/schemas.py        # Pydantic request/response schemas
    │   └── services/
    │       ├── discovery/           # Candidate discovery & URL normalization
    │       ├── crawling/            # Ethical HTTP crawler, SSRF guard & robots.txt
    │       └── verification/        # Source classifier with explainable reasons
    └── tests/                       # Automated backend tests (38 tests)
```

---

## Windows PowerShell Setup & Run Instructions

### Prerequisites
- Python 3.12+ (Python 3.14 supported)
- Node.js 18+ and npm

### 1. Clone & Environment Configuration

Open Windows PowerShell in the project root:

```powershell
Copy-Item .env.example .env
```

### 2. Backend Setup & Virtual Environment

```powershell
# Create virtual environment
python -m venv backend/.venv

# Activate virtual environment
.\backend\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Run Automated Tests

Execute the 38-test pytest suite validating security, crawling, discovery, database, and API endpoints:

```powershell
$env:PYTHONPATH="backend;backend/app"
.\backend\.venv\Scripts\python.exe -m pytest backend/tests
```

### 4. Start the Backend API

```powershell
$env:PYTHONPATH="backend;backend/app"
.\backend\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Health Endpoint**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- **API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Candidate URLs API**: [http://127.0.0.1:8000/api/discovery/candidates](http://127.0.0.1:8000/api/discovery/candidates)
- **Seed Sources API**: [http://127.0.0.1:8000/api/discovery/sources](http://127.0.0.1:8000/api/discovery/sources)

### 5. Run a Discovery or Crawl Operation via PowerShell

You can trigger discovery and crawling directly via PowerShell `Invoke-RestMethod`:

```powershell
# Trigger a discovery run across top 3 seed sources
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/discovery/run" -Method Post -ContentType "application/json" -Body '{"max_seeds": 3, "respect_robots": false}'

# List discovered candidates
(Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/discovery/candidates?page=1&page_size=10").items | Format-Table id, source_category, relevance_score, normalized_url

# Trigger a crawl run on queued candidates
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/crawl/run" -Method Post -ContentType "application/json" -Body '{"max_pages": 3}'
```

### 6. Start the Frontend Dashboard

In a separate Windows PowerShell window:

```powershell
cd frontend
npm install
npm run dev
```

- **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)

---

## Phase 2 Implementation Summary

- [x] **Configurable Seed Portals**: 15 authentic seed sources across Central Government, State Government, Universities, Corporate CSR, Trusts, and Aggregators.
- [x] **SSRF Security Protection**: Blocks loopback, RFC 1918 private subnets, cloud metadata IPs (`169.254.169.254`), non-HTTP schemes, and unsafe redirects.
- [x] **Ethical Crawling**: Robots.txt compliance, per-domain rate limiting, max response size safeguards (5MB), and Content-Type enforcement (`text/html`).
- [x] **URL Normalization & Relevance Scoring**: Strips fragments, cleans tracking parameters, filters binary downloads, and scores scholarship keyword relevance.
- [x] **Deterministic Source Classification**: Classifies sources with explainable reasons and confidence trust scores.
- [x] **Audit History**: Records `CrawlRun` and `CrawlAttempt` with SHA-256 content hashes, HTTP status codes, and timing.
- [x] **Real Discovery Verified**: Successfully extracted 53 genuine candidates from live portals into SQLite with zero duplicate insertions on repeated runs.
- [x] **Comprehensive Testing**: 38 automated pytest tests passing cleanly.
