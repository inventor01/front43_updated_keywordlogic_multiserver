#!/usr/bin/env python3
"""
Clean Test System - Fixed Version
Tests the optimized system without broken imports or syntax errors
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

class CleanSystemTester:
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
        
    def setup_test_environment(self):
        """Setup test environment with proper database schema"""
        print("\n🔧 STEP 1: Setting Up Clean Test Environment")
        print("=" * 60)
        
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # Create keywords table if it doesn't exist (fixed constraint)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keywords (
                    id SERIAL PRIMARY KEY,
                    keyword VARCHAR(255) NOT NULL,
                    user_id VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create unique index if it doesn't exist
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS keywords_user_keyword_idx 
                ON keywords (user_id, keyword)
            """)
            
            # Create notified_tokens table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notified_tokens (
                    id SERIAL PRIMARY KEY,
                    token_address VARCHAR(255) NOT NULL,
                    keyword VARCHAR(255) NOT NULL,
                    notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(token_address, keyword)
                )
            """)
            
            # Clear previous test data
            cursor.execute("DELETE FROM notified_tokens WHERE token_address LIKE %s", ('test_%',))
            cursor.execute("DELETE FROM keywords WHERE user_id = %s", (self.test_user_id,))
            
            # Add test keywords
            for keyword in self.test_keywords:
                cursor.execute("""
                    INSERT INTO keywords (user_id, keyword) 
                    VALUES (%s, %s) 
                    ON CONFLICT (keyword, user_id) DO NOTHING
                """, (self.test_user_id, keyword))
            
            conn.commit()
            
            # Verify keywords were added
            cursor.execute("SELECT keyword FROM keywords WHERE user_id = %s", (self.test_user_id,))
            added_keywords = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            print(f"✅ Added test keywords: {added_keywords}")
            print(f"✅ Database tables created/verified")
            print(f"✅ Test environment ready")
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    async def test_optimized_extraction_system(self):
        """Test the optimized name extraction system"""
        print("\n🎯 STEP 2: Testing Optimized Extraction System")
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
    
    async def test_clean_server_functionality(self):
        """Test the clean server functionality"""
        print("\n🚀 STEP 3: Testing Clean Server Functionality")
        print("=" * 60)
        
        try:
            from clean_alchemy_server import CleanAlchemyServer
            
            # Initialize clean server
            server = CleanAlchemyServer()
            await server.initialize_optimized_components()
            server.load_keywords_from_database()
            
            print(f"✅ Clean server initialized")
            print(f"✅ Keywords loaded: {len(server.keywords)}")
            print(f"✅ Optimized components: {'Ready' if server.high_success_extractor else 'Not Ready'}")
            
            # Test token processing
            test_token = {
                'address': '7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU',
                'symbol': 'SAMO',
                'name': 'Samoyed Coin'
            }
            
            print(f"\n🧪 Testing token processing...")
            start_time = time.time()
            result = await server.process_token_detection(test_token)
            processing_time = time.time() - start_time
            
            print(f"✅ Token processed: {result}")
            print(f"✅ Processing time: {processing_time:.2f}s")
            print(f"✅ Stats: {server.stats}")
            
            return result
            
        except Exception as e:
            print(f"❌ Clean server test failed: {e}")
            return False
    
    async def test_keyword_matching(self):
        """Test keyword matching functionality"""
        print("\n🎯 STEP 4: Testing Keyword Matching")
        print("=" * 60)
        
        try:
            from clean_alchemy_server import CleanAlchemyServer
            
            server = CleanAlchemyServer()
            server.load_keywords_from_database()
            
            # Test cases (updated for refined matching)
            test_cases = [
                ('Moon Dog', ['moon']),
                ('Pepe Coin', ['pepe']),
                ('Doge Forever', ['doge']),
                ('Shiba Inu Token', []),  # 'shib' not in name, refined matching
                ('Bitcoin Cash', []),     # No target keywords
                ('Random Token', [])      # No target keywords
            ]
            
            all_passed = True
            
            for token_name, expected_matches in test_cases:
                matches = server.matches_keywords(token_name)
                
                if set(matches) == set(expected_matches):
                    print(f"✅ '{token_name}' -> {matches} (correct)")
                else:
                    print(f"❌ '{token_name}' -> {matches} (expected {expected_matches})")
                    all_passed = False
            
            if all_passed:
                print(f"\n✅ All keyword matching tests passed")
                return True
            else:
                print(f"\n❌ Some keyword matching tests failed")
                return False
                
        except Exception as e:
            print(f"❌ Keyword matching test failed: {e}")
            return False
    
    async def test_discord_notification_format(self):
        """Test Discord notification formatting"""
        print("\n💬 STEP 5: Testing Discord Notification Format")
        print("=" * 60)
        
        try:
            from clean_alchemy_server import CleanAlchemyServer
            
            server = CleanAlchemyServer()
            
            # Test notification data
            test_notification = {
                'token_address': '7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU',
                'name': 'Moon Dog',
                'symbol': 'MOON',
                'keywords': ['moon'],
                'confidence': 0.95,
                'source': 'dexscreener',
                'timestamp': datetime.now(),
                'platform': 'letsbonk.fun'
            }
            
            print(f"📨 Testing notification format...")
            await server.send_discord_notification(test_notification)
            
            print(f"✅ Notification format test completed")
            return True
            
        except Exception as e:
            print(f"❌ Discord notification test failed: {e}")
            return False
    
    async def run_all_clean_tests(self):
        """Run all clean system tests"""
        print("\n🚀 RUNNING COMPLETE CLEAN SYSTEM TESTS")
        print("=" * 70)
        print("Testing cleaned system without broken imports or syntax errors")
        print("=" * 70)
        
        test_results = {}
        
        # Test 1: Setup environment
        print("\n📊 TEST 1: Test Environment Setup")
        test_results['environment_setup'] = self.setup_test_environment()
        
        # Test 2: Optimized extraction system
        print("\n⚡ TEST 2: Optimized Extraction System")
        test_results['optimized_extraction'] = await self.test_optimized_extraction_system()
        
        # Test 3: Clean server functionality
        print("\n🚀 TEST 3: Clean Server Functionality")
        test_results['clean_server'] = await self.test_clean_server_functionality()
        
        # Test 4: Keyword matching
        print("\n🎯 TEST 4: Keyword Matching")
        test_results['keyword_matching'] = await self.test_keyword_matching()
        
        # Test 5: Discord notifications
        print("\n💬 TEST 5: Discord Notification Format")
        test_results['discord_notifications'] = await self.test_discord_notification_format()
        
        # Final results
        print("\n" + "=" * 70)
        print("🎯 CLEAN SYSTEM TEST RESULTS")
        print("=" * 70)
        
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        for test_name, passed in test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status:10} {test_name.replace('_', ' ').title()}")
        
        print("=" * 70)
        print(f"TOTAL: {passed_tests} PASSED, {total_tests - passed_tests} FAILED")
        
        if passed_tests == total_tests:
            print("✅ ALL TESTS PASSED - CLEAN SYSTEM READY FOR DEPLOYMENT")
        elif passed_tests >= 4:
            print("⚠️ MOSTLY WORKING - System functional with minor issues")
        else:
            print("❌ SYSTEM NEEDS ATTENTION - Critical issues detected")
        
        return test_results

async def main():
    """Main test execution"""
    tester = CleanSystemTester()
    await tester.run_all_clean_tests()

if __name__ == "__main__":
    asyncio.run(main())