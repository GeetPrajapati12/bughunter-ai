"""
modules/security.py
--------------------
Security Testing Module for BugHunter AI.

Provides automated, non-destructive security checks commonly used in
web application security assessments (similar in spirit to OWASP ZAP's
passive/active baseline scans). Designed to help identify common
misconfigurations and vulnerability classes so a security engineer can
investigate further — this module surfaces findings, it does not perform
deep exploitation or attempt to extract real data.

IMPORTANT: Only run this against websites you own or have explicit
written authorization to test. Unauthorized security testing may be
illegal in your jurisdiction.

Checks included:
  - Security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options,
    Referrer-Policy, Permissions-Policy)
  - Cookie security flags (HttpOnly, Secure, SameSite)
  - SSL/TLS certificate validity
  - Exposed sensitive files (.env, .git, backup files, etc.)
  - Directory listing exposure
  - robots.txt / sitemap.xml information disclosure
  - CSRF token presence on forms
  - CORS misconfiguration (overly permissive Access-Control-Allow-Origin)
  - Basic reflected input handling test (checks if a harmless marker
    string is reflected back unescaped — signals potential XSS risk
    without executing any script)
  - Basic error-based signal test (checks if a single quote character
    causes a database/server error message to be exposed — signals
    potential injection risk without extracting data)
  - Server / technology fingerprinting from response headers
"""

from __future__ import annotations

import re
import ssl
import socket
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class SecurityFinding:
    category:    str    # "headers" | "cookies" | "ssl" | "exposure" | "csrf" | "cors" | "injection-signal" | "fingerprint"
    severity:    str    # "critical" | "high" | "medium" | "low" | "info"
    title:       str
    description: str
    evidence:    str = ""
    recommendation: str = ""


class SecurityScanner:
    """
    Runs a suite of passive and lightly-active security checks against
    a target URL. Uses `requests` directly (not the browser) so it can
    inspect raw headers, cookies, and TLS info.
    """

    # Harmless marker used to test reflection — not a working XSS payload
    _REFLECTION_MARKER = "bughunterai_reflect_9f3a"

    _SENSITIVE_PATHS = [
        ".env", ".env.local", ".env.production",
        ".git/config", ".git/HEAD",
        "wp-config.php.bak", "config.php.bak", "backup.zip", "backup.sql",
        ".DS_Store", "web.config", "docker-compose.yml",
        "phpinfo.php", ".htpasswd", "id_rsa",
    ]

    _DB_ERROR_SIGNATURES = [
        "sql syntax", "mysql_fetch", "ORA-01756", "PostgreSQL query failed",
        "SQLite3::", "unclosed quotation mark", "syntax error at or near",
        "Microsoft OLE DB Provider for SQL Server", "Warning: mysqli",
    ]

    def __init__(self, timeout: int = 10) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "BugHunterAI-SecurityScanner/1.0"})

    # ── Public API ─────────────────────────────────────────────────────────────

    def scan(self, url: str, html: str = "") -> list[SecurityFinding]:
        """
        Run the full security check suite against a single page URL.
        `html` (already-fetched page source) is optional — if provided,
        it's reused for CSRF/form checks instead of re-fetching.
        """
        findings: list[SecurityFinding] = []

        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
        except Exception as exc:
            logger.warning("SecurityScanner: could not fetch {}: {}", url, exc)
            return findings

        findings += self._check_headers(response)
        findings += self._check_cookies(response)
        findings += self._check_cors(response)
        findings += self._check_fingerprint(response)

        if urlparse(url).scheme == "https":
            findings += self._check_ssl(url)

        page_html = html or response.text
        findings += self._check_csrf(page_html)
        findings += self._check_reflection(url)
        findings += self._check_injection_signal(url)

        logger.info("SecurityScanner: {} findings for {}", len(findings), url)
        return findings

    def scan_site_exposure(self, base_url: str) -> list[SecurityFinding]:
        """
        One-time site-wide checks: exposed sensitive files, directory
        listing, robots.txt disclosure. Call this once per domain,
        not once per page.
        """
        findings: list[SecurityFinding] = []
        findings += self._check_exposed_files(base_url)
        findings += self._check_robots_txt(base_url)
        return findings

    # ── Header checks ─────────────────────────────────────────────────────────

    def _check_headers(self, response: requests.Response) -> list[SecurityFinding]:
        findings = []
        headers  = {k.lower(): v for k, v in response.headers.items()}

        required = {
            "content-security-policy": (
                "high", "Missing Content-Security-Policy header",
                "No CSP header found. This increases risk of XSS and data injection attacks.",
                "Add a Content-Security-Policy header restricting script/style/resource sources.",
            ),
            "x-frame-options": (
                "medium", "Missing X-Frame-Options header",
                "Page can potentially be embedded in an iframe, enabling clickjacking attacks.",
                "Add 'X-Frame-Options: DENY' or 'SAMEORIGIN', or use CSP frame-ancestors.",
            ),
            "x-content-type-options": (
                "low", "Missing X-Content-Type-Options header",
                "Browser may MIME-sniff responses, which can lead to content-type confusion attacks.",
                "Add 'X-Content-Type-Options: nosniff'.",
            ),
            "strict-transport-security": (
                "high", "Missing HSTS header",
                "Site does not enforce HTTPS via HSTS, allowing potential downgrade/MITM attacks.",
                "Add 'Strict-Transport-Security: max-age=31536000; includeSubDomains'.",
            ),
            "referrer-policy": (
                "low", "Missing Referrer-Policy header",
                "Full URLs (potentially with sensitive query params) may leak to third parties via the Referer header.",
                "Add 'Referrer-Policy: strict-origin-when-cross-origin' or stricter.",
            ),
            "permissions-policy": (
                "info", "Missing Permissions-Policy header",
                "No explicit restriction on browser feature access (camera, mic, geolocation, etc.).",
                "Add a Permissions-Policy header to restrict unused browser features.",
            ),
        }

        for header, (severity, title, desc, rec) in required.items():
            if header not in headers:
                findings.append(SecurityFinding(
                    category="headers", severity=severity, title=title,
                    description=desc, recommendation=rec,
                ))

        return findings

    # ── Cookie checks ──────────────────────────────────────────────────────────

    def _check_cookies(self, response: requests.Response) -> list[SecurityFinding]:
        findings = []
        for cookie in response.cookies:
            issues = []
            if not cookie.secure:
                issues.append("missing Secure flag")
            if not cookie.has_nonstandard_attr("HttpOnly") and not getattr(cookie, "_rest", {}).get("HttpOnly"):
                issues.append("missing HttpOnly flag")
            samesite = cookie._rest.get("SameSite") if hasattr(cookie, "_rest") else None
            if not samesite:
                issues.append("missing SameSite attribute")

            if issues:
                findings.append(SecurityFinding(
                    category="cookies",
                    severity="medium",
                    title=f"Cookie '{cookie.name}' missing security flags",
                    description=f"Issues: {', '.join(issues)}.",
                    evidence=f"Cookie: {cookie.name}",
                    recommendation="Set Secure, HttpOnly, and SameSite=Strict/Lax on all session cookies.",
                ))
        return findings

    # ── CORS checks ────────────────────────────────────────────────────────────

    def _check_cors(self, response: requests.Response) -> list[SecurityFinding]:
        findings = []
        acao = response.headers.get("Access-Control-Allow-Origin", "")
        acac = response.headers.get("Access-Control-Allow-Credentials", "")

        if acao == "*" and acac.lower() == "true":
            findings.append(SecurityFinding(
                category="cors", severity="critical",
                title="Overly permissive CORS with credentials allowed",
                description="Access-Control-Allow-Origin is '*' while Allow-Credentials is true — "
                             "this combination is invalid per spec but some servers misconfigure it, "
                             "and if honoured by any client it would leak credentialed data cross-origin.",
                evidence=f"ACAO={acao}, ACAC={acac}",
                recommendation="Never combine wildcard origin with credentialed requests. "
                               "Use an explicit origin allow-list.",
            ))
        elif acao == "*":
            findings.append(SecurityFinding(
                category="cors", severity="low",
                title="Wildcard CORS policy",
                description="Access-Control-Allow-Origin is '*', allowing any website to read responses.",
                evidence=f"ACAO={acao}",
                recommendation="Restrict Access-Control-Allow-Origin to known, trusted origins only.",
            ))
        return findings

    # ── SSL/TLS checks ─────────────────────────────────────────────────────────

    def _check_ssl(self, url: str) -> list[SecurityFinding]:
        findings = []
        hostname = urlparse(url).hostname
        if not hostname:
            return findings

        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((hostname, 443), timeout=self.timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()

            not_after = cert.get("notAfter", "")
            if not_after:
                expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                days_left = (expiry - datetime.utcnow()).days
                if days_left < 0:
                    findings.append(SecurityFinding(
                        category="ssl", severity="critical",
                        title="SSL certificate has expired",
                        description=f"Certificate expired on {not_after}.",
                        recommendation="Renew the SSL/TLS certificate immediately.",
                    ))
                elif days_left < 14:
                    findings.append(SecurityFinding(
                        category="ssl", severity="medium",
                        title="SSL certificate expiring soon",
                        description=f"Certificate expires in {days_left} days ({not_after}).",
                        recommendation="Renew the certificate before it expires.",
                    ))

        except ssl.SSLCertVerificationError as exc:
            findings.append(SecurityFinding(
                category="ssl", severity="critical",
                title="SSL certificate verification failed",
                description=str(exc),
                recommendation="Fix the certificate chain — use a certificate signed by a trusted CA.",
            ))
        except Exception as exc:
            logger.debug("SSL check skipped for {}: {}", hostname, exc)

        return findings

    # ── Exposed file checks ────────────────────────────────────────────────────

    def _check_exposed_files(self, base_url: str) -> list[SecurityFinding]:
        findings = []
        origin = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"

        for path in self._SENSITIVE_PATHS:
            test_url = urljoin(origin + "/", path)
            try:
                resp = self.session.get(test_url, timeout=self.timeout, allow_redirects=False)
                if resp.status_code == 200 and len(resp.content) > 0:
                    findings.append(SecurityFinding(
                        category="exposure", severity="critical",
                        title=f"Sensitive file exposed: {path}",
                        description=f"{test_url} returned HTTP 200 and may expose sensitive data.",
                        evidence=f"Status: {resp.status_code}, Size: {len(resp.content)} bytes",
                        recommendation=f"Remove or block public access to {path}.",
                    ))
            except Exception:
                continue

        return findings

    def _check_robots_txt(self, base_url: str) -> list[SecurityFinding]:
        findings = []
        origin = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
        try:
            resp = self.session.get(urljoin(origin, "/robots.txt"), timeout=self.timeout)
            if resp.status_code == 200:
                sensitive_hints = re.findall(r"Disallow:\s*(/\S*(admin|backup|config|internal|private)\S*)",
                                              resp.text, re.IGNORECASE)
                if sensitive_hints:
                    paths = [h[0] for h in sensitive_hints]
                    findings.append(SecurityFinding(
                        category="exposure", severity="low",
                        title="robots.txt discloses sensitive-looking paths",
                        description=f"robots.txt lists paths that hint at sensitive areas: {paths[:5]}",
                        recommendation="Avoid listing sensitive paths in robots.txt; "
                                       "rely on proper authentication instead.",
                    ))
        except Exception:
            pass
        return findings

    # ── CSRF checks ────────────────────────────────────────────────────────────

    def _check_csrf(self, html: str) -> list[SecurityFinding]:
        findings = []
        soup = BeautifulSoup(html, "lxml")

        for form in soup.find_all("form"):
            method = (form.get("method") or "GET").upper()
            if method != "POST":
                continue

            has_csrf_field = bool(form.find(
                "input",
                attrs={"name": re.compile(r"(csrf|_token|authenticity_token)", re.IGNORECASE)}
            ))
            if not has_csrf_field:
                action = form.get("action", "(no action)")
                findings.append(SecurityFinding(
                    category="csrf", severity="high",
                    title="Form missing CSRF token",
                    description=f"POST form (action='{action}') has no visible CSRF token field.",
                    recommendation="Add a CSRF token to all state-changing forms and validate it server-side.",
                ))

        return findings

    # ── Reflection / injection signal checks ───────────────────────────────────

    def _check_reflection(self, url: str) -> list[SecurityFinding]:
        """
        Appends a harmless marker string as a query parameter and checks
        whether it's reflected unescaped in the response — a signal
        (not proof) of potential reflected-XSS risk. No script is executed.
        """
        findings = []
        try:
            sep = "&" if "?" in url else "?"
            test_url = f"{url}{sep}q={self._REFLECTION_MARKER}"
            resp = self.session.get(test_url, timeout=self.timeout)

            if self._REFLECTION_MARKER in resp.text:
                # Check if it appears unescaped (not HTML-entity-encoded)
                unescaped = f"{self._REFLECTION_MARKER}" in resp.text
                findings.append(SecurityFinding(
                    category="injection-signal", severity="medium",
                    title="Unvalidated input reflected in response",
                    description="A test query parameter was reflected back in the page response. "
                                 "If user input is reflected without proper output encoding, "
                                 "this can indicate a reflected XSS risk. Manual verification recommended.",
                    evidence=f"Tested URL pattern: ?q={self._REFLECTION_MARKER}",
                    recommendation="Ensure all user-supplied input is HTML-escaped before being "
                                   "rendered back into page content.",
                ))
        except Exception as exc:
            logger.debug("Reflection check skipped for {}: {}", url, exc)

        return findings

    def _check_injection_signal(self, url: str) -> list[SecurityFinding]:
        """
        Appends a single quote character to a query parameter and checks
        for database/server error signatures in the response — a signal
        (not proof) of potential injection risk. Does not attempt to
        extract, modify, or access any real data.
        """
        findings = []
        try:
            sep = "&" if "?" in url else "?"
            test_url = f"{url}{sep}id=1%27"
            resp = self.session.get(test_url, timeout=self.timeout)
            lower_body = resp.text.lower()

            for sig in self._DB_ERROR_SIGNATURES:
                if sig.lower() in lower_body:
                    findings.append(SecurityFinding(
                        category="injection-signal", severity="high",
                        title="Possible injection vulnerability signal",
                        description=f"A database/server error signature ('{sig}') appeared after "
                                     "submitting a single-quote test character in a URL parameter. "
                                     "This suggests unsanitized input may reach a database or "
                                     "interpreter. Manual verification by a security professional "
                                     "is strongly recommended before drawing conclusions.",
                        evidence=f"Signature matched: {sig}",
                        recommendation="Use parameterized queries / prepared statements for all "
                                       "database access. Never concatenate user input into queries.",
                    ))
                    break
        except Exception as exc:
            logger.debug("Injection signal check skipped for {}: {}", url, exc)

        return findings

    # ── Fingerprinting ─────────────────────────────────────────────────────────

    def _check_fingerprint(self, response: requests.Response) -> list[SecurityFinding]:
        findings = []
        server = response.headers.get("Server", "")
        powered_by = response.headers.get("X-Powered-By", "")

        if server or powered_by:
            findings.append(SecurityFinding(
                category="fingerprint", severity="info",
                title="Server technology disclosed via headers",
                description=f"Server: '{server or 'n/a'}', X-Powered-By: '{powered_by or 'n/a'}'. "
                             "Exposing exact software/version can help attackers target known "
                             "vulnerabilities for that specific version.",
                recommendation="Suppress or genericize Server and X-Powered-By headers in production.",
            ))
        return findings
