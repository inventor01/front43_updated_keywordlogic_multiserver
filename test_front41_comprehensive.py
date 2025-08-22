#!/usr/bin/env python3
"""
Front 41 - Comprehensive QA Test Suite
Tests all keyword matching improvements, Discord commands, and functionality
"""

import sys
import asyncio
import re
from integrated_monitoring_system import IntegratedTokenMonitor

class Front41QATest:
    def __init__(self):
        self.monitor = IntegratedTokenMonitor()
        self.passed = 0
        self.failed = 0
        
    def test_keyword_normalization(self):
        """Test keyword matching with normalization"""
        print("\n🧪 Testing Keyword Normalization...")
        
        test_cases = [
            # (token_name, keyword, should_match, description)
            ("AppleCoin", "coin", True, "coin matches AppleCoin"),
            ("Apple-coin", "coin", True, "coin matches Apple-coin"),
            ("Apple_Coin", "coin", True, "coin matches Apple_Coin"),
            ("APPLE COIN", "coin", True, "coin matches APPLE COIN (case insensitive)"),
            ("Coincidence", "coin", True, "coin matches Coincidence (substring)"),
            ("Bitcoin", "coin", True, "coin matches Bitcoin"),
            ("Love Token", "love", True, "love matches Love Token"),
            ("Glove", "love", True, "love matches Glove (partial)"),
            ("Micheal Jackson Token", "micheal jackson", True, "multi-word exact match"),
            ("MICHEAL_JACKSON", "micheal jackson", True, "multi-word with underscore"),
            ("The Big Leagues", "big leagues", True, "phrase matching"),
            ("xyz", "coin", False, "no false positives"),
        ]
        
        for token_name, keyword, expected, description in test_cases:
            result = self.monitor.is_keyword_match(token_name, keyword)
            if result == expected:
                print(f"  ✅ {description}")
                self.passed += 1
            else:
                print(f"  ❌ {description} - Expected {expected}, got {result}")
                self.failed += 1
    
    def test_system_keywords(self):
        """Test System keyword handling"""
        print("\n🧪 Testing System Keywords...")
        
        # Simulate keywords from database
        self.monitor.user_keywords = {
            'System': ['coin', 'token'],
            '123456789': ['personal']
        }
        
        matches = self.monitor.check_keyword_matches("Apple Coin", "test123pump")
        
        if matches:
            system_match = any(match['keyword'] == 'coin' for match in matches)
            if system_match:
                print("  ✅ System keywords apply to all users")
                self.passed += 1
            else:
                print("  ❌ System keywords not working")
                self.failed += 1
        else:
            print("  ❌ No matches found for System keywords")
            self.failed += 1
    
    def test_platform_detection(self):
        """Test platform detection"""
        print("\n🧪 Testing Platform Detection...")
        
        test_cases = [
            ("abc123pump", "Pump.fun", "PumpFun address"),
            ("xyz456bonk", "LetsBonk", "LetsBonk address"),
            ("random123", "Other", "Other platform"),
        ]
        
        for address, expected, description in test_cases:
            platform = self.monitor.detect_platform(address)
            if platform == expected:
                print(f"  ✅ {description}: {platform}")
                self.passed += 1
            else:
                print(f"  ❌ {description}: Expected {expected}, got {platform}")
                self.failed += 1
    
    def test_name_enhancement(self):
        """Test token name enhancement and fallbacks"""
        print("\n🧪 Testing Name Enhancement...")
        
        # Test with fallback to symbol
        enhanced = asyncio.run(self.monitor.enhance_token_name("test123", "Unknown", "TESTCOIN"))
        if enhanced == "TESTCOIN":
            print("  ✅ Symbol fallback working")
            self.passed += 1
        else:
            print(f"  ❌ Symbol fallback failed: got {enhanced}")
            self.failed += 1
        
        # Test with address fallback
        enhanced = asyncio.run(self.monitor.enhance_token_name("abc123def", "Unknown", ""))
        if enhanced.startswith("Token_abc123"):
            print("  ✅ Address fallback working")
            self.passed += 1
        else:
            print(f"  ❌ Address fallback failed: got {enhanced}")
            self.failed += 1
    
    def test_discord_commands_structure(self):
        """Test Discord bot command structure"""
        print("\n🧪 Testing Discord Commands Structure...")
        
        try:
            import complete_discord_bot_with_commands
            print("  ✅ Discord bot module loads successfully")
            self.passed += 1
        except Exception as e:
            print(f"  ❌ Discord bot module failed to load: {e}")
            self.failed += 1
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Front 41 Comprehensive QA Test Suite")
        print("=" * 50)
        
        self.test_keyword_normalization()
        self.test_system_keywords() 
        self.test_platform_detection()
        self.test_name_enhancement()
        self.test_discord_commands_structure()
        
        print("\n" + "=" * 50)
        print(f"📊 TEST RESULTS:")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {self.passed/(self.passed+self.failed)*100:.1f}%")
        
        if self.failed == 0:
            print("🎉 ALL TESTS PASSED - Front 41 ready for deployment!")
            return True
        else:
            print("⚠️  Some tests failed - review issues before deployment")
            return False

if __name__ == "__main__":
    tester = Front41QATest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)