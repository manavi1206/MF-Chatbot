#!/usr/bin/env python3
"""
FAQ Assistant with Query Classification and Two-Stage LLM
Handles greetings, out-of-context queries, advice-seeking, and factual queries
"""

import os
import re
from typing import List, Dict, Any, Optional, Tuple
from rag_system import RAGSystem
from citation_handler import CitationHandler

class FAQAssistant:
    def __init__(self, model_type: str = None, model_name: str = None, api_key: Optional[str] = None):
        """
        Initialize FAQ Assistant with support for multiple LLM backends
        
        Args:
            model_type: "ollama", "gemini", "openai", "anthropic" (default: from LLM_MODEL_TYPE env var or "gemini")
            model_name: Model name (e.g., "llama3.1:8b" for Ollama, "gemini-2.0-flash" for Gemini)
            api_key: API key (only needed for cloud models)
        """
        # Default to Gemini for production
        self.model_type = (model_type or os.getenv('LLM_MODEL_TYPE', 'gemini')).lower()
        
        # Set default model name based on type
        if not model_name:
            if self.model_type == 'gemini':
                model_name = os.getenv('LLM_MODEL_NAME', 'gemini-2.0-flash')
            elif self.model_type == 'openai':
                model_name = os.getenv('LLM_MODEL_NAME', 'gpt-3.5-turbo')
            elif self.model_type == 'anthropic':
                model_name = os.getenv('LLM_MODEL_NAME', 'claude-3-5-sonnet-20241022')
            else:  # ollama
                model_name = os.getenv('LLM_MODEL_NAME', 'llama3.1:8b')
        
        self.model_name = model_name
        self.api_key = api_key
        self.model = None
        self._initialize_model()
        
        self.rag_system = RAGSystem()
        self.citation_handler = CitationHandler()
        
        # Vector store will be initialized on first use
        # Don't create it here to avoid blocking initialization
    
    def _initialize_model(self):
        """Initialize the appropriate LLM model"""
        if self.model_type == "ollama":
            try:
                import ollama
                self.model = ollama
                self.model_client = ollama
                print(f"✓ Using Ollama with model: {self.model_name}")
                # Test connection
                try:
                    ollama.list()
                    print("  ✓ Ollama connection successful")
                except Exception as e:
                    print(f"⚠️  Ollama connection failed: {e}")
                    print("   Please start Ollama with: ollama serve")
                    print(f"   Then pull the model: ollama pull {self.model_name}")
            except ImportError:
                print("⚠️  Ollama not installed. Install with: pip install ollama")
                raise ValueError("Ollama not available. Install with: pip install ollama")
        
        elif self.model_type == "gemini":
            try:
                import google.generativeai as genai
                from google.generativeai.types import HarmCategory, HarmBlockThreshold
                self.api_key = self.api_key or os.getenv('GEMINI_API_KEY')
                if not self.api_key:
                    raise ValueError("Gemini API key not found. Set GEMINI_API_KEY environment variable.")
                
                genai.configure(api_key=self.api_key)
                try:
                    self.model = genai.GenerativeModel(self.model_name or 'gemini-2.0-flash')
                except:
                    self.model = genai.GenerativeModel('gemini-pro-latest')
                self.HarmCategory = HarmCategory
                self.HarmBlockThreshold = HarmBlockThreshold
                print(f"✓ Using Gemini with model: {self.model_name or 'gemini-2.0-flash'}")
            except ImportError:
                raise ValueError("Google Generative AI not installed. Install with: pip install google-generativeai")
        
        elif self.model_type == "openai":
            try:
                import openai
                self.api_key = self.api_key or os.getenv('OPENAI_API_KEY')
                if not self.api_key:
                    raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
                openai.api_key = self.api_key
                self.model = openai
                self.model_name = self.model_name or 'gpt-3.5-turbo'
                print(f"✓ Using OpenAI with model: {self.model_name}")
            except ImportError:
                raise ValueError("OpenAI not installed. Install with: pip install openai")
        
        elif self.model_type == "anthropic":
            try:
                import anthropic
                self.api_key = self.api_key or os.getenv('ANTHROPIC_API_KEY')
                if not self.api_key:
                    raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable.")
                self.model = anthropic.Anthropic(api_key=self.api_key)
                self.model_name = self.model_name or 'claude-3-5-sonnet-20241022'
                print(f"✓ Using Anthropic Claude with model: {self.model_name}")
            except ImportError:
                raise ValueError("Anthropic not installed. Install with: pip install anthropic")
        
        else:
            raise ValueError(f"Unknown model_type: {self.model_type}. Use: ollama, gemini, openai, or anthropic")
    
    def _call_llm(self, prompt: str, max_tokens: int = 200, temperature: float = 0.3, system_prompt: str = None) -> str:
        """Call the appropriate LLM API"""
        if self.model_type == "ollama":
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Ollama generate returns a generator, collect all chunks
            response_text = ""
            try:
                response = self.model.generate(
                    model=self.model_name,
                    prompt=full_prompt,
                    options={
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                )
                # Collect all response chunks
                for chunk in response:
                    if 'response' in chunk:
                        response_text += chunk['response']
                    elif isinstance(chunk, str):
                        response_text += chunk
                return response_text.strip()
            except Exception as e:
                # Fallback: try direct API call
                try:
                    response = self.model_client.chat(
                        model=self.model_name,
                        messages=[
                            {"role": "system", "content": system_prompt} if system_prompt else None,
                            {"role": "user", "content": prompt}
                        ],
                        options={
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    )
                    if response and 'message' in response:
                        return response['message']['content'].strip()
                    return response_text.strip() if response_text else str(response)
                except:
                    raise e
        
        elif self.model_type == "gemini":
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            if response.candidates and response.candidates[0].finish_reason == 1:
                return response.text.strip()
            else:
                raise ValueError("Gemini response blocked")
        
        elif self.model_type == "openai":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.model.ChatCompletion.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        
        elif self.model_type == "anthropic":
            messages = [{"role": "user", "content": prompt}]
            if system_prompt:
                response = self.model.messages.create(
                    model=self.model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=messages
                )
            else:
                response = self.model.messages.create(
                    model=self.model_name,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=messages
                )
            return response.content[0].text.strip()
    
    def is_greeting(self, query: str) -> bool:
        """Detect greetings using keywords and patterns"""
        query_lower = query.lower().strip()
        greeting_patterns = [
            r'^(hi|hello|hey|greetings|good morning|good afternoon|good evening|good night)',
            r'^(hi|hello|hey)\s+there',
            r'^(hi|hello|hey)\s*[!.]*$',
            r'^howdy',
            r'^what\'?s up',
            r'^sup'
        ]
        
        for pattern in greeting_patterns:
            if re.match(pattern, query_lower):
                return True
        
        return False
    
    def is_advice_query(self, query: str) -> bool:
        """Detect advice-seeking queries"""
        query_lower = query.lower()
        advice_keywords = [
            'should i', 'should i buy', 'should i invest', 'should i sell',
            'is it good', 'is it bad', 'is it worth', 'is it safe',
            'recommend', 'recommendation', 'suggest', 'suggestion',
            'better', 'best', 'worst', 'good for me', 'suitable for me',
            'compare returns', 'which is better', 'which fund',
            'should i choose', 'advice', 'opinion', 'think'
        ]
        
        for keyword in advice_keywords:
            if keyword in query_lower:
                return True
        
        return False
    
    def is_coverage_query(self, query: str) -> bool:
        """Detect queries asking about what funds/schemes we cover"""
        query_lower = query.lower()
        coverage_patterns = [
            r'what (funds|schemes|mutual funds).*(do you|can you).*(have|cover|support|offer)',
            r'which (funds|schemes|mutual funds).*(do you|can you).*(have|cover|support|offer)',
            r'(what|which) (funds|schemes).*(available|covered)',
            r'list.*(funds|schemes)',
            r'show.*(funds|schemes)',
            r'tell me.*(funds|schemes).*(you|we) (have|cover)',
            r'(funds|schemes).*(you|we) (have|cover|support)',
            r'coverage',
            r'what.*schemes.*do.*have',
            r'which.*schemes.*available',
            r'what (all )?can i ask (you|about)',
            r'what (all )?(questions|topics|things) can i ask',
            r'what can you (help|answer|tell)',
            r'what (do|can) you (know|answer|help)',
            r'what are your capabilities',
            r'what (topics|questions) (do you|can you) (answer|handle|cover)',
            r'tell me what you can do',
            r'what information (do you|can you) provide'
        ]
        
        for pattern in coverage_patterns:
            if re.search(pattern, query_lower):
                return True
        return False
    
    def is_out_of_context(self, query: str) -> bool:
        """Detect out-of-context queries (non-MF related)"""
        query_lower = query.lower().strip()
        
        # Check for meaningless queries first
        # 1. Only numbers (like "565665")
        if query_lower.isdigit():
            return True
        
        # 2. Very short queries (1-2 characters) that aren't greetings
        if len(query_lower) <= 2 and not self.is_greeting(query_lower):
            return True
        
        # 3. Only special characters or very short gibberish
        if len(query_lower) <= 3 and not any(c.isalpha() for c in query_lower):
            return True
        
        # 4. Queries with mostly numbers and few/no words
        words = re.findall(r'[a-zA-Z]+', query_lower)
        if len(words) == 0 or (len(query_lower) > 5 and len(''.join(words)) < len(query_lower) * 0.3):
            return True
        
        # MF-related keywords that indicate the query is relevant
        mf_keywords = [
            'mutual fund', 'mf', 'fund', 'scheme', 'nav', 'aum',
            'expense ratio', 'exit load', 'sip', 'elss', 'lock-in',
            'riskometer', 'benchmark', 'portfolio', 'factsheet',
            'hdfc', 'amc', 'sebi', 'amfi', 'cas', 'statement',
            'tax', 'capital gains', 'dividend', 'redemption',
            'allotment', 'units', 'investment', 'equity', 'debt'
        ]
        
        # Check if query contains MF-related terms
        has_mf_terms = any(keyword in query_lower for keyword in mf_keywords)
        
        # Out-of-context indicators - expanded list
        out_of_context_patterns = [
            r'\bpm\b', r'prime minister', r'president', r'minister',
            r'capital of', r'capital city',
            r'favorite sport', r'favourite sport',
            r'tell me a joke', r'joke',
            r'weather', r'temperature',
            r'what is your name', r'who are you',
            r'what time is it', r'what day is it',
            r'how are you', r'how do you do',
            r'who is (the )?(pm|president|ceo|founder|director)',
            r'what is (the )?(population|area|size)',
            r'when (is|was|will)',
            r'where (is|was|are)',
            r'(cricket|football|sports|movie|film|music)',
            r'(recipe|food|cooking|restaurant)',
            r'(technology|computer|phone|laptop)(?! fund)',
            r'(game|gaming|video)',
            r'(travel|tourism|hotel|flight)'
        ]
        
        # If it has out-of-context patterns and no MF terms, it's out of context
        has_out_of_context = any(re.search(pattern, query_lower) for pattern in out_of_context_patterns)
        
        if has_out_of_context and not has_mf_terms:
            return True
        
        # If it's a greeting, it's not out-of-context (handled separately)
        if self.is_greeting(query):
            return False
        
        # If it's advice-seeking, it's not out-of-context (handled separately)
        if self.is_advice_query(query):
            return False
        
        # If no MF terms, it's likely out of context
        if not has_mf_terms:
            # Check if it's a general knowledge question
            general_patterns = [r'^who (is|was)', r'^what (is|was)', r'^when (is|was)', r'^where (is|was)', r'^why (is|was)', r'^how (is|was)']
            is_general_question = any(re.search(pattern, query_lower) for pattern in general_patterns)
            if is_general_question:
                return True
        
        return False  # Default to factual if unsure
    
    def classify_query_type(self, query: str) -> str:
        """Classify query type: greeting, coverage, out_of_context, advice, or factual"""
        if self.is_greeting(query):
            return 'greeting'
        elif self.is_coverage_query(query):
            return 'coverage'
        elif self.is_advice_query(query):
            return 'advice'
        elif self.is_out_of_context(query):
            return 'out_of_context'
        else:
            return 'factual'
    
    def handle_greeting(self) -> str:
        """Generate greeting response"""
        return """Hello! 👋 I'm a facts-only mutual fund assistant.

I can help you with factual questions about **HDFC Mutual Funds**, such as:
• Expense ratios and fees
• Exit loads and lock-in periods
• Riskometers and benchmarks
• How to download statements (CAS, tax reports)
• Fund details and investment objectives

What would you like to know about HDFC Mutual Funds?"""
    
    def handle_coverage_query(self) -> str:
        """Generate response about what funds we cover"""
        return """I can help you with **factual questions** about **4 HDFC Mutual Fund schemes**:

**Funds I Cover:**

**1. HDFC Large Cap Fund**
   • Category: Large Cap Equity
   • Investment Objective: Long-term capital growth from large-cap stocks

**2. HDFC Flexi Cap Fund**
   • Category: Flexi Cap Equity
   • Investment Objective: Capital appreciation across market caps

**3. HDFC TaxSaver (ELSS)**
   • Category: Equity Linked Savings Scheme
   • Investment Objective: Tax-saving with 3-year lock-in and equity growth

**4. HDFC Hybrid Equity Fund**
   • Category: Aggressive Hybrid
   • Investment Objective: Balanced exposure to equity and debt

**Questions You Can Ask:**
• What is the expense ratio of [fund name]?
• What is the minimum SIP amount for [fund name]?
• What is the exit load of [fund name]?
• What is the ELSS lock-in period?
• What is the benchmark of [fund name]?
• Who is the fund manager of [fund name]?
• How to download CAS statement?
• How to invest in mutual funds?

Try asking about any of these topics for the funds listed above!"""
    
    def handle_out_of_context(self) -> str:
        """Generate out-of-context refusal response"""
        return """I'm designed to answer factual questions about **mutual funds only**.

I can help you with information about **HDFC Mutual Funds**, including:
• Expense ratios and fees
• Exit loads and lock-in periods
• Riskometers and benchmarks
• How to download statements (CAS, tax reports)
• Fund details and investment objectives

Please ask me a question about mutual funds."""
    
    def handle_advice_query(self) -> str:
        """Generate advice-seeking refusal response"""
        amfi_link = "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=IntroductionMutualFunds"
        return f"""I provide **factual information only** and cannot give investment advice.

For guidance on investment decisions, please consult a **registered financial advisor**.

You can learn more about mutual funds at the [AMFI Knowledge Center]({amfi_link})."""
    
    def refine_query(self, query: str, chat_history: List[Dict[str, str]]) -> str:
        """Stage 1: Refine query using LLM with chat history"""
        # Build context from chat history
        history_context = ""
        if chat_history:
            recent_history = chat_history[-3:]  # Last 3 exchanges
            history_context = "\n\nPrevious conversation:\n"
            for exchange in recent_history:
                history_context += f"User: {exchange.get('user', '')}\n"
                history_context += f"Assistant: {exchange.get('assistant', '')}\n"
        
        prompt = f"""Given the chat history and current question, generate a clear, factual query optimized for retrieving information about mutual funds. 

CRITICAL: Preserve the EXACT fund name mentioned (Large Cap, Flexi Cap, ELSS, Hybrid). Do not change or substitute fund names.

Focus on key terms like fund name and metric names (expense ratio, exit load, etc.). Return only the refined query, nothing else.

{history_context}

Current question: {query}

Refined query (must include the exact fund name if mentioned):"""
        
        try:
            system_prompt = "You are a query refinement assistant. ALWAYS preserve exact fund names from the original question. Return only the refined query, no explanations."
            refined = self._call_llm(prompt, max_tokens=100, temperature=0.05, system_prompt=system_prompt)
            
            # Safety check: ensure fund name is preserved
            query_lower = query.lower()
            refined_lower = refined.lower() if refined else ""
            
            fund_names = {
                'large cap': 'HDFC Large Cap Fund',
                'flexi cap': 'HDFC Flexi Cap Fund',
                'flexicap': 'HDFC Flexi Cap Fund',
                'elss': 'HDFC TaxSaver ELSS',
                'taxsaver': 'HDFC TaxSaver ELSS',
                'tax saver': 'HDFC TaxSaver ELSS',
                'hybrid': 'HDFC Hybrid Equity Fund'
            }
            
            # Check if fund name in original but missing in refined
            for key, full_name in fund_names.items():
                if key in query_lower and key not in refined_lower:
                    # Fund name was lost, add it back
                    refined = f"{full_name} {refined}" if refined else query
                    break
            
            return refined if refined else query
        except Exception as e:
            error_msg = str(e)
            print(f"Error refining query: {error_msg}")
            return query  # Fallback to original query
    
    def _retry_with_simpler_prompt(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """Retry with a much simpler prompt if initial attempt was blocked"""
        # Use only the first chunk, and only first 1000 chars
        simple_context = chunks[0]['text'][:1000] if chunks else ""

        try:
            simple_prompt = f"""Answer this question using only the information below:

{simple_context}

Question: {query}

Answer in one sentence:"""
            
            simple_system = "You are a helpful assistant. Answer questions concisely using only the provided information."
            
            answer = self._call_llm(simple_prompt, max_tokens=100, temperature=0.1, system_prompt=simple_system)
            return answer if answer else "I apologize, but I'm unable to generate a response. The information may not be available in the retrieved context, or there was an issue processing the request."
        except Exception as e:
            return f"I encountered an error: {str(e)[:100]}. Please try rephrasing your question."
    
    def _clean_context(self, text: str) -> str:
        """Clean context text to remove noise only - keeps all content"""
        # Remove excessive whitespace (3+ newlines -> 2 newlines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove common PDF artifacts
        text = re.sub(r'Page \d+ of \d+', '', text)
        # Remove navigation elements
        text = re.sub(r'Home\s*/\s*[^\n]*', '', text)
        text = re.sub(r'© \d{4}.*?All Rights Reserved', '', text)
        # Remove excessive repeated characters (like "---" or "===")
        text = re.sub(r'[-=]{3,}', '', text)
        # Clean up multiple spaces
        text = re.sub(r' {2,}', ' ', text)
        # Remove empty lines at start/end
        text = text.strip()
        return text
    
    def generate_answer(self, refined_query: str, chunks: List[Dict[str, Any]], source_url: str) -> str:
        """Stage 2: Generate answer using LLM with retrieved context"""
        # Combine and clean ALL retrieved chunks (keep full content)
        context_parts = []
        for chunk in chunks:
            cleaned_text = self._clean_context(chunk['text'])
            context_parts.append(cleaned_text)
        
        # Join all chunks with clear separators
        context = "\n\n---\n\n".join(context_parts)
        
        system_prompt = """You are a helpful assistant that answers factual questions about mutual funds. Provide natural, well-formatted answers that are precise and friendly. Answer ONLY what is asked. Use proper formatting with bullet points and line breaks for better readability. Only use information from the provided context."""
        
        user_prompt = f"""Use the following information to answer the question. Provide a well-formatted answer with proper structure.

{context}

Question: {refined_query}

Important formatting rules:
1. Answer ONLY the specific question asked - don't add extra information
2. For simple single-value questions (like "What is the expense ratio?"), give a direct sentence answer
3. For questions with multiple points, use bullet points (•) with each point on a new line
4. For step-by-step instructions, use numbered points (1., 2., 3.)
5. Use line breaks between different concepts for better readability
6. For minimum SIP questions, look for "Minimum SIP" amount, not "additional purchase"
7. Be precise - distinguish between initial minimum and additional purchase amounts

Format examples:
- Single answer: "The expense ratio of HDFC Large Cap Fund is 0.96%."
- Multiple points: "The HDFC Large Cap Fund has the following features:\n• Expense ratio: 0.96%\n• Exit load: 1% if redeemed within 1 year\n• Minimum SIP: Rs. 500"
- Steps: "To download your CAS statement:\n1. Visit the CAMS or Karvy website\n2. Enter your PAN and email\n3. Click on 'Submit'"

Answer:"""
        
        try:
            # Increase max_tokens for better formatted answers
            answer = self._call_llm(user_prompt, max_tokens=250, temperature=0.2, system_prompt=system_prompt)
            return answer if answer else self._retry_with_simpler_prompt(refined_query, chunks)
        except Exception as e:
            error_msg = str(e)
            print(f"Error generating answer: {error_msg}")
            # Try simpler prompt on error
            try:
                return self._retry_with_simpler_prompt(refined_query, chunks)
            except:
                # Return a more helpful error message
                if "API key" in error_msg or "authentication" in error_msg.lower():
                    return "Error: API authentication failed. Please check your API key in the .env file."
                elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    return "Error: API quota exceeded. Please try again later."
                else:
                    return f"I encountered an error: {error_msg[:100]}. Please try again."
    
    def format_response(self, answer: str, source_url: str, source_title: str, last_updated: str) -> str:
        """Format response with citation and last updated date"""
        citation = self.citation_handler.format_citation(source_url, source_title)
        
        # Remove any existing "Source:" from answer if LLM added it
        answer = re.sub(r'\s*Source:.*$', '', answer, flags=re.IGNORECASE)
        answer = answer.strip()
        
        # Format with cleaner layout - Streamlit-compatible
        formatted = f"{answer}\n\n> 📄 **Source:** {citation}  \n> *Updated: {last_updated}*"
        return formatted
    
    def needs_clarification(self, query: str, chat_history: List[Dict[str, str]]) -> Tuple[bool, Optional[str]]:
        """Check if query needs clarification (e.g., which fund?)"""
        query_lower = query.lower()
        
        # List of ambiguous queries that need fund specification
        ambiguous_patterns = [
            (r'\b(minimum|min).*(sip|investment|amount)', 
             "Which fund would you like to know about?\n\nWe cover:\n• HDFC Large Cap Fund\n• HDFC Flexi Cap Fund\n• HDFC TaxSaver (ELSS)\n• HDFC Hybrid Equity Fund"),
            (r'\b(expense ratio|ter|fees)\b', 
             "Which fund's expense ratio would you like to know?\n\nWe cover:\n• HDFC Large Cap Fund\n• HDFC Flexi Cap Fund\n• HDFC TaxSaver (ELSS)\n• HDFC Hybrid Equity Fund"),
            (r'\b(exit load|redemption)\b', 
             "Which fund's exit load would you like to know?\n\nWe cover:\n• HDFC Large Cap Fund\n• HDFC Flexi Cap Fund\n• HDFC TaxSaver (ELSS)\n• HDFC Hybrid Equity Fund"),
            (r'\b(benchmark|index)\b', 
             "Which fund's benchmark would you like to know?\n\nWe cover:\n• HDFC Large Cap Fund\n• HDFC Flexi Cap Fund\n• HDFC TaxSaver (ELSS)\n• HDFC Hybrid Equity Fund"),
            (r'\bfund manager\b', 
             "Which fund's fund manager would you like to know?\n\nWe cover:\n• HDFC Large Cap Fund\n• HDFC Flexi Cap Fund\n• HDFC TaxSaver (ELSS)\n• HDFC Hybrid Equity Fund"),
            (r'\baum\b', 
             "Which fund's AUM would you like to know?\n\nWe cover:\n• HDFC Large Cap Fund\n• HDFC Flexi Cap Fund\n• HDFC TaxSaver (ELSS)\n• HDFC Hybrid Equity Fund"),
        ]
        
        # Check if query mentions a specific fund
        fund_mentions = ['large cap', 'flexi cap', 'flexicap', 'elss', 'taxsaver', 'tax saver', 'hybrid']
        has_fund_mention = any(fund in query_lower for fund in fund_mentions)
        
        # If no fund mentioned and matches ambiguous pattern, ask for clarification
        if not has_fund_mention:
            for pattern, clarification in ambiguous_patterns:
                if re.search(pattern, query_lower):
                    return True, clarification
        
        return False, None
    
    def handle_factual_query(self, query: str, chat_history: List[Dict[str, str]]) -> Tuple[str, Optional[str]]:
        """Handle factual query using two-stage RAG"""
        # Check if query needs clarification
        needs_clarif, clarification_msg = self.needs_clarification(query, chat_history)
        if needs_clarif:
            return clarification_msg, None
        
        # Ensure vector store is initialized
        if not self.rag_system.collection:
            try:
                # Try to create vector store automatically
                self.rag_system.create_vector_store(force_recreate=False)
            except FileNotFoundError as e:
                if 'cleaned_knowledge_base.json' in str(e):
                    return "Error: Knowledge base file not found. Please ensure cleaned_knowledge_base.json exists in the repository.", None
                return f"Error: Required file not found. {str(e)}", None
            except Exception as e:
                # Log the error but try to continue
                import traceback
                print(f"Warning: Vector store initialization error: {e}")
                print(traceback.format_exc())
                # Try to continue anyway - might work if collection exists
                if not self.rag_system.collection:
                    return f"Error: Could not initialize vector store. {str(e)}", None
        
        # Stage 1: Refine query
        refined_query = self.refine_query(query, chat_history)
        
        # Retrieve relevant chunks (increased to 5 to catch factsheet with metrics)
        chunks = self.rag_system.retrieve_relevant_chunks(refined_query, k=5)
        
        if not chunks:
            return "I couldn't find relevant information in my knowledge base. Please try rephrasing your question or ask about a different aspect of HDFC Mutual Funds.", None
        
        # Get citation from top chunk
        top_chunk = chunks[0]
        citation_info = self.citation_handler.extract_citation(top_chunk['metadata'])
        
        if not citation_info:
            return "I found information but couldn't retrieve the source. Please try again.", None
        
        # Stage 2: Generate answer
        answer = self.generate_answer(refined_query, chunks, citation_info['url'])
        
        # Format response
        last_updated = self.rag_system.get_last_updated_date()
        formatted_answer = self.format_response(
            answer,
            citation_info['url'],
            citation_info['title'],
            last_updated
        )
        
        return formatted_answer, citation_info['url']
    
    def process_query(self, query: str, chat_history: List[Dict[str, str]] = None) -> Tuple[str, Optional[str]]:
        """Main method to process a query"""
        if chat_history is None:
            chat_history = []
        
        query_type = self.classify_query_type(query)
        
        if query_type == 'greeting':
            return self.handle_greeting(), None
        elif query_type == 'coverage':
            return self.handle_coverage_query(), None
        elif query_type == 'out_of_context':
            return self.handle_out_of_context(), None
        elif query_type == 'advice':
            return self.handle_advice_query(), None
        else:  # factual
            return self.handle_factual_query(query, chat_history)

