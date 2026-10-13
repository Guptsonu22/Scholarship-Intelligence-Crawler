from urllib.parse import urlparse
from typing import Tuple

# Known trusted corporate CSR domains
KNOWN_CORPORATE_CSR_DOMAINS = {
    "reliancefoundation.org",
    "tatatrusts.org",
    "ongcfoundation.org",
    "infosys.org",
    "hdfcbank.com",
    "tatamotors.com",
    "adityabirla.com",
    "adityabirlascholars.net",
    "drreddys.com",
    "persistentfoundation.org",
    "kotakeducation.org",
}

# Known philanthropic trusts and educational foundations
KNOWN_TRUST_DOMAINS = {
    "kcmet.org",
    "nsfoundation.co.in",
    "snst.org.in",
    "sitaramjindalfoundation.org",
    "inlaksfoundation.org",
    "azimpremjifoundation.org",
    "azimpremjiuniversity.edu.in",
    "loreal.com",
}

# Known scholarship aggregators (discovery feeds, not primary sources)
KNOWN_AGGREGATOR_DOMAINS = {
    "buddy4study.com",
    "scholarshipsinindia.com",
    "indiascholarships.com",
    "vidyasaarathi.co.in",
    "desischools.com",
}

# State identifier indicators in gov domains
STATE_GOV_IDENTIFIERS = [
    "karnataka.gov.in",
    "maharashtra.gov.in",
    "up.gov.in",
    "bihar.gov.in",
    "odisha.gov.in",
    "wb.gov.in",
    "oasis.gov.in",
    "tn.gov.in",
    "kerala.gov.in",
    "rajasthan.gov.in",
    "mp.gov.in",
    "punjab.gov.in",
    "haryana.gov.in",
    "highereduhry.ac.in",
    "gujarat.gov.in",
    "assam.gov.in",
    "telangana.gov.in",
    "ap.gov.in",
    "jharkhand.gov.in",
]


class SourceClassificationResult:
    """Classification details for a domain or source URL."""

    def __init__(
        self,
        domain: str,
        category: str,
        is_official: bool,
        trust_score: float,
        reason: str,
    ):
        self.domain = domain
        self.category = category
        self.is_official = is_official
        self.trust_score = trust_score
        self.reason = reason


class SourceClassifier:
    """Classifies source URLs and domains into authentic categories using deterministic rules."""

    @staticmethod
    def classify(url_or_domain: str) -> SourceClassificationResult:
        """Determines category, authenticity, and explainable reason for a URL or domain."""
        if "://" in url_or_domain:
            domain = urlparse(url_or_domain).netloc.lower()
        else:
            domain = url_or_domain.lower()

        # Strip standard port numbers or subdomains if necessary
        clean_domain = domain.split(":")[0].strip()
        # Remove www.
        if clean_domain.startswith("www."):
            clean_domain = clean_domain[4:]

        # 1. State Government identification
        for state_suffix in STATE_GOV_IDENTIFIERS:
            if clean_domain.endswith(state_suffix):
                return SourceClassificationResult(
                    domain=clean_domain,
                    category="STATE_GOVERNMENT",
                    is_official=True,
                    trust_score=0.98,
                    reason=f"Verified Indian state government official domain ending in '{state_suffix}'.",
                )

        # 2. Central Government identification
        if clean_domain.endswith(".gov.in") or clean_domain.endswith(".nic.in"):
            return SourceClassificationResult(
                domain=clean_domain,
                category="CENTRAL_GOVERNMENT",
                is_official=True,
                trust_score=0.99,
                reason="Verified Government of India official apex domain (.gov.in / .nic.in).",
            )

        if clean_domain in (
            "aicte-india.org",
            "aicte.gov.in",
            "facilities.aicte-india.org",
            "pgscholarship.aicte.gov.in",
            "ugc.gov.in",
            "dst.gov.in",
            "online-inspire.gov.in",
            "csirhrdg.res.in",
            "education.gov.in",
        ):
            return SourceClassificationResult(
                domain=clean_domain,
                category="CENTRAL_GOVERNMENT",
                is_official=True,
                trust_score=0.99,
                reason="Official statutory body / central ministry portal.",
            )

        # 3. University / Educational Institution identification
        if clean_domain.endswith(".ac.in") or clean_domain.endswith(".edu.in") or "bitsadmission.com" in clean_domain:
            return SourceClassificationResult(
                domain=clean_domain,
                category="UNIVERSITY",
                is_official=True,
                trust_score=0.95,
                reason="Official Indian accredited university / academic institution domain.",
            )

        # 4. Corporate CSR Programs
        for csr_domain in KNOWN_CORPORATE_CSR_DOMAINS:
            if clean_domain == csr_domain or clean_domain.endswith("." + csr_domain):
                return SourceClassificationResult(
                    domain=clean_domain,
                    category="CORPORATE_CSR",
                    is_official=True,
                    trust_score=0.90,
                    reason=f"Official corporate CSR education grant provider domain ({csr_domain}).",
                )

        # 5. Philanthropic Trusts and Foundations
        for trust_domain in KNOWN_TRUST_DOMAINS:
            if clean_domain == trust_domain or clean_domain.endswith("." + trust_domain):
                return SourceClassificationResult(
                    domain=clean_domain,
                    category="TRUST_FOUNDATION",
                    is_official=True,
                    trust_score=0.90,
                    reason=f"Registered philanthropic trust / educational foundation domain ({trust_domain}).",
                )

        # 6. Aggregators & Discovery Portals
        for agg_domain in KNOWN_AGGREGATOR_DOMAINS:
            if clean_domain == agg_domain or clean_domain.endswith("." + agg_domain):
                return SourceClassificationResult(
                    domain=clean_domain,
                    category="AGGREGATOR",
                    is_official=False,
                    trust_score=0.50,
                    reason=f"Scholarship discovery aggregator ({agg_domain}); requires primary source for verification.",
                )

        # 7. Unclassified / Unknown
        return SourceClassificationResult(
            domain=clean_domain,
            category="UNKNOWN",
            is_official=False,
            trust_score=0.20,
            reason="Unrecognized domain; neither official government, academic institute, nor verified CSR provider.",
        )
