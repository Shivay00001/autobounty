"""
app/services/report_builder.py
Report generation service with markdown templates
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.models.evidence import Evidence
from app.models.target import Target

logger = logging.getLogger(__name__)

class ReportBuilder:
    def __init__(self):
        self.templates = {
            "missing_headers": self._template_missing_headers,
            "exposed_config": self._template_exposed_config,
            "default": self._template_default
        }
    
    def build_markdown_report(self, db: Session, finding_id: int) -> str:
        finding = db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            raise ValueError(f"Finding {finding_id} not found")
        
        target = db.query(Target).filter(Target.id == finding.target_id).first()
        evidence_list = db.query(Evidence).filter(Evidence.finding_id == finding_id).all()
        
        template_key = self._determine_template(finding)
        template_func = self.templates.get(template_key, self.templates["default"])
        
        return template_func(finding, target, evidence_list)
    
    def build_target_summary_report(self, db: Session, target_id: int) -> str:
        target = db.query(Target).filter(Target.id == target_id).first()
        if not target:
            raise ValueError(f"Target {target_id} not found")
        
        findings = db.query(Finding).filter(
            Finding.target_id == target_id,
            Finding.status.in_(["open", "triaged"])
        ).all()
        
        report = f"# Security Assessment Summary: {target.name}\n\n"
        report += f"**Target URL:** {target.url}\n"
        report += f"**Assessment Date:** {datetime.now().strftime('%Y-%m-%d')}\n"
        report += f"**Total Findings:** {len(findings)}\n\n"
        
        severity_counts = {}
        for finding in findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
        
        report += "## Findings Summary\n\n"
        for severity in ["critical", "high", "medium", "low", "info"]:
            count = severity_counts.get(severity, 0)
            if count > 0:
                report += f"- **{severity.upper()}:** {count}\n"
        
        report += "\n## Detailed Findings\n\n"
        
        for idx, finding in enumerate(findings, 1):
            report += f"### {idx}. {finding.title}\n\n"
            report += f"**Severity:** {finding.severity.upper()}\n"
            report += f"**Status:** {finding.status}\n\n"
            if finding.description:
                report += f"{finding.description}\n\n"
            report += "---\n\n"
        
        return report
    
    def _determine_template(self, finding: Finding) -> str:
        title_lower = finding.title.lower()
        
        if "header" in title_lower or "hsts" in title_lower or "csp" in title_lower:
            return "missing_headers"
        elif "exposed" in title_lower or "disclosure" in title_lower:
            return "exposed_config"
        else:
            return "default"
    
    def _template_missing_headers(self, finding: Finding, target: Target, evidence: List[Evidence]) -> str:
        report = f"# {finding.title}\n\n"
        report += f"## Summary\n\n"
        report += f"The target application at `{target.url}` is missing critical security headers "
        report += f"that protect against common web vulnerabilities.\n\n"
        
        report += f"## Target Information\n\n"
        report += f"- **Program:** {target.name}\n"
        report += f"- **URL:** {target.url}\n"
        report += f"- **Severity:** {finding.severity.upper()}\n\n"
        
        report += f"## Vulnerability Details\n\n"
        report += f"{finding.description or 'Security headers are HTTP response headers that enhance application security.'}\n\n"
        
        report += f"## Impact\n\n"
        report += f"Missing security headers can lead to:\n\n"
        report += f"- Clickjacking attacks (missing X-Frame-Options)\n"
        report += f"- MIME-type sniffing attacks (missing X-Content-Type-Options)\n"
        report += f"- Man-in-the-middle attacks (missing HSTS)\n"
        report += f"- Cross-site scripting (inadequate CSP)\n\n"
        
        report += f"## Steps to Reproduce\n\n"
        report += f"1. Send an HTTP request to `{target.url}`\n"
        report += f"2. Inspect the response headers\n"
        report += f"3. Observe the missing security headers\n\n"
        
        report += f"## Evidence\n\n"
        if evidence:
            for ev in evidence:
                if ev.file_path:
                    report += f"- [{ev.type}]({ev.file_path})\n"
        else:
            report += f"HTTP response headers captured during assessment.\n\n"
        
        report += f"## Remediation\n\n"
        report += f"Add the following security headers to all HTTP responses:\n\n"
        report += f"```\n"
        report += f"Strict-Transport-Security: max-age=31536000; includeSubDomains\n"
        report += f"Content-Security-Policy: default-src 'self'\n"
        report += f"X-Frame-Options: DENY\n"
        report += f"X-Content-Type-Options: nosniff\n"
        report += f"Referrer-Policy: strict-origin-when-cross-origin\n"
        report += f"```\n\n"
        
        return report
    
    def _template_exposed_config(self, finding: Finding, target: Target, evidence: List[Evidence]) -> str:
        report = f"# {finding.title}\n\n"
        report += f"## Summary\n\n"
        report += f"Sensitive information is being exposed through server response headers or accessible files.\n\n"
        
        report += f"## Target Information\n\n"
        report += f"- **Program:** {target.name}\n"
        report += f"- **URL:** {target.url}\n"
        report += f"- **Severity:** {finding.severity.upper()}\n\n"
        
        report += f"## Vulnerability Details\n\n"
        report += f"{finding.description or 'The application exposes technical implementation details.'}\n\n"
        
        report += f"## Impact\n\n"
        report += f"Information disclosure can:\n\n"
        report += f"- Aid attackers in reconnaissance\n"
        report += f"- Reveal technology stack and versions\n"
        report += f"- Expose potential attack vectors\n"
        report += f"- Facilitate targeted exploits\n\n"
        
        report += f"## Steps to Reproduce\n\n"
        report += f"1. Navigate to `{target.url}`\n"
        report += f"2. Inspect HTTP response headers\n"
        report += f"3. Observe disclosed information\n\n"
        
        report += f"## Evidence\n\n"
        if evidence:
            for ev in evidence:
                if ev.file_path:
                    report += f"- [{ev.type}]({ev.file_path})\n"
        
        report += f"\n## Remediation\n\n"
        report += f"- Remove or mask server identification headers\n"
        report += f"- Disable verbose error messages in production\n"
        report += f"- Implement proper access controls\n\n"
        
        return report
    
    def _template_default(self, finding: Finding, target: Target, evidence: List[Evidence]) -> str:
        report = f"# {finding.title}\n\n"
        report += f"## Summary\n\n"
        report += f"A security issue has been identified in {target.name}.\n\n"
        
        report += f"## Target Information\n\n"
        report += f"- **Program:** {target.name}\n"
        report += f"- **URL:** {target.url}\n"
        report += f"- **Severity:** {finding.severity.upper()}\n\n"
        
        report += f"## Description\n\n"
        report += f"{finding.description or 'Security finding details.'}\n\n"
        
        report += f"## Steps to Reproduce\n\n"
        report += f"1. Access {target.url}\n"
        report += f"2. Follow the specific steps that reproduce the issue\n"
        report += f"3. Observe the security impact\n\n"
        
        report += f"## Evidence\n\n"
        if evidence:
            for ev in evidence:
                if ev.file_path:
                    report += f"- [{ev.type}]({ev.file_path})\n"
        
        report += f"\n## Recommended Fix\n\n"
        report += f"Address the identified security issue according to best practices.\n\n"
        
        return report

report_builder = ReportBuilder()


"""
app/services/h1_client.py
HackerOne API client for report submission
"""
import requests
import logging
from typing import Dict, Any, Optional

from app.core.config import settings
from app.models.target import Target

logger = logging.getLogger(__name__)

class HackerOneClient:
    def __init__(self):
        self.base_url = settings.HACKERONE_API_URL
        self.api_token = settings.HACKERONE_API_TOKEN
        self.team_handle = settings.HACKERONE_TEAM_HANDLE
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def _get_auth(self) -> tuple:
        if not self.api_token:
            raise ValueError("HackerOne API token not configured")
        return (self.api_token, "")
    
    def submit_report(
        self,
        title: str,
        markdown: str,
        severity: str,
        target: Target,
        weakness_id: Optional[int] = None
    ) -> Dict[str, Any]:
        if not self.api_token or not self.team_handle:
            logger.warning("HackerOne not configured, simulating submission")
            return {
                "status": "simulated",
                "message": "HackerOne API not configured. Report was not actually submitted.",
                "report_id": None
            }
        
        url = f"{self.base_url}/reports"
        
        severity_rating_map = {
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "info": "none"
        }
        
        payload = {
            "data": {
                "type": "report",
                "attributes": {
                    "team_handle": self.team_handle,
                    "title": title,
                    "vulnerability_information": markdown,
                    "severity_rating": severity_rating_map.get(severity.lower(), "medium")
                }
            }
        }
        
        if weakness_id:
            payload["data"]["attributes"]["weakness_id"] = weakness_id
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                auth=self._get_auth(),
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                report_id = data.get("data", {}).get("id")
                logger.info(f"Report submitted successfully: {report_id}")
                return {
                    "status": "success",
                    "report_id": report_id,
                    "response": data
                }
            else:
                logger.error(f"Report submission failed: {response.status_code} - {response.text}")
                return {
                    "status": "error",
                    "message": response.text,
                    "status_code": response.status_code
                }
        
        except Exception as e:
            logger.error(f"Report submission exception: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_program_info(self, handle: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/programs/{handle}"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                auth=self._get_auth(),
                timeout=15
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch program info: {response.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"Program info fetch failed: {e}")
            return None

h1_client = HackerOneClient()