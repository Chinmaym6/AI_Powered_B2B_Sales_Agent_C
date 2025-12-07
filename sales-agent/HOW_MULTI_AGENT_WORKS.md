# 🔄 How Multi-Agent System Works

## Complete Flow & Prompts Documentation

---

## Table of Contents

1. [System Activation](#1-system-activation)
2. [Multi-Agent vs Single Agent Decision](#2-multi-agent-vs-single-agent-decision)
3. [Complete Workflow Flow](#3-complete-workflow-flow)
4. [Phase 1: Product Analysis](#phase-1-product-analysis)
5. [Phase 2: Lead Search](#phase-2-lead-search)
6. [Phase 3: Research (Researcher Agent)](#phase-3-research-researcher-agent)
7. [Phase 4: Qualification (Qualifier Agent)](#phase-4-qualification-qualifier-agent)
8. [Phase 5: Email Generation (Copywriter Agent)](#phase-5-email-generation-copywriter-agent)
9. [Phase 6: Save to Database](#phase-6-save-to-database)
10. [Phase 7: Send Emails](#phase-7-send-emails)
11. [Complete Prompt Reference](#complete-prompt-reference)
12. [Data Transformation Flow](#data-transformation-flow)

---

## 1. System Activation

### How Multi-Agent Mode Gets Enabled

When a campaign starts, the system checks which mode to use:

```python
# File: app/api/routes/campaigns.py

# Check if multi-agent mode is enabled
import os
use_multi_agent = os.getenv("USE_MULTI_AGENT", "true").lower() == "true"

if use_multi_agent:
    # Use Multi-Agent Collaborative System
    from ..core.multi_agent import create_multi_agent_system
    
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
    # Use standard single LangGraph agent
    agent = AutonomousAgent(campaign_dict, emit_update)

result = await agent.run()
```

### Environment Configuration

In your `.env` file:
```bash
USE_MULTI_AGENT=true   # Activates multi-agent system
USE_MULTI_AGENT=false  # Falls back to single agent
```

---

## 2. Multi-Agent vs Single Agent Decision

```
┌─────────────────────────────────────────────────────────────┐
│                    Campaign Start                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │ Check USE_MULTI_AGENT │
                │    Environment Var    │
                └───────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
    ┌───────────────┐               ┌───────────────┐
    │   true        │               │   false       │
    └───────────────┘               └───────────────┘
            │                               │
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│ MultiAgentOrchestrator│       │   AutonomousAgent     │
│ ├── ResearcherAgent   │       │   (Single LangGraph)  │
│ ├── QualifierAgent    │       └───────────────────────┘
│ └── CopywriterAgent   │
└───────────────────────┘
```

---

## 3. Complete Workflow Flow

### Visual Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         MULTI-AGENT WORKFLOW                                 │
└──────────────────────────────────────────────────────────────────────────────┘

[USER CREATES CAMPAIGN]
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: ANALYZE PRODUCT                                                   │
│  ─────────────────────────                                                  │
│  • Extract keywords from product description                                │
│  • Identify target industries                                               │
│  • Define Ideal Customer Profile (ICP)                                      │
│  • Generate search queries                                                  │
│                                                                             │
│  Input:  Campaign { product_description, target_industry, target_audience } │
│  Output: ProductAnalysis { keywords, target_industries, pain_points, icp }  │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: SEARCH LEADS                                                      │
│  ────────────────────                                                       │
│  • Generate search queries from keywords + industries                       │
│  • Search web for matching companies                                        │
│  • Extract basic company info (name, website, description)                  │
│  • Deduplicate by company name                                              │
│                                                                             │
│  Input:  ProductAnalysis { keywords, target_industries }                    │
│  Output: raw_leads [10-20 leads with basic info]                            │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: RESEARCH (🔬 RESEARCHER AGENT)                                    │
│  ────────────────────────────────────────                                   │
│  • Deep dive into each company                                              │
│  • Scrape website for additional data                                       │
│  • AI extraction of pain points, tech stack                                 │
│  • Find decision makers and contacts                                        │
│  • Parallel processing (5 concurrent)                                       │
│                                                                             │
│  Input:  raw_leads + ProductAnalysis                                        │
│  Output: researched_leads [enriched with intelligence]                      │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 4: QUALIFY (🎯 QUALIFIER AGENT)                                      │
│  ─────────────────────────────────────                                      │
│  • ML scoring with XGBoost                                                  │
│  • Semantic similarity with embeddings                                      │
│  • AI qualification with detailed reasoning                                 │
│  • Calculate final score (ML 40% + Semantic 30% + AI 30%)                   │
│  • Filter to top leads (score >= 0.5)                                       │
│  • Parallel processing (5 concurrent)                                       │
│                                                                             │
│  Input:  researched_leads + ProductAnalysis                                 │
│  Output: qualified_leads [scored with reasoning, top 15]                    │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 5: COPYWRITE (✍️ COPYWRITER AGENT)                                   │
│  ────────────────────────────────────────                                   │
│  • Generate 3 personalized email variants per lead                          │
│  • Use pain points and company context                                      │
│  • Optimize subject lines and CTAs                                          │
│  • Select recommended variant                                               │
│  • Parallel processing (3 concurrent)                                       │
│                                                                             │
│  Input:  qualified_leads (with email) + ProductAnalysis                     │
│  Output: leads_with_emails [3 variants per lead]                            │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 6: SAVE TO DATABASE                                                  │
│  ────────────────────────                                                   │
│  • Persist all qualified leads to Lead table                                │
│  • Store ML scores, confidence, explanation                                 │
│  • Check for duplicates                                                     │
│                                                                             │
│  Input:  qualified_leads                                                    │
│  Output: Database records created                                           │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CONDITIONAL: ENOUGH QUALITY LEADS?                                         │
│  ─────────────────────────────────                                          │
│                                                                             │
│  IF leads_with_emails >= 3:  → Continue to Send Emails                      │
│  ELSE:                       → Skip to END                                  │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 7: SEND EMAILS                                                       │
│  ───────────────────                                                        │
│  • Send recommended email variant to each lead                              │
│  • Record in Email table with status="sent"                                 │
│  • Emit progress updates via WebSocket                                      │
│                                                                             │
│  Input:  leads_with_emails                                                  │
│  Output: emails_sent count                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  COMPLETE                                                                   │
│  ────────                                                                   │
│  • Update campaign status to "completed"                                    │
│  • Return final results                                                     │
│                                                                             │
│  Output: { success: true, emails_sent: N, leads_qualified: M }              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Product Analysis

### What Happens

1. Receive campaign configuration from user
2. Send product description to Gemini AI
3. Extract keywords, industries, pain points
4. Generate Ideal Customer Profile

### Code Flow

```python
async def _analyze_product_node(self, state: MultiAgentState) -> Dict:
    await self.emit("🤖 Multi-Agent System: Analyzing product...")
    
    campaign = state["campaign"]
    
    prompt = PRODUCT_ANALYSIS_PROMPT.format(
        product_description=campaign.get('product_description', ''),
        target_industry=campaign.get('target_industry', 'B2B'),
        target_audience=campaign.get('target_audience', 'decision makers')
    )
    
    response = await asyncio.to_thread(self.gemini.generate, prompt)
    analysis = self.gemini.parse_json_response(response)
    
    return {"product_analysis": analysis, "progress": 10.0}
```

### Prompt Used

```
Analyze this product/service for B2B sales targeting:

PRODUCT: {product_description}
TARGET INDUSTRY: {target_industry}
TARGET AUDIENCE: {target_audience}

Provide comprehensive analysis in JSON format:
{
    "product_summary": "One-sentence value prop",
    "core_benefits": ["Benefit 1", "Benefit 2", "Benefit 3"],
    "pain_points_solved": ["Pain 1", "Pain 2", "Pain 3"],
    "ideal_customer_profile": {
        "industries": ["Industry 1", "Industry 2"],
        "company_sizes": ["Size range"],
        "job_titles": ["Title 1", "Title 2"],
        "geographic_focus": "Regions"
    },
    "competitive_advantages": ["Advantage 1", "Advantage 2"],
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "target_industries": ["Industry 1", "Industry 2"],
    "objection_handlers": {
        "price_concern": "Response",
        "competitor_comparison": "Response"
    },
    "social_proof_opportunities": ["Type 1", "Type 2"],
    "recommended_email_hooks": ["Hook 1", "Hook 2", "Hook 3"]
}
```

### Output Example

```json
{
    "product_summary": "AI-powered sales automation that finds and engages leads automatically",
    "keywords": ["sales automation", "AI sales", "lead generation", "B2B outreach"],
    "target_industries": ["Technology", "SaaS", "Marketing Agencies"],
    "pain_points_solved": ["Manual prospecting", "Low conversion rates", "Time-consuming outreach"],
    "ideal_customer_profile": {
        "industries": ["SaaS", "Technology"],
        "company_sizes": ["11-50", "51-200"],
        "job_titles": ["VP Sales", "Sales Director", "Head of Growth"]
    }
}
```

---

## Phase 2: Lead Search

### What Happens

1. Generate search queries from keywords + industries
2. Call search API to find companies
3. Extract basic company information
4. Deduplicate by company name

### Code Flow

```python
async def _search_leads_node(self, state: MultiAgentState) -> Dict:
    await self.emit("🔍 Multi-Agent: Searching for leads...")
    
    product_analysis = state["product_analysis"]
    keywords = product_analysis.get("keywords", ["B2B", "solution"])
    industries = product_analysis.get("target_industries", ["technology"])
    
    all_leads = []
    for industry in industries[:2]:
        for keyword in keywords[:3]:
            query = f"{keyword} {industry} companies"
            leads = await search_and_scrape_leads(query, max_results=5)
            all_leads.extend(leads)
    
    # Deduplicate
    seen = set()
    unique_leads = []
    for lead in all_leads:
        name = lead.get('company_name', '').lower()
        if name and name not in seen:
            seen.add(name)
            unique_leads.append(lead)
    
    return {"raw_leads": unique_leads, "progress": 25.0}
```

### Output Example

```json
[
    {
        "company_name": "TechCorp",
        "website": "https://techcorp.com",
        "description": "Enterprise software solutions",
        "industry": "Technology"
    },
    {
        "company_name": "GrowthHub",
        "website": "https://growthhub.io",
        "description": "Marketing automation platform",
        "industry": "SaaS"
    }
]
```

---

## Phase 3: Research (Researcher Agent)

### What Happens

1. **Researcher Agent** receives raw leads
2. Scrapes each company website for additional data
3. Uses AI to extract structured intelligence
4. Runs in parallel (5 concurrent max)

### Code Flow

```python
class ResearcherAgent(BaseAgent):
    
    async def research_company(self, company: Dict, product_analysis: Dict) -> Dict:
        await self.emit(f"🔬 Researcher: Analyzing {company.get('company_name')}...")
        
        enriched = company.copy()
        
        # Step 1: Scrape website
        if company.get('website'):
            scraped = await self.scraper.enrich_lead(
                company.get('website'),
                company.get('company_name', '')
            )
            enriched.update(scraped)
        
        # Step 2: AI extraction
        prompt = LEAD_RESEARCH_PROMPT.format(
            company_name=enriched.get('company_name'),
            website=enriched.get('website'),
            description=enriched.get('description', '')[:500],
            product_analysis=json.dumps(product_analysis)[:1000]
        )
        
        research = await self.invoke(prompt)  # Uses RESEARCHER_SYSTEM_PROMPT
        
        # Step 3: Merge results
        if research:
            enriched['pain_points'] = research.get('pain_points', [])
            enriched['technology_stack'] = research.get('technology_stack', [])
            enriched['decision_makers'] = research.get('decision_makers', [])
            enriched['research_confidence'] = research.get('research_confidence', 0.5)
        
        return enriched
```

### Full Researcher System Prompt

```
You are an elite B2B company research analyst with 15+ years of experience 
in market intelligence.

YOUR MISSION: Extract the most valuable, actionable intelligence about 
companies that will help qualify them as sales leads.

RESEARCH METHODOLOGY:
1. Company Overview: Name, industry, size, headquarters, founding year
2. Business Model: What they sell, who they serve, revenue model
3. Technology Stack: Tools/platforms they use (look for integration opportunities)
4. Pain Points: Challenges they might face based on their business
5. Decision Makers: Key executives, their roles, LinkedIn profiles
6. Recent News: Funding, expansions, new products, challenges
7. Contact Info: Verified email patterns, social media presence

OUTPUT FORMAT (JSON):
{
    "company_name": "Exact company name",
    "industry": "Primary industry",
    "sub_industry": "Specific niche",
    "company_size": "1-10 / 11-50 / 51-200 / 201-500 / 500+",
    "headquarters": "City, Country",
    "website": "https://...",
    "business_model": "Brief description of how they make money",
    "technology_stack": ["Tool1", "Tool2"],
    "pain_points": ["Pain point 1", "Pain point 2"],
    "decision_makers": [
        {"name": "John Doe", "title": "CEO", "linkedin": "url"}
    ],
    "contact_email": "best email found or pattern like first@company.com",
    "recent_news": "Any relevant recent developments",
    "research_confidence": 0.0-1.0,
    "notes": "Any additional valuable insights"
}

QUALITY STANDARDS:
- Verify information from multiple sources when possible
- Flag uncertain information with lower confidence
- Prioritize actionable intelligence over generic facts
- Focus on information that helps qualify the lead
```

### Lead Research Task Prompt

```
Research this company for B2B sales opportunity:

COMPANY: {company_name}
WEBSITE: {website}
RAW DESCRIPTION: {description}

PRODUCT CONTEXT:
{product_analysis}

Research thoroughly and extract actionable intelligence for sales outreach.
Return ONLY valid JSON matching the research format specified.
```

### Output Example

```json
{
    "company_name": "TechCorp",
    "industry": "Technology",
    "company_size": "51-200",
    "business_model": "B2B SaaS platform for project management",
    "technology_stack": ["AWS", "React", "Salesforce"],
    "pain_points": ["Manual reporting", "Data silos", "Scaling challenges"],
    "decision_makers": [
        {"name": "Jane Smith", "title": "VP Engineering", "linkedin": "..."}
    ],
    "contact_email": "jane@techcorp.com",
    "research_confidence": 0.85
}
```

---

## Phase 4: Qualification (Qualifier Agent)

### What Happens

1. **Qualifier Agent** receives researched leads
2. Runs ML scoring (XGBoost)
3. Calculates semantic similarity with embeddings
4. Uses AI for detailed qualification reasoning
5. Computes final score: `ML(40%) + Semantic(30%) + AI(30%)`
6. Filters to leads with score >= 0.5

### Code Flow

```python
class QualifierAgent(BaseAgent):
    
    async def qualify_lead(self, lead: Dict, product_analysis: Dict) -> Dict:
        await self.emit(f"🎯 Qualifier: Scoring {lead.get('company_name')}...")
        
        qualified = lead.copy()
        
        # Step 1: ML Scoring
        ml_result = self.ml_scorer.predict(lead, product_analysis)
        qualified['ml_score'] = ml_result.get('score', 0.5)
        qualified['ml_confidence'] = ml_result.get('confidence', 0.5)
        qualified['score_explanation'] = ml_result.get('top_factors', [])
        
        # Step 2: Semantic Similarity
        ideal = product_analysis.get('ideal_customer_profile', '')
        lead_text = f"{lead.get('company_name')} {lead.get('description')} {lead.get('industry')}"
        similarity = self.embeddings.calculate_similarity(ideal, lead_text)
        qualified['semantic_similarity'] = float(similarity)
        
        # Step 3: AI Qualification
        prompt = LEAD_QUALIFICATION_PROMPT.format(
            company_research=json.dumps(lead),
            product_analysis=json.dumps(product_analysis)
        )
        qualification = await self.invoke(prompt)  # Uses QUALIFIER_SYSTEM_PROMPT
        
        if qualification:
            qualified['qualification_tier'] = qualification.get('qualification_tier', 'WARM')
            qualified['qualification_reasoning'] = qualification.get('icp_fit', {}).get('reasoning', '')
            qualified['recommended_approach'] = qualification.get('recommended_approach', '')
            qualified['objections_anticipated'] = qualification.get('objections_anticipated', [])
            
            # Final score calculation
            ai_score = qualification.get('qualification_score', 50) / 100
            qualified['final_score'] = (
                qualified['ml_score'] * 0.4 + 
                qualified['semantic_similarity'] * 0.3 + 
                ai_score * 0.3
            )
        
        return qualified
```

### Full Qualifier System Prompt

```
You are a senior B2B lead qualification specialist with expertise in 
sales pipeline optimization.

YOUR MISSION: Evaluate leads against the Ideal Customer Profile (ICP) 
and provide detailed qualification reasoning.

QUALIFICATION FRAMEWORK:

1. ICP FIT ANALYSIS (40% weight):
   - Industry match
   - Company size match
   - Geographic fit
   - Technology alignment

2. PAIN POINT ALIGNMENT (30% weight):
   - Do they have problems our product solves?
   - How urgent are these pain points?
   - Are they actively seeking solutions?

3. BUYING SIGNALS (20% weight):
   - Recent funding (budget available)
   - Hiring in relevant areas
   - Technology investments
   - Competitive pressure

4. ACCESSIBILITY (10% weight):
   - Contact information quality
   - Decision maker identified
   - LinkedIn presence

OUTPUT FORMAT (JSON):
{
    "company_name": "Name",
    "qualification_score": 0-100,
    "qualification_tier": "HOT / WARM / COLD / DISQUALIFY",
    "icp_fit": {
        "score": 0-100,
        "reasoning": "Why they fit or don't fit ICP"
    },
    "pain_point_alignment": {
        "score": 0-100,
        "identified_pains": ["Pain 1", "Pain 2"],
        "reasoning": "How our product addresses their needs"
    },
    "buying_signals": {
        "score": 0-100,
        "signals_found": ["Signal 1", "Signal 2"],
        "reasoning": "Evidence of buying intent"
    },
    "objections_anticipated": ["Possible objection 1", "Possible objection 2"],
    "recommended_approach": "Best angle to approach this lead",
    "priority_rank": 1-10,
    "confidence": 0.0-1.0
}

SCORING GUIDE:
- 80-100: HOT - High priority, immediate outreach
- 60-79: WARM - Good fit, worth pursuing
- 40-59: COLD - Needs nurturing, lower priority
- 0-39: DISQUALIFY - Not a fit, save resources
```

### Lead Qualification Task Prompt

```
Qualify this lead against our Ideal Customer Profile:

COMPANY RESEARCH:
{company_research}

PRODUCT/ICP CONTEXT:
{product_analysis}

Score and qualify this lead with detailed reasoning.
Return ONLY valid JSON matching the qualification format specified.
```

### Output Example

```json
{
    "company_name": "TechCorp",
    "final_score": 0.82,
    "qualification_tier": "HOT",
    "ml_score": 0.85,
    "ml_confidence": 0.78,
    "semantic_similarity": 0.79,
    "icp_fit": {
        "score": 90,
        "reasoning": "Perfect industry match, company size in sweet spot"
    },
    "pain_point_alignment": {
        "score": 85,
        "identified_pains": ["Manual reporting", "Data silos"],
        "reasoning": "They clearly struggle with automation"
    },
    "objections_anticipated": ["Already using competitor", "Budget constraints"],
    "recommended_approach": "Lead with efficiency gains and ROI"
}
```

---

## Phase 5: Email Generation (Copywriter Agent)

### What Happens

1. **Copywriter Agent** receives qualified leads (with emails)
2. Generates 3 email variants per lead:
   - Variant 1: INSIGHT-LED (thought leadership)
   - Variant 2: DIRECT-PITCH (clear value prop)
   - Variant 3: SOCIAL-PROOF (case study driven)
3. Selects recommended variant
4. Runs in parallel (3 concurrent max)

### Code Flow

```python
class CopywriterAgent(BaseAgent):
    
    async def write_email(self, lead: Dict, product_analysis: Dict) -> Dict:
        await self.emit(f"✍️ Copywriter: Crafting email for {lead.get('company_name')}...")
        
        lead_with_email = lead.copy()
        
        prompt = EMAIL_GENERATION_PROMPT.format(
            company_name=lead.get('company_name'),
            industry=lead.get('industry'),
            description=lead.get('description', '')[:300],
            decision_maker=lead.get('decision_maker_name', 'Decision Maker'),
            pain_points=', '.join(lead.get('pain_points', [])[:3]),
            qualification=lead.get('qualification_tier', 'WARM'),
            product_analysis=json.dumps(product_analysis)[:600]
        )
        
        email_result = await self.invoke(prompt)  # Uses COPYWRITER_SYSTEM_PROMPT
        
        if email_result:
            lead_with_email['email_variants'] = email_result
            
            # Select recommended variant
            recommended = email_result.get('recommended_variant', 1)
            variant = email_result[f'email_variant_{recommended}']
            
            lead_with_email['email_subject'] = variant.get('subject')
            lead_with_email['email_body'] = variant.get('body')
        
        return lead_with_email
```

### Full Copywriter System Prompt

```
You are a world-class B2B email copywriter who has generated $50M+ in 
pipeline through cold outreach.

YOUR MISSION: Craft highly personalized, compelling emails that get 
responses and book meetings.

COPYWRITING PRINCIPLES:

1. PERSONALIZATION IS KING:
   - Reference specific company details
   - Mention recent news/achievements
   - Connect to their industry challenges
   - Never sound like a template

2. VALUE-FIRST APPROACH:
   - Lead with insight, not pitch
   - Show you understand their world
   - Offer immediate value
   - Make them curious

3. PSYCHOLOGICAL TRIGGERS:
   - Social proof (relevant case studies)
   - Scarcity (if applicable)
   - Authority (expertise signals)
   - Reciprocity (give before asking)

4. STRUCTURE FOR OPENS & REPLIES:
   - Subject: 3-7 words, curiosity-driven, personalized
   - First Line: Hook that proves research
   - Problem: Agitate a specific pain point
   - Solution: Hint at how you help (don't oversell)
   - CTA: Single, clear, low-commitment ask

OUTPUT FORMAT (JSON):
{
    "email_variant_1": {
        "style": "INSIGHT-LED",
        "subject": "Subject line",
        "preview_text": "First 90 chars",
        "body": "Full email body",
        "cta": "Specific call to action"
    },
    "email_variant_2": {
        "style": "DIRECT-PITCH",
        "subject": "Subject line",
        "preview_text": "First 90 chars",
        "body": "Full email body",
        "cta": "Specific call to action"
    },
    "email_variant_3": {
        "style": "SOCIAL-PROOF",
        "subject": "Subject line",
        "preview_text": "First 90 chars",
        "body": "Full email body",
        "cta": "Specific call to action"
    },
    "recommended_variant": 1-3,
    "personalization_hooks_used": ["Hook 1", "Hook 2"],
    "sending_time_recommendation": "Best time to send"
}

EMAIL RULES:
- Maximum 120 words per email
- No jargon or buzzwords
- Sound human, not robotic
- Include 1 question to encourage reply
- No attachments or links in first email (except meeting link in CTA)
```

### Email Generation Task Prompt

```
Write personalized B2B outreach emails for this prospect:

COMPANY: {company_name}
INDUSTRY: {industry}
COMPANY DESCRIPTION: {description}
DECISION MAKER: {decision_maker}
PAIN POINTS: {pain_points}
QUALIFICATION: {qualification}

OUR PRODUCT:
{product_analysis}

Generate 3 email variants optimized for response rate.
Return ONLY valid JSON matching the email format specified.
```

### Output Example

```json
{
    "email_variant_1": {
        "style": "INSIGHT-LED",
        "subject": "Quick thought on TechCorp's scaling",
        "body": "Hi Jane,\n\nNoticed TechCorp is growing rapidly...",
        "cta": "Worth a quick 15-min chat?"
    },
    "email_variant_2": {
        "style": "DIRECT-PITCH",
        "subject": "TechCorp + AI Sales Automation",
        "body": "Hi Jane,\n\nGiven your team's focus on...",
        "cta": "Open to exploring this?"
    },
    "email_variant_3": {
        "style": "SOCIAL-PROOF",
        "subject": "How [Similar Company] solved reporting issues",
        "body": "Hi Jane,\n\n[Similar Company] was facing similar...",
        "cta": "Want to see how?"
    },
    "recommended_variant": 1,
    "personalization_hooks_used": ["Tech stack (AWS)", "Pain point (Manual reporting)"]
}
```

---

## Phase 6: Save to Database

### What Happens

1. Iterate through all qualified leads
2. Check for existing duplicates
3. Create Lead records with all data
4. Store ML scores, confidence, explanations

### Code Flow

```python
async def _save_leads_node(self, state: MultiAgentState) -> Dict:
    await self.emit("💾 Saving leads to database...")
    
    db = SessionLocal()
    leads_to_save = state.get("qualified_leads", [])
    saved_count = 0
    
    for lead_data in leads_to_save:
        # Check for duplicates
        existing = db.query(Lead).filter(
            Lead.campaign_id == campaign_id,
            Lead.company_name == lead_data.get("company_name")
        ).first()
        
        if existing:
            continue
        
        # Create new lead record
        lead = Lead(
            campaign_id=campaign_id,
            company_name=lead_data.get("company_name"),
            industry=lead_data.get("industry"),
            website=lead_data.get("website"),
            description=lead_data.get("description"),
            email=lead_data.get("email"),
            ml_score=lead_data.get("final_score"),
            ml_confidence=lead_data.get("ml_confidence"),
            score_explanation=lead_data.get("score_explanation"),
            status="new"
        )
        db.add(lead)
        saved_count += 1
    
    db.commit()
    db.close()
    
    return {"progress": 90.0}
```

---

## Phase 7: Send Emails

### What Happens

1. Iterate through leads with emails
2. Send recommended email variant via EmailService
3. Create Email record in database
4. Track success/failure

### Code Flow

```python
async def _send_emails_node(self, state: MultiAgentState) -> Dict:
    await self.emit("📧 [MULTI-AGENT] Sending personalized emails...")
    
    leads = state["leads_with_emails"]
    sent_count = 0
    
    for lead in leads:
        if not lead.get('email') or not lead.get('email_body'):
            continue
        
        # Send email
        sent = await self.email_service.send_email(
            to_email=lead['email'],
            subject=lead.get('email_subject'),
            body=lead.get('email_body')
        )
        
        if sent:
            # Record in database
            email_record = Email(
                lead_id=db_lead.id,
                subject=lead.get('email_subject'),
                body=lead.get('email_body'),
                status="sent",
                sent_at=datetime.utcnow()
            )
            db.add(email_record)
            db.commit()
            
            sent_count += 1
            await self.emit(f"✅ Email sent to {lead.get('company_name')}")
    
    return {"emails_sent": sent_count, "progress": 100.0}
```

---

## Complete Prompt Reference

### All Prompts in One Place

| Prompt | Location | Used By |
|--------|----------|---------|
| `RESEARCHER_SYSTEM_PROMPT` | `agent_prompts.py` | ResearcherAgent |
| `QUALIFIER_SYSTEM_PROMPT` | `agent_prompts.py` | QualifierAgent |
| `COPYWRITER_SYSTEM_PROMPT` | `agent_prompts.py` | CopywriterAgent |
| `SUPERVISOR_SYSTEM_PROMPT` | `agent_prompts.py` | (Future) |
| `PRODUCT_ANALYSIS_PROMPT` | `agent_prompts.py` | Product Analysis Phase |
| `LEAD_RESEARCH_PROMPT` | `agent_prompts.py` | ResearcherAgent |
| `LEAD_QUALIFICATION_PROMPT` | `agent_prompts.py` | QualifierAgent |
| `EMAIL_GENERATION_PROMPT` | `agent_prompts.py` | CopywriterAgent |

---

## Data Transformation Flow

### Lead Data at Each Stage

```
STAGE 1: raw_leads (from search)
──────────────────────────────
{
    company_name: "TechCorp"
    website: "https://techcorp.com"
    description: "Enterprise software..."
}

          │
          ▼ [Researcher Agent]

STAGE 2: researched_leads (enriched)
────────────────────────────────────
{
    company_name: "TechCorp"
    website: "https://techcorp.com"
    description: "Enterprise software..."
    + pain_points: ["Manual processes", ...]
    + technology_stack: ["AWS", "React"]
    + decision_makers: [{name, title}]
    + contact_email: "jane@techcorp.com"
    + research_confidence: 0.85
}

          │
          ▼ [Qualifier Agent]

STAGE 3: qualified_leads (scored)
─────────────────────────────────
{
    ... all above ...
    + ml_score: 0.85
    + ml_confidence: 0.78
    + semantic_similarity: 0.79
    + final_score: 0.82
    + qualification_tier: "HOT"
    + qualification_reasoning: "..."
    + recommended_approach: "..."
    + objections_anticipated: [...]
}

          │
          ▼ [Copywriter Agent]

STAGE 4: leads_with_emails (ready to send)
──────────────────────────────────────────
{
    ... all above ...
    + email_variants: {
        email_variant_1: {subject, body, cta},
        email_variant_2: {...},
        email_variant_3: {...}
    }
    + email_subject: "Quick thought on TechCorp's scaling"
    + email_body: "Hi Jane,\n\nNoticed TechCorp..."
}

          │
          ▼ [Database + Email Sender]

STAGE 5: Complete
─────────────────
Lead saved to database
Email sent to recipient
Email record created
```

---

*Last Updated: December 2024*
*Version: 1.0.0*
