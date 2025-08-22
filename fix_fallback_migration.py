#!/usr/bin/env python3
"""
Fix fallback token migration by processing stuck tokens
"""

import requests
import logging
import time
from fixed_dual_table_processor import FixedDualTableProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_token_name_dexscreener(contract_address):
    """Get token name from DexScreener API (synchronous)"""
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            pairs = data.get('pairs', [])
            
            if pairs:
                token_info = pairs[0]
                name = token_info.get('baseToken', {}).get('name')
                symbol = token_info.get('baseToken', {}).get('symbol')
                
                if name and not name.startswith('Unnamed'):
                    return {'success': True, 'name': name, 'symbol': symbol}
        
        return {'success': False, 'error': 'No valid name found'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def fix_fallback_migrations():
    """Fix migration issues for fallback tokens"""
    print("🔧 FIXING FALLBACK TOKEN MIGRATIONS")
    print("=" * 60)
    
    processor = FixedDualTableProcessor()
    
    # Get current fallback tokens
    fallback_tokens = processor.get_fallback_tokens(limit=20)
    
    print(f"📋 Found {len(fallback_tokens)} tokens in fallback processing")
    
    if not fallback_tokens:
        print("📭 No fallback tokens to process")
        return
    
    migrated_count = 0
    test_addresses = ['TEST_', 'DEMO', 'RETRY', 'INVALID', 'FAKE', 'RAILWAY']
    
    for token in fallback_tokens:
        contract_address = token[0]
        current_name = token[1]
        
        print(f"\n🔍 Processing: {current_name} ({contract_address[:10]}...)")
        
        # Skip test/demo addresses
        if any(contract_address.startswith(prefix) for prefix in test_addresses):
            print(f"⏭️ Skipping test address")
            continue
        
        try:
            # Try to resolve real name
            result = get_token_name_dexscreener(contract_address)
            
            if result['success'] and result['name']:
                resolved_name = result['name']
                symbol = result.get('symbol', 'UNKNOWN')
                
                print(f"✅ Resolved: {resolved_name}")
                
                # Use the new migration method
                success = processor.migrate_fallback_to_detected(
                    contract_address=contract_address,
                    token_name=resolved_name,
                    symbol=symbol,
                    matched_keywords=[]
                )
                
                if success:
                    migrated_count += 1
                    print(f"✅ Migrated successfully")
                else:
                    print(f"❌ Migration failed")
            else:
                print(f"⚠️ Could not resolve name: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Rate limiting
        time.sleep(1)
    
    print(f"\n📊 MIGRATION RESULTS:")
    print(f"   Successfully migrated: {migrated_count} tokens")
    
    # Check final status
    import psycopg2
    import os
    
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) as total_fallback, 
               COUNT(CASE WHEN migrated_to_detected = true THEN 1 END) as migrated,
               COUNT(CASE WHEN processing_status = 'resolved' THEN 1 END) as resolved
        FROM fallback_processing_coins
    """)
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    print(f"📈 UPDATED STATUS:")
    print(f"   Total fallback tokens: {result[0]}")
    print(f"   Migrated to detected: {result[1]}")
    print(f"   Status = resolved: {result[2]}")
    
    print("\n" + "=" * 60)
    print("MIGRATION FIX COMPLETE")

if __name__ == "__main__":
    fix_fallback_migrations()