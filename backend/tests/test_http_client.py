import io
import socket
import pytest
import requests
from unittest.mock import MagicMock
from app.services.crawling.http_client import EthicalHttpClient


@pytest.fixture
def mock_public_dns(monkeypatch):
    """Ensures mock public IP resolution for test domains."""
    def mock_getaddrinfo(host, port):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("164.100.1.1", 443))]
    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)


def test_http_client_fetch_success(mock_public_dns, monkeypatch):
    client = EthicalHttpClient(timeout=5, default_delay=0.0)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "text/html; charset=utf-8"}
    mock_resp.encoding = "utf-8"
    mock_resp.iter_content.return_value = [b"<html><body><h1>National Scholarship</h1></body></html>"]

    monkeypatch.setattr(client.session, "get", lambda *args, **kwargs: mock_resp)
    # Mock robots to allow
    client.robots_manager.is_allowed = lambda url: (True, "Allowed")

    result = client.fetch("https://scholarships.gov.in/test")
    assert result.status == "SUCCESS"
    assert result.http_status == 200
    assert "<h1>National Scholarship</h1>" in result.html
    assert result.content_hash is not None
    assert len(result.content_hash) == 64


def test_http_client_blocks_ssrf():
    client = EthicalHttpClient(timeout=5, default_delay=0.0)
    result = client.fetch("http://127.0.0.1:8000/admin")
    assert result.status == "BLOCKED_SSRF"
    assert "restricted" in result.error_reason


def test_http_client_handles_http_error(mock_public_dns, monkeypatch):
    client = EthicalHttpClient(timeout=5, default_delay=0.0)

    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.headers = {"Content-Type": "text/html"}

    monkeypatch.setattr(client.session, "get", lambda *args, **kwargs: mock_resp)
    client.robots_manager.is_allowed = lambda url: (True, "Allowed")

    result = client.fetch("https://scholarships.gov.in/non-existent")
    assert result.status == "HTTP_ERROR"
    assert result.http_status == 404


def test_http_client_rejects_unsupported_content_type(mock_public_dns, monkeypatch):
    client = EthicalHttpClient(timeout=5, default_delay=0.0)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.headers = {"Content-Type": "application/pdf"}

    monkeypatch.setattr(client.session, "get", lambda *args, **kwargs: mock_resp)
    client.robots_manager.is_allowed = lambda url: (True, "Allowed")

    result = client.fetch("https://scholarships.gov.in/brochure.pdf")
    assert result.status == "INVALID_CONTENT_TYPE"
    assert "Unsupported Content-Type" in result.error_reason


def test_http_client_handles_timeout(mock_public_dns, monkeypatch):
    client = EthicalHttpClient(timeout=1, default_delay=0.0, max_retries=1)

    def mock_timeout(*args, **kwargs):
        raise requests.exceptions.Timeout("Read timed out")

    monkeypatch.setattr(client.session, "get", mock_timeout)
    client.robots_manager.is_allowed = lambda url: (True, "Allowed")

    result = client.fetch("https://scholarships.gov.in/slow-page")
    assert result.status == "TIMEOUT"
    assert "timed out" in result.error_reason.lower()


def test_http_client_blocks_unsafe_redirect(mock_public_dns, monkeypatch):
    client = EthicalHttpClient(timeout=5, default_delay=0.0)

    # First response redirects to loopback
    mock_redirect = MagicMock()
    mock_redirect.status_code = 302
    mock_redirect.headers = {"Location": "http://127.0.0.1:8000/internal"}

    monkeypatch.setattr(client.session, "get", lambda *args, **kwargs: mock_redirect)
    client.robots_manager.is_allowed = lambda url: (True, "Allowed")

    result = client.fetch("https://scholarships.gov.in/redirect")
    assert result.status == "BLOCKED_SSRF"
    assert "127.0.0.1" in result.final_url
