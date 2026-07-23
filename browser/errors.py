"""User-friendly browser/navigation error classification."""

from __future__ import annotations


class NavigationError(RuntimeError):
    pass


def classify_browser_error(error: BaseException) -> str:
    text = str(error)
    upper = text.upper()
    if "ERR_NAME_NOT_RESOLVED" in upper or "DNS" in upper:
        return "DNS lookup failed. Check the host name and network connection."
    if "ERR_CERT" in upper or "CERTIFICATE" in upper or "SSL" in upper:
        return "HTTPS certificate error. Enable 'Ignore HTTPS Errors' in Settings."
    if "ERR_CONNECTION_REFUSED" in upper or "CONNECTION REFUSED" in upper:
        return "Connection refused. Check whether the web server and port are available."
    if "TIMEOUT" in upper or "TIMED OUT" in upper:
        return "Connection timed out. Check the network or increase the server response time."
    if "HTTP 404" in upper:
        return "HTTP 404: The requested page was not found."
    if "HTTP 500" in upper:
        return "HTTP 500: The server encountered an internal error."
    return f"Browser error: {text}"
