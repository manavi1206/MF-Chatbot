#!/usr/bin/env python3
"""
Test 20 queries across different categories
Tests: fund-related, knowledge, help, miscellaneous, advice, greetings
"""

import os
import sys
from dotenv import load_dotenv
from faq_assistant import FAQAssistant
from rag_system import RAGSystem

# Load environment variables
load_dotenv()

# Test queries organized by category
test_queries = {
    "Fund-Related (Factual)": [
        "What is the expense ratio of HDFC Large Cap Fund?",
        "What is the exit load for HDFC Flexi Cap Fund?",
        "What is the benchmark for HDFC TaxSaver (ELSS)?",
        "What is the AUM of HDFC Hybrid Equity Fund?",
        "Who is the fund manager of HDFC Large Cap Fund?",
        "What is the lock-in period for ELSS funds?",
        "What is the minimum investment amount for HDFC Flexi Cap Fund?",
    ],
    "Knowledge (General MF)": [
        "What is a mutual fund?",
        "What is NAV?",
        "What is expense ratio?",
        "What is the difference between direct and regular plans?",
    ],
    "Help (How-to)": [
        "How to download CAS statement?",
        "How to invest in mutual funds?",
        "How to redeem mutual fund units?",
    ],
    "Miscellaneous (Out of Context)": [
        "What is the capital of India?",
        "What is your favorite sport?",
        "Tell me a joke",
    ],
    "Advice (Should be Refused)": [
        "Should I invest in HDFC Large Cap Fund?",
        "Is HDFC Flexi Cap Fund good for me?",
        "Which fund should I buy?",
    ],
    "Greetings": [
        "Hello",
        "Hi there",
    ]
}

def test_query(assistant, query, category):
    """Test a single query and return the result"""
    print(f"\n{'='*80}")
    print(f"Category: {category}")
    print(f"Query: {query}")
    print(f"{'='*80}")
    
    try:
        # Get answer using the assistant
        answer, source = assistant.process_query(query, [])
        
        print(f"Answer: {answer}")
        if source:
            print(f"Source: {source}")
        return {
            'query': query,
            'category': category,
            'answer': answer,
            'source': source,
            'status': 'success'
        }
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'query': query,
            'category': category,
            'answer': f"Error: {str(e)}",
            'status': 'error'
        }

def main():
    print("="*80)
    print("TESTING 20 QUERIES ACROSS ALL CATEGORIES")
    print("="*80)
    
    # Initialize assistant
    print("\nInitializing FAQ Assistant...")
    try:
        # Use Ollama by default (no rate limits)
        model_type = os.getenv('LLM_MODEL_TYPE', 'ollama')
        model_name = os.getenv('LLM_MODEL_NAME', 'llama3.1:8b')
        api_key = os.getenv('GEMINI_API_KEY') if model_type == 'gemini' else None
        
        assistant = FAQAssistant(model_type=model_type, model_name=model_name, api_key=api_key)
        print("✓ FAQ Assistant initialized")
        
        # Initialize RAG system
        rag = RAGSystem()
        rag.create_vector_store(force_recreate=False)
        print("✓ RAG system initialized\n")
    except Exception as e:
        print(f"❌ Error initializing: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test all queries
    results = []
    total_queries = sum(len(queries) for queries in test_queries.values())
    current = 0
    
    for category, queries in test_queries.items():
        for query in queries:
            current += 1
            print(f"\n[{current}/{total_queries}] ", end="")
            result = test_query(assistant, query, category)
            results.append(result)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    by_category = {}
    for result in results:
        category = result['category']
        if category not in by_category:
            by_category[category] = {'total': 0, 'success': 0, 'error': 0}
        by_category[category]['total'] += 1
        if result['status'] == 'success':
            by_category[category]['success'] += 1
        else:
            by_category[category]['error'] += 1
    
    for category, stats in by_category.items():
        print(f"\n{category}:")
        print(f"  Total: {stats['total']}")
        print(f"  Success: {stats['success']}")
        print(f"  Errors: {stats['error']}")
    
    print(f"\n{'='*80}")
    print(f"Total Queries: {total_queries}")
    print(f"Successful: {sum(s['success'] for s in by_category.values())}")
    print(f"Errors: {sum(s['error'] for s in by_category.values())}")
    print("="*80)
    
    # Save results to file
    import json
    with open('test_query_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Results saved to test_query_results.json")

if __name__ == '__main__':
    main()

