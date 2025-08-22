#!/usr/bin/env python3
"""
Test 70% Success Rate System
Tests the DexScreener-focused system with smart retries
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

# Import our 70% system
sys.path.append('.')

class SeventyPercentTester:
    def __init__(self):
        self.test_tokens = [
            {
                'address': '7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU',
                'name': 'Samoyed Coin',
                'symbol': 'SAMO'
            },
            {
                'address': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', 
                'name': 'USD Coin',
                'symbol': 'USDC'
            },
            {
                'address': 'So11111111111111111111111111111111111111112',
                'name': 'Wrapped SOL',
                'symbol': 'SOL'
            },
            {
                'address': 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',
                'name': 'Bonk',
                'symbol': 'BONK'
            },
            {
                'address': 'mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So',
                'name': 'Marinade staked SOL',
                'symbol': 'mSOL'
            }
        ]
        
    async def test_70_percent_extraction(self):
        """Test the 70% success rate system"""
        print("\n🎯 TESTING 70% SUCCESS RATE SYSTEM")
        print("=" * 70)
        
        try:
            from dexscreener_70_percent_extractor import extract_name_70_percent, get_70_percent_stats
            
            results = []
            total_start = time.time()
            
            for i, token in enumerate(self.test_tokens):
                print(f"\n🔍 Test {i+1}/5: {token['address']}")
                start_time = time.time()
                
                try:
                    result = await extract_name_70_percent(token['address'])
                    extraction_time = time.time() - start_time
                    
                    if result and result.success:
                        print(f"✅ SUCCESS: '{result.name}' in {extraction_time:.2f}s")
                        print(f"   Confidence: {result.confidence}")
                        print(f"   Source: {result.source}")
                        
                        # Check if it's a real name (not fallback)
                        is_real_name = (
                            result.name and 
                            not result.name.lower().startswith(('token ', 'letsbonk token ')) and
                            result.confidence >= 0.8
                        )
                        
                        results.append({
                            'success': True,
                            'time': extraction_time,
                            'real_name': is_real_name,
                            'name': result.name,
                            'confidence': result.confidence
                        })
                    else:
                        print(f"❌ FAILED: No valid result in {extraction_time:.2f}s")
                        results.append({
                            'success': False,
                            'time': extraction_time,
                            'real_name': False,
                            'name': None,
                            'confidence': 0
                        })
                        
                except Exception as e:
                    print(f"❌ ERROR: {e}")
                    results.append({
                        'success': False,
                        'time': 999,
                        'real_name': False,
                        'name': None,
                        'confidence': 0
                    })
            
            total_time = time.time() - total_start
            
            # Calculate performance metrics
            successful = [r for r in results if r['success']]
            real_names = [r for r in results if r['real_name']]
            
            success_rate = (len(successful) / len(results)) * 100 if results else 0
            real_name_rate = (len(real_names) / len(results)) * 100 if results else 0
            avg_time = sum(r['time'] for r in successful) / len(successful) if successful else 0
            
            print(f"\n" + "=" * 70)
            print(f"📊 70% SYSTEM PERFORMANCE METRICS:")
            print(f"=" * 70)
            print(f"✅ Success Rate: {success_rate:.1f}% ({len(successful)}/{len(results)})")
            print(f"✅ Real Names: {real_name_rate:.1f}% ({len(real_names)}/{len(results)})")
            print(f"✅ Average Time: {avg_time:.2f}s")
            print(f"✅ Total Time: {total_time:.2f}s")
            
            # Get system stats
            try:
                stats = await get_70_percent_stats()
                print(f"✅ Overall System Success Rate: {stats['success_rate']:.1f}%")
                print(f"✅ Total Attempts: {stats['total_attempts']}")
            except:
                pass
            
            # Determine if test passes (70%+ success rate target)
            test_passed = success_rate >= 70 and real_name_rate >= 60 and avg_time <= 10.0
            
            print(f"\n" + "=" * 70)
            if test_passed:
                print("🎉 70% SUCCESS RATE TEST PASSED!")
                print("   System meets 70%+ success rate target")
            else:
                print("❌ 70% Success Rate Test Failed")
                if success_rate < 70:
                    print(f"   Success rate {success_rate:.1f}% below 70% target")
                if real_name_rate < 60:
                    print(f"   Real name rate {real_name_rate:.1f}% below 60% target")
                if avg_time > 10.0:
                    print(f"   Average time {avg_time:.2f}s above 10s target")
            print("=" * 70)
                
            return test_passed
            
        except Exception as e:
            print(f"❌ Test setup failed: {e}")
            return False
    
    def test_clean_server_compatibility(self):
        """Test that 70% system works with clean server"""
        print("\n🔧 TESTING CLEAN SERVER COMPATIBILITY")
        print("=" * 70)
        
        try:
            from clean_alchemy_server import app
            from dexscreener_70_percent_extractor import DexScreener70PercentExtractor
            
            print("✅ Clean server imports successfully")
            print("✅ 70% extractor imports successfully")
            
            # Check if Flask app is created
            if hasattr(app, 'run'):
                print("✅ Flask app is properly configured")
                return True
            else:
                print("❌ Flask app not properly configured")
                return False
                
        except Exception as e:
            print(f"❌ Compatibility test failed: {e}")
            return False

async def main():
    """Run all 70% success rate tests"""
    print("🚀 70% SUCCESS RATE SYSTEM TEST SUITE")
    print("=" * 80)
    print(f"Testing Date: {datetime.now()}")
    print("Target: 70%+ success rate using DexScreener with smart retries")
    print("=" * 80)
    
    tester = SeventyPercentTester()
    
    # Run tests
    test_results = []
    
    # Test 1: Clean server compatibility
    result1 = tester.test_clean_server_compatibility()
    test_results.append(("Clean Server Compatibility", result1))
    
    # Test 2: 70% extraction system
    result2 = await tester.test_70_percent_extraction()
    test_results.append(("70% Success Rate Extraction", result2))
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 FINAL TEST RESULTS")
    print("=" * 80)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}     {test_name}")
        if result:
            passed += 1
    
    print("=" * 80)
    print(f"TOTAL: {passed} PASSED, {len(test_results) - passed} FAILED")
    
    if passed == len(test_results):
        print("🎉 ALL TESTS PASSED - 70% SUCCESS RATE SYSTEM READY")
        print("   System uses DexScreener with smart retries for optimal results")
    else:
        print("⚠️ Some tests failed - needs attention")
    
    return passed == len(test_results)

if __name__ == "__main__":
    asyncio.run(main())