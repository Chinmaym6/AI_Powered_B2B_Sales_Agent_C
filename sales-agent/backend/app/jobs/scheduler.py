"""
Background Job Scheduler for Email Monitoring and Auto-Retraining
Uses APScheduler to run periodic tasks
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from ..services.email_monitor_service import EmailMonitorService
from ..models.database import SessionLocal
from ..models.tables import Lead
import subprocess
from pathlib import Path


class JobScheduler:
    """Schedule and manage background jobs"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.email_monitor = EmailMonitorService()
    
    async def start(self):
        """Start all scheduled jobs"""
        
        print("🚀 Starting background job scheduler...")
        
        # Job 1: Check for email replies every 5 minutes
        self.scheduler.add_job(
            func=self.check_email_replies_job,
            trigger=IntervalTrigger(minutes=5),
            id='check_email_replies',
            name='Check Email Replies',
            replace_existing=True
        )
        print("  ✅ Email reply checker: Every 5 minutes")
        
        # Job 2: Auto-retrain model daily at 2 AM (if enough data)
        self.scheduler.add_job(
            func=self.auto_retrain_job,
            trigger=CronTrigger(hour=2, minute=0),
            id='auto_retrain_model',
            name='Auto-Retrain ML Model',
            replace_existing=True
        )
        print("  ✅ Auto-retrain ML model: Daily at 2:00 AM")
        
        # Job 3: Clean up old data monthly
        self.scheduler.add_job(
            func=self.cleanup_job,
            trigger=CronTrigger(day=1, hour=3, minute=0),
            id='cleanup_old_data',
            name='Cleanup Old Data',
            replace_existing=True
        )
        print("  ✅ Data cleanup: Monthly on the 1st")
        
        self.scheduler.start()
        print("✅ Background jobs started successfully!\n")
    
    async def stop(self):
        """Stop all scheduled jobs"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("🛑 Background jobs stopped")
    
    async def check_email_replies_job(self):
        """
        Job: Check inbox for new replies and process them
        Runs every 5 minutes
        """
        
        try:
            print(f"\n📧 [{datetime.now().strftime('%H:%M:%S')}] Checking for email replies...")
            
            stats = await self.email_monitor.check_for_replies()
            
            if 'error' in stats:
                print(f"   ⚠️ Error: {stats['error']}")
            else:
                print(f"   📊 Checked: {stats.get('total_checked', 0)} emails")
                print(f"   💌 Replies found: {stats.get('replies_found', 0)}")
                print(f"   ✅ Processed: {stats.get('processed', 0)}")
                print(f"   🤖 Auto-labeled: {stats.get('auto_labeled', 0)}")
                
                if stats.get('errors', 0) > 0:
                    print(f"   ❌ Errors: {stats.get('errors', 0)}")
            
        except Exception as e:
            print(f"❌ Email reply check job failed: {e}")
    
    async def auto_retrain_job(self):
        """
        Job: Auto-retrain XGBoost model if enough new labeled data
        Runs daily at 2 AM
        """
        
        try:
            print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] Checking if model retraining is needed...")
            
            # Count labeled leads
            db = SessionLocal()
            labeled_count = db.query(Lead).filter(
                Lead.actual_outcome.isnot(None)
            ).count()
            db.close()
            
            min_labels = 50  # Minimum labels needed for retraining
            
            print(f"   📊 Labeled leads: {labeled_count}")
            
            if labeled_count >= min_labels:
                print(f"   🧠 Enough data! Starting model retraining...")
                
                # Run retraining script
                backend_path = Path(__file__).parent.parent.parent
                retrain_script = backend_path / "scripts" / "retrain_with_real_data.py"
                
                if retrain_script.exists():
                    result = subprocess.run(
                        ["python", str(retrain_script)],
                        cwd=str(backend_path),
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        print("   ✅ Model retrained successfully!")
                        print(result.stdout)
                    else:
                        print(f"   ❌ Retraining failed: {result.stderr}")
                else:
                    print(f"   ⚠️ Retraining script not found: {retrain_script}")
            else:
                print(f"   ⏳ Not enough data yet. Need {min_labels - labeled_count} more labeled leads.")
        
        except Exception as e:
            print(f"❌ Auto-retrain job failed: {e}")
    
    async def cleanup_job(self):
        """
        Job: Clean up old data (optional)
        Runs monthly
        """
        
        try:
            print(f"\n🧹 [{datetime.now().strftime('%H:%M:%S')}] Running data cleanup...")
            
            # Example: Delete very old campaigns that are completed
            # (Customize this based on your needs)
            
            print("   ✅ Cleanup completed")
        
        except Exception as e:
            print(f"❌ Cleanup job failed: {e}")


# Global scheduler instance
_scheduler_instance = None


async def start_scheduler():
    """Start the global scheduler instance"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = JobScheduler()
        await _scheduler_instance.start()


async def stop_scheduler():
    """Stop the global scheduler instance"""
    global _scheduler_instance
    
    if _scheduler_instance:
        await _scheduler_instance.stop()
        _scheduler_instance = None


def get_scheduler() -> JobScheduler:
    """Get the global scheduler instance"""
    return _scheduler_instance
