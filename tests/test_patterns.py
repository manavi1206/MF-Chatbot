#!/usr/bin/env python3
"""
Test out-of-context pattern matching (no LLM needed)
"""

import re

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_patterns():
    """Test regex patterns for out-of-context detection"""
    print("Testing out-of-context patterns...\n")
    
    # Pattern from faq_assistant.py
    out_of_context_patterns = [
        r'\bpm\b', r'prime minister', r'president', r'minister',
        r'capital of', r'capital city',
        r'favorite sport', r'favourite sport',
        r'tell me a joke', r'joke',
        r'weather', r'temperature',
        r'what is your name', r'who are you',
        r'what time is it', r'what day is it',
        r'how are you', r'how do you do',
        r'who is (the )?(pm|president|ceo|founder|director)',
        r'what is (the )?(population|area|size)',
        r'when (is|was|will)',
        r'where (is|was|are)',
        r'\b(do you|can you|did you)\s+(cook|eat|sleep|dance|sing|play|run|walk)',
        r'\b(cooking|baking|chef|kitchen|meal|breakfast|lunch|dinner)\b',
        r'(cricket|football|sports|movie|film|music)',
        r'(recipe|food|restaurant)',
        r'(technology|computer|phone|laptop)(?! fund)',
        r'(game|gaming|video)',
        r'(travel|tourism|hotel|flight)'
    ]
    
    test_cases = [
        ("do you cook", True, "cooking question"),
        ("what's the weather", True, "weather question"),
        ("who is PM of India", True, "politics question"),
        ("tell me a joke", True, "joke request"),
        ("can you dance", True, "personal ability question"),
        ("What is the expense ratio of HDFC Large Cap Fund?", False, "factual MF question"),
        ("What is the ELSS lock-in period?", False, "factual MF question"),
        ("hi", False, "greeting"),
    ]
    
    passed = 0
    failed = 0
    
    for query, should_match, description in test_cases:
        query_lower = query.lower()
        has_out_of_context = any(re.search(pattern, query_lower) for pattern in out_of_context_patterns)
        
        if has_out_of_context == should_match:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"{status}: '{query}' → Pattern match: {has_out_of_context} (expected: {should_match}) - {description}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{len(test_cases)} passed")
    print(f"{'='*60}\n")
    
    if failed > 0:
        print(f"⚠️  {failed} test(s) failed")
    else:
        print("🎉 All pattern tests passed!")

if __name__ == "__main__":
    test_patterns()

