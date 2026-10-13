import logging
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from typing import Dict, Tuple
import requests

logger = logging.getLogger(__name__)


class RobotsPolicyManager:
    """Fetches, parses, and caches robots.txt per domain."""

    def __init__(self, user_agent: str, timeout: int = 10):
        self.user_agent = user_agent
        self.timeout = timeout
        self._cache: Dict[str, RobotFileParser] = {}

    def is_allowed(self, url: str) -> Tuple[bool, str]:
        """Checks if the URL is permitted by the domain's robots.txt.

        Returns:
            (is_allowed, reason)
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False, "Invalid URL structure"

            domain_root = f"{parsed.scheme}://{parsed.netloc}"

            if domain_root not in self._cache:
                self._load_robots(domain_root)

            rp = self._cache.get(domain_root)
            if rp is None:
                # If robots.txt could not be fetched or 404, default is permitted
                return True, "No robots.txt restriction found"

            allowed = rp.can_fetch(self.user_agent, url)
            if allowed:
                return True, "Permitted by robots.txt"
            else:
                return False, f"URL path disallowed by robots.txt for User-Agent '{self.user_agent}'"

        except Exception as exc:
            logger.warning(f"Error checking robots.txt for {url}: {exc}")
            # If robots parsing fails, default to allowing with warning
            return True, f"Robots check bypassed due to error: {str(exc)}"

    def _load_robots(self, domain_root: str) -> None:
        """Fetches robots.txt for domain root and populates cache."""
        robots_url = urljoin(domain_root, "/robots.txt")
        rp = RobotFileParser()
        try:
            headers = {"User-Agent": self.user_agent}
            resp = requests.get(robots_url, headers=headers, timeout=self.timeout)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
                self._cache[domain_root] = rp
                logger.info(f"Loaded and parsed robots.txt for {domain_root}")
            else:
                # HTTP 404 or other non-200 means no explicit restrictions
                self._cache[domain_root] = None
        except Exception as exc:
            logger.debug(f"Could not load robots.txt for {domain_root}: {exc}")
            self._cache[domain_root] = None
