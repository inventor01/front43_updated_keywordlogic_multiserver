#!/usr/bin/env python3
"""
Force Retry Scenario - Creates tokens that will actually need retries
"""

import time
import logging
from fixed_dual_table_processor import FixedDualTableProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_retry_test_tokens():
    """Create several test tokens that will demonstrate retry functionality"""
    print("🔧 CREATING RETRY TEST TOKENS")
    print("=" * 60)
    
    processor = FixedDualTableProcessor()
    
    # Create tokens with addresses that won't resolve easily
    test_tokens = [
        {
            'address': 'FAKE1234567890ABCDEF1234567890ABCDEF123456',
            'name': 'Unnamed Token FAKE123',
            'symbol': 'FAKE1',
            'status': 'name_pending'
        },
        {
            'address': 'INVALID9876543210FEDCBA9876543210FEDCBA987654',
            'name': 'Unnamed Token INVALID',
            'symbol': 'INV1',
            'status': 'api_timeout'
        },
        {
            'address': 'RETRY5555666677778888999900001111222233334444',
            'name': 'Unnamed Token RETRY555',
            'symbol': 'RET1',
            'status': 'name_pending'
        },
        {
            'address': 'DEMO1111222233334444555566667777888899990000',
            'name': 'Unnamed Token DEMO111',
            'symbol': 'DEMO',
            'status': 'resolution_failed'
        }
    ]
    
    created_count = 0
    
    for token in test_tokens:
        print(f"\n📝 Creating: {token['name']}")
        
        token_id = processor.insert_fallback_token(
            contract_address=token['address'],
            token_name=token['name'],
            symbol=token['symbol'],
            processing_status=token['status'],
            error_message=f"Test token for retry demonstration - {token['status']}"
        )
        
        if token_id:
            print(f"   ✅ Created with ID: {token_id}")
            created_count += 1
        else:
            print(f"   ❌ Failed to create")
    
    print(f"\n📊 SUMMARY: {created_count}/{len(test_tokens)} test tokens created")
    
    # Now force some retry increments
    print(f"\n🔄 FORCING RETRY INCREMENTS")
    print("-" * 40)
    
    for token in test_tokens[:2]:  # Only increment first 2 tokens
        print(f"\n🎯 Forcing retries for: {token['name']}")
        
        for retry_num in range(1, 4):
            success = processor.update_retry_count(token['address'], 'fallback_processing_coins')
            if success:
                print(f"   ✅ Retry #{retry_num} recorded")
            else:
                print(f"   ❌ Failed to record retry #{retry_num}")
            time.sleep(0.5)
    
    # Show final status
    print(f"\n📋 FINAL STATUS OF TEST TOKENS:")
    print("-" * 50)
    
    fallback_tokens = processor.get_fallback_tokens(limit=20)
    
    for token in fallback_tokens:
        # Check if this is one of our test tokens
        if any(test['address'] == token[0] for test in test_tokens):
            print(f"\n📌 {token[1]}")
            print(f"   Address: {token[0][:20]}...")
            print(f"   Retry Count: {token[3] if len(token) > 3 else 'N/A'}")
            print(f"   Status: {token[6] if len(token) > 6 else 'N/A'}")
            print(f"   Last Retry: {token[7] if len(token) > 7 else 'N/A'}")
    
    print(f"\n" + "=" * 60)
    print("🎯 TEST TOKENS CREATED AND READY")
    print("Now check your Railway dashboard - you should see retry counts!")
    print("These test tokens will show increasing retry counts over time.")
    print("=" * 60)

def clean_test_tokens():
    """Clean up test tokens"""
    print("🗑️ CLEANING TEST TOKENS")
    
    processor = FixedDualTableProcessor()
    
    test_addresses = [
        'FAKE1234567890ABCDEF1234567890ABCDEF123456',
        'INVALID9876543210FEDCBA9876543210FEDCBA987654',
        'RETRY5555666677778888999900001111222233334444',
        'DEMO1111222233334444555566667777888899990000'
    ]
    
    try:
        conn = processor.get_db_connection()
        cursor = conn.cursor()
        
        for address in test_addresses:
            cursor.execute("DELETE FROM fallback_processing_coins WHERE contract_address = %s", (address,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Test tokens cleaned up")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean_test_tokens()
    else:
        create_retry_test_tokens()
        print("\nTo clean up test tokens later, run:")
        print("python force_retry_scenario.py clean")