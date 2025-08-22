#!/usr/bin/env python3
"""
Test Unnamed Token Routing Fix
Verifies that tokens with "Unnamed Token" names are properly routed to fallback_processing_coins table
"""

import os
import logging
from fixed_dual_table_processor import FixedDualTableProcessor
from updated_production_server import ProductionServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_unnamed_token_routing():
    """Test that Unnamed Token entries go to fallback table"""
    
    # Test token scenarios
    test_tokens = [
        {
            'name': 'Unnamed Token DgV5A5',
            'symbol': 'BONK',
            'address': 'DgV5A5qM1jW8Cy8DF5VN84w9dRaJxqZJYc5UmPegbonk',
            'name_status': 'pending',
            'blockchain_age': 0.0
        },
        {
            'name': 'Unnamed Token ABC123',
            'symbol': 'BONK', 
            'address': 'ABC123qM1jW8Cy8DF5VN84w9dRaJxqZJYc5UmPegtest',
            'name_status': 'pending',
            'blockchain_age': 5.2
        }
    ]
    
    # Initialize server
    server = ProductionServer()
    processor = FixedDualTableProcessor()
    
    logger.info("🧪 Testing Unnamed Token Routing to Fallback Table")
    
    # Check initial fallback count
    conn = processor.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM fallback_processing_coins')
    initial_count = cursor.fetchone()[0]
    logger.info(f"📊 Initial fallback tokens: {initial_count}")
    cursor.close()
    conn.close()
    
    # Process test tokens
    logger.info("🔄 Processing test tokens...")
    server.handle_new_token_with_fallback(test_tokens)
    
    # Check final fallback count
    conn = processor.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM fallback_processing_coins')
    final_count = cursor.fetchone()[0]
    
    # Check if our test tokens are in fallback table
    cursor.execute('''
        SELECT token_name, contract_address, processing_status 
        FROM fallback_processing_coins 
        WHERE token_name LIKE 'Unnamed Token%' 
        ORDER BY detected_at DESC 
        LIMIT 5
    ''')
    fallback_tokens = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    logger.info(f"📊 Final fallback tokens: {final_count}")
    logger.info(f"📈 Tokens added: {final_count - initial_count}")
    
    if fallback_tokens:
        logger.info("✅ Found Unnamed Tokens in fallback table:")
        for token in fallback_tokens:
            logger.info(f"  - {token[0]} ({token[1][:10]}...) - Status: {token[2]}")
    else:
        logger.warning("⚠️ No Unnamed Tokens found in fallback table")
    
    # Verify routing worked
    if final_count > initial_count:
        logger.info("✅ SUCCESS: Unnamed tokens are being routed to fallback table")
        return True
    else:
        logger.error("❌ FAILURE: Unnamed tokens are not reaching fallback table")
        return False

if __name__ == "__main__":
    success = test_unnamed_token_routing()
    if success:
        logger.info("🎉 Unnamed token routing test PASSED")
    else:
        logger.error("💥 Unnamed token routing test FAILED")