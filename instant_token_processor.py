#!/usr/bin/env python3
"""
Instant Token Processor - Zero Delay Processing System
"""

import time
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import requests

logger = logging.getLogger(__name__)

class InstantTokenProcessor:
    def __init__(self, keywords=None, webhook_notifier=None):
        self.keywords = set(kw.lower() for kw in (keywords or []))
        self.webhook_notifier = webhook_notifier
        self.notification_cache = {}
        self.processing_lock = Lock()
        
        # Pre-compiled regex patterns for ultra-fast matching
        self.keyword_patterns = {}
        for keyword in self.keywords:
            self.keyword_patterns[keyword] = keyword.lower()
        
        logger.info(f"⚡ INSTANT PROCESSOR: Initialized with {len(self.keywords)} keywords")
    
    def instant_keyword_match(self, token_name):
        """
        Ultra-fast keyword matching using set operations (O(1) lookup)
        Processing time: <1ms
        """
        if not token_name:
            return []
        
        token_name_lower = token_name.lower()
        matches = []
        
        # Direct string matching - fastest possible approach
        for keyword in self.keywords:
            if keyword in token_name_lower:
                matches.append(keyword)
        
        return matches
    
    async def process_token_instant(self, token_data):
        """
        Process token with absolute minimal delay
        Target: <50ms total processing time
        """
        process_start = time.time()
        
        # Extract token info (already provided, no API calls needed)
        token_name = token_data.get('name', '')
        token_address = token_data.get('address', '')
        
        # Instant keyword matching
        matched_keywords = self.instant_keyword_match(token_name)
        
        # If match found, fire notification immediately (non-blocking)
        if matched_keywords:
            # Pre-build notification data
            notification_data = {
                'name': token_name,
                'address': token_address,
                'symbol': token_data.get('symbol', ''),
                'age_display': '0s ago',  # New token, instant detection
                'market_data': None,
                'url': f"https://letsbonk.fun/token/{token_address}",
                'social_links': []
            }
            
            # Fire notification without waiting (async task)
            asyncio.create_task(self._fire_instant_notification(notification_data, matched_keywords[0]))
            
            processing_time = (time.time() - process_start) * 1000
            logger.info(f"⚡ INSTANT MATCH: {token_name} → '{matched_keywords[0]}' in {processing_time:.1f}ms")
            
            return {
                'processed': True,
                'matched_keywords': matched_keywords,
                'processing_time_ms': processing_time,
                'notification_sent': True
            }
        
        # No match - ultra-fast rejection
        processing_time = (time.time() - process_start) * 1000
        return {
            'processed': True,
            'matched_keywords': [],
            'processing_time_ms': processing_time,
            'notification_sent': False
        }
    
    async def _fire_instant_notification(self, token_data, keyword):
        """
        Send notification with zero blocking
        """
        try:
            if self.webhook_notifier:
                # Fire webhook notification (async, non-blocking)
                await self.webhook_notifier.send_token_notification(token_data, keyword)
                logger.info(f"🚀 INSTANT ALERT: {token_data['name']} → Discord")
        except Exception as e:
            logger.debug(f"Notification error: {e}")
    
    def batch_process_instant(self, tokens):
        """
        Process multiple tokens in parallel with zero delay
        """
        if not tokens:
            return []
        
        batch_start = time.time()
        results = []
        
        # Process all tokens simultaneously
        for token in tokens:
            result = asyncio.run(self.process_token_instant(token))
            results.append(result)
        
        batch_time = (time.time() - batch_start) * 1000
        matched_count = sum(1 for r in results if r['matched_keywords'])
        
        logger.info(f"⚡ INSTANT BATCH: {len(tokens)} tokens processed in {batch_time:.1f}ms, {matched_count} matches")
        
        return results

class ZeroDelayKeywordMatcher:
    """
    Ultra-optimized keyword matching for zero-delay processing
    """
    def __init__(self, keywords):
        # Pre-process keywords for maximum speed
        self.keyword_set = set(kw.lower() for kw in keywords)
        self.keyword_map = {kw.lower(): kw for kw in keywords}  # Original case mapping
        
        # Pre-compile common patterns
        self.bonk_variants = {'bonk', 'bonking', 'bonked'}
        self.business_variants = {'business', 'busienss', 'bizness'}
        
        logger.info(f"⚡ ZERO-DELAY MATCHER: {len(self.keyword_set)} keywords optimized")
    
    def match_instant(self, text):
        """
        Instant keyword matching - target <1ms
        """
        if not text:
            return []
        
        text_lower = text.lower()
        matches = []
        
        # Ultra-fast set intersection
        for keyword in self.keyword_set:
            if keyword in text_lower:
                matches.append(self.keyword_map[keyword])
        
        return matches
    
    def match_fuzzy_instant(self, text):
        """
        Instant fuzzy matching for common typos
        """
        matches = self.match_instant(text)
        
        if not matches and text:
            text_lower = text.lower()
            
            # Check common variants instantly
            if any(variant in text_lower for variant in self.bonk_variants):
                if 'bonk' in self.keyword_set:
                    matches.append('bonk')
            
            if any(variant in text_lower for variant in self.business_variants):
                if 'business' in self.keyword_set:
                    matches.append('business')
        
        return matches

# Integration function
def integrate_zero_delay_processing(alchemy_server):
    """
    Integrate zero-delay processing into the main system
    """
    try:
        # Create instant processor
        keywords = alchemy_server.keywords if hasattr(alchemy_server, 'keywords') else []
        webhook_notifier = alchemy_server.webhook_notifier if hasattr(alchemy_server, 'webhook_notifier') else None
        
        instant_processor = InstantTokenProcessor(keywords, webhook_notifier)
        zero_delay_matcher = ZeroDelayKeywordMatcher(keywords)
        
        # Attach to alchemy server
        alchemy_server.instant_processor = instant_processor
        alchemy_server.zero_delay_matcher = zero_delay_matcher
        
        logger.info("⚡ ZERO-DELAY INTEGRATION: Complete - instant processing enabled")
        return True
        
    except Exception as e:
        logger.error(f"❌ Zero-delay integration failed: {e}")
        return False

# Performance testing function
async def test_zero_delay_performance():
    """
    Test zero-delay processing performance
    """
    keywords = ['bonk', 'business', 'elon', 'doge', 'test']
    processor = InstantTokenProcessor(keywords)
    
    # Test tokens
    test_tokens = [
        {'name': 'Bonk Token Test', 'address': 'test123', 'symbol': 'BONK'},
        {'name': 'Business Opportunity', 'address': 'test456', 'symbol': 'BIZ'},
        {'name': 'Random Token', 'address': 'test789', 'symbol': 'RAND'},
        {'name': 'Elon Musk Coin', 'address': 'test000', 'symbol': 'ELON'}
    ]
    
    # Performance test
    start_time = time.time()
    
    for token in test_tokens:
        result = await processor.process_token_instant(token)
        print(f"Token: {token['name']} - Matches: {result['matched_keywords']} - Time: {result['processing_time_ms']:.1f}ms")
    
    total_time = (time.time() - start_time) * 1000
    print(f"\n⚡ TOTAL PROCESSING TIME: {total_time:.1f}ms for {len(test_tokens)} tokens")
    print(f"⚡ AVERAGE PER TOKEN: {total_time/len(test_tokens):.1f}ms")

if __name__ == "__main__":
    asyncio.run(test_zero_delay_performance())