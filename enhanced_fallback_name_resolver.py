#!/usr/bin/env python3
"""
Enhanced Fallback Name Resolver
Processes tokens in fallback_processing_coins table to get accurate names using multiple sources
"""

import asyncio
import aiohttp
import logging
import time
import os
from fixed_dual_table_processor import FixedDualTableProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedFallbackResolver:
    def __init__(self):
        self.processor = FixedDualTableProcessor()
        
    async def resolve_fallback_tokens(self):
        """Process tokens in fallback_processing_coins to get accurate names"""
        logger.info("🔄 Starting enhanced fallback name resolution...")
        
        # Get tokens that need name resolution
        fallback_tokens = self.processor.get_fallback_tokens(limit=20)
        
        if not fallback_tokens:
            logger.info("📭 No fallback tokens to process")
            return
            
        logger.info(f"🎯 Processing {len(fallback_tokens)} fallback tokens")
        
        async with aiohttp.ClientSession() as session:
            for token in fallback_tokens:
                contract_address = token[0]
                current_name = token[1]
                processing_status = token[6] if len(token) > 6 else 'pending'
                
                logger.info(f"🔍 Resolving: {current_name} ({contract_address[:10]}...)")
                
                # Try to get accurate name from DexScreener
                accurate_name = await self.get_name_from_dexscreener(session, contract_address)
                
                if accurate_name and not accurate_name.startswith('Unnamed'):
                    # Success! Migrate to detected_tokens
                    logger.info(f"✅ RESOLVED: '{accurate_name}' for {contract_address[:10]}...")
                    
                    # Insert into detected_tokens with real name
                    resolved_id = self.processor.insert_resolved_token(
                        contract_address=contract_address,
                        token_name=accurate_name,
                        symbol='BONK',
                        blockchain_age_seconds=token[5] if len(token) > 5 else None
                    )
                    
                    if resolved_id:
                        # Remove from fallback table
                        self.remove_from_fallback(contract_address)
                        logger.info(f"🎉 MIGRATED: {accurate_name} moved to detected_tokens")
                    
                else:
                    # Still no luck - update retry count
                    logger.info(f"⏳ Still resolving: {current_name}")
                    self.processor.update_retry_count(contract_address, 'fallback_processing_coins')
                
                # Rate limiting
                await asyncio.sleep(0.5)
    
    async def get_name_from_dexscreener(self, session, contract_address):
        """Get token name from DexScreener API"""
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
            
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('pairs') and len(data['pairs']) > 0:
                        pair = data['pairs'][0]
                        base_token = pair.get('baseToken', {})
                        token_name = base_token.get('name')
                        
                        if token_name and len(token_name.strip()) > 0:
                            logger.info(f"🎯 DexScreener found: '{token_name}'")
                            return token_name.strip()
                
                logger.debug(f"No name found on DexScreener for {contract_address[:10]}...")
                return None
                
        except Exception as e:
            logger.debug(f"DexScreener error for {contract_address[:10]}...: {e}")
            return None
    
    def remove_from_fallback(self, contract_address):
        """Remove token from fallback_processing_coins after successful resolution"""
        try:
            conn = self.processor.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM fallback_processing_coins 
                WHERE contract_address = %s
            ''', (contract_address,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"🗑️ Removed {contract_address[:10]}... from fallback table")
            
        except Exception as e:
            logger.error(f"❌ Failed to remove from fallback: {e}")

async def main():
    """Main resolution loop"""
    resolver = EnhancedFallbackResolver()
    
    while True:
        try:
            await resolver.resolve_fallback_tokens()
            logger.info("😴 Waiting 60 seconds before next resolution cycle...")
            await asyncio.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("👋 Fallback resolver stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Error in fallback resolver: {e}")
            await asyncio.sleep(30)

if __name__ == "__main__":
    logger.info("🚀 Starting Enhanced Fallback Name Resolver...")
    asyncio.run(main())