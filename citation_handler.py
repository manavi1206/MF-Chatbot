#!/usr/bin/env python3
"""
Citation Extraction and Formatting
Extracts source URLs from retrieved chunks and formats citations
"""

import csv
from typing import Dict, Any, Optional

class CitationHandler:
    def __init__(self, sources_csv_path='sources.csv'):
        self.sources_csv_path = sources_csv_path
        self.source_metadata = {}
        self._load_source_metadata()
    
    def _load_source_metadata(self):
        """Load source metadata from CSV"""
        try:
            with open(self.sources_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.source_metadata[row['source_id']] = {
                        'title': row['source_title'],
                        'url': row['source_url'],
                        'type': row['source_type'],
                        'authority': row['authority']
                    }
        except FileNotFoundError:
            print(f"Warning: {self.sources_csv_path} not found. Citation validation will be limited.")
    
    def extract_citation(self, chunk_metadata: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Extract citation information from chunk metadata"""
        source_id = chunk_metadata.get('source_id', '')
        url = chunk_metadata.get('url', '')
        title = chunk_metadata.get('source_title', '')
        
        # If we have source_id, try to get metadata from CSV
        if source_id and source_id in self.source_metadata:
            metadata = self.source_metadata[source_id]
            url = url or metadata.get('url', '')
            title = title or metadata.get('title', '')
        
        # Fallback: use metadata directly if available
        if not title:
            title = chunk_metadata.get('source_title', 'Unknown Source')
        
        if not url:
            url = chunk_metadata.get('url', '')
        
        if not url:
            return None
        
        return {
            'url': url,
            'title': title
        }
    
    def format_citation(self, url: str, title: str) -> str:
        """Format citation as markdown link"""
        if not url or not title:
            return ""
        return f"[{title}]({url})"
    
    def validate_source(self, url: str) -> bool:
        """Validate that URL exists in sources.csv"""
        if not url:
            return False
        
        # Check if URL exists in any source metadata
        for source_id, metadata in self.source_metadata.items():
            if metadata.get('url', '') == url:
                return True
        
        return False
    
    def get_citation_from_chunk(self, chunk_metadata: Dict[str, Any]) -> str:
        """Get formatted citation from chunk metadata"""
        citation_info = self.extract_citation(chunk_metadata)
        if not citation_info:
            return "Source: [Not available]"
        
        return self.format_citation(citation_info['url'], citation_info['title'])

