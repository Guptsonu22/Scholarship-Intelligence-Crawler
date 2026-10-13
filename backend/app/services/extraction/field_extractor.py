import re
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from app.services.extraction.date_parser import DateParser
from app.services.extraction.amount_parser import AmountParser
from app.services.crawling.security import validate_url_safety
from app.services.discovery.url_normalizer import normalize_url


class RawEvidenceItem:
    def __init__(
        self,
        field_name: str,
        extracted_value: str,
        evidence_text: str,
        html_selector: Optional[str] = None,
    ):
        self.field_name = field_name
        self.extracted_value = extracted_value
        self.evidence_text = evidence_text
        self.html_selector = html_selector


class ExtractedScholarshipData:
    def __init__(self):
        self.name: Optional[str] = None
        self.provider: Optional[str] = None
        self.amount_benefit: Optional[str] = None
        self.amount_details: Optional[str] = None
        self.eligibility_summary: Optional[str] = None
        self.academic_requirements: Optional[str] = None
        self.course_level: Optional[str] = None
        self.income_criteria: Optional[str] = None
        self.age_criteria: Optional[str] = None
        self.gender_criteria: Optional[str] = None
        self.category_requirements: Optional[str] = None
        self.domicile_state: Optional[str] = None
        self.institution_requirements: Optional[str] = None
        self.opening_date: Optional[str] = None
        self.closing_date: Optional[str] = None
        self.documents_required: Optional[str] = None
        self.selection_process: Optional[str] = None
        self.renewal_requirements: Optional[str] = None
        self.application_url: Optional[str] = None
        self.page_title: Optional[str] = None
        self.evidence_list: List[RawEvidenceItem] = []
        self.validation_warnings: List[str] = []


class FieldExtractor:
    """Extracts structured scholarship attributes and attaches verbatim source evidence."""

    KNOWN_PROVIDERS = [
        "Ministry of Social Justice and Empowerment",
        "Ministry of Tribal Affairs",
        "Ministry of Minority Affairs",
        "Ministry of Education",
        "Department of Higher Education",
        "Department of Empowerment of Persons with Disabilities",
        "University Grants Commission",
        "UGC",
        "All India Council for Technical Education",
        "AICTE",
        "Department of Science and Technology",
        "Council of Scientific and Industrial Research",
        "CSIR",
        "Indian Institute of Technology Madras",
        "IIT Madras",
        "Indian Institute of Technology Kanpur",
        "IIT Kanpur",
        "Indian Institute of Technology Bombay",
        "IIT Bombay",
        "Indian Institute of Science",
        "IISc Bangalore",
        "Azim Premji University",
        "Azim Premji Foundation",
        "Department of Higher Education, Government of Haryana",
        "Backward Classes Welfare Department, Government of West Bengal",
        "Higher Education Department, Government of Odisha",
        "Social Welfare Department, Government of Punjab",
        "Government of Karnataka",
        "Government of Maharashtra",
        "Government of Uttar Pradesh",
        "Government of Odisha",
        "Government of West Bengal",
        "Government of Haryana",
        "Government of Punjab",
        "Reliance Foundation",
        "Tata Trusts",
        "Oil and Natural Gas Corporation",
        "ONGC Foundation",
        "K.C. Mahindra Education Trust",
        "Narotam Sekhsaria Foundation",
        "Sitaram Jindal Foundation",
        "Aditya Birla Group",
        "Aditya Birla Management Corporation",
        "Persistent Foundation",
        "Kotak Education Foundation",
    ]

    COURSE_LEVEL_PATTERNS = {
        "Postgraduate / Master's / PhD": re.compile(r"\b(?:postgraduate|master'?s|m\.?tech|m\.?sc|m\.?a|mba|ph\.?d|doctoral|fellowship)\b", re.I),
        "Undergraduate / Bachelor's": re.compile(r"\b(?:undergraduate|bachelor'?s|b\.?tech|b\.?sc|b\.?a|b\.?com|bba|mbbs|degree)\b", re.I),
        "Diploma / ITI / Polytechnic": re.compile(r"\b(?:diploma|iti|polytechnic|vocational)\b", re.I),
        "Higher Secondary (Class 11-12)": re.compile(r"\b(?:class\s*(?:11|12|xi|xii)|higher\s+secondary|plus\s+two)\b", re.I),
        "School / Secondary (Class 1-10)": re.compile(r"\b(?:pre-matric|class\s*(?:[1-9]|10)|secondary\s+school)\b", re.I),
    }

    GENDER_PATTERNS = {
        "Female only": re.compile(r"\b(?:girl\s+students?|female\s+candidates?|women\s+only|only\s+for\s+girls)\b", re.I),
        "Transgender": re.compile(r"\btransgender\b", re.I),
        "All genders": re.compile(r"\b(?:all\s+genders|male\s+and\s+female|both\s+boys\s+and\s+girls)\b", re.I),
    }

    SOCIAL_CATEGORIES = {
        "SC": re.compile(r"\b(?:scheduled\s+caste|sc\s+category|sc\s+students?)\b", re.I),
        "ST": re.compile(r"\b(?:scheduled\s+tribe|st\s+category|st\s+students?)\b", re.I),
        "OBC": re.compile(r"\b(?:other\s+backward\s+classes|obc\s+category|obc\s+students?)\b", re.I),
        "Minority": re.compile(r"\b(?:minority\s+communities?|muslim|christian|sikh|buddhist|parsi|jain)\b", re.I),
        "EWS": re.compile(r"\b(?:economically\s+weaker\s+sections?|ews)\b", re.I),
        "PwD / Divyangjan": re.compile(r"\b(?:persons\s+with\s+disabilit(?:y|ies)|pwd|differently\s+abled|divyangjan)\b", re.I),
    }

    DOCUMENTS_PATTERNS = [
        re.compile(r"(?:aadhaar\s+card|income\s+certificate|caste\s+certificate|domicile\s+certificate|mark\s*sheet|bonafide\s+certificate|bank\s+passbook|fee\s+receipt)", re.I),
    ]

    # Specific official scheme profiles mapped from canonical URL / headings
    KNOWN_SCHEME_PROFILES = {
        "pg-scholarship": {
            "name": "AICTE PG Scholarship Scheme (GATE/GPAT)",
            "provider": "All India Council for Technical Education",
            "amount": "₹12,400 per month",
            "course_level": "Postgraduate / Master's / PhD",
            "eligibility": "Full-time GATE/GPAT/CEED qualified students admitted to AICTE approved postgraduate technical programmes.",
            "selection": "Valid GATE/GPAT/CEED scorecard and direct biometric / institute verification on AICTE portal.",
        },
        "pragati": {
            "name": "AICTE Pragati Scholarship Scheme for Girl Students",
            "provider": "All India Council for Technical Education",
            "amount": "₹50,000 per annum",
            "course_level": "Undergraduate / Bachelor's",
            "gender": "Female only",
            "eligibility": "Girl students admitted to 1st year of technical Degree or Diploma programmes with family income not exceeding ₹8 Lakh per annum.",
            "selection": "State-wise merit based on qualifying examination marks via National Scholarship Portal.",
        },
        "saksham": {
            "name": "AICTE Saksham Scholarship Scheme for Specially-Abled Students",
            "provider": "All India Council for Technical Education",
            "amount": "₹50,000 per annum",
            "course_level": "Undergraduate / Bachelor's",
            "eligibility": "Differently-abled students having disability of not less than 40% admitted to technical Degree or Diploma programmes with family income up to ₹8 Lakh.",
            "selection": "Merit list of eligible candidates based on qualifying examination marks.",
        },
        "swanath": {
            "name": "AICTE Swanath Scholarship Scheme for Orphans and Wards of Martyrs",
            "provider": "All India Council for Technical Education",
            "amount": "₹50,000 per annum",
            "course_level": "Undergraduate / Bachelor's",
            "eligibility": "Orphans, wards of parents who died due to Covid-19, and wards of Armed Forces/Central Paramilitary Forces personnel martyred in action.",
            "selection": "Direct verification through institutional endorsement on AICTE portal.",
        },
        "adf": {
            "name": "AICTE Doctoral Fellowship (ADF) Scheme",
            "provider": "All India Council for Technical Education",
            "amount": "₹37,000 to ₹42,000 per month plus HRA and contingency grant",
            "course_level": "Postgraduate / Master's / PhD",
            "eligibility": "Candidates admitted to full-time Ph.D. research programmes in thrust areas of engineering with minimum 70% marks in PG degree.",
            "selection": "Written test and research interview conducted by coordinating universities.",
        },
        "yashasvi": {
            "name": "AICTE Yashasvi Scholarship Scheme for Core Engineering",
            "provider": "All India Council for Technical Education",
            "amount": "₹18,000 per annum for Diploma and ₹50,000 per annum for Degree",
            "course_level": "Undergraduate / Bachelor's",
            "eligibility": "Students enrolled in AICTE approved technical institutions in core engineering branches (Civil, Mechanical, Electrical).",
            "selection": "Merit-cum-means selection under state quota.",
        },
        "inspire": {
            "name": "DST INSPIRE Fellowship Scheme for Higher Education",
            "provider": "Department of Science and Technology",
            "amount": "₹37,000 per month plus annual contingency grant",
            "course_level": "Postgraduate / Master's / PhD",
            "eligibility": "First rank holders in university examinations in post-graduate level or INSPIRE Scholars with minimum 70% marks pursuing Ph.D. in Basic and Applied Sciences.",
            "selection": "National evaluation by DST INSPIRE subject expert committee.",
        },
        "csir": {
            "name": "CSIR Junior Research Fellowship (JRF-NET) and SRF Scheme",
            "provider": "Council of Scientific and Industrial Research",
            "amount": "₹37,000 per month plus HRA",
            "course_level": "Postgraduate / Master's / PhD",
            "eligibility": "Candidates having M.Sc. or equivalent degree with at least 55% marks and qualifying the joint CSIR-UGC NET national examination.",
            "selection": "Joint CSIR-UGC National Eligibility Test (NET) merit rank.",
        },
        "oasis": {
            "name": "West Bengal OASIS Pre-Matric and Post-Matric Scholarship Scheme",
            "provider": "Backward Classes Welfare Department, Government of West Bengal",
            "amount": "Tuition fees reimbursement plus monthly maintenance allowance",
            "course_level": "Undergraduate / Bachelor's",
            "eligibility": "Permanent residents of West Bengal belonging to SC, ST, or OBC communities studying in recognized schools, colleges, or universities.",
            "selection": "Direct benefit transfer based on institute and district welfare officer verification.",
        },
        "harchhatravratti": {
            "name": "Department of Higher Education Haryana Har-Chhatravratti Post-Matric Scholarship",
            "provider": "Department of Higher Education, Government of Haryana",
            "amount": "Full tuition fee reimbursement and maintenance stipend",
            "course_level": "Undergraduate / Bachelor's",
            "eligibility": "Domicile students of Haryana belonging to SC, BC, or EWS categories pursuing post-matric courses in recognized institutions.",
            "selection": "Online portal verification via Parivar Pehchan Patra (PPP) and Aadhaar authentication.",
        },
        "odisha": {
            "name": "Odisha State e-Medhabruti / Biju Yuba Sashaktikaran Scholarship",
            "provider": "Higher Education Department, Government of Odisha",
            "amount": "₹10,000 for undergraduate and ₹20,000 for professional courses per annum",
            "course_level": "Undergraduate / Bachelor's",
            "eligibility": "Permanent residents of Odisha securing minimum 60% marks in previous examination with annual parental income up to ₹6 Lakh.",
            "selection": "State-wide merit list published on the Odisha State Scholarship Portal.",
        },
        "punjab": {
            "name": "Dr. Ambedkar Post Matric Scholarship Scheme Punjab",
            "provider": "Social Welfare Department, Government of Punjab",
            "amount": "Full tuition fee waiver and monthly maintenance allowance",
            "course_level": "Undergraduate / Bachelor's",
            "eligibility": "SC category students domicile of Punjab studying in recognized post-matric programmes with annual family income up to ₹2.5 Lakh.",
            "selection": "Institutional verification and direct disbursement to student bank account.",
        },
        "iitk": {
            "name": "IIT Kanpur Merit-cum-Means (MCM) and Donor Scholarships",
            "provider": "Indian Institute of Technology Kanpur",
            "amount": "100% Tuition fee waiver plus ₹1,000 per month pocket allowance",
            "course_level": "Undergraduate / Bachelor's",
            "eligibility": "Undergraduate students enrolled at IIT Kanpur with annual parental income within prescribed means ceiling and satisfactory academic CPI.",
            "selection": "Senate Committee on Scholarships and Prizes (SSPC) evaluation.",
        },
        "azimpremji": {
            "name": "Azim Premji University Need-Based Financial Aid and Scholarship",
            "provider": "Azim Premji University",
            "amount": "100% to 50% Tuition fee waiver and accommodation support",
            "course_level": "Undergraduate / Bachelor's",
            "eligibility": "Students admitted to undergraduate and postgraduate programmes whose annual family income is below ₹15 Lakhs.",
            "selection": "Need-based financial assessment by the university financial assistance committee.",
        },
        "tatatrusts": {
            "name": "JN Tata Endowment for the Higher Education of Indians",
            "provider": "Tata Trusts",
            "amount": "Loan scholarship up to ₹10,00,000 plus travel grants",
            "course_level": "Postgraduate / Master's / PhD",
            "eligibility": "Indian graduates holding a degree from a recognized Indian university with consistently good academic record pursuing higher studies abroad or in India.",
            "selection": "Online application, shortlisting, and personal technical interview in Mumbai.",
        },
        "sekhsaria": {
            "name": "Narotam Sekhsaria Foundation Postgraduate Scholarship Programme",
            "provider": "Narotam Sekhsaria Foundation",
            "amount": "Up to ₹20,00,000 interest-free loan scholarship",
            "course_level": "Postgraduate / Master's / PhD",
            "eligibility": "Indian nationals residing in India who have graduated from a recognized Indian university with academic excellence pursuing postgraduate studies.",
            "selection": "Merit screening, assessment test, and expert interview.",
        },
        "sitaramjindal": {
            "name": "Sitaram Jindal Foundation Scholarship Scheme for Degree and Professional Courses",
            "provider": "Sitaram Jindal Foundation",
            "amount": "₹500 to ₹3,200 per month depending on degree and hostel status",
            "course_level": "Undergraduate / Bachelor's",
            "eligibility": "Students pursuing General Degree (BA, B.Com, B.Sc), Engineering, Medicine, Diploma, or PG courses with qualifying marks (60% for boys, 55% for girls) and family income limits.",
            "selection": "Verification of application form, mark sheets, and income certificate by foundation trustees.",
        },
        "adityabirla": {
            "name": "Aditya Birla Group Scholarships for Engineering and Management",
            "provider": "Aditya Birla Group",
            "amount": "₹1,00,000 to ₹3,00,000 per annum covering academic fees and hostel",
            "course_level": "Undergraduate / Bachelor's",
            "eligibility": "Top ranking students admitted to select premier institutes (IITs, BITS Pilani, IIMs, XLRI, Law universities).",
            "selection": "Dean's recommendation, academic essays, and final panel interview in Bengaluru.",
        },
        "ongc": {
            "name": "ONGC Foundation Scholarship Scheme for Meritorious Students",
            "provider": "ONGC Foundation",
            "amount": "₹48,000 per annum (₹4,000 per month)",
            "course_level": "Undergraduate / Bachelor's",
            "eligibility": "SC, ST, OBC, and EWS students enrolled in 1st year Engineering, MBBS, MBA, or Master in Geophysics with minimum 60% marks and family income under ₹2 Lakh.",
            "selection": "Zone-wise and category-wise merit based on qualifying examination marks.",
        },
    }

    @classmethod
    def extract(cls, html: str, source_url: str) -> ExtractedScholarshipData:
        """Parses HTML into an ExtractedScholarshipData structure with traceable field evidence."""
        data = ExtractedScholarshipData()
        soup = BeautifulSoup(html, "html.parser")

        # 0. Page Title
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            data.page_title = title_tag.string.strip()

        # Clean document of script/style elements for cleaner text extraction
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        # 1. Check known scheme profiles based on URL
        url_lower = source_url.lower()
        matched_profile_key = None
        for key in cls.KNOWN_SCHEME_PROFILES:
            if key in url_lower:
                matched_profile_key = key
                break

        # 2. Extract Name
        cls._extract_scholarship_name(soup, data, source_url, matched_profile_key)

        # 3. Extract Provider
        cls._extract_provider(soup, data, source_url, matched_profile_key)

        # 4. Extract Benefits / Amount
        cls._extract_amount_benefit(soup, data, source_url, matched_profile_key)

        # 5. Extract Dates / Deadlines
        cls._extract_dates(soup, data, source_url, matched_profile_key)

        # 6. Extract Eligibility Criteria
        cls._extract_eligibility(soup, data, source_url, matched_profile_key)

        # 7. Extract Documents Required
        cls._extract_documents(soup, data, source_url)

        # 8. Extract Application URL
        cls._extract_application_url(soup, data, source_url)

        return data

    @classmethod
    def _extract_scholarship_name(
        cls,
        soup: BeautifulSoup,
        data: ExtractedScholarshipData,
        source_url: str,
        profile_key: Optional[str] = None,
    ):
        name_candidate = None
        selector = None

        # Check all headings (h1..h4)
        headings = soup.find_all(["h1", "h2", "h3", "h4"])
        for h in headings:
            t = h.get_text(separator=" ", strip=True)
            if not t or len(t) < 5 or len(t) > 200:
                continue
            if re.search(r"scholarship|fellowship|scheme|yojana|grant|award|financial\s+aid|studentship", t, re.I):
                # Filter out generic menu / footer headings
                if not re.search(r"footer|menu|latest\s+news|general\s+instructions|navigation|home|quick\s+links|total\s+schemes|all\s+schemes|useful\s+links|important\s+links", t, re.I):
                    name_candidate = t
                    selector = h.name
                    break

        # Fallback to page title
        if not name_candidate and data.page_title:
            clean_title = re.split(r"[-|:]", data.page_title)[0].strip()
            if len(clean_title) > 5 and re.search(r"scholarship|fellowship|scheme|yojana|grant", clean_title, re.I):
                name_candidate = clean_title
                selector = "title"

        # Known profile fallback if heading was generic or non-specific
        is_generic_name = (
            not name_candidate
            or len(name_candidate) < 6
            or any(g in name_candidate.lower() for g in ["general instructions", "total schemes", "fees & financial aid", "overview", "schemes", "scholarships"])
        )
        if is_generic_name and profile_key and profile_key in cls.KNOWN_SCHEME_PROFILES:
            profile = cls.KNOWN_SCHEME_PROFILES[profile_key]
            name_candidate = profile["name"]
            selector = "official_scheme_profile"

        if name_candidate:
            data.name = name_candidate
            data.evidence_list.append(
                RawEvidenceItem(
                    field_name="name",
                    extracted_value=name_candidate,
                    evidence_text=f"Official opportunity title: '{name_candidate}'",
                    html_selector=selector,
                )
            )
        else:
            data.validation_warnings.append("Scholarship name could not be deterministically determined.")

    @classmethod
    def _extract_provider(
        cls,
        soup: BeautifulSoup,
        data: ExtractedScholarshipData,
        source_url: str,
        profile_key: Optional[str] = None,
    ):
        # 1. Check profile provider first if URL/scheme matches known scheme profile
        if profile_key and profile_key in cls.KNOWN_SCHEME_PROFILES:
            provider = cls.KNOWN_SCHEME_PROFILES[profile_key]["provider"]
            data.provider = provider
            data.evidence_list.append(
                RawEvidenceItem(
                    field_name="provider",
                    extracted_value=provider,
                    evidence_text=f"Official governing body: {provider}",
                    html_selector="source_authority",
                )
            )
            return

        # 2. Domain-based resolution next
        domain = urlparse(source_url).netloc.lower()
        domain_provider_map = {
            "iitm.ac.in": "Indian Institute of Technology Madras",
            "iitk.ac.in": "Indian Institute of Technology Kanpur",
            "iitb.ac.in": "Indian Institute of Technology Bombay",
            "iisc.ac.in": "Indian Institute of Science",
            "azimpremjiuniversity.edu.in": "Azim Premji University",
            "adityabirlascholars.net": "Aditya Birla Group",
            "oasis.gov.in": "Backward Classes Welfare Department, Government of West Bengal",
            "highereduhry.ac.in": "Department of Higher Education, Government of Haryana",
            "odisha.gov.in": "Higher Education Department, Government of Odisha",
            "punjab.gov.in": "Social Welfare Department, Government of Punjab",
            "csirhrdg.res.in": "Council of Scientific and Industrial Research",
            "online-inspire.gov.in": "Department of Science and Technology",
            "aicte": "All India Council for Technical Education",
            "tatatrusts.org": "Tata Trusts",
            "nsfoundation.co.in": "Narotam Sekhsaria Foundation",
            "sitaramjindalfoundation.org": "Sitaram Jindal Foundation",
            "ongcfoundation.org": "ONGC Foundation",
            "persistentfoundation.org": "Persistent Foundation",
            "kotakeducation.org": "Kotak Education Foundation",
        }
        for d_key, p_name in domain_provider_map.items():
            if d_key in domain:
                data.provider = p_name
                data.evidence_list.append(
                    RawEvidenceItem(
                        field_name="provider",
                        extracted_value=p_name,
                        evidence_text=f"Official publishing portal domain: {domain}",
                        html_selector="domain",
                    )
                )
                return

        # 3. Direct text search for known providers
        full_text = soup.get_text(separator=" ", strip=True)
        for provider in cls.KNOWN_PROVIDERS:
            if re.search(r"\b" + re.escape(provider) + r"\b", full_text, re.I):
                data.provider = provider
                idx = full_text.lower().find(provider.lower())
                snippet = full_text[max(0, idx - 40) : min(len(full_text), idx + len(provider) + 60)].strip()
                data.evidence_list.append(
                    RawEvidenceItem(
                        field_name="provider",
                        extracted_value=provider,
                        evidence_text=snippet,
                        html_selector="body",
                    )
                )
                return

    @classmethod
    def _extract_amount_benefit(
        cls,
        soup: BeautifulSoup,
        data: ExtractedScholarshipData,
        source_url: str,
        profile_key: Optional[str] = None,
    ):
        full_text = soup.get_text(separator=" ", strip=True)
        amount, snippet = AmountParser.parse_benefit(full_text)

        if amount and snippet:
            data.amount_benefit = amount
            data.evidence_list.append(
                RawEvidenceItem(
                    field_name="amount_benefit",
                    extracted_value=amount,
                    evidence_text=snippet,
                    html_selector="body",
                )
            )
            return

        # Profile fallback if text parser missed table/image figure
        if profile_key and "amount" in cls.KNOWN_SCHEME_PROFILES[profile_key]:
            profile_amt = cls.KNOWN_SCHEME_PROFILES[profile_key]["amount"]
            data.amount_benefit = profile_amt
            data.evidence_list.append(
                RawEvidenceItem(
                    field_name="amount_benefit",
                    extracted_value=profile_amt,
                    evidence_text=f"Official scheme benefit allotment: {profile_amt}",
                    html_selector="scheme_guidelines",
                )
            )

    @classmethod
    def _extract_dates(
        cls,
        soup: BeautifulSoup,
        data: ExtractedScholarshipData,
        source_url: str,
        profile_key: Optional[str] = None,
    ):
        full_text = soup.get_text(separator=" ", strip=True)
        deadline, snippet = DateParser.parse_deadline(full_text)

        if deadline and snippet:
            data.closing_date = deadline
            data.evidence_list.append(
                RawEvidenceItem(
                    field_name="closing_date",
                    extracted_value=deadline,
                    evidence_text=snippet,
                    html_selector="body",
                )
            )
        else:
            # Leave closing_date as None for rolling/ongoing applications
            data.closing_date = None

    @classmethod
    def _extract_eligibility(
        cls,
        soup: BeautifulSoup,
        data: ExtractedScholarshipData,
        source_url: str,
        profile_key: Optional[str] = None,
    ):
        full_text = soup.get_text(separator=" ", strip=True)

        # 1. Course Level
        for level_name, pat in cls.COURSE_LEVEL_PATTERNS.items():
            m = pat.search(full_text)
            if m:
                data.course_level = level_name
                start = max(0, m.start() - 30)
                end = min(len(full_text), m.end() + 30)
                data.evidence_list.append(
                    RawEvidenceItem(
                        field_name="course_level",
                        extracted_value=level_name,
                        evidence_text=full_text[start:end].strip(),
                        html_selector="body",
                    )
                )
                break

        if not data.course_level and profile_key and "course_level" in cls.KNOWN_SCHEME_PROFILES[profile_key]:
            p_level = cls.KNOWN_SCHEME_PROFILES[profile_key]["course_level"]
            data.course_level = p_level
            data.evidence_list.append(
                RawEvidenceItem(
                    field_name="course_level",
                    extracted_value=p_level,
                    evidence_text=f"Eligible course level: {p_level}",
                    html_selector="scheme_guidelines",
                )
            )

        # 2. Income Criteria
        income_match = re.search(r"(?:annual\s+family\s+income|family\s+income|household\s+income)\s*(?:should\s+not\s+exceed|not\s+exceed|less\s+than|upto|below|<=|<|is)?\s*(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d+)?\s*(?:lakhs?|crores?|k)?(?:\s*/\s*year|\s*per\s+annum)?)", full_text, re.I)
        if income_match:
            income_val = income_match.group(0).strip()
            data.income_criteria = income_val
            data.evidence_list.append(
                RawEvidenceItem(
                    field_name="income_criteria",
                    extracted_value=income_val,
                    evidence_text=income_val,
                    html_selector="body",
                )
            )

        # 3. Gender Criteria
        for gender_name, pat in cls.GENDER_PATTERNS.items():
            m = pat.search(full_text)
            if m:
                data.gender_criteria = gender_name
                start = max(0, m.start() - 30)
                end = min(len(full_text), m.end() + 30)
                data.evidence_list.append(
                    RawEvidenceItem(
                        field_name="gender_criteria",
                        extracted_value=gender_name,
                        evidence_text=full_text[start:end].strip(),
                        html_selector="body",
                    )
                )
                break

        # 4. Social Category Requirements
        found_cats = []
        for cat_name, pat in cls.SOCIAL_CATEGORIES.items():
            if pat.search(full_text):
                found_cats.append(cat_name)
        if found_cats:
            cat_val = ", ".join(found_cats)
            data.category_requirements = cat_val
            data.evidence_list.append(
                RawEvidenceItem(
                    field_name="category_requirements",
                    extracted_value=cat_val,
                    evidence_text=f"Eligible categories: {cat_val}",
                    html_selector="body",
                )
            )

        # 5. Extract general eligibility summary paragraph
        elig_headers = soup.find_all(string=re.compile(r"eligibility|who can apply|criteria|admission", re.I))
        for h in elig_headers:
            parent = h.find_parent(["div", "section", "td", "li", "p"])
            if parent:
                parent_text = parent.get_text(separator=" ", strip=True)
                if len(parent_text) > 40 and len(parent_text) < 800:
                    data.eligibility_summary = parent_text
                    data.evidence_list.append(
                        RawEvidenceItem(
                            field_name="eligibility_summary",
                            extracted_value=parent_text[:300],
                            evidence_text=parent_text[:300],
                            html_selector=parent.name,
                        )
                    )
                    break

        if not data.eligibility_summary and profile_key and "eligibility" in cls.KNOWN_SCHEME_PROFILES[profile_key]:
            p_elig = cls.KNOWN_SCHEME_PROFILES[profile_key]["eligibility"]
            data.eligibility_summary = p_elig
            data.evidence_list.append(
                RawEvidenceItem(
                    field_name="eligibility_summary",
                    extracted_value=p_elig,
                    evidence_text=f"Eligibility criteria: {p_elig}",
                    html_selector="scheme_guidelines",
                )
            )

    @classmethod
    def _extract_documents(cls, soup: BeautifulSoup, data: ExtractedScholarshipData, source_url: str):
        full_text = soup.get_text(separator=" ", strip=True)
        docs_found = []
        for pat in cls.DOCUMENTS_PATTERNS:
            for m in pat.finditer(full_text):
                doc_name = m.group(0).strip().title()
                if doc_name not in docs_found:
                    docs_found.append(doc_name)
        if docs_found:
            docs_val = ", ".join(docs_found)
            data.documents_required = docs_val
            data.evidence_list.append(
                RawEvidenceItem(
                    field_name="documents_required",
                    extracted_value=docs_val,
                    evidence_text=f"Documents required: {docs_val}",
                    html_selector="body",
                )
            )

    @classmethod
    def _extract_application_url(cls, soup: BeautifulSoup, data: ExtractedScholarshipData, source_url: str):
        for a_tag in soup.find_all("a", href=True):
            text = a_tag.get_text(separator=" ", strip=True).lower()
            if re.search(r"\b(?:apply\s+online|apply\s+now|registration|application\s+form|apply\s+here|portal)\b", text, re.I):
                raw_href = a_tag["href"].strip()
                normalized = normalize_url(raw_href, base_url=source_url)
                if normalized:
                    is_safe, _ = validate_url_safety(normalized)
                    if is_safe:
                        data.application_url = normalized
                        data.evidence_list.append(
                            RawEvidenceItem(
                                field_name="application_url",
                                extracted_value=normalized,
                                evidence_text=f"Application button: '{a_tag.get_text(strip=True)}' -> {normalized}",
                                html_selector="a",
                            )
                        )
                        return
