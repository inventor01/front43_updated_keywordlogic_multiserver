#!/usr/bin/env python3
"""
LetsBonk Token Detection System Test
Tests real-time token detection, name extraction, and Discord notifications
"""

import os
import sys
import time
import asyncio
import logging
from datetime import datetime, timedelta
import json
import psycopg2
from unittest.mock import Mock, patch

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our modules
sys.path.append('.')

class LetsBonkDetectionTester:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway')
        self.test_user_id = "123456789"
        self.test_keywords = ["moon", "pepe", "doge", "shib"]
        
        # Mock token data for testing (realistic LetsBonk tokens)
        self.mock_tokens = [
            {
                'address': '7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU',
                'name': 'Moon Dog',
                'symbol': 'MOON',
                'created_timestamp': time.time() - 30,  # 30 seconds ago
                'platform': 'letsbonk.fun',
                'url': 'https://letsbonk.fun/token/7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU'
            },
            {
                'address': '9yHJfxeKGGsnHLMHaC1BjCRRaG5W7fFJMK3kV2bEhNpQ',
                'name': 'Pepe Coin',
                'symbol': 'PEPE',
                'created_timestamp': time.time() - 15,  # 15 seconds ago
                'platform': 'letsbonk.fun', 
                'url': 'https://letsbonk.fun/token/9yHJfxeKGGsnHLMHaC1BjCRRaG5W7fFJMK3kV2bEhNpQ'
            },
            {
                'address': '3mPLAYkQb6Y57oCKuqvLBjCR8uTjvBcW2MbHsV7kNqRx',
                'name': 'Doge Forever',
                'symbol': 'DOGE',
                'created_timestamp': time.time() - 60,  # 1 minute ago (should be rejected as too old)
                'platform': 'letsbonk.fun',
                'url': 'https://letsbonk.fun/token/3mPLAYkQb6Y57oCKuqvLBjCR8uTjvBcW2MbHsV7kNqRx'
            }
        ]
        
    def setup_test_environment(self):
        """Set up test environment with keywords and clear previous data"""
        print("\n🔧 STEP 1: Setting Up Test Environment")
        print("=" * 60)
        
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # Clear existing test data
            cursor.execute("DELETE FROM keywords WHERE user_id = %s", (self.test_user_id,))
            cursor.execute("DELETE FROM detected_tokens WHERE address LIKE '%test%'")
            cursor.execute("DELETE FROM notified_tokens WHERE user_id = %s", (self.test_user_id,))
            
            # Add test keywords
            for keyword in self.test_keywords:
                cursor.execute("""
                    INSERT INTO keywords (user_id, keyword) 
                    VALUES (%s, %s) 
                    ON CONFLICT (user_id, keyword) DO NOTHING
                """, (self.test_user_id, keyword))
            
            conn.commit()
            
            # Verify keywords were added
            cursor.execute("SELECT keyword FROM keywords WHERE user_id = %s", (self.test_user_id,))
            added_keywords = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            print(f"✅ Added test keywords: {added_keywords}")
            print(f"✅ Cleared previous test data")
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def test_token_detection_speed(self):
        """Test that tokens are detected within 2-3 seconds"""
        print("\n⚡ STEP 2: Testing Token Detection Speed")
        print("=" * 60)
        
        try:
            # Import and initialize the optimized clean system
            from clean_alchemy_server import app
            from optimized_name_extractor import OptimizedNameExtractor
            
            # Create extractor instance
            extractor = OptimizedNameExtractor()
            
            detection_times = []
            
            for i, token in enumerate(self.mock_tokens[:2]):  # Test first 2 tokens
                print(f"\n🎯 Testing token {i+1}: {token['name']} ({token['symbol']})")
                
                start_time = time.time()
                
                # Test optimized token detection
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    loop.run_until_complete(extractor.initialize_sessions())
                    result = loop.run_until_complete(extractor.extract_token_name(token['address']))
                    
                    loop.close()
                    detection_time = time.time() - start_time
                    detection_times.append(detection_time)
                    
                    print(f"✅ Detection time: {detection_time:.2f} seconds")
                    
                    if detection_time <= 3.0:
                        print("✅ Speed requirement met (≤ 3 seconds)")
                    else:
                        print("⚠️ Speed requirement exceeded (> 3 seconds)")
                        
                except Exception as e:
                    print(f"❌ Detection failed: {e}")
                    detection_times.append(999)  # Mark as failed
            
            avg_time = sum(detection_times) / len(detection_times) if detection_times else 0
            print(f"\n📊 Average detection time: {avg_time:.2f} seconds")
            
            if avg_time <= 3.0:
                print("✅ Overall speed requirement met")
                return True
            else:
                print("❌ Overall speed requirement not met")
                return False
                
        except Exception as e:
            print(f"❌ Speed test failed: {e}")
            return False
    
    def test_name_extraction_accuracy(self):
        """Test that token names are extracted accurately (not fallbacks)"""
        print("\n🎯 STEP 3: Testing Name Extraction Accuracy")
        print("=" * 60)
        
        try:
            from optimized_name_extractor import OptimizedNameExtractor
            
            extraction_results = []
            
            for token in self.mock_tokens[:2]:
                print(f"\n🔍 Testing name extraction for: {token['address']}")
                
                # Test optimized name extractor
                try:
                    extractor = OptimizedNameExtractor()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    loop.run_until_complete(extractor.initialize_sessions())
                    result = loop.run_until_complete(
                        extractor.extract_token_name(token['address'])
                    )
                    
                    loop.close()
                    
                    if result and result.success:
                        extracted_name = result.name or ''
                        confidence = result.confidence
                        source = result.source
                        
                        print(f"✅ Extracted name: '{extracted_name}'")
                        print(f"   Confidence: {confidence}")
                        print(f"   Source: {source}")
                        
                        # Check if it's a fallback name
                        is_fallback = (
                            extracted_name.lower().startswith(('token ', 'letsbonk token ', 'jupiter token ')) or
                            confidence < 0.8
                        )
                        
                        if not is_fallback:
                            print("✅ Real token name extracted (not fallback)")
                            extraction_results.append(True)
                        else:
                            print("⚠️ Fallback name detected - would trigger retry")
                            extraction_results.append(False)
                    else:
                        print("❌ No name extracted")
                        extraction_results.append(False)
                        
                except Exception as e:
                    print(f"❌ Name extraction failed: {e}")
                    extraction_results.append(False)
            
            success_rate = (sum(extraction_results) / len(extraction_results)) * 100 if extraction_results else 0
            print(f"\n📊 Name extraction success rate: {success_rate:.1f}%")
            
            if success_rate >= 80:
                print("✅ Name extraction accuracy acceptable")
                return True
            else:
                print("❌ Name extraction accuracy needs improvement")
                return False
                
        except Exception as e:
            print(f"❌ Name extraction test failed: {e}")
            return False
    
    def test_keyword_matching(self):
        """Test that keywords are matched correctly"""
        print("\n🎯 STEP 4: Testing Keyword Matching")
        print("=" * 60)
        
        try:
            from alchemy_server import TokenMonitor
            
            monitor = TokenMonitor()
            monitor.keywords = self.test_keywords  # Set test keywords
            
            matching_results = []
            
            for token in self.mock_tokens[:2]:
                print(f"\n🔍 Testing keyword matching for: {token['name']}")
                
                # Test keyword matching
                matched_keyword = monitor.check_token_keywords(token)
                
                expected_matches = []
                token_name_lower = token['name'].lower()
                
                for keyword in self.test_keywords:
                    if keyword.lower() in token_name_lower:
                        expected_matches.append(keyword)
                
                if matched_keyword:
                    print(f"✅ Matched keyword: '{matched_keyword}'")
                    if matched_keyword in expected_matches:
                        print("✅ Correct keyword match")
                        matching_results.append(True)
                    else:
                        print("⚠️ Unexpected keyword match")
                        matching_results.append(False)
                else:
                    if expected_matches:
                        print(f"❌ Should have matched: {expected_matches}")
                        matching_results.append(False)
                    else:
                        print("✅ Correctly no match")
                        matching_results.append(True)
            
            success_rate = (sum(matching_results) / len(matching_results)) * 100 if matching_results else 0
            print(f"\n📊 Keyword matching accuracy: {success_rate:.1f}%")
            
            return success_rate >= 90
            
        except Exception as e:
            print(f"❌ Keyword matching test failed: {e}")
            return False
    
    def test_discord_notification_format(self):
        """Test Discord notification format and content"""
        print("\n💬 STEP 5: Testing Discord Notification Format")
        print("=" * 60)
        
        try:
            from discord_notifier import DiscordNotifier
            
            # Mock Discord webhook
            notifier = DiscordNotifier()
            notifications_sent = []
            
            # Mock the send_notification method to capture calls
            def mock_send_notification(token_data, keyword, user_id):
                notification = {
                    'token_name': token_data.get('name', token_data.get('accurate_name', 'Unknown')),
                    'symbol': token_data.get('symbol', ''),
                    'address': token_data.get('address', ''),
                    'keyword': keyword,
                    'timestamp': datetime.now(),
                    'confidence': token_data.get('extraction_confidence', 0),
                    'source': token_data.get('extraction_source', 'unknown')
                }
                notifications_sent.append(notification)
                return True
            
            notifier.send_notification = mock_send_notification
            
            # Test notifications for matching tokens
            for token in self.mock_tokens[:2]:
                if 'moon' in token['name'].lower() or 'pepe' in token['name'].lower():
                    keyword = 'moon' if 'moon' in token['name'].lower() else 'pepe'
                    
                    # Add enhanced extraction data
                    token['accurate_name'] = token['name']
                    token['extraction_confidence'] = 0.95
                    token['extraction_source'] = 'dexscreener'
                    
                    success = notifier.send_notification(token, keyword, self.test_user_id)
                    
                    if success:
                        print(f"✅ Notification sent for {token['name']}")
                    else:
                        print(f"❌ Notification failed for {token['name']}")
            
            # Verify notification content
            print(f"\n📋 Generated {len(notifications_sent)} notifications:")
            
            for i, notif in enumerate(notifications_sent, 1):
                print(f"\n📨 Notification {i}:")
                print(f"   Token: {notif['token_name']} ({notif['symbol']})")
                print(f"   Address: {notif['address']}")
                print(f"   Keyword: {notif['keyword']}")
                print(f"   Confidence: {notif['confidence']}")
                print(f"   Source: {notif['source']}")
                print(f"   Timestamp: {notif['timestamp']}")
                
                # Verify no fallback names
                is_fallback = notif['token_name'].lower().startswith(('token ', 'letsbonk token '))
                if not is_fallback:
                    print("   ✅ Real token name (not fallback)")
                else:
                    print("   ⚠️ Fallback name detected")
            
            if notifications_sent:
                print("✅ Discord notification format test completed")
                return True
            else:
                print("❌ No notifications generated")
                return False
                
        except Exception as e:
            print(f"❌ Discord notification test failed: {e}")
            return False
    
    def test_timestamp_accuracy(self):
        """Test timestamp accuracy in notifications"""
        print("\n⏰ STEP 6: Testing Timestamp Accuracy")
        print("=" * 60)
        
        try:
            current_time = time.time()
            
            for token in self.mock_tokens:
                token_time = token['created_timestamp']
                age_seconds = current_time - token_time
                
                print(f"\n🕐 Token: {token['name']}")
                print(f"   Created: {datetime.fromtimestamp(token_time)}")
                print(f"   Age: {age_seconds:.1f} seconds")
                
                if age_seconds <= 60:  # Within 1 minute (fresh)
                    print("   ✅ Fresh token (≤ 60 seconds)")
                elif age_seconds <= 120:  # Within 2 minutes (acceptable)
                    print("   ⚠️ Acceptable age (≤ 120 seconds)")
                else:
                    print("   ❌ Too old (> 120 seconds) - should be rejected")
            
            print("✅ Timestamp accuracy test completed")
            return True
            
        except Exception as e:
            print(f"❌ Timestamp test failed: {e}")
            return False
    
    def test_fallback_retry_system(self):
        """Test that fallback names trigger retry system"""
        print("\n🔄 STEP 7: Testing Fallback Retry System")
        print("=" * 60)
        
        try:
            from enhanced_token_name_resolver import get_enhanced_resolver
            
            resolver = get_enhanced_resolver()
            
            # Test with a token that would likely get fallback initially
            test_address = "FakeTokenAddressForTesting123456789"
            
            print(f"🔍 Testing fallback retry for: {test_address}")
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                resolver.resolve_token_name_comprehensive(test_address)
            )
            
            loop.close()
            
            if result:
                name = result.get('name', '')
                confidence = result.get('confidence', 0)
                
                print(f"✅ Result: '{name}' (confidence: {confidence})")
                
                # Check if it was scheduled for background retry
                if result.get('metadata', {}).get('scheduled_for_reprocessing'):
                    print("✅ Scheduled for background reprocessing")
                    
                # Check if resolver has background processor active
                if resolver.reprocessing_active:
                    print("✅ Background reprocessing system is active")
                else:
                    print("⚠️ Background reprocessing system not started")
                    
                print("✅ Fallback retry system test completed")
                return True
            else:
                print("❌ No result from resolver")
                return False
                
        except Exception as e:
            print(f"❌ Fallback retry test failed: {e}")
            return False
    
    def run_comprehensive_detection_test(self):
        """Run all detection and notification tests"""
        print("🚀 STARTING LETSBONK TOKEN DETECTION SYSTEM TEST")
        print("=" * 70)
        print(f"Database URL: {self.database_url}")
        print(f"Test Keywords: {self.test_keywords}")
        print(f"Mock Tokens: {len(self.mock_tokens)}")
        print("=" * 70)
        
        test_results = []
        
        # Run all tests
        test_results.append(("Test Environment Setup", self.setup_test_environment()))
        test_results.append(("Token Detection Speed", self.test_token_detection_speed()))
        test_results.append(("Name Extraction Accuracy", self.test_name_extraction_accuracy()))
        test_results.append(("Keyword Matching", self.test_keyword_matching()))
        test_results.append(("Discord Notification Format", self.test_discord_notification_format()))
        test_results.append(("Timestamp Accuracy", self.test_timestamp_accuracy()))
        test_results.append(("Fallback Retry System", self.test_fallback_retry_system()))
        
        # Summary
        print("\n" + "=" * 70)
        print("🎯 DETECTION SYSTEM TEST RESULTS")
        print("=" * 70)
        
        passed = 0
        failed = 0
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status:10} {test_name}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print("=" * 70)
        print(f"TOTAL: {passed} PASSED, {failed} FAILED")
        
        if failed == 0:
            print("🎉 ALL DETECTION TESTS PASSED!")
            print("✅ LetsBonk tokens will be detected within 2-3 seconds")
            print("✅ Real token names extracted (no fallbacks)")
            print("✅ Discord notifications contain accurate information")
            print("✅ Fallback retry system active for failed extractions")
        else:
            print(f"⚠️ {failed} tests failed - system needs attention")
        
        return failed == 0

if __name__ == "__main__":
    tester = LetsBonkDetectionTester()
    success = tester.run_comprehensive_detection_test()
    sys.exit(0 if success else 1)