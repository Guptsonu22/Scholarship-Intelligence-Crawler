import pytest
from app.services.extraction.date_parser import DateParser


def test_parse_slash_format_date():
    text = "The application closing date is 31/10/2026."
    date_str, snippet = DateParser.parse_deadline(text)
    assert date_str == "2026-10-31"
    assert "31/10/2026" in snippet


def test_parse_hyphen_format_date():
    text = "Last Date to Apply: 15-11-2026."
    date_str, snippet = DateParser.parse_deadline(text)
    assert date_str == "2026-11-15"
    assert "15-11-2026" in snippet


def test_parse_text_month_date():
    text = "Closing Date: 31st October 2026 for all categories."
    date_str, snippet = DateParser.parse_deadline(text)
    assert date_str == "2026-10-31"
    assert "31st October 2026" in snippet


def test_parse_month_day_year_date():
    text = "Deadline: November 30, 2026."
    date_str, snippet = DateParser.parse_deadline(text)
    assert date_str == "2026-11-30"


def test_parse_deadline_missing_returns_none():
    text = "Students are requested to register and fill the form."
    date_str, snippet = DateParser.parse_deadline(text)
    assert date_str is None
    assert snippet is None
