#!/usr/bin/env python3
"""
Fetch and store regulatory and help sources
These will be used for general knowledge base queries
"""

import csv
import json
import requests
from bs4 import BeautifulSoup
import pdfplumber
from datetime import datetime
import time
import re
import os

class RegulatorySourceFetcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.regulatory_data = {}
        
    def read_sources_csv(self):
        """Read the sources CSV file"""
        sources = []
        with open('sources.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Only process regulatory and help sources (not fund-specific)
                if row['scheme_tag'] == 'ALL' and row['source_type'] in ['regulatory', 'help_page', 'factsheet_consolidated']:
                    sources.append(row)
        return sources
    
    def fetch_webpage(self, url, max_retries=3):
        """Fetch webpage content"""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                return response.text
            except Exception as e:
                print(f"Error fetching {url} (attempt {attempt+1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return None
        return None
    
    def extract_pdf_text(self, url):
        """Download and extract text from PDF"""
        try:
            response = requests.get(url, headers=self.headers, timeout=60)
            response.raise_for_status()
            
            # Save temporarily
            with open('temp_regulatory_pdf.pdf', 'wb') as f:
                f.write(response.content)
            
            # Extract text
            text = ""
            with pdfplumber.open('temp_regulatory_pdf.pdf') as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            os.remove('temp_regulatory_pdf.pdf')
            return text
        except Exception as e:
            print(f"Error extracting PDF {url}: {e}")
            if os.path.exists('temp_regulatory_pdf.pdf'):
                os.remove('temp_regulatory_pdf.pdf')
            return None
    
    def parse_webpage(self, html, source_id):
        """Extract content from webpage"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get main content
        text = soup.get_text(separator='\n', strip=True)
        
        # Try to find main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|article', re.I))
        
        if main_content:
            main_text = main_content.get_text(separator='\n', strip=True)
            if len(main_text) > 500:  # If main content is substantial, use it
                text = main_text
        
        return {
            'raw_html': html,
            'extracted_text': text,
            'title': soup.title.string if soup.title else None
        }
    
    def fetch_all_regulatory_sources(self):
        """Fetch all regulatory and help sources"""
        sources = self.read_sources_csv()
        
        print("="*80)
        print("FETCHING REGULATORY & HELP SOURCES")
        print("="*80)
        print(f"Total sources to process: {len(sources)}\n")
        
        for idx, source in enumerate(sources, 1):
            source_id = source['source_id']
            source_type = source['source_type']
            url = source['source_url']
            title = source['source_title']
            authority = source['authority']
            
            print(f"[{idx}/{len(sources)}] Processing: {source_id}")
            print(f"  Type: {source_type} | Authority: {authority}")
            
            data = {
                'source_id': source_id,
                'source_title': title,
                'source_url': url,
                'source_type': source_type,
                'authority': authority,
                'scheme_tag': source['scheme_tag'],
                'fetched_at': datetime.now().isoformat()
            }
            
            if source_type == 'factsheet_consolidated':
                # Already processed, skip or mark as processed
                print(f"  ⚠ Factshet already processed in fund datasets")
                data['status'] = 'already_processed'
                data['note'] = 'Data extracted and integrated into fund datasets'
            elif source_type == 'regulatory':
                if url.endswith('.pdf'):
                    # PDF source
                    pdf_text = self.extract_pdf_text(url)
                    if pdf_text:
                        data['content'] = {
                            'type': 'pdf',
                            'text': pdf_text,
                            'length': len(pdf_text)
                        }
                        print(f"  ✓ Extracted PDF ({len(pdf_text)} chars)")
                    else:
                        data['status'] = 'failed'
                        print(f"  ✗ Failed to extract PDF")
                else:
                    # Web page
                    html = self.fetch_webpage(url)
                    if html:
                        parsed = self.parse_webpage(html, source_id)
                        data['content'] = {
                            'type': 'webpage',
                            'text': parsed['extracted_text'],
                            'title': parsed['title'],
                            'length': len(parsed['extracted_text'])
                        }
                        print(f"  ✓ Fetched webpage ({len(parsed['extracted_text'])} chars)")
                    else:
                        data['status'] = 'failed'
                        print(f"  ✗ Failed to fetch webpage")
            elif source_type == 'help_page':
                # Help page
                html = self.fetch_webpage(url)
                if html:
                    parsed = self.parse_webpage(html, source_id)
                    data['content'] = {
                        'type': 'webpage',
                        'text': parsed['extracted_text'],
                        'title': parsed['title'],
                        'length': len(parsed['extracted_text'])
                    }
                    print(f"  ✓ Fetched help page ({len(parsed['extracted_text'])} chars)")
                else:
                    data['status'] = 'failed'
                    print(f"  ✗ Failed to fetch help page")
            
            self.regulatory_data[source_id] = data
            time.sleep(1)  # Be respectful with requests
        
        print("\n" + "="*80)
        print("FETCH COMPLETE")
        print("="*80)
    
    def save_regulatory_data(self):
        """Save regulatory data to JSON file"""
        filename = 'regulatory_knowledge_base.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.regulatory_data, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Saved regulatory data to {filename}")
        
        # Also create a summary
        summary = {
            'total_sources': len(self.regulatory_data),
            'by_type': {},
            'by_authority': {},
            'sources': []
        }
        
        for source_id, data in self.regulatory_data.items():
            source_type = data.get('source_type', 'unknown')
            authority = data.get('authority', 'unknown')
            
            summary['by_type'][source_type] = summary['by_type'].get(source_type, 0) + 1
            summary['by_authority'][authority] = summary['by_authority'].get(authority, 0) + 1
            
            summary['sources'].append({
                'source_id': source_id,
                'title': data.get('source_title'),
                'type': source_type,
                'authority': authority,
                'has_content': 'content' in data,
                'content_length': data.get('content', {}).get('length', 0) if 'content' in data else 0
            })
        
        summary_filename = 'regulatory_knowledge_base_summary.json'
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved summary to {summary_filename}")
        
        # Print summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total sources: {summary['total_sources']}")
        print(f"\nBy Type:")
        for source_type, count in summary['by_type'].items():
            print(f"  {source_type}: {count}")
        print(f"\nBy Authority:")
        for authority, count in summary['by_authority'].items():
            print(f"  {authority}: {count}")
        
        successful = sum(1 for s in summary['sources'] if s['has_content'])
        print(f"\nSuccessfully fetched: {successful}/{summary['total_sources']}")

def main():
    fetcher = RegulatorySourceFetcher()
    fetcher.fetch_all_regulatory_sources()
    fetcher.save_regulatory_data()

if __name__ == '__main__':
    main()

