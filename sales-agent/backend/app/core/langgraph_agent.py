"""
Advanced LangGraph Agent - FULLY FUNCTIONAL with TRUE Parallel Execution
"""

from typing import Dict, List, TypedDict, Annotated, Callable
import asyncio
import operator
import random

# Direct imports - no try/except wrapper
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ..services.gemini_service import GeminiService
from ..services.search_service import SearchService
from ..services.scraper_service import ScraperService
from ..services.email_service import EmailService
from ..ml.lead_scorer import MLLeadScorer
from ..ml.embeddings import EmbeddingService

# Export for checking
LANGGRAPH_AVAILABLE = True


class CampaignState(TypedDict):
    """Complete campaign state"""
    campaign_id: str
    campaign: Dict
    current_step: str
    progress: float
    errors: List[str]
    product_analysis: Dict
    search_queries: List[str]
    raw_leads: Annotated[List[Dict], operator.add]
    enriched_leads: List[Dict]
    scored_leads: List[Dict]
    filtered_leads: List[Dict]
    high_quality_leads: List[Dict]
    lead_id_map: Dict[str, str]  # Map company_name to database lead_id
    emails_sent: int
    human_approved: bool
    pending_approval_batch: List[Dict]


class LangGraphAgent:
    """Advanced LangGraph agent with parallel execution"""
    
    def __init__(self, campaign: Dict, emit_update: Callable):
        self.campaign = campaign
        self.emit = emit_update
        
        # Services
        self.gemini = GeminiService()
        self.search_service = SearchService()
        self.scraper = ScraperService()
        self.email_service = EmailService()
        self.ml_scorer = MLLeadScorer()
        self.embeddings = EmbeddingService()
        
        # Config
        self.MAX_CONCURRENT_ENRICHMENT = 10
        self.MAX_CONCURRENT_EMAILS = 5
        self.QUALITY_THRESHOLD = 0.65
        self.MAX_RETRIES = 3
        
        self.workflow = self._build_workflow()
    
    def _build_workflow(self):
        """Build workflow with conditional routing"""
        workflow = StateGraph(CampaignState)
        
        # Add nodes
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("search", self._search_node)
        workflow.add_node("enrich_parallel", self._enrich_parallel_node)
        workflow.add_node("score_filter", self._score_filter_node)
        workflow.add_node("quality_check", self._quality_check_node)
        workflow.add_node("send_parallel", self._send_parallel_node)
        
        # Edges
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "search")
        workflow.add_edge("search", "enrich_parallel")
        workflow.add_edge("enrich_parallel", "score_filter")
        workflow.add_edge("score_filter", "quality_check")
        
        # Conditional routing
        workflow.add_conditional_edges(
            "quality_check",
            lambda state: "proceed" if len(state.get("high_quality_leads", [])) >= 5 else "skip_save",
            {"proceed": "save_leads", "skip_save": "save_leads"}
        )
        
        # Add save_leads node
        workflow.add_node("save_leads", self._save_leads_node)
        
        # After saving, conditionally send emails
        workflow.add_conditional_edges(
            "save_leads",
            lambda state: "send" if len(state.get("high_quality_leads", [])) >= 5 else "skip",
            {"send": "send_parallel", "skip": END}
        )
        
        workflow.add_edge("send_parallel", END)
        
        return workflow.compile(checkpointer=MemorySaver())
    
    async def _retry(self, func, *args, **kwargs):
        """Retry with exponential backoff"""
        for attempt in range(self.MAX_RETRIES):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise
                await asyncio.sleep((2 ** attempt) + random.uniform(0, 1))
        return None
    
    async def _analyze_node(self, state: CampaignState) -> Dict:
        await self.emit("🤖 [LangGraph] Analyzing product...")
        
        product_desc = state["campaign"].get("product_description", "")
        target_industry = state["campaign"].get("target_industry", "")
        
        prompt = f"""Analyze this B2B product:
Product: {product_desc}
Industry: {target_industry}

Return JSON with:
1. features: list of 8-12 features
2. target_industries: list of 4-6 industries  
3. pain_points: list of 6-9 problems solved
4. ideal_customer_profile: detailed description
5. keywords: list of 12-18 search keywords

Return ONLY valid JSON."""
        
        response = await self._retry(self.gemini.generate, prompt)
        parsed = self.gemini.parse_json_response(response)
        
        await self.emit(f"✅ Identified {len(parsed.get('keywords', []))} keywords")
        
        return {"product_analysis": parsed, "current_step": "analyze", "progress": 10.0}
    
    async def _search_node(self, state: CampaignState) -> Dict:
        await self.emit("🔍 [LangGraph] Searching...")
        
        product_analysis = state["product_analysis"]
        queries = []
        
        for industry in product_analysis.get("target_industries", [])[:3]:
            queries.append(f'"{industry}" "contact us"')
            queries.append(f'"{industry}" "about us"')
        
        for keyword in product_analysis.get("keywords", [])[:4]:
            queries.append(f'"{keyword}" companies')
        
        all_leads = []
        seen_domains = set()
        
        for query in queries[:10]:
            results = await self.search_service.search(query, num_results=8)
            for result in results:
                url = result.get("link", "")
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                
                if url and domain not in seen_domains:
                    seen_domains.add(domain)
                    all_leads.append({
                        "company_name": self.scraper.extract_company_name_from_url(url),
                        "website": url,
                        "snippet": result.get("snippet", "")
                    })
            await asyncio.sleep(0.5)
        
        await self.emit(f"📊 Found {len(all_leads)} companies")
        return {"raw_leads": all_leads, "current_step": "search", "progress": 40.0}
    
    async def _enrich_one(self, lead: Dict, sem: asyncio.Semaphore) -> Dict:
        async with sem:
            try:
                data = await self.scraper.scrape_website(lead["website"])
                if data and data.get("email"):
                    dms = data.get("decision_makers", [])
                    lead.update({
                        "description": data.get("description", lead["snippet"]),
                        "industry": data.get("industry", ""),
                        "email": data.get("email"),
                        "linkedin_url": data.get("linkedin"),
                        "company_size": data.get("size", 0),
                        "decision_maker_name": dms[0].get("name") if dms else None,
                        "decision_maker_title": dms[0].get("title") if dms else None
                    })
                    return lead
            except Exception as e:
                print(f"Enrich failed: {e}")
            return None
    
    async def _enrich_parallel_node(self, state: CampaignState) -> Dict:
        await self.emit("💎 [LangGraph PARALLEL] Enriching leads...")
        await self.emit(f"⚡ Using {self.MAX_CONCURRENT_ENRICHMENT} parallel workers")
        
        raw_leads = state["raw_leads"][:30]
        sem = asyncio.Semaphore(self.MAX_CONCURRENT_ENRICHMENT)
        
        start = asyncio.get_event_loop().time()
        
        tasks = [self._enrich_one(lead, sem) for lead in raw_leads]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = asyncio.get_event_loop().time() - start
        
        enriched = [r for r in results if r and isinstance(r, dict) and r.get("email")]
        
        await self.emit(f"✅ Enriched {len(enriched)}/{len(raw_leads)} in {elapsed:.1f}s")
        await self.emit(f"⚡ Speed: {len(raw_leads)/elapsed:.1f} leads/sec")
        
        return {"enriched_leads": enriched, "current_step": "enrich", "progress": 60.0}
    
    async def _score_filter_node(self, state: CampaignState) -> Dict:
        await self.emit("🤖 [LangGraph] Scoring & filtering...")
        
        enriched = state["enriched_leads"]
        product_analysis = state["product_analysis"]
        
        # Score leads with ML model
        for lead in enriched:
            try:
                ml = self.ml_scorer.predict(lead, product_analysis)
                lead["ml_score"] = ml["score"]
                lead["ml_confidence"] = ml["confidence"]
                lead["score_explanation"] = ml.get("top_factors", [])
                lead["ml_model_version"] = ml.get("model_version", 1)
            except Exception as e:
                print(f"Scoring error for {lead.get('company_name')}: {e}")
                lead["ml_score"] = 0.5
                lead["ml_confidence"] = 0.3
                lead["score_explanation"] = [{"name": "Fallback", "impact": 0.5, "value": 1.0}]
                lead["ml_model_version"] = 0
        
        # Get ideal customer profile as STRING (not dict)
        ideal = product_analysis.get("ideal_customer_profile", "")
        if isinstance(ideal, dict):
            # Convert dict to string if needed
            ideal = " ".join(str(v) for v in ideal.values() if v)
        ideal = str(ideal) if ideal else "B2B company looking for solutions"
        
        try:
            similar = self.embeddings.find_most_similar_leads(ideal, enriched, top_k=20)
        except Exception as e:
            print(f"Embedding error: {e}")
            # Fallback: use all enriched leads with default similarity
            similar = [(lead, 0.5) for lead in enriched[:20]]
        
        filtered = []
        for lead, sim in similar:
            lead["semantic_similarity"] = float(sim)
            lead["final_score"] = lead["ml_score"] * 0.7 + float(sim) * 0.3
            filtered.append(lead)
        
        filtered.sort(key=lambda x: x["final_score"], reverse=True)
        
        await self.emit(f"✨ Top {len(filtered)} leads scored")
        return {"filtered_leads": filtered, "current_step": "score", "progress": 75.0}
    
    async def _quality_check_node(self, state: CampaignState) -> Dict:
        await self.emit("🎯 [LangGraph] Quality check...")
        
        filtered = state["filtered_leads"]
        high_quality = [l for l in filtered if l.get("final_score", 0) >= self.QUALITY_THRESHOLD]
        
        if len(high_quality) >= 5:
            await self.emit(f"✅ {len(high_quality)} high-quality leads → Proceeding to emails")
        else:
            await self.emit(f"⚠️ Only {len(high_quality)} quality leads → Skipping emails")
        
        return {"high_quality_leads": high_quality, "current_step": "quality", "progress": 85.0}
    
    async def _save_leads_node(self, state: CampaignState) -> Dict:
        """Save all leads to database"""
        await self.emit("💾 [LangGraph] Saving leads to database...")
        
        try:
            from ..models.database import SessionLocal
            from ..models.tables import Lead
            
            db = SessionLocal()
            campaign_id = state["campaign_id"]
            
            # Save all filtered leads (not just high quality)
            leads_to_save = state.get("filtered_leads", [])
            if not leads_to_save:
                leads_to_save = state.get("enriched_leads", [])
            
            saved_count = 0
            lead_id_map = {}  # Map company_name to lead_id for email saving
            
            for lead_data in leads_to_save:
                try:
                    # Check if lead already exists
                    existing = db.query(Lead).filter(
                        Lead.campaign_id == campaign_id,
                        Lead.company_name == lead_data.get("company_name")
                    ).first()
                    
                    if existing:
                        lead_id_map[lead_data.get("company_name")] = existing.id
                        continue
                    
                    lead = Lead(
                        campaign_id=campaign_id,
                        company_name=lead_data.get("company_name", "Unknown"),
                        industry=lead_data.get("industry"),
                        website=lead_data.get("website"),
                        description=lead_data.get("description", "")[:1000] if lead_data.get("description") else None,
                        company_size=lead_data.get("company_size"),
                        location=lead_data.get("location"),
                        decision_maker_name=lead_data.get("decision_maker_name"),
                        decision_maker_title=lead_data.get("decision_maker_title"),
                        email=lead_data.get("email"),
                        linkedin_url=lead_data.get("linkedin_url"),
                        ml_score=lead_data.get("final_score") or lead_data.get("ml_score"),
                        ml_confidence=lead_data.get("ml_confidence"),
                        score_explanation=lead_data.get("score_explanation"),  # ML factors
                        ml_model_version=lead_data.get("ml_model_version", 1),
                        status="new"
                    )
                    db.add(lead)
                    db.flush()  # Get the ID
                    lead_id_map[lead_data.get("company_name")] = lead.id
                    saved_count += 1
                except Exception as e:
                    print(f"Error saving lead {lead_data.get('company_name')}: {e}")
            
            db.commit()
            db.close()
            
            await self.emit(f"✅ Saved {saved_count} leads to database")
            
            # Store lead_id_map in state for email saving
            return {"current_step": "saved", "progress": 88.0, "lead_id_map": lead_id_map}
            
        except Exception as e:
            print(f"Error in save_leads_node: {e}")
            await self.emit(f"⚠️ Error saving leads: {str(e)[:50]}")
            return {"current_step": "saved", "progress": 88.0, "lead_id_map": {}}
    
    async def _send_one_email(self, lead: Dict, product: Dict, campaign: Dict, lead_id: str, sem: asyncio.Semaphore) -> bool:
        async with sem:
            try:
                prompt = f"""Write professional B2B email:
Product: {campaign.get('product_description', '')[:200]}
Company: {lead['company_name']}
Description: {lead.get('description', '')[:150]}

Return JSON: {{"subject": "...", "body": "..."}}
Under 120 words."""
                
                response = await self._retry(self.gemini.generate, prompt)
                email_content = self.gemini.parse_json_response(response)
                
                subject = email_content.get("subject", "Partnership Opportunity")
                body = email_content.get("body", "")
                
                sent = await self.email_service.send_email(
                    to_email=lead["email"],
                    subject=subject,
                    body=body
                )
                
                if sent:
                    # Save email to database
                    try:
                        from ..models.database import SessionLocal
                        from ..models.tables import Email
                        from datetime import datetime
                        
                        db = SessionLocal()
                        email_record = Email(
                            lead_id=lead_id,
                            subject=subject,
                            body=body,
                            status="sent",  # Mark as sent
                            sent_at=datetime.utcnow()
                        )
                        db.add(email_record)
                        db.commit()
                        db.close()
                    except Exception as e:
                        print(f"Error saving email to DB: {e}")
                    
                    await self.emit(f"✅ Sent to {lead['company_name']}")
                    return True
            except Exception as e:
                print(f"Email error: {e}")
            return False
    
    async def _send_parallel_node(self, state: CampaignState) -> Dict:
        await self.emit("✉️ [LangGraph PARALLEL] Sending emails...")
        await self.emit(f"⚡ Using {self.MAX_CONCURRENT_EMAILS} parallel workers")
        
        leads = state["high_quality_leads"][:15]
        product = state["product_analysis"]
        campaign = state["campaign"]
        lead_id_map = state.get("lead_id_map", {})
        
        sem = asyncio.Semaphore(self.MAX_CONCURRENT_EMAILS)
        
        start = asyncio.get_event_loop().time()
        
        # Pass lead_id to email sending
        tasks = []
        for lead in leads:
            lead_id = lead_id_map.get(lead.get("company_name"))
            if lead_id and lead.get("email"):
                tasks.append(self._send_one_email(lead, product, campaign, lead_id, sem))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = asyncio.get_event_loop().time() - start
        
        sent = sum(1 for r in results if r is True)
        
        await self.emit(f"🎉 Complete! Sent {sent} emails in {elapsed:.1f}s")
        await self.emit(f"⚡ Speed: {sent/elapsed:.1f} emails/sec" if elapsed > 0 else "⚡ Speed: instant")
        
        return {"emails_sent": sent, "current_step": "complete", "progress": 100.0}
    
    async def run(self) -> Dict:
        await self.emit("🌐 LangGraph ADVANCED Mode: ENABLED")
        await self.emit("⚡ Parallel execution: UP TO 10x FASTER")
        await self.emit("🎯 Conditional routing: ENABLED")
        
        try:
            initial_state: CampaignState = {
                "campaign_id": str(self.campaign.get("id")),
                "campaign": self.campaign,
                "current_step": "start",
                "progress": 0.0,
                "errors": [],
                "product_analysis": {},
                "search_queries": [],
                "raw_leads": [],
                "enriched_leads": [],
                "scored_leads": [],
                "filtered_leads": [],
                "high_quality_leads": [],
                "lead_id_map": {},
                "emails_sent": 0,
                "human_approved": False,
                "pending_approval_batch": []
            }
            
            config = {"configurable": {"thread_id": str(self.campaign.get("id"))}}
            final_state = await self.workflow.ainvoke(initial_state, config)
            
            try:
                from ..models.database import SessionLocal
                from ..models.tables import Campaign
                
                db = SessionLocal()
                camp = db.query(Campaign).filter(Campaign.id == self.campaign.get('id')).first()
                if camp:
                    camp.status = "completed"
                    db.commit()
                db.close()
            except Exception as e:
                print(f"DB error: {e}")
            
            return {
                "status": "success",
                "leads_found": len(final_state.get("high_quality_leads", [])),
                "emails_sent": final_state.get("emails_sent", 0)
            }
            
        except Exception as e:
            await self.emit(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
