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

interface FieldEvidenceItem {
  id: number
  scholarship_id: number | null
  candidate_id: number | null
  field_name: string
  extracted_value: string | null
  source_url: string
  evidence_text: string
  page_title: string | null
  retrieval_timestamp: string
  content_hash: string | null
  extraction_method: string
  html_selector: string | null
  validation_status: string
}

interface ScholarshipItem {
  id: number
  stable_id: string
  name: string | null
  provider: string | null
  official_source_url: string
  application_url: string | null
  source_category: string
  is_official_source: boolean
  amount_benefit: string | null
  closing_date: string | null
  course_level: string | null
  income_criteria: string | null
  gender_criteria: string | null
  category_requirements: string | null
  lifecycle_status: string
  page_type: string
  extraction_timestamp: string
  evidence_count: number
}

interface ScholarshipDetailResponse {
  scholarship: ScholarshipItem
  evidence_records: FieldEvidenceItem[]
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'scholarships' | 'candidates'>('scholarships')
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [scholarships, setScholarships] = useState<ScholarshipItem[]>([])
  const [totalScholarships, setTotalScholarships] = useState<number>(0)
  const [candidates, setCandidates] = useState<CandidateItem[]>([])
  const [totalCandidates, setTotalCandidates] = useState<number>(0)
  const [loading, setLoading] = useState<boolean>(false)
  const [extracting, setExtracting] = useState<boolean>(false)
  const [selectedScholarship, setSelectedScholarship] = useState<ScholarshipDetailResponse | null>(null)
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')

  const fetchHealth = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/health')
      if (res.ok) setHealth(await res.json())
    } catch {
      setHealth(null)
    }
  }

  const fetchScholarships = async () => {
    setLoading(true)
    try {
      let url = 'http://127.0.0.1:8000/api/scholarships?page=1&page_size=20'
      if (categoryFilter) url += `&category=${encodeURIComponent(categoryFilter)}`
      if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        setScholarships(data.items)
        setTotalScholarships(data.total)
      }
    } catch {
      // Backend offline or error
    } finally {
      setLoading(false)
    }
  }

  const fetchCandidates = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/discovery/candidates?page=1&page_size=20')
      if (res.ok) {
        const data = await res.json()
        setCandidates(data.items)
        setTotalCandidates(data.total)
      }
    } catch {
      // Backend offline or error
    }
  }

  const inspectEvidence = async (id: number) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/scholarships/${id}`)
      if (res.ok) {
        const data: ScholarshipDetailResponse = await res.json()
        setSelectedScholarship(data)
      }
    } catch {
      // Error fetching details
    }
  }

  const triggerExtraction = async () => {
    setExtracting(true)
    try {
      const res = await fetch('http://127.0.0.1:8000/api/extraction/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ max_candidates: 10 }),
      })
      if (res.ok) {
        await fetchScholarships()
        await fetchCandidates()
      }
    } finally {
      setExtracting(false)
    }
  }

  useEffect(() => {
    fetchHealth()
    fetchScholarships()
    fetchCandidates()
  }, [categoryFilter, searchQuery])

  return (
    <div className="container">
      <header className="header">
        <div className="badge">EDXSO Assignment 2 • Phase 3 Extraction & Evidence</div>
        <h1>Scholarship Intelligence Crawler</h1>
        <p className="subtitle">
          Deterministic extraction of scholarship records with field-level verbatim evidence traceability.
        </p>
      </header>

      {/* Metrics Bar */}
      <section className="metrics-bar">
        <div className="metric-box">
          <span className="metric-num">{totalScholarships}</span>
          <span className="metric-label">Extracted Scholarships</span>
        </div>
        <div className="metric-box">
          <span className="metric-num">{totalCandidates}</span>
          <span className="metric-label">Crawled Candidates</span>
        </div>
        <div className="metric-box">
          <span className="metric-num">
            {scholarships.reduce((acc, s) => acc + s.evidence_count, 0)}
          </span>
          <span className="metric-label">Field Evidence Traces</span>
        </div>
        <div className="metric-box">
          <span className="metric-num">
            {health?.status === 'ok' ? 'Online' : 'Offline'}
          </span>
          <span className="metric-label">FastAPI Backend</span>
        </div>
      </section>

      {/* Navigation Tabs */}
      <div className="tab-navigation">
        <button
          className={`tab-btn ${activeTab === 'scholarships' ? 'active' : ''}`}
          onClick={() => setActiveTab('scholarships')}
        >
          Extracted Scholarships ({totalScholarships})
        </button>
        <button
          className={`tab-btn ${activeTab === 'candidates' ? 'active' : ''}`}
          onClick={() => setActiveTab('candidates')}
        >
          Discovered Candidates ({totalCandidates})
        </button>
      </div>

      <main className="main-content">
        {activeTab === 'scholarships' && (
          <section className="card">
            <div className="card-header">
              <div>
                <h2>Structured Scholarship Records</h2>
                <p className="section-desc">
                  Extracted without hallucinations. Blank fields remain unspecified with zero invented values.
                </p>
              </div>
              <div className="actions-group">
                <button
                  type="button"
                  className="refresh-btn secondary"
                  onClick={fetchScholarships}
                  disabled={loading}
                >
                  {loading ? 'Refreshing...' : 'Refresh Records'}
                </button>
                <button
                  type="button"
                  className="refresh-btn primary"
                  onClick={triggerExtraction}
                  disabled={extracting}
                >
                  {extracting ? 'Extracting Fields...' : 'Run Extraction Session'}
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
                </select>
              </label>
              <input
                type="text"
                placeholder="Search by scholarship or provider..."
                className="search-input"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            {/* Scholarships Table */}
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Scholarship Name</th>
                    <th>Provider</th>
                    <th>Category</th>
                    <th>Benefit / Amount</th>
                    <th>Closing Date</th>
                    <th>Evidence</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {scholarships.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="empty-state">
                        {loading
                          ? 'Loading scholarships...'
                          : 'No structured scholarships extracted yet. Click "Run Extraction Session" to process candidates.'}
                      </td>
                    </tr>
                  ) : (
                    scholarships.map((s) => (
                      <tr key={s.id}>
                        <td>#{s.id}</td>
                        <td className="name-cell">
                          <strong>{s.name || 'Not specified'}</strong>
                          <div className="sub-url">
                            <a href={s.official_source_url} target="_blank" rel="noopener noreferrer">
                              {s.official_source_url}
                            </a>
                          </div>
                        </td>
                        <td>{s.provider || <span className="unspecified">Not specified</span>}</td>
                        <td>
                          <span className={`tag-category ${s.source_category.toLowerCase()}`}>
                            {s.source_category.replace('_', ' ')}
                          </span>
                        </td>
                        <td>
                          {s.amount_benefit ? (
                            <span className="benefit-badge">{s.amount_benefit}</span>
                          ) : (
                            <span className="unspecified">Not specified</span>
                          )}
                        </td>
                        <td>
                          {s.closing_date ? (
                            <span className="date-badge">{s.closing_date}</span>
                          ) : (
                            <span className="unspecified">Not specified</span>
                          )}
                        </td>
                        <td>
                          <span className="score-pill">{s.evidence_count} Fields</span>
                        </td>
                        <td>
                          <button
                            type="button"
                            className="inspect-btn"
                            onClick={() => inspectEvidence(s.id)}
                          >
                            Trace Evidence
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {activeTab === 'candidates' && (
          <section className="card">
            <div className="card-header">
              <div>
                <h2>Discovered Candidate URLs</h2>
                <p className="section-desc">Entrypoint candidates queued for crawling and extraction.</p>
              </div>
            </div>
            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Category</th>
                    <th>Candidate URL</th>
                    <th>Anchor Text</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {candidates.map((cand) => (
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
                        <span className={`tag-status ${cand.status.toLowerCase()}`}>
                          {cand.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Evidence Modal / Detail Drawer */}
        {selectedScholarship && (
          <div className="modal-backdrop" onClick={() => setSelectedScholarship(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <div>
                  <span className="modal-badge">
                    {selectedScholarship.scholarship.source_category.replace('_', ' ')} • STABLE ID: {selectedScholarship.scholarship.stable_id}
                  </span>
                  <h2>{selectedScholarship.scholarship.name}</h2>
                </div>
                <button
                  type="button"
                  className="close-btn"
                  onClick={() => setSelectedScholarship(null)}
                >
                  ✕
                </button>
              </div>

              <div className="modal-body">
                <div className="meta-grid">
                  <div className="meta-item">
                    <span className="meta-label">Provider</span>
                    <span className="meta-val">{selectedScholarship.scholarship.provider || 'Not specified'}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Financial Benefit</span>
                    <span className="meta-val">{selectedScholarship.scholarship.amount_benefit || 'Not specified'}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Closing Deadline</span>
                    <span className="meta-val">{selectedScholarship.scholarship.closing_date || 'Not specified'}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Course / Level</span>
                    <span className="meta-val">{selectedScholarship.scholarship.course_level || 'Not specified'}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Income Limit</span>
                    <span className="meta-val">{selectedScholarship.scholarship.income_criteria || 'Not specified'}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Eligible Categories</span>
                    <span className="meta-val">{selectedScholarship.scholarship.category_requirements || 'Not specified'}</span>
                  </div>
                </div>

                <div className="official-link-box">
                  <strong>Official Source URL:</strong>{' '}
                  <a href={selectedScholarship.scholarship.official_source_url} target="_blank" rel="noopener noreferrer">
                    {selectedScholarship.scholarship.official_source_url}
                  </a>
                </div>

                <h3>Traceable Field-Level Evidence ({selectedScholarship.evidence_records.length} Records)</h3>
                <p className="evidence-hint">
                  Verbatim snippets captured directly from the official portal with selector and content hash audit trails.
                </p>

                <div className="evidence-list">
                  {selectedScholarship.evidence_records.map((ev) => (
                    <div key={ev.id} className="evidence-card">
                      <div className="evidence-header">
                        <span className="field-tag">{ev.field_name}</span>
                        <span className="method-tag">{ev.extraction_method}</span>
                        <span className="status-tag valid">{ev.validation_status}</span>
                      </div>
                      <div className="evidence-value">
                        <strong>Extracted Value:</strong> {ev.extracted_value || 'None'}
                      </div>
                      <blockquote className="evidence-snippet">
                        "{ev.evidence_text}"
                      </blockquote>
                      <div className="evidence-footer">
                        <span>DOM Selector: <code>{ev.html_selector || 'body'}</code></span>
                        <span>Hash: <code>{ev.content_hash ? ev.content_hash.slice(0, 16) + '...' : 'N/A'}</code></span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

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
            <div className="phase-badge completed">
              <span className="phase-num">Phase 3</span>
              <h3>Deterministic Extraction</h3>
              <p>Deterministic field extraction with traceable verbatim evidence.</p>
              <span className="state-tag active">COMPLETED</span>
            </div>
            <div className="phase-badge pending">
              <span className="phase-num">Phase 4</span>
              <h3>Verification & Scoring</h3>
              <p>Explainable confidence scoring; strictly ≥95% required for VERIFIED status.</p>
              <span className="state-tag">NEXT PHASE</span>
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
        <p>Scholarship Intelligence Crawler • Phase 3 Extraction & Evidence Verified • Zero hallucinated data policy</p>
      </footer>
    </div>
  )
}
