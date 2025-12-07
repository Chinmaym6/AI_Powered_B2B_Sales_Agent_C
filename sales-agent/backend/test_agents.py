"""
Multi-Agent System Test
========================
Tests all three agents: Researcher, Qualifier, Copywriter
"""
import asyncio
import sys
sys.path.insert(0, '.')

print("="*70)
print("         MULTI-AGENT SYSTEM TEST")
print("="*70)

# Test data
test_company = {
    "company_name": "TechCorp AI",
    "website": "https://techcorp.ai",
    "description": "Enterprise AI platform for automation and analytics",
    "email": "sales@techcorp.ai",
    "industry": "Technology"
}

test_product = {
    "name": "DataFlow Pro",
    "description": "AI-powered data analytics platform",
    "keywords": ["ai", "analytics", "enterprise", "automation"],
    "target_industries": ["Technology", "Finance"],
    "value_proposition": "Reduce data processing time by 80%"
}

async def emit(msg):
    print(f"   {msg}")

async def test_researcher():
    print("\n" + "-"*70)
    print("STEP 1: RESEARCHER AGENT (Uses Groq)")
    print("-"*70)
    
    from app.services.gemini_service import GeminiService
    from app.services.scraper_service import ScraperService
    from app.core.multi_agent import ResearcherAgent
    
    gemini = GeminiService()
    scraper = ScraperService()
    researcher = ResearcherAgent(gemini, scraper, emit)
    
    print(f"✅ ResearcherAgent initialized")
    
    # Test research
    result = await researcher.research_company(test_company, test_product)
    
    print(f"✅ Research complete!")
    print(f"   Company: {result.get('company_name')}")
    print(f"   Research confidence: {result.get('research_confidence', 'N/A')}")
    
    return result

async def test_qualifier(researched_lead):
    print("\n" + "-"*70)
    print("STEP 2: QUALIFIER AGENT (Uses ML-only)")
    print("-"*70)
    
    from app.services.gemini_service import GeminiService
    from app.ml.lead_scorer import MLLeadScorer
    from app.core.multi_agent import QualifierAgent
    
    gemini = GeminiService()
    ml_scorer = MLLeadScorer()
    
    # Mock embeddings service (not needed for ML-only mode)
    class MockEmbeddings:
        pass
    embeddings = MockEmbeddings()
    
    qualifier = QualifierAgent(gemini, ml_scorer, embeddings, emit)
    
    print(f"✅ QualifierAgent initialized")
    
    # Test qualification
    result = await qualifier.qualify_lead(researched_lead, test_product)
    
    print(f"✅ Qualification complete!")
    print(f"   Score: {result.get('qualification_score', 0):.2f}")
    print(f"   Tier: {result.get('qualification_tier', 'N/A')}")
    print(f"   Ready for email: {result.get('should_email', False)}")
    
    return result

async def test_copywriter(qualified_lead):
    print("\n" + "-"*70)
    print("STEP 3: COPYWRITER AGENT (Uses Gemini -> Groq fallback)")
    print("-"*70)
    
    from app.services.gemini_service import GeminiService
    from app.core.multi_agent import CopywriterAgent
    
    gemini = GeminiService()
    copywriter = CopywriterAgent(gemini, emit)
    
    print(f"✅ CopywriterAgent initialized")
    
    # Test email generation
    result = await copywriter.write_email(qualified_lead, test_product)
    
    print(f"✅ Email generated!")
    print(f"   Subject: {result.get('email_subject', 'N/A')[:50]}...")
    print(f"   Body preview: {result.get('email_body', 'N/A')[:100]}...")
    
    return result

async def main():
    try:
        # Test all three agents in sequence
        researched = await test_researcher()
        qualified = await test_qualifier(researched)
        email = await test_copywriter(qualified)
        
        print("\n" + "="*70)
        print("              ALL AGENTS WORKING!")
        print("="*70)
        print("""
   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │  RESEARCHER │ --> │  QUALIFIER  │ --> │  COPYWRITER │
   │   (Groq)    │     │  (ML-only)  │     │   (Gemini)  │
   │    FREE     │     │    FREE     │     │  w/Fallback │
   └─────────────┘     └─────────────┘     └─────────────┘
        """)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
