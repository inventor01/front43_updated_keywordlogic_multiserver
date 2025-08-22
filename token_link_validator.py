#!/usr/bin/env python3
"""
Token Link Validator Module for Token Monitoring System
Validates token addresses and social media links for authenticity
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
import re
# from config import Config  # Disabled for pure deployment

class TokenLinkValidator:
    """Validates token addresses and social media links"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.solana_address_pattern = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
        
    async def initialize(self) -> bool:
        """Initialize token link validator"""
        try:
            self.logger.info("🔗 Token link validator initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize token link validator: {e}")
            return False
    
    def validate_solana_address(self, address: str) -> bool:
        """Validate Solana token address format"""
        if not address or len(address) < 32 or len(address) > 44:
            return False
        return bool(self.solana_address_pattern.match(address))
    
    def validate_social_link(self, url: str) -> Dict[str, Any]:
        """Validate social media link and extract platform"""
        social_patterns = {
            'twitter': r'(?:twitter\.com|x\.com)/[^/]+',
            'telegram': r't\.me/[^/]+',
            'discord': r'discord\.(?:gg|com)/[^/]+',
            'website': r'https?://[^\s]+',
        }
        
        result = {
            'valid': False,
            'platform': 'unknown',
            'normalized_url': url
        }
        
        for platform, pattern in social_patterns.items():
            if re.search(pattern, url, re.IGNORECASE):
                result['valid'] = True
                result['platform'] = platform
                break
                
        return result
    
    async def validate_token_data(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive token data validation"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate token address
        address = token_data.get('address', '')
        if not self.validate_solana_address(address):
            validation_result['valid'] = False
            validation_result['errors'].append('Invalid Solana address format')
        
        # Validate social links
        for link_key in ['website', 'twitter', 'telegram']:
            link = token_data.get(link_key, '')
            if link:
                validation = self.validate_social_link(link)
                if not validation['valid']:
                    validation_result['warnings'].append(f'Invalid {link_key} link format')
        
        return validation_result
    
    def get_token_links(self, token_data: Dict[str, Any]) -> List[str]:
        """Extract all social media links from token data"""
        links = []
        for key in ['website', 'twitter', 'telegram', 'discord']:
            link = token_data.get(key, '')
            if link:
                links.append(link)
        return links
    
    def get_link_summary(self, links: List[str]) -> Dict[str, Any]:
        """Get summary of social media links"""
        summary = {
            'total_links': len(links),
            'platforms': {},
            'valid_links': 0
        }
        
        for link in links:
            validation = self.validate_social_link(link)
            if validation['valid']:
                summary['valid_links'] += 1
                platform = validation['platform']
                summary['platforms'][platform] = summary['platforms'].get(platform, 0) + 1
        
        return summary
    
    def get_status(self) -> Dict[str, Any]:
        """Get validator status"""
        return {
            'status': 'active',
            'supported_platforms': ['twitter', 'telegram', 'discord', 'website'],
            'validation_patterns': 'loaded'
        }