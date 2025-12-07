from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Set
import asyncio
from datetime import datetime

from ...core.agent import AutonomousAgent
from ...models.database import get_db, SessionLocal
from ...models.tables import Campaign, Lead, Email
from ...models.schemas import CampaignCreate, CampaignUpdate, CampaignResponse, LeadResponse

router = APIRouter(tags=["campaigns"])

# Connection Manager for WebSockets
class ConnectionManager:
    def __init__(self):
        # campaign_id -> List[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Track running campaigns to prevent duplicate runs
        self.running_campaigns: Set[str] = set()

    async def connect(self, campaign_id: str, websocket: WebSocket):
        await websocket.accept()
        if campaign_id not in self.active_connections:
            self.active_connections[campaign_id] = []
        self.active_connections[campaign_id].append(websocket)

    def disconnect(self, campaign_id: str, websocket: WebSocket):
        if campaign_id in self.active_connections:
            if websocket in self.active_connections[campaign_id]:
                self.active_connections[campaign_id].remove(websocket)
            if not self.active_connections[campaign_id]:
                del self.active_connections[campaign_id]

    async def broadcast(self, campaign_id: str, message: dict):
        if campaign_id in self.active_connections:
            for connection in self.active_connections[campaign_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error broadcasting to {campaign_id}: {e}")

manager = ConnectionManager()

async def run_background_agent(campaign_id: str):
    """Run the agent in the background"""
    print(f"DEBUG: Starting background agent for {campaign_id}")
    manager.running_campaigns.add(campaign_id)
    
    # Create a new DB session for this background task
    db = SessionLocal()
    
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            print(f"ERROR: Campaign {campaign_id} not found in background task")
            return

        # Define emit function that broadcasts to all connected clients
        async def emit_update(message: str):
            await manager.broadcast(campaign_id, {
                "type": "update",
                "message": message,
                "timestamp": datetime.now().isoformat()
            })

        # Prepare campaign dict
        campaign_dict = {
            "id": str(campaign.id),
            "name": campaign.name,
            "product_description": campaign.product_description,
            "target_industry": campaign.target_industry,
            "company_size": campaign.company_size,
            "target_regions": campaign.target_regions,
            "product_name": campaign.product_name,
            "target_audience": campaign.target_audience
        }

        # Check if multi-agent mode is enabled
        import os
        use_multi_agent = os.getenv("USE_MULTI_AGENT", "true").lower() == "true"
        
        if use_multi_agent:
            # Use Multi-Agent Collaborative System
            from app.core.multi_agent import create_multi_agent_system
            from app.services.gemini_service import GeminiService
            from app.services.scraper_service import ScraperService
            from app.ml.lead_scorer import MLLeadScorer
            from app.ml.embeddings import EmbeddingService
            from app.services.email_service import EmailService
            
            await emit_update("🤖 Multi-Agent Mode: ACTIVATED")
            
            gemini = GeminiService()
            scraper = ScraperService()
            ml_scorer = MLLeadScorer()
            embeddings = EmbeddingService()
            email_service = EmailService()
            
            agent = create_multi_agent_system(
                campaign=campaign_dict,
                gemini_service=gemini,
                scraper_service=scraper,
                ml_scorer=ml_scorer,
                embedding_service=embeddings,
                email_service=email_service,
                emit_callback=emit_update
            )
        else:
            # Use standard LangGraph agent
            agent = AutonomousAgent(campaign_dict, emit_update)
        
        result = await agent.run()
        
        # Broadcast completion
        await manager.broadcast(campaign_id, {
            "type": "complete",
            "result": result
        })
        
    except Exception as e:
        print(f"Background agent error: {e}")
        import traceback
        traceback.print_exc()
        await manager.broadcast(campaign_id, {
            "type": "error",
            "message": str(e)
        })
    finally:
        if campaign_id in manager.running_campaigns:
            manager.running_campaigns.remove(campaign_id)
        db.close()
        print(f"DEBUG: Background agent for {campaign_id} finished")

@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign: CampaignCreate,
    db: Session = Depends(get_db)
):
    """Create a new campaign"""
    
    db_campaign = Campaign(
        name=campaign.name,
        product_description=campaign.product_description,
        target_industry=campaign.target_industry,
        company_size=campaign.company_size,
        target_regions=campaign.target_regions,
        status="pending"
    )
    
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    
    return db_campaign

@router.get("/", response_model=List[Dict])
async def list_campaigns(db: Session = Depends(get_db)):
    """List all campaigns"""
    campaigns = db.query(Campaign).order_by(Campaign.created_at.desc()).all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "status": c.status,
            "created_at": c.created_at,
            "leads_count": len(c.leads)
        }
        for c in campaigns
    ]

@router.post("/{campaign_id}/stop")
async def stop_campaign(campaign_id: str, db: Session = Depends(get_db)):
    """Stop a running campaign"""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign.status == "running":
        campaign.status = "stopped"
        db.commit()
        # Broadcast stopped message
        await manager.broadcast(campaign_id, {
            "type": "info",
            "message": "Campaign stopped by user."
        })
    
    return {"status": "stopped"}

@router.put("/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    campaign_update: CampaignUpdate,
    db: Session = Depends(get_db)
):
    """Update campaign inputs (name, product_description, target_industry, etc.)"""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Update only provided fields
    update_data = campaign_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(campaign, field, value)
    
    db.commit()
    db.refresh(campaign)
    
    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "product_description": campaign.product_description,
        "target_industry": campaign.target_industry,
        "company_size": campaign.company_size,
        "target_regions": campaign.target_regions,
        "status": campaign.status,
        "message": "Campaign updated successfully"
    }

@router.post("/{campaign_id}/rerun")
async def rerun_campaign(campaign_id: str, db: Session = Depends(get_db)):
    """
    Rerun a campaign: Delete old leads/emails and start fresh.
    """
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Check if campaign is currently running
    if campaign_id in manager.running_campaigns:
        raise HTTPException(status_code=400, detail="Campaign is already running")
    
    # Delete old emails first (due to foreign key constraint)
    old_leads = db.query(Lead).filter(Lead.campaign_id == campaign_id).all()
    for lead in old_leads:
        db.query(Email).filter(Email.lead_id == lead.id).delete()
    
    # Delete old leads
    db.query(Lead).filter(Lead.campaign_id == campaign_id).delete()
    
    # Reset campaign status to trigger new run
    campaign.status = "pending"
    campaign.execution_state = "idle"
    campaign.current_step = None
    campaign.progress_percentage = 0
    campaign.leads_processed = 0
    campaign.leads_total = 0
    campaign.error_message = None
    campaign.can_resume = True
    campaign.product_analysis = None  # Reset product analysis for fresh run
    
    db.commit()
    
    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "status": "pending",
        "message": "Campaign cleared and ready to rerun. All old leads and emails deleted."
    }

@router.get("/{campaign_id}/inputs")
async def get_campaign_inputs(campaign_id: str, db: Session = Depends(get_db)):
    """Get campaign input details for editing"""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "product_name": getattr(campaign, 'product_name', '') or '',
        "product_description": campaign.product_description,
        "target_industry": campaign.target_industry or '',
        "target_audience": getattr(campaign, 'target_audience', '') or '',
        "company_size": campaign.company_size or '',
        "target_regions": campaign.target_regions or [],
        "status": campaign.status,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None
    }

@router.delete("/{campaign_id}")
async def delete_campaign(campaign_id: str, db: Session = Depends(get_db)):
    """Delete a campaign and all associated data"""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Stop if running
    if campaign.status == "running":
        # We can reuse the stop logic or just let the delete happen
        # If we delete, the background task might fail on next DB access, which is handled in the try/except block of run_background_agent
        pass

    # Remove from running set if present
    if campaign_id in manager.running_campaigns:
        manager.running_campaigns.remove(campaign_id)
        
    # Close connections
    if campaign_id in manager.active_connections:
        # Notify clients
        await manager.broadcast(campaign_id, {
            "type": "info",
            "message": "Campaign deleted."
        })
        # We can't easily force close from here without iterating, but the client will handle the error/close
        del manager.active_connections[campaign_id]

    db.delete(campaign)
    db.commit()
    
    return {"status": "deleted", "id": campaign_id}

@router.websocket("/{campaign_id}/live")
async def campaign_live_feed(
    websocket: WebSocket,
    campaign_id: str,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time campaign updates
    """
    
    await manager.connect(campaign_id, websocket)
    
    try:
        # Get campaign
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        
        if not campaign:
            await websocket.send_json({"error": "Campaign not found"})
            await websocket.close()
            return
        
        # If campaign is pending, start it in background
        if campaign.status == "pending" and campaign_id not in manager.running_campaigns:
            print(f"DEBUG: Triggering background run for {campaign_id}")
            # Update status to running immediately
            campaign.status = "running"
            db.commit()
            
            # Start background task
            asyncio.create_task(run_background_agent(campaign_id))
            
        elif campaign.status == "running" and campaign_id not in manager.running_campaigns:
            # Recovery: It says running in DB but not in memory (maybe server restarted)
            # Restart it
            print(f"DEBUG: Recovering/Restarting background run for {campaign_id}")
            asyncio.create_task(run_background_agent(campaign_id))
            
        # Keep connection open to receive broadcasts
        while True:
            # We just wait for messages (or disconnect)
            # The client might send "ping" or something, but mostly we just push data
            data = await websocket.receive_text()
            
    except WebSocketDisconnect:
        manager.disconnect(campaign_id, websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(campaign_id, websocket)


@router.get("/{campaign_id}/status")
async def get_campaign_status(campaign_id: str, db: Session = Depends(get_db)):
    """Get current campaign execution status and progress"""
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return {
        "campaign_id": str(campaign.id),
        "execution_state": campaign.execution_state or "idle",
        "current_step": campaign.current_step,
        "progress_percentage": campaign.progress_percentage or 0,
        "leads_processed": campaign.leads_processed or 0,
        "leads_total": campaign.leads_total or 0,
        "last_activity_at": campaign.last_activity_at.isoformat() if campaign.last_activity_at else None,
        "error_message": campaign.error_message,
        "can_resume": campaign.can_resume,
        "is_running": campaign_id in manager.running_campaigns
    }

@router.get("/{campaign_id}")
async def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    """Get campaign details and stats"""
    
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    leads = db.query(Lead).filter(Lead.campaign_id == campaign_id).all()
    emails = db.query(Email).join(Lead).filter(Lead.campaign_id == campaign_id).all()
    
    stats = {
        "leads_found": len(leads),
        "emails_sent": len([e for e in emails if e.sent_at]),
        "replies": len([e for e in emails if e.replied_at]),
        "positive_interest": len([e for e in emails if e.reply_sentiment == "positive"])
    }
    
    leads_with_emails = [l for l in leads if l.email]
    top_leads = sorted(leads_with_emails, key=lambda x: x.ml_score or 0, reverse=True)[:20]
    
    leads_data = []
    for lead in top_leads:
        lead_emails = [e for e in emails if e.lead_id == lead.id]
        reply_status = "none"
        sentiment = "neutral"
        
        if any(e.replied_at for e in lead_emails):
            reply_status = "replied"
            latest_reply = sorted([e for e in lead_emails if e.replied_at], key=lambda x: x.replied_at, reverse=True)[0]
            sentiment = latest_reply.reply_sentiment or "neutral"
            if sentiment == "positive":
                reply_status = "positive"
            elif sentiment == "negative":
                reply_status = "negative"
        elif any(e.sent_at for e in lead_emails):
            reply_status = "emailed"
            
        leads_data.append({
            "id": str(lead.id),
            "company_name": lead.company_name,
            "industry": lead.industry,
            "website": lead.website,
            "description": lead.description,
            "company_size": lead.company_size,
            "location": lead.location,
            "decision_maker_name": lead.decision_maker_name,
            "decision_maker_title": lead.decision_maker_title,
            "email": lead.email,
            "linkedin_url": lead.linkedin_url,
            "ml_score": lead.ml_score,
            "ml_confidence": lead.ml_confidence,
            "score_explanation": lead.score_explanation,
            "status": lead.status,
            "replyStatus": reply_status,
            "sentiment": sentiment,
            "created_at": lead.created_at.isoformat() if lead.created_at else None
        })
        
    email_logs = []
    for email in emails:
        if email.sent_at:
            email_logs.append({
                "leadId": str(email.lead_id),
                "company_name": next((l.company_name for l in leads if l.id == email.lead_id), "Unknown"),
                "subject": email.subject,
                "body": email.body,
                "success": email.status == "sent",
                "sent_at": email.sent_at.isoformat()
            })
    
    email_logs.sort(key=lambda x: x["sent_at"], reverse=True)
    
    return {
        "campaign": {
            "id": str(campaign.id),
            "name": campaign.name,
            "status": campaign.status,
            "execution_state": campaign.execution_state or "idle",
            "current_step": campaign.current_step,
            "progress_percentage": campaign.progress_percentage or 0,
            "created_at": campaign.created_at.isoformat() if campaign.created_at else None
        },
        "stats": stats,
        "leads": leads_data,
        "email_logs": email_logs
    }
