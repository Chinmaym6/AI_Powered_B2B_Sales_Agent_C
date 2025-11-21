from typing import Dict, Callable, List
import asyncio
from ..ml.lead_scorer import MLLeadScorer
from ..ml.embeddings import EmbeddingService
from ..ml.response_classifier import ResponseClassifier
from ..services.gemini_service import GeminiService
from ..services.search_service import SearchService
from ..services.scraper_service import ScraperService
from ..services.email_service import EmailService

class AutonomousAgent:
    """
    Main agent that orchestrates the entire sales pipeline
    """
    
    def __init__(self, campaign: Dict, emit_update: Callable):
        self.campaign = campaign
        self.emit = emit_update
        
        # Initialize all services
        self.gemini = GeminiService()
        self.search_service = SearchService()
        self.scraper = ScraperService()
        self.email_service = EmailService()
        
        # Initialize ML models
        self.ml_scorer = MLLeadScorer()
        self.embeddings = EmbeddingService()
        self.response_classifier = ResponseClassifier()
        
        self.product_analysis = None
        self.leads = []
    
    def check_if_stopped(self):
        """Check if campaign has been stopped manually"""
        try:
            from ..models.database import SessionLocal
            from ..models.tables import Campaign
            db = SessionLocal()
            campaign = db.query(Campaign).filter(Campaign.id == self.campaign.get('id')).first()
            is_stopped = False
            if campaign and campaign.status == "stopped":
                is_stopped = True
            db.close()
            return is_stopped
        except Exception as e:
            print(f"Error checking status: {e}")
            return False

    async def run(self):
        """Execute the full autonomous pipeline"""
        
        try:
            # Check if stopped at start
            if self.check_if_stopped():
                await self.emit("🛑 Campaign stopped by user.")
                return {"status": "stopped"}

            # Step 1: Analyze product
            await self.emit("🤖 Agent: Analyzing your product...")
            self.product_analysis = await self.analyze_product()
            await self.emit(f"✅ Extracted keywords: {', '.join(self.product_analysis.get('keywords', [])[:5])}")
            
            if self.check_if_stopped():
                await self.emit("🛑 Campaign stopped by user.")
                return {"status": "stopped"}

            # Step 2: Generate search queries
            await self.emit("🧠 Generating smart search queries...")
            search_queries = await self.generate_search_queries()
            await self.emit(f"📋 Created {len(search_queries)} targeted search queries")
            
            if self.check_if_stopped():
                await self.emit("🛑 Campaign stopped by user.")
                return {"status": "stopped"}

            # Step 3: Search and scrape
            await self.emit("🔍 Searching the web for potential leads...")
            raw_leads = await self.search_and_scrape(search_queries)
            await self.emit(f"📊 Found {len(raw_leads)} potential companies")
            
            if self.check_if_stopped():
                await self.emit("🛑 Campaign stopped by user.")
                return {"status": "stopped"}

            # Step 4: Enrich leads
            await self.emit("💎 Enriching leads with company data...")
            enriched_leads = await self.enrich_leads(raw_leads)
            
            # Filter leads: Only keep those with emails
            leads_with_emails = [l for l in enriched_leads if l.get("email")]
            await self.emit(f"📧 Found {len(leads_with_emails)} leads with valid emails (out of {len(enriched_leads)} enriched)")
            
            if not leads_with_emails:
                await self.emit("⚠️ No leads with emails found. Stopping campaign.")
                # Update status to completed even if no leads
                try:
                    from ..models.database import SessionLocal
                    from ..models.tables import Campaign
                    db = SessionLocal()
                    campaign = db.query(Campaign).filter(Campaign.id == self.campaign.get('id')).first()
                    if campaign:
                        campaign.status = "completed"
                        db.commit()
                    db.close()
                except:
                    pass
                return {"status": "no_leads", "leads_found": 0}
            
            if self.check_if_stopped():
                await self.emit("🛑 Campaign stopped by user.")
                return {"status": "stopped"}

            # Step 5: ML scoring
            await self.emit("🤖 Scoring leads with ML model...")
            scored_leads = await self.score_leads(leads_with_emails)
            
            if self.check_if_stopped():
                await self.emit("🛑 Campaign stopped by user.")
                return {"status": "stopped"}

            # Step 6: Semantic filtering
            await self.emit("🧠 Applying semantic filtering...")
            filtered_leads = await self.semantic_filtering(scored_leads)
            
            if self.check_if_stopped():
                await self.emit("🛑 Campaign stopped by user.")
                return {"status": "stopped"}

            # Step 7: Generate and send emails
            await self.emit("✉️ Generating personalized emails...")
            await self.generate_and_send_emails(filtered_leads[:10])
            
            await self.emit("🎉 Campaign complete! Check your dashboard for results.")
            
            # Update campaign status to completed
            try:
                from ..models.database import SessionLocal
                from ..models.tables import Campaign
                
                db = SessionLocal()
                campaign = db.query(Campaign).filter(Campaign.id == self.campaign.get('id')).first()
                if campaign:
                    campaign.status = "completed"
                    db.commit()
                db.close()
            except Exception as e:
                print(f"Error updating campaign status: {e}")
            
            return {
                "status": "success",
                "leads_found": len(filtered_leads),
                "emails_sent": min(10, len(filtered_leads))
            }
            
        except Exception as e:
            await self.emit(f"❌ Error: {str(e)}")
            print(f"Agent error: {e}")
            # Don't raise, just return error status
            return {"status": "error", "message": str(e)}
    
    async def analyze_product(self) -> Dict:
        """Analyze product description using Gemini"""
        
        product_desc = self.campaign.get('product_description', '')
        target_industry = self.campaign.get('target_industry', '')
        
        prompt = f"""You are a B2B sales expert. Analyze the following product and provide detailed insights.

**Product Description:** {product_desc}

**Target Industry (if specified):** {target_industry}

Extract the following information and return ONLY a valid JSON object (no markdown, no explanations):

1. **features**: List 8-12 specific, unique features of THIS product (be specific to the description, not generic)
2. **target_industries**: List 4-6 industries that would benefit from THIS specific product
3. **pain_points**: List 6-9 specific problems THIS product solves (based on the description)
4. **ideal_customer_profile**: A detailed 3-4 sentence description of the perfect customer for THIS product
5. **keywords**: List 12-18 search keywords highly relevant to THIS product (avoid generic terms like "sales automation" unless they're specific to this product)

CRITICAL: 
- Be SPECIFIC to the product description provided
- DO NOT use generic keywords
- Extract keywords directly from the product description
- Return ONLY valid JSON, no other text

JSON Format:
{{
  "features": ["specific feature 1", "specific feature 2", ...],
  "target_industries": ["Industry 1", "Industry 2", ...],
  "pain_points": ["specific pain point 1", "specific pain point 2", ...],
  "ideal_customer_profile": "detailed description here...",
  "keywords": ["specific keyword 1", "specific keyword 2", ...]
}}"""
        
        await self.emit(f"📝 Analyzing product with AI...")
        response = await self.gemini.generate(prompt)
        parsed = self.gemini.parse_json_response(response)
        
        # Log what was extracted
        if parsed:
            await self.emit(f"🎯 Identified {len(parsed.get('keywords', []))} keywords")
            await self.emit(f"🏭 Target industries: {', '.join(parsed.get('target_industries', [])[:3])}")
        
        return parsed
    
    async def generate_search_queries(self) -> list:
        """Generate smart search queries based on product analysis"""
        
        queries = []
        
        # Industry-based queries with B2B intent
        for industry in self.product_analysis.get("target_industries", [])[:3]:
            # Look for actual company pages
            queries.append(f'"{industry}" "contact us" -intitle:"top" -intitle:"best"')
            queries.append(f'"{industry}" "about us" "our team"')
            queries.append(f'site:linkedin.com/company "{industry}"')
        
        # Keyword-based queries
        for keyword in self.product_analysis.get("keywords", [])[:5]:
            queries.append(f'"{keyword}" companies {self.campaign.get("target_industry", "")} -blog -news')
        
        # Pain point queries - targeted at finding companies with these problems
        for pain_point in self.product_analysis.get("pain_points", [])[:3]:
            queries.append(f'companies "looking for" {pain_point}')
            queries.append(f'"{pain_point}" solutions companies')
        
        return queries[:12]  # Limit to 12 queries
    
    async def search_and_scrape(self, queries: list) -> list:
        """Search web and scrape company data"""
        
        all_leads = []
        seen_domains = set()
        
        # Blacklist of domains and title patterns to ignore
        ignored_domains = [
            "medium.com", "wikipedia.org", "facebook.com", "twitter.com", 
            "instagram.com", "youtube.com", "pinterest.com", "reddit.com",
            "yelp.com", "clutch.co", "capterra.com", "g2.com", "upwork.com",
            "glassdoor.com", "indeed.com", "yellowpages.com", "bbb.org",
            "crunchbase.com", "bloomberg.com", "forbes.com", "techcrunch.com",
            "businessinsider.com", "nytimes.com", "wsj.com"
        ]
        
        ignored_title_patterns = [
            "top 10", "top 20", "best", "vs", "review", "guide", "how to",
            "list of", "directory", "job", "career", "salary"
        ]
        
        for i, query in enumerate(queries):
            await self.emit(f"🔍 Searching: {query}...")
            
            # Search via multi-provider service
            results = await self.search_service.search(query, num_results=8)
            
            for result in results:
                url = result.get("link", "")
                original_url = url.lower()
                title = result.get("title", "").lower()
                
                # Deduplicate by domain
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                if not url or domain in seen_domains:
                    continue
                
                # Filter out ignored domains
                if any(ignored_domain in original_url for ignored_domain in ignored_domains):
                    continue
                    
                # Filter out blog posts and articles
                if "/blog/" in original_url or "/article/" in original_url or "/news/" in original_url:
                    continue
                    
                # Filter out "Top X" lists, reviews, and directories
                if any(pattern in title for pattern in ignored_title_patterns):
                    continue
                
                # Filter out directory/list pages
                if "companies near me" in title or "list of" in title or "directory" in title:
                    continue
                
                seen_domains.add(domain)
                
                # Extract proper company name from URL or title
                company_name = self.scraper.extract_company_name_from_url(url)
                
                # Extract company info
                lead = {
                    "company_name": company_name,
                    "website": url,
                    "snippet": result.get("snippet", ""),
                    "source_query": query
                }
                
                all_leads.append(lead)
            
            # Rate limiting
            await asyncio.sleep(1)
        
        return all_leads
    
    async def enrich_leads(self, leads: list) -> list:
        """Enrich leads with company details and contact info"""
        
        enriched = []
        
        for i, lead in enumerate(leads):
            await self.emit(f"💎 Enriching lead {i+1}/{len(leads)}: {lead['company_name']}")
            
            try:
                # Scrape company website
                company_data = await self.scraper.scrape_website(lead["website"])
                
                if company_data:
                    # Extract decision makers if available
                    decision_makers = company_data.get("decision_makers", [])
                    decision_maker_name = None
                    decision_maker_title = None
                    
                    if decision_makers and len(decision_makers) > 0:
                        decision_maker_name = decision_makers[0].get("name")
                        decision_maker_title = decision_makers[0].get("title")
                    
                    lead.update({
                        "description": company_data.get("description", lead["snippet"]),
                        "industry": company_data.get("industry", ""),
                        "email": company_data.get("email"),
                        "linkedin_url": company_data.get("linkedin"),
                        "company_size": company_data.get("size", 0),
                        "decision_maker_name": decision_maker_name,
                        "decision_maker_title": decision_maker_title
                    })
                    
                    enriched.append(lead)
                
            except Exception as e:
                # Skip leads that fail to scrape
                print(f"Enrichment error: {e}")
                continue
            
            # Rate limiting
            await asyncio.sleep(0.5)
        
            # Rate limiting
            await asyncio.sleep(0.5)
            
        # Strict Relevance Verification
        verified_leads = []
        for lead in enriched:
            if not lead.get('full_content') and not lead.get('description'):
                continue
                
            # If we have full content from deep scraping, use it. Otherwise use description.
            context = lead.get('full_content', lead.get('description', ''))
            
            is_relevant = await self.verify_lead_relevance(lead['company_name'], context)
            if is_relevant:
                verified_leads.append(lead)
            else:
                await self.emit(f"❌ Discarding {lead['company_name']}: Not a relevant match.")
            
        enriched = verified_leads
            
        # Save enriched leads to database immediately
        try:
            from ..models.database import SessionLocal
            from ..models.tables import Lead as LeadModel
            
            db = SessionLocal()
            for lead in enriched:
                # Check if lead already exists for this campaign
                existing = db.query(LeadModel).filter(
                    LeadModel.campaign_id == self.campaign.get('id'),
                    LeadModel.website == lead['website']
                ).first()
                
                if not existing:
                    db_lead = LeadModel(
                        campaign_id=self.campaign.get('id'),
                        company_name=lead['company_name'],
                        website=lead['website'],
                        description=lead.get('description', ''),
                        industry=lead.get('industry', ''),
                        email=lead.get('email'),
                        linkedin_url=lead.get('linkedin_url'),
                        company_size=lead.get('company_size', 0),
                        decision_maker_name=lead.get('decision_maker_name'),
                        decision_maker_title=lead.get('decision_maker_title'),
                        status="enriched"
                    )
                    db.add(db_lead)
                    db.commit()
                    db.refresh(db_lead)
                    lead['db_id'] = str(db_lead.id)
                    await self.emit(f"💾 Saved {lead['company_name']} to database")
                else:
                    lead['db_id'] = str(existing.id)
            
            db.close()
        except Exception as e:
            print(f"Error saving leads to DB: {e}")
            await self.emit(f"⚠️ Error saving leads: {str(e)}")
        
        return enriched
    
    async def score_leads(self, leads: list) -> list:
        """Score leads using ML model and update database"""
        
        from ..models.database import SessionLocal
        from ..models.tables import Lead as LeadModel
        
        for lead in leads:
            # ML scoring
            ml_result = self.ml_scorer.predict(lead, self.product_analysis)
            
            lead["ml_score"] = ml_result["score"]
            lead["ml_confidence"] = ml_result["confidence"]
            lead["score_explanation"] = ml_result["top_factors"]
            
            await self.emit(
                f"✅ {lead['company_name']}: "
                f"Score {ml_result['score']:.2f} "
                f"(Confidence: {ml_result['confidence']:.0%})"
            )
            
            # Update database with scores
            if lead.get('db_id'):
                try:
                    db = SessionLocal()
                    db_lead = db.query(LeadModel).filter(LeadModel.id == lead['db_id']).first()
                    if db_lead:
                        db_lead.ml_score = ml_result["score"]
                        db_lead.ml_confidence = ml_result["confidence"]
                        db_lead.score_explanation = ml_result["top_factors"]
                        db.commit()
                    db.close()
                except Exception as e:
                    print(f"Database update error: {e}")
        
        # Sort by ML score
        leads.sort(key=lambda x: x["ml_score"], reverse=True)
        
        return leads
    
    async def semantic_filtering(self, leads: list) -> list:
        """Filter leads using semantic similarity"""
        
        ideal_customer = self.product_analysis.get("ideal_customer_profile", "")
        
        similar_leads = self.embeddings.find_most_similar_leads(
            ideal_customer,
            leads,
            top_k=20
        )
        
        # Combine ML score and semantic similarity
        filtered = []
        for lead, similarity in similar_leads:
            lead["semantic_similarity"] = similarity
            lead["final_score"] = (lead["ml_score"] * 0.7 + similarity * 0.3)
            filtered.append(lead)
        
        filtered.sort(key=lambda x: x["final_score"], reverse=True)
        
        return filtered
    
    async def generate_and_send_emails(self, leads: list):
        """Generate personalized emails and send via MailHog"""
        
        for i, lead in enumerate(leads):
            await self.emit(f"✉️ Generating email {i+1}/{len(leads)} for {lead['company_name']}...")
            
            # Generate email with Gemini
            email = await self.generate_email(lead)
            
            # Send email
            sent_success = False
            if lead.get("email"):
                await self.emit(f"📤 Sending to {lead['email']}...")
                sent_success = await self.email_service.send_email(
                    to_email=lead["email"],
                    subject=email.get("subject", "Hello"),
                    body=email.get("body", "Hi there")
                )
                
                if sent_success:
                    await self.emit(f"✅ Email sent to {lead['company_name']}")
                else:
                    await self.emit(f"⚠️ Failed to send email to {lead['company_name']}")
            else:
                await self.emit(f"⚠️ No email found for {lead['company_name']}")
            
            # Save email to database
            if lead.get('db_id'):
                try:
                    from ..models.database import SessionLocal
                    from ..models.tables import Email as EmailModel
                    from datetime import datetime
                    
                    db = SessionLocal()
                    
                    email_record = EmailModel(
                        lead_id=lead['db_id'],
                        subject=email.get("subject", ""),
                        body=email.get("body", ""),
                        status="sent" if sent_success else "failed",
                        sent_at=datetime.now() if sent_success else None
                    )
                    
                    db.add(email_record)
                    db.commit()
                    db.close()
                    
                except Exception as e:
                    print(f"Error saving email to DB: {e}")
            
            await asyncio.sleep(1)
    
    async def generate_email(self, lead: Dict) -> Dict:
        """Generate personalized cold email using Gemini"""
        
        prompt = f"""
        Write a professional, personalized cold email for B2B sales.
        
        Product: {self.campaign.get('product_description', '')}
        Product Benefits: {', '.join(self.product_analysis.get('features', [])[:3])}
        
        Target Company: {lead['company_name']}
        Company Description: {lead.get('description', 'N/A')}
        Industry: {lead.get('industry', 'N/A')}
        
        Requirements:
        - Reference specific company details
        - Highlight 1-2 relevant product benefits
        - Keep under 120 words
        - Include clear call-to-action
        - Professional but conversational tone
        - Subject line under 50 characters
        
        Return as JSON: {{"subject": "...", "body": "..."}}
        """
        
        response = await self.gemini.generate(prompt)
        return self.gemini.parse_json_response(response)

    async def verify_lead_relevance(self, company_name: str, context: str) -> bool:
        """Strictly verify if the lead matches the campaign requirements"""
        
        prompt = f"""
        You are a strict lead qualification expert. Determine if this company is a GOOD MATCH for the product.
        
        Product Description: {self.campaign.get('product_description', '')}
        Target Industry: {self.campaign.get('target_industry', '')}
        
        Company Name: {company_name}
        Company Context (Website Content):
        {context[:2000]}
        
        Task:
        1. Does this company operate in the target industry or a related field?
        2. Would they realistically have a need for this product?
        3. Are they a potential buyer (B2B company) rather than a consumer or irrelevant entity?
        
        Return JSON: {{"is_match": true/false, "reason": "short explanation"}}
        """
        
        try:
            response = await self.gemini.generate(prompt)
            parsed = self.gemini.parse_json_response(response)
            return parsed.get("is_match", False)
        except:
            return True # Default to keeping it if check fails

