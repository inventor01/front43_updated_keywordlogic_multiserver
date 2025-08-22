#!/usr/bin/env python3
"""
Speed-Optimized Cache for Token Name Extraction
Reduces repeated API calls and improves immediate success rate
"""

import time
import logging
from typing import Dict, Optional, List
import threading

logger = logging.getLogger(__name__)

class SpeedOptimizedCache:
    """High-performance cache for token names and patterns"""
    
    def __init__(self):
        self.name_cache = {}  # token_address -> (name, timestamp)
        self.pattern_cache = {}  # address_pattern -> names
        self.success_patterns = []  # Recently successful extraction patterns
        self.cache_lock = threading.Lock()
        self.cache_ttl = 3600  # 1 hour cache TTL
        
        # Pattern learning system
        self.successful_addresses = []  # Track successful addresses for pattern learning
        self.api_performance = {  # Track which APIs are fastest
            'dexscreener': {'success_count': 0, 'avg_time': 0},
            'pumpfun': {'success_count': 0, 'avg_time': 0},
            'jupiter': {'success_count': 0, 'avg_time': 0},
            'solscan': {'success_count': 0, 'avg_time': 0}
        }
        
    def get_cached_name(self, token_address: str) -> Optional[str]:
        """Get cached token name if available and fresh"""
        with self.cache_lock:
            if token_address in self.name_cache:
                name, timestamp = self.name_cache[token_address]
                if time.time() - timestamp < self.cache_ttl:
                    logger.debug(f"✅ CACHE HIT: {token_address[:10]}... → '{name}'")
                    return name
                else:
                    # Remove expired entry
                    del self.name_cache[token_address]
        return None
    
    def cache_name(self, token_address: str, name: str, api_source: Optional[str] = None, extraction_time: Optional[float] = None):
        """Cache successful extraction"""
        with self.cache_lock:
            self.name_cache[token_address] = (name, time.time())
            
            # Track successful patterns for future optimization
            if len(token_address) >= 10:
                pattern = token_address[:6] + "..." + token_address[-4:]
                if pattern not in self.pattern_cache:
                    self.pattern_cache[pattern] = []
                self.pattern_cache[pattern].append(name)
                
            # Update API performance stats
            if api_source and extraction_time:
                if api_source.lower() in self.api_performance:
                    stats = self.api_performance[api_source.lower()]
                    stats['success_count'] += 1
                    # Calculate rolling average
                    old_avg = stats['avg_time']
                    count = stats['success_count']
                    stats['avg_time'] = ((old_avg * (count - 1)) + extraction_time) / count
                    
        logger.debug(f"✅ CACHED: {token_address[:10]}... → '{name}' via {api_source}")
    
    def get_fastest_apis(self) -> List[str]:
        """Return APIs ordered by performance (fastest first)"""
        apis_by_performance = []
        
        for api, stats in self.api_performance.items():
            if stats['success_count'] > 0:
                # Score: success rate * speed (lower time = higher score)
                speed_score = 1.0 / (stats['avg_time'] + 0.1)  # Avoid division by zero
                total_score = stats['success_count'] * speed_score
                apis_by_performance.append((api, total_score))
        
        # Sort by performance score (descending)
        apis_by_performance.sort(key=lambda x: x[1], reverse=True)
        return [api for api, score in apis_by_performance]
    
    def predict_likely_success(self, token_address: str) -> bool:
        """Predict if this token is likely to be found quickly"""
        # Check for similar address patterns that were successful
        pattern = token_address[:6] + "..." + token_address[-4:]
        
        if pattern in self.pattern_cache:
            logger.debug(f"🎯 PATTERN MATCH: Similar addresses found for {token_address[:10]}...")
            return True
            
        # Check if address follows common successful patterns
        for successful_addr in self.successful_addresses[-20:]:  # Last 20 successful
            if (token_address[:3] == successful_addr[:3] or 
                token_address[-3:] == successful_addr[-3:]):
                logger.debug(f"🎯 PREFIX/SUFFIX MATCH: {token_address[:10]}...")
                return True
                
        return False
    
    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics"""
        with self.cache_lock:
            total_cached = len(self.name_cache)
            fresh_entries = sum(1 for name, timestamp in self.name_cache.values() 
                              if time.time() - timestamp < self.cache_ttl)
            
            api_stats = {}
            for api, stats in self.api_performance.items():
                if stats['success_count'] > 0:
                    api_stats[api] = {
                        'successes': stats['success_count'],
                        'avg_time': f"{stats['avg_time']:.2f}s"
                    }
            
            return {
                'total_cached': total_cached,
                'fresh_entries': fresh_entries,
                'cache_hit_rate': f"{(fresh_entries/max(total_cached, 1))*100:.1f}%",
                'api_performance': api_stats,
                'patterns_learned': len(self.pattern_cache)
            }
    
    def cleanup_expired(self):
        """Remove expired cache entries"""
        current_time = time.time()
        with self.cache_lock:
            expired_keys = []
            for key, (name, timestamp) in self.name_cache.items():
                if current_time - timestamp > self.cache_ttl:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.name_cache[key]
                
            if expired_keys:
                logger.debug(f"🧹 CACHE CLEANUP: Removed {len(expired_keys)} expired entries")

# Global cache instance
speed_cache = SpeedOptimizedCache()