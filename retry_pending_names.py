#!/usr/bin/env python3
"""
Retry Pending Names Service
Background service that continuously retries name resolution for pending tokens.
"""

import asyncio
import logging
import time
from datetime import datetime
from dual_table_token_processor import DualTableTokenProcessor
from dual_table_name_resolver import DualTableNameResolver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RetryPendingNamesService:
    def __init__(self, interval_seconds=60):
        self.processor = DualTableTokenProcessor()
        self.resolver = DualTableNameResolver()
        self.interval = interval_seconds
        self.running = False
        
    async def process_pending_tokens(self):
        """Process all pending tokens in the background"""
        try:
            logger.info("🔄 Starting pending token resolution cycle...")
            
            # Get pending tokens
            pending_tokens = self.processor.get_pending_tokens(limit=100)
            
            if not pending_tokens:
                logger.info("✅ No pending tokens to process")
                return 0
            
            logger.info(f"📋 Found {len(pending_tokens)} pending tokens for name resolution")
            
            resolved_count = 0
            
            # Process each pending token
            for token_data in pending_tokens:
                contract_address, placeholder_name, matched_keywords, retry_count, detected_at, blockchain_age = token_data
                
                logger.info(f"🔍 Resolving: {placeholder_name} ({contract_address[:10]}...) - attempt #{retry_count + 1}")
                
                try:
                    # Try to resolve the name
                    result = await self.resolver.resolve_token_name_dexscreener(contract_address)
                    
                    if result and result.get('name'):
                        # Successfully resolved - migrate to detected_tokens
                        success = self.processor.migrate_pending_to_resolved(
                            contract_address=contract_address,
                            token_name=result['name'],
                            symbol=result.get('symbol'),
                            social_links={'dexscreener': True}
                        )
                        
                        if success:
                            resolved_count += 1
                            logger.info(f"✅ RESOLVED & MIGRATED: {result['name']} (was {placeholder_name})")
                        else:
                            logger.error(f"❌ Migration failed for {result['name']}")
                    else:
                        # Still not available - update retry count
                        self.processor.update_retry_count(contract_address)
                        logger.info(f"⏳ Still pending: {placeholder_name} (will retry later)")
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {placeholder_name}: {e}")
                    # Update retry count even on error
                    self.processor.update_retry_count(contract_address)
            
            logger.info(f"📊 RESOLUTION CYCLE COMPLETE: {resolved_count}/{len(pending_tokens)} tokens resolved")
            return resolved_count
            
        except Exception as e:
            logger.error(f"❌ Error in pending token processing: {e}")
            return 0
    
    async def run_service(self):
        """Run the continuous retry service"""
        self.running = True
        logger.info(f"🚀 Starting retry pending names service (interval: {self.interval}s)")
        
        cycle_count = 0
        total_resolved = 0
        
        while self.running:
            try:
                cycle_count += 1
                logger.info(f"🔄 CYCLE #{cycle_count} - Processing pending tokens...")
                
                # Get system stats before processing
                stats_before = self.processor.get_system_stats()
                
                # Process pending tokens
                resolved_this_cycle = await self.process_pending_tokens()
                total_resolved += resolved_this_cycle
                
                # Get system stats after processing
                stats_after = self.processor.get_system_stats()
                
                logger.info(f"📊 CYCLE #{cycle_count} SUMMARY:")
                logger.info(f"   • Resolved this cycle: {resolved_this_cycle}")
                logger.info(f"   • Total resolved since start: {total_resolved}")
                logger.info(f"   • Pending before: {stats_before['pending_tokens']}")
                logger.info(f"   • Pending after: {stats_after['pending_tokens']}")
                logger.info(f"   • Total resolved tokens: {stats_after['total_resolved']}")
                
                # Wait for next cycle
                if self.running:
                    logger.info(f"⏰ Next cycle in {self.interval} seconds...")
                    await asyncio.sleep(self.interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal")
                self.stop()
            except Exception as e:
                logger.error(f"❌ Error in service cycle: {e}")
                await asyncio.sleep(10)  # Short delay before retry
    
    def stop(self):
        """Stop the retry service"""
        self.running = False
        logger.info("🛑 Retry pending names service stopped")

async def test_single_run():
    """Test a single resolution cycle"""
    logger.info("🧪 Testing single retry cycle...")
    
    service = RetryPendingNamesService()
    resolved_count = await service.process_pending_tokens()
    
    logger.info(f"✅ Test complete: {resolved_count} tokens resolved")
    return resolved_count

async def main():
    """Main service entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run single test
        return await test_single_run()
    else:
        # Run continuous service
        service = RetryPendingNamesService(interval_seconds=60)
        
        try:
            await service.run_service()
        except KeyboardInterrupt:
            logger.info("🛑 Service stopped by user")
            service.stop()
        except Exception as e:
            logger.error(f"❌ Service crashed: {e}")

# Alias for backward compatibility
PendingNameResolver = RetryPendingNamesService

if __name__ == "__main__":
    asyncio.run(main())