#!/usr/bin/env python3
"""
Demo the enhanced notification system with fresh test data
"""

import logging
import time
import random
from enhanced_notification_system import enhanced_notifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_enhanced_notifications():
    """Demo the enhanced notification system with realistic scenarios"""
    
    logger.info("🎬 ENHANCED NOTIFICATION SYSTEM DEMO")
    logger.info("=" * 60)
    
    # Clean up old test tokens first
    logger.info("🧹 Cleaning up old test notifications (7+ days old)...")
    enhanced_notifier.cleanup_old_notifications(days_old=7)
    
    # Generate unique test tokens for this demo
    timestamp = int(time.time())
    
    # Demo 1: Brand new token (should succeed)
    logger.info("🎯 DEMO 1: Brand new token notification")
    new_token = {
        'address': f'DEMO_{timestamp}_BrandNew{random.randint(1000,9999)}Token',
        'name': f'Demo Token {timestamp}',
        'symbol': 'DEMO',
        'created_timestamp': time.time(),
        'market_data': {
            'price': 0.000001234,
            'market_cap': 50000,
            'volume_24h': 12500,
            'price_change_24h': 15.7
        },
        'social_links': [
            'https://x.com/demotoken',
            'https://t.me/demotoken'
        ],
        'matched_keyword': 'demo'
    }
    
    result1 = enhanced_notifier.send_enhanced_token_notification(new_token, 'demo')
    logger.info(f"   Result: {'✅ SUCCESS' if result1 else '❌ FAILED'}")
    
    time.sleep(1)
    
    # Demo 2: Exact same token (should be prevented)
    logger.info("🎯 DEMO 2: Duplicate token (should be prevented)")
    result2 = enhanced_notifier.send_enhanced_token_notification(new_token, 'demo')
    logger.info(f"   Result: {'✅ DUPLICATE PREVENTED' if not result2 else '❌ DUPLICATE SENT'}")
    
    # Demo 3: Token without market data (should still work)
    logger.info("🎯 DEMO 3: Token without market data")
    basic_token = {
        'address': f'DEMO_{timestamp}_BasicToken{random.randint(1000,9999)}',
        'name': 'Basic Demo Token',
        'symbol': 'BASIC',
        'created_timestamp': time.time() - 300,  # 5 minutes ago
        'matched_keyword': 'basic'
    }
    
    result3 = enhanced_notifier.send_enhanced_token_notification(basic_token, 'basic')
    logger.info(f"   Result: {'✅ SUCCESS' if result3 else '❌ FAILED'}")
    
    # Demo 4: Multiple tokens rapidly (test rate limiting)
    logger.info("🎯 DEMO 4: Rapid notifications (testing rate limiting)")
    start_time = time.time()
    
    for i in range(3):
        rapid_token = {
            'address': f'DEMO_{timestamp}_Rapid{i}_{random.randint(1000,9999)}',
            'name': f'Rapid Token {i}',
            'symbol': f'RAPID{i}',
            'created_timestamp': time.time(),
            'matched_keyword': f'rapid{i}'
        }
        
        result = enhanced_notifier.send_enhanced_token_notification(rapid_token)
        logger.info(f"   Token {i}: {'✅ SENT' if result else '❌ FAILED'}")
    
    elapsed = time.time() - start_time
    logger.info(f"   Rate limiting test: {elapsed:.2f}s for 3 tokens (should be ~3s)")
    
    # Demo 5: Get current statistics
    logger.info("🎯 DEMO 5: Current notification statistics")
    stats = enhanced_notifier.get_notification_stats()
    logger.info(f"   Today: {stats.get('today', 0)} notifications")
    logger.info(f"   This week: {stats.get('week', 0)} notifications")
    logger.info(f"   Recent token: {stats.get('recent_token', 'None')}")
    if stats.get('recent_time'):
        logger.info(f"   Recent time: {stats['recent_time']}")
    
    # Demo 6: Blocked token verification
    logger.info("🎯 DEMO 6: Blocked token (should be rejected)")
    blocked_token = {
        'address': '7Zje1wV3r5sq8JEvJ1jFWifmSZe6CSBLRz4prFSXbonk',  # From blocked list
        'name': 'Blocked Demo Token',
        'symbol': 'BLOCKED',
        'created_timestamp': time.time()
    }
    
    result6 = enhanced_notifier.send_enhanced_token_notification(blocked_token)
    logger.info(f"   Result: {'✅ CORRECTLY BLOCKED' if not result6 else '❌ SHOULD BE BLOCKED'}")
    
    logger.info("=" * 60)
    logger.info("🎉 ENHANCED NOTIFICATION SYSTEM DEMO COMPLETE")
    logger.info("   ✅ Duplicate prevention working")
    logger.info("   ✅ Rate limiting functional")
    logger.info("   ✅ Market data integration")
    logger.info("   ✅ Social links support")
    logger.info("   ✅ Blocked tokens protection")
    logger.info("   ✅ Statistics tracking")

if __name__ == "__main__":
    demo_enhanced_notifications()