from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import List
import random

app = FastAPI(title="AutoBounty - Bug Bounty Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScanRequest(BaseModel):
    target: str
    scan_type: str = "quick"

class Vulnerability(BaseModel):
    id: str
    severity: str
    title: str
    description: str
    cve: str | None = None

@app.get("/")
async def root():
    return {
        "message": "AutoBounty Bug Bounty Platform API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/scan")
async def start_scan(scan: ScanRequest):
    # Mock scan results
    vuln_templates = [
        ("high", "SQL Injection", "Potential SQL injection vulnerability detected", "CVE-2023-1234"),
        ("medium", "XSS Vulnerability", "Cross-site scripting vulnerability found", "CVE-2023-5678"),
        ("low", "Information Disclosure", "Sensitive information exposed in headers", None),
        ("medium", "CSRF Token Missing", "CSRF protection not implemented", None),
    ]
    
    vulns = []
    for i, (sev, title, desc, cve) in enumerate(random.sample(vuln_templates, 3)):
        vulns.append(Vulnerability(
            id=f"VULN-{i+1:03d}",
            severity=sev,
            title=title,
            description=desc,
            cve=cve
        ))
    
    return {
        "scan_id": f"SCAN-{random.randint(1000, 9999)}",
        "target": scan.target,
        "status": "completed",
        "vulnerabilities": vulns,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/vulnerabilities")
async def get_vulnerabilities():
    return {
        "total": 47,
        "high": 5,
        "medium": 18,
        "low": 24,
        "recent": [
            {"id": "VULN-001", "severity": "high", "title": "Remote Code Execution", "target": "example.com"},
            {"id": "VULN-002", "severity": "medium", "title": "Path Traversal", "target": "test.com"},
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)