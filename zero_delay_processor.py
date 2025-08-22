#!/usr/bin/env python3
"""
Zero-Delay Token Processor - Instant Detection and Processing
"""

import asyncio
import time
import logging
from concurrent.futures import ThreadPoolExecutor
import requests
from threading import Lock

logger = logging.getLogger(__name__)

class ZeroDelayProcessor:
    def __init__(self, webhook_notifier=None, keywords=None):
        self.webhook_notifier = webhook_notifier
        self.keywords = keywords or []
        self.executor = ThreadPoolExecutor(max_workers=10)  # Parallel processing
        self.cache = {}  # In-memory cache for instant lookups
        self.processing_lock = Lock()
        
    async def instant_process_token(self, token_data):
        """
        Process token with zero delay using parallel operations
        """
        start_time = time.time()
        
        # Immediate keyword check (no external calls)
        token_name = token_data.get('name', '').lower()
        token_address = token_data.get('address', '')
        
        # Ultra-fast keyword matching
        matched_keywords = []
        for keyword in self.keywords:
            if keyword.lower() in token_name:
                matched_keywords.append(keyword)
        
        # If keyword match found, send notification immediately
        if matched_keywords:
            # Fire notification without waiting
            asyncio.create_task(self._fire_instant_notification(token_data, matched_keywords[0]))
            
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        logger.info(f"⚡ INSTANT PROCESSING: {token_name} in {processing_time:.1f}ms")
        
        return {
            'processed': True,
            'matched_keywords': matched_keywords,
            'processing_time_ms': processing_time,
            'timestamp': time.time()
        }
    
    async def _fire_instant_notification(self, token_data, keyword):
        """
        Send notification without any blocking operations
        """
        try:
            if self.webhook_notifier:
                # Non-blocking notification
                asyncio.create_task(self.webhook_notifier.send_token_notification(token_data, keyword))
                logger.info(f"🚀 INSTANT ALERT: {token_data.get('name')} matched '{keyword}'")
        except Exception as e:
            logger.debug(f"Notification error: {e}")
    
    def parallel_name_extraction(self, token_address):
        """
        Ultra-fast name extraction using parallel requests
        """
        try:
            # Multiple API calls in parallel for redundancy
            urls = [
                f"https://api.dexscreener.com/latest/dex/tokens/{token_address}",
                f"https://api.birdeye.so/public/token/{token_address}",
                f"https://api.jupiter.ag/price/v2?ids={token_address}"
            ]
            
            # Submit all requests simultaneously
            futures = []
            for url in urls:
                future = self.executor.submit(self._fast_request, url)
                futures.append(future)
            
            # Return first successful response
            for future in futures:
                try:
                    result = future.result(timeout=0.5)  # 500ms max wait
                    if result:
                        return result
                except:
                    continue
                    
            return None
            
        except Exception as e:
            logger.debug(f"Parallel extraction failed: {e}")
            return None
    
    def _fast_request(self, url):
        """
        Ultra-fast HTTP request with minimal timeout
        """
        try:
            response = requests.get(url, timeout=0.3)  # 300ms timeout
            if response.status_code == 200:
                data = response.json()
                
                # Extract name from different API formats
                if 'pairs' in data and data['pairs']:
                    return data['pairs'][0].get('baseToken', {}).get('name')
                elif 'name' in data:
                    return data['name']
                elif 'data' in data and isinstance(data['data'], dict):
                    return data['data'].get('name')
                    
        except Exception:
            pass
        return None

    async def process_batch_instant(self, tokens):
        """
        Process multiple tokens simultaneously with zero delay
        """
        tasks = []
        for token in tokens:
            task = asyncio.create_task(self.instant_process_token(token))
            tasks.append(task)
        
        # Process all tokens in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_count = sum(1 for r in results if isinstance(r, dict) and r.get('processed'))
        matched_count = sum(len(r.get('matched_keywords', [])) for r in results if isinstance(r, dict))
        
        logger.info(f"⚡ BATCH PROCESSED: {processed_count} tokens, {matched_count} matches in parallel")
        
        return results

# Ultra-fast keyword matcher
class InstantKeywordMatcher:
    def __init__(self, keywords):
        self.keywords = set(kw.lower() for kw in keywords)
        self.keyword_map = {kw.lower(): kw for kw in keywords}  # Preserve original case
        
    def instant_match(self, text):
        """
        Instant keyword matching using set operations (O(1) lookup)
        """
        if not text:
            return []
            
        text_lower = text.lower()
        matches = []
        
        # Direct exact matches (fastest)
        for keyword in self.keywords:
            if keyword in text_lower:
                matches.append(self.keyword_map[keyword])
        
        return matches
    
    def batch_match(self, texts):
        """
        Process multiple texts simultaneously
        """
        results = []
        for text in texts:
            matches = self.instant_match(text)
            results.append({
                'text': text,
                'matches': matches,
                'match_count': len(matches)
            })
        return results

# Integration function for main system
def create_zero_delay_processor(webhook_notifier, keywords):
    """
    Create and configure zero-delay processor
    """
    processor = ZeroDelayProcessor(webhook_notifier, keywords)
    matcher = InstantKeywordMatcher(keywords)
    
    logger.info(f"⚡ ZERO-DELAY PROCESSOR: Initialized with {len(keywords)} keywords")
    logger.info("🚀 ULTRA-FAST MODE: Sub-100ms processing target")
    
    return processor, matcher