"""Deterministic Verification Scoring Model.

Implements an explainable, deterministic scoring formula totaling 100 maximum points.
The engine never asks an LLM to invent confidence scores.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CriterionScore:
    """Individual criterion score breakdown."""
    criterion_name: str
    points_awarded: float
    max_points: float
    explanation: str
    deductions: List[str] = field(default_factory=list)


@dataclass
class VerificationScoreResult:
    """Aggregated score result across all criteria."""
    total_score: float
    max_total_score: float
    scoring_version: str
    criteria: Dict[str, CriterionScore]
    deductions_summary: List[str]

    @property
    def percentage(self) -> float:
        if self.max_total_score <= 0:
            return 0.0
        return round((self.total_score / self.max_total_score) * 100.0, 2)


class DeterministicScoringModel:
    """Calculates evidence-based confidence scores based on strict verifiable rules.
    
    Allocation (100 total points):
    1. Official primary source established: 25 pts
    2. Scholarship-specific identity and presence: 20 pts
    3. Critical fields supported by relevant evidence: 20 pts
    4. Application URL verified (when applicable): 10 pts
    5. Deadline supported by contextual evidence (when applicable): 10 pts
    6. Source freshness and successful recent fetch: 10 pts
    7. Extraction consistency and contradiction checks: 5 pts
    """

    MODEL_VERSION = "v1.0-deterministic"

    @classmethod
    def evaluate(
        cls,
        source_category: str,
        is_official_source: bool,
        is_aggregator: bool,
        name: Optional[str],
        provider: Optional[str],
        is_umbrella_or_listing: bool,
        field_evidence_summary: Dict[str, str],  # field_name -> quality_rating
        has_application_url: bool,
        is_app_url_official: bool,
        app_url_not_applicable: bool,
        has_closing_date: bool,
        is_deadline_contextual: bool,
        is_deadline_expired: bool,
        days_since_fetch: Optional[int],
        crawl_http_status: Optional[int],
        has_contradictions: bool,
        contradiction_details: Optional[List[str]] = None,
    ) -> VerificationScoreResult:
        criteria: Dict[str, CriterionScore] = {}
        all_deductions: List[str] = []

        # -------------------------------------------------------------
        # 1. Official primary source established (Max 25 pts)
        # -------------------------------------------------------------
        cat_upper = (source_category or "UNKNOWN").upper()
        if is_aggregator:
            pts_source = 0.0
            ded = "Source is an aggregator (discovery feed), not an authoritative primary source (-25 pts)."
            exp = "Aggregators may assist discovery but receive 0 points for primary source establishment."
            criteria["official_source"] = CriterionScore("official_source", pts_source, 25.0, exp, [ded])
            all_deductions.append(ded)
        elif is_official_source:
            if cat_upper in ("CENTRAL_GOVERNMENT", "STATE_GOVERNMENT"):
                pts_source = 25.0
                exp = f"Verified official government domain ({cat_upper}) receives full credit (25/25)."
                criteria["official_source"] = CriterionScore("official_source", pts_source, 25.0, exp)
            elif cat_upper == "UNIVERSITY":
                pts_source = 23.0
                ded = "Accredited educational institution (.ac.in/.edu.in), minor variance from apex ministry (-2 pts)."
                exp = "Accredited university official portal (23/25)."
                criteria["official_source"] = CriterionScore("official_source", pts_source, 25.0, exp, [ded])
                all_deductions.append(ded)
            elif cat_upper in ("CORPORATE_CSR", "TRUST_FOUNDATION"):
                pts_source = 20.0
                ded = "Corporate CSR / registered trust domain, requires active verification of registration (-5 pts)."
                exp = "Verified corporate CSR or registered foundation source (20/25)."
                criteria["official_source"] = CriterionScore("official_source", pts_source, 25.0, exp, [ded])
                all_deductions.append(ded)
            else:
                pts_source = 15.0
                ded = "Official source flag present but unclassified category (-10 pts)."
                exp = "Official source with general classification (15/25)."
                criteria["official_source"] = CriterionScore("official_source", pts_source, 25.0, exp, [ded])
                all_deductions.append(ded)
        else:
            pts_source = 0.0
            ded = "Source is not an established official primary domain (-25 pts)."
            exp = "Unverified or non-official domain receives 0 points for primary source."
            criteria["official_source"] = CriterionScore("official_source", pts_source, 25.0, exp, [ded])
            all_deductions.append(ded)

        # -------------------------------------------------------------
        # 2. Scholarship-specific identity and presence (Max 20 pts)
        # -------------------------------------------------------------
        pts_identity = 20.0
        identity_deds: List[str] = []
        if not name or len(name.strip()) < 5:
            pts_identity = 0.0
            ded = "Missing or empty scholarship opportunity name (-20 pts)."
            identity_deds.append(ded)
            exp_id = "No valid opportunity name found."
        elif is_umbrella_or_listing:
            pts_identity = 5.0
            ded = "Name refers to an umbrella portal or multi-scheme index rather than an individual grant (-15 pts)."
            identity_deds.append(ded)
            exp_id = f"Generic or multi-scheme title '{name}' lacks specific singular funding opportunity presence."
        else:
            exp_id = f"Specific, identifiable scholarship opportunity '{name}' present (20/20)."

        if not provider or len(provider.strip()) < 3:
            pts_identity = max(0.0, pts_identity - 5.0)
            ded = "Provider name is absent or unrecognized (-5 pts)."
            identity_deds.append(ded)

        criteria["scholarship_identity"] = CriterionScore("scholarship_identity", pts_identity, 20.0, exp_id, identity_deds)
        all_deductions.extend(identity_deds)

        # -------------------------------------------------------------
        # 3. Critical fields supported by relevant evidence (Max 20 pts)
        # -------------------------------------------------------------
        # Critical fields: name, provider, eligibility_summary / requirements, course_level / amount
        pts_fields = 0.0
        fields_deds: List[str] = []
        # Name evidence (5 pts)
        name_ev = field_evidence_summary.get("name")
        if name_ev == "SUPPORTED":
            pts_fields += 5.0
        elif name_ev == "WEAK_EVIDENCE":
            pts_fields += 2.0
            fields_deds.append("Name evidence is weak or drawn from generic container (-3 pts).")
        else:
            fields_deds.append("Name lacks verifiable source evidence (-5 pts).")

        # Provider evidence (5 pts)
        prov_ev = field_evidence_summary.get("provider")
        if prov_ev == "SUPPORTED":
            pts_fields += 5.0
        elif prov_ev == "WEAK_EVIDENCE":
            pts_fields += 2.5
            fields_deds.append("Provider evidence is weak or drawn from generic page body (-2.5 pts).")
        else:
            fields_deds.append("Provider lacks verifiable source evidence (-5 pts).")

        # Eligibility / requirements evidence (5 pts)
        elig_ev = field_evidence_summary.get("eligibility_summary") or field_evidence_summary.get("academic_requirements") or field_evidence_summary.get("category_requirements")
        if elig_ev == "SUPPORTED":
            pts_fields += 5.0
        elif elig_ev == "WEAK_EVIDENCE":
            pts_fields += 2.5
            fields_deds.append("Eligibility criteria supported only by weak evidence (-2.5 pts).")
        else:
            fields_deds.append("No verifiable eligibility criteria evidence found (-5 pts).")

        # Course level or benefit evidence (5 pts)
        benefit_ev = field_evidence_summary.get("amount_benefit") or field_evidence_summary.get("course_level")
        if benefit_ev == "SUPPORTED":
            pts_fields += 5.0
        elif benefit_ev == "WEAK_EVIDENCE":
            pts_fields += 2.5
            fields_deds.append("Benefit or course level supported only by weak evidence (-2.5 pts).")
        else:
            fields_deds.append("Neither benefit amount nor course level supported by evidence (-5 pts).")

        criteria["critical_field_evidence"] = CriterionScore(
            "critical_field_evidence",
            pts_fields,
            20.0,
            f"Evidence coverage: {pts_fields:.1f}/20 points based on field evidence relevance.",
            fields_deds,
        )
        all_deductions.extend(fields_deds)

        # -------------------------------------------------------------
        # 4. Application URL verified, when applicable (Max 10 pts)
        # -------------------------------------------------------------
        app_deds: List[str] = []
        if app_url_not_applicable:
            pts_app = 10.0
            exp_app = "Application URL is marked NOT_APPLICABLE (applications not yet open or offline submission); full neutral credit awarded."
        elif has_application_url:
            if is_app_url_official:
                pts_app = 10.0
                exp_app = "Application URL verified on official provider or national portal (10/10)."
            else:
                pts_app = 3.0
                ded = "Application URL points to third-party or untrusted domain (-7 pts)."
                app_deds.append(ded)
                exp_app = "Application link present but lacks domain alignment with official provider."
        else:
            pts_app = 0.0
            ded = "Application URL missing when required by page context (-10 pts)."
            app_deds.append(ded)
            exp_app = "No valid application portal link found."

        criteria["application_url"] = CriterionScore("application_url", pts_app, 10.0, exp_app, app_deds)
        all_deductions.extend(app_deds)

        # -------------------------------------------------------------
        # 5. Deadline supported by contextual evidence (Max 10 pts)
        # -------------------------------------------------------------
        deadline_deds: List[str] = []
        if is_deadline_expired:
            pts_deadline = 0.0
            ded = "Reported closing date has already passed as of evaluation date (-10 pts)."
            deadline_deds.append(ded)
            exp_dl = "Deadline is expired; opportunities with past deadlines receive 0 points for deadline validity."
        elif has_closing_date:
            if is_deadline_contextual:
                pts_deadline = 10.0
                exp_dl = "Active closing date directly supported by contextual deadline evidence (10/10)."
            else:
                pts_deadline = 4.0
                ded = "Closing date present but extracted from generic text without clear deadline context (-6 pts)."
                deadline_deds.append(ded)
                exp_dl = "Closing date lacks contextual deadline keywords."
        else:
            # No closing date published (e.g. rolling / open-ended)
            pts_deadline = 6.0
            ded = "No closing date published; awarded neutral base score (-4 pts)."
            deadline_deds.append(ded)
            exp_dl = "Opportunity does not publish explicit deadline (open/rolling submission)."

        criteria["deadline_evidence"] = CriterionScore("deadline_evidence", pts_deadline, 10.0, exp_dl, deadline_deds)
        all_deductions.extend(deadline_deds)

        # -------------------------------------------------------------
        # 6. Source freshness and successful recent fetch (Max 10 pts)
        # -------------------------------------------------------------
        freshness_deds: List[str] = []
        if crawl_http_status != 200:
            pts_fresh = 0.0
            ded = f"Recent fetch was not HTTP 200 (status: {crawl_http_status}) (-10 pts)."
            freshness_deds.append(ded)
            exp_fresh = "Source could not be confirmed via recent successful HTTP 200 fetch."
        elif days_since_fetch is None:
            pts_fresh = 4.0
            ded = "Fetch timestamp missing or undetermined (-6 pts)."
            freshness_deds.append(ded)
            exp_fresh = "Unknown fetch recency."
        elif days_since_fetch <= 14:
            pts_fresh = 10.0
            exp_fresh = f"Source successfully fetched {days_since_fetch} days ago (fresh, 10/10)."
        elif days_since_fetch <= 60:
            pts_fresh = 7.0
            ded = f"Source fetched {days_since_fetch} days ago; mildly aged (-3 pts)."
            freshness_deds.append(ded)
            exp_fresh = f"Source fetched {days_since_fetch} days ago (7/10)."
        elif days_since_fetch <= 120:
            pts_fresh = 4.0
            ded = f"Source fetched {days_since_fetch} days ago; approaching staleness (-6 pts)."
            freshness_deds.append(ded)
            exp_fresh = f"Aged source fetched {days_since_fetch} days ago."
        else:
            pts_fresh = 1.0
            ded = f"Source fetch is stale (>120 days old: {days_since_fetch} days) (-9 pts)."
            freshness_deds.append(ded)
            exp_fresh = f"Stale source ({days_since_fetch} days old)."

        criteria["freshness"] = CriterionScore("freshness", pts_fresh, 10.0, exp_fresh, freshness_deds)
        all_deductions.extend(freshness_deds)

        # -------------------------------------------------------------
        # 7. Extraction consistency and contradiction checks (Max 5 pts)
        # -------------------------------------------------------------
        contra_deds: List[str] = []
        if has_contradictions:
            pts_contra = 0.0
            ded = "Internal contradictions or conflicting dates/schemes detected (-5 pts)."
            contra_deds.append(ded)
            if contradiction_details:
                for c_det in contradiction_details:
                    contra_deds.append(f"Contradiction: {c_det}")
            exp_contra = "Unresolved contradictions detected."
        else:
            pts_contra = 5.0
            exp_contra = "No conflicting dates, benefits, or scheme details detected (5/5)."

        criteria["consistency"] = CriterionScore("consistency", pts_contra, 5.0, exp_contra, contra_deds)
        all_deductions.extend(contra_deds)

        # Compute total
        total = sum(c.points_awarded for c in criteria.values())
        total = round(min(100.0, max(0.0, total)), 2)

        return VerificationScoreResult(
            total_score=total,
            max_total_score=100.0,
            scoring_version=cls.MODEL_VERSION,
            criteria=criteria,
            deductions_summary=all_deductions,
        )
