#!/usr/bin/env python3
"""
Comprehensive Fund Data Fetcher
Fetches and compiles exhaustive dataset for all 4 HDFC Mutual Funds
"""

import csv
import json
import requests
from bs4 import BeautifulSoup
import pdfplumber
import pandas as pd
from datetime import datetime
import time
import re
from urllib.parse import urlparse

class FundDataFetcher:
    def __init__(self):
        self.funds_data = {
            'LARGE_CAP': {
                'fund_name': 'HDFC Large Cap Fund',
                'scheme_tag': 'LARGE_CAP',
                'sources': {}
            },
            'FLEXI_CAP': {
                'fund_name': 'HDFC Flexi Cap Fund',
                'scheme_tag': 'FLEXI_CAP',
                'sources': {}
            },
            'ELSS': {
                'fund_name': 'HDFC TaxSaver (ELSS)',
                'scheme_tag': 'ELSS',
                'sources': {}
            },
            'HYBRID': {
                'fund_name': 'HDFC Hybrid Equity Fund',
                'scheme_tag': 'HYBRID',
                'sources': {}
            }
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def read_sources_csv(self):
        """Read the sources CSV file"""
        sources = []
        with open('sources.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
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
            response = requests.get(url, headers=self.headers, timeout=60, stream=True)
            response.raise_for_status()
            
            # Save temporarily
            with open('temp_pdf.pdf', 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Extract text
            text = ""
            with pdfplumber.open('temp_pdf.pdf') as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            import os
            os.remove('temp_pdf.pdf')
            return text
        except Exception as e:
            print(f"Error extracting PDF {url}: {e}")
            return None
    
    def parse_overview_page(self, html, fund_tag):
        """Extract data from fund overview page"""
        soup = BeautifulSoup(html, 'html.parser')
        data = {}
        
        # Try to extract key metrics
        # This will vary based on actual page structure
        # Common elements to look for:
        
        # NAV
        nav_elements = soup.find_all(string=re.compile(r'NAV|Net Asset Value', re.I))
        if nav_elements:
            data['nav_info'] = nav_elements[0].strip() if nav_elements else None
        
        # Expense Ratio
        expense_elements = soup.find_all(string=re.compile(r'Expense Ratio|Total Expense Ratio', re.I))
        if expense_elements:
            data['expense_ratio_info'] = expense_elements[0].strip() if expense_elements else None
        
        # AUM
        aum_elements = soup.find_all(string=re.compile(r'AUM|Assets Under Management', re.I))
        if aum_elements:
            data['aum_info'] = aum_elements[0].strip() if aum_elements else None
        
        # Riskometer
        risk_elements = soup.find_all(string=re.compile(r'Riskometer|Risk Level', re.I))
        if risk_elements:
            data['riskometer_info'] = risk_elements[0].strip() if risk_elements else None
        
        # Performance data
        performance_elements = soup.find_all(string=re.compile(r'Returns|Performance|1 Year|3 Year|5 Year', re.I))
        if performance_elements:
            data['performance_info'] = [elem.strip() for elem in performance_elements[:10]]
        
        # Fund Manager
        manager_elements = soup.find_all(string=re.compile(r'Fund Manager|Manager', re.I))
        if manager_elements:
            data['fund_manager_info'] = manager_elements[0].strip() if manager_elements else None
        
        # Extract all text for comprehensive analysis
        data['full_text'] = soup.get_text(separator='\n', strip=True)
        
        # Extract structured data from tables
        tables = soup.find_all('table')
        if tables:
            data['tables'] = []
            for table in tables:
                rows = []
                for tr in table.find_all('tr'):
                    cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                    if cells:
                        rows.append(cells)
                if rows:
                    data['tables'].append(rows)
        
        return data
    
    def parse_sid_kim_pdf(self, pdf_text, doc_type):
        """Extract structured data from SID/KIM PDF"""
        data = {
            'document_type': doc_type,
            'raw_text': pdf_text,
            'extracted_info': {}
        }
        
        # Extract key sections
        sections = {
            'investment_objective': re.search(r'Investment Objective[:\s]*(.*?)(?=\n\n|\n[A-Z])', pdf_text, re.I | re.S),
            'asset_allocation': re.search(r'Asset Allocation[:\s]*(.*?)(?=\n\n|\n[A-Z])', pdf_text, re.I | re.S),
            'expense_ratio': re.search(r'Total Expense Ratio[:\s]*(.*?)(?=\n\n|\n[A-Z])', pdf_text, re.I | re.S),
            'exit_load': re.search(r'Exit Load[:\s]*(.*?)(?=\n\n|\n[A-Z])', pdf_text, re.I | re.S),
            'minimum_investment': re.search(r'Minimum Investment[:\s]*(.*?)(?=\n\n|\n[A-Z])', pdf_text, re.I | re.S),
            'fund_manager': re.search(r'Fund Manager[:\s]*(.*?)(?=\n\n|\n[A-Z])', pdf_text, re.I | re.S),
            'risk_factors': re.search(r'Risk Factors[:\s]*(.*?)(?=\n\n|\n[A-Z])', pdf_text, re.I | re.S),
        }
        
        for key, match in sections.items():
            if match:
                data['extracted_info'][key] = match.group(1).strip()[:500]  # Limit length
        
        # Extract numbers (NAV, AUM, etc.)
        nav_match = re.search(r'NAV[:\s]*₹?\s*([\d,]+\.?\d*)', pdf_text, re.I)
        if nav_match:
            data['extracted_info']['nav'] = nav_match.group(1)
        
        aum_match = re.search(r'AUM[:\s]*₹?\s*([\d,]+\.?\d*)\s*(Crore|Cr|Lakh|L)', pdf_text, re.I)
        if aum_match:
            data['extracted_info']['aum'] = aum_match.group(1) + ' ' + aum_match.group(2)
        
        return data
    
    def parse_factsheet(self, pdf_text):
        """Extract data from consolidated factsheet for all funds"""
        data = {}
        
        # Split by fund names
        fund_patterns = {
            'LARGE_CAP': r'HDFC Large Cap Fund|Large Cap',
            'FLEXI_CAP': r'HDFC Flexi Cap Fund|Flexi Cap',
            'ELSS': r'HDFC TaxSaver|ELSS|Tax Saver',
            'HYBRID': r'HDFC Hybrid Equity Fund|Hybrid Equity'
        }
        
        for fund_tag, pattern in fund_patterns.items():
            match = re.search(pattern, pdf_text, re.I)
            if match:
                # Extract section for this fund
                start = match.start()
                end = min(start + 5000, len(pdf_text))  # Next 5000 chars
                fund_section = pdf_text[start:end]
                
                # Extract key metrics
                fund_data = {}
                
                # NAV
                nav_match = re.search(r'NAV[:\s]*₹?\s*([\d,]+\.?\d*)', fund_section, re.I)
                if nav_match:
                    fund_data['nav'] = nav_match.group(1)
                
                # AUM
                aum_match = re.search(r'AUM[:\s]*₹?\s*([\d,]+\.?\d*)\s*(Crore|Cr)', fund_section, re.I)
                if aum_match:
                    fund_data['aum'] = aum_match.group(1) + ' ' + aum_match.group(2)
                
                # Returns
                returns_match = re.findall(r'(\d+\.\d+)%', fund_section)
                if returns_match:
                    fund_data['returns'] = returns_match[:10]  # First 10 return values
                
                data[fund_tag] = fund_data
        
        return data
    
    def fetch_all_data(self):
        """Main method to fetch all data"""
        sources = self.read_sources_csv()
        
        print("Starting comprehensive data fetch...")
        print(f"Total sources to process: {len(sources)}\n")
        
        for idx, source in enumerate(sources, 1):
            source_type = source['source_type']
            scheme_tag = source['scheme_tag']
            url = source['source_url']
            source_id = source['source_id']
            
            print(f"[{idx}/{len(sources)}] Processing: {source_id} ({source_type})")
            
            if scheme_tag in ['LARGE_CAP', 'FLEXI_CAP', 'ELSS', 'HYBRID']:
                if scheme_tag not in self.funds_data:
                    continue
                
                if source_type == 'scheme_overview':
                    html = self.fetch_webpage(url)
                    if html:
                        data = self.parse_overview_page(html, scheme_tag)
                        self.funds_data[scheme_tag]['sources'][source_id] = {
                            'type': source_type,
                            'url': url,
                            'data': data,
                            'fetched_at': datetime.now().isoformat()
                        }
                        print(f"  ✓ Fetched overview page")
                
                elif source_type in ['sid_pdf', 'kim_pdf']:
                    pdf_text = self.extract_pdf_text(url)
                    if pdf_text:
                        data = self.parse_sid_kim_pdf(pdf_text, source_type)
                        self.funds_data[scheme_tag]['sources'][source_id] = {
                            'type': source_type,
                            'url': url,
                            'data': data,
                            'fetched_at': datetime.now().isoformat()
                        }
                        print(f"  ✓ Extracted PDF data ({len(pdf_text)} chars)")
            
            elif source_type == 'factsheet_consolidated':
                pdf_text = self.extract_pdf_text(url)
                if pdf_text:
                    data = self.parse_factsheet(pdf_text)
                    for fund_tag in self.funds_data.keys():
                        if fund_tag in data:
                            if 'factsheet' not in self.funds_data[fund_tag]['sources']:
                                self.funds_data[fund_tag]['sources']['factsheet'] = {
                                    'type': source_type,
                                    'url': url,
                                    'data': data[fund_tag],
                                    'fetched_at': datetime.now().isoformat()
                                }
                    print(f"  ✓ Extracted factsheet data")
            
            time.sleep(1)  # Be respectful with requests
        
        print("\n✓ Data fetch completed!")
    
    def compile_comprehensive_dataset(self):
        """Compile all data into comprehensive dataset"""
        comprehensive_data = []
        
        for fund_tag, fund_info in self.funds_data.items():
            fund_record = {
                'fund_name': fund_info['fund_name'],
                'scheme_tag': fund_info['scheme_tag'],
                'data_sources': list(fund_info['sources'].keys()),
            }
            
            # Compile all extracted information
            all_text = []
            structured_data = {}
            
            for source_id, source_data in fund_info['sources'].items():
                data = source_data['data']
                
                if source_data['type'] == 'scheme_overview':
                    if 'full_text' in data:
                        all_text.append(data['full_text'])
                    # Add structured fields
                    for key in ['nav_info', 'expense_ratio_info', 'aum_info', 'riskometer_info', 'fund_manager_info']:
                        if key in data and data[key]:
                            structured_data[key.replace('_info', '')] = data[key]
                    if 'performance_info' in data:
                        structured_data['performance_indicators'] = data['performance_info']
                
                elif source_data['type'] in ['sid_pdf', 'kim_pdf']:
                    if 'raw_text' in data:
                        all_text.append(data['raw_text'])
                    if 'extracted_info' in data:
                        structured_data.update(data['extracted_info'])
                
                elif source_data['type'] == 'factsheet_consolidated':
                    if isinstance(data, dict):
                        structured_data.update(data)
            
            fund_record['compiled_text'] = '\n\n---\n\n'.join(all_text)
            fund_record['structured_data'] = structured_data
            fund_record['total_sources'] = len(fund_info['sources'])
            fund_record['last_updated'] = datetime.now().isoformat()
            
            comprehensive_data.append(fund_record)
        
        return comprehensive_data
    
    def save_dataset(self, data, format='json'):
        """Save comprehensive dataset"""
        if format == 'json':
            filename = 'comprehensive_fund_dataset.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n✓ Saved comprehensive dataset to {filename}")
        
        # Also save as CSV (flattened)
        csv_data = []
        for fund in data:
            row = {
                'fund_name': fund['fund_name'],
                'scheme_tag': fund['scheme_tag'],
                'total_sources': fund['total_sources'],
                'data_sources': ', '.join(fund['data_sources']),
            }
            # Add structured data fields
            for key, value in fund['structured_data'].items():
                if isinstance(value, (str, int, float)):
                    row[key] = value
                else:
                    row[key] = str(value)
            csv_data.append(row)
        
        df = pd.DataFrame(csv_data)
        csv_filename = 'comprehensive_fund_dataset.csv'
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        print(f"✓ Saved flattened dataset to {csv_filename}")
        
        # Save detailed text files for each fund
        for fund in data:
            filename = f"fund_data_{fund['scheme_tag']}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Fund: {fund['fund_name']}\n")
                f.write(f"Scheme Tag: {fund['scheme_tag']}\n")
                f.write(f"Total Sources: {fund['total_sources']}\n")
                f.write(f"Data Sources: {', '.join(fund['data_sources'])}\n")
                f.write(f"Last Updated: {fund['last_updated']}\n")
                f.write("\n" + "="*80 + "\n")
                f.write("STRUCTURED DATA:\n")
                f.write("="*80 + "\n")
                for key, value in fund['structured_data'].items():
                    f.write(f"\n{key.upper().replace('_', ' ')}:\n")
                    f.write(f"{value}\n")
                f.write("\n" + "="*80 + "\n")
                f.write("COMPILED TEXT FROM ALL SOURCES:\n")
                f.write("="*80 + "\n")
                f.write(fund['compiled_text'])
            print(f"✓ Saved detailed text file: {filename}")

def main():
    fetcher = FundDataFetcher()
    fetcher.fetch_all_data()
    comprehensive_data = fetcher.compile_comprehensive_dataset()
    fetcher.save_dataset(comprehensive_data)
    
    print("\n" + "="*80)
    print("COMPREHENSIVE DATASET SUMMARY")
    print("="*80)
    for fund in comprehensive_data:
        print(f"\n{fund['fund_name']} ({fund['scheme_tag']}):")
        print(f"  - Sources: {fund['total_sources']}")
        print(f"  - Data points extracted: {len(fund['structured_data'])}")
        print(f"  - Total text length: {len(fund['compiled_text'])} characters")

if __name__ == '__main__':
    main()

