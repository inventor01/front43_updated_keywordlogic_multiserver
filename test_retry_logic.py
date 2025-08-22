#!/usr/bin/env python3
"""
Test retry logic to ensure fallback tokens show increasing retry counts
"""

import time
import logging
from fixed_dual_table_processor import FixedDualTableProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_retry_logic():
    """Test that retry counts increment properly"""
    print("🧪 TESTING RETRY LOGIC")
    print("=" * 50)
    
    processor = FixedDualTableProcessor()
    
    # Create test token with unnamed pattern
    test_token_address = "TEST123TokenAddress456ForRetryTest"
    test_token_name = "Unnamed Token TEST123"
    
    print(f"📝 Creating test token: {test_token_name}")
    
    # Insert into fallback table
    token_id = processor.insert_fallback_token(
        contract_address=test_token_address,
        token_name=test_token_name,
        symbol="TEST",
        processing_status='name_pending',
        error_message='Test token for retry logic'
    )
    
    if token_id:
        print(f"✅ Test token inserted with ID: {token_id}")
        
        # Test multiple retry increments
        for i in range(1, 4):
            print(f"\n🔄 Testing retry #{i}")
            
            # Get current retry count
            fallback_tokens = processor.get_fallback_tokens(limit=1)
            if fallback_tokens:
                for token in fallback_tokens:
                    if token[0] == test_token_address:
                        current_retry_count = token[3] if len(token) > 3 else 0
                        print(f"   Current retry count: {current_retry_count}")
            
            # Update retry count
            success = processor.update_retry_count(test_token_address, 'fallback_processing_coins')
            
            if success:
                print(f"   ✅ Retry count updated successfully")
            else:
                print(f"   ❌ Failed to update retry count")
            
            time.sleep(1)
        
        # Check final retry count
        print(f"\n📊 FINAL RETRY STATUS:")
        fallback_tokens = processor.get_fallback_tokens(limit=10)
        
        for token in fallback_tokens:
            if token[0] == test_token_address:
                print(f"   Token: {token[1]}")
                print(f"   Address: {token[0][:20]}...")
                print(f"   Retry Count: {token[3] if len(token) > 3 else 'N/A'}")
                print(f"   Status: {token[6] if len(token) > 6 else 'N/A'}")
        
        # Clean up test token
        try:
            conn = processor.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM fallback_processing_coins WHERE contract_address = %s", (test_token_address,))
            conn.commit()
            cursor.close()
            conn.close()
            print(f"\n🗑️ Test token cleaned up")
        except Exception as e:
            print(f"\n⚠️ Cleanup failed: {e}")
    
    else:
        print("❌ Failed to insert test token")
    
    print("\n" + "=" * 50)
    print("🧪 RETRY LOGIC TEST COMPLETED")

if __name__ == "__main__":
    test_retry_logic()