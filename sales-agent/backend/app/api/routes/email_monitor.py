"""
Email Monitor API Routes
Manual triggers and stats for email reply monitoring
"""

from fastapi import APIRouter, HTTPException
from typing import Dict
from ...services.email_monitor_service import EmailMonitorService
from ...jobs.scheduler import get_scheduler
from ...models.database import SessionLocal
from ...models.tables import Lead, Email
from sqlalchemy import func

router = APIRouter()

email_monitor = EmailMonitorService()


@router.post("/check")
async def manual_check_replies() -> Dict:
    """
    Manually trigger email reply checking
    (Normally runs automatically every 5 minutes)
    """
    
    try:
        stats = await email_monitor.check_for_replies()
        return {
            "success": True,
            "message": "Email check completed",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_monitoring_stats() -> Dict:
    """Get email monitoring statistics"""
    
    try:
        db = SessionLocal()
        
        # Count leads with replies
        total_leads = db.query(Lead).count()
        replied_leads = db.query(Lead).filter(Lead.reply_received == True).count()
        
        # Count by sentiment
        positive_replies = db.query(Lead).filter(
            Lead.reply_sentiment == 'positive'
        ).count()
        
        negative_replies = db.query(Lead).filter(
            Lead.reply_sentiment == 'negative'
        ).count()
        
        neutral_replies = db.query(Lead).filter(
            Lead.reply_sentiment == 'neutral'
        ).count()
        
        # Count auto-labeled
        auto_labeled = db.query(Lead).filter(
            Lead.auto_labeled == True
        ).count()
        
        # Count needs review
        needs_review = db.query(Lead).filter(
            Lead.needs_manual_review == True
        ).count()
        
        # Count labeled outcomes
        good_leads = db.query(Lead).filter(Lead.actual_outcome == 1).count()
        bad_leads = db.query(Lead).filter(Lead.actual_outcome == 0).count()
        unlabeled = db.query(Lead).filter(Lead.actual_outcome.is_(None)).count()
        
        db.close()
        
        return {
            "total_leads": total_leads,
            "replied_leads": replied_leads,
            "reply_rate": f"{(replied_leads/total_leads*100):.1f}%" if total_leads > 0 else "0%",
            "sentiment_breakdown": {
                "positive": positive_replies,
                "negative": negative_replies,
                "neutral": neutral_replies
            },
            "auto_labeled": auto_labeled,
            "needs_manual_review": needs_review,
            "outcomes": {
                "good_leads": good_leads,
                "bad_leads": bad_leads,
                "unlabeled": unlabeled
            },
            "ready_for_retraining": good_leads + bad_leads >= 50
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrain")
async def manual_trigger_retrain() -> Dict:
    """
    Manually trigger XGBoost model retraining
    (Normally runs automatically daily at 2 AM)
    """
    
    try:
        import subprocess
        from pathlib import Path
        
        # Count labeled leads
        db = SessionLocal()
        labeled_count = db.query(Lead).filter(
            Lead.actual_outcome.isnot(None)
        ).count()
        db.close()
        
        if labeled_count < 50:
            return {
                "success": False,
                "message": f"Not enough labeled data. Have {labeled_count}, need 50.",
                "labeled_count": labeled_count,
                "needed": 50
            }
        
        # Run retraining script
        backend_path = Path(__file__).parent.parent.parent.parent
        retrain_script = backend_path / "scripts" / "retrain_with_real_data.py"
        
        if not retrain_script.exists():
            raise HTTPException(
                status_code=500, 
                detail=f"Retraining script not found: {retrain_script}"
            )
        
        result = subprocess.run(
            ["python", str(retrain_script)],
            cwd=str(backend_path),
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": "Model retrained successfully",
                "labeled_count": labeled_count,
                "output": result.stdout[:500]  # First 500 chars
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Retraining failed: {result.stderr}"
            )
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Retraining timeout (>2 minutes)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler/status")
async def get_scheduler_status() -> Dict:
    """Get background scheduler status"""
    
    scheduler = get_scheduler()
    
    if not scheduler:
        return {
            "running": False,
            "message": "Scheduler not initialized"
        }
    
    jobs = []
    for job in scheduler.scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None
        })
    
    return {
        "running": scheduler.scheduler.running,
        "jobs": jobs
    }
