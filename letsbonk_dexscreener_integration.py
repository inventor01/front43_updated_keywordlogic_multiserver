#!/usr/bin/env python3
"""
LetsBonk DexScreener Integration Module
Provides DexScreener API integration for token validation and metadata
"""

import logging
import requests
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class LetsBonkDexScreenerIntegration:
    """DexScreener integration for LetsBonk token validation"""
    
    def __init__(self):
        self.base_url = "https://api.dexscreener.com/latest/dex"
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def validate_token(self, token_address: str) -> bool:
        """Validate token exists on DexScreener"""
        try:
            # Check cache first
            cache_key = f"validate_{token_address}"
            if cache_key in self.cache:
                cached_time, result = self.cache[cache_key]
                if time.time() - cached_time < self.cache_ttl:
                    return result
            
            # Query DexScreener API
            url = f"{self.base_url}/tokens/{token_address}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                result = len(data.get('pairs', [])) > 0
                self.cache[cache_key] = (time.time(), result)
                return result
            
            return False
            
        except Exception as e:
            logger.debug(f"DexScreener validation failed: {e}")
            return False
    
    def get_token_metadata(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get token metadata from DexScreener"""
        try:
            # Check cache first
            cache_key = f"metadata_{token_address}"
            if cache_key in self.cache:
                cached_time, result = self.cache[cache_key]
                if time.time() - cached_time < self.cache_ttl:
                    return result
            
            # Query DexScreener API
            url = f"{self.base_url}/tokens/{token_address}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                if pairs:
                    # Get the most liquid pair
                    best_pair = max(pairs, key=lambda p: float(p.get('liquidity', {}).get('usd', 0)))
                    
                    metadata = {
                        'name': best_pair.get('baseToken', {}).get('name', ''),
                        'symbol': best_pair.get('baseToken', {}).get('symbol', ''),
                        'address': token_address,
                        'price_usd': best_pair.get('priceUsd'),
                        'liquidity_usd': best_pair.get('liquidity', {}).get('usd'),
                        'market_cap': best_pair.get('marketCap'),
                        'dex': best_pair.get('dexId'),
                        'pair_address': best_pair.get('pairAddress')
                    }
                    
                    self.cache[cache_key] = (time.time(), metadata)
                    return metadata
            
            return None
            
        except Exception as e:
            logger.debug(f"DexScreener metadata fetch failed: {e}")
            return None

# Global instance
dexscreener_integration = LetsBonkDexScreenerIntegration()

def validate_with_dexscreener(token_address: str) -> bool:
    """Validate token using DexScreener API"""
    return dexscreener_integration.validate_token(token_address)

def get_dexscreener_metadata(token_address: str) -> Optional[Dict[str, Any]]:
    """Get token metadata from DexScreener"""
    return dexscreener_integration.get_token_metadata(token_address)

logger.info("✅ LetsBonk DexScreener integration initialized")