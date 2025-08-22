"""
Free social media scraper without external dependencies
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import re

logger = logging.getLogger(__name__)

class APIFreeSocialScraper:
    """Social media scraper using free APIs and direct requests"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def extract_social_links(self, url: str) -> Tuple[List[str], float]:
        """Extract social media links from a URL"""
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return [], 0.0
            
            content = response.text.lower()
            links = []
            
            # Extract token addresses (Solana format)
            token_pattern = r'[1-9A-HJ-NP-Za-km-z]{32,44}'
            potential_tokens = re.findall(token_pattern, content)
            
            # Filter for likely Solana addresses
            for token in potential_tokens:
                if 32 <= len(token) <= 44:
                    links.append(token)
            
            # Extract social media mentions
            social_patterns = [
                r'twitter\.com/[\w]+',
                r'x\.com/[\w]+',
                r'telegram\.me/[\w]+',
                r't\.me/[\w]+',
                r'instagram\.com/[\w]+',
                r'youtube\.com/[\w]+',
                r'reddit\.com/r/[\w]+'
            ]
            
            for pattern in social_patterns:
                matches = re.findall(pattern, content)
                links.extend(matches)
            
            # Remove duplicates
            links = list(set(links))
            
            return links, len(links) * 0.1  # Simple scoring
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return [], 0.0
    
    def get_social_links(self, url: str) -> List[str]:
        """Get social media links from URL"""
        links, _ = self.extract_social_links(url)
        return links