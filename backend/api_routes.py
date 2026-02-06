"""
app/api/routes_targets.py
Target management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.models.target import Target
from app.schemas.target import TargetCreate, TargetUpdate, TargetResponse

router = APIRouter()

@router.get("/", response_model=List[TargetResponse])
def list_targets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    targets = db.query(Target).offset(skip).limit(limit).all()
    return targets

@router.get("/{target_id}", response_model=TargetResponse)
def get_target(target_id: int, db: Session = Depends(get_db)):
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target

@router.post("/", response_model=TargetResponse)
def create_target(target: TargetCreate, db: Session = Depends(get_db)):
    existing = db.query(Target).filter(Target.handle == target.handle).first()
    if existing:
        raise HTTPException(status_code=400, detail="Target with this handle already exists")
    
    db_target = Target(**target.dict())
    db.add(db_target)
    db.commit()
    db.refresh(db_target)
    return db_target

@router.put("/{target_id}", response_model=TargetResponse)
def update_target(target_id: int, target: TargetUpdate, db: Session = Depends(get_db)):
    db_target = db.query(Target).filter(Target.id == target_id).first()
    if not db_target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    update_data = target.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_target, field, value)
    
    db.commit()
    db.refresh(db_target)
    return db_target

@router.delete("/{target_id}")
def delete_target(target_id: int, db: Session = Depends(get_db)):
    db_target = db.query(Target).filter(Target.id == target_id).first()
    if not db_target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    db.delete(db_target)
    db.commit()
    return {"message": "Target deleted successfully"}


"""
app/api/routes_findings.py
Finding management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.db import get_db
from app.models.finding import Finding
from app.schemas.finding import FindingCreate, FindingUpdate, FindingResponse

router = APIRouter()

@router.get("/", response_model=List[FindingResponse])
def list_findings(
    target_id: Optional[int] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Finding)
    
    if target_id:
        query = query.filter(Finding.target_id == target_id)
    if severity:
        query = query.filter(Finding.severity == severity)
    if status:
        query = query.filter(Finding.status == status)
    
    findings = query.offset(skip).limit(limit).all()
    return findings

@router.get("/{finding_id}", response_model=FindingResponse)
def get_finding(finding_id: int, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding

@router.post("/", response_model=FindingResponse)
def create_finding(finding: FindingCreate, db: Session = Depends(get_db)):
    db_finding = Finding(**finding.dict())
    db.add(db_finding)
    db.commit()
    db.refresh(db_finding)
    return db_finding

@router.put("/{finding_id}", response_model=FindingResponse)
def update_finding(finding_id: int, finding: FindingUpdate, db: Session = Depends(get_db)):
    db_finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not db_finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    update_data = finding.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_finding, field, value)
    
    db.commit()
    db.refresh(db_finding)
    return db_finding

@router.delete("/{finding_id}")
def delete_finding(finding_id: int, db: Session = Depends(get_db)):
    db_finding = db.query(Finding).filter(Finding.id == finding_id).first()
    if not db_finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    db.delete(db_finding)
    db.commit()
    return {"message": "Finding deleted successfully"}


"""
app/api/routes_evidence.py
Evidence capture and management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.models.evidence import Evidence
from app.models.target import Target
from app.schemas.evidence import EvidenceCreate, EvidenceResponse, EvidenceCaptureRequest
from app.services.evidence_service import evidence_service

router = APIRouter()

@router.get("/", response_model=List[EvidenceResponse])
def list_evidence(
    target_id: int = None,
    finding_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Evidence)
    
    if target_id:
        query = query.filter(Evidence.target_id == target_id)
    if finding_id:
        query = query.filter(Evidence.finding_id == finding_id)
    
    evidence = query.offset(skip).limit(limit).all()
    return evidence

@router.post("/capture")
def capture_evidence(request: EvidenceCaptureRequest, db: Session = Depends(get_db)):
    target = db.query(Target).filter(Target.id == request.target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    results = []
    errors = []
    
    for capture_type in request.capture_types:
        try:
            if capture_type == "fullpage":
                result = evidence_service.capture_fullpage(request.url, request.target_id)
            elif capture_type == "mobile":
                result = evidence_service.capture_mobile(request.url, request.target_id)
            elif capture_type == "http":
                result = evidence_service.capture_http_response(request.url, request.target_id)
            elif capture_type == "network":
                result = evidence_service.capture_network_log(request.url, request.target_id)
            else:
                errors.append(f"Unknown capture type: {capture_type}")
                continue
            
            evidence = Evidence(
                target_id=request.target_id,
                finding_id=request.finding_id,
                type=result["type"],
                file_path=result.get("file_path"),
                meta=result.get("meta"),
                content=result.get("content")
            )
            db.add(evidence)
            results.append(result)
        
        except Exception as e:
            errors.append(f"{capture_type}: {str(e)}")
    
    db.commit()
    
    return {
        "success": len(results) > 0,
        "captured": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }

@router.delete("/{evidence_id}")
def delete_evidence(evidence_id: int, db: Session = Depends(get_db)):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    db.delete(evidence)
    db.commit()
    return {"message": "Evidence deleted successfully"}


"""
app/api/routes_reports.py
Report management and submission endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.models.report import Report
from app.models.target import Target
from app.schemas.report import ReportCreate, ReportUpdate, ReportResponse, ReportSubmitRequest
from app.services.report_builder import report_builder
from app.services.h1_client import h1_client
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=List[ReportResponse])
def list_reports(
    target_id: int = None,
    status: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Report)
    
    if target_id:
        query = query.filter(Report.target_id == target_id)
    if status:
        query = query.filter(Report.status == status)
    
    reports = query.offset(skip).limit(limit).all()
    return reports

@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.post("/", response_model=ReportResponse)
def create_report(report: ReportCreate, db: Session = Depends(get_db)):
    target = db.query(Target).filter(Target.id == report.target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    db_report = Report(**report.dict())
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

@router.post("/generate/{finding_id}")
def generate_report(finding_id: int, db: Session = Depends(get_db)):
    try:
        markdown = report_builder.build_markdown_report(db, finding_id)
        
        from app.models.finding import Finding
        finding = db.query(Finding).filter(Finding.id == finding_id).first()
        
        report = Report(
            target_id=finding.target_id,
            title=finding.title,
            markdown=markdown,
            severity=finding.severity,
            status="draft",
            finding_ids=[finding_id]
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        return report
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{report_id}", response_model=ReportResponse)
def update_report(report_id: int, report: ReportUpdate, db: Session = Depends(get_db)):
    db_report = db.query(Report).filter(Report.id == report_id).first()
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    update_data = report.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_report, field, value)
    
    db.commit()
    db.refresh(db_report)
    return db_report

@router.post("/{report_id}/submit")
def submit_report(report_id: int, request: ReportSubmitRequest, db: Session = Depends(get_db)):
    db_report = db.query(Report).filter(Report.id == report_id).first()
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if db_report.status == "submitted":
        raise HTTPException(status_code=400, detail="Report already submitted")
    
    target = db.query(Target).filter(Target.id == db_report.target_id).first()
    
    if request.platform == "hackerone":
        result = h1_client.submit_report(
            title=db_report.title,
            markdown=db_report.markdown,
            severity=db_report.severity,
            target=target
        )
        
        db_report.status = "submitted" if result.get("status") == "success" else "failed"
        db_report.submitted_to = request.platform
        db_report.submission_response = result
        db_report.submitted_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_report)
        
        return {
            "success": result.get("status") == "success",
            "report": db_report,
            "submission_result": result
        }
    
    else:
        raise HTTPException(status_code=400, detail="Unsupported platform")

@router.delete("/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    db_report = db.query(Report).filter(Report.id == report_id).first()
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    db.delete(db_report)
    db.commit()
    return {"message": "Report deleted successfully"}


"""
app/api/routes_scheduler.py
Scheduler control endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.scheduler_service import scheduler_service
from app.core.config import settings

router = APIRouter()

@router.get("/status")
def get_scheduler_status():
    return {
        "enabled": settings.SCHEDULER_ENABLED,
        "interval_hours": settings.SCHEDULER_INTERVAL_HOURS
    }

@router.post("/run")
def trigger_scheduler(db: Session = Depends(get_db)):
    try:
        results = scheduler_service.run_scheduled_recon(db)
        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run/target/{target_id}")
def trigger_target_recon(target_id: int, db: Session = Depends(get_db)):
    from app.models.target import Target
    
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    
    try:
        result = scheduler_service.run_target_recon(db, target)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


"""
app/api/routes_config.py
Configuration management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import settings
from app.core.security import mask_api_key
from app.schemas.config_schema import PlatformConfig, SchedulerConfig

router = APIRouter()

@router.get("/platform")
def get_platform_config():
    return {
        "hackerone": {
            "api_url": settings.HACKERONE_API_URL,
            "team_handle": settings.HACKERONE_TEAM_HANDLE,
            "token_configured": bool(settings.HACKERONE_API_TOKEN),
            "token_masked": mask_api_key(settings.HACKERONE_API_TOKEN) if settings.HACKERONE_API_TOKEN else None
        },
        "intigriti": {
            "api_url": settings.INTIGRITI_API_URL,
            "token_configured": bool(settings.INTIGRITI_API_TOKEN),
            "token_masked": mask_api_key(settings.INTIGRITI_API_TOKEN) if settings.INTIGRITI_API_TOKEN else None
        },
        "telegram": {
            "bot_configured": bool(settings.TELEGRAM_BOT_TOKEN),
            "chat_id": settings.TELEGRAM_CHAT_ID
        },
        "slack": {
            "webhook_configured": bool(settings.SLACK_WEBHOOK_URL)
        }
    }

@router.get("/scheduler")
def get_scheduler_config():
    return {
        "enabled": settings.SCHEDULER_ENABLED,
        "interval_hours": settings.SCHEDULER_INTERVAL_HOURS,
        "max_crawl_pages": settings.MAX_CRAWL_PAGES,
        "crawl_rate_limit_seconds": settings.CRAWL_RATE_LIMIT_SECONDS
    }

@router.get("/system")
def get_system_config():
    return {
        "chrome_driver_configured": bool(settings.CHROME_DRIVER_PATH),
        "headless_browser": settings.HEADLESS_BROWSER,
        "evidence_path": settings.EVIDENCE_BASE_PATH
    }