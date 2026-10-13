# Scholarship Intelligence Crawler: Demo & Evaluation Walkthrough

**Target**: Evaluators & Technical Reviewers  
**Repository**: `Scholarship Intelligence Crawler for Indian Students`  
**OS Target**: Windows (PowerShell)  
**Database**: Pre-populated SQLite database at `data/scholarships.db`  

---

## 1. Prerequisites & Quick Start

Ensure Python 3.12+ and Node.js 18+ are available in your path.

### Terminal 1: Start the Backend Service
```powershell
# From project root
backend\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --app-dir backend
```
*Expected Output:*
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Database tables verified and initialized.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Terminal 2: Start the Frontend UI
```powershell
# From project root
npm run dev --prefix frontend
```
*Expected Output:*
```
  VITE v8.3.4  ready in 180 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

---

## 2. Step-by-Step Evaluator Walkthrough

### Step 1: Health & API Documentation
1. Open your browser and navigate to:
   - **Health Endpoint**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
     - Confirm `"status": "ok"` and `"database": "connected"`.
   - **Interactive OpenAPI Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
     - View all 20+ documented endpoints across Discovery, Crawl, Extraction, Verification, Changes, and Scheduler.

### Step 2: Main Dashboard Metrics
1. Navigate to [http://localhost:5173/](http://localhost:5173/).
2. Verify the top metric cards (dynamically populated from `GET /api/verification/summary` and `GET /api/scholarships`):
   - **Total Extracted**: `22`
   - **Verified (>=95%)**: `10`
   - **Review Required**: `12`
   - **Active Opportunities**: `21`
   - **Expired Opportunities**: `1`
3. Notice the live scheduler banner at the top showing current scheduler state (`IDLE / STOPPED`) with action buttons (`Start 24h Scheduler`, `Run Immediate Crawl`).

### Step 3: Inspect an Authentic VERIFIED Scholarship (#2)
1. In the Scholarships table, click on record **#2: PG Scholarship Scheme** (or click **"View Evidence"**).
2. The modal displays:
   - **Official Provider**: `All India Council for Technical Education`
   - **Monetary Benefit**: `₹12,400 per month`
   - **Course Level**: `Diploma / ITI / Polytechnic / PG`
   - **Application URL**: `https://portal.aicte.gov.in/aicte/app/partnerportal/enu`
   - **Confidence Score**: `96.0%` with green **VERIFIED** badge.
3. Click **"Verification Breakdown"**:
   - Confirm all **7 Mandatory Gates** evaluate to **PASS**:
     - *Official Source Gate*: PASS (`CENTRAL_GOVERNMENT` on `aicte.gov.in`)
     - *Scholarship Identity Gate*: PASS (Distinct funding scheme)
     - *Field Evidence Gate*: PASS (6 supported items)
     - *Contradiction Gate*: PASS (No conflicting rules)
     - *Freshness Gate*: PASS (0 days old)
     - *Application Link Gate*: PASS (Authorized portal)
     - *Lifecycle Gate*: PASS (Active window)
   - View verbatim evidence snippets and exact CSS/DOM selectors (`h1`, `source_authority`, `scheme_guidelines`, `a`).

### Step 4: Inspect a REVIEW_REQUIRED / EXPIRED Record (#1)
1. In the Scholarships table, locate record **#1: Students Development schemes**.
2. Notice:
   - **Status**: `REVIEW_REQUIRED` (Orange badge)
   - **Lifecycle**: `EXPIRED` (Red badge)
   - **Score**: `62.0%`
3. Click **"Verification Breakdown"**:
   - Notice why it failed:
     - *Identity Gate*: Failed (represents an umbrella portal rather than an individual grant).
     - *Lifecycle Gate*: Failed (`closing_date: 2026-09-28` is in the past).
     - *Evidence Gate*: Weak container citations docked score by 15 points.
   - This proves the engine **refuses to verify** umbrella portals or expired schemes even when hosted on `.gov.in` domains.

### Step 5: Inspect State Government, University, and CSR Records
1. Use the **Category Filter** dropdown:
   - Filter by **STATE_GOVERNMENT**: Record `#8 West Bengal OASIS` (Score: 96.0%, Verified).
   - Filter by **UNIVERSITY**: Record `#9 IIT Kanpur MCM` (Score: 74.0%, Review Required) and `#10 Azim Premji University` (Score: 94.0%).
   - Filter by **TRUST_FOUNDATION / CORPORATE_CSR**: Record `#11 Tata Trusts` (Score: 91.0%) and `#13 Sitaram Jindal Foundation` (Score: 91.0%).
2. Notice how scores honestly reflect DOM evidence completeness without inflating non-governmental awards to 95%.

### Step 6: Recrawling & Change Detection Engine
1. Click the **"Changes Audit"** tab on the dashboard:
   - Displays real-time changes logged in `scholarship_change_history`.
2. Review the automated change detection test suite:
   ```powershell
   backend\.venv\Scripts\pytest.exe backend\tests\test_change_detection.py -v
   ```
   - Validates noise filtering (extra whitespace ignored), critical deadline extension detection, benefit updates, non-destructive historical evidence preservation, and scheduler concurrency locks.

---

## 3. Regression Testing & Production Build Commands

Run these commands in PowerShell to independently verify code quality and build integrity:

```powershell
# Run the complete test suite (83 passing tests)
backend\.venv\Scripts\pytest.exe backend\tests\ -v

# Run the frontend production build (clean bundle generation)
npm run build --prefix frontend
```

---

## 4. Summary of Verification Rules

| Decision | Threshold Requirement | Gate Requirement |
| :--- | :---: | :---: |
| **VERIFIED** | Score $\ge 95.0\%$ | All 7 Gates must evaluate to `PASS` or `NOT_APPLICABLE` |
| **REVIEW_REQUIRED** | Score $< 95.0\%$ OR any failed gate | Any single `FAIL` gate immediately demotes status |
| **EXPIRED** | Closing date elapsed | Lifecycle status transitions; docked deadline points |
