#!/usr/bin/env python3
"""
Test Front 43_updated_keywordlogic Enhanced Bidirectional Matching
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from complete_discord_bot_with_commands import TokenMonitorBot

class Front43UpdatedKeywordLogicTest:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.bot = TokenMonitorBot()
        
    def test_blue_collar_case(self):
        """Test the specific blue collar scenario that was fixed"""
        print("\n🧪 Testing Blue Collar Fix...")
        
        # The exact case that was failing before Front 43
        result = self.bot.is_keyword_match("blue collar", "blue collar boys")
        if result:
            print("  ✅ 'blue collar' now matches 'blue collar boys' (FIXED!)")
            self.passed += 1
        else:
            print("  ❌ 'blue collar' still doesn't match 'blue collar boys'")
            self.failed += 1
    
    def test_enhanced_bidirectional_matching(self):
        """Test comprehensive bidirectional matching scenarios"""
        print("\n🧪 Testing Enhanced Bidirectional Matching...")
        
        test_cases = [
            # Subset tokens matching superset keywords
            ("blue collar", "blue collar boys", True, "Subset token → superset keyword"),
            ("apple coin", "apple coin token", True, "Subset token → superset keyword"),
            ("bitcoin", "bitcoin cash", True, "Single word → multi-word keyword"),
            ("moon", "moon shot", True, "Single word → phrase keyword"),
            ("talent", "talent show", True, "Single word → phrase keyword"),
            
            # Superset tokens matching subset keywords  
            ("blue collar boys", "blue collar", True, "Superset token → subset keyword"),
            ("apple coin token", "apple coin", True, "Superset token → subset keyword"),
            ("bitcoin cash", "bitcoin", True, "Multi-word token → single word"),
            ("moon shot", "moon", True, "Phrase token → single word"),
            
            # Should NOT match
            ("random token", "completely different", False, "Unrelated words"),
            ("eth", "bitcoin", False, "Different crypto terms"),
            ("cat", "dog house", False, "No word overlap"),
        ]
        
        for token_name, keyword, expected, description in test_cases:
            result = self.bot.is_keyword_match(token_name, keyword)
            if result == expected:
                print(f"  ✅ {description}")
                self.passed += 1
            else:
                print(f"  ❌ {description} - Expected {expected}, got {result}")
                print(f"      Token: '{token_name}' | Keyword: '{keyword}'")
                self.failed += 1
    
    def test_original_functionality_preserved(self):
        """Ensure all original matching still works"""
        print("\n🧪 Testing Original Functionality Preserved...")
        
        test_cases = [
            ("Apple Coin", "coin", True, "Single word matching"),
            ("Bitcoin Cash", "bitcoin", True, "Case-insensitive matching"),
            ("Blue-Collar Worker", "blue collar", True, "Normalized punctuation"),
            ("TALENT SHOW", "talent", True, "Case normalization"),
            ("random token", "xyz", False, "No false positives"),
            ("short", "very long keyword phrase", False, "Length mismatch protection"),
        ]
        
        for token_name, keyword, expected, description in test_cases:
            result = self.bot.is_keyword_match(token_name, keyword)
            if result == expected:
                print(f"  ✅ {description}")
                self.passed += 1
            else:
                print(f"  ❌ {description} - Expected {expected}, got {result}")
                self.failed += 1
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        print("\n🧪 Testing Edge Cases...")
        
        test_cases = [
            ("a", "a very long keyword", False, "Short token protection"),
            ("ab", "ab cd ef gh", False, "Very short token"),
            ("normal token", "", False, "Empty keyword"),
            ("", "keyword", False, "Empty token"),
            ("Token With Numbers123", "numbers", True, "Alphanumeric handling"),
            ("Special-Characters!", "special characters", True, "Special character normalization"),
        ]
        
        for token_name, keyword, expected, description in test_cases:
            try:
                result = self.bot.is_keyword_match(token_name, keyword)
                if result == expected:
                    print(f"  ✅ {description}")
                    self.passed += 1
                else:
                    print(f"  ❌ {description} - Expected {expected}, got {result}")
                    self.failed += 1
            except Exception as e:
                print(f"  ❌ {description} - Exception: {e}")
                self.failed += 1
    
    def run_comprehensive_test(self):
        """Run complete Front 43 test suite"""
        print("🚀 Starting Front 43_updated_keywordlogic Enhanced Matching Test Suite")
        print("=" * 70)
        
        self.test_blue_collar_case()
        self.test_enhanced_bidirectional_matching()
        self.test_original_functionality_preserved()
        self.test_edge_cases()
        
        print("\n" + "=" * 70)
        print(f"📊 FRONT 43_updated_keywordlogic TEST RESULTS:")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        
        if self.failed == 0:
            print(f"📈 Success Rate: 100.0%")
            print("🎉 ALL TESTS PASSED - Front 43_updated_keywordlogic Enhanced Matching Working!")
            print("🔥 Blue collar matching issue RESOLVED!")
            return True
        else:
            success_rate = self.passed/(self.passed+self.failed)*100
            print(f"📈 Success Rate: {success_rate:.1f}%")
            print("⚠️  Some tests failed - review implementation")
            return False

if __name__ == "__main__":
    tester = Front43UpdatedKeywordLogicTest()
    success = tester.run_comprehensive_test()
    
    if success:
        print("\n🚀 Front 43_updated_keywordlogic is ready for deployment!")
        print("✅ Enhanced bidirectional matching fully functional")
    else:
        print("\n⚠️  Front 43_updated_keywordlogic needs additional work")
    
    sys.exit(0 if success else 1)