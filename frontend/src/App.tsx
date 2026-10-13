import { useState, useEffect } from 'react'
import './App.css'

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
  quality_rating?: string
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
  verification_status?: string
  confidence_score?: number | null
}

interface ScholarshipDetailResponse {
  scholarship: ScholarshipItem
  evidence_records: FieldEvidenceItem[]
}

interface VerificationSummary {
  total_scholarships: number
  verified_count: number
  review_required_count: number
  unverified_count: number
  expired_count: number
  active_count: number
  average_confidence: number
  last_verification_run: string | null
}

interface CriterionScoreItem {
  criterion_name: string
  points_awarded: number
  max_points: number
  explanation: string
  deductions: string[]
}

interface GateResultItem {
  gate_name: string
  status: 'PASS' | 'FAIL' | 'NOT_APPLICABLE'
  explanation: string
  evidence_refs: any[]
  evaluated_at: string
}

interface ScholarshipVerificationDetail {
  scholarship_id: number
  confidence_score: number
  verification_status: string
  lifecycle_status: string
  scoring_model_version: string
  criteria_breakdown: Record<string, CriterionScoreItem>
  gate_results: Record<string, GateResultItem>
  deductions: string[]
  evidence_references: Array<{
    evidence_id: number
    field_name: string
    extracted_value: string | null
    quality_rating: string
    explanation: string
    source_url: string
    snippet: string
  }>
  verified_at: string
}

interface ChangeHistoryItem {
  id: number
  scholarship_id: number
  field_name: string
  previous_value: string | null
  new_value: string | null
  detection_timestamp: string
  previous_evidence_id: number | null
  new_evidence_id: number | null
  source_url: string
  crawl_run_id: number | null
  change_classification: string
  requires_reverification: boolean
  is_reviewed: boolean
}

interface SchedulerStatus {
  is_active: boolean
  is_running_job: boolean
  interval_seconds: number
  last_run_time: string | null
  last_run_status: string | null
  last_run_summary: any
  next_run_time: string | null
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'scholarships' | 'candidates' | 'changes'>('scholarships')
  const [scholarships, setScholarships] = useState<ScholarshipItem[]>([])
  const [totalScholarships, setTotalScholarships] = useState<number>(0)
  const [candidates, setCandidates] = useState<CandidateItem[]>([])
  const [totalCandidates, setTotalCandidates] = useState<number>(0)
  const [changes, setChanges] = useState<ChangeHistoryItem[]>([])
  const [totalChanges, setTotalChanges] = useState<number>(0)
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null)
  
  const [loading, setLoading] = useState<boolean>(false)
  const [extracting, setExtracting] = useState<boolean>(false)
  const [verifying, setVerifying] = useState<boolean>(false)
  const [runningCrawl, setRunningCrawl] = useState<boolean>(false)

  const [verificationSummary, setVerificationSummary] = useState<VerificationSummary | null>(null)
  const [selectedScholarship, setSelectedScholarship] = useState<ScholarshipDetailResponse | null>(null)
  const [selectedVerification, setSelectedVerification] = useState<ScholarshipVerificationDetail | null>(null)
  const [selectedScholarshipChanges, setSelectedScholarshipChanges] = useState<{ id: number; name: string; items: ChangeHistoryItem[] } | null>(null)
  
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')

  const fetchSchedulerStatus = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/scheduler/status')
      if (res.ok) setSchedulerStatus(await res.json())
    } catch {
      setSchedulerStatus(null)
    }
  }

  const fetchVerificationSummary = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/verification/summary')
      if (res.ok) setVerificationSummary(await res.json())
    } catch {
      setVerificationSummary(null)
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
    } catch (err) {
      console.error('Error fetching scholarships:', err)
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
    } catch (err) {
      console.error('Error fetching candidates:', err)
    }
  }

  const fetchRecentChanges = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/changes/recent?page=1&page_size=50')
      if (res.ok) {
        const data = await res.json()
        setChanges(data.items)
        setTotalChanges(data.total)
      }
    } catch (err) {
      console.error('Error fetching change history:', err)
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
        await fetchVerificationSummary()
      }
    } catch (err) {
      console.error('Error running extraction session:', err)
    } finally {
      setExtracting(false)
    }
  }

  const triggerVerification = async () => {
    setVerifying(true)
    try {
      const res = await fetch('http://127.0.0.1:8000/api/verification/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      })
      if (res.ok) {
        await fetchScholarships()
        await fetchVerificationSummary()
      }
    } catch (err) {
      console.error('Error running verification session:', err)
    } finally {
      setVerifying(false)
    }
  }

  const triggerUpdateCycle = async () => {
    setRunningCrawl(true)
    try {
      const res = await fetch('http://127.0.0.1:8000/api/crawl/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ max_pages: 5 }),
      })
      if (res.ok) {
        await fetchScholarships()
        await fetchVerificationSummary()
        await fetchRecentChanges()
        await fetchSchedulerStatus()
      }
    } catch (err) {
      console.error('Error running crawl update cycle:', err)
    } finally {
      setRunningCrawl(false)
    }
  }

  const handleStartScheduler = async () => {
    try {
      await fetch('http://127.0.0.1:8000/api/scheduler/start', { method: 'POST' })
      await fetchSchedulerStatus()
    } catch (err) {
      console.error('Error starting scheduler:', err)
    }
  }

  const handleStopScheduler = async () => {
    try {
      await fetch('http://127.0.0.1:8000/api/scheduler/stop', { method: 'POST' })
      await fetchSchedulerStatus()
    } catch (err) {
      console.error('Error stopping scheduler:', err)
    }
  }

  const handleInspectEvidence = async (id: number) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/scholarships/${id}`)
      if (res.ok) {
        const data = await res.json()
        setSelectedScholarship(data)
      }
    } catch (err) {
      console.error('Error loading scholarship detail:', err)
    }
  }

  const handleInspectVerification = async (id: number) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/scholarships/${id}/verification`)
      if (res.ok) {
        const data = await res.json()
        setSelectedVerification(data)
      }
    } catch (err) {
      console.error('Error loading verification detail:', err)
    }
  }

  const handleInspectScholarshipChanges = async (s: ScholarshipItem) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/scholarships/${s.id}/changes`)
      if (res.ok) {
        const data = await res.json()
        setSelectedScholarshipChanges({ id: s.id, name: s.name || 'Scholarship', items: data })
      }
    } catch (err) {
      console.error('Error loading scholarship change history:', err)
    }
  }

  useEffect(() => {
    fetchScholarships()
    fetchCandidates()
    fetchVerificationSummary()
    fetchRecentChanges()
    fetchSchedulerStatus()
  }, [categoryFilter, searchQuery])

  return (
    <div className="container">
      <header className="header">
        <div className="badge">EDXSO Assignment 2 • Phase 5 Recrawling, Change Detection & Lifecycle</div>
        <h1>Scholarship Intelligence Crawler</h1>
        <p className="subtitle">
          Automated ethical recrawling, deterministic field-level change detection, preserved historical observations,
          and lifecycle transition management.
        </p>
      </header>

      {/* Scheduler Control & Status Banner */}
      <section className="scheduler-banner">
        <div className="scheduler-info">
          <div className="scheduler-status-row">
            <span className="scheduler-label">Recurring Crawl Scheduler:</span>
            <span className={`scheduler-pill ${schedulerStatus?.is_running_job ? 'running' : schedulerStatus?.is_active ? 'active' : 'stopped'}`}>
              {schedulerStatus?.is_running_job ? '⚡ CRAWL JOB IN PROGRESS' : schedulerStatus?.is_active ? '● ACTIVE (DAEMON RUNNING)' : '○ STOPPED'}
            </span>
            <span className="scheduler-interval">
              Interval: {schedulerStatus?.interval_seconds ? `${schedulerStatus.interval_seconds / 60}m` : '60m'}
            </span>
          </div>
          <div className="scheduler-meta">
            <span>Next Run: {schedulerStatus?.next_run_time ? new Date(schedulerStatus.next_run_time).toLocaleTimeString() : 'Not scheduled'}</span>
            <span>Last Run: {schedulerStatus?.last_run_time ? new Date(schedulerStatus.last_run_time).toLocaleTimeString() : 'Never'} ({schedulerStatus?.last_run_status || 'None'})</span>
          </div>
        </div>
        <div className="scheduler-actions">
          {schedulerStatus?.is_active ? (
            <button type="button" className="btn-scheduler stop" onClick={handleStopScheduler}>
              Stop Scheduler
            </button>
          ) : (
            <button type="button" className="btn-scheduler start" onClick={handleStartScheduler}>
              Start Scheduler
            </button>
          )}
          <button
            type="button"
            className="btn-scheduler run"
            onClick={triggerUpdateCycle}
            disabled={runningCrawl || schedulerStatus?.is_running_job}
          >
            {runningCrawl ? 'Running Cycle...' : 'Run Update Cycle Now'}
          </button>
        </div>
      </section>

      {/* Metrics Bar with Real Verification Data */}
      <section className="metrics-bar">
        <div className="metric-box">
          <span className="metric-num">{totalScholarships}</span>
          <span className="metric-label">Extracted Records</span>
        </div>
        <div className="metric-box verified">
          <span className="metric-num text-success">{verificationSummary?.verified_count ?? 0}</span>
          <span className="metric-label">Verified (≥95% + Gates)</span>
        </div>
        <div className="metric-box review">
          <span className="metric-num text-warning">{verificationSummary?.review_required_count ?? 0}</span>
          <span className="metric-label">Review Required</span>
        </div>
        <div className="metric-box expired">
          <span className="metric-num text-danger">{verificationSummary?.expired_count ?? 0}</span>
          <span className="metric-label">Expired Deadlines</span>
        </div>
        <div className="metric-box changes">
          <span className="metric-num text-accent">{totalChanges}</span>
          <span className="metric-label">Detected Changes</span>
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
          className={`tab-btn ${activeTab === 'changes' ? 'active' : ''}`}
          onClick={() => { setActiveTab('changes'); fetchRecentChanges(); }}
        >
          Field Change History ({totalChanges})
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
                <h2>Structured Scholarship Records & Lifecycle</h2>
                <p className="section-desc">
                  Authenticity verified against 7 mandatory gates. Records marked VERIFIED only when score ≥ 95% and all gates pass.
                </p>
              </div>
              <div className="actions-group">
                <button
                  type="button"
                  className="refresh-btn secondary"
                  onClick={fetchScholarships}
                  disabled={loading}
                >
                  {loading ? 'Refreshing...' : 'Refresh'}
                </button>
                <button
                  type="button"
                  className="refresh-btn primary"
                  onClick={triggerVerification}
                  disabled={verifying}
                >
                  {verifying ? 'Evaluating Gates...' : 'Run Verification Engine'}
                </button>
                <button
                  type="button"
                  className="refresh-btn secondary"
                  onClick={triggerExtraction}
                  disabled={extracting}
                >
                  {extracting ? 'Extracting...' : 'Extract More Candidates'}
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

              <div className="search-box">
                <input
                  type="text"
                  placeholder="Search scholarship name or provider..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                {searchQuery && (
                  <button type="button" className="clear-btn" onClick={() => setSearchQuery('')}>
                    ✕
                  </button>
                )}
              </div>
            </div>

            {/* Scholarships Table */}
            <div className="table-responsive">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Opportunity & Provider</th>
                    <th>Category</th>
                    <th>Lifecycle</th>
                    <th>Confidence Score</th>
                    <th>Verification Status</th>
                    <th>Closing Date</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {scholarships.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center empty-cell">
                        {loading ? 'Loading records...' : 'No scholarships found. Run extraction or crawler to discover opportunities.'}
                      </td>
                    </tr>
                  ) : (
                    scholarships.map((s) => {
                      const isExpired = s.lifecycle_status === 'EXPIRED'
                      const isVerified = s.verification_status === 'VERIFIED'
                      const scoreVal = s.confidence_score ?? null

                      return (
                        <tr key={s.id} className={isExpired ? 'row-expired' : ''}>
                          <td className="opportunity-cell">
                            <strong className="title-text">{s.name || 'Untitled Opportunity'}</strong>
                            <div className="provider-subtext">{s.provider || 'Provider not explicitly specified'}</div>
                            <div className="source-domain">
                              <a href={s.official_source_url} target="_blank" rel="noopener noreferrer">
                                {new URL(s.official_source_url).hostname} ↗
                              </a>
                            </div>
                          </td>
                          <td>
                            <span className={`tag-category ${s.source_category.toLowerCase()}`}>
                              {s.source_category.replace('_', ' ')}
                            </span>
                          </td>
                          <td>
                            <span className={`lifecycle-tag ${s.lifecycle_status.toLowerCase()}`}>
                              {isExpired ? '⚠️ EXPIRED' : s.lifecycle_status}
                            </span>
                          </td>
                          <td>
                            <div className="score-pill-container">
                              <span className={`score-badge ${scoreVal !== null && scoreVal >= 95 ? 'high' : scoreVal !== null && scoreVal >= 70 ? 'medium' : 'low'}`}>
                                {scoreVal !== null ? `${scoreVal.toFixed(1)}%` : 'Not Scored'}
                              </span>
                            </div>
                          </td>
                          <td>
                            <span className={`verification-badge ${(s.verification_status || 'unverified').toLowerCase()}`}>
                              {isVerified ? '✓ VERIFIED' : s.verification_status === 'REVIEW_REQUIRED' ? '⚠️ REVIEW REQUIRED' : 'UNVERIFIED'}
                            </span>
                          </td>
                          <td>
                            <span className={isExpired ? 'text-danger font-medium' : ''}>
                              {s.closing_date || 'Ongoing / Rolling'}
                            </span>
                          </td>
                          <td className="actions-cell">
                            <button
                              type="button"
                              className="btn-action primary"
                              onClick={() => handleInspectVerification(s.id)}
                            >
                              Audit Breakdown
                            </button>
                            <button
                              type="button"
                              className="btn-action secondary"
                              onClick={() => handleInspectScholarshipChanges(s)}
                            >
                              Change History
                            </button>
                            <button
                              type="button"
                              className="btn-action secondary"
                              onClick={() => handleInspectEvidence(s.id)}
                            >
                              Evidence ({s.evidence_count})
                            </button>
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {activeTab === 'changes' && (
          <section className="card">
            <div className="card-header">
              <div>
                <h2>Field-Level Change Audit History ({totalChanges})</h2>
                <p className="section-desc">
                  Immutable audit records tracking old vs new values, detection timestamps, evidence links, and re-verification triggers.
                </p>
              </div>
              <button
                type="button"
                className="refresh-btn secondary"
                onClick={fetchRecentChanges}
              >
                Refresh Changes
              </button>
            </div>

            <div className="table-responsive">
              <table className="custom-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Scholarship ID</th>
                    <th>Field Name</th>
                    <th>Change Classification</th>
                    <th>Previous Value</th>
                    <th>New Observed Value</th>
                    <th>Re-Verification</th>
                  </tr>
                </thead>
                <tbody>
                  {changes.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center empty-cell">
                        No changes detected yet. Unchanged pages do not produce duplicate change entries.
                      </td>
                    </tr>
                  ) : (
                    changes.map((ch) => (
                      <tr key={ch.id}>
                        <td className="timestamp-cell">
                          {new Date(ch.detection_timestamp).toLocaleString()}
                        </td>
                        <td>#{ch.scholarship_id}</td>
                        <td><strong>{ch.field_name}</strong></td>
                        <td>
                          <span className={`change-classification-tag ${ch.change_classification.toLowerCase()}`}>
                            {ch.change_classification.replace(/_/g, ' ')}
                          </span>
                        </td>
                        <td className="diff-old">{ch.previous_value || '— (None)'}</td>
                        <td className="diff-new">{ch.new_value || '— (None)'}</td>
                        <td>
                          {ch.requires_reverification ? (
                            <span className="reverify-tag required">Required</span>
                          ) : (
                            <span className="reverify-tag not-required">No</span>
                          )}
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
                <h2>Discovered Candidate Pages ({totalCandidates})</h2>
                <p className="section-desc">
                  URLs discovered via seed crawling with ethical throttles, robots.txt compliance, and anti-SSRF filters.
                </p>
              </div>
            </div>

            <div className="table-responsive">
              <table className="custom-table">
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

        {/* Scholarship-Specific Change History Modal */}
        {selectedScholarshipChanges && (
          <div className="modal-backdrop" onClick={() => setSelectedScholarshipChanges(null)}>
            <div className="modal-content modal-changes" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <div>
                  <span className="modal-badge">
                    AUDIT TRAIL • SCHOLARSHIP #{selectedScholarshipChanges.id}
                  </span>
                  <h2>Change History: {selectedScholarshipChanges.name}</h2>
                </div>
                <button
                  type="button"
                  className="close-btn"
                  onClick={() => setSelectedScholarshipChanges(null)}
                >
                  ✕
                </button>
              </div>

              <div className="modal-body">
                {selectedScholarshipChanges.items.length === 0 ? (
                  <p className="empty-text">No recorded field changes for this scholarship yet. Current observations remain unchanged.</p>
                ) : (
                  <div className="changes-timeline">
                    {selectedScholarshipChanges.items.map((item) => (
                      <div key={item.id} className="change-timeline-card">
                        <div className="timeline-header">
                          <span className={`change-classification-tag ${item.change_classification.toLowerCase()}`}>
                            {item.change_classification.replace(/_/g, ' ')}
                          </span>
                          <span className="timeline-date">{new Date(item.detection_timestamp).toLocaleString()}</span>
                        </div>
                        <div className="timeline-field">
                          Field: <strong>{item.field_name}</strong>
                        </div>
                        <div className="timeline-diff">
                          <div className="diff-box old">
                            <span className="diff-label">Previous Value:</span>
                            <span className="diff-text">{item.previous_value || 'None'}</span>
                          </div>
                          <div className="diff-arrow">➔</div>
                          <div className="diff-box new">
                            <span className="diff-label">New Value:</span>
                            <span className="diff-text">{item.new_value || 'None'}</span>
                          </div>
                        </div>
                        {item.requires_reverification && (
                          <div className="timeline-footer">
                            <span className="reverify-tag required">Triggered Deterministic Re-Verification</span>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Verification Audit Modal */}
        {selectedVerification && (
          <div className="modal-backdrop" onClick={() => setSelectedVerification(null)}>
            <div className="modal-content modal-verification" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <div>
                  <span className="modal-badge">
                    CONFIDENCE ENGINE • MODEL: {selectedVerification.scoring_model_version}
                  </span>
                  <h2>Deterministic Verification Audit • #{selectedVerification.scholarship_id}</h2>
                </div>
                <button
                  type="button"
                  className="close-btn"
                  onClick={() => setSelectedVerification(null)}
                >
                  ✕
                </button>
              </div>

              <div className="modal-body">
                {/* Score & Status Highlight */}
                <div className="verification-hero">
                  <div className="hero-score-box">
                    <span className="hero-score-label">Computed Confidence</span>
                    <span className={`hero-score-val ${selectedVerification.confidence_score >= 95 ? 'text-success' : 'text-warning'}`}>
                      {selectedVerification.confidence_score.toFixed(1)}%
                    </span>
                    <span className="hero-score-subtext">Evidence-based deterministic score</span>
                  </div>
                  <div className="hero-status-box">
                    <span className="hero-score-label">Verification Outcome</span>
                    <span className={`hero-status-badge ${selectedVerification.verification_status.toLowerCase()}`}>
                      {selectedVerification.verification_status === 'VERIFIED' ? '✓ VERIFIED' : '⚠️ REVIEW REQUIRED'}
                    </span>
                    <span className="hero-score-subtext">
                      Lifecycle: <strong>{selectedVerification.lifecycle_status}</strong>
                    </span>
                  </div>
                </div>

                {/* Warning if Review Required */}
                {selectedVerification.verification_status !== 'VERIFIED' && (
                  <div className="verification-alert-box">
                    <h4>⚠️ Why This Opportunity Failed Verification</h4>
                    <p>
                      A record can only be marked VERIFIED when its score is at least 95.0% AND all mandatory verification gates pass.
                    </p>
                    {selectedVerification.deductions.length > 0 && (
                      <ul className="deductions-list">
                        {selectedVerification.deductions.map((d, idx) => (
                          <li key={idx}>{d}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                {/* Mandatory Verification Gates */}
                <h3>Mandatory Verification Gates (All 7 Must Pass for Verified Status)</h3>
                <div className="gates-grid">
                  {Object.entries(selectedVerification.gate_results).map(([gName, gVal]) => {
                    const isPass = gVal.status === 'PASS'
                    const isNA = gVal.status === 'NOT_APPLICABLE'
                    return (
                      <div key={gName} className={`gate-card ${gVal.status.toLowerCase()}`}>
                        <div className="gate-header">
                          <span className="gate-title">{gName.replace(/_/g, ' ')}</span>
                          <span className={`gate-status-pill ${gVal.status.toLowerCase()}`}>
                            {isPass ? '✓ PASS' : isNA ? '⚪ NOT APPLICABLE' : '✕ FAIL'}
                          </span>
                        </div>
                        <p className="gate-explanation">{gVal.explanation}</p>
                      </div>
                    )
                  })}
                </div>

                {/* 100-Point Criteria Breakdown */}
                <h3>100-Point Deterministic Formula Allocation</h3>
                <div className="table-responsive">
                  <table className="breakdown-table">
                    <thead>
                      <tr>
                        <th>Criterion</th>
                        <th>Points Awarded</th>
                        <th>Max Points</th>
                        <th>Deterministic Explanation</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(selectedVerification.criteria_breakdown).map(([cKey, cVal]) => (
                        <tr key={cKey}>
                          <td><strong>{cKey.replace(/_/g, ' ')}</strong></td>
                          <td>
                            <span className={`pts-tag ${cVal.points_awarded === cVal.max_points ? 'full' : cVal.points_awarded > 0 ? 'partial' : 'zero'}`}>
                              {cVal.points_awarded.toFixed(1)}
                            </span>
                          </td>
                          <td>{cVal.max_points.toFixed(1)}</td>
                          <td className="explanation-cell">
                            <div>{cVal.explanation}</div>
                            {cVal.deductions && cVal.deductions.length > 0 && (
                              <div className="criterion-deductions">
                                {cVal.deductions.map((cd, i) => (
                                  <span key={i} className="deduction-chip">• {cd}</span>
                                ))}
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Evidence References Used */}
                <h3>Field Evidence Quality Ratings ({selectedVerification.evidence_references.length} Items)</h3>
                <div className="evidence-list">
                  {selectedVerification.evidence_references.map((ev, i) => (
                    <div key={i} className="evidence-card">
                      <div className="evidence-header">
                        <span className="field-tag">{ev.field_name}</span>
                        <span className={`quality-badge ${ev.quality_rating.toLowerCase()}`}>
                          {ev.quality_rating}
                        </span>
                      </div>
                      <div className="evidence-value">
                        <strong>Value:</strong> {ev.extracted_value || 'None'}
                      </div>
                      <blockquote className="evidence-snippet">
                        "{ev.snippet}"
                      </blockquote>
                      <div className="evidence-footer">
                        <span>Relevance Audit: {ev.explanation}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Raw Evidence Modal */}
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
            <div className="phase-badge completed">
              <span className="phase-num">Phase 4</span>
              <h3>Verification & Scoring</h3>
              <p>Deterministic confidence scoring engine; strictly ≥95% required for VERIFIED status.</p>
              <span className="state-tag active">COMPLETED</span>
            </div>
            <div className="phase-badge completed">
              <span className="phase-num">Phase 5</span>
              <h3>Change Detection & Lifecycle</h3>
              <p>Repeatable scheduler, field diff tracking, lifecycle transitions, and audit trail.</p>
              <span className="state-tag active">COMPLETED</span>
            </div>
          </div>
        </section>
      </main>

      <footer className="footer">
        <p>Scholarship Intelligence Crawler • Phase 5 Automatic Recrawling, Change Detection & Lifecycle • Complete Audit Trail</p>
      </footer>
    </div>
  )
}
