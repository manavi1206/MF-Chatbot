#!/usr/bin/env python3
"""
RAG System Setup
Loads knowledge base, creates document chunks, generates embeddings, and builds vector store
"""

import json
import os
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import re

class RAGSystem:
    def __init__(self, knowledge_base_path='data/cleaned_knowledge_base.json', vector_store_path='./chroma_db'):
        # Support both old and new paths for backward compatibility
        if not os.path.exists(knowledge_base_path) and os.path.exists('cleaned_knowledge_base.json'):
            knowledge_base_path = 'cleaned_knowledge_base.json'
        self.knowledge_base_path = knowledge_base_path
        self.vector_store_path = vector_store_path
        self.embedding_model = None
        self.vector_store = None
        self.collection = None
        
    def load_knowledge_base(self) -> Dict[str, Any]:
        """Load and parse cleaned_knowledge_base.json"""
        print("Loading knowledge base...")
        with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
            kb = json.load(f)
        print(f"✓ Loaded knowledge base with {len(kb.get('funds', {}))} funds")
        return kb
    
    def chunk_documents(self, text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
        """Split content into chunks with overlap"""
        if not text or len(text.strip()) < chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < text_length:
                # Look for sentence endings
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size * 0.5:  # If we found a good break point
                    chunk = text[start:start + break_point + 1]
                    start = start + break_point + 1 - overlap
                else:
                    start = end - overlap
            else:
                start = end
            
            if chunk.strip():
                chunks.append(chunk.strip())
        
        return chunks
    
    def prepare_documents(self, kb: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prepare all documents from knowledge base for chunking"""
        documents = []
        
        # Process fund schemes (new consolidated structure)
        for fund_tag, fund_data in kb.get('funds', {}).items():
            fund_name = fund_data.get('fund_name', '')
            content = fund_data.get('content', '')
            metrics = fund_data.get('metrics', {})
            sources = fund_data.get('sources', [])
            
            if not content or len(content.strip()) < 50:
                continue
            
            # Chunk the consolidated content
            chunks = self.chunk_documents(content)
            
            # Prepare metrics text
            metrics_text = ""
            has_expense_ratio = 'expense_ratio' in metrics
            if metrics:
                metrics_parts = []
                if 'expense_ratio' in metrics and metrics['expense_ratio']:
                    metrics_parts.append(f"Total Expense Ratio (TER): {metrics['expense_ratio']}")
                if 'nav' in metrics and metrics['nav'] and metrics['nav'] != ',':
                    metrics_parts.append(f"NAV: {metrics['nav']}")
                if 'aum' in metrics and metrics['aum']:
                    metrics_parts.append(f"AUM: {metrics['aum']}")
                if 'benchmark' in metrics and metrics['benchmark'] and metrics['benchmark'] != 'Riskometer':
                    metrics_parts.append(f"Benchmark: {metrics['benchmark']}")
                if metrics_parts:
                    metrics_text = "\n\nKey Metrics: " + " | ".join(metrics_parts) + "\n"
            
            # Get primary source (first source with URL, or factsheet)
            primary_source = None
            for source in sources:
                if source.get('url') or source.get('source_id') == 'factsheet':
                    primary_source = source
                    break
            if not primary_source and sources:
                primary_source = sources[0]
            
            for idx, chunk in enumerate(chunks):
                chunk_text = chunk
                # Add metrics to ALL chunks if expense_ratio exists
                if has_expense_ratio and metrics_text and 'Key Metrics' not in chunk:
                    chunk_text = metrics_text + chunk
                # Otherwise, add to first chunk only
                elif idx == 0 and metrics_text:
                    chunk_text = metrics_text + chunk
                
                documents.append({
                    'text': chunk_text,
                    'metadata': {
                        'source_id': primary_source.get('source_id', 'unknown') if primary_source else 'unknown',
                        'source_title': primary_source.get('source_title', fund_name) if primary_source else fund_name,
                        'source_type': primary_source.get('source_type', 'consolidated') if primary_source else 'consolidated',
                        'url': primary_source.get('url', '') if primary_source else '',
                        'authority': primary_source.get('authority', 'AMC') if primary_source else 'AMC',
                        'fund_name': fund_name,
                        'fund_tag': fund_tag,
                        'chunk_index': idx,
                        'total_chunks': len(chunks),
                        'all_sources': ', '.join([s.get('source_id', '') for s in sources])  # Track all sources as string
                    }
                })
        
        # Process regulatory sources
        for source_id, reg_data in kb.get('regulatory', {}).items():
            content = reg_data.get('content', '')
            if not content or len(content.strip()) < 50:
                continue
            
            chunks = self.chunk_documents(content)
            
            for idx, chunk in enumerate(chunks):
                documents.append({
                    'text': chunk,
                    'metadata': {
                        'source_id': source_id,
                        'source_title': reg_data.get('title', ''),
                        'source_type': reg_data.get('type', 'regulatory'),
                        'url': reg_data.get('url', ''),
                        'authority': reg_data.get('authority', ''),
                        'fund_name': '',
                        'fund_tag': 'REGULATORY',
                        'chunk_index': idx,
                        'total_chunks': len(chunks)
                    }
                })
        
        # Process help sources
        for source_id, help_data in kb.get('help', {}).items():
            content = help_data.get('content', '')
            if not content or len(content.strip()) < 50:
                continue
            
            chunks = self.chunk_documents(content)
            
            for idx, chunk in enumerate(chunks):
                documents.append({
                    'text': chunk,
                    'metadata': {
                        'source_id': source_id,
                        'source_title': help_data.get('title', ''),
                        'source_type': help_data.get('type', 'help_page'),
                        'url': help_data.get('url', ''),
                        'authority': help_data.get('authority', ''),
                        'fund_name': '',
                        'fund_tag': 'HELP',
                        'chunk_index': idx,
                        'total_chunks': len(chunks)
                    }
                })
        
        print(f"✓ Prepared {len(documents)} document chunks")
        return documents
    
    def create_vector_store(self, force_recreate=False):
        """Create vector store with embeddings"""
        print("Creating vector store...")
        
        # Initialize embedding model
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✓ Embedding model loaded")
        
        # Initialize ChromaDB
        client = chromadb.PersistentClient(path=self.vector_store_path)
        
        # Create or get collection
        collection_name = "mf_knowledge_base"
        if force_recreate:
            try:
                client.delete_collection(collection_name)
            except:
                pass
        
        self.collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "HDFC Mutual Fund Knowledge Base"}
        )
        
        # Load knowledge base and prepare documents
        kb = self.load_knowledge_base()
        documents = self.prepare_documents(kb)
        
        if not documents:
            print("⚠ No documents to process")
            return
        
        # Check if collection is empty or needs update
        if self.collection.count() == 0 or force_recreate:
            print(f"Generating embeddings for {len(documents)} chunks...")
            
            # Extract texts and metadata
            texts = [doc['text'] for doc in documents]
            metadatas = [doc['metadata'] for doc in documents]
            # Create unique IDs by including fund_tag to avoid duplicates
            ids = [f"{doc['metadata'].get('fund_tag', 'GENERAL')}_{doc['metadata']['source_id']}_chunk_{doc['metadata']['chunk_index']}" 
                   for doc in documents]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✓ Added {len(documents)} chunks to vector store")
        else:
            print(f"✓ Vector store already contains {self.collection.count()} chunks")
    
    def retrieve_relevant_chunks(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve top-k relevant chunks for a query"""
        if not self.collection:
            raise ValueError("Vector store not initialized. Call create_vector_store() first.")
        
        if not self.embedding_model:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Extract fund name from query to add as filter/boost
        query_lower = query.lower()
        fund_filter = None
        
        # Map fund mentions to tags
        fund_mapping = {
            'large cap': 'LARGE_CAP',
            'flexi cap': 'FLEXI_CAP',
            'flexicap': 'FLEXI_CAP',
            'elss': 'ELSS',
            'taxsaver': 'ELSS',
            'tax saver': 'ELSS',
            'hybrid': 'HYBRID'
        }
        
        # Check which fund is mentioned
        for fund_key, fund_tag in fund_mapping.items():
            if fund_key in query_lower:
                fund_filter = fund_tag
                break
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Query the collection with more results if we have a fund filter
        n_results = k * 3 if fund_filter else k
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results
        )
        
        # Parse results
        all_chunks = []
        if results['documents'] and len(results['documents'][0]) > 0:
            for i in range(len(results['documents'][0])):
                chunk = {
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                }
                all_chunks.append(chunk)
        
        # If we have a fund filter, strongly prioritize chunks from that fund
        if fund_filter and all_chunks:
            # Separate chunks by type
            fund_specific = [c for c in all_chunks if c['metadata'].get('fund_tag') == fund_filter]
            regulatory = [c for c in all_chunks if c['metadata'].get('fund_tag') == 'REGULATORY']
            help_docs = [c for c in all_chunks if c['metadata'].get('fund_tag') == 'HELP']
            other = [c for c in all_chunks if c['metadata'].get('fund_tag') not in [fund_filter, 'REGULATORY', 'HELP']]
            
            # Prioritize: fund-specific first, then help docs, then other funds, then regulatory
            # Regulatory docs should be LAST because they contain generic definitions
            chunks = (fund_specific + help_docs + other + regulatory)[:k]
            
            print(f"Query fund filter: {fund_filter}, Found {len(fund_specific)} fund-specific, {len(regulatory)} regulatory chunks")
        else:
            # No specific fund - still prefer fund docs over regulatory
            fund_chunks = [c for c in all_chunks if c['metadata'].get('fund_tag') not in ['REGULATORY', 'HELP']]
            regulatory = [c for c in all_chunks if c['metadata'].get('fund_tag') == 'REGULATORY']
            help_docs = [c for c in all_chunks if c['metadata'].get('fund_tag') == 'HELP']
            
            chunks = (fund_chunks + help_docs + regulatory)[:k]
        
        return chunks
    
    def get_last_updated_date(self) -> str:
        """Get the last updated date from knowledge base metadata"""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                kb = json.load(f)
            created_at = kb.get('metadata', {}).get('created_at', '')
            if created_at:
                # Format date nicely
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    return dt.strftime('%B %d, %Y')
                except:
                    return created_at[:10] if len(created_at) >= 10 else created_at
            return "Unknown"
        except:
            return "Unknown"

def main():
    """Test the RAG system"""
    rag = RAGSystem()
    rag.create_vector_store(force_recreate=True)
    
    # Test retrieval
    print("\nTesting retrieval...")
    test_query = "What is the expense ratio of HDFC Large Cap Fund?"
    chunks = rag.retrieve_relevant_chunks(test_query, k=3)
    print(f"\nRetrieved {len(chunks)} chunks for query: '{test_query}'")
    for i, chunk in enumerate(chunks, 1):
        print(f"\nChunk {i}:")
        print(f"  Source: {chunk['metadata'].get('source_title', 'Unknown')}")
        print(f"  URL: {chunk['metadata'].get('url', 'N/A')[:60]}...")
        print(f"  Text preview: {chunk['text'][:100]}...")

if __name__ == '__main__':
    main()

