#!/usr/bin/env python3
"""
Fixed Test System for Optimized 70%+ Success Rate
Comprehensive testing with all critical fixes applied
"""

import os
import sys
import time
import asyncio
import logging
from datetime import datetime, timedelta
import json
import psycopg2

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our modules
sys.path.append('.')

class OptimizedDetectionTester:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway')
        self.test_user_id = "123456789"
        self.test_keywords = ["moon", "pepe", "doge", "shib"]
        
        # Test tokens for validation
        self.test_tokens = [
            '7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU',  # Known token: Samoyed Coin
            'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
            'So11111111111111111111111111111111111111112'    # Wrapped SOL
        ]
        
    async def test_optimized_extraction_accuracy(self):
        """Test the optimized name extraction system for 70%+ success rate"""
        print("\n🎯 TESTING OPTIMIZED 70%+ SUCCESS RATE SYSTEM")
        print("=" * 60)
        
        try:
            from optimized_system_integration import test_optimized_system
            
            # Run comprehensive optimized test
            performance_results = await test_optimized_system()
            
            print(f"📊 OPTIMIZED SYSTEM PERFORMANCE:")
            print(f"   Success Rate: {performance_results['success_rate']:.1f}%")
            print(f"   Average Time: {performance_results['average_time']:.2f}s")
            print(f"   Total Time: {performance_results['total_time']:.2f}s")
            print(f"   System Active: {performance_results['optimized_system_active']}")
            
            # Detailed results
            print(f"\n📋 DETAILED RESULTS:")
            for i, result in enumerate(performance_results['results'], 1):
                success_icon = "✅" if result['success'] else "❌"
                print(f"   {success_icon} Token {i}: {result['name']}")
                print(f"      Address: {result['token_address'][:10]}...")
                print(f"      Confidence: {result['confidence']:.2f}")
                print(f"      Time: {result['extraction_time']:.2f}s")
                print(f"      Source: {result['source']}")
            
            # Success rate validation
            if performance_results['success_rate'] >= 70:
                print(f"\n✅ SUCCESS RATE TARGET MET: {performance_results['success_rate']:.1f}% ≥ 70%")
                return True
            else:
                print(f"\n⚠️ SUCCESS RATE BELOW TARGET: {performance_results['success_rate']:.1f}% < 70%")
                return False
                
        except Exception as e:
            print(f"❌ Optimized extraction test failed: {e}")
            return False
    
    async def test_speed_performance(self):
        """Test optimized speed performance"""
        print("\n⚡ TESTING OPTIMIZED SPEED PERFORMANCE")
        print("=" * 50)
        
        try:
            from optimized_system_integration import optimized_extract_name
            
            # Single token speed test
            test_address = '7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU'
            
            start_time = time.time()
            result = await optimized_extract_name(test_address)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            print(f"✅ Optimized Processing Time: {processing_time:.2f}s")
            print(f"✅ Token Name: {result['name']}")
            print(f"✅ Success: {result['success']}")
            print(f"✅ Confidence: {result['confidence']:.2f}")
            print(f"✅ Source: {result['source']}")
            
            # Speed validation (target: sub-second for 70%+ system)
            if processing_time < 1.0 and result['success']:
                print(f"✅ SPEED TARGET MET: {processing_time:.2f}s < 1.0s with success")
                return True
            else:
                print(f"⚠️ SPEED TARGET MISSED: {processing_time:.2f}s or failed extraction")
                return False
                
        except Exception as e:
            print(f"❌ Speed test failed: {e}")
            return False
    
    async def test_background_retry_system(self):
        """Test the progressive retry queue system"""
        print("\n🔄 TESTING PROGRESSIVE RETRY QUEUE SYSTEM")
        print("=" * 50)
        
        try:
            from optimized_name_extractor import get_optimized_extractor
            
            extractor = await get_optimized_extractor()
            
            # Test retry queue functionality
            fake_address = "FakeTokenAddressForRetryTest123456789"
            
            print(f"🧪 Testing retry system with fake address...")
            result = await extractor.extract_token_name(fake_address)
            
            print(f"✅ Initial Result: {result['name']}")
            print(f"✅ Retry Scheduled: {result.get('retry_scheduled', False)}")
            print(f"✅ Method: {result['method']}")
            
            # Check if retry queue is active
            if result.get('retry_scheduled') or 'retry' in result.get('method', ''):
                print("✅ RETRY SYSTEM ACTIVE: Background processing enabled")
                return True
            else:
                print("⚠️ RETRY SYSTEM: May need verification")
                return False
                
        except Exception as e:
            print(f"❌ Retry system test failed: {e}")
            return False
    
    async def run_optimized_tests(self):
        """Run all optimized system tests"""
        print("\n🚀 RUNNING COMPLETE OPTIMIZED SYSTEM TESTS")
        print("=" * 70)
        print("Testing restored 70%+ success rate architecture")
        print("=" * 70)
        
        test_results = {}
        
        # Test 1: Optimized extraction accuracy (70%+ target)
        print("\n📊 TEST 1: Optimized Extraction Accuracy")
        test_results['extraction_accuracy'] = await self.test_optimized_extraction_accuracy()
        
        # Test 2: Speed performance 
        print("\n⚡ TEST 2: Speed Performance")
        test_results['speed_performance'] = await self.test_speed_performance()
        
        # Test 3: Background retry system
        print("\n🔄 TEST 3: Background Retry System")
        test_results['retry_system'] = await self.test_background_retry_system()
        
        # Final results
        print("\n" + "=" * 70)
        print("🎯 OPTIMIZED SYSTEM TEST RESULTS")
        print("=" * 70)
        
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        for test_name, passed in test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status:10} {test_name.replace('_', ' ').title()}")
        
        print("=" * 70)
        print(f"TOTAL: {passed_tests} PASSED, {total_tests - passed_tests} FAILED")
        
        if passed_tests == total_tests:
            print("✅ ALL TESTS PASSED - 70%+ SUCCESS RATE SYSTEM READY")
        elif passed_tests >= 2:
            print("⚠️ MOSTLY WORKING - System functional with minor issues")
        else:
            print("❌ SYSTEM NEEDS ATTENTION - Critical issues detected")
        
        return test_results

async def main():
    """Main test execution"""
    tester = OptimizedDetectionTester()
    await tester.run_optimized_tests()

if __name__ == "__main__":
    asyncio.run(main())