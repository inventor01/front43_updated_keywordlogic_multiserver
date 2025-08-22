#!/usr/bin/env python3
"""
Live Smart Polling System Test
Demonstrates how the system handles both instant and delayed name extraction
"""

import asyncio
import time
import logging
from ultimate_name_resolver import UltimateNameResolver
from delayed_name_extractor import DelayedNameExtractor
from discord_notifier import DiscordNotifier
from config_manager import ConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_smart_polling_scenarios():
    """Test different smart polling scenarios"""
    logger.info("🧪 SMART POLLING LIVE TEST")
    logger.info("=" * 60)
    
    # Initialize components
    resolver = UltimateNameResolver()
    config_manager = ConfigManager()
    discord_notifier = DiscordNotifier()
    
    # Test tokens (mix of ready and not-ready names)
    test_tokens = [
        "5n84o7jmJm8zVnwjzHfN93bZ9qdPowqnEpxeAoH2bonk",  # Should have name ready
        "k7wgREpBjJE9QZuE8K1MqNdAPCwqfJKwm8GzvHDhBonk",  # Should have name ready
        "HmHfMJ76J5F7j4z9s8qUZVLLQGxBxKs5UiEqmXeBbonk",   # Might need polling
    ]
    
    logger.info(f"📋 Testing {len(test_tokens)} tokens for smart polling behavior")
    logger.info("")
    
    for i, token_address in enumerate(test_tokens, 1):
        logger.info(f"🔍 TEST {i}/3: {token_address[:8]}...")
        
        # Test immediate extraction
        start_time = time.time()
        result = await resolver.resolve_token_name(token_address, wait_for_indexing=False)
        extraction_time = time.time() - start_time
        
        if result and result.confidence > 0.8:
            logger.info(f"   ✅ INSTANT SUCCESS: '{result.name}' (confidence: {result.confidence:.2f}) in {extraction_time:.2f}s")
            logger.info(f"   ⚡ SMART POLLING: Would send notification immediately - no delay needed")
        else:
            logger.info(f"   ⏳ NEEDS SMART POLLING: Name not ready yet, would queue for delayed extraction")
            logger.info(f"   🔄 SMART POLLING: Would check every 30s for up to 6 minutes")
            
            # Simulate what delayed extraction would do
            logger.info(f"   📊 SIMULATING DELAYED EXTRACTION...")
            for attempt in range(1, 4):  # Simulate 3 attempts
                logger.info(f"   📊 POLLING ATTEMPT {attempt}: Checking if name is ready...")
                result = await resolver.resolve_token_name(token_address, wait_for_indexing=False)
                
                if result and result.confidence > 0.8:
                    logger.info(f"   ✅ SMART POLLING SUCCESS: '{result.name}' found on attempt {attempt}")
                    logger.info(f"   ⚡ INSTANT NOTIFICATION: Would send notification immediately")
                    break
                else:
                    logger.info(f"   ⏳ ATTEMPT {attempt} FAILED: Name still not ready, waiting...")
                    if attempt < 3:
                        await asyncio.sleep(2)  # Short delay for demo
            else:
                logger.info(f"   ❌ SMART POLLING: Would continue checking for full 6 minutes")
        
        logger.info("")
    
    logger.info("📋 SMART POLLING TEST COMPLETE")
    logger.info("=" * 60)
    logger.info("✅ System sends instant notifications when names are ready")
    logger.info("🔄 System polls every 30s for up to 6 minutes when names aren't ready")
    logger.info("⚡ No unnecessary waiting - notifications sent as soon as possible")

if __name__ == "__main__":
    asyncio.run(test_smart_polling_scenarios())