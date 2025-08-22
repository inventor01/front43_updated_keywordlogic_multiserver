#!/usr/bin/env python3
"""
Enhanced Retry Background Service
Runs continuously to process fallback tokens and increment retry counts
"""

import asyncio
import logging
import time
from datetime import datetime
from fixed_dual_table_processor import FixedDualTableProcessor
from enhanced_fallback_name_resolver import EnhancedFallbackResolver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedRetryBackgroundService:
    def __init__(self, retry_interval=300):  # 5 minutes between retry cycles
        self.processor = FixedDualTableProcessor()
        self.resolver = EnhancedFallbackResolver()
        self.retry_interval = retry_interval
        self.running = False
        
    async def start_background_service(self):
        """Start the background retry service"""
        self.running = True
        logger.info("🔄 Enhanced Retry Background Service Started")
        logger.info(f"⏰ Retry interval: {self.retry_interval} seconds")
        
        while self.running:
            try:
                await self.process_retry_cycle()
                logger.info(f"😴 Sleeping for {self.retry_interval} seconds...")
                await asyncio.sleep(self.retry_interval)
                
            except Exception as e:
                logger.error(f"❌ Background service error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def process_retry_cycle(self):
        """Process one cycle of retry attempts"""
        logger.info("🔄 Starting retry cycle...")
        
        # Get tokens that need retry processing
        fallback_tokens = self.processor.get_fallback_tokens(limit=50)
        
        if not fallback_tokens:
            logger.info("📭 No fallback tokens to process")
            return
        
        logger.info(f"🎯 Processing {len(fallback_tokens)} fallback tokens")
        
        processed = 0
        resolved = 0
        retried = 0
        
        for token in fallback_tokens:
            try:
                contract_address = token[0]
                token_name = token[1]
                current_retry_count = token[3] if len(token) > 3 else 0
                
                logger.info(f"🔍 Processing: {token_name} (retry #{current_retry_count})")
                
                # Try to resolve the token name
                resolved_name = await self.attempt_name_resolution(contract_address)
                
                if resolved_name and not resolved_name.startswith('Unnamed'):
                    # Success! Migrate to detected tokens
                    logger.info(f"✅ RESOLVED: '{resolved_name}' for {contract_address[:10]}...")
                    
                    resolved_id = self.processor.insert_resolved_token(
                        contract_address=contract_address,
                        token_name=resolved_name,
                        symbol=token[2] if len(token) > 2 else 'UNKNOWN'
                    )
                    
                    if resolved_id:
                        # Remove from fallback table
                        await self.remove_from_fallback(contract_address)
                        logger.info(f"🎉 MIGRATED: {resolved_name} moved to detected_tokens")
                        resolved += 1
                    
                else:
                    # Still couldn't resolve - increment retry count
                    logger.info(f"⏳ Still unresolved: {token_name} (retry #{current_retry_count + 1})")
                    
                    success = self.processor.update_retry_count(contract_address, 'fallback_processing_coins')
                    if success:
                        retried += 1
                        logger.info(f"📈 Retry count incremented to {current_retry_count + 1}")
                    else:
                        logger.warning(f"⚠️ Failed to increment retry count for {contract_address[:10]}...")
                
                processed += 1
                
                # Rate limiting between requests
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error processing token {contract_address[:10]}...: {e}")
                continue
        
        # Log cycle summary
        logger.info("=" * 60)
        logger.info(f"📊 RETRY CYCLE SUMMARY:")
        logger.info(f"   • Processed: {processed} tokens")
        logger.info(f"   • Resolved: {resolved} tokens")
        logger.info(f"   • Retried: {retried} tokens")
        logger.info(f"   • Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
    
    async def attempt_name_resolution(self, contract_address):
        """Attempt to resolve token name using multiple methods"""
        try:
            # Try DexScreener first
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
                
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('pairs') and len(data['pairs']) > 0:
                            pair = data['pairs'][0]
                            base_token = pair.get('baseToken', {})
                            token_name = base_token.get('name')
                            
                            if token_name and len(token_name.strip()) > 0:
                                return token_name.strip()
            
            return None
            
        except Exception as e:
            logger.debug(f"Name resolution failed for {contract_address[:10]}...: {e}")
            return None
    
    async def remove_from_fallback(self, contract_address):
        """Remove successfully resolved token from fallback table"""
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
    
    def stop_service(self):
        """Stop the background service"""
        self.running = False
        logger.info("🛑 Enhanced Retry Background Service Stopped")

async def main():
    """Main entry point for the background service"""
    service = EnhancedRetryBackgroundService(retry_interval=120)  # 2 minutes for testing
    
    try:
        await service.start_background_service()
    except KeyboardInterrupt:
        logger.info("🛑 Service stopped by user")
        service.stop_service()

if __name__ == "__main__":
    asyncio.run(main())