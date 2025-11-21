# Deep Dive: Scraping & Gemini AI Integration Flow

This document explains the technical details of how the `ScraperService` gathers data and how `Gemini AI` processes it to ensure high-quality leads.

## 1. The Scraping Engine (`ScraperService`)

The scraper is designed to be robust and thorough, using a multi-stage approach to gather as much context as possible.

### Step 1: Intelligent Strategy Selection
When a URL is provided, the service decides how to scrape it:
1.  **Static Scraping (Fast)**: It first tries using standard HTTP requests (`requests` library). This is fast and works for most simple business sites.
2.  **Dynamic Scraping (Fallback)**: If static scraping fails to find a description or email, it automatically switches to a **Headless Browser (Playwright)**. This renders the full JavaScript of the page, allowing it to see content hidden behind React/Vue/Angular apps.

### Step 2: Deep Context Gathering (Sub-page Crawling)
To understand a company, looking at the homepage isn't enough. The scraper now performs a "Deep Crawl":
1.  **Link Discovery**: It scans the homepage for internal links matching keywords like:
    *   `about`, `company`, `story` (to understand who they are)
    *   `product`, `service`, `solution` (to understand what they do)
    *   `contact`, `team`, `career` (to find people and emails)
2.  **Content Aggregation**: It visits up to 3 of these relevant sub-pages and extracts their text.
3.  **Context Merging**: The text from the homepage and these sub-pages is combined into a single `full_content` block (truncated to ~5000 characters) to give the AI a complete picture.

### Step 3: Data Extraction Logic
The scraper uses specific heuristics to extract structured data:
*   **Emails**:
    *   Regex pattern matching for standard emails.
    *   `mailto:` link extraction (often missed by regex).
    *   Obfuscation decoding (e.g., "sales [at] company [dot] com").
    *   **Priority Filtering**: It prioritizes emails starting with `contact`, `sales`, `info`, `hello` over generic ones.
*   **Decision Makers**: It looks for "Team" sections and extracts names/titles, filtering for C-level (CEO, CTO) and VPs.
*   **Socials**: Extracts LinkedIn company profile URLs.

---

## 2. The AI Brain (`GeminiService` & `AutonomousAgent`)

Once the data is scraped, Gemini AI takes over to "think" about the lead. This happens in four distinct stages.

### Stage 1: Strict Relevance Verification (The Gatekeeper)
Before saving a lead, the agent asks Gemini to act as a strict judge.
*   **Input**: The `full_content` (Homepage + About + Services text) + Campaign Target Industry + Product Description.
*   **Prompt**:
    > "You are a strict lead qualification expert. Determine if this company is a GOOD MATCH...
    > 1. Does this company operate in the target industry?
    > 2. Would they realistically have a need for this product?
    > 3. Are they a potential buyer (B2B)?"
*   **Outcome**: If Gemini says `is_match: false`, the lead is **discarded immediately**. This prevents "junk" leads from entering the system.

### Stage 2: Enrichment
If the lead passes verification, Gemini analyzes the text to fill in the blanks.
*   **Task**: Infer missing details that weren't explicitly stated but are implied.
*   **Extraction**: It identifies specific technologies used, business model (B2B/B2C), and key pain points mentioned in their copy.

### Stage 3: Scoring (0-100)
Gemini evaluates the lead against the Ideal Customer Profile (ICP).
*   **Prompt**: "Score this lead from 0-100 based on fit."
*   **Factors**:
    *   **Industry Fit**: Is it a perfect match or just adjacent?
    *   **Company Size**: Are they the right size for the product?
    *   **Tech Stack**: Do they use compatible technologies?
*   **Result**: A score and a "Score Explanation" (e.g., "High fit because they explicitly mention needing supply chain optimization").

### Stage 4: Hyper-Personalized Email Generation
Finally, Gemini writes the outreach email.
*   **Input**: Lead Name, Company Name, `full_content`, Product Benefits.
*   **Prompt**:
    > "Write a professional B2B cold email...
    > Reference specific company details found in the context...
    > Connect their specific business needs to our product benefits..."
*   **Output**: A unique email for *that specific company*. It might say "I noticed you recently expanded your logistics team..." instead of a generic opening.

---

## Summary of Data Flow

1.  **Scraper** -> Raw HTML -> **Text & Metadata** (Emails, Names)
2.  **Scraper** -> Sub-pages -> **Full Context**
3.  **Agent** -> Full Context -> **Gemini (Verification)** -> Pass/Fail
4.  **Agent** -> Valid Lead -> **Gemini (Enrichment & Scoring)** -> Scored Lead
5.  **Agent** -> Scored Lead -> **Gemini (Email Gen)** -> Final Email
