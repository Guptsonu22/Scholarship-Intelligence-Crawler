# Technical Note: Scholarship Intelligence Crawler for Indian Students

**Author**: EDXSO AI Engineer Intern Candidate  
**Project**: Assignment 2 — Scholarship Intelligence Crawler for Indian Students  
**Status**: Final Acceptance Audit & Submission Package (Phase 7 Audited)  
**Evaluation Date**: October 2026  

---

## 1. Problem Statement and Approach

Indian higher education students navigate a fragmented landscape of scholarship opportunities across central ministries, state welfare departments, premier academic institutions, and corporate CSR foundations. Existing scholarship aggregators suffer from:
1. **Unverified and Outdated Data**: Expired deadlines, obsolete stipend figures, and inactive portals are frequently presented as active schemes.
2. **Lack of Evidence**: Claimed awards lack direct citations to authoritative government gazettes or official web elements.
3. **Black-Box Confidence Scoring**: Synthetic LLM-generated hallucinated "confidence" numbers replace rigorous, deterministic verification.
4. **No Change Detection**: Websites quietly update eligibility criteria, extend deadlines, or retire schemes without student notification.

### Our Approach
We designed and implemented a **deterministic, evidence-based intelligence crawler** adhering to four core engineering principles:
- **Primary Source Exclusivity**: Authoritative seeds restricted to official government (`.gov.in`, `.nic.in`, `.res.in`), university (`.ac.in`, `.edu.in`), and registered CSR trusts (`.org`).
- **Verbatim Evidence Anchoring**: Every critical attribute (identity, provider, monetary benefits, eligibility criteria, application portal, and closing dates) is anchored to specific HTML selectors and exact source excerpts.
- **Deterministic 100-Point Verification Engine**: Verification decisions require a deterministic score $\ge 95\%$ **and** unconditional passage of seven mandatory gates. No LLM is permitted to assign confidence scores.
- **Immutable Audit Trails and Lifecycle State Machine**: Historical observations are preserved without deletion. All status transitions (`ACTIVE`, `EXPIRING_SOON`, `EXPIRED`, `NO_LONGER_VERIFIABLE`) maintain full historical lineage.

---

## 2. Architecture and Technology Stack

```
┌────────────────────────────────────────────────────────────────────────┐
│                        React + TypeScript Frontend                     │
│  (Real-Time Metric Cards, Gate Status Pills, Diff Modal, Evidence DOM) │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ HTTP / REST
┌───────────────────────────────────▼────────────────────────────────────┐
│                         FastAPI Backend Engine                         │
│  ┌───────────────────────┬──────────────────────┬────────────────────┐ │
│  │   Discovery Service   │   Ethical Crawler    │  Page Assessor &   │ │
│  │  (URL Normalization,  │ (SSRF Guard, Robots, │  Field Extractor   │ │
│  │   Seed Categorizer)   │  Domain Throttling)  │ (Deterministic DOM)│ │
│  └───────────────────────┴──────────────────────┴────────────────────┘ │
│  ┌───────────────────────┬──────────────────────┬────────────────────┐ │
│  │  Verification Engine  │  Lifecycle Manager   │  Crawl Scheduler   │ │
│  │ (100-Pt Scoring Model,│ (Staleness Checks &  │ (Thread-Safe Lock, │ │
│  │  7 Mandatory Gates)   │  State Transitions)  │ Overlap Preventer) │ │
│  └───────────────────────┴──────────────────────┴────────────────────┘ │
└───────────────────────────────────▲────────────────────────────────────┘
                                    │ SQLAlchemy ORM
┌───────────────────────────────────▼────────────────────────────────────┐
│                      SQLite Persistent Database                        │
│ (scholarships, field_evidence, verification_records, change_history)   │
└────────────────────────────────────────────────────────────────────────┘
```

- **Backend**: FastAPI (Python 3.12+) asynchronous REST API with Pydantic v2 schemas.
- **Database**: SQLite persistent local storage (`data/scholarships.db`) accessed via SQLAlchemy ORM with foreign key integrity.
- **Frontend**: React 19 + TypeScript + Vite with dynamic API polling, responsive modal diff views, and verification gate breakdowns.
- **Security & Crawling**: Custom `EthicalHttpClient` enforcing RFC private network SSRF blocking (blocking loopbacks, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, AWS/GCP cloud metadata `169.254.169.254`), polite rate limiting (2.0s per-domain backoff), and `RobotsPolicyManager`.

---

## 3. Discovery, Extraction, Evidence, Scoring & Lifecycle Methodology

### Discovery & Classification
Incoming URLs are normalized by removing URL tracking parameters (`utm_*`, `ref`), lowercasing hosts, and resolving relative links. Candidate links are classified across four target sectors:
1. `CENTRAL_GOVERNMENT`: AICTE, UGC, CSIR, National Scholarship Portal (`scholarships.gov.in`).
2. `STATE_GOVERNMENT`: West Bengal OASIS (`oasis.gov.in`), Karnataka SSP, MahaDBT.
3. `UNIVERSITY`: IIT Kanpur, IIT Bhubaneswar, Azim Premji University.
4. `TRUST_FOUNDATION` / `CORPORATE_CSR`: Tata Trusts, Sitaram Jindal Foundation, Narotam Sekhsaria, Aditya Birla, Persistent Foundation.

### Deterministic Extraction & Verbatim Evidence
Each crawled page is evaluated by `PageAssessor` to distinguish specific opportunities (`SCHOLARSHIP_DETAIL`) from directories (`LISTING`), portals (`APPLICATION_PORTAL`), or homepages. `FieldExtractor` applies targeted DOM extraction for:
- **Identity & Provider**: H1 headers, portal titles, and authoritative organizational markers.
- **Financial Benefit**: INR patterns (`₹`, `Rs`, `lakh`, `per month`, `per annum`), fee waivers, and book grants.
- **Eligibility & Category**: Domicile requirements, degree/course levels, reservation criteria (SC/ST/OBC/Disability), and income thresholds.
- **Deadline**: Standardized Indian date formats (`DD/MM/YYYY`, `DD-MM-YYYY`, text dates).
- **Evidence Record (`FieldEvidence`)**: Persists `field_name`, `extracted_value`, `source_url`, `evidence_text` (verbatim snippet), `html_selector`, `content_hash`, and `quality_rating` (`SUPPORTED`, `WEAK_EVIDENCE`, `CONFLICTING`).

### Verification Engine & Mandatory Gates
A scholarship record can be verified **only** if its score is $\ge 95\%$ **and** all seven mandatory gates evaluate to `PASS` (or `NOT_APPLICABLE` for non-portal awards):
1. **Official Source Gate**: Source URL domain must match an authorized government, university, or registered trust registry.
2. **Scholarship Identity Gate**: Opportunity title must represent a distinct, singular funding program rather than an umbrella portal.
3. **Critical Field Evidence Gate**: Critical fields (`name`, `provider`, `amount_benefit`, `eligibility_summary`) must be backed by supported DOM evidence.
4. **Contradiction Gate**: No conflicting benefit tiers or overlapping incompatible scheme descriptions.
5. **Freshness Gate**: Fetch timestamp must be fresh (0–90 days).
6. **Application Link Gate**: Valid application URL on an official provider portal or verified apex platform.
7. **Lifecycle Gate**: Closing date must not have elapsed as of the evaluation timestamp.

### Lifecycle Management
The lifecycle state machine tracks opportunities through:
$$\text{ACTIVE} \xrightarrow{\le 14\text{ days}} \text{EXPIRING\_SOON} \xrightarrow{\text{past deadline}} \text{EXPIRED}$$
If an authoritative endpoint returns HTTP 404, the status transitions to `NO_LONGER_VERIFIABLE`. Transient HTTP errors (500, 503, timeouts) strictly preserve existing records without marking opportunities withdrawn.

---

## 4. Actual Audited Results (Phase 7 Audit)

The live database (`data/scholarships.db`) was independently audited without resetting or modifying historical records.

| Metric | Target / Claim | Audited Result | Verification Status |
| :--- | :---: | :---: | :---: |
| **Total Scholarship Records** | $\ge 20$ | **21 distinct records** | **PASS** |
| **VERIFIED Records ($\ge 95\%$ + 7 Gates)** | $\ge 10$ | **10 records (all 96.0%)** | **PASS** |
| **REVIEW_REQUIRED Records** | $>0$ | **11 records (62.0% – 94.0%)** | **PASS** |
| **Field Evidence Records** | $>100$ | **120 items** | **PASS** |
| **Verification Audit Records** | $>100$ | **110 records** | **PASS** |
| **Primary-Source Domains** | $\ge 4$ sectors | **10 domains across 4 sectors** | **PASS** |
| **Duplicate / Suspicious Records** | 0 | **0 duplicate URLs / names** | **PASS** |
| **Backend Automated Tests** | All passing | **83 passed in 5.15s** | **PASS** |
| **Frontend Production Build** | Zero errors | **Vite build clean in 1.29s** | **PASS** |

### Verified Scholarships Breakdown
All 10 `VERIFIED` records represent distinct, authentic scholarships:
1. `#2` **AICTE PG Scholarship Scheme** (₹12,400/month, Central Gov) — Score: 96.0%
2. `#3` **AICTE PRAGATI Scheme for Girls** (₹50,000/annum, Central Gov) — Score: 96.0%
3. `#4` **AICTE SAKSHAM Scheme for Differently Abled** (₹50,000/annum, Central Gov) — Score: 96.0%
4. `#5` **AICTE Swanath Scheme** (₹50,000/annum, Central Gov) — Score: 96.0%
5. `#6` **AICTE ADF (Doctoral Fellowship) Scheme** (₹37,000–₹42,000/month, Central Gov) — Score: 96.0%
6. `#7` **AICTE Yashasvi Scholarship Scheme** (₹18,000–₹50,000/annum, Central Gov) — Score: 96.0%
7. `#8` **West Bengal OASIS Pre/Post-Matric Scheme** (Tuition + maintenance, State Gov) — Score: 96.0%
8. `#16` **AICTE PMSSS J&K and Ladakh Special Scheme** (₹1.25L fees + ₹1.00L allowance, Central Gov) — Score: 96.0%
9. `#17` **CSIR Junior Research Fellowship (JRF-NET)** (₹37,000/month + HRA, Central Gov) — Score: 96.0%
10. `#18` **CSIR Partial Financial Assistance (PFA) Scheme** (₹30,000 travel assistance, Central Gov) — Score: 96.0%

---

## 5. Demonstration of Change Detection and Expired/Stale Handling

### Change Detection
- **Live Portal Stability**: Official government scholarship portals (`aicte.gov.in`, `csirhrdg.res.in`, `oasis.gov.in`) did not publish altered guidelines during our observation window. Per assignment rules, zero artificial changes were injected into the live database.
- **Deterministic Test Fixtures**: Validated via `backend/tests/test_change_detection.py` (9 tests passing):
  - *Example 1 (Deadline Extension)*: `closing_date` extended from `2026-10-31` $\rightarrow$ `2026-11-30`. Detected classification: `CRITICAL_DEADLINE`, `requires_reverification: True`. Prior evidence set to `is_current: False`.
  - *Example 2 (Benefit Update & Noise Filter)*: Extra whitespace `"  ₹50,000 / year  "` normalized without generating false change records; real benefit increase `₹50,000` $\rightarrow$ `₹60,000` flagged with `BENEFIT_UPDATE` and linked to new `FieldEvidence` row.

### Expired and Stale Lifecycle Handling
- **Real Database Example 1 (Past Application Deadline)**: Scholarship `#1` (`AICTE Students Development schemes`, `closing_date: 2026-09-28`). Evaluated against current clock (`2026-10-13`). Result: `lifecycle_status: EXPIRED`, `lifecycle_gate: FAIL`, confidence score docked to 62.0%, status: `REVIEW_REQUIRED`.
- **Real Database Example 2 (Retired Portal Endpoint)**: AICTE PMSSS Batch 2023–24 portal candidate (`https://www.aicte.gov.in/PMSSS-2023-24`). Probe returned HTTP 404 Not Found. Lifecycle transition logic accurately classifies dead scheme URLs as `NO_LONGER_VERIFIABLE`.
- **Stale Freshness Policy**: Records un-crawled for $>90$ days trigger `is_stale = True`, penalizing the freshness criterion and prompting the scheduler for priority re-crawl.

---

## 6. Limitations and Reproducibility Instructions

### Known Limitations
1. **Portal WAF & Captchas**: Portals utilizing client-side anti-bot challenges (e.g. MahaDBT Cloudflare turnstiles) require headless browser integration for automated live extraction.
2. **PDF-Embedded Guidelines**: Certain university notifications exist exclusively as scanned PDFs; our current pipeline extracts from HTML DOM and flags PDF links for manual review.

### Reproducibility Commands
```powershell
# 1. Run all backend regression and security tests (83 passing)
backend\.venv\Scripts\pytest.exe backend\tests\ -v

# 2. Run frontend production build (zero errors)
npm run build --prefix frontend

# 3. Start Backend REST API
backend\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --app-dir backend

# 4. Start Frontend UI
npm run dev --prefix frontend
```
All endpoints and metrics can be verified at `http://127.0.0.1:8000/docs` and `http://localhost:5173`.
