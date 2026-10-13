# Scholarship Intelligence Crawler for Indian Students

**EDXSO AI Engineer Intern Assignment 2**  
*Authentic scholarship opportunity discovery, deterministic extraction, verifiable confidence scoring, and automatic recrawling lifecycle change detection.*

---

## Architecture Overview

- **Backend**: FastAPI (Python 3.12+)
- **Database**: SQLite (persistent local storage under `data/scholarships.db` with non-destructive migrations)
- **Frontend**: React + TypeScript + Vite (real-time metrics, scheduler controls, field change audit history & verification breakdown)
- **Crawling & Discovery**: Requests, BeautifulSoup4, SSRF Security Guard, Robots.txt Policy Manager, Domain Throttling
- **Extraction Engine**: Deterministic DOM parser, Indian date parser, monetary benefit parser, page classifier (`SCHOLARSHIP_DETAIL`, `LISTING`, `APPLICATION_PORTAL`, `GENERIC_PAGE`), and field-level evidence tracker
- **Verification Engine (Phase 4)**: 100-point deterministic scoring model, 7 mandatory verification gates, field evidence quality ratings (`SUPPORTED`, `WEAK_EVIDENCE`, `NOT_FOUND`, `CONFLICTING`, `STALE`), strict `>=95%` confidence requirement, and persistent audit history. Zero LLM reliance for confidence scoring.
- **Repeatable Scheduler & Change Engine (Phase 5)**: Thread-safe background crawl scheduler with overlap prevention, candidate prioritization (existing scholarships due for refresh first, then official seeds), whitespace noise filtering, non-destructive historical evidence preservation (`is_current = False`), field-level change history tracking (`previous_value` $\rightarrow$ `new_value`), lifecycle transitions, and automatic re-verification triggers.
- **Validation**: Pydantic v2
- **Testing**: Pytest (**78 automated tests** passing covering change detection, whitespace noise filtering, lifecycle transitions, network error handling, scheduler overlap prevention, verification scoring, mandatory gates, extraction, security, and endpoints)

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
│   │   ├── App.tsx                  # Dashboard interface, scheduler banner, changes tab & modals
│   │   ├── App.css                  # UI styling, diff view, gate pills & timeline styles
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
└── backend/                         # FastAPI backend service
    ├── requirements.txt             # Python dependencies
    ├── pyproject.toml               # Pytest configuration
    ├── app/
    │   ├── main.py                  # FastAPI application entrypoint & lifespan management
    │   ├── core/config.py           # Configuration & environment variables
    │   ├── db/
    │   │   ├── database.py          # SQLite engine & session factory
    │   │   ├── models.py            # Models (Scholarship, FieldEvidence, ScholarshipChangeHistory, etc.)
    │   │   └── init_db.py           # Table initialization & safe non-destructive migrations
    │   ├── api/routes/
    │   │   ├── health.py            # GET /api/health
    │   │   ├── discovery.py         # /api/discovery/sources, /run, /candidates
    │   │   ├── crawl.py             # /api/crawl/runs, /run, /status, /candidates/{id}
    │   │   ├── scholarships.py      # /api/scholarships, /{id}, /{id}/evidence, /{id}/changes, /{id}/verification
    │   │   ├── extraction.py        # /api/extraction/run, /runs
    │   │   ├── verification.py      # /api/verification/run, /summary, /history/{id}, /detail/{id}
    │   │   ├── changes.py           # /api/changes/recent (paginated change history audit)
    │   │   └── scheduler.py         # /api/scheduler/start, /stop, /status
    │   ├── models/schemas.py        # Pydantic request/response schemas
    │   └── services/
    │       ├── discovery/           # Candidate discovery & URL normalization
    │       ├── crawling/            # Ethical HTTP crawler, SSRF guard, robots.txt & CrawlScheduler
    │       ├── extraction/          # Deterministic field extraction & evidence engine
    │       ├── verification/        # Deterministic scoring, mandatory gates & evidence evaluator
    │       └── lifecycle/           # ChangeDetector & LifecycleManager
    └── tests/                       # Automated backend tests (78 tests)
```

---

## Phase 5: Recrawling, Change Detection & Scholarship Lifecycle

### 1. Repeatable Crawl Scheduler

- **Thread-Safe Singleton (`CrawlScheduler`)**: Enforces atomic job acquisition (`is_running_job`). Rejects concurrent manual or timer-triggered crawl requests with `OVERLAPPING_REJECTED` (HTTP 409).
- **Candidate Prioritization**:
  1. Previously extracted scholarships due for refresh or re-verification.
  2. Discovered candidate pages from primary government and educational sources.
  3. Polite delays and robots.txt rules applied per domain.
- **Graceful Lifecycle**: Managed start/stop methods with thread synchronization, configurable crawl interval, and maximum candidates per run.

### 2. Field-Level Change Detection & Noise Filtering

- **Whitespace & Formatting Normalization**: Compares normalized string representations (`normalize_value`), stripping extra spaces, tabs, line breaks, and punctuation formatting to eliminate noise from HTML restructuring or advertising widgets.
- **Empty Observation Protection**: When a re-crawl yields `None` or insufficient content for an existing field, the system **strictly preserves the prior value and evidence**. A failed fetch or layout change is **never** treated as a confirmed deletion.
- **Audit History Schema (`ScholarshipChangeHistory`)**:
  - `change_id`, `scholarship_id`, `field_name`
  - `previous_value`, `new_value`
  - `detection_timestamp`
  - `previous_evidence_id`, `new_evidence_id`
  - `official_source_url`, `crawl_run_id`
  - `change_classification` (`CRITICAL_UPDATE`, `DEADLINE_EXTENSION`, `DEADLINE_PASSED`, `UPDATE`, `INITIAL_DISCOVERY`)
  - `requires_reverification` (Boolean flag)
  - `is_reviewed` (Boolean flag)

### 3. Preserving Historical Observations

- Prior `FieldEvidence` records are **never deleted or silently overwritten**.
- When an updated value is accepted, the previous evidence row has `is_current = False` set, and a new `FieldEvidence` row is persisted with `is_current = True`.
- Both old and new evidence IDs are linked in `ScholarshipChangeHistory` for full traceability.

### 4. Lifecycle Transitions & Freshness Rules

| State | Transition Criteria |
| :--- | :--- |
| **`ACTIVE`** | Closing date is in the future (or rolling/ongoing) and evidence is fresh ($\le 90$ days). |
| **`EXPIRING_SOON`** | Closing date is active but within the configurable threshold ($\le 14$ days from current evaluation date). |
| **`EXPIRED`** | Closing date has passed relative to the current evaluation clock. |
| **`NO_LONGER_VERIFIABLE`** | Official source permanently returns HTTP 404 or explicit credible removal notice is detected. |
| **`REVIEW_REQUIRED`** | Extraction ambiguity, failed verification gate, or unresolved contradictions. |
| **`STALE`** | Evidence fetch age exceeds 90 days or overdue for re-verification. |

### 5. Automatic Re-Verification

Whenever any of the critical fields (`name`, `provider`, `amount_benefit`, `eligibility_summary`, `closing_date`, `application_url`) change:
1. `requires_reverification = True` is flagged in `ScholarshipChangeHistory`.
2. `VerificationEngine.evaluate_scholarship()` is immediately executed.
3. Verification records and gates are re-computed and stored transactionally.

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

## REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/crawl/run` | Trigger a controlled crawl and change-detection update cycle |
| `GET` | `/api/crawl/status` | Retrieve current crawl job and scheduler execution status |
| `GET` | `/api/crawl/runs` | List crawl-run history |
| `GET` | `/api/scholarships/{id}/changes` | List field-level change history for a scholarship |
| `GET` | `/api/changes/recent` | List paginated recent field changes across all scholarships |
| `POST` | `/api/scheduler/start` | Start the background recurring crawl scheduler |
| `POST` | `/api/scheduler/stop` | Gracefully stop the background recurring crawl scheduler |
| `GET` | `/api/scheduler/status` | Report scheduler daemon status and next planned run |
| `GET` | `/api/scholarships` | List extracted scholarships with confidence and verification status |
| `GET` | `/api/scholarships/{id}/evidence` | Inspect verbatim field-level evidence |
| `GET` | `/api/scholarships/{id}/verification` | View 100-pt score breakdown and 7 gate evaluations |
| `GET` | `/api/verification/summary` | Summary of verified, review required, and expired records |

---

## Windows PowerShell Setup & Run Instructions

### Prerequisites
- Python 3.12+ (Python 3.14 verified)
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

Execute the 78-test pytest suite validating change detection, noise filtering, lifecycle rules, scheduler overlap prevention, verification scoring, gates, boundary conditions, field extraction, dates, amounts, security, and APIs:

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
- **Scheduler Status**: [http://127.0.0.1:8000/api/scheduler/status](http://127.0.0.1:8000/api/scheduler/status)
- **Recent Changes**: [http://127.0.0.1:8000/api/changes/recent](http://127.0.0.1:8000/api/changes/recent)
- **Verification Summary**: [http://127.0.0.1:8000/api/verification/summary](http://127.0.0.1:8000/api/verification/summary)
- **Scholarships API**: [http://127.0.0.1:8000/api/scholarships](http://127.0.0.1:8000/api/scholarships)
- **API Documentation (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 4. Start the Frontend Dashboard

```powershell
npm run dev --prefix frontend
```

Open [http://localhost:5173](http://localhost:5173) in your browser.
