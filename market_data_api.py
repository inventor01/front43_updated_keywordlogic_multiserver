"""
Market data API integration for token information
"""

import requests
import logging
from typing import Dict, List, Optional, Any
import time
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class MarketDataAPI:
    """Market data API for token information and pricing"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TokenMonitor/1.0'
        })
        
        # Cache for API responses (5 minute TTL)
        self.cache = TTLCache(maxsize=1000, ttl=300)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum seconds between requests
    
    def _rate_limit(self):
        """Apply rate limiting"""
        now = time.time()
        time_since_last = now - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def get_token_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get basic token information"""
        try:
            # Check cache first
            cache_key = f"token_info_{token_address}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            self._rate_limit()
            
            # Try DexScreener API
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                if pairs:
                    pair = pairs[0]  # Take first pair
                    token_info = {
                        'address': token_address,
                        'name': pair.get('baseToken', {}).get('name'),
                        'symbol': pair.get('baseToken', {}).get('symbol'),
                        'price_usd': pair.get('priceUsd'),
                        'market_cap': pair.get('marketCap'),
                        'liquidity': pair.get('liquidity', {}).get('usd'),
                        'volume_24h': pair.get('volume', {}).get('h24'),
                        'price_change_24h': pair.get('priceChange', {}).get('h24'),
                        'dexscreener_url': pair.get('url'),
                        'last_updated': time.time()
                    }
                    
                    # Cache the result
                    self.cache[cache_key] = token_info
                    return token_info
            
            logger.warning(f"No token info found for {token_address}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting token info for {token_address}: {e}")
            return None
    
    def get_token_data(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive token data"""
        return self.get_token_info(token_address)
    
    def search_tokens_by_keyword(self, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for tokens by keyword"""
        try:
            self._rate_limit()
            
            # Use DexScreener search
            url = f"https://api.dexscreener.com/latest/dex/search?q={keyword}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                results = []
                for pair in pairs[:limit]:
                    if pair and pair.get('baseToken'):
                        token_info = {
                            'address': pair.get('baseToken', {}).get('address'),
                            'name': pair.get('baseToken', {}).get('name'),
                            'symbol': pair.get('baseToken', {}).get('symbol'),
                            'price_usd': pair.get('priceUsd'),
                            'market_cap': pair.get('marketCap'),
                            'liquidity': pair.get('liquidity', {}).get('usd'),
                            'dexscreener_url': pair.get('url'),
                        }
                        results.append(token_info)
                
                return results
            
            return []
            
        except Exception as e:
            logger.error(f"Error searching tokens by keyword '{keyword}': {e}")
            return []
    
    def get_trending_tokens(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get trending tokens"""
        try:
            self._rate_limit()
            
            # This would require a trending API endpoint
            # For now, return empty list
            logger.info("Trending tokens API not implemented yet")
            return []
            
        except Exception as e:
            logger.error(f"Error getting trending tokens: {e}")
            return []
    
    def get_token_price_history(self, token_address: str, timeframe: str = "1h") -> List[Dict[str, Any]]:
        """Get token price history"""
        try:
            # This would require historical data API
            # For now, return empty list
            logger.info(f"Price history for {token_address} not implemented yet")
            return []
            
        except Exception as e:
            logger.error(f"Error getting price history for {token_address}: {e}")
            return []
    
    def clear_cache(self):
        """Clear the API response cache"""
        self.cache.clear()
        logger.info("Market data cache cleared")

# Global instance
market_data_api = MarketDataAPI()