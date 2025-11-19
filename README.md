# Facts-Only MF Assistant

A RAG-based chatbot that answers factual questions about HDFC Mutual Funds using verified sources from AMC, SEBI, and AMFI websites. Provides concise, citation-backed responses while strictly avoiding any investment advice.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Intelligent Systems](#intelligent-systems)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Architecture](#architecture)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Disclaimer](#disclaimer)

---

## Overview

This assistant uses **Retrieval-Augmented Generation (RAG)** with a **two-stage LLM approach** and **LLM-powered intelligent systems** to answer factual questions about mutual funds.

### Scope

**AMC:** HDFC Asset Management Company

**Schemes Covered (4):**
1. HDFC Large Cap Fund
2. HDFC Flexi Cap Fund
3. HDFC TaxSaver (ELSS)
4. HDFC Hybrid Equity Fund

**Sources:** 25 verified sources
- 12 fund-specific sources (3 per fund + consolidated factsheet)
- 8 regulatory sources (AMFI, SEBI)
- 4 help pages (Groww)
- 1 consolidated factsheet

---

## Key Features

### ✅ Core Capabilities
- **Facts-Only:** Answers factual questions with citations
- **Source Attribution:** Every answer includes a citation link
- **Two-Stage RAG:** Query refinement + answer generation
- **Chat History:** Maintains conversation context
- **No Investment Advice:** Strictly refuses advice-seeking queries
- **Multiple LLM Support:** Ollama (local), OpenAI, Anthropic, Gemini

### 🧠 LLM-Powered Intelligence (No Hardcoding!)
- **Intelligent Out-of-Context Detection:** Handles ANY irrelevant query
- **Intelligent Clarification Detection:** Handles ANY ambiguous query
- **Intelligent Query Classification:** 2-stage robust filtering

---

## Intelligent Systems

This chatbot uses **LLM intelligence** instead of hardcoded patterns for key decision-making. This makes it robust, scalable, and zero-maintenance.

### 1. 🎯 Intelligent Out-of-Context Detection

**What it does:** Uses LLM to determine if a query is related to mutual funds.

**Examples:**
| Query | Detection | Result |
|-------|----------|---------|
| "will you go on a date with me" | Out-of-context ✅ | Polite refusal |
| "can u cok" | Out-of-context ✅ | Polite refusal |
| "who is PM of India" | Out-of-context ✅ | Polite refusal |
| "565665" (random number) | Out-of-context ✅ | Polite refusal |
| "how to download CAS" | MF-related ✅ | Factual answer |

**Benefits:**
- ✅ Handles ANY out-of-context query
- ✅ No maintenance needed
- ✅ Understands natural language variations
- ✅ ~$0.00001 per check

### 2. 🔍 Intelligent Clarification Detection

**What it does:** Uses LLM to determine if a query needs a specific fund name.

**Examples:**
| Query | Detection | Result |
|-------|----------|---------|
| "minimum sip amount" | Needs clarification ✅ | "Which fund?" |
| "hmm minimum sip" | Needs clarification ✅ | "Which fund?" |
| "what's the NAV" | Needs clarification ✅ | "Which fund?" |
| "tell me the AUM" | Needs clarification ✅ | "Which fund?" |
| "how to download CAS" | No clarification ✅ | Direct answer |
| "what is ELSS lock-in" | No clarification ✅ | Direct answer |

**Benefits:**
- ✅ Handles ANY ambiguous query (NAV, AUM, returns, inception date, etc.)
- ✅ Understands typos and filler words
- ✅ Zero maintenance
- ✅ Future-proof (new metrics work automatically)

### 3. 🧠 Intelligent Query Classification

**Two-Stage Classification:**

**Stage 1:** Relevance Check
```
is_mutual_fund_related(query) → yes/no
```

**Stage 2:** Intent Classification (if relevant)
```
classify_query_type(query) → greeting | coverage | factual | advice
```

**Benefits:**
- ✅ Robust 2-stage filtering
- ✅ Handles ambiguous queries intelligently
- ✅ No hardcoded patterns needed
- ✅ Graceful fallback if LLM fails

### 💰 Cost Analysis

| System | Cost per Query | Daily Cost (1000 queries) |
|--------|---------------|-------------------------|
| Out-of-context detection | $0.00001 | $0.01 |
| Clarification detection | $0.00001 | $0.01 |
| Query classification | $0.00001 | $0.01 |
| **Total overhead** | **$0.00003** | **$0.03** |

**Negligible cost for infinite scalability!** 🚀

---

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Ollama (for local development) OR API key for cloud LLM (OpenAI/Anthropic/Gemini)

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd /path/to/MF-Chatbot
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv mf-env
   source mf-env/bin/activate  # On Windows: mf-env\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up LLM (choose one):**

   **Option A: Ollama (Recommended for Development - Free, No Rate Limits)**
   ```bash
   # Install Ollama
   brew install ollama  # macOS
   # Or download from: https://ollama.ai/download
   
   # Start Ollama
   ollama serve
   
   # Pull model (in new terminal)
   ollama pull llama3.1:8b
   
   # Set environment variables (optional, defaults to Ollama)
   export LLM_MODEL_TYPE=ollama
   export LLM_MODEL_NAME=llama3.1:8b
   ```

   **Option B: Gemini (Recommended for Production)**
   ```bash
   export LLM_MODEL_TYPE=gemini
   export LLM_MODEL_NAME=gemini-2.0-flash
   export GEMINI_API_KEY=your_key_here
   ```

   **Option C: OpenAI**
   ```bash
   export LLM_MODEL_TYPE=openai
   export LLM_MODEL_NAME=gpt-3.5-turbo
   export OPENAI_API_KEY=sk-...
   ```

   **Option D: Anthropic**
   ```bash
   export LLM_MODEL_TYPE=anthropic
   export LLM_MODEL_NAME=claude-3-5-sonnet-20241022
   export ANTHROPIC_API_KEY=sk-ant-...
   ```

   Or create a `.env` file:
   ```bash
   LLM_MODEL_TYPE=gemini
   LLM_MODEL_NAME=gemini-2.0-flash
   GEMINI_API_KEY=your_key_here
   ```

5. **Initialize the vector store:**
   ```bash
   python rag_system.py
   ```
   
   This will:
   - Load the cleaned knowledge base
   - Create document chunks
   - Generate embeddings
   - Build the ChromaDB vector store
   
   **Note:** This may take a few minutes on first run.

6. **Run the Streamlit app:**
   ```bash
   streamlit run app.py
   ```
   
   The app will open in your browser at `http://localhost:8501`

---

## Usage

### Starting the Application

```bash
# Make sure Ollama is running (if using Ollama)
ollama serve

# In another terminal, run the app
streamlit run app.py
```

### Example Queries

**Factual Queries:**
- "What is the expense ratio of HDFC Large Cap Fund?"
- "What is the exit load for HDFC Flexi Cap Fund?"
- "What is the ELSS lock-in period?"
- "How to download CAS statement?"
- "What is the benchmark for HDFC Large Cap Fund?"
- "What funds do you cover?"

**Greetings:**
- "Hello"
- "Hi"
- "Good morning"

**Out-of-Context (politely refused):**
- "What is the capital of India?"
- "Will you date me?"
- "565665" (random numbers)

**Advice-Seeking (politely refused):**
- "Should I buy HDFC Large Cap Fund?"
- "Is this fund good for me?"

**Ambiguous (clarification requested):**
- "minimum sip amount" → Bot asks: "Which fund?"
- "expense ratio" → Bot asks: "Which fund?"
- "NAV" → Bot asks: "Which fund?"

---

## Architecture

### Two-Stage RAG Flow

1. **Query Classification:** Determines query type using LLM intelligence
   - Greeting → Friendly welcome
   - Coverage → Lists 4 HDFC funds
   - Out-of-context → Polite refusal
   - Advice → Educational link
   - Factual → Proceed to RAG

2. **Clarification Check:** LLM determines if fund name is needed
   - If ambiguous → Ask "Which fund?"
   - If clear → Proceed

3. **Stage 1 - Query Refinement:** LLM refines query using chat history
   - Preserves exact fund names
   - Infers context from previous queries
   - Optimizes for retrieval

4. **Retrieval:** Vector store retrieves top-k relevant chunks
   - Prioritizes fund-specific documents
   - Filters by fund name if specified
   - Re-ranks for relevance

5. **Stage 2 - Answer Generation:** LLM generates answer from context
   - Uses only retrieved information
   - Formats with bullets/lists
   - Concise and human-friendly

6. **Citation:** Extracts and formats source
   - Cleans tracking parameters
   - Shows fund name + document type
   - Includes last updated date

7. **Response:** Formatted answer with citation

### Components

- **`app.py`:** Streamlit UI with Groww-inspired design
- **`faq_assistant.py`:** LLM-powered query classification and RAG
- **`rag_system.py`:** Vector store setup and retrieval
- **`citation_handler.py`:** Citation extraction and formatting
- **`config.py`:** Configuration management
- **`cleaned_knowledge_base.json`:** Structured knowledge base

---

## Testing

### 1. Quick Health Check ⭐ Recommended

```bash
python quick_health_check.py
```

Tests 10 essential functionalities:
- ✅ Greetings
- ✅ Coverage queries
- ✅ Factual queries
- ✅ Clarification requests
- ✅ Advice refusal
- ✅ Out-of-context refusal
- ✅ Meaningless query rejection
- ✅ Fund-specific retrieval

**Expected:** 10/10 tests passing

### 2. Full Test Suite

```bash
python test_queries.py
```

Runs 20+ test queries across all categories.

### 3. Manual Testing

Test directly in the Streamlit UI:
```bash
streamlit run app.py
```

**Key test cases:**
1. "what schemes do you have" → Lists 4 HDFC funds ✅
2. "expense ratio of HDFC Large Cap Fund" → "0.96%" ✅
3. "minimum sip amount" → "Which fund?" ✅
4. "HDFC Large Cap Fund" (after clarification) → Minimum SIP amount ✅
5. "how to download CAS statement" → Step-by-step instructions ✅
6. "will you date me" → Polite refusal ✅
7. "565665" → Polite refusal ✅

### Common Issues to Watch

- ❌ Wrong fund cited (asked Large Cap, got Flexi Cap)
- ❌ Extra information (asked expense ratio, got AUM too)
- ❌ Source on refusal (out-of-context shows HDFC document)
- ❌ Ugly URLs (tracking parameters like `?_gl=`)
- ❌ Poor formatting (no bullets, no line breaks)

---

## Deployment

### Option 1: Streamlit Cloud ⭐ Recommended (5 minutes)

1. **Push to GitHub:**
   ```bash
   git push origin main
   ```

2. **Go to:** https://streamlit.io/cloud

3. **Connect repository:** Your GitHub repo (e.g., `manavi1206/MF-Chatbot`)

4. **Set Main file path:** `app.py`

5. **Set Secrets** (in Streamlit Cloud dashboard):
   ```toml
   LLM_MODEL_TYPE = "gemini"
   LLM_MODEL_NAME = "gemini-2.0-flash"
   GEMINI_API_KEY = "your_gemini_api_key_here"
   ```

6. **Deploy!** The app will be live in ~2 minutes

**Get Gemini API Key:** https://makersuite.google.com/app/apikey

### Option 2: Docker + Cloud Provider

```bash
# Build Docker image
docker build -t mf-chatbot .

# Deploy to:
# - AWS ECS/Fargate
# - Google Cloud Run
# - Azure Container Instances
# - DigitalOcean App Platform
```

### Option 3: Self-Hosted Server

```bash
# On your server:
ollama serve &
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

---

## Troubleshooting

### Ollama Connection Failed
```bash
# Make sure Ollama is running
ollama serve

# Test connection
curl http://localhost:11434/api/tags

# Pull model if missing
ollama pull llama3.1:8b
```

### Vector Store Not Found
```bash
python rag_system.py
```

### API Key Error
```bash
# Set in environment or .env file
export GEMINI_API_KEY=your_key_here
```

### Import Errors
```bash
pip install -r requirements.txt
```

### ChromaDB Issues
```bash
rm -rf chroma_db/
python rag_system.py
```

### Streamlit Cloud Deployment Issues

**Issue:** App shows "Ollama connection failed"
**Fix:** Check that `LLM_MODEL_TYPE` is set to `gemini` (not `ollama`) in Streamlit Cloud secrets

**Issue:** "Vector store not found"
**Fix:** The vector store will be automatically created on first run. If it fails, check that `cleaned_knowledge_base.json` is in the repository.

**Issue:** "API quota exceeded"
**Fix:** Check your Gemini API quota at https://makersuite.google.com/app/apikey

---

## LLM Model Options

### Ollama Models (Local - Free)

| Model | Size | Speed | Quality | RAM Needed |
|-------|------|-------|---------|------------|
| `phi3:mini` | 3.8B | ⚡⚡⚡ Very Fast | ⭐⭐⭐ Good | 4GB |
| `llama3.1:8b` | 8B | ⚡⚡ Fast | ⭐⭐⭐⭐ Great | 8GB |
| `llama3.1:70b` | 70B | ⚡ Slower | ⭐⭐⭐⭐⭐ Excellent | 40GB |

**Recommendation:** Start with `llama3.1:8b`

### Cloud LLM Options (Production)

- **Google Gemini 2.0 Flash:** ~$0.000375 per 1K tokens, fast, competitive pricing ⭐ Recommended
- **OpenAI GPT-3.5-turbo:** ~$0.002 per 1K tokens, reliable, good rate limits
- **Anthropic Claude 3.5 Sonnet:** ~$0.009 per 1K tokens, excellent quality

---

## File Structure

```
MF-Chatbot/
├── app.py                          # Streamlit UI
├── faq_assistant.py               # LLM-powered query classification & RAG
├── rag_system.py                  # Vector store & retrieval
├── citation_handler.py            # Citation extraction
├── config.py                      # Configuration
├── cleaned_knowledge_base.json    # Knowledge base
├── sources.csv                    # Source metadata
├── test_queries.py               # Full test suite
├── quick_health_check.py         # Quick health check
├── requirements.txt              # Dependencies
├── chroma_db/                    # Vector store (created on first run)
└── README.md                     # This file
```

---

## Known Limits

1. **Scope:** Only covers HDFC Mutual Funds (4 schemes)
2. **Factual Only:** Cannot provide investment advice
3. **Source Coverage:** Limited to 25 verified sources
4. **Data Freshness:** Knowledge base updated manually (last: Nov 19, 2025)

---

## Why LLM-Based Intelligence?

### ❌ Old Approach: Hardcoded Patterns
```python
out_of_context_patterns = [
    r'\b(weather|temperature)\b',
    r'\b(cook|recipe)\b',
    r'\b(date|dating)\b',
    # ... endless patterns needed
]
```

**Problems:**
- ❌ Can't anticipate every query
- ❌ Constant maintenance required
- ❌ Breaks on typos/filler words
- ❌ Not scalable

### ✅ New Approach: LLM Intelligence
```python
def is_mutual_fund_related(query):
    """Use LLM to determine relevance"""
    return llm.check("Is this about mutual funds?", query)
```

**Benefits:**
- ✅ Handles ANY query phrasing
- ✅ Zero maintenance
- ✅ Typo-tolerant
- ✅ Future-proof
- ✅ Minimal cost (~$0.00003/query)

**Result:** A robust, scalable, zero-maintenance chatbot! 🚀

---

## Disclaimer

**Important:** This assistant provides factual information only. It does not provide investment advice. For investment decisions, consult a registered financial advisor.

All information is sourced from official HDFC AMC, SEBI, and AMFI documents. While we strive for accuracy, please verify critical information from official sources.

---

## License

This project is for educational and informational purposes only.

---

**Last Updated:** November 19, 2025

**Version:** 2.0 (LLM-Powered Intelligence)
