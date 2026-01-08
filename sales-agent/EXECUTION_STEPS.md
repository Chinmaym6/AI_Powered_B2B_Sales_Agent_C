# ⚡ Execution Steps for AI Sales Agent

This guide focuses strictly on getting the application running on your machine.

---

## ✅ Prerequisites Checklist

Before you start, make sure you have these 3 things installed:

1.  **Python** (3.10 or newer)
    *   Verify: `python --version`
2.  **Node.js** (18 or newer)
    *   Verify: `node --version`
3.  **PostgreSQL** (Running)
    *   Verify by checking if you can connect to your local database.
    *   **Required Database Name**: `sales_agent_db`

---

## 🏃 Option A: The "One-Click" Start (Windows)

We have created a batch script that handles everything for you.

1.  Open the folder: `AI_Powered_B2B_Sales_Agent_C\sales-agent`
2.  Double-click **`start.bat`**
3.  Two windows will open:
    *   **Backend Window**: Shows "Uvicorn running on http://0.0.0.0:8000"
    *   **Frontend Window**: Shows "Local: http://localhost:5173"

**Done!** Go to [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🛠️ Option B: Manual Execution (Step-by-Step)

If the script fails or you prefer manual control, follow these steps exactly.

### Phase 1: Configure Environment

1.  Navigate to `sales-agent\backend`.
2.  Copy `.env.example` and rename it to `.env`.
3.  Open `.env` in a text editor (Notepad, VS Code).
4.  **CRITICAL**: Update the `DATABASE_URL` with your postgres password.
    *   Format: `postgresql://postgres:YOUR_PASSWORD@localhost:5432/sales_agent_db`
5.  Add your `GEMINI_API_KEY` and `SERPAPI_KEY`.

### Phase 2: Start the Backend

1.  Open a Terminal (Command Prompt / PowerShell).
2.  Move to the backend folder:
    ```powershell
    cd sales-agent\backend
    ```
3.  Create/Activate Virtual Environment:
    ```powershell
    # Create (only need to do this once)
    python -m venv venv
    
    # Activate
    .\venv\Scripts\activate
    ```
4.  Install Requirements (only need to do this once):
    ```powershell
    pip install -r requirements.txt
    ```
5.  **Run the Server**:
    ```powershell
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    *   *Success Message*: "Application startup complete."

### Phase 3: Start the Frontend

1.  Open a **New** Terminal window.
2.  Move to the frontend folder:
    ```powershell
    cd sales-agent\frontend
    ```
3.  Install Dependencies (only need to do this once):
    ```powershell
    npm install
    ```
4.  **Run the UI**:
    ```powershell
    npm run dev
    ```
    *   *Success Message*: "➜  Local:   http://localhost:5173/"

---

## ❓ Troubleshooting

### ❌ Error: "database 'sales_agent_db' does not exist"
**Fix**: You need to create the database in Postgres.
Run this command in your terminal (if you have psql installed):
```cmd
createdb -U postgres sales_agent_db
```
Or use pgAdmin to create a new database named `sales_agent_db`.

### ❌ Error: "Address already in use"
**Fix**: Another program is using port 8000 or 5173.
*   Check if you have another terminal running the agent.
*   Close it and try again.

### ❌ Error: "Module not found"
**Fix**: You probably didn't activate the virtual environment.
Make sure you see `(venv)` at the start of your terminal line before running `uvicorn`.

---

## 🔗 Links

*   **App Dashboard**: [http://localhost:5173](http://localhost:5173)
*   **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
