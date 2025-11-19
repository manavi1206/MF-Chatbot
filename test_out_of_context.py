#!/usr/bin/env python3
"""
Quick test for out-of-context detection
"""

from faq_assistant import FAQAssistant

def test_out_of_context():
    """Test out-of-context query detection"""
    print("Testing out-of-context detection...\n")
    
    assistant = FAQAssistant()
    
    test_cases = [
        ("do you cook", "out_of_context"),
        ("what's the weather", "out_of_context"),
        ("who is PM of India", "out_of_context"),
        ("tell me a joke", "out_of_context"),
        ("What is the expense ratio of HDFC Large Cap Fund?", "factual"),
        ("Should I invest in ELSS?", "advice"),
        ("hi", "greeting"),
        ("what funds do you have", "coverage"),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected_type in test_cases:
        actual_type = assistant.classify_query_type(query)
        
        if actual_type == expected_type:
            print(f"✅ PASS: '{query}' → {actual_type}")
            passed += 1
        else:
            print(f"❌ FAIL: '{query}' → Expected: {expected_type}, Got: {actual_type}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{len(test_cases)} passed")
    print(f"{'='*60}\n")
    
    if failed > 0:
        print(f"⚠️  {failed} test(s) failed")
        return 1
    else:
        print("🎉 All tests passed!")
        return 0

if __name__ == "__main__":
    exit(test_out_of_context())

