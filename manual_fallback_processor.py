#!/usr/bin/env python3
"""
Manual Fallback Token Processor
Processes stuck fallback tokens to resolve names and migrate to detected_tokens
"""

import requests
import time
import logging
from fixed_dual_table_processor import FixedDualTableProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ManualFallbackProcessor:
    def __init__(self):
        self.processor = FixedDualTableProcessor()
        
    def process_stuck_tokens(self, batch_size=10):
        """Process tokens that have been stuck in fallback processing"""
        logger.info("🔄 Starting manual fallback token processing...")
        
        # Get tokens that need processing
        fallback_tokens = self.processor.get_fallback_tokens(limit=batch_size)
        
        if not fallback_tokens:
            logger.info("📭 No fallback tokens to process")
            return 0
            
        logger.info(f"🎯 Processing {len(fallback_tokens)} fallback tokens")
        
        processed = 0
        for token in fallback_tokens:
            contract_address = token[0]
            current_name = token[1]
            retry_count = token[7] if len(token) > 7 else 0
            
            logger.info(f"🔍 Processing: {current_name} ({contract_address[:10]}...) - retry {retry_count}")
            
            # Try multiple name resolution methods
            resolved_name = self.try_resolve_name(contract_address)
            
            if resolved_name and not resolved_name.startswith('Unnamed'):
                # Success! Migrate to detected_tokens
                success = self.processor.migrate_fallback_to_detected(
                    contract_address=contract_address,
                    token_name=resolved_name,
                    symbol='BONK',
                    matched_keywords=[]
                )
                
                if success:
                    logger.info(f"✅ MIGRATED: {resolved_name} ({contract_address[:10]}...)")
                    processed += 1
                else:
                    logger.error(f"❌ Migration failed for {resolved_name}")
                    
            else:
                # Still no luck - update retry count
                self.processor.update_fallback_retry_count(contract_address)
                logger.info(f"⏳ Still resolving: {current_name} - retry count updated")
            
            # Rate limiting
            time.sleep(1)
        
        logger.info(f"🎉 Processed {processed}/{len(fallback_tokens)} tokens successfully")
        return processed
    
    def try_resolve_name(self, contract_address):
        """Try multiple methods to resolve token name"""
        
        # Method 1: DexScreener API
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                if pairs and len(pairs) > 0:
                    token_info = pairs[0]
                    name = token_info.get('baseToken', {}).get('name')
                    
                    if name and len(name.strip()) > 0 and not name.startswith('Unnamed'):
                        logger.info(f"🎯 DexScreener found: {name}")
                        return name.strip()
            
        except Exception as e:
            logger.debug(f"DexScreener failed: {e}")
        
        # Method 2: Try Solscan API
        try:
            url = f"https://public-api.solscan.io/token/meta?tokenAddress={contract_address}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                name = data.get('name')
                
                if name and len(name.strip()) > 0 and not name.startswith('Unnamed'):
                    logger.info(f"🎯 Solscan found: {name}")
                    return name.strip()
                    
        except Exception as e:
            logger.debug(f"Solscan failed: {e}")
        
        # Method 3: Check if it's a known problematic token that should be marked as resolved
        if contract_address in ['TEST_ADDRESS_123', 'DEMO', 'RETRY']:
            return None  # Skip test addresses
        
        return None

if __name__ == "__main__":
    processor = ManualFallbackProcessor()
    
    # Process tokens in batches
    total_processed = 0
    for batch in range(5):  # Process 5 batches of 10 tokens each
        logger.info(f"📦 Processing batch {batch + 1}/5...")
        batch_processed = processor.process_stuck_tokens(batch_size=10)
        total_processed += batch_processed
        
        if batch_processed == 0:
            logger.info("🏁 No more tokens to process")
            break
            
        # Wait between batches
        time.sleep(5)
    
    logger.info(f"🎊 TOTAL PROCESSED: {total_processed} tokens migrated successfully")