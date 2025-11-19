#!/usr/bin/env python3
"""
Quick test - 5 key queries to verify everything works
"""

import os
import sys
from dotenv import load_dotenv
from faq_assistant import FAQAssistant
from rag_system import RAGSystem

load_dotenv()

# Quick test queries
quick_tests = [
    "What is the expense ratio of HDFC Large Cap Fund?",
    "What is the ELSS lock-in period?",
    "What is NAV?",
    "Should I invest in HDFC Large Cap Fund?",  # Should refuse
    "Hello"  # Greeting
]

def quick_test():
    print("="*60)
    print("QUICK TEST - 5 Queries")
    print("="*60)
    
    # Initialize
    print("\n1. Initializing FAQ Assistant...")
    try:
        assistant = FAQAssistant(model_type='ollama', model_name='llama3.1:8b')
        print("   ✓ FAQ Assistant initialized")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    print("\n2. Initializing RAG system...")
    try:
        rag = RAGSystem()
        rag.create_vector_store(force_recreate=False)
        print("   ✓ RAG system initialized")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test queries
    print("\n3. Testing queries...")
    results = []
    for i, query in enumerate(quick_tests, 1):
        print(f"\n   [{i}/5] {query[:50]}...")
        try:
            answer, source = assistant.process_query(query, [])
            print(f"   ✓ Success")
            results.append(True)
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "="*60)
    print("QUICK TEST SUMMARY")
    print("="*60)
    print(f"Passed: {sum(results)}/5")
    print(f"Failed: {5 - sum(results)}/5")
    
    if all(results):
        print("\n✅ ALL TESTS PASSED - Ready to deploy!")
        return True
    else:
        print("\n⚠️  Some tests failed - Check errors above")
        return False

if __name__ == '__main__':
    success = quick_test()
    sys.exit(0 if success else 1)

