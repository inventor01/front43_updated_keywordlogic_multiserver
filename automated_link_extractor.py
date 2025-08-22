#!/usr/bin/env python3
"""
Automated Link Extractor Module for Token Monitoring System
Extracts token links from social media and websites automatically
"""

import asyncio
import logging
import re
from typing import Optional, Dict, Any, List
from config import Config

class AutomatedLinkExtractor:
    """Automated extraction of token links from various sources"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.token_patterns = [
            r'([1-9A-HJ-NP-Za-km-z]{32,44})',  # Solana address pattern
            r'pump\.fun/([1-9A-HJ-NP-Za-km-z]{32,44})',  # Pump.fun links
            r'dexscreener\.com/solana/([1-9A-HJ-NP-Za-km-z]{32,44})',  # DexScreener links
        ]
        
    async def initialize(self) -> bool:
        """Initialize automated link extractor"""
        try:
            self.logger.info("🔗 Automated link extractor initialized")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize link extractor: {e}")
            return False
    
    async def extract_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract token addresses from text content"""
        extracted_links = []
        
        for pattern in self.token_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                extracted_links.append({
                    'address': match,
                    'source': 'text_extraction',
                    'confidence': 0.8
                })
        
        return extracted_links
    
    async def extract_from_url(self, url: str) -> List[Dict[str, Any]]:
        """Extract token information from URL"""
        extracted_data = []
        
        try:
            # Extract from pump.fun URLs
            if 'pump.fun' in url:
                match = re.search(r'pump\.fun/([1-9A-HJ-NP-Za-km-z]{32,44})', url)
                if match:
                    extracted_data.append({
                        'address': match.group(1),
                        'source': 'pump_fun',
                        'url': url,
                        'confidence': 0.9
                    })
            
            # Extract from DexScreener URLs
            elif 'dexscreener.com' in url:
                match = re.search(r'dexscreener\.com/solana/([1-9A-HJ-NP-Za-km-z]{32,44})', url)
                if match:
                    extracted_data.append({
                        'address': match.group(1),
                        'source': 'dexscreener',
                        'url': url,
                        'confidence': 0.9
                    })
        
        except Exception as e:
            self.logger.error(f"Error extracting from URL {url}: {e}")
        
        return extracted_data
    
    def get_status(self) -> Dict[str, Any]:
        """Get extractor status"""
        return {
            'status': 'active',
            'supported_sources': ['pump_fun', 'dexscreener', 'text_extraction'],
            'patterns_loaded': len(self.token_patterns)
        }