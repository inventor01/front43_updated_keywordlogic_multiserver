#!/usr/bin/env python3
"""
Delayed Name Extractor - Extract token names with delay for better accuracy
Part of the Solana token monitoring system
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DelayedNameExtractor:
    """
    Delayed name extractor for tokens that need time to populate metadata
    """
    
    def __init__(self, delay_seconds=300, discord_notifier=None, **kwargs):  # 5 minutes default
        """Initialize the delayed name extractor"""
        self.delay_seconds = delay_seconds
        self.discord_notifier = discord_notifier
        self.pending_extractions = {}
        self.extracted_names = {}
        self.running = False
        
        # Accept any additional kwargs to prevent initialization errors
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        logger.info(f"✅ Delayed name extractor initialized (delay: {delay_seconds}s)")
    
    def queue_extraction(self, token_address: str, fallback_name: str):
        """Queue a token for delayed name extraction"""
        if token_address not in self.pending_extractions:
            self.pending_extractions[token_address] = {
                'fallback_name': fallback_name,
                'queued_time': time.time(),
                'attempts': 0
            }
            logger.info(f"⏰ Queued for delayed extraction: {token_address[:8]}...")
    
    async def start_extraction_loop(self):
        """Start the delayed extraction loop"""
        self.running = True
        logger.info("🔄 Starting delayed name extraction loop")
        
        while self.running:
            try:
                await self._process_pending_extractions()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"❌ Delayed extraction loop error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _process_pending_extractions(self):
        """Process pending extractions that are ready"""
        current_time = time.time()
        ready_extractions = []
        
        for address, data in self.pending_extractions.items():
            if current_time - data['queued_time'] >= self.delay_seconds:
                ready_extractions.append(address)
        
        for address in ready_extractions:
            try:
                await self._extract_delayed_name(address)
            except Exception as e:
                logger.warning(f"⚠️ Delayed extraction failed for {address[:8]}...: {e}")
    
    async def _extract_delayed_name(self, address: str):
        """Extract name for a specific token after delay"""
        data = self.pending_extractions.get(address)
        if not data:
            return
        
        try:
            # Try to get real name now that time has passed
            # This would integrate with your existing name extraction methods
            extracted_name = await self._attempt_name_extraction(address)
            
            if extracted_name and extracted_name != data['fallback_name']:
                self.extracted_names[address] = {
                    'name': extracted_name,
                    'extracted_time': time.time(),
                    'fallback_name': data['fallback_name']
                }
                logger.info(f"✅ Delayed extraction success: {address[:8]}... → '{extracted_name}'")
                
                # Notify callback if available
                if hasattr(self, 'callback_func') and self.callback_func:
                    await self.callback_func(address, extracted_name)
            
            # Remove from pending regardless of success
            del self.pending_extractions[address]
            
        except Exception as e:
            logger.warning(f"⚠️ Delayed extraction error for {address[:8]}...: {e}")
            
            # Increment attempts and retry or remove
            data['attempts'] += 1
            if data['attempts'] >= 3:
                del self.pending_extractions[address]
                logger.warning(f"❌ Giving up on delayed extraction for {address[:8]}...")
    
    async def _attempt_name_extraction(self, address: str) -> Optional[str]:
        """Attempt to extract the real name for a token"""
        # This is a placeholder - integrate with your existing extraction methods
        # For now, return None to indicate no extraction available
        return None
    
    def get_extracted_name(self, address: str) -> Optional[str]:
        """Get extracted name if available"""
        data = self.extracted_names.get(address)
        return data['name'] if data else None
    
    def stop(self):
        """Stop the extraction loop"""
        self.running = False
        logger.info("🛑 Delayed name extractor stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get extraction statistics"""
        return {
            'pending_extractions': len(self.pending_extractions),
            'completed_extractions': len(self.extracted_names),
            'delay_seconds': self.delay_seconds,
            'running': self.running
        }

# Factory function
def create_delayed_extractor(delay_seconds=300) -> DelayedNameExtractor:
    """Create a delayed name extractor"""
    return DelayedNameExtractor(delay_seconds)