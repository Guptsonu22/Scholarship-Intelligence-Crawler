import pytest
from app.services.extraction.amount_parser import AmountParser


def test_parse_rupee_symbol_amount():
    text = "Eligible students will receive ₹50,000 per annum towards fees."
    amount, snippet = AmountParser.parse_benefit(text)
    assert "50,000" in amount
    assert "₹50,000" in snippet or "50,000" in snippet


def test_parse_rs_text_amount():
    text = "Scholarship Amount: Rs. 12,000 per year for pre-matric students."
    amount, snippet = AmountParser.parse_benefit(text)
    assert "12,000" in amount
    assert "Rs. 12,000" in snippet or "12,000" in snippet


def test_parse_lakh_amount():
    text = "Financial Assistance up to 2 Lakhs per annum."
    amount, snippet = AmountParser.parse_benefit(text)
    assert "2 Lakhs" in amount or "2" in amount


def test_parse_descriptive_benefit():
    text = "Selected scholars will be granted 100% Tuition Fee Waiver."
    benefit, snippet = AmountParser.parse_benefit(text)
    assert "tuition fee waiver" in benefit.lower()


def test_amount_missing_returns_none():
    text = "Applicants must submit marksheets and college certificates."
    amount, snippet = AmountParser.parse_benefit(text)
    assert amount is None
    assert snippet is None
