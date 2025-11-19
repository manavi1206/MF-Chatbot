# Streamlit Cloud Deployment Guide

## Quick Setup Checklist

### 1. Environment Variables (Secrets)

In Streamlit Cloud dashboard → Settings → Secrets, add:

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
LLM_MODEL_TYPE = "gemini"
LLM_MODEL_NAME = "gemini-2.0-flash"
ENVIRONMENT = "production"
```

**Get Gemini API Key:** https://makersuite.google.com/app/apikey

### 2. Common Errors & Fixes

#### Error: "API key not found" or "GEMINI_API_KEY"
**Fix:** 
- Go to Streamlit Cloud → Settings → Secrets
- Add `GEMINI_API_KEY=your_key`
- Redeploy

#### Error: "Vector store not initialized"
**Fix:**
- This should auto-create on first use
- Make sure `cleaned_knowledge_base.json` is in the repository
- Check logs for specific error

#### Error: "Module not found" or Import errors
**Fix:**
- Check `requirements.txt` includes all dependencies
- Streamlit Cloud installs from requirements.txt automatically

#### Error: "Knowledge base file not found"
**Fix:**
- Ensure `cleaned_knowledge_base.json` is committed to GitHub
- Check file exists in repository root

### 3. Verify Deployment

1. Check app loads without errors
2. Try a test query: "What is the expense ratio of HDFC Large Cap Fund?"
3. Check Streamlit Cloud logs for any warnings

### 4. Files Required in Repository

- ✅ `app.py` - Main Streamlit app
- ✅ `faq_assistant.py` - Assistant logic
- ✅ `rag_system.py` - RAG system
- ✅ `citation_handler.py` - Citation handling
- ✅ `config.py` - Configuration
- ✅ `cleaned_knowledge_base.json` - Knowledge base
- ✅ `requirements.txt` - Dependencies
- ✅ `sources.csv` - Source metadata

### 5. First Run

On first deployment:
- Vector store will be created automatically
- This may take 2-3 minutes
- Subsequent runs will be faster

---

**Need Help?** Check Streamlit Cloud logs in the dashboard for detailed error messages.

