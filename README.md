# 🚀 AI-Powered B2B Sales Agent

An autonomous multi-agent system that automates outbound sales campaigns. It discovers, researches, qualifies, and engages B2B leads using AI-driven orchestration with LangGraph, maximizing conversion rates through personalized outreach.

![System Architecture](system_flow_diagram.png)

## 🌟 Key Features

*   **🕵️‍♂️ Automated Lead Discovery**: Finds companies via SerpAPI/Google Custom Search.
*   **🔬 Deep Research Agent**: Scrapes websites (static + Playwright) to extract emails, tech stacks, and decision-makers.
*   **🎯 Smart Qualification**: Scores leads using XGBoost ML models + Semantic Analysis (HOT/WARM/COLD).
*   **✍️ Hyper-Personalized Emails**: Generates unique emails using Gemini/Groq tailored to each prospect.
*   **🧠 Auto-Learning Pipeline**: Analyzes replies to retrain the ML model and improve future performance.
*   **📊 Real-Time Dashboard**: React-based UI for monitoring campaigns and leads live.

---

## 🛠️ Prerequisites

Before running the project, ensure you have the following installed:

1.  **Python 3.10+**: [Download](https://www.python.org/downloads/)
2.  **Node.js 18+**: [Download](https://nodejs.org/)
3.  **PostgreSQL**: [Download](https://www.postgresql.org/download/)
    *   *Requirement*: Create a database named `sales_agent_db`.
    *   `createdb sales_agent_db` (if using command line tool)
4.  **API Keys** (See `.env.example`):
    *   **Gemini API** (Google AI Studio)
    *   **SerpAPI** (Google Search)
    *   **Groq API** (Optional, for fast research)
    *   **Google/Outlook App Password** (For sending emails)

---

## 🚀 Quick Start (Windows)

The easiest way to run the application is using the provided batch script.

1.  **Configure Environment**:
    *   Go to `sales-agent\backend`.
    *   Copy `.env.example` to `.env`.
    *   **Edit `.env`** and add your API keys and Database URL.
    ```ini
    DATABASE_URL=postgresql://postgres:password@localhost:5432/sales_agent_db
    GEMINI_API_KEY=your_key_here
    SERPAPI_KEY=your_key_here
    ...
    ```

2.  **Run the App**:
    *   Open terminal in the `sales-agent` directory.
    *   Run:
        ```cmd
        .\start.bat
        ```
    *   This script will:
        *   Start the FastAPI Backend (Port 8000).
        *   Start the React Frontend (Port 5173).

3.  **Access the Dashboard**:
    *   Frontend: [http://localhost:5173](http://localhost:5173)
    *   Backend API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔧 Manual Installation & Setup

If `start.bat` doesn't work or you are on Linux/Mac, follow these steps.

### 1. Backend Setup

```bash
cd backend

# Create Virtual Environment
python -m venv venv

# Activate Virtual Environment
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

# Install Dependencies
pip install -r requirements.txt

# Run Database Migrations (if needed)
# The app often initializes DB on start, but ensure DB exists.

# Start Server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup

```bash
cd frontend

# Install Dependencies
npm install

# Start Dev Server
npm run dev
```

---

## 📖 Usage Guide

1.  **Login/Register**: Create an account on the dashboard.
2.  **Create Campaign**:
    *   Click "New Campaign".
    *   Enter Product Name (e.g., "AI Analytics Tool") and Target Audience (e.g., "CTOs in FinTech").
3.  **Start Campaign**:
    *   The **Orchestrator** kicks in.
    *   **Step 1**: Analyzes your product to generate search terms.
    *   **Step 2**: Finds leads via Google.
    *   **Step 3**: **Researcher Agent** scrapes their sites.
    *   **Step 4**: **Qualifier Agent** scores them (look for 🔥 HOT leads).
    *   **Step 5**: **Copywriter Agent** drafts emails.
4.  **Monitor**: Watch the "Live Feed" to see agents working in real-time.

---

## 📂 Project Structure

```
sales-agent/
├── backend/               # FastAPI Application
│   ├── app/
│   │   ├── core/          # Orchestrator & LangGraph Agents
│   │   ├── api/           # REST Endpoints
│   │   ├── services/      # Scraping, Email, ML Services
│   │   └── models/        # Database & Pydantic Models
│   ├── models/            # Trained XGBoost Models
│   └── start_server.bat
│
├── frontend/              # React + Vite Application
│   ├── src/
│   │   ├── components/    # Reusable UI Components
│   │   ├── pages/         # Application Views/Routes
│   │   └── context/       # Auth & State Management
│   └── package.json
│
├── start.bat              # One-click startup script
└── SYSTEM_DESIGN.md       # Detailed technical documentation
```

## 🏗️ Architecture

```mermaid
graph TD
    User[User] -->|Create Campaign| API[FastAPI Backend]
    API -->|Start Workflow| Orch[LangGraph Orchestrator]
    
    subgraph "Multi-Agent System"
        Orch -->|Search| WA[Web Search]
        WA -->|Results| RA[Researcher Agent]
        RA -->|Scraped Data| QA[Qualifier Agent]
        QA -->|Score & Filter| CA[Copywriter Agent]
    end
    
    subgraph "Services"
        RA -- Uses --> SM[Scraper Service]
        QA -- Uses --> ML[XGBoost Model]
        CA -- Uses --> LLM[Gemini/Groq API]
    end
    
    CA -->|Drafts| DB[(PostgreSQL)]
    DB -->|Visuals| FE[React Frontend]
```

---
**Note**: Ensure your `DATABASE_URL` is correct in `.env` before running!
