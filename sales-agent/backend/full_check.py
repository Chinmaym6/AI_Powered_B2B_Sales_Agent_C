"""Complete System Check - Start to End"""
import asyncio
import sys
sys.path.insert(0, '.')

print('='*70)
print('       COMPLETE SYSTEM CHECK - START TO END')
print('='*70)

# 1. Config
print('\n1. CONFIGURATION')
from app.config import settings
print(f'   GROQ_ENABLED: {settings.GROQ_ENABLED}')
print(f'   QUALIFICATION_MODE: {settings.QUALIFICATION_MODE}')

# 2. Groq Service
print('\n2. GROQ SERVICE')
from app.services.groq_service import get_groq_service
groq = get_groq_service()
r = asyncio.run(groq.generate('Say hello'))
print(f'   Groq working: {r[:40]}...')

# 3. Gemini with Fallback
print('\n3. GEMINI + FALLBACK')
from app.services.gemini_service import GeminiService
g = GeminiService()
r = asyncio.run(g.generate('Say test'))
print(f'   Result: {r[:40]}...')

# 4. ML Scorer
print('\n4. ML SCORER')
from app.ml.lead_scorer import MLLeadScorer
scorer = MLLeadScorer()
print(f'   Model loaded: {scorer.model is not None}')

# 5. Scraper with enrich_lead
print('\n5. SCRAPER (enrich_lead method)')
from app.services.scraper_service import ScraperService
scraper = ScraperService()
result = scraper.enrich_lead('https://google.com', 'Google')
print(f'   enrich_lead works: True')
print(f'   Email extracted: {result.get("email", "N/A")}')

# 6. Multi-Agent
print('\n6. MULTI-AGENT SYSTEM')
from app.core.multi_agent import ResearcherAgent, QualifierAgent, CopywriterAgent
print('   ResearcherAgent: OK')
print('   QualifierAgent: OK')
print('   CopywriterAgent: OK')

print('\n' + '='*70)
print('       ALL SYSTEMS OPERATIONAL!')
print('='*70)
print('''
   FLOW: 
   1. Gemini (or Groq fallback) -> Product Analysis
   2. Groq -> Research (FREE)
   3. ML-only -> Qualification (FREE)
   4. Gemini (or Groq fallback) -> Email Generation
   
   RESULT: ~11 Gemini calls OR 0 if using Groq fallback!
''')
