#!/usr/bin/env python3
"""
Enhanced social media link extractor using pattern detection and manual guides
"""

import asyncio
import logging
import os
from typing import List, Dict, Optional
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class EnhancedSocialMediaExtractor:
    """
    Enhanced social media extractor with multiple methods:
    1. Pattern detection (primary)  
    2. Manual extraction guide (secondary)
    """
    
    def __init__(self):
        # BrowserCat removed - using only pattern detection and manual guides
        self.browsercat_scraper = None
    
    async def extract_social_links(self, token_address: str, token_name: str = "") -> Dict[str, any]:
        """
        Extract social media links using all available methods
        
        Returns:
            Dict with 'links' and 'method' used
        """
        
        if not token_address.endswith('bonk'):
            return {'links': [], 'method': 'not_letsbonk_token', 'error': 'Only LetsBonk tokens supported'}
        
        letsbonk_url = f"https://letsbonk.fun/coin/{token_address}"
        
        # Method 1: Static HTML pattern detection (limited for SPAs)
        try:
            import requests
            response = requests.get(letsbonk_url, timeout=10)
            html = response.text
            
            # Look for social media patterns in static HTML
            patterns = [
                r'href=["\']([^"\']*(?:twitter\.com|x\.com|t\.me|discord|tiktok|instagram|youtube)[^"\']*)["\']',
                r'data-v-[^>]*href=["\']([^"\']*(?:twitter\.com|x\.com|t\.me|discord|tiktok|instagram|youtube)[^"\']*)["\']'
            ]
            
            found_links = set()
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    if self._is_valid_social_link(match):
                        found_links.add(match)
            
            if found_links:
                logger.info(f"✅ Pattern detection: {len(found_links)} links found")
                return {
                    'links': list(found_links),
                    'method': 'pattern_detection',
                    'success': True,
                    'url': letsbonk_url
                }
            
        except Exception as e:
            logger.warning(f"⚠️ Pattern detection failed: {e}")
        
        # Method 2: Return manual extraction guide
        logger.info("💡 Automated extraction failed - providing manual extraction guide")
        return {
            'links': [],
            'method': 'manual_guide',
            'success': False,
            'url': letsbonk_url,
            'manual_steps': [
                f"1. Open: {letsbonk_url}",
                "2. Right-click → 'Inspect Element' (NOT 'View Page Source')",
                "3. Look for social media buttons with Vue.js data-v attributes",
                "4. Extract href URLs from Twitter, Telegram, Discord buttons"
            ]
        }
    
    def _is_valid_social_link(self, url: str) -> bool:
        """Validate if URL is a social media link"""
        if not url:
            return False
            
        try:
            parsed = urlparse(url.lower())
            social_domains = [
                'twitter.com', 'x.com', 't.me', 'discord.gg', 'discord.com',
                'tiktok.com', 'instagram.com', 'youtube.com', 'telegram.org'
            ]
            
            return any(domain in parsed.netloc for domain in social_domains)
            
        except Exception:
            return False
    
    def format_social_links_for_discord(self, extraction_result: Dict) -> str:
        """Format social links for Discord notification"""
        
        if not extraction_result.get('success') or not extraction_result.get('links'):
            if extraction_result.get('method') == 'manual_guide':
                return "🔍 **Social Media Links**: Manual extraction required\n" + \
                       f"💡 Open: {extraction_result.get('url', 'N/A')}\n" + \
                       "👆 Right-click → Inspect Element → Find social buttons"
            else:
                return "🔍 **Social Media Links**: None found"
        
        links = extraction_result['links']
        method = extraction_result.get('method', 'unknown')
        
        formatted = f"🔗 **Social Media Links** ({len(links)} found via {method}):\n"
        
        for i, link in enumerate(links[:5], 1):  # Limit to 5 links for Discord
            # Determine platform icon
            link_lower = link.lower()
            if 'twitter.com' in link_lower or 'x.com' in link_lower:
                icon = "🐦"
            elif 't.me' in link_lower:
                icon = "💬"
            elif 'discord' in link_lower:
                icon = "🎮"
            elif 'tiktok' in link_lower:
                icon = "🎵"
            elif 'instagram' in link_lower:
                icon = "📸"
            elif 'youtube' in link_lower:
                icon = "📺"
            else:
                icon = "🔗"
                
            formatted += f"  {icon} [{self._get_platform_name(link)}]({link})\n"
        
        if len(links) > 5:
            formatted += f"  ... and {len(links) - 5} more links\n"
            
        return formatted
    
    def _get_platform_name(self, link: str) -> str:
        """Get platform name from URL"""
        link_lower = link.lower()
        if 'twitter.com' in link_lower or 'x.com' in link_lower:
            return "Twitter/X"
        elif 't.me' in link_lower:
            return "Telegram"
        elif 'discord' in link_lower:
            return "Discord"
        elif 'tiktok' in link_lower:
            return "TikTok"
        elif 'instagram' in link_lower:
            return "Instagram"
        elif 'youtube' in link_lower:
            return "YouTube"
        else:
            return "Social Media"


# Global extractor instance
enhanced_extractor = EnhancedSocialMediaExtractor()

async def extract_token_social_links(token_address: str, token_name: str = "") -> Dict:
    """
    Convenience function to extract social links for a token
    """
    return await enhanced_extractor.extract_social_links(token_address, token_name)


# Test function
async def test_enhanced_extractor():
    """Test the enhanced extractor"""
    print("🧪 TESTING ENHANCED SOCIAL MEDIA EXTRACTOR")
    print("==========================================")
    
    # Test with known LetsBonk token
    test_address = "FvPT783aYoJAfr4b7wKDLkgmpStqq5Go5wVKRJMpbonk"
    test_name = "Test Token"
    
    result = await extract_token_social_links(test_address, test_name)
    
    print(f"\n📊 RESULTS:")
    print(f"Method: {result.get('method', 'unknown')}")
    print(f"Success: {result.get('success', False)}")
    print(f"Links found: {len(result.get('links', []))}")
    
    if result.get('links'):
        print("\n🔗 Social Media Links:")
        for i, link in enumerate(result['links'], 1):
            print(f"  {i}. {link}")
    
    print(f"\n💬 Discord Format:")
    discord_text = enhanced_extractor.format_social_links_for_discord(result)
    print(discord_text)


if __name__ == "__main__":
    asyncio.run(test_enhanced_extractor())