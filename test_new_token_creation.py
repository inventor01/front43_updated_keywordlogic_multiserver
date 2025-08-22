#!/usr/bin/env python3
"""
Test creating new fallback tokens to verify they start with retry_count = 1
"""

import os
import time
from fixed_dual_table_processor import FixedDualTableProcessor

def test_new_token_creation():
    """Test that new fallback tokens start with retry_count = 1"""
    print("🧪 Testing New Token Creation with Retry Count")
    print("=" * 60)
    
    processor = FixedDualTableProcessor()
    
    # Create a test token with unique contract address
    test_address = f"TEST_RETRY_VERIFICATION_{int(time.time())}"
    token_name = "Unnamed Token RETRY_TEST"
    
    print(f"📝 Creating test token: {token_name}")
    print(f"   Contract: {test_address}")
    
    # Insert new fallback token
    result = processor.insert_fallback_token(
        contract_address=test_address,
        token_name=token_name,
        symbol="TEST",
        processing_status="name_pending"
    )
    
    if result:
        print(f"✅ Token created with ID: {result}")
        
        # Check the retry count
        tokens = processor.get_fallback_tokens(limit=1)
        
        # Look for our specific token
        for token in tokens:
            if token[0] == test_address:
                retry_count = token[3] if len(token) > 3 else "NOT_FOUND"
                print(f"🔍 Found token in database:")
                print(f"   Name: {token[1]}")
                print(f"   Retry Count: {retry_count}")
                
                if retry_count == 1:
                    print("✅ SUCCESS: New token starts with retry_count = 1")
                elif retry_count == 0:
                    print("❌ PROBLEM: New token starts with retry_count = 0")
                    print("   This is why new tokens don't have at least one retry")
                else:
                    print(f"⚠️ UNEXPECTED: retry_count = {retry_count}")
                
                break
        else:
            print("❌ Could not find the test token in fallback table")
    
    else:
        print("❌ Failed to create test token")
    
    print("\n" + "=" * 60)
    print("Test completed")

if __name__ == "__main__":
    test_new_token_creation()