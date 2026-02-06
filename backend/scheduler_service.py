"""
app/services/scheduler_service.py
Watchlist scheduler for automated recon and notifications
"""
import logging
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.target import Target
from app.models.finding import Finding
from app.services.recon_service import recon_service, ReconResult
from app.core.notifications import notification_service

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.last_run: Dict[int, datetime] = {}
    
    def run_scheduled_recon(self, db: Session) -> Dict[str, Any]:
        logger.info("Starting scheduled recon for all enabled targets")
        
        targets = db.query(Target).filter(Target.enabled == True).all()
        
        results = {
            "total_targets": len(targets),
            "successful": 0,
            "failed": 0,
            "new_findings": 0,
            "targets_processed": []
        }
        
        for target in targets:
            try:
                target_result = self.run_target_recon(db, target)
                results["successful"] += 1
                results["new_findings"] += target_result["new_findings_count"]
                results["targets_processed"].append({
                    "target_id": target.id,
                    "target_name": target.name,
                    "new_findings": target_result["new_findings_count"]
                })
                
                logger.info(f"Recon completed for {target.name}: {target_result['new_findings_count']} new findings")
            
            except Exception as e:
                logger.error(f"Recon failed for {target.name}: {e}")
                results["failed"] += 1
        
        logger.info(f"Scheduled recon completed: {results['successful']}/{len(targets)} targets, {results['new_findings']} new findings")
        
        return results
    
    def run_target_recon(self, db: Session, target: Target) -> Dict[str, Any]:
        logger.info(f"Running recon for target: {target.name}")
        
        recon_result: ReconResult = recon_service.run_passive_recon(target.url, target.name)
        
        old_hash = target.recon_hash
        new_hash = recon_result.hash
        
        is_changed = old_hash != new_hash
        new_findings_count = 0
        new_findings = []
        
        if is_changed or old_hash is None:
            logger.info(f"Changes detected for {target.name} (old: {old_hash}, new: {new_hash})")
            
            for finding_data in recon_result.findings:
                finding_hash = self._compute_finding_hash(finding_data)
                
                existing = db.query(Finding).filter(
                    Finding.target_id == target.id,
                    Finding.finding_hash == finding_hash
                ).first()
                
                if not existing:
                    new_finding = Finding(
                        target_id=target.id,
                        title=finding_data.get("title", "Unknown Finding"),
                        severity=finding_data.get("severity", "info"),
                        status="open",
                        description=finding_data.get("description", ""),
                        raw_data=finding_data.get("raw_data", {}),
                        finding_hash=finding_hash
                    )
                    
                    db.add(new_finding)
                    new_findings_count += 1
                    new_findings.append(new_finding)
            
            target.recon_hash = new_hash
            target.last_recon = datetime.utcnow()
            db.commit()
            
            if new_findings_count > 0:
                self._send_notifications(target, new_findings)
        
        else:
            logger.info(f"No changes detected for {target.name}")
            target.last_recon = datetime.utcnow()
            db.commit()
        
        return {
            "target_id": target.id,
            "target_name": target.name,
            "is_changed": is_changed,
            "new_findings_count": new_findings_count,
            "total_findings": len(recon_result.findings),
            "hash": new_hash
        }
    
    def _compute_finding_hash(self, finding_data: Dict[str, Any]) -> str:
        import hashlib
        hash_string = f"{finding_data.get('title', '')}{finding_data.get('severity', '')}{finding_data.get('description', '')}"
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def _send_notifications(self, target: Target, findings: List[Finding]):
        if not findings:
            return
        
        severity_groups = {}
        for finding in findings:
            if finding.severity not in severity_groups:
                severity_groups[finding.severity] = []
            severity_groups[finding.severity].append(finding)
        
        for severity, group in severity_groups.items():
            if group:
                first_finding = group[0]
                notification_service.send_finding_alert(
                    target_name=target.name,
                    finding_title=first_finding.title,
                    severity=severity,
                    count=len(group)
                )

scheduler_service = SchedulerService()


"""
app/workers/scheduler_worker.py
APScheduler-based worker for running scheduled tasks
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from app.core.db import SessionLocal
from app.core.config import settings
from app.services.scheduler_service import scheduler_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_scheduled_job():
    logger.info("=" * 60)
    logger.info(f"Starting scheduled recon job at {datetime.now()}")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        results = scheduler_service.run_scheduled_recon(db)
        logger.info(f"Job completed: {results}")
    except Exception as e:
        logger.error(f"Job failed with error: {e}", exc_info=True)
    finally:
        db.close()
    
    logger.info("=" * 60)
    logger.info(f"Scheduled job finished at {datetime.now()}")
    logger.info("=" * 60)

def main():
    logger.info("AutoBounty OS Scheduler Worker Starting...")
    logger.info(f"Scheduler interval: {settings.SCHEDULER_INTERVAL_HOURS} hours")
    logger.info(f"Scheduler enabled: {settings.SCHEDULER_ENABLED}")
    
    if not settings.SCHEDULER_ENABLED:
        logger.warning("Scheduler is disabled in configuration. Exiting.")
        return
    
    scheduler = BlockingScheduler()
    
    scheduler.add_job(
        run_scheduled_job,
        trigger=IntervalTrigger(hours=settings.SCHEDULER_INTERVAL_HOURS),
        id='recon_job',
        name='Periodic Recon Job',
        replace_existing=True
    )
    
    logger.info("Scheduler configured. Starting...")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler shutting down...")
        scheduler.shutdown()

if __name__ == "__main__":
    main()


"""
scripts/run_scheduler.py
Standalone script to run the scheduler
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.workers.scheduler_worker import main

if __name__ == "__main__":
    main()