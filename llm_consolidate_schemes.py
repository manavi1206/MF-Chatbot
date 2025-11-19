#!/usr/bin/env python3
"""
LLM-based Scheme Consolidation
Uses Gemini API to intelligently extract metrics and consolidate content from all sources
Creates a single source of truth for each fund scheme
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMSchemeConsolidator:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key not found. Set GEMINI_API_KEY environment variable.")
        
        genai.configure(api_key=self.api_key)
        # Use gemini-2.0-flash (known to work) with fallback
        try:
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        except:
            self.model = genai.GenerativeModel('gemini-pro-latest')
        
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
    
    def extract_metrics_with_llm(self, fund_name: str, fund_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to extract structured metrics from all sources"""
        
        # Get content from the main content field (consolidated content)
        main_content = fund_data.get('content', '')
        
        # Also try to get content from sources if available
        source_contents = []
        for source in fund_data.get('sources', []):
            content = source.get('content', '')
            if content and len(content.strip()) > 50:
                source_title = source.get('source_title', 'Unknown')
                source_type = source.get('source_type', 'unknown')
                # Truncate to first 8000 chars per source
                truncated_content = content[:8000] if len(content) > 8000 else content
                source_contents.append(f"=== {source_title} ({source_type}) ===\n{truncated_content}\n---END OF SOURCE---")
        
        # Combine main content and source contents
        if source_contents:
            all_content = main_content + "\n\n" + "\n\n".join(source_contents)
        else:
            all_content = main_content
        
        # Truncate total content to ~40000 chars to stay within token limits but get more data
        if len(all_content) > 40000:
            # Keep first 35000 chars and last 5000 chars to preserve both beginning and end
            all_content = all_content[:35000] + "\n\n[... content truncated ...]\n\n" + all_content[-5000:]
        
        prompt = f"""You are a data extraction expert. Extract structured metrics from mutual fund documents.

FUND NAME: {fund_name}

SOURCE DOCUMENTS:
{all_content}

TASK: Extract all available metrics from the source documents above. Return ONLY a valid JSON object with this exact structure:

{{
  "expense_ratio": "percentage as string (e.g., '0.96%') or null",
  "benchmark": "exact benchmark index name (e.g., 'NIFTY 100 Total Return Index') or null - DO NOT return 'Riskometer'",
  "nav": "NAV value as number string (e.g., '1234.56') or null",
  "aum": "AUM with unit (e.g., '39,779.26 Cr') or null",
  "exit_load": "complete exit load description or null",
  "riskometer": "risk level (e.g., 'Very High', 'Moderate', 'Low') or null",
  "investment_objective": "complete investment objective statement or null",
  "returns": ["array of return percentages as strings"] or null,
  "inception_date": "date in DD/MM/YYYY format or null",
  "fund_manager": "fund manager name(s) or null",
  "min_investment": "minimum investment amount (e.g., '₹100') or null",
  "lock_in_period": "lock-in period if applicable (e.g., '3 years') or null"
}}

CRITICAL RULES:
1. Return ONLY the JSON object, no explanations, no markdown, no code blocks
2. For benchmark: Extract actual index names like "NIFTY 100 TRI", "NIFTY 500 TRI" - NEVER return "Riskometer" or "Benchmark Riskometer". Look for phrases like "NIFTY 100 (Total Return Index)" or "NIFTY 500 TRI"
3. For expense_ratio: Look for "Total Expense Ratio", "TER", "expense ratio", or numbers like "0.96" followed by "%" - extract the percentage value
4. For returns: Extract all return percentages mentioned (look for numbers like "13.99%", "16.97%", etc.)
5. For AUM: Look for "AUM", "Assets Under Management", or amounts like "₹39,779.26 Cr"
6. For NAV: Look for "NAV" followed by numbers like "1234.56" or dates with NAV values
7. For exit_load: Look for "Exit Load" or "exit load" and extract the complete description
8. For riskometer: Look for "Very High", "High", "Moderate", "Low" risk levels
9. Only include fields where you found actual data in the source documents above - use null for missing fields
10. If multiple values exist, use the most recent or most authoritative (factsheet > SID > KIM > overview)

IMPORTANT: The source documents above contain the actual data. Read through them carefully and extract the real values. Do not return all nulls - the data is there in the documents.

BEGIN YOUR RESPONSE WITH {{ AND END WITH }}"""

        try:
            generation_config = {
                "temperature": 0.0,  # Lower temperature for more consistent extraction
                "max_output_tokens": 2000,
            }
            
            # Retry logic for rate limits
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config=generation_config,
                        safety_settings=self.safety_settings
                    )
                    break
                except Exception as e:
                    if "429" in str(e) or "Resource exhausted" in str(e):
                        if attempt < max_retries - 1:
                            print(f"  ⚠️ Rate limit hit, retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                            import time
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                    raise
            
            if response.candidates and response.candidates[0].finish_reason == 1:  # STOP
                result_text = response.text.strip()
                
                # Check if LLM gave a "ready" response instead of actual extraction
                if "ready" in result_text.lower() or "please provide" in result_text.lower() or "i'm" in result_text.lower():
                    print(f"  ⚠️ LLM returned 'ready' response instead of extracting. Using fallback extraction.")
                    return self._fallback_extract_metrics(all_content)
                
                # Extract JSON from response (handle markdown code blocks)
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                # Try to find JSON object in response
                import re
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(0)
                
                try:
                    metrics = json.loads(result_text)
                    # Filter out null values and empty strings - only keep fields with actual data
                    filtered_metrics = {}
                    for k, v in metrics.items():
                        if v is not None and v != "null" and v != "" and v != []:
                            # Also check if it's a list with only null/empty values
                            if isinstance(v, list):
                                v = [item for item in v if item is not None and item != "" and item != "null"]
                                if v:  # Only add if list has items
                                    filtered_metrics[k] = v
                            else:
                                filtered_metrics[k] = v
                    
                    if not filtered_metrics:
                        print(f"  ⚠️ All metrics were null. LLM response: {result_text[:500]}...")
                        print(f"  Using fallback extraction...")
                        fallback_metrics = self._fallback_extract_metrics(all_content)
                        if fallback_metrics:
                            print(f"  ✓ Fallback extracted: {list(fallback_metrics.keys())}")
                        return fallback_metrics
                    
                    return filtered_metrics
                except json.JSONDecodeError as e:
                    print(f"  ⚠️ JSON parse error: {e}")
                    print(f"  Response preview: {result_text[:300]}...")
                    print(f"  Using fallback extraction...")
                    return self._fallback_extract_metrics(all_content)
            else:
                print(f"  ⚠️ LLM response blocked or incomplete")
                return {}
                
        except Exception as e:
            print(f"  ⚠️ Error extracting metrics with LLM: {e}")
            return self._fallback_extract_metrics(all_content)
    
    def _fallback_extract_metrics(self, content: str) -> Dict[str, Any]:
        """Fallback regex-based metric extraction if LLM fails"""
        import re
        metrics = {}
        
        # Expense Ratio
        er_match = re.search(r'expense\s+ratio[:\s]*([\d.]+)%?', content, re.IGNORECASE)
        if er_match:
            metrics['expense_ratio'] = er_match.group(1) + '%'
        
        # Benchmark (look for actual index names)
        bench_patterns = [
            r'(NIFTY\s+\d+\s+(?:Total\s+Return\s+Index|TRI))',
            r'(NIFTY\s+\d+)',
            r'(BSE\s+\w+)',
            r'benchmark[:\s]*([A-Z][^.\n]{5,50}?(?:Index|TRI))',
        ]
        for pattern in bench_patterns:
            bench_match = re.search(pattern, content, re.IGNORECASE)
            if bench_match and 'riskometer' not in bench_match.group(1).lower():
                metrics['benchmark'] = bench_match.group(1).strip()
                break
        
        # NAV
        nav_match = re.search(r'nav[:\s]*₹?\s*([\d,]+\.?\d*)', content, re.IGNORECASE)
        if nav_match:
            nav_val = nav_match.group(1).replace(',', '')
            if nav_val and nav_val != ',':
                metrics['nav'] = nav_val
        
        # AUM
        aum_match = re.search(r'aum[:\s]*₹?\s*([\d,]+\.?\d*)\s*(Cr|Crore|Lakh|L)', content, re.IGNORECASE)
        if aum_match:
            metrics['aum'] = aum_match.group(1) + ' ' + aum_match.group(2)
        
        # Exit Load
        exit_match = re.search(r'exit\s+load[:\s]*([^.\n]{20,300})', content, re.IGNORECASE | re.DOTALL)
        if exit_match:
            metrics['exit_load'] = exit_match.group(1).strip()[:300]
        
        # Riskometer
        risk_match = re.search(r'riskometer[:\s]*(Very\s+High|High|Moderate|Low|Moderately\s+High)', content, re.IGNORECASE)
        if risk_match:
            metrics['riskometer'] = risk_match.group(1)
        
        # Returns
        returns = []
        return_matches = re.findall(r'(\d+\.\d+)%', content)
        for match in return_matches:
            if float(match) > 0 and float(match) < 100:  # Reasonable return range
                returns.append(match)
        if returns:
            metrics['returns'] = returns[:5]  # Limit to 5 returns
        
        # Investment Objective
        obj_match = re.search(r'investment\s+objective[:\s]*([^.\n]{30,400})', content, re.IGNORECASE | re.DOTALL)
        if obj_match:
            metrics['investment_objective'] = obj_match.group(1).strip()[:400]
        
        return metrics
    
    def consolidate_content_with_llm(self, fund_name: str, fund_data: Dict[str, Any]) -> str:
        """Use LLM to consolidate content from all sources, removing duplicates"""
        
        # Get main consolidated content
        main_content = fund_data.get('content', '')
        
        # Also get content from sources if available
        source_contents = []
        for source in fund_data.get('sources', []):
            content = source.get('content', '')
            if content and len(content.strip()) > 50:
                source_type = source.get('source_type', 'unknown')
                source_title = source.get('source_title', 'Unknown')
                # Truncate to first 8000 chars per source
                truncated_content = content[:8000] if len(content) > 8000 else content
                source_contents.append({
                    'type': source_type,
                    'title': source_title,
                    'content': truncated_content
                })
        
        # Combine main content and source contents
        if source_contents:
            combined_content = main_content + "\n\n" + "\n\n".join([
                f"=== {src['title']} ({src['type']}) ===\n{src['content']}"
                for src in source_contents
            ])
        else:
            combined_content = main_content
        
        # Truncate total to ~40000 chars
        if len(combined_content) > 40000:
            combined_content = combined_content[:40000] + "\n\n[Content truncated...]"
        
        prompt = f"""You are a financial data consolidation expert. Consolidate information from multiple mutual fund sources into one comprehensive, clean knowledge base entry.

FUND NAME: {fund_name}

SOURCE DOCUMENTS:
{combined_content}

TASK: Create a single consolidated knowledge base entry by:
1. Removing ALL duplicates and redundant information
2. Removing navigation elements, footers, headers, and noise (like "Click here", "Follow us", "Careers", "Contact us", etc.)
3. Organizing information in a logical, readable structure
4. Preserving ALL unique factual information
5. Keeping important details: investment objective, exit load, fund manager, scheme features, investment strategy, etc.

OUTPUT FORMAT (use these sections):
=== {fund_name} ===

Investment Objective:
[Complete investment objective statement]

Key Features:
[Important scheme features and characteristics]

Exit Load:
[Complete exit load details]

Fund Manager:
[Fund manager name(s)]

Investment Strategy:
[How the fund invests, asset allocation, etc.]

Other Information:
[Any other relevant factual information]

CRITICAL: 
- Return ONLY the consolidated content, no explanations, no "I'm ready" messages
- Start directly with the fund name section
- Remove all navigation, footer, and header noise
- Keep factual information only, no opinions or advice"""

        try:
            generation_config = {
                "temperature": 0.1,  # Lower temperature for more consistent output
                "max_output_tokens": 8000,
            }
            
            # Retry logic for rate limits
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config=generation_config,
                        safety_settings=self.safety_settings
                    )
                    break
                except Exception as e:
                    if "429" in str(e) or "Resource exhausted" in str(e):
                        if attempt < max_retries - 1:
                            print(f"  ⚠️ Rate limit hit, retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                            import time
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                    raise
            
            if response.candidates and response.candidates[0].finish_reason == 1:  # STOP
                consolidated = response.text.strip()
                
                # Check if LLM gave a "ready" response
                if "ready" in consolidated.lower() or "please provide" in consolidated.lower() or len(consolidated) < 200:
                    print(f"  ⚠️ LLM returned 'ready' response. Using fallback consolidation.")
                    return self._fallback_consolidate_content(source_contents)
                
                return consolidated
            else:
                print(f"  ⚠️ LLM response blocked for content consolidation")
                return self._fallback_consolidate_content(source_contents)
                
        except Exception as e:
            print(f"  ⚠️ Error consolidating content with LLM: {e}")
            return self._fallback_consolidate_content(source_contents)
    
    def _fallback_consolidate_content(self, source_contents: List[Dict[str, Any]]) -> str:
        """Fallback content consolidation if LLM fails"""
        import re
        
        seen_paragraphs = set()
        consolidated_parts = []
        
        for src in source_contents:
            content = src['content']
            # Split into paragraphs
            paragraphs = re.split(r'\n{2,}', content)
            
            for para in paragraphs:
                para = para.strip()
                if len(para) < 30:
                    continue
                
                # Normalize for duplicate detection
                normalized = re.sub(r'\s+', ' ', para.lower())
                normalized = re.sub(r'[^\w\s]', '', normalized)
                
                # Skip navigation/footer noise
                if any(word in normalized for word in ['click here', 'follow us', 'careers', 'contact us', 'home', 'statutory disclosures']):
                    continue
                
                # Check for duplicates
                if normalized not in seen_paragraphs and len(normalized) > 50:
                    consolidated_parts.append(para)
                    seen_paragraphs.add(normalized)
        
        return '\n\n'.join(consolidated_parts)
    
    def consolidate_scheme(self, fund_tag: str, fund_data: Dict[str, Any]) -> Dict[str, Any]:
        """Consolidate one scheme using LLM"""
        fund_name = fund_data.get('fund_name', '')
        sources = fund_data.get('sources', [])
        
        print(f"\n{'='*80}")
        print(f"Processing: {fund_name} ({fund_tag})")
        print(f"{'='*80}")
        print(f"  Sources: {len(sources)}")
        
        # Extract metrics using LLM
        print(f"\n  Step 1: Extracting metrics with LLM...")
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
        
        # Consolidate content using LLM
        print(f"\n  Step 2: Consolidating content with LLM...")
        consolidated_content = self.consolidate_content_with_llm(fund_name, fund_data)
        print(f"  ✓ Consolidated content: {len(consolidated_content)} chars")
        
        # Prepare source metadata (without content)
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
        print("LLM-BASED SCHEME CONSOLIDATION")
        print("="*80)
        
        print("\nLoading knowledge base...")
        with open(input_file, 'r', encoding='utf-8') as f:
            kb = json.load(f)
        
        # If input file doesn't have content in sources, try to use consolidated_scheme_data.json
        if not any(source.get('content') for fund in kb.get('funds', {}).values() for source in fund.get('sources', [])):
            print("  Sources don't have content. Trying consolidated_scheme_data.json...")
            try:
                with open('consolidated_scheme_data.json', 'r', encoding='utf-8') as f:
                    consolidated_data = json.load(f)
                    # Merge content from consolidated data
                    for fund_tag, consolidated_fund in consolidated_data.get('funds', {}).items():
                        if fund_tag in kb.get('funds', {}):
                            kb['funds'][fund_tag]['content'] = consolidated_fund.get('content', '')
                            # Also merge any existing metrics
                            if consolidated_fund.get('metrics'):
                                kb['funds'][fund_tag].setdefault('metrics', {}).update(consolidated_fund['metrics'])
                print("  ✓ Loaded content from consolidated_scheme_data.json")
            except FileNotFoundError:
                print("  ⚠️ consolidated_scheme_data.json not found. Using available content.")
        
        consolidated = {
            'metadata': {
                'created_at': kb.get('metadata', {}).get('created_at', ''),
                'version': '4.0',
                'description': 'LLM-consolidated scheme data - Single source of truth per scheme with intelligent metric extraction',
                'consolidated_at': datetime.now().isoformat()
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
    consolidator = LLMSchemeConsolidator()
    consolidated = consolidator.consolidate_all(
        'cleaned_knowledge_base.json',
        'cleaned_knowledge_base.json'
    )
    
    print("\n" + "="*80)
    print("✓ CONSOLIDATION COMPLETE")
    print("="*80)

