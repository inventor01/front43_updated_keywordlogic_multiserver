#!/usr/bin/env python3
"""
Test the background service to ensure it's incrementing retry counts properly
"""

import asyncio
import logging
from enhanced_retry_background_service import EnhancedRetryBackgroundService
from fixed_dual_table_processor import FixedDualTableProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_background_service():
    """Test the background retry service"""
    print("🧪 TESTING BACKGROUND RETRY SERVICE")
    print("=" * 60)
    
    processor = FixedDualTableProcessor()
    service = EnhancedRetryBackgroundService(retry_interval=10)  # 10 second intervals for testing
    
    # Check current tokens
    print("📋 Current fallback tokens:")
    tokens = processor.get_fallback_tokens(limit=10)
    for i, token in enumerate(tokens):
        retry_count = token[3] if len(token) > 3 else 0
        print(f"   {i+1}. {token[1][:40]}... | Retry: {retry_count}")
    
    if not tokens:
        print("   No fallback tokens found - creating test token...")
        
        # Create a test token
        test_id = processor.insert_fallback_token(
            contract_address="BACKGROUND_TEST_" + str(asyncio.get_event_loop().time()),
            token_name="Background Test Token",
            symbol="BGT",
            processing_status='name_pending',
            error_message='Background service test'
        )
        
        if test_id:
            print(f"   ✅ Created test token with ID: {test_id}")
        else:
            print("   ❌ Failed to create test token")
            return
    
    # Run one processing cycle
    print("\n🔄 Running background service cycle...")
    await service.process_retry_cycle()
    
    # Check updated tokens
    print("\n📋 After background processing:")
    updated_tokens = processor.get_fallback_tokens(limit=10)
    for i, token in enumerate(updated_tokens):
        retry_count = token[3] if len(token) > 3 else 0
        print(f"   {i+1}. {token[1][:40]}... | Retry: {retry_count}")
    
    print("\n" + "=" * 60)
    print("🧪 BACKGROUND SERVICE TEST COMPLETED")

if __name__ == "__main__":
    asyncio.run(test_background_service())