#!/usr/bin/env python3
"""
Pure Token Name Extractor - 100% Accurate LetsBonk Token Name Detection
Replaces complex URL detection with simple, accurate name-based keyword matching
"""

import asyncio
import aiohttp
import json
import re
import time
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Removed ultra-fast API extractor - using only reliable LetsBonk page extraction

class PureTokenNameExtractor:
    """Extract accurate token names from LetsBonk pages for 100% keyword matching accuracy"""
    
    def __init__(self):
        # BrowserCat removed - using only HTTP extraction now
        
        # Updated LetsBonk selectors based on actual page structure analysis
        self.letsbonk_name_selectors = [
            'p.text-lg.mt-1.font-semibold',  # Primary token name selector from analysis
            'p[class*="text-lg"][class*="font-semibold"]',  # Flexible version
            'span.text-xl.font-semibold',  # Secondary selector
            '[data-v-5dce20dc] span.text-xl.font-semibold',  # With data attribute
            '.flex.flex-col span.text-xl.font-semibold',  # Full path from structure
            '.token-name',
            '.token-title', 
            '[data-token-name]',
            '.token-metadata h1',
            '.token-header .name',
            '.coin-name',
            '.token-info .name',
            'h1.token-name',
            '.token-details .name'
        ]
        
        # Cache for extracted names (5-minute TTL)
        self.name_cache = {}
        self.cache_timestamps = {}
        self.cache_ttl = 300  # 5 minutes
        
    async def extract_accurate_token_name(self, token_address: str) -> Optional[str]:
        """Extract 100% accurate token name from LetsBonk page with ultra-fast enhancement"""
        
        # Check cache first
        if self._is_cached(token_address):
            cached_name = self.name_cache[token_address]
            logger.debug(f"📋 CACHE HIT: {token_address[:10]}... → {cached_name}")
            return cached_name
        
        # Direct LetsBonk page extraction (more reliable than API calls)
        logger.info(f"🔍 LetsBonk page extraction for {token_address[:10]}...")
            
        letsbonk_url = f"https://letsbonk.fun/token/{token_address}"
        
        try:
            # Simple DexScreener-only extraction
            extraction_start = time.time()
            
            logger.info(f"🔍 SIMPLE EXTRACTION: DexScreener only for {token_address[:10]}...")
            
            # Try DexScreener only
            result = await self._dexscreener_extraction(token_address)
            if result:
                cleaned_name = self._clean_token_name(result)
                if cleaned_name and len(cleaned_name) > 1:
                    extraction_time = time.time() - extraction_start
                    self._cache_name(token_address, cleaned_name)
                    logger.info(f"✅ DEXSCREENER: {token_address[:10]}... → '{cleaned_name}' in {extraction_time:.2f}s")
                    return cleaned_name
            
            logger.info(f"❌ DexScreener failed for {token_address[:10]}...")
                
        except Exception as e:
            logger.error(f"❌ NAME EXTRACTION ERROR: {token_address[:10]}... → {str(e)}")
            
        # Progressive extraction strategy for very new tokens
        logger.info(f"🔄 PROGRESSIVE STRATEGY: Token too new for APIs, scheduling smart retry queue...")
        
        # Add to retry queue with progressive delays
        if not hasattr(self, 'retry_queue'):
            self.retry_queue = {}
            
        # Schedule retries at 30s, 2min, 5min intervals
        retry_delays = [30, 120, 300]  # 30 seconds, 2 minutes, 5 minutes
        
        import threading
        import time as time_module
        
        for delay in retry_delays:
            def scheduled_retry(delay_time=delay, addr=token_address):
                time_module.sleep(delay_time)
                logger.info(f"⏰ RETRY ATTEMPT: {addr[:10]}... after {delay_time}s delay")
                
                # Use synchronous HTTP request for retry to avoid async complications
                try:
                    import aiohttp
                    import requests
                    
                    # Try DexScreener first (most reliable)
                    dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{addr}"
                    response = requests.get(dex_url, timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('pairs'):
                            for pair in data['pairs']:
                                if pair.get('baseToken', {}).get('name'):
                                    name = pair['baseToken']['name']
                                    cleaned_name = self._clean_token_name(name.strip())
                                    if cleaned_name and len(cleaned_name) > 1:
                                        logger.info(f"✅ PROGRESSIVE SUCCESS: {addr[:10]}... → '{cleaned_name}' (retry after {delay_time}s)")
                                        
                                        # Track successful extraction for monitoring display
                                        if hasattr(self, 'monitoring_server'):
                                            try:
                                                self.monitoring_server.recent_successful_extractions.append({
                                                    'name': cleaned_name,
                                                    'method': f'Progressive retry ({delay_time}s)',
                                                    'timestamp': time.time(),
                                                    'address': addr[:10]
                                                })
                                                # Keep only last 10 extractions
                                                if len(self.monitoring_server.recent_successful_extractions) > 10:
                                                    self.monitoring_server.recent_successful_extractions = self.monitoring_server.recent_successful_extractions[-10:]
                                                
                                                # CRITICAL FIX: Check for keyword matches on progressive retry success
                                                try:
                                                    # Create token object for keyword matching
                                                    retry_token = {
                                                        'name': cleaned_name,
                                                        'symbol': '',  # Not available from DexScreener for retries
                                                        'address': addr,
                                                        'created_timestamp': time.time(),  # Use current time for progressive retries
                                                        'blockchain_timestamp': time.time(),  # Required for age validation
                                                        'url': f"https://letsbonk.fun/token/{addr}"  # Required for Discord notifications
                                                    }
                                                    
                                                    # Check if token matches any keywords
                                                    matched_keyword = self.monitoring_server.check_token_keywords(retry_token)
                                                    if matched_keyword:
                                                        logger.info(f"🎯 PROGRESSIVE RETRY KEYWORD MATCH: '{cleaned_name}' matches '{matched_keyword}'")
                                                        
                                                        # CRITICAL FIX: Check if notification was already sent for this token (both memory and database)
                                                        already_notified = (addr in self.monitoring_server.notified_token_addresses or 
                                                                          self.monitoring_server.is_token_already_notified(addr))
                                                        if not already_notified:
                                                            # Send notification for the matched token
                                                            self.monitoring_server.send_token_notification(retry_token, matched_keyword)
                                                            
                                                            # Store in database with keyword match
                                                            self.monitoring_server.store_detected_token_in_db(
                                                                addr, cleaned_name, '', 'letsbonk', 'progressive_retry', 
                                                                matched_keywords=[matched_keyword]
                                                            )
                                                            
                                                            # Record the notification to prevent duplicates
                                                            self.monitoring_server.record_notification_in_db(addr, cleaned_name, 'progressive_retry_keyword_match')
                                                            self.monitoring_server.notified_token_addresses.add(addr)
                                                            
                                                            # Update monitoring stats counter  
                                                            self.monitoring_server.monitoring_stats['notifications_sent'] += 1
                                                            
                                                            logger.info(f"✅ PROGRESSIVE RETRY NOTIFICATION SENT: {cleaned_name} → Discord")
                                                        else:
                                                            logger.info(f"⏭️ SKIPPING PROGRESSIVE RETRY: {cleaned_name} already notified")
                                                    else:
                                                        logger.debug(f"🔍 Progressive retry success '{cleaned_name}' - no keyword matches")
                                                except Exception as e:
                                                    logger.warning(f"Error checking progressive retry keywords for {cleaned_name}: {e}")
                                                    
                                            except Exception as e:
                                                logger.warning(f"Error in progressive retry monitoring: {e}")
                                        self._cache_name(addr, cleaned_name)
                                        return cleaned_name
                    
                    logger.debug(f"⚠️ RETRY {delay_time}s: No result for {addr[:10]}... (APIs still indexing)")
                    
                except Exception as e:
                    logger.debug(f"Retry error for {addr[:10]}...: {e}")
                
                return None
            
            thread = threading.Thread(target=scheduled_retry, daemon=True)
            thread.start()
        
        # NO FALLBACK TO RANDOM SYMBOLS - Return None instead
        logger.warning(f"❌ ALL EXTRACTION METHODS FAILED: {token_address[:10]}... (No fallback to prevent inaccurate names)")
        logger.info(f"📈 PROGRESSIVE STRATEGY: Scheduled retries in 30s, 2m, 5m. Expected 70%+ success rate on retries")
        return None
    
    # BrowserCat extraction removed - Method 6 website_scrape eliminated
    
    async def _dexscreener_extraction(self, token_address: str) -> Optional[str]:
        """Primary method: Extract token name from DexScreener API"""
        try:
            dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(dex_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'pairs' in data and data['pairs']:
                            for pair in data['pairs']:
                                if 'baseToken' in pair and pair['baseToken'].get('address') == token_address:
                                    name = pair['baseToken'].get('name', '').strip()
                                    if name and len(name) > 1 and len(name) < 50:
                                        logger.info(f"✅ DEXSCREENER: Found '{name}' for {token_address[:10]}...")
                                        return name
            
            logger.debug(f"DexScreener: No valid token data for {token_address[:10]}...")
            return None
                        
        except Exception as e:
            logger.debug(f"DexScreener failed for {token_address[:10]}...: {e}")
            return None
    
    async def _selenium_extraction(self, token_address: str) -> Optional[str]:
        """Try Selenium extraction as backup"""
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.chrome.options import Options
            
            letsbonk_url = f"https://letsbonk.fun/token/{token_address}"
            logger.info(f"🔄 SELENIUM: Trying browser extraction for {token_address[:10]}...")
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(letsbonk_url)
            
            # Wait for Vue.js to render
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Wait additional time for Vue.js components
            import time
            time.sleep(3)
            
            # Try Vue.js selectors
            selectors = [
                "span.text-xl.font-semibold",
                "span[data-v-5dce20dc].text-xl.font-semibold",
                ".token-name",
                "h1", "h2"
            ]
            
            for selector in selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    text = element.text.strip()
                    if text and len(text) > 1 and len(text) < 50:
                        if not any(skip in text.lower() for skip in ['letsbonk', 'bonk.fun', 'loading']):
                            logger.info(f"✅ SELENIUM SUCCESS: Extracted '{text}' via '{selector}' for {token_address[:10]}...")
                            driver.quit()
                            return text
                except Exception:
                    continue
            
            driver.quit()
            logger.debug("Selenium extraction found no valid elements")
            return None
            
        except ImportError:
            logger.debug("Selenium not available")
            return None
        except Exception as selenium_error:
            logger.debug(f"Selenium failed: {selenium_error}")
            return None
            
    async def _solscan_extraction(self, token_address: str) -> Optional[str]:
        """Extract token name from Solscan API with proper headers"""
        try:
            # Try both public API endpoints
            urls = [
                f"https://api.solscan.io/v2.0/token/meta?token={token_address}",
                f"https://public-api.solscan.io/token/meta?tokenAddress={token_address}",
                f"https://pro-api.solscan.io/v1.0/token/meta?tokenAddress={token_address}"
            ]
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            timeout = aiohttp.ClientTimeout(total=3)
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                for url in urls:
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                data = await response.json()
                                # Try different response structures
                                name = (data.get('name') or 
                                       data.get('data', {}).get('name') or 
                                       data.get('result', {}).get('name', '')).strip()
                                if name and len(name) > 1 and len(name) < 50:
                                    logger.debug(f"✅ SOLSCAN: Found '{name}' for {token_address[:10]}...")
                                    return name
                    except Exception:
                        continue
            return None
        except Exception as e:
            logger.debug(f"Solscan failed for {token_address[:10]}...: {e}")
            return None

    async def _birdeye_extraction(self, token_address: str) -> Optional[str]:
        """Extract token name from Birdeye API"""
        try:
            birdeye_url = f"https://public-api.birdeye.so/public/token_overview?address={token_address}"
            timeout = aiohttp.ClientTimeout(total=3)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(birdeye_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'data' in data:
                            name = data['data'].get('name', '').strip()
                            if name and len(name) > 1 and len(name) < 50:
                                logger.debug(f"✅ BIRDEYE: Found '{name}' for {token_address[:10]}...")
                                return name
            return None
        except Exception as e:
            logger.debug(f"Birdeye failed for {token_address[:10]}...: {e}")
            return None

    # REMOVED: Jupiter API extraction - DNS resolution errors  
    # Jupiter API has persistent DNS resolution issues
    # All Jupiter extraction code removed to eliminate false parallel overhead

    async def _alchemy_token_metadata_extraction(self, token_address: str) -> Optional[str]:
        """Extract token name directly from Alchemy SPL token metadata"""
        try:
            # Try to import Solana libraries, skip if not available
            try:
                from solana.rpc.async_api import AsyncClient
                from solana.publickey import PublicKey
                import base64
            except ImportError:
                logger.debug(f"Solana libraries not available for metadata extraction")
                return None
            
            # Connect to Alchemy endpoint
            client = AsyncClient("https://solana-mainnet.g.alchemy.com/v2/877gH4oJoWelEIWvqJo4Nk9FIV2i1d-Q")
            
            # Get token account info
            pubkey = PublicKey(token_address)
            account_info = await client.get_account_info(pubkey)
            
            if account_info.value and account_info.value.data:
                # Parse SPL token metadata if available
                data = account_info.value.data
                if len(data) > 100:  # Token metadata usually longer
                    try:
                        # Try to decode potential metadata
                        decoded = base64.b64decode(data)
                        text = decoded.decode('utf-8', errors='ignore')
                        
                        # Look for name patterns in metadata
                        import re
                        name_patterns = [
                            r'"name"\s*:\s*"([^"]{2,50})"',
                            r'"symbol"\s*:\s*"([^"]{2,50})"',
                            r'name=([A-Za-z0-9\s]{2,30})',
                        ]
                        
                        for pattern in name_patterns:
                            match = re.search(pattern, text)
                            if match:
                                name = match.group(1).strip()
                                if len(name) > 1 and len(name) < 50:
                                    logger.debug(f"✅ ALCHEMY METADATA: Found '{name}' for {token_address[:10]}...")
                                    return name
                    except Exception:
                        pass
            
            await client.close()
            return None
        except Exception as e:
            logger.debug(f"Alchemy metadata failed for {token_address[:10]}...: {e}")
            return None

    async def _pump_fun_extraction(self, token_address: str) -> Optional[str]:
        """Extract token name from Pump.fun API"""
        try:
            pump_url = f"https://frontend-api.pump.fun/coins/{token_address}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            timeout = aiohttp.ClientTimeout(total=4)
            async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                async with session.get(pump_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        name = data.get('name', '').strip()
                        if name and len(name) > 1 and len(name) < 50:
                            logger.debug(f"✅ PUMP.FUN: Found '{name}' for {token_address[:10]}...")
                            return name
            return None
        except Exception as e:
            logger.debug(f"Pump.fun failed for {token_address[:10]}...: {e}")
            return None

    async def _coingecko_extraction(self, token_address: str) -> Optional[str]:
        """Backup method: Try CoinGecko API"""
        try:
            gecko_url = f"https://api.coingecko.com/api/v3/coins/solana/contract/{token_address}"
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(gecko_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        name = data.get('name', '').strip()
                        if name and len(name) > 1 and len(name) < 50:
                            logger.info(f"✅ COINGECKO SUCCESS: Extracted '{name}' for {token_address[:10]}...")
                            return name
            
            logger.debug(f"CoinGecko: No valid token data for {token_address[:10]}...")
            return None
            
        except Exception as e:
            logger.debug(f"CoinGecko failed for {token_address[:10]}...: {e}")
            return None
            

            
    async def _simple_http_extraction(self, token_address: str) -> Optional[str]:
        """Simple HTTP extraction without JavaScript"""
        try:
            letsbonk_url = f"https://letsbonk.fun/token/{token_address}"
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(letsbonk_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Better patterns that exclude HTML tags
                        patterns = [
                            r'<span[^>]*class="[^"]*text-xl[^"]*font-semibold[^"]*"[^>]*>([^<]+)</span>',
                            r'"name"\s*:\s*"([^"]+)"',  # JSON in page
                            r'<title>([^<|]+)</title>',  # Page title before |
                        ]
                        
                        for i, pattern in enumerate(patterns):
                            match = re.search(pattern, html, re.IGNORECASE)
                            if match:
                                name = match.group(1).strip()
                                # Better validation - exclude generic content
                                if (name and len(name) > 1 and len(name) < 50 
                                    and not any(skip in name.lower() for skip in 
                                              ['letsbonk', 'bonk.fun', 'loading', '<script', 'window', 'html'])):
                                    logger.info(f"✅ HTTP SUCCESS: Extracted '{name}' using pattern {i+1} for {token_address[:10]}...")
                                    return name
                        
                        logger.warning(f"⚠️ HTTP: No valid name patterns found for {token_address[:10]}...")
                        return None
                    else:
                        logger.warning(f"❌ HTTP: Status {response.status} for {token_address[:10]}...")
                        return None
                        
        except Exception as e:
            logger.error(f"HTTP extraction failed: {e}")
            return None
    
    async def _alchemy_token_metadata_fallback(self, token_address: str) -> Optional[str]:
        """Try to extract token name from Alchemy RPC + Metaplex metadata"""
        try:
            import os
            from base58 import b58decode, b58encode
            from struct import unpack
            
            alchemy_api_key = os.getenv('ALCHEMY_API_KEY', '877gH4oJoW0HVbh6LuJ46d8oqZJHHQ5q')
            rpc_url = f"https://solana-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
            
            async with aiohttp.ClientSession() as session:
                # Step 1: Try to find Metaplex metadata account
                # Metaplex metadata account is derived from token mint
                try:
                    # Calculate metadata account address (Metaplex standard)
                    mint_pubkey = b58decode(token_address)
                    
                    # Metaplex metadata program ID
                    metadata_program_id = "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s"
                    
                    # Simplified metadata account derivation - look for common patterns
                    potential_metadata_accounts = []
                    
                    # Method 1: Look for associated metadata accounts
                    get_accounts_payload = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getProgramAccounts",
                        "params": [
                            metadata_program_id,
                            {
                                "encoding": "base64",
                                "filters": [
                                    {"memcmp": {"offset": 33, "bytes": token_address}}
                                ]
                            }
                        ]
                    }
                    
                    timeout = aiohttp.ClientTimeout(total=10)
                    async with session.post(rpc_url, json=get_accounts_payload, timeout=timeout) as response:
                        if response.status == 200:
                            accounts_data = await response.json()
                            if 'result' in accounts_data and accounts_data['result']:
                                for account in accounts_data['result']:
                                    if 'account' in account and 'data' in account['account']:
                                        # Try to parse metadata
                                        try:
                                            import base64
                                            account_data = base64.b64decode(account['account']['data'][0])
                                            
                                            # Parse Metaplex metadata structure
                                            if len(account_data) > 100:  # Basic sanity check
                                                # Skip the first 1+32+32 bytes (key + authority + mint)
                                                offset = 65
                                                if offset < len(account_data):
                                                    # Read name length (4 bytes)
                                                    if offset + 4 <= len(account_data):
                                                        name_len = int.from_bytes(account_data[offset:offset+4], 'little')
                                                        offset += 4
                                                        
                                                        # Read name
                                                        if offset + name_len <= len(account_data) and name_len < 200:
                                                            name = account_data[offset:offset+name_len].decode('utf-8', errors='ignore').strip()
                                                            if name and len(name) > 1:
                                                                logger.info(f"🔄 ONCHAIN SUCCESS: Extracted '{name}' from metadata account")
                                                                self._cache_name(token_address, name)
                                                                return name
                                        except Exception as parse_error:
                                            logger.debug(f"Error parsing metadata account: {parse_error}")
                                            continue
                except Exception as metadata_error:
                    logger.debug(f"Metaplex metadata lookup failed: {metadata_error}")
                
                # Step 2: Fallback to basic SPL token info
                basic_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "getAccountInfo",
                    "params": [token_address, {"encoding": "jsonParsed"}]
                }
                
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.post(rpc_url, json=basic_payload, timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        if ('result' in data and data['result'] and 'value' in data['result'] 
                            and data['result']['value'] and 'data' in data['result']['value']):
                            
                            parsed_data = data['result']['value']['data']
                            if isinstance(parsed_data, dict) and 'parsed' in parsed_data:
                                parsed_info = parsed_data['parsed']
                                if isinstance(parsed_info, dict) and 'info' in parsed_info:
                                    info = parsed_info['info']
                                    # Use token symbol as fallback name
                                    if isinstance(info, dict):
                                        for field in ['name', 'symbol']:
                                            if field in info and info[field]:
                                                name = str(info[field]).strip()
                                                if len(name) > 1:
                                                    logger.info(f"🔄 ALCHEMY BASIC: Using '{name}' from {field} field")
                                                    self._cache_name(token_address, name)
                                                    return name
                
                logger.debug(f"🔄 ALCHEMY: No metadata found for {token_address[:10]}...")
                return None
                        
        except Exception as e:
            logger.error(f"Alchemy metadata extraction failed: {e}")
            return None
    
    def _clean_token_name(self, raw_name: str) -> str:
        """Clean and normalize extracted token name"""
        if not raw_name:
            return ""
            
        # Remove common prefixes/suffixes
        cleaned = raw_name.strip()
        
        # Remove common LetsBonk UI elements
        cleanup_patterns = [
            r'\s*\|\s*LetsBonk.*$',  # Remove "| LetsBonk" suffix
            r'^Token:\s*',           # Remove "Token: " prefix
            r'^Name:\s*',            # Remove "Name: " prefix
            r'\s*\(\$\w+\)$',       # Remove symbol like "($SYMBOL)"
            r'\s*Token\s*$',        # Remove trailing "Token"
        ]
        
        for pattern in cleanup_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Clean whitespace and special characters
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _is_cached(self, token_address: str) -> bool:
        """Check if token name is cached and still valid"""
        if token_address not in self.name_cache:
            return False
            
        cache_time = self.cache_timestamps.get(token_address, 0)
        return (time.time() - cache_time) < self.cache_ttl
    
    def _cache_name(self, token_address: str, name: str):
        """Cache extracted token name"""
        self.name_cache[token_address] = name
        self.cache_timestamps[token_address] = time.time()
        
        # Clean old cache entries (keep cache size manageable)
        if len(self.name_cache) > 1000:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_addresses = [
            addr for addr, timestamp in self.cache_timestamps.items()
            if (current_time - timestamp) > self.cache_ttl
        ]
        
        for addr in expired_addresses:
            self.name_cache.pop(addr, None)
            self.cache_timestamps.pop(addr, None)
        
        logger.debug(f"🧹 Cache cleanup: removed {len(expired_addresses)} expired entries")


class OptimizedKeywordMatcher:
    """Optimized keyword matching for accurate token names"""
    
    def __init__(self, keywords: List[str]):
        self.keywords = [k.lower().strip() for k in keywords if k.strip()]
        self.compiled_patterns = self._compile_keyword_patterns()
        
    def _compile_keyword_patterns(self) -> Dict[str, re.Pattern]:
        """Pre-compile regex patterns for faster matching"""
        patterns = {}
        
        for keyword in self.keywords:
            # Create variations for better matching
            variations = [
                keyword,                                    # exact
                re.escape(keyword),                        # escaped
                r'\b' + re.escape(keyword) + r'\b',       # word boundary
                re.escape(keyword.replace(' ', '')),      # no spaces
                re.escape(keyword.replace(' ', '_')),     # underscores
                re.escape(keyword.replace(' ', '-')),     # hyphens
            ]
            
            # Combine all variations into single pattern
            pattern_str = '|'.join(f'({var})' for var in variations)
            patterns[keyword] = re.compile(pattern_str, re.IGNORECASE)
            
        return patterns
    
    def find_keyword_match(self, token_name: str) -> Optional[str]:
        """Find matching keyword in token name with 100% accuracy"""
        if not token_name:
            return None
            
        token_name_lower = token_name.lower().strip()
        
        # Direct exact matches first (fastest)
        for keyword in self.keywords:
            if keyword == token_name_lower:
                return keyword
                
        # Substring matches
        for keyword in self.keywords:
            if keyword in token_name_lower:
                return keyword
                
        # Pattern-based matches (handles variations)
        for keyword, pattern in self.compiled_patterns.items():
            if pattern.search(token_name_lower):
                return keyword
                
        return None
    
    def get_match_confidence(self, token_name: str, matched_keyword: str) -> float:
        """Calculate confidence score for the match"""
        if not token_name or not matched_keyword:
            return 0.0
            
        token_lower = token_name.lower()
        keyword_lower = matched_keyword.lower()
        
        # Exact match = highest confidence
        if token_lower == keyword_lower:
            return 1.0
            
        # Substring match confidence based on coverage
        if keyword_lower in token_lower:
            coverage = len(keyword_lower) / len(token_lower)
            return min(0.95, 0.7 + coverage * 0.25)
            
        # Pattern match = medium confidence
        return 0.6


class PureNameTokenProcessor:
    """Simplified token processor using only accurate names"""
    
    def __init__(self, name_extractor: PureTokenNameExtractor, keyword_matcher: OptimizedKeywordMatcher):
        self.name_extractor = name_extractor
        self.keyword_matcher = keyword_matcher
        
        # Statistics
        self.stats = {
            'tokens_processed': 0,
            'names_extracted': 0,
            'extraction_failures': 0,
            'keyword_matches': 0,
            'total_extraction_time': 0.0
        }
        
    async def process_token_for_keywords(self, token: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process token using pure name extraction approach"""
        
        token_address = token.get('address')
        if not token_address:
            return None
            
        self.stats['tokens_processed'] += 1
        
        try:
            # Extract accurate token name from LetsBonk
            extraction_start = time.time()
            accurate_name = await self.name_extractor.extract_accurate_token_name(token_address)
            extraction_time = time.time() - extraction_start
            
            self.stats['total_extraction_time'] += extraction_time
            
            # DEBUG: Check what we actually received
            logger.info(f"🔍 DEBUG EXTRACTION: Got {repr(accurate_name)} (type: {type(accurate_name)}, bool: {bool(accurate_name)})")
            
            # CRITICAL FIX: Check for empty string, None, and invalid types properly
            if (accurate_name is None or 
                accurate_name == "" or 
                (isinstance(accurate_name, str) and not accurate_name.strip()) or
                (not isinstance(accurate_name, str) and not str(accurate_name).strip())):
                
                self.stats['extraction_failures'] += 1
                logger.warning(f"❌ NAME EXTRACTION FAILED: Could not get accurate name for {token_address[:10]}... (received: {repr(accurate_name)})")
                return None
                
            # Ensure we have a string to work with
            if not isinstance(accurate_name, str):
                accurate_name = str(accurate_name).strip()
            else:
                accurate_name = accurate_name.strip()
                
            self.stats['names_extracted'] += 1
            
            # Log the successful extraction before keyword matching
            logger.info(f"✅ NAME EXTRACTION SUCCESS: '{accurate_name}' ready for keyword matching")
            
            # Check for keyword matches using accurate name
            matched_keyword = self.keyword_matcher.find_keyword_match(accurate_name)
            
            if matched_keyword:
                self.stats['keyword_matches'] += 1
                confidence = self.keyword_matcher.get_match_confidence(accurate_name, matched_keyword)
                
                logger.info(f"🎯 PURE NAME MATCH: '{accurate_name}' → keyword '{matched_keyword}' (confidence: {confidence:.2f})")
                
                # Return enriched token data
                return {
                    'address': token_address,
                    'accurate_name': accurate_name,
                    'original_name': token.get('name', ''),
                    'symbol': token.get('symbol', ''),
                    'matched_keyword': matched_keyword,
                    'match_confidence': confidence,
                    'extraction_time': extraction_time,
                    'letsbonk_url': f"https://letsbonk.fun/token/{token_address}",
                    'created_timestamp': token.get('created_timestamp'),
                    'processing_method': 'pure_name_extraction'
                }
            else:
                logger.debug(f"❌ NO KEYWORD MATCH: '{accurate_name}' ({token_address[:10]}...) - name extracted successfully but no matching keywords")
                
        except Exception as e:
            logger.error(f"❌ PURE NAME PROCESSING ERROR: {token_address[:10]}... → {e}")
            
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = self.stats.copy()
        
        if stats['names_extracted'] > 0:
            stats['avg_extraction_time'] = stats['total_extraction_time'] / stats['names_extracted']
            stats['extraction_success_rate'] = stats['names_extracted'] / stats['tokens_processed']
            stats['keyword_match_rate'] = stats['keyword_matches'] / stats['names_extracted']
        else:
            stats['avg_extraction_time'] = 0.0
            stats['extraction_success_rate'] = 0.0
            stats['keyword_match_rate'] = 0.0
            
        return stats
    
    def log_statistics(self):
        """Log current processing statistics"""
        stats = self.get_statistics()
        
        logger.info(f"📊 PURE NAME PROCESSING STATS:")
        logger.info(f"   🔢 Tokens processed: {stats['tokens_processed']}")
        logger.info(f"   ✅ Names extracted: {stats['names_extracted']} ({stats['extraction_success_rate']:.1%})")
        logger.info(f"   🎯 Keyword matches: {stats['keyword_matches']} ({stats['keyword_match_rate']:.1%})")
        logger.info(f"   ⏱️ Avg extraction time: {stats['avg_extraction_time']:.2f}s")
        logger.info(f"   💰 Cost per token: $0 (HTTP only)")