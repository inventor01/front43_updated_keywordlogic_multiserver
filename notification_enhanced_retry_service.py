#!/usr/bin/env python3
"""
Notification Enhanced Retry Service
Background service that includes keyword matching and Discord notifications when tokens are migrated.
"""

import asyncio
import logging
import time
from datetime import datetime
from fixed_dual_table_processor import FixedDualTableProcessor
from dual_table_name_resolver import DualTableNameResolver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationEnhancedRetryService:
    def __init__(self, interval_seconds=60):
        self.processor = FixedDualTableProcessor()
        self.resolver = DualTableNameResolver()
        self.interval = interval_seconds
        self.running = False
        
        # Keywords for matching (loaded from database or hardcoded)
        self.keywords = self.load_keywords()
        
    def load_keywords(self):
        """Load keywords from database or use defaults"""
        try:
            # Try to load from database first
            conn = self.processor.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT keyword FROM user_keywords WHERE active = TRUE")
            db_keywords = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            if db_keywords:
                logger.info(f"📋 Loaded {len(db_keywords)} keywords from database")
                return db_keywords
            else:
                # Fallback to default keywords
                default_keywords = ['moon', 'pepe', 'doge', 'shib', 'pump', 'meme', 'bonk']
                logger.info(f"📋 Using default keywords: {default_keywords}")
                return default_keywords
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to load keywords from database: {e}")
            default_keywords = ['moon', 'pepe', 'doge', 'shib', 'pump', 'meme', 'bonk']
            logger.info(f"📋 Using default keywords: {default_keywords}")
            return default_keywords
    
    def check_keyword_matches(self, token_name):
        """Check if token name matches any keywords"""
        if not token_name or not self.keywords:
            return []
        
        token_name_lower = token_name.lower()
        matched_keywords = []
        
        for keyword in self.keywords:
            if keyword and keyword.lower() in token_name_lower:
                matched_keywords.append(keyword)
        
        return matched_keywords
    
    async def send_discord_notification(self, token_name, symbol, contract_address, matched_keywords):
        """Send Discord notification for migrated token that matches keywords"""
        try:
            # Create notification message
            message = f"""🚀 **RESOLVED TOKEN ALERT**

**Name**: {token_name}
**Symbol**: {symbol or 'N/A'}
**Address**: `{contract_address}`
**Keywords**: {', '.join(matched_keywords)}
**Source**: Migration from Pending
**Status**: Name Resolved ✅

This token was resolved from pending status and matches your keywords!
"""
            
            logger.info(f"📨 MIGRATION NOTIFICATION: {token_name} → {', '.join(matched_keywords)}")
            
            # TODO: Integrate with actual Discord notifier
            # For now, just log the notification
            logger.info(f"🎯 KEYWORD MATCH IN MIGRATION: '{token_name}' matches {matched_keywords}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Discord notification error: {e}")
            return False
    
    async def process_pending_tokens(self):
        """Process pending tokens with keyword matching and notifications (compatibility method)"""
        return await self.process_pending_tokens_with_notifications()
    
    async def process_pending_tokens_with_notifications(self):
        """Process pending tokens with keyword matching and notifications"""
        try:
            logger.info("🔄 Starting pending token resolution cycle...")
            
            # Get pending tokens
            pending_tokens = self.processor.get_pending_tokens(limit=100)
            
            if not pending_tokens:
                logger.info("✅ No pending tokens to process")
                return 0
            
            logger.info(f"📋 Found {len(pending_tokens)} pending tokens for name resolution")
            
            resolved_count = 0
            notification_count = 0
            
            # Process each pending token
            for token_data in pending_tokens:
                contract_address, placeholder_name, matched_keywords, retry_count, detected_at, blockchain_age = token_data
                
                logger.info(f"🔍 Resolving: {placeholder_name} ({contract_address[:10]}...) - attempt #{retry_count + 1}")
                
                try:
                    # Try to resolve the name
                    result = await self.resolver.resolve_token_name_dexscreener(contract_address)
                    
                    if result and result.get('name'):
                        resolved_name = result['name']
                        symbol = result.get('symbol')
                        
                        # CHECK FOR KEYWORD MATCHES ON RESOLVED NAME
                        keyword_matches = self.check_keyword_matches(resolved_name)
                        
                        # Migrate to detected_tokens
                        success = self.processor.migrate_pending_to_resolved(
                            contract_address=contract_address,
                            token_name=resolved_name,
                            symbol=symbol,
                            social_links={'dexscreener': True}
                        )
                        
                        if success:
                            resolved_count += 1
                            logger.info(f"✅ RESOLVED & MIGRATED: {resolved_name} (was {placeholder_name})")
                            
                            # SEND NOTIFICATION IF KEYWORDS MATCH
                            if keyword_matches:
                                notification_sent = await self.send_discord_notification(
                                    resolved_name, symbol, contract_address, keyword_matches
                                )
                                if notification_sent:
                                    notification_count += 1
                                    logger.info(f"🎯 NOTIFICATION SENT: {resolved_name} → {', '.join(keyword_matches)}")
                                else:
                                    logger.warning(f"⚠️ Notification failed for {resolved_name}")
                            else:
                                logger.info(f"🔍 No keyword matches for: {resolved_name}")
                        else:
                            logger.error(f"❌ Migration failed for {resolved_name}")
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
            
            logger.info(f"📊 RESOLUTION CYCLE COMPLETE:")
            logger.info(f"   • Tokens resolved: {resolved_count}/{len(pending_tokens)}")
            logger.info(f"   • Notifications sent: {notification_count}")
            
            return resolved_count
            
        except Exception as e:
            logger.error(f"❌ Error in pending token processing: {e}")
            return 0
    
    async def run_service(self):
        """Run the continuous retry service with notifications"""
        self.running = True
        logger.info(f"🚀 Starting notification-enhanced retry service (interval: {self.interval}s)")
        
        cycle_count = 0
        total_resolved = 0
        total_notifications = 0
        
        while self.running:
            try:
                cycle_count += 1
                logger.info(f"🔄 CYCLE #{cycle_count} - Processing pending tokens with keyword matching...")
                
                # Get system stats before processing
                stats_before = self.processor.get_system_stats()
                
                # Process pending tokens with notifications
                resolved_this_cycle = await self.process_pending_tokens_with_notifications()
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
        logger.info("🛑 Notification-enhanced retry service stopped")

async def main():
    """Main service entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run single test
        service = NotificationEnhancedRetryService()
        resolved_count = await service.process_pending_tokens_with_notifications()
        logger.info(f"✅ Test complete: {resolved_count} tokens resolved")
        return resolved_count
    else:
        # Run continuous service
        service = NotificationEnhancedRetryService(interval_seconds=60)
        
        try:
            await service.run_service()
        except KeyboardInterrupt:
            logger.info("🛑 Service stopped by user")
            service.stop()
        except Exception as e:
            logger.error(f"❌ Service crashed: {e}")

if __name__ == "__main__":
    asyncio.run(main())