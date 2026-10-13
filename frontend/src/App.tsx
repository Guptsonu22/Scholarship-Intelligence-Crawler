import { useState, useEffect } from 'react'
import './App.css'

interface HealthResponse {
  status: string
  app_name: string
  version: string
  environment: string
  database: string
  timestamp: string
}

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [lastChecked, setLastChecked] = useState<string | null>(null)

  const checkHealth = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('http://127.0.0.1:8000/api/health')
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
      const data: HealthResponse = await response.json()
      setHealth(data)
      setLastChecked(new Date().toLocaleTimeString())
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to connect to backend')
      setHealth(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    checkHealth()
  }, [])

  return (
    <div className="container">
      <header className="header">
        <div className="badge">EDXSO Assignment 2 • Phase 1 Foundation</div>
        <h1>Scholarship Intelligence Crawler</h1>
        <p className="subtitle">
          High-accuracy scholarship discovery, deterministic verification, and lifecycle tracking for Indian students.
        </p>
      </header>

      <main className="main-content">
        <section className="card health-card">
          <div className="card-header">
            <h2>Backend & Database Status</h2>
            <button
              type="button"
              className="refresh-btn"
              onClick={checkHealth}
              disabled={loading}
            >
              {loading ? 'Checking...' : 'Ping Backend API'}
            </button>
          </div>

          {error && (
            <div className="status-banner error">
              <span className="dot error"></span>
              <div>
                <strong>Backend Unreachable:</strong> {error}
                <p className="help-text">
                  Ensure the FastAPI backend is running via <code>uvicorn app.main:app --reload</code> on port 8000.
                </p>
              </div>
            </div>
          )}

          {health && (
            <div className="status-grid">
              <div className="status-item">
                <span className="label">Service Status</span>
                <span className="value status-badge ok">
                  <span className="dot ok"></span>
                  {health.status.toUpperCase()}
                </span>
              </div>
              <div className="status-item">
                <span className="label">Database Connection</span>
                <span className="value status-badge ok">
                  <span className="dot ok"></span>
                  {health.database.toUpperCase()} (SQLite)
                </span>
              </div>
              <div className="status-item">
                <span className="label">API Version</span>
                <span className="value">{health.version}</span>
              </div>
              <div className="status-item">
                <span className="label">Environment</span>
                <span className="value">{health.environment}</span>
              </div>
              <div className="status-item full-width">
                <span className="label">Backend UTC Timestamp</span>
                <span className="value timestamp">{health.timestamp}</span>
              </div>
            </div>
          )}

          {lastChecked && (
            <div className="last-checked">
              Last probed at: {lastChecked}
            </div>
          )}
        </section>

        <section className="card architecture-card">
          <h2>Project Roadmap & Architecture</h2>
          <div className="roadmap-grid">
            <div className="phase-badge completed">
              <span className="phase-num">Phase 1</span>
              <h3>Project Foundation</h3>
              <p>FastAPI backend, SQLite DB, React/Vite/TS dashboard, configuration, and test suites.</p>
              <span className="state-tag active">COMPLETED</span>
            </div>
            <div className="phase-badge pending">
              <span className="phase-num">Phase 2</span>
              <h3>Authentic Crawling</h3>
              <p>Targeting NSP, State Portals, UGC, Buddy4Study, CSR & Philanthropic foundations.</p>
              <span className="state-tag">PLANNED</span>
            </div>
            <div className="phase-badge pending">
              <span className="phase-num">Phase 3</span>
              <h3>Deterministic Extraction</h3>
              <p>Extracting title, eligibility, benefits, deadline, and field-level evidence snippets.</p>
              <span className="state-tag">PLANNED</span>
            </div>
            <div className="phase-badge pending">
              <span className="phase-num">Phase 4</span>
              <h3>Verification & Scoring</h3>
              <p>Explainable confidence scoring; strictly ≥95% required for VERIFIED status.</p>
              <span className="state-tag">PLANNED</span>
            </div>
            <div className="phase-badge pending">
              <span className="phase-num">Phase 5</span>
              <h3>Change Detection & UI</h3>
              <p>Audit logging, diff tracking, status lifecycle (Active, Stale, Expired), and full UI.</p>
              <span className="state-tag">PLANNED</span>
            </div>
          </div>
        </section>
      </main>

      <footer className="footer">
        <p>Scholarship Intelligence Crawler • Zero hallucinated data policy • Windows PowerShell native</p>
      </footer>
    </div>
  )
}
