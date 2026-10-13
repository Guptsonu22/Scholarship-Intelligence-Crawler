# Scholarship Intelligence Crawler for Indian Students

**EDXSO AI Engineer Intern Assignment 2**  
*Authentic scholarship opportunity discovery, deterministic extraction, verifiable confidence scoring, and lifecycle change detection.*

---

## Architecture Overview

- **Backend**: FastAPI (Python 3.12+)
- **Database**: SQLite (persistent local storage under `data/scholarships.db` with non-destructive migrations)
- **Frontend**: React + TypeScript + Vite
- **Crawling & Discovery**: Requests, BeautifulSoup4, SSRF Security Guard, Robots.txt Policy Manager, Domain Throttling
- **Extraction Engine**: Deterministic DOM parser, Indian date parser, monetary benefit parser, page classifier (`SCHOLARSHIP_DETAIL`, `LISTING`, `APPLICATION_PORTAL`, `GENERIC_PAGE`), and field-level evidence tracker
- **Verification Engine (Phase 4)**: 100-point deterministic scoring model, 7 mandatory verification gates, field evidence quality ratings (`SUPPORTED`, `WEAK_EVIDENCE`, `NOT_FOUND`, `CONFLICTING`, `STALE`), strict `>=95%` confidence requirement, and persistent audit history. Never relies on LLMs for confidence scoring.
- **Validation**: Pydantic v2
- **Testing**: Pytest (69 automated tests covering verification scoring, mandatory gates, 94.99 vs 95 boundary, expired deadlines, extraction, dates, amounts, page assessors, discovery, security, and endpoints)

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
│   │   ├── App.tsx                  # Dashboard interface & evidence/verification inspector
│   │   ├── App.css                  # UI styling & gate status indicators
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
    │   │   ├── models.py            # Models (Scholarship, FieldEvidence, VerificationRecord, etc.)
    │   │   └── init_db.py           # Table initialization & safe migrations
    │   ├── api/routes/
    │   │   ├── health.py            # GET /api/health
    │   │   ├── discovery.py         # /api/discovery/sources, /run, /candidates
    │   │   ├── crawl.py             # /api/crawl/runs, /run, /candidates/{id}
    │   │   ├── scholarships.py      # /api/scholarships, /{id}, /{id}/evidence, /{id}/verification
    │   │   ├── extraction.py        # /api/extraction/run, /runs
    │   │   └── verification.py      # /api/verification/run, /summary, /history/{id}, /detail/{id}
    │   ├── models/schemas.py        # Pydantic request/response schemas
    │   └── services/
    │       ├── discovery/           # Candidate discovery & URL normalization
    │       ├── crawling/            # Ethical HTTP crawler, SSRF guard & robots.txt
    │       ├── extraction/          # Deterministic field extraction & evidence engine
    │       └── verification/        # Deterministic scoring, mandatory gates & evidence evaluator
    └── tests/                       # Automated backend tests (69 tests)
```

---

## Phase 4: Deterministic Confidence Engine & Verification

### Scoring Allocation (100 Maximum Points)

| Criterion | Max Points | Description |
| :--- | :---: | :--- |
| **Official primary source established** | 25 | Verified government (.gov.in/.nic.in) = 25; accredited university (.ac.in/.edu.in) = 23; verified corporate CSR/trust = 20; aggregators = 0. |
| **Scholarship-specific identity and presence** | 20 | Distinct named opportunity = 20; umbrella/directory listing title = 5 (-15 deduction); missing provider = -5. |
| **Critical fields supported by relevant evidence** | 20 | Verified support for Name (5), Provider (5), Eligibility (5), Benefit/Course Level (5). Generic body snippets penalized. |
| **Application URL verified, when applicable** | 10 | Verified official provider or apex portal link = 10; not applicable (applications closed/offline) = 10; third-party = 3; missing when required = 0. |
| **Deadline supported by contextual evidence** | 10 | Contextual active deadline = 10; generic date without context = 4; expired deadline = 0; open/rolling = 6. |
| **Source freshness and recent fetch** | 10 | Successful HTTP 200 within 14 days = 10; within 60 days = 7; aged/stale = 1–4; fetch failure = 0. |
| **Extraction consistency & contradiction checks** | 5 | Clean internal consistency = 5; conflicting dates, multiple deadlines, or conflated schemes = 0. |
| **Total** | **100** | Reproducible evidence-based score. |

### Mandatory Verification Gates

A record can **ONLY** receive the `VERIFIED` designation when:
1. Its computed confidence score is $\ge 95.0\%$.
2. **All 7 mandatory gates pass** (`PASS` or `NOT_APPLICABLE`):
   - `official_source_gate`: Authoritative official primary source verified (fails for aggregators).
   - `scholarship_identity_gate`: Specific singular opportunity (fails for multi-scheme listings).
   - `field_evidence_gate`: Direct relevant evidence for critical fields (fails for generic body snippets).
   - `contradiction_gate`: No unresolved conflicting dates or schemes.
   - `freshness_gate`: Recent successful HTTP 200 crawl.
   - `application_link_gate`: Official application portal or legitimate `NOT_APPLICABLE`.
   - `lifecycle_gate`: Closing date is active/future relative to evaluation date (fails for expired deadlines).
3. If score $\ge 95\%$ but ANY gate fails $\rightarrow$ status becomes `REVIEW_REQUIRED`.

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

Execute the 69-test pytest suite validating verification scoring, gates, boundary conditions, field extraction, dates, amounts, security, and APIs:

```powershell
$env:PYTHONPATH="backend;backend/app"
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -v
```

### 3. Start the Backend API

```powershell
$env:PYTHONPATH="backend;backend/app"
.\backend\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Health Endpoint**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- **Verification Summary**: [http://127.0.0.1:8000/api/verification/summary](http://127.0.0.1:8000/api/verification/summary)
- **Scholarships API**: [http://127.0.0.1:8000/api/scholarships](http://127.0.0.1:8000/api/scholarships)
- **API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 4. Start the Frontend Dashboard

```powershell
npm run dev --prefix frontend
```

Open [http://localhost:5173](http://localhost:5173) in your browser.
