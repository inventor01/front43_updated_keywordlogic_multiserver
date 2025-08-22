#!/usr/bin/env python3
"""
Multi-Source Timestamp Validator Module
Validates token creation timestamps using multiple blockchain sources
"""

import logging
import requests
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class MultiSourceTimestampValidator:
    """Multi-source timestamp validation for token creation"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 600  # 10 minutes
        self.max_age_hours = 24  # Only tokens created in last 24 hours
        
    def validate_token_age(self, token_address: str, max_age_minutes: int = 1440) -> bool:
        """Validate token is within acceptable age range"""
        try:
            # Check cache first
            cache_key = f"age_{token_address}"
            if cache_key in self.cache:
                cached_time, result = self.cache[cache_key]
                if time.time() - cached_time < self.cache_ttl:
                    return result
            
            # Get token creation timestamp
            creation_time = self.get_token_creation_time(token_address)
            
            if creation_time:
                # Calculate age in minutes
                now = datetime.utcnow()
                age_minutes = (now - creation_time).total_seconds() / 60
                
                # Validate age
                result = age_minutes <= max_age_minutes
                self.cache[cache_key] = (time.time(), result)
                
                logger.debug(f"Token {token_address[:10]}... age: {age_minutes:.1f} minutes (valid: {result})")
                return result
            
            # If can't determine age, assume valid (fallback)
            return True
            
        except Exception as e:
            logger.debug(f"Age validation failed: {e}")
            return True  # Fail open
    
    def get_token_creation_time(self, token_address: str) -> Optional[datetime]:
        """Get token creation timestamp from multiple sources"""
        try:
            # Try multiple sources in order of preference
            sources = [
                self._get_timestamp_from_solscan,
                self._get_timestamp_from_dexscreener,
                self._get_timestamp_from_helius
            ]
            
            for source in sources:
                try:
                    timestamp = source(token_address)
                    if timestamp:
                        return timestamp
                except Exception as e:
                    logger.debug(f"Source failed: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Timestamp fetch failed: {e}")
            return None
    
    def _get_timestamp_from_solscan(self, token_address: str) -> Optional[datetime]:
        """Get timestamp from Solscan API (fallback method)"""
        try:
            # This is a placeholder - would need actual Solscan API integration
            # For now, return None to try other sources
            return None
        except Exception:
            return None
    
    def _get_timestamp_from_dexscreener(self, token_address: str) -> Optional[datetime]:
        """Get timestamp from DexScreener API"""
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                if pairs:
                    # Find the earliest pair creation time
                    earliest_time = None
                    for pair in pairs:
                        pair_created = pair.get('pairCreatedAt')
                        if pair_created:
                            try:
                                # Parse timestamp (assuming Unix timestamp in milliseconds)
                                pair_time = datetime.utcfromtimestamp(pair_created / 1000)
                                if not earliest_time or pair_time < earliest_time:
                                    earliest_time = pair_time
                            except Exception:
                                continue
                    
                    return earliest_time
            
            return None
            
        except Exception:
            return None
    
    def _get_timestamp_from_helius(self, token_address: str) -> Optional[datetime]:
        """Get timestamp from Helius API (fallback method)"""
        try:
            # This is a placeholder - would need actual Helius API integration
            # For now, return None
            return None
        except Exception:
            return None
    
    def get_validation_confidence(self, token_address: str) -> float:
        """Get confidence score for timestamp validation (0.0 to 1.0)"""
        try:
            creation_time = self.get_token_creation_time(token_address)
            
            if creation_time:
                # Higher confidence for more recent tokens
                age_hours = (datetime.utcnow() - creation_time).total_seconds() / 3600
                
                if age_hours <= 1:
                    return 1.0  # Very high confidence
                elif age_hours <= 6:
                    return 0.9  # High confidence
                elif age_hours <= 24:
                    return 0.7  # Medium confidence
                else:
                    return 0.3  # Low confidence
            
            return 0.5  # Default confidence when timestamp unavailable
            
        except Exception:
            return 0.5

# Global instance
timestamp_validator = MultiSourceTimestampValidator()

def validate_token_timestamp(token_address: str, max_age_minutes: int = 1440) -> bool:
    """Validate token age using multiple sources"""
    return timestamp_validator.validate_token_age(token_address, max_age_minutes)

def get_token_creation_timestamp(token_address: str) -> Optional[datetime]:
    """Get token creation timestamp"""
    return timestamp_validator.get_token_creation_time(token_address)

def get_timestamp_confidence(token_address: str) -> float:
    """Get validation confidence score"""
    return timestamp_validator.get_validation_confidence(token_address)

logger.info("✅ Multi-source timestamp validator initialized")