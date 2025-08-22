"""
Ultimate Token Name Resolver - 100% Success Rate Target
Comprehensive approach using multiple data sources and methods
"""

import time
import logging
import requests
import asyncio
import aiohttp
from typing import Optional, Dict, List
from dataclasses import dataclass
import base58
import json

logger = logging.getLogger(__name__)

@dataclass
class TokenMetadata:
    name: str
    symbol: str
    source: str
    confidence: float

class UltimateNameResolver:
    """Comprehensive token name resolution with 100% success target"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Streamlined endpoints - ONLY AUTHENTIC DATA SOURCES
        self.endpoints = [
            self._dexscreener_api,
            self._letsbonk_api
            # REMOVED: _fallback_generation - only use real token names
        ]
    
    async def resolve_token_name(self, address: str, max_attempts: int = 8, wait_for_indexing: bool = False) -> TokenMetadata:
        """Resolve token name using all available methods with optional delay for 100% real names"""
        if wait_for_indexing:
            logger.info(f"🔍 DELAYED EXTRACTION: Resolving name for {address[:8]}... after indexing wait")
        else:
            logger.info(f"🔍 Resolving name for {address[:8]}... using {len(self.endpoints)} streamlined methods")
        
        results = []
        
        # Try each method sequentially until we get a good result
        for i, method in enumerate(self.endpoints):
            try:
                # Pass wait_for_indexing flag to DexScreener method
                if method == self._dexscreener_api:
                    result = await method(address, wait_for_indexing)
                else:
                    result = await method(address)
                if result and result.confidence > 0.7:
                    logger.info(f"✅ Method {i+1} SUCCESS: {result.name} [{result.source}] confidence: {result.confidence}")
                    return result
                elif result:
                    results.append(result)
                    logger.debug(f"⚠️ Method {i+1} partial: {result.name} confidence: {result.confidence}")
            except Exception as e:
                logger.debug(f"❌ Method {i+1} failed: {e}")
                continue
        
        # If no high-confidence result, return best available if authentic
        if results:
            best = max(results, key=lambda x: x.confidence)
            # Only return if confidence is reasonable (authentic data)
            if best.confidence >= 0.3:
                logger.info(f"📊 Best available: {best.name} [{best.source}] confidence: {best.confidence}")
                return best
            else:
                logger.warning(f"❌ SKIPPING LOW CONFIDENCE: {best.name} (confidence: {best.confidence})")
        
        # NO FALLBACK - Return None for failed extractions to avoid fake names
        logger.warning(f"❌ NAME EXTRACTION FAILED: {address[:8]}... - no authentic name available")
        return None
    
    async def _dexscreener_api(self, address: str, wait_for_indexing: bool = False) -> Optional[TokenMetadata]:
        """DexScreener API with optional wait for indexing to get 100% real names"""
        try:
            # If wait_for_indexing is True, add delay to let DexScreener index the token
            if wait_for_indexing:
                logger.info(f"⏰ WAITING FOR INDEXING: Allowing DexScreener 5 minutes to index {address[:8]}...")
                time.sleep(300)  # Wait 5 minutes for DexScreener to index the token
                logger.info(f"✅ INDEXING WAIT COMPLETE: Now extracting real name for {address[:8]}...")
            
            url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
            response = self.session.get(url, timeout=10)  # Longer timeout for delayed extraction
            
            logger.debug(f"DexScreener API response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                logger.debug(f"DexScreener pairs found: {len(pairs) if pairs else 0}")
                
                if pairs:
                    token_data = pairs[0].get('baseToken', {})
                    name = token_data.get('name')
                    symbol = token_data.get('symbol', 'BONK')
                    
                    logger.debug(f"DexScreener extracted name: '{name}', symbol: '{symbol}'")
                    
                    if name and len(name.strip()) > 2 and not name.startswith('Unknown'):
                        confidence = 0.95 if not name.startswith('LetsBonk Token') else 0.3
                        logger.info(f"✅ DEXSCREENER SUCCESS: {address[:8]}... → '{name.strip()}'")
                        return TokenMetadata(name.strip(), symbol, 'dexscreener_fast', confidence)
                        
        except Exception as e:
            logger.warning(f"DexScreener API failed for {address[:8]}...: {e}")
        
        return None
    
    async def _letsbonk_api(self, address: str) -> Optional[TokenMetadata]:
        """Fast LetsBonk.fun API"""
        try:
            url = f"https://letsbonk.fun/api/token/{address}"
            response = self.session.get(url, timeout=3)  # Reduced timeout
            
            if response.status_code == 200:
                data = response.json()
                name = data.get('name')
                symbol = data.get('symbol', 'BONK')
                
                if name and len(name.strip()) > 2:
                    confidence = 0.9 if not name.startswith('LetsBonk Token') else 0.3
                    return TokenMetadata(name.strip(), symbol, 'letsbonk_api_fast', confidence)
                    
        except Exception as e:
            logger.debug(f"Fast LetsBonk API failed: {e}")
        
        return None
    
# Removed: Solana RPC method - only generated placeholder names
    
# Removed: Birdeye API - 0% success due to authentication issues
    
# Removed: Jupiter API - low success rate for new LetsBonk tokens
    

# Removed: SolScan scraping - unreliable regex parsing
    
    # REMOVED: _fallback_generation method
    # Only use authentic token names from APIs - no synthetic/fallback names
    
    # Note: Removed underperforming methods:
    # - Birdeye API (0% success, authentication failures)
    # - Solana RPC (placeholder names only)  
    # - Jupiter API (limited coverage for new tokens)
    # - SolScan scraping (unreliable parsing)