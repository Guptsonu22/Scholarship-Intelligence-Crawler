import re
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup
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
        "Reliance Foundation",
        "Tata Trusts",
        "Oil and Natural Gas Corporation",
        "ONGC Foundation",
        "K.C. Mahindra Education Trust",
        "Narotam Sekhsaria Foundation",
        "Sitaram Jindal Foundation",
        "Government of Karnataka",
        "Government of Maharashtra",
        "Government of Uttar Pradesh",
        "Government of Odisha",
        "Government of West Bengal",
        "Department of Science and Technology",
    ]

    COURSE_LEVEL_PATTERNS = {
        "Postgraduate / Master's / PhD": re.compile(r"\b(?:postgraduate|master'?s|m\.?tech|m\.?sc|m\.?a|mba|ph\.?d|doctoral)\b", re.I),
        "Undergraduate / Bachelor's": re.compile(r"\b(?:undergraduate|bachelor'?s|b\.?tech|b\.?sc|b\.?a|b\.?com|bba|mbbs)\b", re.I),
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

        # 1. Scholarship Name Extraction
        cls._extract_scholarship_name(soup, data, source_url)

        # 2. Provider Extraction
        cls._extract_provider(soup, data, source_url)

        # 3. Benefits / Amount
        cls._extract_amount_benefit(soup, data, source_url)

        # 4. Dates / Deadlines
        cls._extract_dates(soup, data, source_url)

        # 5. Eligibility Criteria
        cls._extract_eligibility(soup, data, source_url)

        # 6. Documents Required
        cls._extract_documents(soup, data, source_url)

        # 7. Application URL
        cls._extract_application_url(soup, data, source_url)

        return data

    @classmethod
    def _extract_scholarship_name(cls, soup: BeautifulSoup, data: ExtractedScholarshipData, source_url: str):
        # Check <h1>, <h2>, or prominent heading
        heading = soup.find(["h1", "h2"])
        name_candidate = None
        selector = None

        if heading:
            text = heading.get_text(separator=" ", strip=True)
            if len(text) > 5 and len(text) < 200 and re.search(r"scholarship|fellowship|scheme|yojana|grant|award", text, re.I):
                name_candidate = text
                selector = heading.name

        if not name_candidate and data.page_title:
            clean_title = re.split(r"[-|:]", data.page_title)[0].strip()
            if len(clean_title) > 5 and re.search(r"scholarship|fellowship|scheme|yojana", clean_title, re.I):
                name_candidate = clean_title
                selector = "title"

        if name_candidate:
            data.name = name_candidate
            data.evidence_list.append(
                RawEvidenceItem(
                    field_name="name",
                    extracted_value=name_candidate,
                    evidence_text=name_candidate,
                    html_selector=selector,
                )
            )
        else:
            data.validation_warnings.append("Scholarship name could not be deterministically determined from headings or title.")

    @classmethod
    def _extract_provider(cls, soup: BeautifulSoup, data: ExtractedScholarshipData, source_url: str):
        full_text = soup.get_text(separator=" ", strip=True)
        for provider in cls.KNOWN_PROVIDERS:
            if re.search(r"\b" + re.escape(provider) + r"\b", full_text, re.I):
                data.provider = provider
                # Extract snippet
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
    def _extract_amount_benefit(cls, soup: BeautifulSoup, data: ExtractedScholarshipData, source_url: str):
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

    @classmethod
    def _extract_dates(cls, soup: BeautifulSoup, data: ExtractedScholarshipData, source_url: str):
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

    @classmethod
    def _extract_eligibility(cls, soup: BeautifulSoup, data: ExtractedScholarshipData, source_url: str):
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
        elig_headers = soup.find_all(string=re.compile(r"eligibility|who can apply|criteria", re.I))
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
            if re.search(r"\b(?:apply\s+online|apply\s+now|registration|application\s+form|apply\s+here)\b", text, re.I):
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
