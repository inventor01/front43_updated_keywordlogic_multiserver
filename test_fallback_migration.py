#!/usr/bin/env python3
"""
Test and fix fallback token migration
"""

import logging
from fixed_dual_table_processor import FixedDualTableProcessor
from dexscreener_70_percent_extractor import DexScreener70PercentExtractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fallback_migration():
    """Test migrating fallback tokens that have resolvable names"""
    print("🔍 TESTING FALLBACK TOKEN MIGRATION")
    print("=" * 60)
    
    processor = FixedDualTableProcessor()
    extractor = DexScreener70PercentExtractor()
    
    # Get current fallback tokens
    fallback_tokens = processor.get_fallback_tokens(limit=10)
    
    print(f"📋 Found {len(fallback_tokens)} tokens in fallback processing")
    
    if not fallback_tokens:
        print("📭 No fallback tokens to process")
        return
    
    migrated_count = 0
    
    for token in fallback_tokens:
        contract_address = token[0]
        current_name = token[1]
        
        print(f"\n🔍 Testing: {current_name} ({contract_address[:10]}...)")
        
        # Skip test addresses
        if contract_address.startswith(('TEST_', 'DEMO', 'RETRY', 'INVALID', 'FAKE', 'RAILWAY')):
            print(f"⏭️ Skipping test address: {contract_address}")
            continue
        
        try:
            # Try to extract real name using DexScreener
            result = extractor.extract_name_with_confidence(contract_address)
            
            if result['success'] and result['name'] and not result['name'].startswith('Unnamed Token'):
                resolved_name = result['name']
                print(f"✅ Resolved name: {resolved_name}")
                
                # Migrate to detected_tokens
                success = processor.migrate_fallback_to_detected(
                    contract_address=contract_address,
                    token_name=resolved_name,
                    symbol=result.get('symbol'),
                    matched_keywords=[]
                )
                
                if success:
                    migrated_count += 1
                    print(f"✅ Migration successful: {resolved_name}")
                else:
                    print(f"❌ Migration failed for: {resolved_name}")
            else:
                print(f"⚠️ Name resolution failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Error processing {contract_address[:10]}...: {e}")
    
    print(f"\n📊 MIGRATION SUMMARY")
    print(f"   Total processed: {len([t for t in fallback_tokens if not t[0].startswith(('TEST_', 'DEMO', 'RETRY', 'INVALID', 'FAKE', 'RAILWAY'))])}")
    print(f"   Successfully migrated: {migrated_count}")
    
    # Check migration status
    import psycopg2
    import os
    
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) as total_fallback, 
               COUNT(CASE WHEN migrated_to_detected = true THEN 1 END) as migrated
        FROM fallback_processing_coins
    """)
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    print(f"📈 CURRENT STATUS:")
    print(f"   Total fallback tokens: {result[0]}")
    print(f"   Migrated to detected: {result[1]}")
    
    print("\n" + "=" * 60)
    print("MIGRATION TEST COMPLETE")

if __name__ == "__main__":
    test_fallback_migration()