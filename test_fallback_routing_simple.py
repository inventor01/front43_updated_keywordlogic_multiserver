#!/usr/bin/env python3
"""
Simple test to verify fallback routing works correctly
"""

import os
import logging
from fixed_dual_table_processor import FixedDualTableProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fallback_routing():
    """Test that Unnamed Token entries are properly handled"""
    processor = FixedDualTableProcessor()
    
    # Simulate what the updated server logic does
    test_token = {
        'name': 'Unnamed Token DgV5A5',
        'symbol': 'BONK',
        'address': 'DgV5A5qM1jW8Cy8DF5VN84w9dRaJxqZJYc5UmPegtest',
        'blockchain_age': 0.0
    }
    
    logger.info("🧪 Testing fallback routing for Unnamed Token...")
    
    # Test the routing logic
    token_name = test_token.get('name', '')
    
    if token_name.startswith('Unnamed Token'):
        # This should go to fallback_processing_coins
        result = processor.insert_fallback_token(
            contract_address=test_token['address'],
            token_name=test_token['name'],
            symbol=test_token['symbol'],
            blockchain_age_seconds=test_token['blockchain_age'],
            processing_status='name_pending',
            error_message='Token detected with placeholder name - needs accurate name resolution'
        )
        
        if result:
            logger.info(f"✅ SUCCESS: {test_token['name']} routed to fallback_processing_coins")
            
            # Verify it's in the fallback table
            conn = processor.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT token_name, processing_status 
                FROM fallback_processing_coins 
                WHERE contract_address = %s
            ''', (test_token['address'],))
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                logger.info(f"✅ VERIFIED: Found in fallback table - {result[0]} ({result[1]})")
                return True
            else:
                logger.error("❌ NOT FOUND: Token not in fallback table")
                return False
        else:
            logger.error("❌ FAILED: Could not insert into fallback table")
            return False
    else:
        logger.error("❌ LOGIC ERROR: Token should have been detected as Unnamed")
        return False

if __name__ == "__main__":
    success = test_fallback_routing()
    if success:
        logger.info("🎉 Fallback routing test PASSED")
    else:
        logger.error("💥 Fallback routing test FAILED")