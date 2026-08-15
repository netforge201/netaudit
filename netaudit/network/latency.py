"""HTTP(S) reachability/latency checks using httpx."""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx


@dataclass
class HttpCheckResult:
    url: str
    reachable: bool
    status_code: int | None
    latency_ms: float | None
    error: str | None = None


def check_http(url: str, timeout: float = 5.0) -> HttpCheckResult:
    """Perform an HTTP(S) GET request and measure response latency."""
    start = time.monotonic()
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, verify=True) as client:
            response = client.get(url)
        elapsed_ms = round((time.monotonic() - start) * 1000, 2)
        return HttpCheckResult(url, True, response.status_code, elapsed_ms)
    except httpx.ConnectTimeout:
        return HttpCheckResult(url, False, None, None, "Connection timed out")
    except httpx.ConnectError as exc:
        return HttpCheckResult(url, False, None, None, f"Connection failed: {exc}")
    except httpx.HTTPError as exc:
        return HttpCheckResult(url, False, None, None, str(exc))
