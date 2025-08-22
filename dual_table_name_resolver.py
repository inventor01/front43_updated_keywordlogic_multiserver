#!/usr/bin/env python3
"""
Dual Table Name Resolver
Background service that resolves pending token names and migrates them to resolved table.
"""

import asyncio
import aiohttp
import psycopg2
import os
import logging
from datetime import datetime
import json
from fixed_dual_table_processor import FixedDualTableProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DualTableNameResolver:
    def __init__(self):
        self.processor = FixedDualTableProcessor()
        self.running = False
        
    async def resolve_token_name_dexscreener(self, contract_address):
        """Resolve token name using DexScreener API"""
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and 'pairs' in data and data['pairs']:
                            # Get the first pair with valid data
                            for pair in data['pairs']:
                                if pair and 'baseToken' in pair:
                                    base_token = pair['baseToken']
                                    
                                    if base_token and base_token.get('address', '').lower() == contract_address.lower():
                                        name = base_token.get('name', '').strip()
                                        symbol = base_token.get('symbol', '').strip()
                                        
                                        if name and name != 'Unknown':
                                            logger.info(f"🎯 DEXSCREENER RESOLVED: {name} ({symbol})")
                                            return {
                                                'name': name,
                                                'symbol': symbol,
                                                'source': 'DexScreener'
                                            }
                        
                        logger.info(f"⏳ DexScreener: Token {contract_address[:10]}... not indexed yet")
                        return None
                    else:
                        logger.warning(f"⚠️ DexScreener API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ DexScreener resolution failed: {e}")
            return None
    
    async def process_pending_tokens(self):
        """Process all pending tokens and attempt name resolution"""
        try:
            pending_tokens = self.processor.get_pending_tokens(limit=100)
            
            if not pending_tokens:
                logger.info("✅ No pending tokens to process")
                return 0
            
            logger.info(f"🔄 Processing {len(pending_tokens)} pending tokens...")
            
            resolved_count = 0
            
            for token_data in pending_tokens:
                (contract_address, placeholder_name, keyword, matched_keywords, 
                 retry_count, detected_at, blockchain_age_seconds) = token_data
                
                logger.info(f"🔍 Attempting to resolve: {placeholder_name} ({contract_address[:10]}...)")
                
                # Try to resolve the name
                result = await self.resolve_token_name_dexscreener(contract_address)
                
                if result:
                    # Successfully resolved - migrate to detected_tokens
                    success = self.processor.migrate_pending_to_resolved(
                        contract_address,
                        result['name'],
                        result.get('symbol'),
                        {'dexscreener': True}
                    )
                    
                    if success:
                        resolved_count += 1
                        logger.info(f"✅ RESOLVED & MIGRATED: {result['name']} (was {placeholder_name})")
                    else:
                        logger.error(f"❌ Migration failed for {result['name']}")
                else:
                    # Update retry count
                    self.update_retry_count(contract_address)
                    logger.info(f"⏳ Still pending: {placeholder_name} (retry #{retry_count + 1})")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
            
            logger.info(f"📊 RESOLUTION SUMMARY: {resolved_count}/{len(pending_tokens)} tokens resolved")
            return resolved_count
            
        except Exception as e:
            logger.error(f"❌ Error processing pending tokens: {e}")
            return 0
    
    def update_retry_count(self, contract_address):
        """Update retry count for a pending token"""
        try:
            conn = self.processor.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE pending_tokens 
                SET retry_count = retry_count + 1,
                    last_attempt = CURRENT_TIMESTAMP
                WHERE contract_address = %s
            ''', (contract_address,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to update retry count: {e}")
    
    async def run_continuous_resolution(self, interval_seconds=60):
        """Run continuous background name resolution"""
        self.running = True
        logger.info(f"🚀 Starting dual table name resolver (interval: {interval_seconds}s)")
        
        while self.running:
            try:
                logger.info("🔄 Starting name resolution cycle...")
                
                # Get system stats before processing
                stats_before = self.processor.get_system_stats()
                logger.info(f"📊 Before: {stats_before['pending_tokens']} pending, {stats_before['total_resolved']} total resolved")
                
                # Process pending tokens
                resolved_count = await self.process_pending_tokens()
                
                # Get system stats after processing
                stats_after = self.processor.get_system_stats()
                logger.info(f"📊 After: {stats_after['pending_tokens']} pending, {stats_after['total_resolved']} total resolved")
                
                if resolved_count > 0:
                    logger.info(f"✅ Resolution cycle complete: {resolved_count} tokens migrated to resolved table")
                else:
                    logger.info("✅ Resolution cycle complete: no new resolutions")
                
                # Wait for next cycle
                logger.info(f"⏰ Next resolution cycle in {interval_seconds} seconds...")
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"❌ Error in resolution cycle: {e}")
                await asyncio.sleep(10)  # Short delay before retry
    
    def stop(self):
        """Stop the continuous resolution"""
        self.running = False
        logger.info("🛑 Stopping dual table name resolver...")

async def test_single_resolution():
    """Test resolving a single token"""
    resolver = DualTableNameResolver()
    
    # Test with a known token
    test_address = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
    result = await resolver.resolve_token_name_dexscreener(test_address)
    
    if result:
        print(f"✅ Test resolution successful: {result}")
    else:
        print("❌ Test resolution failed")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run single test
        asyncio.run(test_single_resolution())
    else:
        # Run continuous resolver
        resolver = DualTableNameResolver()
        
        try:
            asyncio.run(resolver.run_continuous_resolution(interval_seconds=60))
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal")
            resolver.stop()
        except Exception as e:
            logger.error(f"❌ Resolver crashed: {e}")