import pytest
from app.services.crawling.security import validate_url_safety


def test_ssrf_blocks_loopback_ip():
    is_safe, msg = validate_url_safety("http://127.0.0.1:8000/api/health")
    assert is_safe is False
    assert "restricted network" in msg or "restricted IP" in msg or "restricted host" in msg


def test_ssrf_blocks_localhost():
    is_safe, msg = validate_url_safety("http://localhost:8000")
    assert is_safe is False
    assert "restricted host 'localhost'" in msg


def test_ssrf_blocks_private_ip_ranges():
    # 10.0.0.0/8
    is_safe, msg = validate_url_safety("http://10.1.2.3/secret")
    assert is_safe is False
    assert "restricted network" in msg

    # 192.168.0.0/16
    is_safe, msg = validate_url_safety("http://192.168.1.1/admin")
    assert is_safe is False
    assert "restricted network" in msg

    # 172.16.0.0/12
    is_safe, msg = validate_url_safety("http://172.16.0.5/api")
    assert is_safe is False
    assert "restricted network" in msg


def test_ssrf_blocks_cloud_metadata_ip():
    is_safe, msg = validate_url_safety("http://169.254.169.254/latest/meta-data/")
    assert is_safe is False
    assert "restricted" in msg


def test_ssrf_blocks_google_metadata_host():
    is_safe, msg = validate_url_safety("http://metadata.google.internal/computeMetadata/v1/")
    assert is_safe is False
    assert "restricted host" in msg or "private domain" in msg


def test_ssrf_blocks_non_http_schemes():
    is_safe, msg = validate_url_safety("file:///C:/Windows/win.ini")
    assert is_safe is False
    assert "Unsupported scheme" in msg

    is_safe, msg = validate_url_safety("ftp://ftp.example.com")
    assert is_safe is False
    assert "Unsupported scheme" in msg


def test_ssrf_allows_safe_public_domains(monkeypatch):
    # Mock socket.getaddrinfo to resolve to a public IP address (e.g. 164.100.1.1)
    def mock_getaddrinfo(host, port):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("164.100.1.1", 443))]

    import socket
    monkeypatch.setattr(socket, "getaddrinfo", mock_getaddrinfo)

    is_safe, msg = validate_url_safety("https://scholarships.gov.in/public/schemeGuidelines")
    assert is_safe is True
