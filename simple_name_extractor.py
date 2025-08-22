#!/usr/bin/env python3
"""
Simple Name Extractor - Optimized for Zero Delay Processing
"""

import requests
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

logger = logging.getLogger(__name__)

class SimpleNameExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.cache = {}  # Simple in-memory cache
        
    def extract_name_instant(self, token_address):
        """
        Extract token name with minimal delay - target <100ms
        """
        start_time = time.time()
        
        # Check cache first
        if token_address in self.cache:
            cached_result = self.cache[token_address]
            if time.time() - cached_result['timestamp'] < 300:  # 5 minute cache
                logger.debug(f"⚡ CACHE HIT: {token_address[:10]}... → {cached_result['name']}")
                return cached_result['name']
        
        # Try DexScreener API with minimal timeout
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            response = self.session.get(url, timeout=0.5)  # Ultra-short timeout
            
            if response.status_code == 200:
                data = response.json()
                if 'pairs' in data and data['pairs']:
                    name = data['pairs'][0].get('baseToken', {}).get('name')
                    if name:
                        # Cache the result
                        self.cache[token_address] = {
                            'name': name,
                            'timestamp': time.time()
                        }
                        
                        extraction_time = (time.time() - start_time) * 1000
                        logger.info(f"⚡ INSTANT EXTRACTION: {name} in {extraction_time:.1f}ms")
                        return name
        except Exception as e:
            logger.debug(f"Fast extraction failed for {token_address[:10]}...: {e}")
        
        # Failed - return None for instant processing
        extraction_time = (time.time() - start_time) * 1000
        logger.debug(f"⚡ INSTANT FAIL: {token_address[:10]}... in {extraction_time:.1f}ms")
        return None
    
    def batch_extract_instant(self, token_addresses):
        """
        Extract multiple token names in parallel with zero delay
        """
        if not token_addresses:
            return {}
        
        results = {}
        batch_start = time.time()
        
        # Use ThreadPoolExecutor for parallel requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_address = {
                executor.submit(self.extract_name_instant, addr): addr 
                for addr in token_addresses
            }
            
            for future in as_completed(future_to_address, timeout=1.0):  # 1 second max for batch
                address = future_to_address[future]
                try:
                    name = future.result()
                    results[address] = name
                except Exception as e:
                    logger.debug(f"Batch extraction error for {address[:10]}...: {e}")
                    results[address] = None
        
        batch_time = (time.time() - batch_start) * 1000
        success_count = sum(1 for name in results.values() if name)
        
        logger.info(f"⚡ BATCH EXTRACTION: {success_count}/{len(token_addresses)} names in {batch_time:.1f}ms")
        
        return results

class ZeroDelayTokenProcessor:
    """
    Zero-delay token processing combining instant name extraction and keyword matching
    """
    def __init__(self, keywords, name_extractor=None):
        self.keywords = set(kw.lower() for kw in keywords)
        self.keyword_lookup = {kw.lower(): kw for kw in keywords}
        self.name_extractor = name_extractor or SimpleNameExtractor()
        
        logger.info(f"⚡ ZERO-DELAY PROCESSOR: {len(self.keywords)} keywords ready for instant matching")
    
    def process_token_zero_delay(self, token_data):
        """
        Process token with absolute zero delay
        Target: <50ms total processing
        """
        start_time = time.time()
        
        # Step 1: Instant keyword matching on existing name (0-5ms)
        existing_name = token_data.get('name', '').lower()
        matched_keywords = []
        
        for keyword in self.keywords:
            if keyword in existing_name:
                matched_keywords.append(self.keyword_lookup[keyword])
        
        # If immediate match found, return instantly
        if matched_keywords:
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"⚡ INSTANT MATCH: {token_data.get('name')} → {matched_keywords[0]} in {processing_time:.1f}ms")
            
            return {
                'status': 'instant_match',
                'matched_keywords': matched_keywords,
                'processing_time_ms': processing_time,
                'name_used': token_data.get('name'),
                'requires_notification': True
            }
        
        # Step 2: Try instant name extraction (only if no immediate match)
        token_address = token_data.get('address')
        if token_address:
            extracted_name = self.name_extractor.extract_name_instant(token_address)
            
            if extracted_name:
                # Check extracted name for keywords
                extracted_name_lower = extracted_name.lower()
                for keyword in self.keywords:
                    if keyword in extracted_name_lower:
                        matched_keywords.append(self.keyword_lookup[keyword])
                
                if matched_keywords:
                    processing_time = (time.time() - start_time) * 1000
                    logger.info(f"⚡ EXTRACTED MATCH: {extracted_name} → {matched_keywords[0]} in {processing_time:.1f}ms")
                    
                    return {
                        'status': 'extracted_match',
                        'matched_keywords': matched_keywords,
                        'processing_time_ms': processing_time,
                        'name_used': extracted_name,
                        'requires_notification': True
                    }
        
        # No match found
        processing_time = (time.time() - start_time) * 1000
        return {
            'status': 'no_match',
            'matched_keywords': [],
            'processing_time_ms': processing_time,
            'name_used': token_data.get('name', 'unknown'),
            'requires_notification': False
        }
    
    def batch_process_zero_delay(self, tokens):
        """
        Process multiple tokens with zero delay
        """
        if not tokens:
            return []
        
        results = []
        batch_start = time.time()
        
        for token in tokens:
            result = self.process_token_zero_delay(token)
            results.append(result)
        
        batch_time = (time.time() - batch_start) * 1000
        matched_count = sum(1 for r in results if r['requires_notification'])
        
        logger.info(f"⚡ ZERO-DELAY BATCH: {len(tokens)} tokens, {matched_count} matches in {batch_time:.1f}ms")
        
        return results

def integrate_zero_delay_system(alchemy_server):
    """
    Integrate zero-delay processing into the main monitoring system
    """
    try:
        # Create zero-delay components
        name_extractor = SimpleNameExtractor()
        keywords = getattr(alchemy_server, 'keywords', [])
        zero_delay_processor = ZeroDelayTokenProcessor(keywords, name_extractor)
        
        # Attach to server
        alchemy_server.zero_delay_processor = zero_delay_processor
        alchemy_server.simple_name_extractor = name_extractor
        
        logger.info("⚡ ZERO-DELAY INTEGRATION: Complete - sub-50ms processing enabled")
        return True
        
    except Exception as e:
        logger.error(f"❌ Zero-delay integration failed: {e}")
        return False

if __name__ == "__main__":
    # Test zero-delay processing
    test_keywords = ['bonk', 'business', 'test']
    processor = ZeroDelayTokenProcessor(test_keywords)
    
    test_tokens = [
        {'name': 'Bonk Token Test', 'address': 'test123'},
        {'name': 'Business Token', 'address': 'test456'},
        {'name': 'Random Token', 'address': 'test789'}
    ]
    
    results = processor.batch_process_zero_delay(test_tokens)
    
    for i, result in enumerate(results):
        print(f"Token {i+1}: {result['status']} - {result['processing_time_ms']:.1f}ms - Matches: {result['matched_keywords']}")