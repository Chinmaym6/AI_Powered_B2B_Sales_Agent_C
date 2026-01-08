# 🏗️ AI-Powered B2B Sales Agent - System Design

## Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Technology Stack](#technology-stack)
4. [Multi-Agent System](#multi-agent-system)
5. [Database Schema](#database-schema)
6. [ML Pipeline](#ml-pipeline)
7. [Service Layer](#service-layer)
8. [API Design](#api-design)
9. [Frontend Architecture](#frontend-architecture)
10. [Data Flow](#data-flow)
11. [Security & Authentication](#security--authentication)
12. [External Integrations](#external-integrations)
13. [Real-Time Communication](#real-time-communication)
14. [Auto-Learning Pipeline](#auto-learning-pipeline)
15. [Deployment Architecture](#deployment-architecture)

---

## System Overview

The **AI-Powered B2B Sales Agent** is an autonomous multi-agent system that automates outbound sales campaigns. It discovers, researches, qualifies, and engages B2B leads using AI-driven orchestration with LangGraph.

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Lead Discovery** | Automated search via SerpAPI/Google Custom Search |
| **Deep Research** | Web scraping with Playwright + BeautifulSoup |
| **AI Qualification** | XGBoost ML scoring + semantic matching |
| **Email Generation** | Personalized multi-variant emails via Gemini/Groq |
| **Auto-Learning** | Sentiment analysis of replies for model retraining |

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    React + Vite Frontend (TypeScript/JSX)             │  │
│  │   Dashboard │ Campaign Form │ Lead Cards │ Live Feed │ Auth Pages    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ HTTP/WebSocket
┌────────────────────────────────▼────────────────────────────────────────────┐
│                                API LAYER                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     FastAPI Backend (Python)                          │  │
│  │   /api/campaigns │ /api/auth │ /api/email-monitor │ WebSocket /ws    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────────┐
│                           ORCHESTRATION LAYER                                │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    LangGraph Multi-Agent Workflow                     │  │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                 │  │
│  │  │ Researcher  │──▶│ Qualifier   │──▶│ Copywriter  │                 │  │
│  │  │   Agent     │   │   Agent     │   │   Agent     │                 │  │
│  │  └─────────────┘   └─────────────┘   └─────────────┘                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────────┐
│                             SERVICE LAYER                                    │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌───────────┐ │
│  │ Gemini     │ │ Groq       │ │ Scraper    │ │ Email      │ │ Sentiment │ │
│  │ Service    │ │ Service    │ │ Service    │ │ Service    │ │ Service   │ │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └───────────┘ │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────────┐
│                               ML LAYER                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │ XGBoost Lead Scorer │ SHAP Explainer │ Embeddings │ Response Classifier│  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────────┐
│                               DATA LAYER                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      PostgreSQL Database                              │  │
│  │  campaigns │ leads │ emails │ users │ ml_models │ lead_outcomes      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | FastAPI | Async REST API + WebSocket |
| **Database** | PostgreSQL | Persistent data storage |
| **ORM** | SQLAlchemy | Database interactions |
| **AI Orchestration** | LangGraph | Multi-agent workflow |
| **LLM APIs** | Gemini, Groq | Text generation |
| **ML** | XGBoost, SHAP | Lead scoring + explanations |
| **Embeddings** | sentence-transformers | Semantic similarity |
| **Scraping** | Playwright, BeautifulSoup | Web data extraction |
| **Email** | SMTP (smtplib), IMAP | Send/receive emails |

### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | React 18 | UI rendering |
| **Build Tool** | Vite | Fast development |
| **Language** | TypeScript + JSX | Type safety |
| **Styling** | TailwindCSS | Utility-first CSS |
| **State** | React Context | Global state management |
| **HTTP Client** | Fetch API | API communication |

---

## Multi-Agent System

### Agent Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   MultiAgentOrchestrator                        │
│                  (LangGraph StateGraph)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   PHASE 1: analyze_product                                      │
│        ↓                                                        │
│   PHASE 2: search_leads                                         │
│        ↓                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ PHASE 3: research_phase                                 │   │
│   │  ┌───────────────────────────────────────────────────┐  │   │
│   │  │           🔬 ResearcherAgent                      │  │   │
│   │  │  • Web scraping via ScraperService                │  │   │
│   │  │  • Uses Groq API (fast, saves Gemini quota)       │  │   │
│   │  │  • Extracts: email, description, tech stack       │  │   │
│   │  │  • Batch processing with semaphore (5 concurrent) │  │   │
│   │  └───────────────────────────────────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────┘   │
│        ↓                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ PHASE 4: qualify_phase                                  │   │
│   │  ┌───────────────────────────────────────────────────┐  │   │
│   │  │           🎯 QualifierAgent                       │  │   │
│   │  │  • ML scoring via XGBoost                         │  │   │
│   │  │  • SHAP explanations                              │  │   │
│   │  │  • Semantic similarity matching                   │  │   │
│   │  │  • Modes: ml_only, ml_ai, ai_only                 │  │   │
│   │  └───────────────────────────────────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────┘   │
│        ↓                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ PHASE 5: copywrite_phase                                │   │
│   │  ┌───────────────────────────────────────────────────┐  │   │
│   │  │           ✍️ CopywriterAgent                      │  │   │
│   │  │  • Generates 3 email variants per lead            │  │   │
│   │  │  • Styles: INSIGHT-LED, DIRECT-PITCH, SOCIAL-PROOF│  │   │
│   │  │  • Uses Gemini API for personalization            │  │   │
│   │  └───────────────────────────────────────────────────┘  │   │
│   └─────────────────────────────────────────────────────────┘   │
│        ↓                                                        │
│   PHASE 6: save_leads                                           │
│        ↓                                                        │
│   PHASE 7: send_emails (conditional: ≥3 qualified leads)        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### State Schema

```python
class MultiAgentState(TypedDict):
    campaign_id: str
    campaign: Dict
    current_phase: str
    progress: float
    product_analysis: Dict
    raw_leads: List[Dict]           # From search
    researched_leads: List[Dict]    # After ResearcherAgent
    qualified_leads: List[Dict]     # After QualifierAgent
    leads_with_emails: List[Dict]   # After CopywriterAgent
    agent_outputs: List[Dict]
    errors: List[str]
    emails_sent: int
```

### Key Files

| File | Purpose |
|------|---------|
| `app/core/multi_agent.py` | Multi-agent orchestrator (921 lines) |
| `app/core/agent_prompts.py` | Specialized system prompts |
| `app/core/langgraph_agent.py` | Single-agent fallback |
| `app/core/agent.py` | Legacy autonomous agent |

---

## Database Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                         users                                    │
├─────────────────────────────────────────────────────────────────┤
│ id (UUID, PK)                                                   │
│ email (String, UNIQUE)                                          │
│ hashed_password (String)                                        │
│ full_name (String)                                              │
│ created_at (DateTime)                                           │
└───────────────────────────────┬─────────────────────────────────┘
                                │ 1:N
┌───────────────────────────────▼─────────────────────────────────┐
│                        campaigns                                 │
├─────────────────────────────────────────────────────────────────┤
│ id (UUID, PK)                                                   │
│ user_id (UUID, FK → users)                                      │
│ name, product_name, product_description                         │
│ target_industry, target_audience, company_size                  │
│ target_regions (ARRAY[String])                                  │
│ status (String: active/paused/completed)                        │
│ product_analysis (JSONB)                                        │
│ execution_state (String: idle/running/paused/completed/failed)  │
│ current_step, progress_percentage, leads_processed, leads_total │
│ can_resume (Boolean)                                            │
│ created_at, updated_at, last_activity_at                        │
└───────────────────────────────┬─────────────────────────────────┘
                                │ 1:N
┌───────────────────────────────▼─────────────────────────────────┐
│                          leads                                   │
├─────────────────────────────────────────────────────────────────┤
│ id (UUID, PK)                                                   │
│ campaign_id (UUID, FK → campaigns, CASCADE)                     │
│ company_name, industry, website, description                    │
│ company_size (Integer), location                                │
│ decision_maker_name, decision_maker_title                       │
│ email, linkedin_url                                             │
│ rule_based_score, ml_score, ml_confidence, ml_model_version     │
│ score_explanation (JSONB)                                       │
│ description_embedding (ARRAY[Float])                            │
│ actual_outcome (Integer: 1=good, 0=bad, NULL=unknown)           │
│ reply_received, reply_sentiment, reply_confidence, reply_intent │
│ replied_at, needs_manual_review, auto_labeled                   │
│ status (String: new/contacted/replied/converted)                │
│ created_at, updated_at                                          │
└───────────────────────────────┬─────────────────────────────────┘
                                │ 1:N
┌───────────────────────────────▼─────────────────────────────────┐
│                          emails                                  │
├─────────────────────────────────────────────────────────────────┤
│ id (UUID, PK)                                                   │
│ lead_id (UUID, FK → leads, CASCADE)                             │
│ subject, body (Text)                                            │
│ status (String: pending/sent/opened/replied)                    │
│ sent_at, opened_at, clicked_at, replied_at                      │
│ reply_text, reply_sentiment, reply_intent, reply_confidence     │
│ processed_for_sentiment (Boolean)                               │
│ message_id (String, for threading)                              │
│ created_at                                                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        ml_models                                 │
├─────────────────────────────────────────────────────────────────┤
│ id (UUID, PK)                                                   │
│ model_type, version, model_path                                 │
│ accuracy, precision_score, recall_score, f1_score               │
│ num_training_samples, hyperparameters (JSONB)                   │
│ is_active (Boolean), trained_at                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      lead_outcomes                               │
├─────────────────────────────────────────────────────────────────┤
│ id (UUID, PK)                                                   │
│ lead_id (UUID, FK → leads)                                      │
│ replied, reply_sentiment                                        │
│ converted_to_call, converted_to_customer                        │
│ revenue_generated, user_quality_rating, notes                   │
│ recorded_at                                                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      model_feedback                              │
├─────────────────────────────────────────────────────────────────┤
│ id (UUID, PK)                                                   │
│ lead_id (UUID, FK → leads)                                      │
│ model_version, predicted_score, actual_quality                  │
│ user_id, feedback_timestamp                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## ML Pipeline

### XGBoost Lead Scorer

```
┌─────────────────────────────────────────────────────────────────┐
│                     MLLeadScorer                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INPUT: lead dict + product_analysis                            │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │             Feature Extraction (15 features)            │    │
│  │  • industry_match (0/1)                                 │    │
│  │  • company_size (normalized)                            │    │
│  │  • has_email, has_linkedin (0/1)                        │    │
│  │  • has_decision_maker (0/1)                             │    │
│  │  • description_length (normalized)                      │    │
│  │  • keyword_match_score (0-1)                            │    │
│  │  • semantic_similarity (0-1)                            │    │
│  │  • has_website, domain_quality                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           XGBoost Model Prediction                      │    │
│  │     models/lead_scorer_v1.json                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│           │                                                     │
│           ▼                                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           SHAP Explanation                              │    │
│  │  • Top 5 contributing factors                           │    │
│  │  • Human-readable explanations                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│           │                                                     │
│           ▼                                                     │
│  OUTPUT: {                                                      │
│    "score": 0.85,                                               │
│    "confidence": 0.92,                                          │
│    "factors": [{"feature": "Industry Match", "impact": +0.15}]  │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

### Scoring Tiers

| Score | Tier | Action |
|-------|------|--------|
| 80-100 | 🔥 HOT | Immediate outreach |
| 60-79 | 🟡 WARM | Worth pursuing |
| 40-59 | 🔵 COLD | Needs nurturing |
| 0-39 | ❌ DISQUALIFY | Skip |

---

## Service Layer

### ScraperService

```python
class ScraperService:
    """Dual-strategy web scraping"""
    
    def scrape_website(url: str) -> Dict:
        # Strategy 1: Fast static scraping (requests + BeautifulSoup)
        # Strategy 2: Playwright for JS-heavy sites
        
    def _extract_email(text, soup) -> str:
        # Smart email extraction with validation
        
    def _extract_description(soup) -> str:
        # Multi-strategy description extraction
        
    def enrich_lead(url, company_name) -> Dict:
        # Full lead enrichment for ResearcherAgent
```

### EmailService

| Feature | Implementation |
|---------|---------------|
| Testing Mode | MailHog (no auth, port 1025) |
| Production | Gmail SMTP with TLS (port 587) |
| Authentication | App Password for Gmail |

### GeminiService / GroqService

| Service | Use Case | Quota Strategy |
|---------|----------|----------------|
| **Gemini** | Email generation, complex analysis | Conservative usage |
| **Groq** | Research, fast inference | 14,400 req/day FREE |

---

## API Design

### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/auth/register` | User registration |
| `POST` | `/api/auth/login` | JWT authentication |
| `GET` | `/api/campaigns` | List campaigns |
| `POST` | `/api/campaigns` | Create campaign |
| `GET` | `/api/campaigns/{id}` | Campaign details |
| `POST` | `/api/campaigns/{id}/start` | Start campaign |
| `POST` | `/api/campaigns/{id}/stop` | Stop campaign |
| `GET` | `/api/campaigns/{id}/leads` | Campaign leads |
| `GET` | `/api/email-monitor/check` | Check for replies |
| `GET` | `/api/email-monitor/stats` | Monitoring stats |
| `WS` | `/ws/{campaign_id}` | Real-time updates |

### WebSocket Events

```javascript
// Server → Client
{
  "type": "status" | "lead" | "email" | "error",
  "message": "Processing lead...",
  "data": {...}
}
```

---

## Frontend Architecture

### Component Hierarchy

```
App.jsx
├── AuthContext (Context Provider)
├── Routes
│   ├── LandingPage.tsx
│   ├── LoginPage.tsx
│   ├── RegisterPage.tsx
│   ├── AllCampaignsPage.tsx
│   └── CreateCampaign.jsx
│
└── Components
    ├── Dashboard.jsx (Campaign overview)
    ├── CampaignDetails.jsx (Full campaign view)
    ├── CampaignForm.jsx (Create/Edit form)
    ├── LeadCard.jsx (Individual lead display)
    ├── LiveFeed.jsx (Real-time updates)
    └── MLScoreExplanation.jsx (SHAP visualization)
```

---

## Data Flow

### Campaign Execution Flow

```
User Creates Campaign
        │
        ▼
┌───────────────────┐
│ 1. Analyze Product│ ← Gemini: Extract keywords, ICP, value props
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ 2. Search Leads   │ ← SerpAPI/Google: Find companies
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ 3. Research Phase │ ← ResearcherAgent: Scrape websites, extract data
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ 4. Qualify Phase  │ ← QualifierAgent: ML scoring + semantic matching
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ 5. Copywrite Phase│ ← CopywriterAgent: Generate 3 email variants
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ 6. Save to DB     │ ← PostgreSQL: Persist leads + emails
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ 7. Send Emails    │ ← SMTP: Deliver personalized emails
└─────────┬─────────┘
          │
          ▼
    Campaign Complete
```

---

## Security & Authentication

| Layer | Implementation |
|-------|---------------|
| **Authentication** | JWT tokens (PyJWT) |
| **Password Hashing** | bcrypt |
| **CORS** | FastAPI CORSMiddleware |
| **Secrets** | Environment variables (.env) |
| **API Keys** | Stored in settings, never exposed |

---

## External Integrations

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **Gemini API** | LLM for analysis/generation | `GEMINI_API_KEY` |
| **Groq API** | Fast LLM for research | `GROQ_API_KEY` |
| **SerpAPI** | Google search results | `SERPAPI_KEY` |
| **Google Custom Search** | Alternative search | `GOOGLE_SEARCH_API_KEY`, `GOOGLE_CSE_ID` |
| **Gmail SMTP** | Email sending | `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS` |
| **Gmail IMAP** | Reply monitoring | `IMAP_HOST`, `IMAP_USER`, `IMAP_PASS` |

---

## Real-Time Communication

```
┌─────────┐              ┌─────────────┐              ┌──────────┐
│ Frontend│◀─────────────│  WebSocket  │◀─────────────│  Backend │
│ (React) │   /ws/{id}   │   Server    │   emit()     │  (Agent) │
└─────────┘              └─────────────┘              └──────────┘
     │                                                      │
     │  Events: status, lead, email, error                  │
     └──────────────────────────────────────────────────────┘
```

---

## Auto-Learning Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│                    Auto-Learning Feedback Loop                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   1. Email Sent → Lead marked 'contacted'                        │
│                     │                                            │
│                     ▼                                            │
│   2. EmailMonitorService checks inbox (IMAP/MailHog)             │
│                     │                                            │
│                     ▼                                            │
│   3. Reply detected → SentimentService analyzes                  │
│         │                                                        │
│         ├─→ Positive (interested) → actual_outcome = 1           │
│         ├─→ Negative (not interested) → actual_outcome = 0       │
│         └─→ Neutral → needs_manual_review = True                 │
│                     │                                            │
│                     ▼                                            │
│   4. Labeled leads accumulate (MIN_LABELS_FOR_RETRAIN = 50)      │
│                     │                                            │
│                     ▼                                            │
│   5. Auto-retrain XGBoost model with new data                    │
│                     │                                            │
│                     ▼                                            │
│   6. New model version deployed (ml_models table)                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Local Development

```bash
# Backend
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend
cd frontend
npm run dev  # Vite dev server on port 5173
```

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/sales_agent_db

# AI APIs
GEMINI_API_KEY=your_key
GROQ_API_KEY=your_key
GROQ_ENABLED=true
QUALIFICATION_MODE=ml_only

# Search
SERPAPI_KEY=your_key

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASS=app_password
EMAIL_FROM=your@gmail.com

# Monitoring
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=your@gmail.com
IMAP_PASS=app_password

# Feature Flags
USE_LANGGRAPH=true
MAX_LEADS_TO_RESEARCH=20
MAX_EMAILS_TO_GENERATE=10
```

### Directory Structure

```
sales-agent/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # FastAPI routers
│   │   ├── core/            # Agent system
│   │   ├── ml/              # ML models
│   │   ├── models/          # Database models
│   │   ├── services/        # Business logic
│   │   ├── jobs/            # Scheduled tasks
│   │   ├── config.py        # Settings
│   │   └── main.py          # Entry point
│   ├── models/              # Trained ML models (.json, .pkl)
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/             # API client
│   │   ├── components/      # React components
│   │   ├── context/         # State management
│   │   └── pages/           # Route pages
│   ├── package.json
│   └── vite.config.ts
│
├── MULTI_AGENT_README.md    # Agent documentation
├── HOW_MULTI_AGENT_WORKS.md # Detailed workflow
└── SYSTEM_DESIGN.md         # This document
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Multi-Agent over Single Agent** | Specialized prompts yield better results |
| **Groq for Research** | Free tier (14k/day), saves Gemini quota |
| **XGBoost + SHAP** | Fast inference + explainable predictions |
| **LangGraph StateGraph** | Structured workflow with checkpointing |
| **Dual Scraping Strategy** | Static for speed, Playwright for JS sites |
| **Auto-Learning Loop** | Model improves from real email responses |

---

*Last Updated: December 2024*
*Version: 2.0.0*
