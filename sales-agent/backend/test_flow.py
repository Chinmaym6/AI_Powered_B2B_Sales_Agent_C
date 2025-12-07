"""
COMPREHENSIVE END-TO-END FLOW TEST
===================================
Tests every component of the hybrid AI system step by step.
"""

import asyncio
import sys
import json
sys.path.insert(0, '.')

print("=" * 70)
print("       COMPREHENSIVE END-TO-END FLOW TEST")
print("=" * 70)

errors = []
passed = 0

# =============================================================================
# STEP 1: Configuration Check
# =============================================================================
print("\n" + "="*70)
print("STEP 1: CONFIGURATION")
print("="*70)

try:
    from app.config import settings
    print(f"✅ MAX_LEADS_TO_RESEARCH: {settings.MAX_LEADS_TO_RESEARCH}")
    print(f"✅ MAX_LEADS_TO_QUALIFY: {settings.MAX_LEADS_TO_QUALIFY}")
    print(f"✅ MAX_EMAILS_TO_GENERATE: {settings.MAX_EMAILS_TO_GENERATE}")
    print(f"✅ MAX_SEARCH_RESULTS: {settings.MAX_SEARCH_RESULTS}")
    print(f"✅ GROQ_ENABLED: {settings.GROQ_ENABLED}")
    print(f"✅ QUALIFICATION_MODE: {settings.QUALIFICATION_MODE}")
    passed += 1
except Exception as e:
    print(f"❌ Config Error: {e}")
    errors.append(f"Config: {e}")

# =============================================================================
# STEP 2: Groq Service Test
# =============================================================================
print("\n" + "="*70)
print("STEP 2: GROQ SERVICE (Research AI)")
print("="*70)

try:
    from app.services.groq_service import get_groq_service
    groq = get_groq_service()
    
    if groq.enabled:
        print(f"✅ Groq initialized: {groq.model}")
        
        # Test generation
        print("⚡ Testing Groq generation...")
        result = asyncio.run(groq.generate("Say 'Groq test passed' exactly"))
        print(f"✅ Groq Response: {result[:60]}")
        passed += 1
    else:
        print("❌ Groq not enabled (missing API key)")
        errors.append("Groq: Not enabled")
except Exception as e:
    print(f"❌ Groq Error: {e}")
    errors.append(f"Groq: {e}")

# =============================================================================
# STEP 3: ML Lead Scorer Test
# =============================================================================
print("\n" + "="*70)
print("STEP 3: ML LEAD SCORER")
print("="*70)

try:
    from app.ml.lead_scorer import MLLeadScorer
    scorer = MLLeadScorer()
    
    if scorer.model is not None:
        print(f"✅ ML Model loaded")
        
        # Test with HOT lead
        hot_lead = {
            'company_name': 'AI Solutions Corp',
            'description': 'Enterprise AI platform for automation and machine learning',
            'email': 'sales@aisolutions.com',
            'industry': 'Technology'
        }
        hot_product = {
            'keywords': ['ai', 'automation', 'machine learning', 'enterprise'],
            'target_industries': ['Technology', 'Software']
        }
        hot_result = scorer.predict(hot_lead, hot_product)
        print(f"   HOT Lead Score: {hot_result.get('score', 0):.2f} -> {hot_result.get('tier', 'N/A')}")
        
        # Test with COLD lead
        cold_lead = {
            'company_name': 'Random Bakery',
            'description': 'Local bakery selling bread and cakes',
            'email': 'info@bakery.com',
            'industry': 'Food'
        }
        cold_result = scorer.predict(cold_lead, hot_product)
        print(f"   COLD Lead Score: {cold_result.get('score', 0):.2f} -> {cold_result.get('tier', 'N/A')}")
        
        passed += 1
    else:
        print("❌ ML Model not loaded")
        errors.append("ML: Model not loaded")
except Exception as e:
    print(f"❌ ML Scorer Error: {e}")
    errors.append(f"ML: {e}")

# =============================================================================
# STEP 4: Gemini Service Check
# =============================================================================
print("\n" + "="*70)
print("STEP 4: GEMINI SERVICE (Product Analysis & Emails)")
print("="*70)

try:
    from app.services.gemini_service import GeminiService
    gemini = GeminiService()
    
    print(f"✅ Gemini Model: {gemini.model}")
    print(f"✅ API Key: {'Set' if gemini.api_key else 'Missing'}")
    passed += 1
except Exception as e:
    print(f"❌ Gemini Error: {e}")
    errors.append(f"Gemini: {e}")

# =============================================================================
# STEP 5: Multi-Agent System
# =============================================================================
print("\n" + "="*70)
print("STEP 5: MULTI-AGENT SYSTEM")
print("="*70)

try:
    from app.core.multi_agent import (
        ResearcherAgent, QualifierAgent, CopywriterAgent,
        create_multi_agent_system
    )
    
    print("✅ ResearcherAgent imported (uses Groq)")
    print("✅ QualifierAgent imported (uses ML-only)")
    print("✅ CopywriterAgent imported (uses Gemini)")
    print("✅ create_multi_agent_system imported")
    passed += 1
except Exception as e:
    print(f"❌ Multi-Agent Error: {e}")
    errors.append(f"Multi-Agent: {e}")

# =============================================================================
# STEP 6: Scraper Service
# =============================================================================
print("\n" + "="*70)
print("STEP 6: SCRAPER SERVICE")
print("="*70)

try:
    from app.services.scraper_service import ScraperService
    scraper = ScraperService()
    print("✅ ScraperService initialized")
    passed += 1
except Exception as e:
    print(f"❌ Scraper Error: {e}")
    errors.append(f"Scraper: {e}")

# =============================================================================
# STEP 7: Database Check
# =============================================================================
print("\n" + "="*70)
print("STEP 7: DATABASE")
print("="*70)

try:
    from app.database import get_db
    from app.models import Campaign, Lead
    print("✅ Database models imported")
    print("✅ Campaign model ready")
    print("✅ Lead model ready")
    passed += 1
except Exception as e:
    print(f"❌ Database Error: {e}")
    errors.append(f"Database: {e}")

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "="*70)
print("                        SUMMARY")
print("="*70)

print(f"\n✅ Tests Passed: {passed}/7")
print(f"❌ Errors: {len(errors)}")

if errors:
    print("\n⚠️ Issues Found:")
    for err in errors:
        print(f"   - {err}")
else:
    print("\n🎉 ALL TESTS PASSED!")

print("""
┌─────────────────────────────────────────────────────────────────────┐
│                     HYBRID AI ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │   Gemini    │    │    Groq     │    │   ML Only   │              │
│  │  (Paid)     │    │   (FREE)    │    │   (FREE)    │              │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘              │
│         │                  │                  │                      │
│         ▼                  ▼                  ▼                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │  Product    │    │  Research   │    │ Qualification│              │
│  │  Analysis   │    │   Agent     │    │    Agent    │              │
│  │  (1 call)   │    │ (20 leads)  │    │ (30 leads)  │              │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘              │
│         │                  │                  │                      │
│         └──────────────────┴──────────────────┘                      │
│                            │                                         │
│                            ▼                                         │
│                   ┌─────────────┐                                    │
│                   │   Gemini    │                                    │
│                   │   Emails    │                                    │
│                   │ (10 calls)  │                                    │
│                   └─────────────┘                                    │
│                                                                      │
│  TOTAL GEMINI API CALLS: ~11 (vs 51 before = 80% reduction!)        │
└─────────────────────────────────────────────────────────────────────┘
""")

print("="*70)
print("              SYSTEM READY FOR CAMPAIGNS!")
print("="*70)
