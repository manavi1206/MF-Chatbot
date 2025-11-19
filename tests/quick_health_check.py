#!/usr/bin/env python3
"""
Quick Health Check - 10 Essential Tests
Run this to verify core functionality is working
"""

import os
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from faq_assistant import FAQAssistant

# Load environment variables
load_dotenv()

# Test queries with expected outcomes
QUICK_TESTS = [
    {
        "id": 1,
        "query": "hi",
        "expected_type": "greeting",
        "description": "Greeting response"
    },
    {
        "id": 2,
        "query": "what can i ask you",
        "expected_type": "coverage",
        "description": "Coverage/capability list",
        "should_contain": ["HDFC Large Cap", "HDFC Flexi Cap", "ELSS", "Hybrid"]
    },
    {
        "id": 3,
        "query": "What is the expense ratio of HDFC Large Cap Fund?",
        "expected_type": "factual",
        "description": "Factual query - expense ratio",
        "should_contain": ["0.96", "Large Cap"],
        "should_not_contain": ["AUM", "benchmark", "Flexi Cap"]
    },
    {
        "id": 4,
        "query": "minimum sip amount",
        "expected_type": "clarification",
        "description": "Ambiguous query needs clarification",
        "should_contain": ["Which fund", "HDFC Large Cap", "HDFC Flexi Cap", "ELSS", "Hybrid"]
    },
    {
        "id": 5,
        "query": "What is the ELSS lock-in period?",
        "expected_type": "factual",
        "description": "ELSS lock-in query",
        "should_contain": ["3 years", "three years"],
        "should_not_contain": ["Flexi Cap", "Large Cap"]
    },
    {
        "id": 6,
        "query": "Should I invest in HDFC Large Cap?",
        "expected_type": "advice",
        "description": "Advice query - should refuse",
        "should_contain": ["cannot give investment advice", "financial advisor"],
        "should_not_contain": ["expense ratio", "0.96"]
    },
    {
        "id": 7,
        "query": "Who is PM of India?",
        "expected_type": "out_of_context",
        "description": "Out-of-context query",
        "should_contain": ["mutual funds only"],
        "should_not_contain": ["Source:", "HDFC", "📄"]
    },
    {
        "id": 8,
        "query": "565665",
        "expected_type": "out_of_context",
        "description": "Meaningless query (random numbers)",
        "should_contain": ["mutual funds only"],
        "should_not_contain": ["Source:", "📄", "Karvy"]
    },
    {
        "id": 9,
        "query": "How to download CAS statement?",
        "expected_type": "factual",
        "description": "How-to query",
        "should_contain": ["CAS", "statement"],
    },
    {
        "id": 10,
        "query": "What is the expense ratio of Flexi Cap?",
        "expected_type": "factual",
        "description": "Flexi Cap query (NOT Large Cap)",
        "should_contain": ["Flexi Cap"],
        "should_not_contain": ["Large Cap Fund"]
    }
]

def run_health_check():
    """Run quick health check tests"""
    print("=" * 70)
    print("MF CHATBOT - QUICK HEALTH CHECK")
    print("=" * 70)
    print()
    
    # Initialize assistant
    try:
        print("🔧 Initializing assistant...")
        assistant = FAQAssistant()
        print("✅ Assistant initialized successfully\n")
    except Exception as e:
        print(f"❌ Failed to initialize assistant: {e}")
        return
    
    # Run tests
    passed = 0
    failed = 0
    results = []
    
    for test in QUICK_TESTS:
        print(f"Test {test['id']}/10: {test['description']}")
        print(f"Query: \"{test['query']}\"")
        
        try:
            # Process query
            answer, citation = assistant.process_query(test['query'], [])
            
            # Check if answer is reasonable
            if not answer or len(answer.strip()) < 10:
                print(f"⚠️  SUSPICIOUS: Very short answer\n")
                failed += 1
                results.append({
                    "test": test['id'],
                    "status": "FAILED",
                    "reason": "Answer too short",
                    "answer": answer[:100]
                })
                continue
            
            # Check "should contain" conditions
            if "should_contain" in test:
                missing = []
                for phrase in test['should_contain']:
                    # Check if any variant of the phrase is present (case-insensitive)
                    if not any(variant.lower() in answer.lower() for variant in [phrase]):
                        missing.append(phrase)
                
                if missing:
                    print(f"⚠️  MISSING: {', '.join(missing)}")
                    print(f"Answer preview: {answer[:200]}...\n")
                    failed += 1
                    results.append({
                        "test": test['id'],
                        "status": "FAILED",
                        "reason": f"Missing: {', '.join(missing)}",
                        "answer": answer[:200]
                    })
                    continue
            
            # Check "should not contain" conditions
            if "should_not_contain" in test:
                found = []
                for phrase in test['should_not_contain']:
                    if phrase.lower() in answer.lower():
                        found.append(phrase)
                
                if found:
                    print(f"⚠️  UNEXPECTED: Found {', '.join(found)}")
                    print(f"Answer preview: {answer[:200]}...\n")
                    failed += 1
                    results.append({
                        "test": test['id'],
                        "status": "FAILED",
                        "reason": f"Unexpected content: {', '.join(found)}",
                        "answer": answer[:200]
                    })
                    continue
            
            # Test passed
            print("✅ PASSED")
            print(f"Answer preview: {answer[:150]}...\n")
            passed += 1
            results.append({
                "test": test['id'],
                "status": "PASSED",
                "answer": answer[:150]
            })
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}\n")
            failed += 1
            results.append({
                "test": test['id'],
                "status": "ERROR",
                "reason": str(e)
            })
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {passed}/10")
    print(f"❌ Failed: {failed}/10")
    print(f"Success Rate: {(passed/10)*100:.0f}%")
    print()
    
    if failed > 0:
        print("Failed Tests:")
        for result in results:
            if result['status'] != "PASSED":
                print(f"  Test {result['test']}: {result.get('reason', 'Unknown error')}")
        print()
    
    # Overall status
    if passed == 10:
        print("🎉 ALL TESTS PASSED! Chatbot is healthy.")
        return 0
    elif passed >= 8:
        print("⚠️  MOSTLY PASSING - Some issues need attention")
        return 1
    elif passed >= 5:
        print("⚠️  SEVERAL FAILURES - Review needed")
        return 1
    else:
        print("❌ CRITICAL - Many tests failing")
        return 1

if __name__ == "__main__":
    exit_code = run_health_check()
    sys.exit(exit_code)

