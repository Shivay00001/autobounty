"""autobounty — honest, scoped web security scanner.

REAL checks only. Every finding cites the actual observed evidence; nothing is
invented. If a check cannot run (no network, connection refused), that is
reported as an observation, never as a vulnerability.

Checks:
  1. HTTP security headers audit   — reports which headers are MISSING (observed)
  2. TLS certificate               — real cert fetched from port 443: validity,
                                     issuer, days until expiry
  3. Open-port scan                — TCP connect to a small set of common ports;
                                     reports only what actually connected
  4. robots.txt / sitemap.xml      — reports whether they exist (HTTP 200) and
                                     their size; exposure notes, not vulns

Severity scale used here: info < low < medium < high. Absence of a finding is
NOT a claim of safety — this is a surface audit, not a penetration test.
"""

import datetime as dt
import os
import socket
import ssl

import httpx

COMMON_PORTS = [21, 22, 23, 25, 80, 443, 3306, 3389, 5432, 6379, 8080, 8443]

SECURITY_HEADERS = {
    "strict-transport-security": (
        "low",
        "missing Strict-Transport-Security header (observed)",
    ),
    "content-security-policy": (
        "low",
        "missing Content-Security-Policy header (observed)",
    ),
    "x-frame-options": ("low", "missing X-Frame-Options header (observed)"),
    "x-content-type-options": ("low", "missing X-Content-Type-Options header (observed)"),
    "referrer-policy": ("info", "missing Referrer-Policy header (observed)"),
    "permissions-policy": ("info", "missing Permissions-Policy header (observed)"),
}


def _now():
    return dt.datetime.now(dt.timezone.utc)


def check_headers(host: str, timeout: float = 15) -> dict:
    """Fetch the site and audit response security headers. Real observations."""
    findings, observed, errors = [], {}, []
    url = None
    resp = None
    for scheme in ("https", "http"):
        url = f"{scheme}://{host}/"
        try:
            resp = httpx.get(url, timeout=timeout, follow_redirects=True)
            break
        except Exception as e:
            errors.append(f"{scheme}: {type(e).__name__}: {e}")
            resp = None
    if resp is None:
        return {
            "check": "security-headers",
            "observations": [f"could not fetch {host} (observed: {'; '.join(errors)})"],
            "findings": [],
        }
    observed = {
        "final_url": str(resp.url),
        "status_code": resp.status_code,
        "headers_present": sorted(resp.headers.keys()),
    }
    lowered = {k.lower(): v for k, v in resp.headers.items()}
    for header, (severity, title) in SECURITY_HEADERS.items():
        if header not in lowered:
            findings.append(
                {
                    "check": "security-headers",
                    "severity": severity,
                    "finding": title,
                    "evidence": {
                        "url": observed["final_url"],
                        "status_code": observed["status_code"],
                        "note": f"header '{header}' not present in response headers",
                    },
                }
            )
        else:
            observed.setdefault("headers_values", {})[header] = lowered[header]
    return {"check": "security-headers", "observations": observed, "findings": findings}


def _parse_cert_time(s: str) -> dt.datetime:
    # e.g. 'Sep 24 00:00:00 2026 GMT' (openssl may emit 'Oct  3' with two spaces)
    import re

    s = re.sub(r"\s+", " ", s.strip())
    return dt.datetime.strptime(s, "%b %d %H:%M:%S %Y %Z").replace(
        tzinfo=dt.timezone.utc
    )


def _cn(dn: str) -> str | None:
    import re

    m = re.search(r"CN\s*=\s*([^,/]+)", dn)
    return m.group(1).strip() if m else None


def _der_info_openssl(der: bytes) -> dict:
    """Extract subject/issuer/validity from DER bytes via the openssl CLI."""
    import re
    import shutil
    import subprocess
    import tempfile

    if not shutil.which("openssl"):
        raise RuntimeError("openssl CLI not available to parse certificate")
    with tempfile.NamedTemporaryFile(suffix=".der", delete=False) as f:
        f.write(der)
        path = f.name
    try:
        out = subprocess.run(
            ["openssl", "x509", "-inform", "der", "-in", path, "-noout",
             "-subject", "-issuer", "-dates"],
            capture_output=True, text=True, timeout=10,
        )
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
    if out.returncode != 0:
        raise RuntimeError(f"openssl parse failed: {out.stderr.strip()}")
    info = {}
    for line in out.stdout.splitlines():
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        info[k.strip()] = v.strip()
    return {
        "subject_CN": _cn(info.get("subject", "")),
        "issuer_CN": _cn(info.get("issuer", "")),
        "not_before": info.get("notBefore", ""),
        "not_after": info.get("notAfter", ""),
    }


def _proxy_tunnel(host: str, port: int, timeout: float):
    """Open a TCP tunnel to host:port via the configured HTTP egress proxy
    (HTTP CONNECT). Raises with the observed proxy response on failure."""
    import re
    from urllib.parse import urlparse

    px = urlparse(os.environ.get("https_proxy") or os.environ.get("http_proxy") or "")
    if not px.hostname:
        raise RuntimeError("no egress proxy configured")
    s = socket.create_connection((px.hostname, px.port or 8080), timeout=timeout)
    try:
        s.sendall(
            f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n"
            f"Proxy-Connection: Keep-Alive\r\n\r\n".encode()
        )
        s.settimeout(timeout)
        resp = b""
        while b"\r\n\r\n" not in resp:
            chunk = s.recv(4096)
            if not chunk:
                break
            resp += chunk
        status = resp.split(b"\r\n", 1)[0].decode("latin1", "replace")
        if not re.search(r"HTTP/\d(\.\d)? 200\b", status):
            raise ConnectionError(f"proxy refused CONNECT: {status!r}")
        return s
    except Exception:
        s.close()
        raise


def _tcp_connect(host: str, port: int, timeout: float):
    """TCP to host:port, via proxy CONNECT tunnel when an egress proxy is set
    (this sandbox intercepts raw sockets, so direct connects are not real)."""
    proxy = os.environ.get("https_proxy") or os.environ.get("http_proxy")
    if proxy:
        try:
            return _proxy_tunnel(host, port, timeout)
        except Exception:
            pass  # fall through to a direct attempt
    return socket.create_connection((host, port), timeout=timeout)


def _fetch_cert(host: str, port: int, timeout: float):
    """Return (info, cipher, tls_version, trusted, trust_error).

    info: dict with subject_CN, issuer_CN, not_before, not_after
    (datetimes strings in getpeercert format)."""
    try:
        ctx = ssl.create_default_context()
        with _tcp_connect(host, port, timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                subject = dict(x[0] for x in cert.get("subject", []))
                issuer = dict(x[0] for x in cert.get("issuer", []))
                return (
                    {
                        "subject_CN": subject.get("commonName"),
                        "issuer_CN": issuer.get("commonName"),
                        "not_before": cert["notBefore"],
                        "not_after": cert["notAfter"],
                    },
                    ssock.cipher(), ssock.version(), True, None,
                )
    except ssl.SSLCertVerificationError as e:
        # untrusted but present: fetch DER without verification and parse it
        # with openssl so we still report real facts about the certificate
        trust_error = getattr(e, "verify_message", None) or str(e)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        try:
            with _tcp_connect(host, port, timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                    der = ssock.getpeercert(binary_form=True)
                    cipher, tls_version = ssock.cipher(), ssock.version()
            if not der:
                raise RuntimeError("peer sent no certificate")
            return _der_info_openssl(der), cipher, tls_version, False, trust_error
        except Exception as e2:
            raise ConnectionError(f"untrusted cert, details unavailable: {e2}")
    except Exception as e:
        raise ConnectionError(f"{type(e).__name__}: {e}")


def check_tls(host: str, port: int = 443, timeout: float = 10) -> dict:
    """Fetch the real TLS certificate from host:443 and report its validity."""
    findings = []
    try:
        info, cipher, tls_version, trusted, trust_error = _fetch_cert(host, port, timeout)
    except ConnectionError as e:
        return {
            "check": "tls-certificate",
            "observations": [f"no TLS handshake on {host}:{port} (observed: {e})"],
            "findings": [],
        }
    not_after = _parse_cert_time(info["not_after"])
    not_before = _parse_cert_time(info["not_before"])
    now = _now()
    days_left = (not_after - now).total_seconds() / 86400
    observed = {
        "host": host,
        "port": port,
        "tls_version": tls_version,
        "cipher": cipher[0] if cipher else None,
        "trusted_by_local_ca_store": trusted,
        "subject_CN": info["subject_CN"],
        "issuer_CN": info["issuer_CN"],
        "not_before": info["not_before"],
        "not_after": info["not_after"],
        "days_until_expiry": round(days_left, 1),
    }
    import re

    issuer_cn = observed["issuer_CN"] or ""
    if re.search(r"proxy|egress|mitm|sandbox|intercept", issuer_cn, re.I):
        # The TLS endpoint is an intercepting proxy, not the origin server:
        # report that fact instead of inventing validity claims about the
        # origin's certificate.
        findings.append(
            {
                "check": "tls-certificate",
                "severity": "info",
                "finding": (
                    "TLS terminates at an intercepting proxy "
                    f"(observed: issuer CN={issuer_cn!r}); the origin server's "
                    "certificate is not visible from this network, so no "
                    "validity findings are reported"
                ),
                "evidence": observed,
            }
        )
        return {"check": "tls-certificate", "observations": observed,
                "findings": findings}
    if not trusted:
        findings.append(
            {
                "check": "tls-certificate",
                "severity": "medium",
                "finding": "TLS certificate is not trusted by the local CA store (observed)",
                "evidence": {**observed, "trust_error": trust_error},
            }
        )
    if days_left < 0:
        findings.append(
            {
                "check": "tls-certificate",
                "severity": "high",
                "finding": "TLS certificate expired (observed)",
                "evidence": observed,
            }
        )
    elif days_left < 30:
        findings.append(
            {
                "check": "tls-certificate",
                "severity": "medium",
                "finding": f"TLS certificate expires in {days_left:.1f} days (observed)",
                "evidence": observed,
            }
        )
    return {"check": "tls-certificate", "observations": observed, "findings": findings}


def check_ports(host: str, ports: list | None = None, timeout: float = 1.0) -> dict:
    """TCP connect scan of common ports. Reports only ports that connected,
    with any service banner observed. If EVERY scanned port connects, the
    network path is intercepting (middlebox/proxy) and the check is reported
    INCONCLUSIVE rather than inventing 'open' findings."""
    ports = ports or COMMON_PORTS
    open_ports, failed, banners = [], [], {}
    for p in ports:
        try:
            s = socket.create_connection((host, p), timeout=timeout)
            try:
                s.settimeout(1.0)
                try:
                    data = s.recv(160)
                except Exception:
                    data = b""
                banners[p] = data.decode("latin1", "replace").strip()
            finally:
                s.close()
            open_ports.append(p)
        except Exception as e:
            failed.append(f"{p}: {type(e).__name__}")
    if len(ports) >= 4 and len(open_ports) == len(ports):
        return {
            "check": "open-ports",
            "observations": {
                "host": host,
                "ports_scanned": ports,
                "verdict": "INCONCLUSIVE",
                "note": (
                    "every scanned port accepted a TCP connection, which is "
                    "not plausible for a real host and indicates an "
                    "intercepting middlebox or egress proxy on the network "
                    "path. No port findings are reported; run this check from "
                    "an uninterrupted network for real results."
                ),
            },
            "findings": [],
        }
    findings = [
        {
            "check": "open-ports",
            "severity": "info",
            "finding": f"port {p} reachable (observed: TCP connect to {host}:{p} succeeded"
                       + (f", banner: {banners[p][:80]!r}" if banners.get(p) else ", no banner")
                       + ")",
            "evidence": {"host": host, "port": p, "banner": banners.get(p, "")},
        }
        for p in open_ports
    ]
    return {
        "check": "open-ports",
        "observations": {
            "host": host,
            "ports_scanned": ports,
            "open": open_ports,
            "closed_or_filtered": [int(f.split(":")[0]) for f in failed],
        },
        "findings": findings,
    }


def check_robots(host: str, timeout: float = 15) -> dict:
    """Report whether robots.txt / sitemap.xml exist. Exposure notes only."""
    findings = []
    for scheme in ("https", "http"):
        base = f"{scheme}://{host}"
        breakable = False
        for path, label in (("/robots.txt", "robots.txt"), ("/sitemap.xml", "sitemap.xml")):
            try:
                r = httpx.get(base + path, timeout=timeout, follow_redirects=True)
            except Exception as e:
                findings.append(
                    {
                        "check": "crawl-files",
                        "severity": "info",
                        "finding": f"could not fetch {label} (observed: {type(e).__name__})",
                        "evidence": {"url": base + path},
                    }
                )
                continue
            if r.status_code == 200 and r.text.strip():
                disallows = (
                    sum(1 for l in r.text.splitlines()
                        if l.strip().lower().startswith("disallow:"))
                    if label == "robots.txt" else 0
                )
                findings.append(
                    {
                        "check": "crawl-files",
                        "severity": "info",
                        "finding": f"{label} exposed (observed: HTTP 200, "
                                   f"{len(r.content)} bytes"
                                   + (f", {disallows} Disallow rules" if label == "robots.txt" else "")
                                   + ")",
                        "evidence": {"url": str(r.url), "status_code": 200,
                                     "bytes": len(r.content)},
                    }
                )
                breakable = True
        if breakable:
            break
    return {"check": "crawl-files", "observations": {}, "findings": findings}


def scan(host: str) -> dict:
    """Run all checks against a host. Scan only hosts you own or that explicitly
    allow scanning (e.g. scanme.nmap.org)."""
    host = host.strip().lower().split("/")[0].split(":")[0]
    results = [
        check_headers(host),
        check_tls(host),
        check_ports(host),
        check_robots(host),
    ]
    findings = [f for r in results for f in r["findings"]]
    return {
        "target": host,
        "scanned_at": _now().isoformat(),
        "summary": {
            "checks_run": len(results),
            "findings": len(findings),
            "by_severity": {
                sev: sum(1 for f in findings if f["severity"] == sev)
                for sev in ("info", "low", "medium", "high")
            },
        },
        "checks": results,
    }
