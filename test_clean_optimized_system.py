#!/usr/bin/env python3
"""
Clean Optimized System Test
Tests the clean optimized system without any retry logic
"""

import os
import sys
import time
import asyncio
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our clean modules
sys.path.append('.')

class CleanSystemTester:
    def __init__(self):
        self.test_tokens = [
            {
                'address': '7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU',
                'name': 'Moon Dog',
                'symbol': 'MOON'
            },
            {
                'address': '9yHJfxeKGGsnHLMHaC1BjCRRaG5W7fFJMK3kV2bEhNpQ', 
                'name': 'Pepe Coin',
                'symbol': 'PEPE'
            }
        ]
        
    async def test_clean_extraction(self):
        """Test the clean optimized name extractor"""
        print("\n🎯 TESTING CLEAN OPTIMIZED EXTRACTION")
        print("=" * 60)
        
        try:
            from optimized_name_extractor import OptimizedNameExtractor
            
            extractor = OptimizedNameExtractor()
            await extractor.initialize_sessions()
            
            results = []
            
            for token in self.test_tokens:
                print(f"\n🔍 Testing: {token['address']}")
                start_time = time.time()
                
                try:
                    result = await extractor.extract_token_name(token['address'])
                    extraction_time = time.time() - start_time
                    
                    # Cleanup sessions to prevent warnings
                    await extractor.cleanup_sessions()
                    
                    if result and result.success:
                        print(f"✅ SUCCESS: '{result.name}' in {extraction_time:.2f}s")
                        print(f"   Source: {result.source}")
                        print(f"   Confidence: {result.confidence}")
                        
                        # Check if it's not a fallback name
                        is_real_name = (
                            result.name and 
                            not result.name.lower().startswith(('token ', 'letsbonk token ')) and
                            result.confidence >= 0.8
                        )
                        
                        results.append({
                            'success': True,
                            'time': extraction_time,
                            'real_name': is_real_name,
                            'name': result.name
                        })
                    else:
                        print(f"❌ FAILED: No valid result")
                        results.append({
                            'success': False,
                            'time': extraction_time,
                            'real_name': False,
                            'name': None
                        })
                        
                except Exception as e:
                    print(f"❌ ERROR: {e}")
                    results.append({
                        'success': False,
                        'time': 999,
                        'real_name': False,
                        'name': None
                    })
            
            # Calculate performance metrics
            successful = [r for r in results if r['success']]
            real_names = [r for r in results if r['real_name']]
            
            success_rate = (len(successful) / len(results)) * 100 if results else 0
            real_name_rate = (len(real_names) / len(results)) * 100 if results else 0
            avg_time = sum(r['time'] for r in successful) / len(successful) if successful else 0
            
            print(f"\n📊 PERFORMANCE METRICS:")
            print(f"   Success Rate: {success_rate:.1f}% ({len(successful)}/{len(results)})")
            print(f"   Real Names: {real_name_rate:.1f}% ({len(real_names)}/{len(results)})")
            print(f"   Average Time: {avg_time:.2f}s")
            
            # Test passes if we get real names quickly
            test_passed = success_rate >= 80 and real_name_rate >= 70 and avg_time <= 5.0
            
            if test_passed:
                print("✅ CLEAN SYSTEM TEST PASSED")
            else:
                print("❌ CLEAN SYSTEM TEST FAILED")
                
            return test_passed
            
        except Exception as e:
            print(f"❌ Test setup failed: {e}")
            return False
    
    def test_clean_server_import(self):
        """Test that clean server imports without errors"""
        print("\n🔧 TESTING CLEAN SERVER IMPORT")
        print("=" * 60)
        
        try:
            from clean_alchemy_server import app
            print("✅ Clean server imports successfully")
            
            # Check if Flask app is created
            if hasattr(app, 'run'):
                print("✅ Flask app is properly configured")
                return True
            else:
                print("❌ Flask app not properly configured")
                return False
                
        except Exception as e:
            print(f"❌ Clean server import failed: {e}")
            return False
    
    def test_system_integration(self):
        """Test overall system integration"""
        print("\n🚀 TESTING SYSTEM INTEGRATION")
        print("=" * 60)
        
        try:
            # Test all key components import cleanly
            from start_clean_system import main
            from high_success_integration import HighSuccessIntegration
            print("✅ All clean components import successfully")
            
            return True
            
        except Exception as e:
            print(f"❌ System integration failed: {e}")
            return False

async def main():
    """Run all clean system tests"""
    print("🚀 CLEAN OPTIMIZED SYSTEM TEST SUITE")
    print("=" * 70)
    print(f"Testing Date: {datetime.now()}")
    print("=" * 70)
    
    tester = CleanSystemTester()
    
    # Run tests
    test_results = []
    
    # Test 1: Clean server import
    result1 = tester.test_clean_server_import()
    test_results.append(("Clean Server Import", result1))
    
    # Test 2: System integration
    result2 = tester.test_system_integration()
    test_results.append(("System Integration", result2))
    
    # Test 3: Clean extraction
    result3 = await tester.test_clean_extraction()
    test_results.append(("Clean Extraction", result3))
    
    # Summary
    print("\n" + "=" * 70)
    print("🎯 TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}     {test_name}")
        if result:
            passed += 1
    
    print("=" * 70)
    print(f"TOTAL: {passed} PASSED, {len(test_results) - passed} FAILED")
    
    if passed == len(test_results):
        print("🎉 ALL TESTS PASSED - CLEAN SYSTEM READY")
    else:
        print("⚠️ Some tests failed - needs attention")
    
    return passed == len(test_results)

if __name__ == "__main__":
    asyncio.run(main())