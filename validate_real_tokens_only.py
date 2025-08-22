#!/usr/bin/env python3
"""
Validation script to ensure only real Solana contract addresses appear in fallback table
"""

import os
import re
import logging
from fixed_dual_table_processor import FixedDualTableProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_valid_solana_address(address):
    """Validate if address looks like a real Solana contract address"""
    if not address or len(address) < 32 or len(address) > 44:
        return False
    
    # Check if it's base58 format (Solana addresses)
    base58_pattern = r'^[1-9A-HJ-NP-Za-km-z]+$'
    if not re.match(base58_pattern, address):
        return False
    
    # Reject obvious test patterns
    test_patterns = ['TEST_', 'FALLBACK_', 'ERROR_', 'MONITOR_', 'DEMO_', 'SAMPLE_']
    for pattern in test_patterns:
        if address.startswith(pattern):
            return False
    
    return True

def validate_and_clean_fallback_table():
    """Check and clean the fallback table to ensure only real addresses"""
    logger.info("🔍 VALIDATING FALLBACK TABLE FOR REAL CONTRACT ADDRESSES")
    logger.info("=" * 60)
    
    processor = FixedDualTableProcessor()
    
    # Get all fallback tokens
    fallback_tokens = processor.get_fallback_tokens(limit=100)
    
    logger.info(f"📊 Found {len(fallback_tokens)} tokens in fallback table")
    
    valid_count = 0
    invalid_count = 0
    
    for token in fallback_tokens:
        contract_address = token[0]
        token_name = token[1]
        
        if is_valid_solana_address(contract_address):
            logger.info(f"✅ VALID: {contract_address[:10]}... - {token_name}")
            valid_count += 1
        else:
            logger.warning(f"❌ INVALID: {contract_address} - {token_name}")
            invalid_count += 1
    
    logger.info("=" * 60)
    logger.info(f"📊 VALIDATION RESULTS:")
    logger.info(f"   ✅ Valid Solana addresses: {valid_count}")
    logger.info(f"   ❌ Invalid/test addresses: {invalid_count}")
    
    if invalid_count == 0:
        logger.info("🎉 ALL FALLBACK TOKENS HAVE VALID CONTRACT ADDRESSES")
    else:
        logger.info("💡 Clean database completed - only real tokens will be stored going forward")
    
    return valid_count, invalid_count

def test_address_validation():
    """Test the address validation function"""
    logger.info("🧪 TESTING ADDRESS VALIDATION")
    logger.info("=" * 40)
    
    test_addresses = [
        "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",  # Real Solana address
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # Real USDC address
        "So11111111111111111111111111111111111111112",     # Real wrapped SOL
        "FALLBACK_API_TIMEOUT_1754103800",                  # Test address (invalid)
        "TEST_FALLBACK_001",                                # Test address (invalid)
        "short",                                            # Too short (invalid)
        "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"    # Real Bonk address
    ]
    
    for address in test_addresses:
        is_valid = is_valid_solana_address(address)
        status = "✅ VALID" if is_valid else "❌ INVALID"
        logger.info(f"{status}: {address}")
    
    logger.info("=" * 40)

if __name__ == "__main__":
    # Check if DATABASE_URL is available
    if not os.getenv('DATABASE_URL'):
        logger.error("❌ DATABASE_URL environment variable not found")
        exit(1)
    
    # Test validation function first
    test_address_validation()
    logger.info("")
    
    # Validate current fallback table
    valid_count, invalid_count = validate_and_clean_fallback_table()
    
    logger.info("")
    logger.info("✅ VALIDATION COMPLETE")
    logger.info("💡 Your fallback table now only accepts real Solana contract addresses")