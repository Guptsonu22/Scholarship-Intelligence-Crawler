import hashlib
import logging
import time
from typing import Optional, Dict, Tuple
from urllib.parse import urlparse, urljoin
import requests
from app.core.config import settings
from app.services.crawling.security import validate_url_safety
from app.services.crawling.robots import RobotsPolicyManager

logger = logging.getLogger(__name__)

# Max allowable HTML response size (5 Megabytes)
MAX_RESPONSE_BYTES = 5 * 1024 * 1024

# Acceptable content-types for scraping
VALID_CONTENT_TYPES = (
    "text/html",
    "application/xhtml+xml",
    "text/plain",
)


class CrawlResult:
    """Standardized result container for a crawl attempt."""

    def __init__(
        self,
        url: str,
        final_url: Optional[str] = None,
        status: str = "FAILED",
        http_status: Optional[int] = None,
        content_type: Optional[str] = None,
        content_length: Optional[int] = None,
        content_hash: Optional[str] = None,
        html: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        error_reason: Optional[str] = None,
    ):
        self.url = url
        self.final_url = final_url or url
        self.status = status  # SUCCESS, HTTP_ERROR, TIMEOUT, BLOCKED_SSRF, ROBOTS_EXCLUDED, INVALID_CONTENT_TYPE, TOO_LARGE, NETWORK_ERROR
        self.http_status = http_status
        self.content_type = content_type
        self.content_length = content_length
        self.content_hash = content_hash
        self.html = html
        self.response_time_ms = response_time_ms
        self.error_reason = error_reason


class EthicalHttpClient:
    """Ethical, SSRF-safe HTTP client with per-domain throttling and content validation."""

    def __init__(
        self,
        user_agent: Optional[str] = None,
        timeout: Optional[int] = None,
        default_delay: Optional[float] = None,
        max_retries: Optional[int] = None,
    ):
        self.user_agent = user_agent or settings.CRAWLER_USER_AGENT
        self.timeout = timeout or settings.CRAWLER_REQUEST_TIMEOUT
        self.default_delay = default_delay or settings.CRAWLER_DEFAULT_DELAY_SECONDS
        self.max_retries = max_retries or settings.CRAWLER_MAX_RETRIES
        self.robots_manager = RobotsPolicyManager(self.user_agent)
        self._last_domain_request: Dict[str, float] = {}
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        })

    def fetch(
        self,
        url: str,
        respect_robots: bool = True,
        max_redirects: int = 5,
        verify_ssl: bool = True,
    ) -> CrawlResult:
        """Fetches an HTML page with safety validations, domain throttling, and manual redirect inspection."""
        current_url = url
        redirect_count = 0
        start_time = time.time()

        while redirect_count <= max_redirects:
            # 1. SSRF and destination address safety validation
            is_safe, safety_msg = validate_url_safety(current_url)
            if not is_safe:
                return CrawlResult(
                    url=url,
                    final_url=current_url,
                    status="BLOCKED_SSRF",
                    error_reason=safety_msg,
                    response_time_ms=int((time.time() - start_time) * 1000),
                )

            # 2. Check robots.txt if requested
            if respect_robots:
                allowed, robots_msg = self.robots_manager.is_allowed(current_url)
                if not allowed:
                    return CrawlResult(
                        url=url,
                        final_url=current_url,
                        status="ROBOTS_EXCLUDED",
                        error_reason=robots_msg,
                        response_time_ms=int((time.time() - start_time) * 1000),
                    )

            # 3. Apply per-domain throttling
            self._throttle_domain(current_url)

            # 4. Perform fetch with exponential backoff for transient errors
            attempt = 0
            response: Optional[requests.Response] = None
            last_exception: Optional[Exception] = None

            while attempt < self.max_retries:
                attempt += 1
                try:
                    response = self.session.get(
                        current_url,
                        timeout=self.timeout,
                        allow_redirects=False,  # We manually validate each redirect hop!
                        stream=True,
                        verify=verify_ssl,
                    )
                    break
                except requests.exceptions.Timeout as exc:
                    last_exception = exc
                    if attempt < self.max_retries:
                        time.sleep(2 ** attempt)
                    else:
                        return CrawlResult(
                            url=url,
                            final_url=current_url,
                            status="TIMEOUT",
                            error_reason=f"Request timed out after {self.timeout}s ({str(exc)})",
                            response_time_ms=int((time.time() - start_time) * 1000),
                        )
                except requests.exceptions.SSLError as exc:
                    return CrawlResult(
                        url=url,
                        final_url=current_url,
                        status="NETWORK_ERROR",
                        error_reason=f"SSL certificate error: {str(exc)}",
                        response_time_ms=int((time.time() - start_time) * 1000),
                    )
                except requests.exceptions.RequestException as exc:
                    last_exception = exc
                    if attempt < self.max_retries:
                        time.sleep(1.5 ** attempt)
                    else:
                        return CrawlResult(
                            url=url,
                            final_url=current_url,
                            status="NETWORK_ERROR",
                            error_reason=f"Network error: {str(exc)}",
                            response_time_ms=int((time.time() - start_time) * 1000),
                        )

            if response is None:
                return CrawlResult(
                    url=url,
                    final_url=current_url,
                    status="NETWORK_ERROR",
                    error_reason=str(last_exception) if last_exception else "No response received",
                    response_time_ms=int((time.time() - start_time) * 1000),
                )

            # 5. Handle redirects safely
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("Location")
                if not location:
                    return CrawlResult(
                        url=url,
                        final_url=current_url,
                        status="HTTP_ERROR",
                        http_status=response.status_code,
                        error_reason="Redirect status code without Location header",
                        response_time_ms=int((time.time() - start_time) * 1000),
                    )
                # Resolve relative redirect URLs against current URL
                current_url = urljoin(current_url, location)
                redirect_count += 1
                continue

            # 6. Validate HTTP status
            if response.status_code >= 400:
                return CrawlResult(
                    url=url,
                    final_url=current_url,
                    status="HTTP_ERROR",
                    http_status=response.status_code,
                    error_reason=f"HTTP server error status {response.status_code}",
                    response_time_ms=int((time.time() - start_time) * 1000),
                )

            # 7. Validate Content-Type
            content_type_header = response.headers.get("Content-Type", "").lower()
            content_type = content_type_header.split(";")[0].strip()
            if not any(valid_ct in content_type for valid_ct in VALID_CONTENT_TYPES):
                return CrawlResult(
                    url=url,
                    final_url=current_url,
                    status="INVALID_CONTENT_TYPE",
                    http_status=response.status_code,
                    content_type=content_type,
                    error_reason=f"Unsupported Content-Type '{content_type_header}'. Only HTML is supported.",
                    response_time_ms=int((time.time() - start_time) * 1000),
                )

            # 8. Check size & stream content
            body_chunks = []
            downloaded_bytes = 0
            for chunk in response.iter_content(chunk_size=16384):
                if chunk:
                    downloaded_bytes += len(chunk)
                    if downloaded_bytes > MAX_RESPONSE_BYTES:
                        response.close()
                        return CrawlResult(
                            url=url,
                            final_url=current_url,
                            status="TOO_LARGE",
                            http_status=response.status_code,
                            content_type=content_type,
                            content_length=downloaded_bytes,
                            error_reason=f"Response exceeded size limit ({MAX_RESPONSE_BYTES} bytes)",
                            response_time_ms=int((time.time() - start_time) * 1000),
                        )
                    body_chunks.append(chunk)

            raw_bytes = b"".join(body_chunks)
            encoding = response.encoding or "utf-8"
            try:
                html_text = raw_bytes.decode(encoding, errors="replace")
            except Exception:
                html_text = raw_bytes.decode("utf-8", errors="replace")

            content_hash = hashlib.sha256(raw_bytes).hexdigest()
            total_duration_ms = int((time.time() - start_time) * 1000)

            return CrawlResult(
                url=url,
                final_url=current_url,
                status="SUCCESS",
                http_status=response.status_code,
                content_type=content_type,
                content_length=len(raw_bytes),
                content_hash=content_hash,
                html=html_text,
                response_time_ms=total_duration_ms,
            )

        # Reached max redirects
        return CrawlResult(
            url=url,
            final_url=current_url,
            status="NETWORK_ERROR",
            error_reason=f"Exceeded maximum redirects ({max_redirects})",
            response_time_ms=int((time.time() - start_time) * 1000),
        )

    def _throttle_domain(self, url: str) -> None:
        """Enforces a polite delay between requests to the same domain."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            now = time.time()
            last_request = self._last_domain_request.get(domain, 0.0)
            elapsed = now - last_request
            if elapsed < self.default_delay:
                sleep_needed = self.default_delay - elapsed
                time.sleep(sleep_needed)
            self._last_domain_request[domain] = time.time()
        except Exception:
            pass
