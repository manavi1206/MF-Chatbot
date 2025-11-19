# Project Structure

## 📁 Directory Organization

```
MF-Chatbot/
│
├── 🎯 CORE APPLICATION (Root)
│   ├── app.py                      # Streamlit UI
│   ├── faq_assistant.py           # LLM-powered query classification & RAG
│   ├── rag_system.py              # Vector store & retrieval
│   ├── citation_handler.py        # Citation extraction & formatting
│   ├── config.py                  # Configuration management
│   │
│   ├── cleaned_knowledge_base.json # Active knowledge base (25 sources)
│   ├── sources.csv                 # Source metadata
│   ├── requirements.txt            # Python dependencies
│   └── README.md                   # Main documentation
│
├── 📜 scripts/                    # Data Processing & Setup
│   ├── fetch_fund_data.py         # Fetch fund documents from web
│   ├── fetch_regulatory_sources.py # Fetch regulatory docs (SEBI, AMFI)
│   ├── clean_and_structure_data.py # Clean and structure raw data
│   ├── consolidate_scheme_data.py  # Consolidate scheme information
│   ├── llm_consolidate_schemes.py  # LLM-based data consolidation
│   ├── update_knowledge_base.py    # Update KB (for scheduled runs)
│   └── setup_cron.sh               # Cron job setup script
│
├── 🧪 tests/                      # Test Suites
│   ├── quick_health_check.py      # Quick 10-test health check ⭐
│   ├── test_queries.py            # Full test suite (20+ queries)
│   ├── test_patterns.py           # Pattern matching tests
│   ├── test_out_of_context.py     # Out-of-context detection tests
│   └── quick_test.py              # Quick 5-query test
│
├── 📊 data/                       # Raw & Intermediate Data
│   ├── fund_data_*.txt            # Raw fund documents (4 funds)
│   ├── comprehensive_fund_dataset.csv/json # Processed datasets
│   ├── consolidated_scheme_data.json # Consolidated scheme data
│   ├── regulatory_knowledge_base.json # Regulatory sources
│   ├── unified_knowledge_base.json # Unified knowledge base
│   ├── knowledge_base_index.json   # Knowledge base index
│   └── sample_qa.json              # Sample Q&A pairs
│
├── 📝 logs/                       # Application Logs
│   └── update_*.log               # Update script logs
│
├── 🗄️ chroma_db/                 # Vector Store (Auto-created)
│   └── (ChromaDB files)           # Vector embeddings & index
│
└── 🐍 mf-env/                     # Virtual Environment (Local only)
    └── (Python packages)           # Isolated dependencies

```

## 🎯 Key Files

### Essential (Keep in Root)
- `app.py` - Streamlit application entry point
- `faq_assistant.py` - Main chatbot logic
- `rag_system.py` - RAG implementation
- `cleaned_knowledge_base.json` - Active knowledge base
- `sources.csv` - Source metadata

### Scripts (scripts/)
Run data processing and setup tasks:
```bash
# Fetch latest data
python scripts/fetch_fund_data.py

# Update knowledge base
python scripts/update_knowledge_base.py

# Setup automated updates
bash scripts/setup_cron.sh
```

### Tests (tests/)
Run quality checks:
```bash
# Quick health check (recommended)
python tests/quick_health_check.py

# Full test suite
python tests/test_queries.py
```

### Data (data/)
Intermediate and raw data files. Not used directly by the app.

## 🚀 Running the Application

```bash
# From project root
streamlit run app.py
```

## 🧪 Running Tests

```bash
# Quick health check (10 tests)
python tests/quick_health_check.py

# Full test suite (20+ tests)
python tests/test_queries.py

# Pattern tests
python tests/test_patterns.py
```

## 📦 What Goes Where?

### Add New Test
→ Place in `tests/` directory
→ Add `sys.path.insert()` to import from root

### Add New Data Processing Script
→ Place in `scripts/` directory
→ Update `scripts/update_knowledge_base.py` if needed

### Add New Raw Data
→ Place in `data/` directory
→ Update processing scripts to use new data

### Modify Core Logic
→ Edit files in root directory
→ No path changes needed

## 🔄 Git Status

All moves were done with `git mv` equivalent, so:
- ✅ File history preserved
- ✅ Git recognizes as renames (not delete + add)
- ✅ Clean git log

## 📝 Notes

1. **Vector Store** (`chroma_db/`) is auto-created on first run
2. **Virtual Environment** (`mf-env/`) should be in `.gitignore`
3. **Logs** are created automatically in `logs/` directory
4. **Active Knowledge Base** stays in root for easy access
5. **Test imports** updated with `sys.path.insert()` for parent access

---

**Last Updated:** November 19, 2025
