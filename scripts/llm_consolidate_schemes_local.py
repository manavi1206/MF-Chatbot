#!/usr/bin/env python3
"""
LLM-based Scheme Consolidation with Local Models Support
Supports: Ollama, Hugging Face Transformers, OpenAI, Anthropic
No rate limits when using local models (Ollama/Hugging Face)
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMSchemeConsolidator:
    def __init__(self, model_type: str = "ollama", model_name: str = "llama3.1:8b", api_key: Optional[str] = None):
        """
        Initialize LLM consolidator
        
        Args:
            model_type: "ollama", "huggingface", "openai", "anthropic", "gemini"
            model_name: Model name (e.g., "llama3.1:8b" for Ollama, "mistralai/Mistral-7B-Instruct-v0.2" for HF)
            api_key: API key (only needed for cloud models)
        """
        self.model_type = model_type.lower()
        self.model_name = model_name
        self.api_key = api_key
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the appropriate model based on model_type"""
        if self.model_type == "ollama":
            try:
                import ollama
                self.model = ollama
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
                raise
        
        elif self.model_type == "huggingface":
            try:
                from transformers import pipeline
                print(f"✓ Loading Hugging Face model: {self.model_name}")
                print("  (This may take a few minutes on first run...)")
                self.model = pipeline(
                    "text-generation",
                    model=self.model_name,
                    device_map="auto",
                    torch_dtype="float16" if os.getenv("USE_GPU", "false").lower() == "true" else None
                )
                print("✓ Model loaded")
            except ImportError:
                print("⚠️  Transformers not installed. Install with: pip install transformers torch")
                raise
        
        elif self.model_type == "openai":
            try:
                import openai
                if not self.api_key:
                    self.api_key = os.getenv('OPENAI_API_KEY')
                if not self.api_key:
                    raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
                openai.api_key = self.api_key
                self.model = openai
                print(f"✓ Using OpenAI with model: {self.model_name}")
            except ImportError:
                print("⚠️  OpenAI not installed. Install with: pip install openai")
                raise
        
        elif self.model_type == "anthropic":
            try:
                import anthropic
                if not self.api_key:
                    self.api_key = os.getenv('ANTHROPIC_API_KEY')
                if not self.api_key:
                    raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable.")
                self.model = anthropic.Anthropic(api_key=self.api_key)
                print(f"✓ Using Anthropic Claude with model: {self.model_name}")
            except ImportError:
                print("⚠️  Anthropic not installed. Install with: pip install anthropic")
                raise
        
        elif self.model_type == "gemini":
            try:
                import google.generativeai as genai
                if not self.api_key:
                    self.api_key = os.getenv('GEMINI_API_KEY')
                if not self.api_key:
                    raise ValueError("Gemini API key required. Set GEMINI_API_KEY environment variable.")
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                print(f"✓ Using Gemini with model: {self.model_name}")
            except ImportError:
                print("⚠️  Google Generative AI not installed. Install with: pip install google-generativeai")
                raise
        else:
            raise ValueError(f"Unknown model_type: {self.model_type}. Use: ollama, huggingface, openai, anthropic, or gemini")
    
    def _call_llm(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.1) -> str:
        """Call the appropriate LLM API"""
        if self.model_type == "ollama":
            response = self.model.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            )
            # Ollama returns the response directly in the 'response' field
            if isinstance(response, dict):
                return response.get('response', '').strip()
            else:
                return str(response).strip()
        
        elif self.model_type == "huggingface":
            # For Hugging Face, we need to format the prompt properly
            formatted_prompt = f"<|system|>You are a helpful assistant.<|user|>{prompt}<|assistant|>"
            result = self.model(
                formatted_prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                return_full_text=False
            )
            return result[0]['generated_text'].strip()
        
        elif self.model_type == "openai":
            response = self.model.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts structured data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        
        elif self.model_type == "anthropic":
            response = self.model.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text.strip()
        
        elif self.model_type == "gemini":
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            response = self.model.generate_content(
                prompt,
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
    
    def extract_metrics_with_llm(self, fund_name: str, fund_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to extract structured metrics from all sources"""
        
        # Get content from the main content field
        main_content = fund_data.get('content', '')
        
        # Also try to get content from sources if available
        source_contents = []
        for source in fund_data.get('sources', []):
            content = source.get('content', '')
            if content and len(content.strip()) > 50:
                source_title = source.get('source_title', 'Unknown')
                source_type = source.get('source_type', 'unknown')
                truncated_content = content[:8000] if len(content) > 8000 else content
                source_contents.append(f"=== {source_title} ({source_type}) ===\n{truncated_content}\n---END OF SOURCE---")
        
        # Combine main content and source contents
        if source_contents:
            all_content = main_content + "\n\n" + "\n\n".join(source_contents)
        else:
            all_content = main_content
        
        # Truncate total content to ~40000 chars
        if len(all_content) > 40000:
            all_content = all_content[:35000] + "\n\n[... content truncated ...]\n\n" + all_content[-5000:]
        
        prompt = f"""Extract structured metrics from mutual fund documents. Return ONLY a JSON object.

FUND NAME: {fund_name}

SOURCE DOCUMENTS:
{all_content}

Extract these metrics (only include if found):
{{
  "expense_ratio": "percentage as string (e.g., '0.96%') or null",
  "benchmark": "exact benchmark index name (e.g., 'NIFTY 100 Total Return Index') or null - NOT 'Riskometer'",
  "nav": "NAV value as number string or null",
  "aum": "AUM with unit (e.g., '39,779.26 Cr') or null",
  "exit_load": "complete exit load description or null",
  "riskometer": "risk level (e.g., 'Very High', 'Moderate') or null",
  "investment_objective": "complete investment objective or null",
  "returns": ["array of return percentages"] or null,
  "inception_date": "DD/MM/YYYY or null",
  "fund_manager": "manager name(s) or null",
  "min_investment": "minimum amount (e.g., '₹100') or null",
  "lock_in_period": "lock-in if applicable or null"
}}

Rules:
- Extract actual benchmark index names, NOT "Riskometer"
- Extract real NAV/AUM values, not commas or placeholders
- Include expense_ratio if mentioned anywhere
- Include returns if any return percentages are mentioned
- Only include fields where you found actual data - use null for missing fields

Return ONLY valid JSON, no explanations."""

        try:
            result_text = self._call_llm(prompt, max_tokens=2000, temperature=0.0)
            
            # Extract JSON from response
            import re
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            # Try to find JSON object
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(0)
            
            try:
                metrics = json.loads(result_text)
                # Filter out null values
                filtered_metrics = {}
                for k, v in metrics.items():
                    if v is not None and v != "null" and v != "" and v != []:
                        if isinstance(v, list):
                            v = [item for item in v if item is not None and item != "" and item != "null"]
                            if v:
                                filtered_metrics[k] = v
                        else:
                            filtered_metrics[k] = v
                return filtered_metrics
            except json.JSONDecodeError as e:
                print(f"  ⚠️ JSON parse error: {e}")
                print(f"  Response: {result_text[:300]}...")
                return {}
        except Exception as e:
            print(f"  ⚠️ Error extracting metrics: {e}")
            return {}
    
    def consolidate_content_with_llm(self, fund_name: str, fund_data: Dict[str, Any]) -> str:
        """Use LLM to consolidate content from all sources"""
        
        main_content = fund_data.get('content', '')
        
        source_contents = []
        for source in fund_data.get('sources', []):
            content = source.get('content', '')
            if content and len(content.strip()) > 50:
                source_type = source.get('source_type', 'unknown')
                source_title = source.get('source_title', 'Unknown')
                truncated_content = content[:8000] if len(content) > 8000 else content
                source_contents.append({
                    'type': source_type,
                    'title': source_title,
                    'content': truncated_content
                })
        
        if source_contents:
            combined_content = main_content + "\n\n" + "\n\n".join([
                f"=== {src['title']} ({src['type']}) ===\n{src['content']}"
                for src in source_contents
            ])
        else:
            combined_content = main_content
        
        if len(combined_content) > 40000:
            combined_content = combined_content[:40000] + "\n\n[Content truncated...]"
        
        prompt = f"""Consolidate mutual fund information from multiple sources into one clean entry.

FUND: {fund_name}

SOURCES:
{combined_content}

Create a single consolidated knowledge base entry by:
1. Removing ALL duplicates and redundant information
2. Removing navigation, footers, headers, and noise
3. Organizing information logically
4. Preserving ALL unique factual information
5. Keeping important details: investment objective, exit load, fund manager, etc.

OUTPUT FORMAT:
=== {fund_name} ===

Investment Objective:
[Complete investment objective]

Key Features:
[Important scheme features]

Exit Load:
[Complete exit load details]

Fund Manager:
[Fund manager name(s)]

Investment Strategy:
[How the fund invests]

Other Information:
[Any other relevant factual information]

Return ONLY the consolidated content, no explanations."""

        try:
            consolidated = self._call_llm(prompt, max_tokens=8000, temperature=0.1)
            
            # Check if LLM gave a "ready" response
            if "ready" in consolidated.lower() or "please provide" in consolidated.lower() or len(consolidated) < 200:
                print(f"  ⚠️ LLM returned 'ready' response. Using original content.")
                return main_content if main_content else combined_content[:2000]
            
            return consolidated
        except Exception as e:
            print(f"  ⚠️ Error consolidating content: {e}")
            return main_content if main_content else ""
    
    def consolidate_scheme(self, fund_tag: str, fund_data: Dict[str, Any]) -> Dict[str, Any]:
        """Consolidate one scheme using LLM"""
        fund_name = fund_data.get('fund_name', '')
        sources = fund_data.get('sources', [])
        
        print(f"\n{'='*80}")
        print(f"Processing: {fund_name} ({fund_tag})")
        print(f"{'='*80}")
        print(f"  Sources: {len(sources)}")
        
        # Extract metrics
        print(f"\n  Step 1: Extracting metrics with {self.model_type}...")
        metrics = self.extract_metrics_with_llm(fund_name, fund_data)
        print(f"  ✓ Extracted metrics: {list(metrics.keys())}")
        for key, value in metrics.items():
            if value:
                if isinstance(value, list):
                    print(f"    - {key}: {value}")
                else:
                    val_str = str(value)
                    if len(val_str) > 100:
                        print(f"    - {key}: {val_str[:100]}...")
                    else:
                        print(f"    - {key}: {val_str}")
        
        # Consolidate content
        print(f"\n  Step 2: Consolidating content with {self.model_type}...")
        consolidated_content = self.consolidate_content_with_llm(fund_name, fund_data)
        print(f"  ✓ Consolidated content: {len(consolidated_content)} chars")
        
        # Prepare source metadata
        source_metadata = []
        for source in sources:
            source_metadata.append({
                'source_id': source.get('source_id', ''),
                'source_title': source.get('source_title', ''),
                'source_type': source.get('source_type', ''),
                'url': source.get('url', ''),
                'authority': source.get('authority', '')
            })
        
        return {
            'fund_name': fund_name,
            'scheme_tag': fund_tag,
            'content': consolidated_content,
            'metrics': metrics,
            'sources': source_metadata,
            'last_updated': fund_data.get('last_updated', datetime.now().isoformat())
        }
    
    def consolidate_all(self, input_file: str, output_file: str):
        """Consolidate all schemes using LLM"""
        print("="*80)
        print(f"LLM-BASED SCHEME CONSOLIDATION ({self.model_type.upper()})")
        print("="*80)
        
        print("\nLoading knowledge base...")
        with open(input_file, 'r', encoding='utf-8') as f:
            kb = json.load(f)
        
        # If input file doesn't have content in sources, try consolidated_scheme_data.json
        if not any(source.get('content') for fund in kb.get('funds', {}).values() for source in fund.get('sources', [])):
            print("  Sources don't have content. Trying consolidated_scheme_data.json...")
            try:
                with open('consolidated_scheme_data.json', 'r', encoding='utf-8') as f:
                    consolidated_data = json.load(f)
                    for fund_tag, consolidated_fund in consolidated_data.get('funds', {}).items():
                        if fund_tag in kb.get('funds', {}):
                            kb['funds'][fund_tag]['content'] = consolidated_fund.get('content', '')
                            if consolidated_fund.get('metrics'):
                                kb['funds'][fund_tag].setdefault('metrics', {}).update(consolidated_fund['metrics'])
                print("  ✓ Loaded content from consolidated_scheme_data.json")
            except FileNotFoundError:
                print("  ⚠️ consolidated_scheme_data.json not found. Using available content.")
        
        consolidated = {
            'metadata': {
                'created_at': kb.get('metadata', {}).get('created_at', ''),
                'version': '4.0',
                'description': f'LLM-consolidated scheme data using {self.model_type}',
                'consolidated_at': datetime.now().isoformat(),
                'model_used': f'{self.model_type}:{self.model_name}'
            },
            'funds': {},
            'regulatory': kb.get('regulatory', {}),
            'help': kb.get('help', {})
        }
        
        print(f"✓ Loaded knowledge base with {len(kb.get('funds', {}))} funds")
        
        # Process each fund
        for fund_tag, fund_data in kb.get('funds', {}).items():
            try:
                consolidated_scheme = self.consolidate_scheme(fund_tag, fund_data)
                consolidated['funds'][fund_tag] = consolidated_scheme
            except Exception as e:
                print(f"\n  ❌ Error processing {fund_tag}: {e}")
                import traceback
                traceback.print_exc()
                # Keep original data as fallback
                consolidated['funds'][fund_tag] = {
                    'fund_name': fund_data.get('fund_name', ''),
                    'scheme_tag': fund_tag,
                    'content': fund_data.get('content', ''),
                    'metrics': fund_data.get('metrics', {}),
                    'sources': [{
                        'source_id': s.get('source_id', ''),
                        'source_title': s.get('source_title', ''),
                        'source_type': s.get('source_type', ''),
                        'url': s.get('url', ''),
                        'authority': s.get('authority', '')
                    } for s in fund_data.get('sources', [])],
                    'last_updated': fund_data.get('last_updated', '')
                }
        
        print("\n" + "="*80)
        print("Saving consolidated knowledge base...")
        print("="*80)
        
        # Backup original file
        backup_file = input_file.replace('.json', '.backup.json')
        if os.path.exists(input_file):
            import shutil
            shutil.copy2(input_file, backup_file)
            print(f"✓ Backed up original to {backup_file}")
        
        # Save consolidated data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(consolidated, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved to {output_file}")
        
        # Print summary
        print("\n" + "="*80)
        print("CONSOLIDATION SUMMARY")
        print("="*80)
        print(f"Total schemes: {len(consolidated['funds'])}")
        for fund_tag, scheme in consolidated['funds'].items():
            print(f"\n{fund_tag}: {scheme['fund_name']}")
            print(f"  Content: {len(scheme['content'])} chars")
            print(f"  Sources: {len(scheme['sources'])}")
            print(f"  Metrics: {len(scheme['metrics'])} fields")
            if scheme['metrics']:
                print(f"    Fields: {', '.join(scheme['metrics'].keys())}")
        
        return consolidated

if __name__ == '__main__':
    import sys
    
    # Parse command line arguments
    model_type = os.getenv('LLM_MODEL_TYPE', 'ollama').lower()
    model_name = os.getenv('LLM_MODEL_NAME', 'llama3.1:8b')
    
    if len(sys.argv) > 1:
        model_type = sys.argv[1].lower()
    if len(sys.argv) > 2:
        model_name = sys.argv[2]
    
    print(f"\nUsing {model_type} with model: {model_name}\n")
    
    consolidator = LLMSchemeConsolidator(
        model_type=model_type,
        model_name=model_name,
        api_key=None  # Will be read from environment variables for cloud models
    )
    
    consolidated = consolidator.consolidate_all(
        'cleaned_knowledge_base.json',
        'cleaned_knowledge_base.json'
    )
    
    print("\n" + "="*80)
    print("✓ CONSOLIDATION COMPLETE")
    print("="*80)

