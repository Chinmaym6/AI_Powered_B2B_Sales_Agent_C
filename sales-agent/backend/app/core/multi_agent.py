"""
Multi-Agent B2B Sales System using LangGraph

This module implements a collaborative multi-agent architecture where
specialized agents work together to research, qualify, and engage leads.

Architecture:
- ResearcherAgent: Deep company research and data extraction
- QualifierAgent: Lead scoring with detailed reasoning
- CopywriterAgent: Personalized email generation
- MultiAgentOrchestrator: Coordinates agent workflow
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .agent_prompts import (
    RESEARCHER_SYSTEM_PROMPT,
    QUALIFIER_SYSTEM_PROMPT,
    COPYWRITER_SYSTEM_PROMPT,
    SUPERVISOR_SYSTEM_PROMPT,
    PRODUCT_ANALYSIS_PROMPT,
    LEAD_RESEARCH_PROMPT,
    LEAD_QUALIFICATION_PROMPT,
    EMAIL_GENERATION_PROMPT
)
from ..config import settings  # Import settings for configurable limits


# =============================================================================
# STATE DEFINITIONS
# =============================================================================

class AgentState(TypedDict):
    """State for individual agent tasks"""
    task: str
    input_data: Dict
    output_data: Dict
    agent_name: str
    success: bool
    error: Optional[str]


class MultiAgentState(TypedDict):
    """Complete state for multi-agent workflow"""
    campaign_id: str
    campaign: Dict
    current_phase: str
    progress: float
    
    # Product analysis
    product_analysis: Dict
    
    # Leads at different stages
    raw_leads: Annotated[List[Dict], operator.add]
    researched_leads: List[Dict]
    qualified_leads: List[Dict]
    leads_with_emails: List[Dict]
    
    # Agent outputs
    agent_outputs: List[Dict]
    
    # Control
    errors: List[str]
    emails_sent: int


# =============================================================================
# BASE AGENT CLASS
# =============================================================================

class BaseAgent:
    """Base class for all specialized agents"""
    
    def __init__(self, gemini_service, emit_callback, system_prompt: str):
        self.gemini = gemini_service
        self.emit = emit_callback
        self.system_prompt = system_prompt
        self.max_retries = 3
    
    async def invoke(self, prompt: str, context: Dict = None) -> Dict:
        """Invoke the agent with a prompt and optional context with retry"""
        full_prompt = f"{self.system_prompt}\n\n---\n\n{prompt}"
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                response = await asyncio.wait_for(
                    self.gemini.generate(full_prompt),
                    timeout=90  # INCREASED: 90s timeout for complex prompts
                )
                
                # Parse JSON response
                result = self.gemini.parse_json_response(response)
                if result:
                    return result
                
                # Empty result but no exception - retry
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                    
            except asyncio.TimeoutError:
                last_error = "Timeout"
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"⏳ Agent invoke timeout, retry {attempt + 1}/{self.max_retries} in {wait_time}s...")
                    await asyncio.sleep(wait_time)
            except Exception as e:
                last_error = str(e)[:50]
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"⚠️ Agent invoke error: {last_error}, retry in {wait_time}s...")
                    await asyncio.sleep(wait_time)
        
        if last_error:
            print(f"❌ Agent invoke failed after {self.max_retries} attempts: {last_error}")
        return {}


# =============================================================================
# SPECIALIZED AGENTS
# =============================================================================

class ResearcherAgent(BaseAgent):
    """Deep company research specialist - Uses Groq (fast API) to save Gemini quota"""
    
    def __init__(self, gemini_service, scraper_service, emit_callback, stop_check=None):
        super().__init__(gemini_service, emit_callback, RESEARCHER_SYSTEM_PROMPT)
        self.scraper = scraper_service
        self.stop_check = stop_check  # Callback to check if stopped
        
        # Initialize Groq service for research (saves Gemini quota)
        self.groq = None
        self.use_groq = settings.GROQ_ENABLED
        if self.use_groq:
            try:
                from ..services.groq_service import get_groq_service
                self.groq = get_groq_service()
                if self.groq.enabled:
                    print("⚡ ResearcherAgent: Using GROQ for research (FREE & FAST)")
                else:
                    print("⚠️ Groq API key not set, will use Gemini")
                    self.use_groq = False
            except Exception as e:
                print(f"⚠️ Groq not available, will use Gemini: {e}")
                self.use_groq = False
        else:
            print("🤖 ResearcherAgent: Using GEMINI for research")
    
    async def research_company(self, company: Dict, product_analysis: Dict) -> Dict:
        """Research a single company - Uses Groq to save Gemini quota"""
        await self.emit(f"🔬 Researcher: Analyzing {company.get('company_name', 'Unknown')}...")
        
        # First, scrape additional data if needed
        enriched = company.copy()
        
        if company.get('website'):
            try:
                scraped = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.scraper.enrich_lead,
                        company.get('website'),
                        company.get('company_name', '')
                    ),
                    timeout=30
                )
                enriched.update(scraped)
            except:
                pass
        
        # Use AI (Groq or Gemini) to extract structured research
        prompt = LEAD_RESEARCH_PROMPT.format(
            company_name=enriched.get('company_name', 'Unknown'),
            website=enriched.get('website', 'N/A'),
            description=enriched.get('description', 'No description available')[:500],
            product_analysis=json.dumps(product_analysis, indent=2)[:1000]
        )
        
        research = {}
        
        # Try Groq first (FREE & FAST), then fallback to Gemini
        if self.use_groq and self.groq and self.groq.enabled:
            try:
                response = await self.groq.generate(prompt)
                research = self.groq.parse_json_response(response)
            except Exception as e:
                print(f"⚠️ Groq failed, falling back to Gemini: {e}")
                research = await self.invoke(prompt)
        else:
            # Use Gemini if Groq not available
            research = await self.invoke(prompt)
        
        # Merge research into enriched data
        if research:
            enriched['ai_research'] = research
            enriched['pain_points'] = research.get('pain_points', [])
            enriched['technology_stack'] = research.get('technology_stack', [])
            enriched['decision_makers'] = research.get('decision_makers', [])
            enriched['research_confidence'] = research.get('research_confidence', 0.5)
            
            # Update contact if found
            if research.get('contact_email') and not enriched.get('email'):
                enriched['email'] = research.get('contact_email')
        
        return enriched
    
    async def research_batch(self, companies: List[Dict], product_analysis: Dict, max_concurrent: int = 5) -> List[Dict]:
        """Research multiple companies in parallel with progress tracking"""
        await self.emit(f"🔬 Researcher: Starting deep research on {len(companies)} companies...")
        
        sem = asyncio.Semaphore(max_concurrent)
        completed = [0]  # Use list for mutable counter in closure
        total = len(companies)
        stopped = [False]  # Track if stopped
        
        async def research_with_sem(company):
            # Check if stopped before processing
            if stopped[0] or (self.stop_check and self.stop_check()):
                stopped[0] = True
                return company  # Return original without processing
                
            async with sem:
                try:
                    result = await asyncio.wait_for(
                        self.research_company(company, product_analysis),
                        timeout=90  # INCREASED from 45s to 90s
                    )
                    completed[0] += 1
                    if completed[0] % 5 == 0 or completed[0] == total:  # Emit every 5 or at end
                        await self.emit(f"📊 Research Progress: {completed[0]}/{total} ({int(completed[0]/total*100)}%)")
                    return result
                except asyncio.TimeoutError:
                    completed[0] += 1
                    # Only timeout, don't skip - return original data for qualification
                    await self.emit(f"⚠️ Slow response for {company.get('company_name', 'Unknown')} - using basic data")
                    return company  # Return original data, still usable
                except Exception as e:
                    completed[0] += 1
                    return company
        
        tasks = [research_with_sem(c) for c in companies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        researched = []
        for result in results:
            if isinstance(result, dict) and result.get('company_name'):
                researched.append(result)
        
        if stopped[0]:
            await self.emit(f"🛑 Research stopped early - processed {len(researched)} companies")
        else:
            await self.emit(f"✅ Researcher: Completed research on {len(researched)} companies")
        return researched


class QualifierAgent(BaseAgent):
    """Lead qualification specialist - Uses ML-only mode to save Gemini quota"""
    
    def __init__(self, gemini_service, ml_scorer, embeddings, emit_callback):
        super().__init__(gemini_service, emit_callback, QUALIFIER_SYSTEM_PROMPT)
        self.ml_scorer = ml_scorer
        self.embeddings = embeddings
        self.qualification_mode = settings.QUALIFICATION_MODE
        
        # Log which mode is being used
        if self.qualification_mode == "ml_only":
            print("🧠 QualifierAgent: Using ML-ONLY mode (NO Gemini API calls)")
        elif self.qualification_mode == "ml_ai":
            print("🤖 QualifierAgent: Using ML + AI mode (Gemini for reasoning)")
        else:
            print("🤖 QualifierAgent: Using AI-ONLY mode (all Gemini)")
    
    async def qualify_lead(self, lead: Dict, product_analysis: Dict) -> Dict:
        """Qualify a single lead - uses ML-only mode by default to save API quota"""
        await self.emit(f"🎯 Qualifier: Scoring {lead.get('company_name', 'Unknown')}...")
        
        qualified = lead.copy()
        
        # ML scoring (always run - no API needed)
        try:
            ml_result = self.ml_scorer.predict(lead, product_analysis)
            qualified['ml_score'] = ml_result.get('score', 0.5)
            qualified['ml_confidence'] = ml_result.get('confidence', 0.5)
            qualified['score_explanation'] = ml_result.get('top_factors', [])
        except Exception as e:
            qualified['ml_score'] = 0.5
            qualified['ml_confidence'] = 0.3
        
        # Semantic similarity scoring (always run - no API needed)
        try:
            ideal = product_analysis.get('ideal_customer_profile', '')
            if isinstance(ideal, dict):
                ideal = ' '.join(str(v) for v in ideal.values() if v)
            
            lead_text = f"{lead.get('company_name', '')} {lead.get('description', '')} {lead.get('industry', '')}"
            similarity = self.embeddings.calculate_similarity(ideal, lead_text)
            qualified['semantic_similarity'] = float(similarity)
        except:
            qualified['semantic_similarity'] = 0.5
        
        # QUALIFICATION MODE: ml_only = skip AI, use ML+Semantic only
        if self.qualification_mode == "ml_only":
            # ML-only scoring (NO API CALLS!)
            qualified['final_score'] = qualified['ml_score'] * 0.5 + qualified['semantic_similarity'] * 0.5
            
            # Determine tier based on final score
            if qualified['final_score'] >= 0.7:
                qualified['qualification_tier'] = 'HOT'
            elif qualified['final_score'] >= 0.5:
                qualified['qualification_tier'] = 'WARM'
            else:
                qualified['qualification_tier'] = 'COLD'
            
            qualified['qualification_reasoning'] = f"ML Score: {qualified['ml_score']:.2f}, Semantic: {qualified['semantic_similarity']:.2f}"
        
        else:
            # AI qualification with reasoning (uses Gemini API)
            prompt = LEAD_QUALIFICATION_PROMPT.format(
                company_research=json.dumps({
                    'company_name': lead.get('company_name'),
                    'industry': lead.get('industry'),
                    'description': lead.get('description', '')[:300],
                    'pain_points': lead.get('pain_points', []),
                    'website': lead.get('website')
                }, indent=2),
                product_analysis=json.dumps(product_analysis, indent=2)[:800]
            )
            
            qualification = await self.invoke(prompt)
            
            if qualification:
                qualified['ai_qualification'] = qualification
                qualified['qualification_tier'] = qualification.get('qualification_tier', 'WARM')
                qualified['qualification_reasoning'] = qualification.get('icp_fit', {}).get('reasoning', '')
                qualified['recommended_approach'] = qualification.get('recommended_approach', '')
                qualified['objections_anticipated'] = qualification.get('objections_anticipated', [])
                
                # Calculate final score with AI
                ai_score = qualification.get('qualification_score', 50) / 100
                qualified['final_score'] = (qualified['ml_score'] * 0.4 + 
                                            qualified['semantic_similarity'] * 0.3 + 
                                            ai_score * 0.3)
            else:
                qualified['final_score'] = qualified['ml_score'] * 0.7 + qualified['semantic_similarity'] * 0.3
        
        return qualified
    
    async def qualify_batch(self, leads: List[Dict], product_analysis: Dict, max_concurrent: int = 5) -> List[Dict]:
        """Qualify multiple leads in parallel with progress tracking"""
        await self.emit(f"🎯 Qualifier: Scoring {len(leads)} leads with ML + AI...")
        
        sem = asyncio.Semaphore(max_concurrent)
        completed = [0]
        total = len(leads)
        
        async def qualify_with_sem(lead):
            async with sem:
                try:
                    result = await asyncio.wait_for(
                        self.qualify_lead(lead, product_analysis),
                        timeout=30
                    )
                    completed[0] += 1
                    score = result.get('final_score', 0) * 100
                    tier = result.get('qualification_tier', 'COLD')
                    await self.emit(f"📊 Qualified {completed[0]}/{total}: {lead.get('company_name', 'Unknown')} = {score:.0f}% ({tier})")
                    return result
                except:
                    completed[0] += 1
                    lead['final_score'] = 0.5
                    lead['qualification_tier'] = 'COLD'
                    return lead
        
        tasks = [qualify_with_sem(l) for l in leads]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        qualified = [r for r in results if isinstance(r, dict) and r.get('company_name')]
        
        # Sort by final score
        qualified.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        
        await self.emit(f"✅ Qualifier: Scored {len(qualified)} leads")
        return qualified


class CopywriterAgent(BaseAgent):
    """Personalized email copywriter"""
    
    def __init__(self, gemini_service, emit_callback, stop_check=None):
        super().__init__(gemini_service, emit_callback, COPYWRITER_SYSTEM_PROMPT)
        self.stop_check = stop_check  # Callback to check if stopped
    
    async def write_email(self, lead: Dict, product_analysis: Dict) -> Dict:
        """Write personalized email variants for a lead"""
        await self.emit(f"✍️ Copywriter: Crafting email for {lead.get('company_name', 'Unknown')}...")
        
        lead_with_email = lead.copy()
        
        prompt = EMAIL_GENERATION_PROMPT.format(
            company_name=lead.get('company_name', 'Unknown'),
            industry=lead.get('industry', 'Unknown'),
            description=lead.get('description', '')[:300],
            decision_maker=lead.get('decision_maker_name', 'Decision Maker'),
            pain_points=', '.join(lead.get('pain_points', [])[:3]) or 'business growth',
            qualification=lead.get('qualification_tier', 'WARM'),
            product_analysis=json.dumps(product_analysis, indent=2)[:600]
        )
        
        email_result = await self.invoke(prompt)
        
        if email_result:
            lead_with_email['email_variants'] = email_result
            
            # Select recommended variant
            recommended = email_result.get('recommended_variant', 1)
            variant_key = f'email_variant_{recommended}'
            
            if variant_key in email_result:
                selected = email_result[variant_key]
                lead_with_email['email_subject'] = selected.get('subject', 'Partnership Opportunity')
                lead_with_email['email_body'] = selected.get('body', '')
                lead_with_email['email_cta'] = selected.get('cta', '')
            else:
                # Fallback to first variant
                for key in ['email_variant_1', 'email_variant_2', 'email_variant_3']:
                    if key in email_result:
                        selected = email_result[key]
                        lead_with_email['email_subject'] = selected.get('subject', 'Partnership Opportunity')
                        lead_with_email['email_body'] = selected.get('body', '')
                        break
        
        return lead_with_email
    
    async def write_emails_batch(self, leads: List[Dict], product_analysis: Dict, max_concurrent: int = 3) -> List[Dict]:
        """Write emails for multiple leads in parallel with retry logic"""
        await self.emit(f"✍️ Copywriter: Writing emails for {len(leads)} leads...")
        
        sem = asyncio.Semaphore(max_concurrent)
        stopped = [False]
        completed = [0]
        total = len(leads)
        failed_leads = []  # Track leads that failed for retry
        
        async def write_with_retry(lead, max_retries: int = 2):
            """Write email with retry logic"""
            # Check if stopped before processing
            if stopped[0] or (self.stop_check and self.stop_check()):
                stopped[0] = True
                return None
            
            for attempt in range(max_retries + 1):
                async with sem:
                    try:
                        result = await asyncio.wait_for(
                            self.write_email(lead, product_analysis),
                            timeout=90  # INCREASED: 90s timeout per email
                        )
                        completed[0] += 1
                        if attempt > 0:
                            await self.emit(f"✅ Retry success for {lead.get('company_name', 'Unknown')}")
                        return result
                    except asyncio.TimeoutError:
                        if attempt < max_retries:
                            wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s
                            await self.emit(f"⏳ Retry {attempt + 1}/{max_retries} for {lead.get('company_name', 'Unknown')} in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                        else:
                            await self.emit(f"⚠️ Email timeout for {lead.get('company_name', 'Unknown')} after {max_retries + 1} attempts")
                            completed[0] += 1
                            return None
                    except Exception as e:
                        if attempt < max_retries:
                            await asyncio.sleep(1)
                        else:
                            completed[0] += 1
                            await self.emit(f"⚠️ Email failed for {lead.get('company_name', 'Unknown')}: {str(e)[:30]}")
                            return None
            return None
        
        # Process all leads with retry
        tasks = [write_with_retry(l) for l in leads]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        with_emails = [r for r in results if isinstance(r, dict) and r.get('email_body')]
        
        if stopped[0]:
            await self.emit(f"🛑 Email writing stopped early - generated {len(with_emails)} emails")
        else:
            success_rate = len(with_emails) / len(leads) * 100 if leads else 0
            await self.emit(f"✅ Copywriter: Generated {len(with_emails)}/{len(leads)} emails ({success_rate:.0f}% success)")
        return with_emails


# =============================================================================
# MULTI-AGENT ORCHESTRATOR
# =============================================================================

class MultiAgentOrchestrator:
    """Orchestrates the multi-agent workflow using LangGraph"""
    
    def __init__(self, campaign: Dict, gemini_service, scraper_service, 
                 ml_scorer, embedding_service, email_service, emit_callback):
        self.campaign = campaign
        self.emit = emit_callback
        self._stopped = False  # Track if campaign was stopped
        
        # Initialize specialized agents WITH stop_check callback
        self.researcher = ResearcherAgent(
            gemini_service, scraper_service, emit_callback, 
            stop_check=self.check_if_stopped  # Pass stop check callback
        )
        self.qualifier = QualifierAgent(gemini_service, ml_scorer, embedding_service, emit_callback)
        self.copywriter = CopywriterAgent(
            gemini_service, emit_callback,
            stop_check=self.check_if_stopped  # Pass stop check callback
        )
        self.email_service = email_service
        self.gemini = gemini_service
        
        # Build workflow
        self.workflow = self._build_workflow()
    
    def check_if_stopped(self) -> bool:
        """Check if campaign has been stopped in database"""
        if self._stopped:
            return True
        try:
            from app.models.database import SessionLocal
            from app.models.tables import Campaign
            db = SessionLocal()
            campaign = db.query(Campaign).filter(Campaign.id == self.campaign.get('id')).first()
            if campaign and campaign.status == "stopped":
                self._stopped = True
                db.close()
                return True
            db.close()
            return False
        except Exception as e:
            print(f"Error checking stop status: {e}")
            return False
    
    async def _check_stopped_and_emit(self) -> bool:
        """Check if stopped and emit message if so"""
        if self.check_if_stopped():
            await self.emit("🛑 Campaign stopped by user - halting workflow")
            return True
        return False
    
    def _build_workflow(self) -> StateGraph:
        """Build the multi-agent workflow graph"""
        workflow = StateGraph(MultiAgentState)
        
        # Add nodes for each phase
        workflow.add_node("analyze_product", self._analyze_product_node)
        workflow.add_node("search_leads", self._search_leads_node)
        workflow.add_node("research_phase", self._research_phase_node)
        workflow.add_node("qualify_phase", self._qualify_phase_node)
        workflow.add_node("copywrite_phase", self._copywrite_phase_node)
        workflow.add_node("save_leads", self._save_leads_node)
        workflow.add_node("send_emails", self._send_emails_node)
        
        # Define edges
        workflow.set_entry_point("analyze_product")
        workflow.add_edge("analyze_product", "search_leads")
        workflow.add_edge("search_leads", "research_phase")
        workflow.add_edge("research_phase", "qualify_phase")
        workflow.add_edge("qualify_phase", "copywrite_phase")
        workflow.add_edge("copywrite_phase", "save_leads")
        
        # Conditional: send emails only if we have quality leads
        workflow.add_conditional_edges(
            "save_leads",
            lambda state: "send" if len(state.get("leads_with_emails", [])) >= 3 else "skip",
            {"send": "send_emails", "skip": END}
        )
        
        workflow.add_edge("send_emails", END)
        
        return workflow.compile(checkpointer=MemorySaver())
    
    async def _analyze_product_node(self, state: MultiAgentState) -> Dict:
        """Analyze the product for targeting"""
        await self.emit("🤖 Multi-Agent System: Analyzing product...")
        await self.emit("🔬 Using Researcher + Qualifier + Copywriter agents")
        
        campaign = state["campaign"]
        
        prompt = PRODUCT_ANALYSIS_PROMPT.format(
            product_description=campaign.get('product_description', ''),
            target_industry=campaign.get('target_industry', 'B2B'),
            target_audience=campaign.get('target_audience', 'decision makers')
        )
        
        # Use researcher's Gemini for product analysis
        response = await asyncio.wait_for(
            self.gemini.generate(prompt),
            timeout=60
        )
        
        analysis = self.gemini.parse_json_response(response) or {
            "keywords": ["solution", "platform"],
            "target_industries": [campaign.get('target_industry', 'technology')],
            "pain_points": ["efficiency", "growth"]
        }
        
        await self.emit(f"✅ Product analyzed: {len(analysis.get('keywords', []))} keywords identified")
        
        return {"product_analysis": analysis, "current_phase": "analyze", "progress": 10.0}
    
    async def _search_leads_node(self, state: MultiAgentState) -> Dict:
        """Search for potential leads"""
        await self.emit("🔍 Multi-Agent: Searching for leads...")
        
        from app.services.search_service import SearchService
        from urllib.parse import urlparse
        
        search_service = SearchService()
        campaign = state["campaign"]
        product_analysis = state["product_analysis"]
        
        # Generate search queries from keywords
        keywords = product_analysis.get("keywords", ["B2B", "solution", "platform"])
        industries = product_analysis.get("target_industries", [campaign.get("target_industry", "technology")])
        
        # Blacklist domains - expanded list
        ignored_domains = [
            "medium.com", "wikipedia.org", "facebook.com", "twitter.com", 
            "youtube.com", "yelp.com", "clutch.co", "capterra.com", "g2.com",
            "linkedin.com", "instagram.com", "pinterest.com", "reddit.com",
            "crunchbase.com", "bloomberg.com", "forbes.com", "techcrunch.com",
            "glassdoor.com", "indeed.com", "quora.com", "github.com"
        ]
        
        # Search for leads - EXPANDED
        all_leads = []
        seen_domains = set()
        total_queries = min(len(industries), 3) * min(len(keywords), 5)
        query_num = 0
        
        await self.emit(f"🔍 Running {total_queries} search queries...")
        
        for industry in industries[:3]:  # INCREASED: 3 industries
            for keyword in keywords[:5]:  # INCREASED: 5 keywords
                query = f"{keyword} {industry} companies"
                query_num += 1
                await self.emit(f"🔍 Query {query_num}/{total_queries}: {query[:40]}...")
                
                try:
                    results = await search_service.search(query, num_results=settings.MAX_SEARCH_RESULTS)  # CONFIGURABLE
                    
                    for result in results:
                        url = result.get("link", "")
                        if not url:
                            continue
                            
                        domain = urlparse(url).netloc
                        if domain in seen_domains:
                            continue
                        if any(ignored in url.lower() for ignored in ignored_domains):
                            continue
                            
                        seen_domains.add(domain)
                        
                        # Extract company name
                        company_name = self.researcher.scraper.extract_company_name_from_url(url)
                        
                        lead = {
                            "company_name": company_name,
                            "website": url,
                            "description": result.get("snippet", ""),
                            "industry": industry
                        }
                        all_leads.append(lead)
                        
                except Exception as e:
                    print(f"Search error: {e}")
                    continue
        
        await self.emit(f"✅ Found {len(all_leads)} unique potential leads")
        
        return {"raw_leads": all_leads, "current_phase": "search", "progress": 25.0}
    
    async def _research_phase_node(self, state: MultiAgentState) -> Dict:
        """Research phase using Researcher Agent"""
        await self.emit("🔬 [RESEARCHER AGENT] Starting deep company research...")
        
        raw_leads = state["raw_leads"][:settings.MAX_LEADS_TO_RESEARCH]  # CONFIGURABLE via env
        product_analysis = state["product_analysis"]
        
        await self.emit(f"🔬 Processing {len(raw_leads)} leads for enrichment (max: {settings.MAX_LEADS_TO_RESEARCH})...")
        
        researched = await self.researcher.research_batch(raw_leads, product_analysis)
        
        await self.emit(f"✅ Research complete: {len(researched)} leads enriched")
        
        return {"researched_leads": researched, "current_phase": "research", "progress": 45.0}
    
    async def _qualify_phase_node(self, state: MultiAgentState) -> Dict:
        """Qualification phase using Qualifier Agent"""
        await self.emit("🎯 [QUALIFIER AGENT] Scoring and qualifying leads...")
        
        researched_leads = state["researched_leads"]
        product_analysis = state["product_analysis"]
        
        qualified = await self.qualifier.qualify_batch(researched_leads, product_analysis)
        
        # Calculate tier breakdown
        hot_leads = [l for l in qualified if l.get('final_score', 0) >= 0.7]
        warm_leads = [l for l in qualified if 0.5 <= l.get('final_score', 0) < 0.7]
        cold_leads = [l for l in qualified if 0.4 <= l.get('final_score', 0) < 0.5]
        
        await self.emit(f"📊 Lead Breakdown: 🔥 HOT: {len(hot_leads)} | 🟡 WARM: {len(warm_leads)} | 🔵 COLD: {len(cold_leads)}")
        
        # Filter to leads with score >= 0.4 (lowered threshold to include more leads)
        top_leads = [l for l in qualified if l.get('final_score', 0) >= 0.4][:settings.MAX_LEADS_TO_QUALIFY]  # CONFIGURABLE
        
        await self.emit(f"✅ Qualifier: {len(top_leads)} leads passed qualification (score >= 40%)")
        
        return {"qualified_leads": top_leads, "current_phase": "qualify", "progress": 65.0}
    
    async def _copywrite_phase_node(self, state: MultiAgentState) -> Dict:
        """Copywriting phase using Copywriter Agent"""
        await self.emit("✍️ [COPYWRITER AGENT] Generating personalized emails...")
        
        qualified_leads = state["qualified_leads"]
        product_analysis = state["product_analysis"]
        
        # Only write emails for leads with email addresses
        leads_with_contact = [l for l in qualified_leads if l.get('email')]
        
        if not leads_with_contact:
            await self.emit("⚠️ No leads with email addresses found")
            return {"leads_with_emails": [], "current_phase": "copywrite", "progress": 80.0}
        
        leads_with_emails = await self.copywriter.write_emails_batch(
            leads_with_contact[:settings.MAX_EMAILS_TO_GENERATE],  # CONFIGURABLE via env
            product_analysis
        )
        
        return {"leads_with_emails": leads_with_emails, "current_phase": "copywrite", "progress": 80.0}
    
    async def _save_leads_node(self, state: MultiAgentState) -> Dict:
        """Save leads to database"""
        await self.emit("💾 Saving leads to database...")
        
        try:
            from app.models.database import SessionLocal
            from app.models.tables import Lead
            
            db = SessionLocal()
            campaign_id = state["campaign_id"]
            
            # Save all qualified leads
            leads_to_save = state.get("qualified_leads", [])
            saved_count = 0
            
            for lead_data in leads_to_save:
                try:
                    existing = db.query(Lead).filter(
                        Lead.campaign_id == campaign_id,
                        Lead.company_name == lead_data.get("company_name")
                    ).first()
                    
                    if existing:
                        continue
                    
                    lead = Lead(
                        campaign_id=campaign_id,
                        company_name=lead_data.get("company_name", "Unknown"),
                        industry=lead_data.get("industry"),
                        website=lead_data.get("website"),
                        description=lead_data.get("description", "")[:1000] if lead_data.get("description") else None,
                        email=lead_data.get("email"),
                        ml_score=lead_data.get("final_score") or lead_data.get("ml_score"),
                        ml_confidence=lead_data.get("ml_confidence"),
                        score_explanation=lead_data.get("score_explanation"),
                        status="new"
                    )
                    db.add(lead)
                    saved_count += 1
                except Exception as e:
                    print(f"Error saving lead: {e}")
            
            db.commit()
            db.close()
            
            await self.emit(f"✅ Saved {saved_count} leads to database")
            
        except Exception as e:
            await self.emit(f"⚠️ Error saving leads: {str(e)[:50]}")
        
        return {"current_phase": "save", "progress": 90.0}
    
    async def _send_emails_node(self, state: MultiAgentState) -> Dict:
        """Send emails to qualified leads"""
        await self.emit("📧 [MULTI-AGENT] Sending personalized emails...")
        
        leads = state["leads_with_emails"]
        sent_count = 0
        
        for lead in leads:
            try:
                if not lead.get('email') or not lead.get('email_body'):
                    continue
                
                subject = lead.get('email_subject', 'Partnership Opportunity')
                body = lead.get('email_body', '')
                
                sent = await self.email_service.send_email(
                    to_email=lead['email'],
                    subject=subject,
                    body=body
                )
                
                if sent:
                    # Save email to database
                    from app.models.database import SessionLocal
                    from app.models.tables import Lead, Email
                    from datetime import datetime
                    
                    db = SessionLocal()
                    db_lead = db.query(Lead).filter(
                        Lead.campaign_id == state["campaign_id"],
                        Lead.company_name == lead.get("company_name")
                    ).first()
                    
                    if db_lead:
                        email_record = Email(
                            lead_id=db_lead.id,
                            subject=subject,
                            body=body,
                            status="sent",
                            sent_at=datetime.utcnow()
                        )
                        db.add(email_record)
                        db.commit()
                    db.close()
                    
                    sent_count += 1
                    await self.emit(f"✅ Email sent to {lead.get('company_name')}")
                    
            except Exception as e:
                print(f"Email error: {e}")
        
        await self.emit(f"🎉 Multi-Agent Complete! Sent {sent_count} personalized emails")
        
        return {"emails_sent": sent_count, "current_phase": "complete", "progress": 100.0}
    
    async def run(self) -> Dict:
        """Run the multi-agent workflow"""
        await self.emit("🚀 Multi-Agent System: ACTIVATED")
        await self.emit("🤖 Agents: Researcher 🔬 | Qualifier 🎯 | Copywriter ✍️")
        
        try:
            initial_state: MultiAgentState = {
                "campaign_id": str(self.campaign.get("id")),
                "campaign": self.campaign,
                "current_phase": "start",
                "progress": 0.0,
                "product_analysis": {},
                "raw_leads": [],
                "researched_leads": [],
                "qualified_leads": [],
                "leads_with_emails": [],
                "agent_outputs": [],
                "errors": [],
                "emails_sent": 0
            }
            
            config = {"configurable": {"thread_id": str(self.campaign.get("id"))}}
            final_state = await self.workflow.ainvoke(initial_state, config)
            
            # Update campaign status
            try:
                from app.models.database import SessionLocal
                from app.models.tables import Campaign
                
                db = SessionLocal()
                camp = db.query(Campaign).filter(Campaign.id == self.campaign.get('id')).first()
                if camp:
                    camp.status = "completed"
                    db.commit()
                db.close()
            except:
                pass
            
            return {
                "success": True,
                "emails_sent": final_state.get("emails_sent", 0),
                "leads_qualified": len(final_state.get("qualified_leads", []))
            }
            
        except Exception as e:
            await self.emit(f"❌ Multi-Agent Error: {str(e)}")
            return {"success": False, "error": str(e)}


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_multi_agent_system(campaign: Dict, gemini_service, scraper_service,
                              ml_scorer, embedding_service, email_service,
                              emit_callback) -> MultiAgentOrchestrator:
    """Factory function to create a multi-agent orchestrator"""
    return MultiAgentOrchestrator(
        campaign=campaign,
        gemini_service=gemini_service,
        scraper_service=scraper_service,
        ml_scorer=ml_scorer,
        embedding_service=embedding_service,
        email_service=email_service,
        emit_callback=emit_callback
    )
