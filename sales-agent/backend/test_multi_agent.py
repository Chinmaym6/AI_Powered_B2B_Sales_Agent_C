"""Test Multi-Agent System"""
import asyncio

async def test_multi_agent():
    print("=" * 50)
    print("MULTI-AGENT SYSTEM VERIFICATION")
    print("=" * 50)
    
    # Test imports
    print("\n1. Testing imports...")
    try:
        from app.core.multi_agent import (
            MultiAgentOrchestrator,
            ResearcherAgent,
            QualifierAgent,
            CopywriterAgent,
            create_multi_agent_system
        )
        from app.core.agent_prompts import (
            RESEARCHER_SYSTEM_PROMPT,
            QUALIFIER_SYSTEM_PROMPT,
            COPYWRITER_SYSTEM_PROMPT,
            SUPERVISOR_SYSTEM_PROMPT
        )
        print("   ✅ All multi-agent imports successful")
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return
    
    # Test services
    print("\n2. Testing service instantiation...")
    try:
        from app.services.gemini_service import GeminiService
        from app.services.scraper_service import ScraperService
        from app.ml.lead_scorer import MLLeadScorer
        from app.services.embedding_service import EmbeddingService
        from app.services.email_service import EmailService
        
        gemini = GeminiService()
        scraper = ScraperService()
        ml_scorer = MLLeadScorer()
        embeddings = EmbeddingService()
        email_service = EmailService()
        print("   ✅ All services instantiated")
    except Exception as e:
        print(f"   ❌ Service error: {e}")
        return
    
    # Test multi-agent creation
    print("\n3. Testing MultiAgentOrchestrator creation...")
    try:
        campaign = {
            "id": "test-123",
            "name": "Test Campaign",
            "product_description": "AI-powered sales automation platform",
            "target_industry": "Technology",
            "target_audience": "Sales managers"
        }
        
        logs = []
        async def emit(msg):
            logs.append(msg)
            print(f"   📢 {msg}")
        
        orchestrator = create_multi_agent_system(
            campaign=campaign,
            gemini_service=gemini,
            scraper_service=scraper,
            ml_scorer=ml_scorer,
            embedding_service=embeddings,
            email_service=email_service,
            emit_callback=emit
        )
        
        print(f"   ✅ MultiAgentOrchestrator created: {type(orchestrator).__name__}")
        print(f"   ✅ Researcher Agent: {type(orchestrator.researcher).__name__}")
        print(f"   ✅ Qualifier Agent: {type(orchestrator.qualifier).__name__}")
        print(f"   ✅ Copywriter Agent: {type(orchestrator.copywriter).__name__}")
        print(f"   ✅ Workflow compiled: {orchestrator.workflow is not None}")
    except Exception as e:
        print(f"   ❌ Orchestrator error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test prompts
    print("\n4. Verifying agent prompts...")
    print(f"   ✅ Researcher prompt: {len(RESEARCHER_SYSTEM_PROMPT)} chars")
    print(f"   ✅ Qualifier prompt: {len(QUALIFIER_SYSTEM_PROMPT)} chars")
    print(f"   ✅ Copywriter prompt: {len(COPYWRITER_SYSTEM_PROMPT)} chars")
    print(f"   ✅ Supervisor prompt: {len(SUPERVISOR_SYSTEM_PROMPT)} chars")
    
    print("\n" + "=" * 50)
    print("✅ MULTI-AGENT SYSTEM VERIFIED SUCCESSFULLY!")
    print("=" * 50)
    print("\nTo use multi-agent mode, ensure USE_MULTI_AGENT=true in .env")
    
if __name__ == "__main__":
    asyncio.run(test_multi_agent())
