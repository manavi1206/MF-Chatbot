# Facts-Only MF Assistant

A RAG-based chatbot that answers factual questions about HDFC Mutual Funds using verified sources from AMC, SEBI, and AMFI websites. Provides concise, citation-backed responses while strictly avoiding any investment advice.

## Overview

This assistant uses Retrieval-Augmented Generation (RAG) with a two-stage LLM approach to answer factual questions about mutual funds. It handles:
- ✅ Factual queries (expense ratio, exit load, lock-in, etc.)
- ✅ Greetings (friendly welcome with nudge to MF topics)
- ✅ Out-of-context queries (polite refusal with nudge to MF topics)
- ✅ Advice-seeking queries (polite refusal with educational link)

## Scope

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

## Features

- **Facts-Only:** Answers factual questions with citations
- **Source Attribution:** Every answer includes a citation link
- **Two-Stage RAG:** Query refinement + answer generation
- **Query Classification:** Handles greetings, out-of-context, advice, and factual queries
- **Chat History:** Maintains conversation context
- **No Investment Advice:** Strictly refuses advice-seeking queries
- **Multiple LLM Support:** Ollama (local), OpenAI, Anthropic, Gemini

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Ollama (for local development) OR API key for cloud LLM (OpenAI/Anthropic/Gemini)

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd /Users/manavisingh/MF-Chatbot
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
   # Install Ollama binary
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

   **Option B: OpenAI (For Production)**
   ```bash
   export LLM_MODEL_TYPE=openai
   export LLM_MODEL_NAME=gpt-3.5-turbo
   export OPENAI_API_KEY=sk-...
   ```

   **Option C: Anthropic (For Production)**
   ```bash
   export LLM_MODEL_TYPE=anthropic
   export LLM_MODEL_NAME=claude-3-5-sonnet-20241022
   export ANTHROPIC_API_KEY=sk-ant-...
   ```

   **Option D: Gemini**
   ```bash
   export LLM_MODEL_TYPE=gemini
   export LLM_MODEL_NAME=gemini-2.0-flash
   export GEMINI_API_KEY=your_key_here
   ```

   Or create a `.env` file:
   ```bash
   LLM_MODEL_TYPE=ollama
   LLM_MODEL_NAME=llama3.1:8b
   # Add API keys if using cloud LLM
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

**Greetings:**
- "Hello"
- "Hi"
- "Good morning"

**Out-of-Context (will be politely refused):**
- "What is the capital of India?"
- "What is your favorite sport?"

**Advice-Seeking (will be politely refused):**
- "Should I buy HDFC Large Cap Fund?"
- "Is this fund good for me?"

## LLM Model Options

### Ollama Models (Local - Free)

| Model | Size | Speed | Quality | RAM Needed |
|-------|------|-------|---------|------------|
| `phi3:mini` | 3.8B | ⚡⚡⚡ Very Fast | ⭐⭐⭐ Good | 4GB |
| `llama3.1:8b` | 8B | ⚡⚡ Fast | ⭐⭐⭐⭐ Great | 8GB |
| `llama3.1:70b` | 70B | ⚡ Slower | ⭐⭐⭐⭐⭐ Excellent | 40GB |

**Recommendation:** Start with `llama3.1:8b`

### Cloud LLM Options (Production)

- **OpenAI GPT-3.5-turbo:** ~$0.002 per 1K tokens, reliable, good rate limits
- **Anthropic Claude 3.5 Sonnet:** ~$0.009 per 1K tokens, excellent quality
- **Google Gemini 2.0 Flash:** ~$0.000375 per 1K tokens, competitive pricing

## Architecture

### Two-Stage RAG Flow

1. **Query Classification:** Determines query type (greeting/out-of-context/advice/factual)
2. **Stage 1 - Query Refinement:** LLM refines the query using chat history
3. **Retrieval:** Vector store retrieves top-k relevant chunks
4. **Stage 2 - Answer Generation:** LLM generates answer from retrieved context
5. **Citation:** Extracts and formats source citation
6. **Response:** Formats answer with citation and "Last updated" date

### Components

- **`app.py`:** Streamlit UI
- **`rag_system.py`:** Vector store setup and retrieval
- **`faq_assistant.py`:** Query classification and two-stage LLM integration
- **`citation_handler.py`:** Citation extraction and formatting
- **`config.py`:** Configuration management
- **`cleaned_knowledge_base.json`:** Structured knowledge base with source attribution

## Testing

We provide multiple ways to test the chatbot comprehensively:

### 1. Quick Health Check (10 Essential Tests) ⭐ Recommended
Run this first to verify core functionality:
```bash
python quick_health_check.py
```

This tests:
- ✅ Greetings
- ✅ Coverage queries
- ✅ Factual queries (expense ratio, ELSS lock-in, etc.)
- ✅ Ambiguous queries (clarification)
- ✅ Advice refusal
- ✅ Out-of-context refusal
- ✅ Meaningless query rejection
- ✅ Fund-specific retrieval accuracy

**Expected output:** 10/10 tests passing

### 2. Comprehensive Test Cases (Manual Testing)
For thorough edge case testing, use the checklist:
```bash
# View the comprehensive test cases
cat comprehensive_test_cases.md
```

This includes:
- 16 categories of test cases
- 100+ individual test scenarios
- Expected outcomes for each query
- Common issues to watch for
- Visual/UI validation checklist

**Best for:** Production readiness verification

### 3. Full Automated Test Suite (20+ queries)
```bash
python test_queries.py
```

### 4. Streamlit App Testing (Manual)
Test directly in the UI:
```bash
streamlit run app.py
```

Then use the test cases from `comprehensive_test_cases.md` to verify:
- Formatting (bullets, line breaks)
- UI appearance (borders, shadows, spacing)
- Source citations (clean URLs, no background)
- Chat flow and context awareness

### Testing Strategy

**Before Deployment:**
1. Run `python quick_health_check.py` → Should pass 10/10
2. Test 5-10 queries manually in Streamlit UI
3. Verify visual appearance matches design

**After Deployment:**
1. Test coverage query: "what can i ask you"
2. Test factual query: "What is the expense ratio of HDFC Large Cap Fund?"
3. Test refusal: "Should I invest in HDFC Large Cap?"
4. Test rejection: "565665" (random numbers)
5. Test ambiguous: "minimum sip amount" (no fund)

**Common Issues to Watch:**
- ❌ Wrong fund cited (asked Large Cap, got Flexi Cap)
- ❌ Extra information (asked expense ratio, got AUM too)
- ❌ Source on refusal (out-of-context shows HDFC document)
- ❌ Wrong amount (minimum SIP shows "additional purchase")
- ❌ Ugly URLs (tracking parameters like `?_gl=`)

See `comprehensive_test_cases.md` for detailed issue reporting guidelines.

## Deployment

### Option 1: Streamlit Cloud (Easiest - 5 minutes) ⭐ Recommended

1. **Push to GitHub** (already done if you're reading this)
2. **Go to** https://streamlit.io/cloud
3. **Connect repository:** `manavi1206/MF-Chatbot`
4. **Set environment variables** in Streamlit Cloud dashboard:
   - `LLM_MODEL_TYPE=gemini`
   - `LLM_MODEL_NAME=gemini-2.0-flash`
   - `GEMINI_API_KEY=your_gemini_api_key_here`
   - `ENVIRONMENT=production` (optional)
5. **Deploy!** The app will be live in ~2 minutes

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
Make sure your API key is set in environment variables or `.env` file:
```bash
export LLM_MODEL_TYPE=openai
export OPENAI_API_KEY=sk-...
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

### Out of Memory (Ollama)
- Use smaller model: `ollama pull phi3:mini`
- Close other apps
- Reduce model size in config

## Data Updates

The knowledge base can be updated manually:

```bash
python update_knowledge_base.py
```

This will:
1. Fetch latest data from all sources
2. Clean and structure the data
3. Update the knowledge base
4. Rebuild the vector store

## File Structure

```
MF-Chatbot/
├── app.py                    # Streamlit UI
├── rag_system.py            # RAG implementation
├── faq_assistant.py         # Query classification & LLM integration
├── citation_handler.py      # Citation extraction
├── config.py                # Configuration management
├── cleaned_knowledge_base.json  # Knowledge base
├── sources.csv              # Source metadata
├── test_queries.py          # Full test suite
├── quick_test.py            # Quick test (5 queries)
├── requirements.txt        # Dependencies
└── chroma_db/              # Vector store (created on first run)
```

## Known Limits

1. **Scope:** Only covers HDFC Mutual Funds (4 schemes). Does not cover other AMCs.
2. **Factual Only:** Cannot provide investment advice, recommendations, or performance comparisons.
3. **Source Coverage:** Limited to 25 verified sources. May not answer questions about very recent changes not yet in the knowledge base.
4. **Data Freshness:** Knowledge base is updated manually. For latest information, check official sources.

## Disclaimer

**Important:** This assistant provides factual information only. It does not provide investment advice. For investment decisions, consult a registered financial advisor.

## License

This project is for educational and informational purposes only.

---

**Last Updated:** November 19, 2025
