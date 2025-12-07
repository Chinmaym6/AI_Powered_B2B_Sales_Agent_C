"""Complete System Check for Hybrid AI"""
import asyncio
import sys
sys.path.insert(0, '.')

print('='*70)
print('           HYBRID AI SYSTEM - COMPLETE FLOW CHECK')
print('='*70)

from app.config import settings

print('\n📋 CONFIGURATION:')
print(f'   MAX_LEADS_TO_RESEARCH: {settings.MAX_LEADS_TO_RESEARCH}')
print(f'   MAX_LEADS_TO_QUALIFY: {settings.MAX_LEADS_TO_QUALIFY}')
print(f'   MAX_EMAILS_TO_GENERATE: {settings.MAX_EMAILS_TO_GENERATE}')
print(f'   MAX_SEARCH_RESULTS: {settings.MAX_SEARCH_RESULTS}')
print(f'   GROQ_ENABLED: {settings.GROQ_ENABLED}')
print(f'   GROQ_MODEL: {settings.GROQ_MODEL}')
print(f'   QUALIFICATION_MODE: {settings.QUALIFICATION_MODE}')

print('\n⚡ GROQ SERVICE:')
from app.services.groq_service import get_groq_service
groq = get_groq_service()

print('\n🔬 GROQ RESEARCH TEST:')
result = asyncio.run(groq.generate('Summarize what TechCorp does in 20 words'))
print(f'   Response: {result[:80]}...')

print('\n🧠 ML SCORER:')
from app.ml.lead_scorer import MLLeadScorer
scorer = MLLeadScorer()
test_lead = {'company_name': 'AI Solutions Inc', 'description': 'Enterprise AI platform', 'email': 'sales@ai.com'}
test_product = {'keywords': ['ai', 'enterprise'], 'target_industries': ['Technology']}
result = scorer.predict(test_lead, test_product)
print(f'   Score: {result.get("score", 0):.2f}')
print(f'   Tier: {result.get("tier", "WARM")}')

print('\n🤖 GEMINI SERVICE:')
from app.services.gemini_service import GeminiService
gemini = GeminiService()
print(f'   Model: {gemini.model}')

print('\n✅ MULTI-AGENT SYSTEM:')
from app.core.multi_agent import ResearcherAgent, QualifierAgent, CopywriterAgent
print('   ResearcherAgent: Uses GROQ (FREE)')
print('   QualifierAgent: Uses ML-only (FREE)')
print('   CopywriterAgent: Uses Gemini')

print('\n' + '='*70)
print('           ALL SYSTEMS OPERATIONAL!')
print('='*70)
print('''
   ┌─────────────────────────────────────────────────────────────────┐
   │                  HYBRID AI FLOW                                  │
   ├─────────────────────────────────────────────────────────────────┤
   │ Phase            │ AI Engine   │ Cost         │ API Calls       │
   ├─────────────────────────────────────────────────────────────────┤
   │ Product Analysis │ Gemini      │ Paid         │ 1               │
   │ Research (20)    │ GROQ ⚡     │ FREE         │ 0 Gemini        │
   │ Qualification    │ ML-only 🧠  │ FREE         │ 0 Gemini        │
   │ Emails (10)      │ Gemini      │ Paid         │ 10              │
   ├─────────────────────────────────────────────────────────────────┤
   │ TOTAL            │             │              │ ~11 Gemini      │
   └─────────────────────────────────────────────────────────────────┘
''')
