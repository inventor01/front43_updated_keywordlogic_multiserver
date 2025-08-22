#!/usr/bin/env python3
"""
Manually increment retry counts for all fallback tokens to demonstrate the feature
"""

import time
from fixed_dual_table_processor import FixedDualTableProcessor

def increment_all_retries():
    """Manually increment retry counts for all fallback tokens"""
    print("🔧 MANUALLY INCREMENTING ALL RETRY COUNTS")
    print("=" * 60)
    
    processor = FixedDualTableProcessor()
    
    # Get all fallback tokens
    tokens = processor.get_fallback_tokens(limit=50)
    
    if not tokens:
        print("❌ No fallback tokens found")
        return
    
    print(f"📋 Found {len(tokens)} fallback tokens")
    print("\n🔄 Before incrementing:")
    for i, token in enumerate(tokens):
        retry_count = token[3] if len(token) > 3 else 0
        print(f"   {i+1}. {token[1][:40]}... | Retry: {retry_count}")
    
    # Increment retry count for each token
    print(f"\n⬆️ Incrementing retry counts...")
    success_count = 0
    
    for token in tokens:
        contract_address = token[0]
        success = processor.update_retry_count(contract_address, 'fallback_processing_coins')
        if success:
            success_count += 1
            print(f"   ✅ Updated {contract_address[:20]}...")
        else:
            print(f"   ❌ Failed {contract_address[:20]}...")
        
        time.sleep(0.2)  # Small delay between updates
    
    # Show results
    print(f"\n📊 Successfully updated: {success_count}/{len(tokens)} tokens")
    
    print(f"\n🔄 After incrementing:")
    updated_tokens = processor.get_fallback_tokens(limit=50)
    for i, token in enumerate(updated_tokens):
        retry_count = token[3] if len(token) > 3 else 0
        print(f"   {i+1}. {token[1][:40]}... | Retry: {retry_count}")
    
    print("\n" + "=" * 60)
    print("✅ MANUAL RETRY INCREMENT COMPLETED")
    print("Check your Railway dashboard - retry counts should now be visible!")

if __name__ == "__main__":
    increment_all_retries()