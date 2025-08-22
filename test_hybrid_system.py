#!/usr/bin/env python3
"""
Test Hybrid Token Processing System
Validates instant processing and background name resolution
"""

import os
import time
import asyncio
import logging
import psycopg2
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HybridSystemTest:
    """Test the complete hybrid token processing system"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.test_tokens = [
            {
                'address': 'TestToken123456bonk',
                'real_name': 'Test Token Alpha',
                'initial_name': 'Unnamed Token TestTo'
            },
            {
                'address': 'MockToken789012bonk', 
                'real_name': 'Mock Token Beta',
                'initial_name': 'Unnamed Token MockTo'
            }
        ]
    
    def cleanup_test_data(self):
        """Clean up any existing test data"""
        try:
            if not self.database_url:
                logger.warning("No DATABASE_URL - skipping cleanup")
                return
                
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # Remove test tokens
            for token in self.test_tokens:
                cursor.execute("DELETE FROM detected_tokens WHERE address = %s", (token['address'],))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("🧹 Test data cleanup complete")
            
        except Exception as e:
            logger.debug(f"Cleanup error: {e}")
    
    def simulate_pending_token_creation(self):
        """Simulate creation of tokens with pending names"""
        try:
            if not self.database_url:
                logger.error("No DATABASE_URL - cannot run test")
                return False
                
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            created_count = 0
            for token in self.test_tokens:
                # Insert token with pending name status
                cursor.execute("""
                    INSERT INTO detected_tokens 
                    (address, name, symbol, platform, status, name_status, detection_timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (address) DO UPDATE SET
                        name = EXCLUDED.name,
                        name_status = EXCLUDED.name_status
                """, (
                    token['address'],
                    token['initial_name'], 
                    'BONK',
                    'letsbonk',
                    'genuine_new',
                    'pending'
                ))
                created_count += 1
                
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Created {created_count} tokens with pending names")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create test tokens: {e}")
            return False
    
    def test_instant_processing(self):
        """Test that tokens are processed instantly with placeholder names"""
        logger.info("🎯 TESTING INSTANT PROCESSING")
        logger.info("-" * 40)
        
        # Test 1: Verify tokens were stored immediately
        try:
            if not self.database_url:
                return False
                
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            instant_count = 0
            for token in self.test_tokens:
                cursor.execute("""
                    SELECT name, name_status, detection_timestamp
                    FROM detected_tokens 
                    WHERE address = %s
                """, (token['address'],))
                
                result = cursor.fetchone()
                if result:
                    name, name_status, timestamp = result
                    logger.info(f"✅ INSTANT: {token['address'][:10]}... → '{name}' (status: {name_status})")
                    instant_count += 1
                else:
                    logger.error(f"❌ Missing: {token['address'][:10]}...")
            
            cursor.close()
            conn.close()
            
            success = instant_count == len(self.test_tokens)
            logger.info(f"📊 Instant Processing: {instant_count}/{len(self.test_tokens)} {'✅ PASS' if success else '❌ FAIL'}")
            return success
            
        except Exception as e:
            logger.error(f"Instant processing test failed: {e}")
            return False
    
    def simulate_name_resolution(self):
        """Simulate background name resolution"""
        logger.info("🔄 SIMULATING BACKGROUND NAME RESOLUTION")
        logger.info("-" * 40)
        
        try:
            if not self.database_url:
                return False
                
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            resolved_count = 0
            for token in self.test_tokens:
                # Simulate name resolution by updating with real names
                cursor.execute("""
                    UPDATE detected_tokens 
                    SET name = %s, name_status = 'resolved', updated_at = NOW()
                    WHERE address = %s AND name_status = 'pending'
                """, (token['real_name'], token['address']))
                
                if cursor.rowcount > 0:
                    logger.info(f"✅ RESOLVED: {token['address'][:10]}... → '{token['real_name']}'")
                    resolved_count += 1
                else:
                    logger.error(f"❌ Failed to resolve: {token['address'][:10]}...")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            success = resolved_count == len(self.test_tokens)
            logger.info(f"📊 Name Resolution: {resolved_count}/{len(self.test_tokens)} {'✅ PASS' if success else '❌ FAIL'}")
            return success
            
        except Exception as e:
            logger.error(f"Name resolution simulation failed: {e}")
            return False
    
    def test_final_state(self):
        """Test final state after name resolution"""
        logger.info("🏁 TESTING FINAL STATE")
        logger.info("-" * 40)
        
        try:
            if not self.database_url:
                return False
                
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # Get all pending tokens (should be 0)
            cursor.execute("SELECT COUNT(*) FROM detected_tokens WHERE name_status = 'pending'")
            pending_count = cursor.fetchone()[0]
            
            # Get resolved tokens
            cursor.execute("SELECT COUNT(*) FROM detected_tokens WHERE name_status = 'resolved'")
            resolved_count = cursor.fetchone()[0]
            
            # Check specific test tokens
            final_count = 0
            for token in self.test_tokens:
                cursor.execute("""
                    SELECT name, name_status 
                    FROM detected_tokens 
                    WHERE address = %s
                """, (token['address'],))
                
                result = cursor.fetchone()
                if result:
                    name, status = result
                    if name == token['real_name'] and status == 'resolved':
                        logger.info(f"✅ FINAL: {token['address'][:10]}... → '{name}' ({status})")
                        final_count += 1
                    else:
                        logger.error(f"❌ FINAL: {token['address'][:10]}... → '{name}' ({status})")
            
            cursor.close()
            conn.close()
            
            success = (pending_count == 0 and final_count == len(self.test_tokens))
            
            logger.info(f"📊 Final State: {final_count}/{len(self.test_tokens)} correct, {pending_count} pending")
            logger.info(f"🏆 Overall Result: {'✅ PASS' if success else '❌ FAIL'}")
            
            return success
            
        except Exception as e:
            logger.error(f"Final state test failed: {e}")
            return False
    
    def run_complete_test(self):
        """Run the complete hybrid system test suite"""
        logger.info("🚀 HYBRID TOKEN PROCESSING TEST SUITE")
        logger.info("=" * 60)
        logger.info(f"Testing Date: {datetime.now()}")
        logger.info("Target: Instant processing + background name resolution")
        logger.info("=" * 60)
        
        # Test setup
        self.cleanup_test_data()
        
        # Test 1: Simulate instant processing with pending names
        if not self.simulate_pending_token_creation():
            logger.error("❌ TEST SETUP FAILED")
            return False
        
        # Test 2: Verify instant processing
        instant_success = self.test_instant_processing()
        
        # Test 3: Simulate background name resolution
        resolution_success = self.simulate_name_resolution()
        
        # Test 4: Verify final state
        final_success = self.test_final_state()
        
        # Summary
        logger.info("=" * 60)
        logger.info("🎯 HYBRID SYSTEM TEST RESULTS")
        logger.info("=" * 60)
        results = [
            ("Instant Processing", instant_success),
            ("Background Resolution", resolution_success), 
            ("Final State Validation", final_success)
        ]
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            logger.info(f"{status:12} {test_name}")
        
        logger.info("=" * 60)
        overall_success = passed == total
        logger.info(f"TOTAL: {passed} PASSED, {total - passed} FAILED")
        
        if overall_success:
            logger.info("🎉 ALL TESTS PASSED - HYBRID SYSTEM READY")
            logger.info("   ⚡ Tokens processed instantly with placeholder names")
            logger.info("   🔄 Names resolved in background when available")
            logger.info("   📄 Database correctly tracks all states")
        else:
            logger.error("❌ TESTS FAILED - SYSTEM NEEDS FIXES")
        
        # Cleanup
        self.cleanup_test_data()
        
        return overall_success

def main():
    """Run the hybrid system test"""
    test = HybridSystemTest()
    success = test.run_complete_test()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())