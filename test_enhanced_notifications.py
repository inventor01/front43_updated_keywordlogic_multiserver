#!/usr/bin/env python3
"""
Test the enhanced notification system with duplicate prevention
"""

import logging
from enhanced_notification_system import enhanced_notifier
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_notifications():
    """Test the enhanced notification system"""
    
    logger.info("🧪 TESTING ENHANCED NOTIFICATION SYSTEM")
    logger.info("=" * 60)
    
    # Test token data
    test_token = {
        'address': 'TEST_7xTALTyqbwK9QddAcvbEgfqfk6rSVP2x5QrKYhfJbonk',
        'name': 'Enhanced Test Token',
        'symbol': 'ENHANCED',
        'created_timestamp': time.time(),
        'matched_keyword': 'test'
    }
    
    # Test 1: First notification (should succeed)
    logger.info("🎯 TEST 1: First notification (should succeed)")
    result1 = enhanced_notifier.send_enhanced_token_notification(test_token, 'test')
    logger.info(f"   Result: {'✅ SUCCESS' if result1 else '❌ FAILED'}")
    
    time.sleep(2)
    
    # Test 2: Duplicate notification (should be prevented)
    logger.info("🎯 TEST 2: Duplicate notification (should be prevented)")
    result2 = enhanced_notifier.send_enhanced_token_notification(test_token, 'test')
    logger.info(f"   Result: {'✅ DUPLICATE PREVENTED' if not result2 else '❌ DUPLICATE SENT'}")
    
    # Test 3: Check notification stats
    logger.info("🎯 TEST 3: Notification statistics")
    stats = enhanced_notifier.get_notification_stats()
    logger.info(f"   Today: {stats.get('today', 0)} notifications")
    logger.info(f"   This week: {stats.get('week', 0)} notifications")
    logger.info(f"   Recent: {stats.get('recent_token', 'None')}")
    
    # Test 4: Different token (should succeed)
    logger.info("🎯 TEST 4: Different token (should succeed)")
    test_token2 = {
        'address': 'TEST_ABC123xyz789DEFghijklmnop456QRSTuvwxyz',
        'name': 'Another Test Token',
        'symbol': 'ATT',
        'created_timestamp': time.time(),
        'social_links': [
            'https://x.com/testtoken',
            'https://t.me/testtoken'
        ]
    }
    result4 = enhanced_notifier.send_enhanced_token_notification(test_token2, 'another')
    logger.info(f"   Result: {'✅ SUCCESS' if result4 else '❌ FAILED'}")
    
    # Test 5: Blocked token (should be blocked)
    logger.info("🎯 TEST 5: Blocked token (should be blocked)")
    blocked_token = {
        'address': 'EK7Ko9zmrfanDz98UnbWB9zkDPFV3Mcpx84t1DS2bonk',  # From blocked list
        'name': 'Blocked Token',
        'symbol': 'BLOCKED',
        'created_timestamp': time.time()
    }
    result5 = enhanced_notifier.send_enhanced_token_notification(blocked_token)
    logger.info(f"   Result: {'✅ BLOCKED CORRECTLY' if not result5 else '❌ SHOULD BE BLOCKED'}")
    
    logger.info("=" * 60)
    logger.info("🎉 ENHANCED NOTIFICATION SYSTEM TEST COMPLETE")

if __name__ == "__main__":
    test_enhanced_notifications()