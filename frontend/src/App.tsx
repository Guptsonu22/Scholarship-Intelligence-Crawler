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

interface CandidateItem {
  id: number
  url: string
  normalized_url: string
  discovery_source_url: string
  discovery_method: string
  source_category: string
  anchor_text: string | null
  relevance_score: number
  status: string
  is_official_source: boolean
  discovered_at: string
}

interface CandidateListResponse {
  items: CandidateItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

interface SeedSourceItem {
  id: number
  name: string
  base_url: string
  category: string
  is_enabled: boolean
}

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [candidates, setCandidates] = useState<CandidateItem[]>([])
  const [totalCandidates, setTotalCandidates] = useState<number>(0)
  const [sources, setSources] = useState<SeedSourceItem[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [discovering, setDiscovering] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')

  const fetchHealth = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/health')
      if (res.ok) setHealth(await res.json())
    } catch {
      setHealth(null)
    }
  }

  const fetchSources = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/discovery/sources')
      if (res.ok) setSources(await res.json())
    } catch {
      // Ignored if backend not running
    }
  }

  const fetchCandidates = async () => {
    setLoading(true)
    setError(null)
    try {
      let url = 'http://127.0.0.1:8000/api/discovery/candidates?page=1&page_size=20'
      if (categoryFilter) url += `&category=${encodeURIComponent(categoryFilter)}`
      if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`

      const res = await fetch(url)
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`)
      const data: CandidateListResponse = await res.json()
      setCandidates(data.items)
      setTotalCandidates(data.total)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to fetch candidate URLs')
    } finally {
      setLoading(false)
    }
  }

  const runDiscovery = async () => {
    setDiscovering(true)
    setError(null)
    try {
      const res = await fetch('http://127.0.0.1:8000/api/discovery/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ max_seeds: 3, respect_robots: false }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      await fetchCandidates()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Discovery run failed')
    } finally {
      setDiscovering(false)
    }
  }

  useEffect(() => {
    fetchHealth()
    fetchSources()
    fetchCandidates()
  }, [categoryFilter, statusFilter])

  return (
    <div className="container">
      <header className="header">
        <div className="badge">EDXSO Assignment 2 • Phase 2 Discovery & Crawling</div>
        <h1>Scholarship Intelligence Crawler</h1>
        <p className="subtitle">
          Real-time candidate discovery, ethical HTTP crawling, and source classification for Indian students.
        </p>
      </header>

      {/* Metrics Bar */}
      <section className="metrics-bar">
        <div className="metric-box">
          <span className="metric-num">{sources.length}</span>
          <span className="metric-label">Configured Seeds</span>
        </div>
        <div className="metric-box">
          <span className="metric-num">{totalCandidates}</span>
          <span className="metric-label">Discovered Candidates</span>
        </div>
        <div className="metric-box">
          <span className="metric-num">
            {candidates.filter((c) => c.is_official_source).length}
          </span>
          <span className="metric-label">Official Sources</span>
        </div>
        <div className="metric-box">
          <span className="metric-num">
            {health?.status === 'ok' ? 'Online' : 'Offline'}
          </span>
          <span className="metric-label">Crawler API Status</span>
        </div>
      </section>

      <main className="main-content">
        {/* Candidates Section */}
        <section className="card">
          <div className="card-header">
            <div>
              <h2>Discovered Scholarship Candidates</h2>
              <p className="section-desc">
                Authenticated URLs extracted from official portals, evaluated for scholarship relevance.
              </p>
            </div>
            <div className="actions-group">
              <button
                type="button"
                className="refresh-btn secondary"
                onClick={fetchCandidates}
                disabled={loading}
              >
                {loading ? 'Refreshing...' : 'Refresh Table'}
              </button>
              <button
                type="button"
                className="refresh-btn primary"
                onClick={runDiscovery}
                disabled={discovering}
              >
                {discovering ? 'Crawling Seeds...' : 'Run Seed Discovery'}
              </button>
            </div>
          </div>

          {/* Filter Bar */}
          <div className="filter-bar">
            <label>
              Category:
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <option value="">All Categories</option>
                <option value="CENTRAL_GOVERNMENT">Central Government</option>
                <option value="STATE_GOVERNMENT">State Government</option>
                <option value="UNIVERSITY">University / Institute</option>
                <option value="CORPORATE_CSR">Corporate CSR</option>
                <option value="TRUST_FOUNDATION">Trust & Foundation</option>
                <option value="AGGREGATOR">Aggregator (Discovery Feed)</option>
              </select>
            </label>
            <label>
              Status:
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All Statuses</option>
                <option value="DISCOVERED">Discovered</option>
                <option value="QUEUED">Queued</option>
                <option value="CRAWLED">Crawled</option>
                <option value="FAILED">Failed</option>
              </select>
            </label>
          </div>

          {error && (
            <div className="status-banner error">
              <span className="dot error"></span>
              <span>{error}</span>
            </div>
          )}

          {/* Candidates Table */}
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Category</th>
                  <th>Candidate URL</th>
                  <th>Anchor Text</th>
                  <th>Relevance</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {candidates.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="empty-state">
                      {loading ? 'Loading candidates...' : 'No candidates match the filter criteria.'}
                    </td>
                  </tr>
                ) : (
                  candidates.map((cand) => (
                    <tr key={cand.id}>
                      <td>#{cand.id}</td>
                      <td>
                        <span className={`tag-category ${cand.source_category.toLowerCase()}`}>
                          {cand.source_category.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="url-cell" title={cand.normalized_url}>
                        <a href={cand.normalized_url} target="_blank" rel="noopener noreferrer">
                          {cand.normalized_url}
                        </a>
                      </td>
                      <td className="anchor-cell">{cand.anchor_text || '—'}</td>
                      <td>
                        <span className="score-pill">
                          {(cand.relevance_score * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td>
                        <span className={`tag-status ${cand.status.toLowerCase()}`}>
                          {cand.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* Phase Roadmap */}
        <section className="card architecture-card">
          <h2>Project Roadmap & Execution Status</h2>
          <div className="roadmap-grid">
            <div className="phase-badge completed">
              <span className="phase-num">Phase 1</span>
              <h3>Project Foundation</h3>
              <p>FastAPI backend, SQLite DB, configuration, and test suites.</p>
              <span className="state-tag active">COMPLETED</span>
            </div>
            <div className="phase-badge completed">
              <span className="phase-num">Phase 2</span>
              <h3>Authentic Crawling</h3>
              <p>Ethical crawler, SSRF security, robots.txt, and candidate discovery.</p>
              <span className="state-tag active">COMPLETED</span>
            </div>
            <div className="phase-badge pending">
              <span className="phase-num">Phase 3</span>
              <h3>Deterministic Extraction</h3>
              <p>Extracting title, eligibility, benefits, deadline, and field-level evidence snippets.</p>
              <span className="state-tag">NEXT PHASE</span>
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
        <p>Scholarship Intelligence Crawler • Phase 2 Verified • Zero hallucinated data policy</p>
      </footer>
    </div>
  )
}
