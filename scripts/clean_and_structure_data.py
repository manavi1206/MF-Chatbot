#!/usr/bin/env python3
"""
Clean and structure the knowledge base data
- Remove noise (navigation, HTML artifacts, etc.)
- Add clear source attribution
- Structure data better
"""

import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
import csv

class DataCleaner:
    def __init__(self):
        # Load source metadata from CSV
        self.source_metadata = {}
        with open('sources.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.source_metadata[row['source_id']] = {
                    'title': row['source_title'],
                    'url': row['source_url'],
                    'type': row['source_type'],
                    'authority': row['authority'],
                    'scheme_tag': row['scheme_tag']
                }
        
        self.noise_patterns = [
            r'Know More',
            r'Invest Now',
            r'VIEW ALL',
            r'Funds\s*Category',
            r'Equity\s*Debt\s*Index',
            r'Learn\s*MF Simplified',
            r'Blogs\s*Quiz\s*Videos',
            r'Zindagi ke liye SIP',
            r'Macros, Markets and More',
            r'Market Review',
            r'Monetary Policy',
            r'HDFC MF Yearbook',
            r'Webinars',
            r'Deep Dives',
            r'Tuesday Talking Point',
            r'Weekend Bytes',
            r'HDFC MF Insights',
            r'Handbooks',
            r'MD and CEO\'S Desk',
            r'Interviews and Articles',
            r'Calculators',
            r'SIP Calculator',
            r'SWAP Calculator',
            r'Top up SIP',
            r'Impact of inflation',
            r'STP calculator',
            r'Goal SIP',
            r'Present value',
            r'Retirement SIP Calculator',
            r'Cost of child education',
            r'Investor Services',
            r'Fund Related Details',
            r'Factsheet',
            r'Fund Documents',
            r'Cookie.*?Accept',
            r'Privacy Policy',
            r'Terms.*?Conditions',
            r'©.*?HDFC',
            r'All rights reserved',
            r'Skip to main content',
            r'Menu',
            r'Search',
            r'Login',
            r'Sign Up',
        ]
        
    def clean_text(self, text):
        """Remove noise from text"""
        if not text:
            return ""
        
        # Remove HTML tags if present
        if '<' in text and '>' in text:
            soup = BeautifulSoup(text, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
        
        # Remove noise patterns
        for pattern in self.noise_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines
        text = re.sub(r' {3,}', ' ', text)  # Max 2 spaces
        text = re.sub(r'\t+', ' ', text)  # Replace tabs with space
        
        # Remove lines that are too short or likely navigation
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if len(line) < 3:  # Skip very short lines
                continue
            if line.isupper() and len(line) < 20 and not line.isdigit():  # Skip short uppercase headers
                continue
            # Skip common navigation items
            if line.lower() in ['home', 'about', 'contact', 'login', 'sign up', 'menu', 'search']:
                continue
            cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def extract_key_metrics(self, text):
        """Extract key metrics from text"""
        metrics = {}
        
        # NAV
        nav_match = re.search(r'NAV[:\s]*₹?\s*([\d,]+\.?\d*)', text, re.I)
        if nav_match:
            metrics['nav'] = nav_match.group(1)
        
        # AUM
        aum_match = re.search(r'AUM[:\s]*₹?\s*([\d,]+\.?\d*)\s*(Crore|Cr|Lakh|L)', text, re.I)
        if aum_match:
            metrics['aum'] = aum_match.group(1) + ' ' + aum_match.group(2)
        
        # Expense Ratio
        expense_match = re.search(r'Total Expense Ratio[:\s]*([\d.]+)%?', text, re.I)
        if expense_match:
            metrics['expense_ratio'] = expense_match.group(1) + '%'
        
        # Returns
        returns = re.findall(r'(\d+\.\d+)%', text)
        if returns:
            metrics['returns'] = returns[:5]  # First 5 return values
        
        return metrics
    
    def split_by_source(self, compiled_text, source_ids):
        """Try to split compiled text by source markers"""
        sources_content = {}
        
        # Look for source markers in the text
        source_markers = {
            'amc_largecap_overview': r'---\s*amc_largecap_overview\s*---|HDFC Large Cap Fund.*?Overview',
            'amc_largecap_sid': r'---\s*SID PDF.*?---|SID.*?Large Cap',
            'amc_largecap_kim': r'---\s*KIM.*?---|KIM.*?Large Cap',
            'amc_flexicap_overview': r'---\s*amc_flexicap_overview\s*---|HDFC Flexi Cap Fund.*?Overview',
            'amc_flexicap_sid': r'---\s*SID PDF.*?---|SID.*?Flexi Cap',
            'amc_flexicap_kim': r'---\s*KIM.*?---|KIM.*?Flexi Cap',
            'amc_elss_overview': r'---\s*amc_elss_overview\s*---|HDFC.*?ELSS.*?Overview',
            'amc_elss_sid': r'---\s*SID PDF.*?---|SID.*?ELSS',
            'amc_elss_kim': r'---\s*KIM.*?---|KIM.*?ELSS',
            'amc_hybrid_overview': r'---\s*amc_hybrid_overview\s*---|HDFC Hybrid.*?Overview',
            'amc_hybrid_sid': r'---\s*SID PDF.*?---|SID.*?Hybrid',
            'amc_hybrid_kim': r'---\s*KIM.*?---|KIM.*?Hybrid',
            'factsheet': r'---\s*factsheet\s*---|Factsheet|October 2025',
        }
        
        # Try to find source sections
        for source_id in source_ids:
            if source_id in source_markers:
                pattern = source_markers[source_id]
                match = re.search(pattern, compiled_text, re.I | re.DOTALL)
                if match:
                    # Extract section (rough approximation)
                    start = match.start()
                    # Find next source or end
                    next_start = len(compiled_text)
                    for other_id in source_ids:
                        if other_id != source_id and other_id in source_markers:
                            other_match = re.search(source_markers[other_id], compiled_text[start+100:], re.I)
                            if other_match:
                                next_start = min(next_start, start + 100 + other_match.start())
                    
                    section_text = compiled_text[start:next_start]
                    cleaned = self.clean_text(section_text)
                    if cleaned and len(cleaned) > 100:
                        sources_content[source_id] = cleaned
        
        # If we couldn't split, return as single source
        if not sources_content:
            cleaned = self.clean_text(compiled_text)
            if cleaned:
                sources_content['compiled'] = cleaned
        
        return sources_content
    
    def structure_fund_data(self, fund_data):
        """Structure fund data with source attribution"""
        structured = {
            'fund_name': fund_data['fund_name'],
            'scheme_tag': fund_data['scheme_tag'],
            'last_updated': fund_data.get('last_updated', datetime.now().isoformat()),
            'sources': []
        }
        
        # Get source IDs
        source_ids = fund_data.get('data_sources', [])
        compiled_text = fund_data.get('compiled_text', '')
        
        # Try to split by source
        sources_content = self.split_by_source(compiled_text, source_ids)
        
        # If splitting failed, use the whole text as one source
        if not sources_content or len(sources_content) == 1:
            cleaned_text = self.clean_text(compiled_text)
            if cleaned_text:
                structured['sources'].append({
                    'source_id': 'compiled',
                    'source_title': 'Compiled from all sources',
                    'source_type': 'compiled',
                    'url': '',
                    'content': cleaned_text,
                    'length': len(cleaned_text),
                    'extracted_metrics': self.extract_key_metrics(cleaned_text)
                })
        else:
            # Add each source separately
            for source_id, content in sources_content.items():
                if source_id in self.source_metadata:
                    metadata = self.source_metadata[source_id]
                    structured['sources'].append({
                        'source_id': source_id,
                        'source_title': metadata['title'],
                        'source_type': metadata['type'],
                        'url': metadata['url'],
                        'authority': metadata['authority'],
                        'content': content,
                        'length': len(content),
                        'extracted_metrics': self.extract_key_metrics(content)
                    })
                else:
                    structured['sources'].append({
                        'source_id': source_id,
                        'source_title': f'Source: {source_id}',
                        'source_type': 'unknown',
                        'url': '',
                        'content': content,
                        'length': len(content),
                        'extracted_metrics': self.extract_key_metrics(content)
                    })
        
        # Add structured data fields
        structured_data = fund_data.get('structured_data', {})
        structured['key_information'] = {}
        
        # Clean and add structured fields
        for key in ['investment_objective', 'asset_allocation', 'exit_load', 'risk_factors']:
            if key in structured_data and structured_data[key]:
                value = str(structured_data[key]).strip()
                cleaned_value = self.clean_text(value)
                if cleaned_value and len(cleaned_value) > 10:
                    structured['key_information'][key] = cleaned_value
        
        # Add metrics from structured_data
        for key in ['nav', 'aum', 'expense_ratio', 'riskometer', 'fund_manager']:
            if key in structured_data and structured_data[key]:
                value = str(structured_data[key]).strip()
                if value and len(value) > 2 and value not in [',', 'AUM', 'Riskometer', 'under Regulation 52 (6):']:
                    cleaned_value = self.clean_text(value)
                    if cleaned_value:
                        structured['key_information'][key] = cleaned_value
        
        return structured
    
    def structure_regulatory_data(self, reg_data):
        """Structure regulatory/help data with source attribution"""
        source_id = reg_data.get('source_id', 'unknown')
        metadata = self.source_metadata.get(source_id, {})
        
        structured = {
            'source_id': source_id,
            'title': reg_data.get('source_title') or metadata.get('title', 'Unknown'),
            'authority': reg_data.get('authority') or metadata.get('authority', 'Unknown'),
            'url': reg_data.get('source_url') or metadata.get('url', ''),
            'type': reg_data.get('source_type') or metadata.get('type', 'unknown'),
            'fetched_at': reg_data.get('fetched_at', datetime.now().isoformat())
        }
        
        content = reg_data.get('content', {})
        if content and 'text' in content:
            cleaned_text = self.clean_text(content['text'])
            structured['content'] = cleaned_text
            structured['content_length'] = len(cleaned_text)
            structured['extracted_metrics'] = self.extract_key_metrics(cleaned_text)
        else:
            structured['content'] = ''
            structured['content_length'] = 0
            structured['extracted_metrics'] = {}
        
        return structured
    
    def clean_all_data(self):
        """Clean and structure all data"""
        print("="*80)
        print("CLEANING AND STRUCTURING DATA")
        print("="*80)
        print("\nLoading data...")
        
        # Load fund data
        with open('comprehensive_fund_dataset.json', 'r', encoding='utf-8') as f:
            fund_data = json.load(f)
        
        # Load regulatory data
        with open('regulatory_knowledge_base.json', 'r', encoding='utf-8') as f:
            regulatory_data = json.load(f)
        
        cleaned_kb = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'version': '2.0',
                'description': 'Cleaned and structured knowledge base with source attribution'
            },
            'funds': {},
            'regulatory': {},
            'help': {}
        }
        
        # Clean fund data
        print("\nCleaning fund data...")
        for fund in fund_data:
            tag = fund['scheme_tag']
            print(f"  Processing {tag} ({fund['fund_name']})...")
            cleaned_fund = self.structure_fund_data(fund)
            cleaned_kb['funds'][tag] = cleaned_fund
            print(f"    - {len(cleaned_fund['sources'])} sources with attribution")
            print(f"    - Total content: {sum(s['length'] for s in cleaned_fund['sources']):,} chars")
            print(f"    - Key information fields: {len(cleaned_fund['key_information'])}")
        
        # Clean regulatory data
        print("\nCleaning regulatory data...")
        for source_id, reg_data in regulatory_data.items():
            if reg_data.get('source_type') == 'regulatory':
                print(f"  Processing {source_id}...")
                cleaned_reg = self.structure_regulatory_data(reg_data)
                cleaned_kb['regulatory'][source_id] = cleaned_reg
                print(f"    - Content: {cleaned_reg['content_length']:,} chars")
        
        # Clean help data
        print("\nCleaning help data...")
        for source_id, help_data in regulatory_data.items():
            if help_data.get('source_type') == 'help_page':
                print(f"  Processing {source_id}...")
                cleaned_help = self.structure_regulatory_data(help_data)
                cleaned_kb['help'][source_id] = cleaned_help
                print(f"    - Content: {cleaned_help['content_length']:,} chars")
        
        # Save cleaned knowledge base
        print("\nSaving cleaned knowledge base...")
        with open('cleaned_knowledge_base.json', 'w', encoding='utf-8') as f:
            json.dump(cleaned_kb, f, indent=2, ensure_ascii=False)
        
        print("✓ Saved cleaned_knowledge_base.json")
        
        # Create summary
        total_fund_content = sum(
            sum(s['length'] for s in fund['sources'])
            for fund in cleaned_kb['funds'].values()
        )
        total_reg_content = sum(reg['content_length'] for reg in cleaned_kb['regulatory'].values())
        total_help_content = sum(help['content_length'] for help in cleaned_kb['help'].values())
        
        print("\n" + "="*80)
        print("CLEANING SUMMARY")
        print("="*80)
        print(f"Funds: {len(cleaned_kb['funds'])}")
        print(f"  Total fund content: {total_fund_content:,} characters")
        print(f"  Total sources: {sum(len(f['sources']) for f in cleaned_kb['funds'].values())}")
        print(f"Regulatory sources: {len(cleaned_kb['regulatory'])}")
        print(f"  Total regulatory content: {total_reg_content:,} characters")
        print(f"Help pages: {len(cleaned_kb['help'])}")
        print(f"  Total help content: {total_help_content:,} characters")
        print(f"\nTotal cleaned content: {total_fund_content + total_reg_content + total_help_content:,} characters")
        print(f"\n✓ All data cleaned and structured with source attribution!")

def main():
    cleaner = DataCleaner()
    cleaner.clean_all_data()

if __name__ == '__main__':
    main()
