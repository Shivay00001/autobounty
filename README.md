# autobounty

**Honest, scoped web security scanner** (rebuilt 2026-09-24 — the previous
version returned hardcoded mock vulnerabilities and has been deleted; inventing
findings is a reputational risk, so this rebuild reports **only what it really
observes**).

## What it actually checks

1. **HTTP security headers** — fetches the site and lists which headers are
   *missing*, e.g. `missing Strict-Transport-Security header (observed)`.
2. **TLS certificate** — real cert from port 443: validity window, issuer,
   days until expiry. Reports expiry only when actually observed.
3. **Open-port scan** — TCP connect to common ports; reports only ports that
   really connected, e.g. `port 443 open (observed: TCP connect succeeded)`.
4. **robots.txt / sitemap.xml** — reports whether they exist (HTTP 200 + size).
   Exposure notes, not vulnerabilities.

Every finding carries an `evidence` object with the raw observation. If a check
can't run, that's reported as an observation — never as a vulnerability.
**Absence of findings is not a claim of safety.**

## Usage

```bash
pip install -r requirements.txt

# CLI (scan only hosts you own or that allow scanning, e.g. scanme.nmap.org)
python cli.py scan example.com
python cli.py scan scanme.nmap.org --json

# API
uvicorn app:app --port 8005
curl -X POST localhost:8005/scan -H 'Content-Type: application/json' \
  -d '{"target": "example.com"}'

# tests (spin up real local HTTP/TLS/TCP servers — no network mocks)
pytest -q
```

## Honest limits

- Surface audit only — not a penetration test, not a vulnerability scanner for
  CVEs, injection, or auth flaws.
- Port scan is deliberately a small common-port set with 1s timeouts; aggressive
  scanning without permission can get you blocked or worse — don't.
- Findings describe observations (`missing X header (observed)`), never
  invented CVEs or severity theater.
- **Intercepted networks:** if every scanned port connects (impossible for a
  real host), the port check reports INCONCLUSIVE instead of fake "open"
  findings; if TLS terminates at a proxy CA, the scanner says so instead of
  reporting the proxy's certificate as the origin's. These guards were verified
  in a sandbox with an intercepting egress proxy.
- TLS trust is evaluated against the local CA store; untrusted-but-present
  certificates are still reported with their real details (parsed via the
  openssl CLI, which must be installed).
