#!/usr/bin/env python3
"""
Test script for AI Smart Keyword Detection System
Verifies that typo tolerance and fuzzy matching work correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_smart_keyword_matcher import AISmartKeywordMatcher, SmartMatchingIntegration
import json

def test_typo_detection():
    """Test the exact user scenario: 'buy a busienss' vs 'buy a business'"""
    
    print("🧠 AI SMART KEYWORD DETECTION TEST")
    print("="*50)
    
    # User's actual keywords including the typo
    keywords = [
        'buy a busienss',  # The typo keyword
        'business',
        'crypto', 
        'token',
        '2k ai videos',
        'bonk',
        'ai',
        'defi'
    ]
    
    # Initialize AI matcher
    matcher = AISmartKeywordMatcher(keywords, fuzzy_threshold=85)
    integration = SmartMatchingIntegration(keywords)
    
    print(f"Keywords loaded: {len(keywords)}")
    print(f"Fuzzy threshold: 85%")
    print()
    
    # Test cases that should match
    test_cases = [
        # The original problem case
        {'token': 'buy a business', 'expected': 'business', 'description': 'Original problem - typo mismatch'},
        
        # User's typo keyword should match exactly
        {'token': 'buy a busienss', 'expected': 'buy a busienss', 'description': 'User typo keyword - exact match'},
        
        # Variations that should work with fuzzy matching
        {'token': 'buy buisness', 'expected': 'business', 'description': 'Another typo variation'},
        {'token': 'buy business', 'expected': 'business', 'description': 'Shortened version'},
        {'token': 'business buy', 'expected': 'business', 'description': 'Word order difference'},
        {'token': 'bussiness', 'expected': 'business', 'description': 'Common misspelling'},
        
        # Other keywords
        {'token': '2k ai video', 'expected': '2k ai videos', 'description': 'Singular vs plural'},
        {'token': 'crypto token', 'expected': 'crypto', 'description': 'Keyword + token'},
        {'token': 'bonk coin', 'expected': 'bonk', 'description': 'Bonk variation'},
        {'token': 'artificial intelligence', 'expected': 'ai', 'description': 'AI expansion'},
        {'token': 'defi protocol', 'expected': 'defi', 'description': 'DeFi variation'},
        
        # Edge cases
        {'token': 'Buy A Business', 'expected': 'business', 'description': 'Case insensitive'},
        {'token': 'buy-a-business', 'expected': 'business', 'description': 'Hyphenated'},
        {'token': 'buy_a_business', 'expected': 'business', 'description': 'Underscored'},
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        token_name = test_case['token']
        expected = test_case['expected']
        description = test_case['description']
        
        # Test using AI smart matcher
        result = matcher.smart_keyword_match(token_name)
        
        # Test using integration wrapper
        integration_result = integration.enhanced_keyword_check(token_name, "")
        
        if result and result['matched_keyword'] == expected:
            status = "✅ PASS"
            passed += 1
            confidence = result['confidence']
            match_type = result['match_type']
            print(f"{i:2d}. {status} '{token_name}' → '{expected}' ({match_type}, {confidence}%)")
            print(f"    {description}")
        else:
            status = "❌ FAIL"
            failed += 1
            actual = result['matched_keyword'] if result else 'No match'
            print(f"{i:2d}. {status} '{token_name}' → Expected: '{expected}', Got: '{actual}'")
            print(f"    {description}")
            
            # Show suggestions for failed cases
            suggestions = matcher.get_typo_suggestions(token_name, limit=3)
            if suggestions:
                print(f"    💡 Suggestions: {[s['keyword'] for s in suggestions]}")
        
        print()
    
    print("SUMMARY")
    print("="*20)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! AI Smart Detection is working perfectly.")
        print("✅ The 'buy a busienss' vs 'buy a business' problem is solved.")
    else:
        print(f"\n⚠️  {failed} tests failed. System needs adjustment.")
    
    return failed == 0

def test_keyword_analysis():
    """Test keyword list analysis for potential issues"""
    
    print("\n🔍 KEYWORD LIST ANALYSIS")
    print("="*30)
    
    # Simulate keywords with potential issues
    test_keywords = [
        'buy a busienss',  # Typo
        'buy a business',  # Correct spelling
        'crypto',
        'krypto',          # Alternative spelling
        'token',
        'tokens',          # Plural
        'ai',
        'AI',              # Case difference
        'defi',
        'DeFi'             # Case difference
    ]
    
    matcher = AISmartKeywordMatcher(test_keywords)
    issues = matcher.validate_keyword_list()
    
    print(f"Analyzing {len(test_keywords)} keywords...")
    
    if issues['potential_typos']:
        print("\n⚠️  POTENTIAL TYPOS DETECTED:")
        for issue in issues['potential_typos']:
            print(f"  • '{issue['keyword1']}' vs '{issue['keyword2']}' ({issue['similarity']}% similar)")
    
    if issues['near_duplicates']:
        print("\n⚠️  NEAR DUPLICATES DETECTED:")
        for issue in issues['near_duplicates']:
            print(f"  • '{issue['keyword1']}' vs '{issue['keyword2']}' ({issue['similarity']}% similar)")
    
    if not issues['potential_typos'] and not issues['near_duplicates']:
        print("✅ No keyword issues detected.")
    
    return True

def main():
    """Run all tests"""
    try:
        print("Starting AI Smart Detection System Tests...\n")
        
        # Test typo detection
        typo_test_passed = test_typo_detection()
        
        # Test keyword analysis
        analysis_test_passed = test_keyword_analysis()
        
        print("\n" + "="*60)
        print("FINAL RESULTS")
        print("="*60)
        
        if typo_test_passed and analysis_test_passed:
            print("🎉 ALL SYSTEMS OPERATIONAL!")
            print("✅ AI Smart Detection successfully solves the typo problem")
            print("✅ System is ready for deployment")
            return 0
        else:
            print("❌ Some tests failed. System needs attention.")
            return 1
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())