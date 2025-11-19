#!/usr/bin/env python3
"""
Streamlit UI for Facts-Only MF Assistant
"""

import streamlit as st
import os
from dotenv import load_dotenv
from faq_assistant import FAQAssistant
from rag_system import RAGSystem

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Facts-Only MF Assistant",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'assistant' not in st.session_state:
    try:
        # Auto-detect environment: production uses cloud LLM, dev uses Ollama
        try:
            from config import Config
            llm_config = Config.get_llm_config()
            model_type = llm_config['model_type']
            model_name = llm_config['model_name']
            api_key = llm_config.get('api_key')
            
            # In production, prefer cloud LLMs; in dev, use Ollama
            if Config.is_production() and model_type == 'ollama':
                st.warning("⚠️ Production environment detected. Consider using a cloud LLM (OpenAI/Anthropic) for better reliability.")
        except ImportError:
            # Fallback to environment variables
            # Default to Gemini for production (Streamlit Cloud)
            model_type = os.getenv('LLM_MODEL_TYPE', 'gemini')
            if model_type == 'gemini':
                model_name = os.getenv('LLM_MODEL_NAME', 'gemini-2.0-flash')
                api_key = os.getenv('GEMINI_API_KEY')
            elif model_type == 'openai':
                model_name = os.getenv('LLM_MODEL_NAME', 'gpt-3.5-turbo')
                api_key = os.getenv('OPENAI_API_KEY')
            elif model_type == 'anthropic':
                model_name = os.getenv('LLM_MODEL_NAME', 'claude-3-5-sonnet-20241022')
                api_key = os.getenv('ANTHROPIC_API_KEY')
            else:  # ollama or other
                model_name = os.getenv('LLM_MODEL_NAME', 'llama3.1:8b')
                api_key = None
        
        st.session_state.assistant = FAQAssistant(
            model_type=model_type,
            model_name=model_name,
            api_key=api_key
        )
        st.session_state.rag_initialized = True
    except Exception as e:
        st.session_state.assistant = None
        st.session_state.rag_initialized = False
        st.session_state.error = str(e)

# Header
st.title("📊 Facts-Only MF Assistant")
st.caption("No Investment Advice • Verified Sources Only")

# Disclaimer banner
st.info("⚠️ **Facts-only. No investment advice.** This assistant provides factual information about HDFC Mutual Funds from official sources (AMC, SEBI, AMFI).")

# Check if assistant is initialized
if not st.session_state.rag_initialized:
    error_msg = st.session_state.get('error', 'Unknown error')
    st.error(f"❌ Error initializing assistant: {error_msg}")
    
    # Check for common issues
    if 'GEMINI_API_KEY' in str(error_msg) or 'API key' in str(error_msg):
        st.info("""
        **Missing API Key:**
        1. In Streamlit Cloud, go to Settings → Secrets
        2. Add your Gemini API key:
           - `GEMINI_API_KEY=your_key_here`
        3. Also set:
           - `LLM_MODEL_TYPE=gemini`
           - `LLM_MODEL_NAME=gemini-2.0-flash`
        4. Redeploy the app
        """)
    elif 'vector store' in str(error_msg).lower() or 'chroma' in str(error_msg).lower():
        st.info("""
        **Vector Store Issue:**
        The vector store will be created automatically on first use.
        If this error persists, the knowledge base file may be missing.
        """)
    else:
        st.info("""
        **Setup Instructions:**
        1. Set your Gemini API key in Streamlit Cloud Secrets
        2. Make sure `cleaned_knowledge_base.json` exists in the repository
        3. The vector store will be created automatically
        """)
    st.stop()

# Welcome section (only show if no chat history)
if not st.session_state.chat_history:
    st.markdown("""
    ### Welcome! 👋
    
    I can help you with factual questions about **HDFC Mutual Funds**, including:
    - Expense ratios and fees
    - Exit loads and lock-in periods  
    - Riskometers and benchmarks
    - How to download statements (CAS, tax reports)
    - Fund details and investment objectives
    
    **Try asking:**
    """)
    
    # Example questions
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💡 What is the expense ratio of HDFC Large Cap Fund?", use_container_width=True):
            st.session_state.example_query = "What is the expense ratio of HDFC Large Cap Fund?"
            st.rerun()
    with col2:
        if st.button("🔒 What is the ELSS lock-in period?", use_container_width=True):
            st.session_state.example_query = "What is the ELSS lock-in period?"
            st.rerun()
    with col3:
        if st.button("📄 How to download CAS statement?", use_container_width=True):
            st.session_state.example_query = "How to download CAS statement?"
            st.rerun()

# Chat interface
st.markdown("---")

# Display chat history
for i, exchange in enumerate(st.session_state.chat_history):
    with st.chat_message("user"):
        st.write(exchange['user'])
    
    with st.chat_message("assistant"):
        st.markdown(exchange['assistant'])
        if exchange.get('citation'):
            st.caption(f"🔗 Source: {exchange['citation']}")

# Handle example query
if 'example_query' in st.session_state:
    query = st.session_state.example_query
    del st.session_state.example_query
else:
    query = None

# Chat input
user_input = st.chat_input("Ask a question about HDFC Mutual Funds...")

if user_input:
    query = user_input

if query:
    # Add user message to chat
    st.session_state.chat_history.append({'user': query, 'assistant': '', 'citation': None})
    
    # Show user message
    with st.chat_message("user"):
        st.write(query)
    
    # Process query
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer, citation_url = st.session_state.assistant.process_query(
                    query,
                    st.session_state.chat_history[:-1]  # Exclude current query
                )
                
                st.markdown(answer)
                
                # Update chat history with response
                st.session_state.chat_history[-1]['assistant'] = answer
                if citation_url:
                    st.session_state.chat_history[-1]['citation'] = citation_url
                    st.caption(f"🔗 Source: {citation_url}")
                
            except Exception as e:
                error_msg = f"I encountered an error: {str(e)}. Please try again."
                st.error(error_msg)
                st.session_state.chat_history[-1]['assistant'] = error_msg
    
    st.rerun()

# Footer
st.markdown("---")
rag_system = RAGSystem()
last_updated = rag_system.get_last_updated_date()
st.caption(f"📅 Last updated from sources: {last_updated}")

# Sidebar with info
with st.sidebar:
    st.header("ℹ️ About")
    st.markdown("""
    **Facts-Only MF Assistant**
    
    This assistant answers factual questions about HDFC Mutual Funds using verified sources from:
    - HDFC AMC (Asset Management Company)
    - SEBI (Securities and Exchange Board of India)
    - AMFI (Association of Mutual Funds in India)
    
    **Coverage:**
    - 4 HDFC Mutual Fund schemes
    - 25 verified sources
    - Regulatory guidelines
    - Help documentation
    """)
    
    st.header("📋 Supported Queries")
    st.markdown("""
    ✅ Factual questions about:
    - Expense ratios
    - Exit loads
    - Lock-in periods
    - Riskometers
    - Benchmarks
    - Statement downloads
    - Fund details
    
    ❌ Cannot answer:
    - Investment advice
    - Performance comparisons
    - General knowledge questions
    """)
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

