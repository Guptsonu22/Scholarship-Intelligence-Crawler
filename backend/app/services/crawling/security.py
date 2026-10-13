import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple

# Restricted IP networks for SSRF prevention
RESTRICTED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),          # Current network
    ipaddress.ip_network("10.0.0.0/8"),         # Private RFC 1918
    ipaddress.ip_network("100.64.0.0/10"),      # Carrier-grade NAT
    ipaddress.ip_network("127.0.0.0/8"),        # Loopback
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local / AWS & Cloud Metadata
    ipaddress.ip_network("172.16.0.0/12"),      # Private RFC 1918
    ipaddress.ip_network("192.0.0.0/24"),       # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),       # TEST-NET-1
    ipaddress.ip_network("192.168.0.0/16"),     # Private RFC 1918
    ipaddress.ip_network("198.18.0.0/15"),      # Network benchmark tests
    ipaddress.ip_network("198.51.100.0/24"),    # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),     # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),        # Multicast
    ipaddress.ip_network("240.0.0.0/4"),        # Reserved / Future use
    ipaddress.ip_network("255.255.255.255/32"), # Broadcast
    # IPv6 ranges
    ipaddress.ip_network("::1/128"),            # IPv6 loopback
    ipaddress.ip_network("::/128"),             # IPv6 unspecified
    ipaddress.ip_network("fc00::/7"),           # Unique local address
    ipaddress.ip_network("fe80::/10"),          # Link-local unicast
    ipaddress.ip_network("ff00::/8"),           # Multicast
]

# Prohibited cloud metadata hostnames
PROHIBITED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "169.254.169.254",
    "instance-data",
}


def validate_url_safety(url: str) -> Tuple[bool, str]:
    """Validates that a URL is safe to fetch and does not point to restricted IP ranges (SSRF protection).

    Returns:
        (is_safe, reason_or_error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL is empty or invalid type"

    try:
        parsed = urlparse(url.strip())
    except Exception as exc:
        return False, f"URL parse failure: {str(exc)}"

    # 1. Enforce scheme: only http and https
    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Unsupported scheme '{parsed.scheme}'. Only http and https are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL does not contain a valid hostname."

    hostname_lower = hostname.lower()

    # 2. Block known dangerous / metadata hostnames
    if hostname_lower in PROHIBITED_HOSTNAMES:
        return False, f"Access to restricted host '{hostname}' is blocked."

    if hostname_lower.endswith(".internal") or hostname_lower.endswith(".local"):
        return False, f"Access to private domain '{hostname}' is blocked."

    # 3. Resolve hostname and check IP addresses against restricted networks
    try:
        # Check if hostname is already a direct IP address
        try:
            ip_obj = ipaddress.ip_address(hostname_lower)
            for net in RESTRICTED_NETWORKS:
                if ip_obj in net:
                    return False, f"Direct IP '{hostname}' belongs to restricted network {net}."
            return True, "Safe direct IP address"
        except ValueError:
            # Hostname is a domain name, resolve via DNS
            pass

        addr_info = socket.getaddrinfo(hostname, None)
        if not addr_info:
            return False, f"Unable to resolve host '{hostname}'"

        for entry in addr_info:
            sockaddr = entry[4]
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)

            for net in RESTRICTED_NETWORKS:
                if ip_obj in net:
                    return False, f"Host '{hostname}' resolves to restricted IP {ip_str} in {net}."

    except socket.gaierror as exc:
        # DNS lookup failure (e.g., offline or non-existent host)
        return False, f"DNS resolution error for '{hostname}': {str(exc)}"
    except Exception as exc:
        return False, f"Security validation exception: {str(exc)}"

    return True, "URL is safe"
