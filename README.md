# Scholarship Intelligence Crawler for Indian Students

**EDXSO AI Engineer Intern Assignment 2**  
*Authentic scholarship opportunity discovery, deterministic extraction, verifiable confidence scoring, and lifecycle change detection.*

---

## Architecture Overview

- **Backend**: FastAPI (Python 3.12+)
- **Database**: SQLite (persistent local storage under `data/scholarships.db`)
- **Frontend**: React + TypeScript + Vite
- **Crawling & Extraction**: Requests, BeautifulSoup4 (deterministic parsing, zero hallucinated data)
- **Validation**: Pydantic v2
- **Testing**: Pytest

---

## Project Structure

```
├── .env.example                     # Environment template
├── .gitignore                       # Git exclusion rules
├── README.md                        # Setup and run instructions
├── data/                            # SQLite database storage
├── docs/
│   └── architecture.md              # Detailed architecture documentation
├── frontend/                        # React + TypeScript + Vite application
│   ├── src/
│   │   ├── App.tsx                  # Foundation dashboard & health monitor
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
    │   ├── db/                      # Database engine & table initialization
    │   ├── api/routes/health.py     # GET /api/health endpoint
    │   ├── models/schemas.py        # Pydantic schemas
    │   └── services/                # Modular domain services
    │       ├── discovery/           # Candidate feeds
    │       ├── crawling/            # Polite HTTP fetching
    │       ├── extraction/          # Deterministic field extraction
    │       ├── verification/        # Evidence validation (>=95% rule)
    │       └── change_detection/    # Lifecycle & diff history
    └── tests/                       # Automated backend tests
```

---

## Windows PowerShell Setup & Run Instructions

### Prerequisites
- Python 3.12+ (Python 3.14 recommended)
- Node.js 18+ and npm

### 1. Clone & Environment Configuration

Open Windows PowerShell in the project directory:

```powershell
Copy-Item .env.example .env
```

### 2. Backend Setup

Create the Python virtual environment and install backend dependencies:

```powershell
# Create virtual environment in backend/.venv
python -m venv backend/.venv

# Activate virtual environment
.\backend\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Run Backend Tests

Run the automated pytest test suite to verify database connectivity and the health endpoint:

```powershell
$env:PYTHONPATH="backend;backend/app"
.\backend\.venv\Scripts\python.exe -m pytest backend/tests
```

### 4. Start the Backend API

Start the FastAPI backend with hot-reload enabled:

```powershell
$env:PYTHONPATH="backend;backend/app"
.\backend\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Health Endpoint**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- **Interactive API Docs (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 5. Frontend Setup & Run

In a separate Windows PowerShell window:

```powershell
# Navigate to frontend and install dependencies
cd frontend
npm install

# Start Vite dev server
npm run dev
```

- **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)

---

## Phase 1 Implementation Status

- [x] Project workspace scaffolding with clean separation of concerns
- [x] Python virtual environment configured (`backend/.venv`)
- [x] Backend dependencies installed (`FastAPI`, `Pydantic v2`, `SQLAlchemy`, `Requests`, `BeautifulSoup4`, `APScheduler`, `pytest`)
- [x] React + TypeScript + Vite frontend scaffolded and built with 0 errors
- [x] Windows-compatible SQLite configuration (`data/scholarships.db`) with automatic table creation
- [x] `GET /api/health` endpoint returning server status and database connectivity
- [x] Automated pytest test suite passing 4/4 tests
- [x] Comprehensive `.gitignore` protecting secrets, virtual environments, node_modules, and databases
- [x] Architecture documentation in `docs/architecture.md`
