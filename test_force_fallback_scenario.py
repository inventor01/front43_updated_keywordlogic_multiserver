#!/usr/bin/env python3
"""
Force fallback scenarios to test the fallback table functionality
"""

import logging
from updated_production_server import UpdatedProductionServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_force_fallback_scenarios():
    """Create scenarios that force tokens into the fallback table"""
    
    server = UpdatedProductionServer()
    
    # Test scenarios that should trigger fallback storage
    fallback_scenarios = [
        {
            'name': 'API Timeout Token',
            'address': 'So11111111111111111111111111111111111111112',  # Real SOL address
            'name_status': 'fallback',
            'api_failed': True,
            'error_message': 'DexScreener API timeout after 10 seconds',
            'blockchain_age': 25.5
        },
        {
            'name': 'Network Error Token',
            'address': '7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU',  # Real SAMO address
            'extraction_failed': True,
            'error': 'Connection refused - network unavailable',
            'blockchain_age': 18.2
        },
        {
            'name': 'Rate Limited Token',
            'address': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # Real USDC address
            'name': 'Rate Limited Token Processing',
            'api_failed': True,
            'error_message': 'DexScreener rate limit exceeded - retry in 60 seconds',
            'blockchain_age': 12.8
        }
    ]
    
    logger.info("🧪 FORCING FALLBACK SCENARIOS")
    logger.info("=" * 50)
    
    for i, scenario in enumerate(fallback_scenarios, 1):
        logger.info(f"🔥 Forcing scenario {i}: {scenario['name']}")
        
        # Create token data that matches fallback conditions
        token_data = {
            'name': scenario['name'],
            'address': scenario['address'],
            'blockchain_age': scenario['blockchain_age'],
            'name_status': scenario.get('name_status'),
            'api_failed': scenario.get('api_failed', False),
            'extraction_failed': scenario.get('extraction_failed', False),
            'error': scenario.get('error'),
            'error_message': scenario.get('error_message')
        }
        
        # Force through fallback handler
        server.handle_new_token_with_fallback([token_data])
        logger.info(f"✅ Scenario {i} processed")
    
    # Check results
    stats = server.token_processor.get_system_stats()
    logger.info("=" * 50)
    logger.info("📊 AFTER FORCED FALLBACK SCENARIOS:")
    logger.info(f"   Detected tokens: {stats['detected_tokens']}")
    logger.info(f"   Pending tokens: {stats['pending_tokens']}")
    logger.info(f"   Fallback tokens: {stats['fallback_tokens']}")
    
    # Show fallback tokens
    fallback_tokens = server.token_processor.get_fallback_tokens(limit=10)
    logger.info("=" * 50)
    logger.info("🔄 TOKENS IN FALLBACK TABLE:")
    
    if fallback_tokens:
        for token in fallback_tokens:
            logger.info(f"   📝 {token[0][:15]}... | {token[1][:30]}... | Status: {token[6] if len(token) > 6 else 'unknown'}")
    else:
        logger.warning("❌ No tokens found in fallback table!")
    
    return len(fallback_tokens)

if __name__ == "__main__":
    import os
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL required")
        exit(1)
    
    fallback_count = test_force_fallback_scenarios()
    
    if fallback_count > 0:
        print(f"\n🎉 SUCCESS: {fallback_count} tokens now in fallback table")
        print("✅ Fallback system is working correctly")
    else:
        print("\n❌ ISSUE: Fallback table still empty after forced scenarios")
        print("💡 Need to check fallback routing logic")