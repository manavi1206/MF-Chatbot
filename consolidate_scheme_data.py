#!/usr/bin/env python3
"""
Consolidate scheme data - One clean entry per scheme
Removes duplicates, redundant info, keeps sources
"""

import json
import re
from typing import Dict, List, Any, Set
from collections import defaultdict

class SchemeConsolidator:
    def __init__(self):
        self.seen_sentences = set()
        self.seen_paragraphs = set()
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters for comparison
        text = re.sub(r'[^\w\s]', '', text.lower())
        return text.strip()
    
    def is_duplicate(self, text: str) -> bool:
        """Check if text is duplicate or redundant"""
        normalized = self.normalize_text(text)
        
        # Check if exact duplicate
        if normalized in self.seen_paragraphs:
            return True
        
        # Check if very similar (90% overlap)
        for seen in self.seen_paragraphs:
            if len(normalized) > 50 and len(seen) > 50:
                # Simple similarity check
                words1 = set(normalized.split())
                words2 = set(seen.split())
                if len(words1) > 0 and len(words2) > 0:
                    overlap = len(words1 & words2) / len(words1 | words2)
                    if overlap > 0.9:
                        return True
        
        return False
    
    def extract_key_info(self, content: str) -> Dict[str, Any]:
        """Extract key information from content"""
        info = {}
        
        # Expense Ratio
        er_match = re.search(r'expense ratio[:\s]*([\d.]+)%?', content, re.IGNORECASE)
        if er_match:
            info['expense_ratio'] = er_match.group(1) + '%'
        
        # Exit Load
        exit_load_match = re.search(r'exit load[:\s]*([^.\n]{20,200})', content, re.IGNORECASE | re.DOTALL)
        if exit_load_match:
            info['exit_load'] = exit_load_match.group(1).strip()[:200]
        
        # Investment Objective
        obj_match = re.search(r'investment objective[:\s]*([^.\n]{30,300})', content, re.IGNORECASE | re.DOTALL)
        if obj_match:
            info['investment_objective'] = obj_match.group(1).strip()[:300]
        
        # Benchmark
        bench_match = re.search(r'benchmark[:\s]*([^.\n]{10,100})', content, re.IGNORECASE)
        if bench_match:
            info['benchmark'] = bench_match.group(1).strip()[:100]
        
        # AUM
        aum_match = re.search(r'aum[:\s]*₹?\s*([\d,]+\.?\d*)\s*(Cr|Crore|Lakh|L)', content, re.IGNORECASE)
        if aum_match:
            info['aum'] = aum_match.group(1) + ' ' + aum_match.group(2)
        
        # NAV
        nav_match = re.search(r'nav[:\s]*₹?\s*([\d,]+\.?\d*)', content, re.IGNORECASE)
        if nav_match:
            info['nav'] = nav_match.group(1)
        
        # Riskometer
        risk_match = re.search(r'riskometer[:\s]*([^.\n]{5,50})', content, re.IGNORECASE)
        if risk_match:
            info['riskometer'] = risk_match.group(1).strip()[:50]
        
        return info
    
    def consolidate_scheme(self, fund_tag: str, fund_data: Dict[str, Any]) -> Dict[str, Any]:
        """Consolidate all sources for one scheme into one clean entry"""
        fund_name = fund_data.get('fund_name', '')
        sources = fund_data.get('sources', [])
        
        # Collect all unique information
        consolidated_content = []
        all_metrics = {}
        all_sources = []
        
        # Priority order: factsheet > SID > KIM > overview (factsheet has most complete info)
        priority_order = {'factsheet': 0, 'sid_pdf': 1, 'kim_pdf': 2, 'scheme_overview': 3}
        sorted_sources = sorted(sources, key=lambda x: priority_order.get(x.get('source_type', ''), 99))
        
        for source in sorted_sources:
            source_id = source.get('source_id', '')
            source_title = source.get('source_title', '')
            source_type = source.get('source_type', '')
            url = source.get('url', '')
            authority = source.get('authority', '')
            content = source.get('content', '')
            metrics = source.get('extracted_metrics', {})
            
            # Merge metrics (prefer factsheet metrics)
            for key, value in metrics.items():
                if key not in all_metrics or value:
                    if value and value != ',' and value != '':
                        all_metrics[key] = value
            
            # Extract key information
            key_info = self.extract_key_info(content)
            for key, value in key_info.items():
                if key not in all_metrics or not all_metrics.get(key):
                    all_metrics[key] = value
            
            # Add source reference
            source_ref = {
                'source_id': source_id,
                'source_title': source_title,
                'source_type': source_type,
                'url': url,
                'authority': authority
            }
            
            # Process content - remove duplicates
            if content and len(content.strip()) > 50:
                # Split into sentences/paragraphs
                paragraphs = re.split(r'\n{2,}|\.\s+(?=[A-Z])', content)
                
                for para in paragraphs:
                    para = para.strip()
                    if len(para) > 30 and not self.is_duplicate(para):
                        # Remove navigation noise
                        if any(word in para.lower() for word in ['home', 'contact us', 'follow us', 'careers', 'statutory disclosures']):
                            continue
                        # Remove repetitive footer text
                        if 'to be the most respected' in para.lower() or 'to be the wealth creator' in para.lower():
                            continue
                        
                        normalized = self.normalize_text(para)
                        if normalized not in self.seen_paragraphs:
                            consolidated_content.append(para)
                            self.seen_paragraphs.add(normalized)
            
            all_sources.append(source_ref)
        
        # Combine all content
        final_content = '\n\n'.join(consolidated_content)
        
        # Clean up final content
        final_content = re.sub(r'\n{3,}', '\n\n', final_content)
        final_content = re.sub(r' {2,}', ' ', final_content)
        final_content = final_content.strip()
        
        return {
            'fund_name': fund_name,
            'scheme_tag': fund_tag,
            'content': final_content,
            'metrics': all_metrics,
            'sources': all_sources,
            'last_updated': fund_data.get('last_updated', '')
        }
    
    def consolidate_all(self, input_file: str, output_file: str):
        """Consolidate all schemes"""
        print("Loading knowledge base...")
        with open(input_file, 'r', encoding='utf-8') as f:
            kb = json.load(f)
        
        consolidated = {
            'metadata': {
                'created_at': kb.get('metadata', {}).get('created_at', ''),
                'version': '3.0',
                'description': 'Consolidated scheme data - One clean entry per scheme, no duplicates'
            },
            'funds': {},
            'regulatory': kb.get('regulatory', {}),
            'help': kb.get('help', {})
        }
        
        print("\nConsolidating schemes...")
        for fund_tag, fund_data in kb.get('funds', {}).items():
            print(f"\nProcessing {fund_tag}: {fund_data.get('fund_name', '')}")
            self.seen_paragraphs = set()  # Reset for each scheme
            
            consolidated_scheme = self.consolidate_scheme(fund_tag, fund_data)
            
            print(f"  Original sources: {len(fund_data.get('sources', []))}")
            print(f"  Consolidated sources: {len(consolidated_scheme['sources'])}")
            print(f"  Content length: {len(consolidated_scheme['content'])} chars")
            print(f"  Metrics: {list(consolidated_scheme['metrics'].keys())}")
            
            consolidated['funds'][fund_tag] = consolidated_scheme
        
        print("\nSaving consolidated knowledge base...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(consolidated, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Saved to {output_file}")
        return consolidated

if __name__ == '__main__':
    consolidator = SchemeConsolidator()
    consolidated = consolidator.consolidate_all(
        'cleaned_knowledge_base.json',
        'consolidated_scheme_data.json'
    )
    
    print("\n" + "="*80)
    print("CONSOLIDATION COMPLETE")
    print("="*80)
    print(f"Total schemes: {len(consolidated['funds'])}")
    for fund_tag, scheme in consolidated['funds'].items():
        print(f"\n{fund_tag}:")
        print(f"  Content: {len(scheme['content'])} chars")
        print(f"  Sources: {len(scheme['sources'])}")
        print(f"  Metrics: {scheme['metrics']}")



