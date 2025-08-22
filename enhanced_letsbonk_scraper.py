#!/usr/bin/env python3
"""
Enhanced LetsBonk Scraper with improved social media link detection
Based on actual HTML structure analysis
"""

import asyncio
import aiohttp
import re
from urllib.parse import unquote
from typing import List, Set

class EnhancedLetsBonkScraper:
    """Enhanced scraper specifically designed for LetsBonk.fun social media links"""
    
    def __init__(self):
        self.social_domains = ['tiktok.com', 'twitter.com', 'x.com', 't.me', 'discord.gg', 'discord.com', 'instagram.com', 'youtube.com']
    
    async def get_social_links(self, token_address: str) -> List[str]:
        """Get social media links using enhanced patterns"""
        print(f"🔍 ENHANCED LETSBONK SCRAPING: {token_address}")
        print("="*60)
        
        url = f"https://letsbonk.fun/token/{token_address}"
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        print(f"✅ Page loaded: {len(content)} chars")
                        
                        # Extract using enhanced patterns
                        social_links = self.extract_enhanced_social_links(content)
                        
                        if social_links:
                            print(f"🎯 Found {len(social_links)} social media links:")
                            for i, link in enumerate(social_links, 1):
                                print(f"   {i}. {link}")
                        else:
                            print(f"📊 No social media links detected")
                        
                        return social_links
                    else:
                        print(f"❌ HTTP {response.status}")
                        return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
    def extract_enhanced_social_links(self, content: str) -> List[str]:
        """Extract social links using enhanced patterns based on actual HTML structure"""
        links = set()
        
        # Pattern 1: LetsBonk specific Vue.js anchor tags with data-v attributes
        letsbonk_patterns = [
            # Main pattern: <a data-v-* target="_blank" href="social_url">
            r'<a\s+data-v-[a-f0-9]+[^>]*target=["\']_blank["\'][^>]*href=["\']([^"\']*(?:tiktok|twitter|x\.com|t\.me|discord|instagram|youtube)[^"\']*)["\'][^>]*>',
            
            # Alternative order: <a target="_blank" data-v-* href="social_url">
            r'<a[^>]*target=["\']_blank["\'][^>]*data-v-[a-f0-9]+[^>]*href=["\']([^"\']*(?:tiktok|twitter|x\.com|t\.me|discord|instagram|youtube)[^"\']*)["\'][^>]*>',
            
            # Generic Vue.js pattern: data-v-* with href
            r'<a[^>]*data-v-[a-f0-9]+[^>]*href=["\']([^"\']*(?:tiktok|twitter|x\.com|t\.me|discord|instagram|youtube)[^"\']*)["\'][^>]*>',
            
            # Target blank pattern (common for external links)
            r'<a[^>]*target=["\']_blank["\'][^>]*href=["\']([^"\']*(?:tiktok|twitter|x\.com|t\.me|discord|instagram|youtube)[^"\']*)["\'][^>]*>',
            
            # Pattern for buttons containing SVG icons (like the X/Twitter icon you showed)
            r'<a[^>]*data-v-[a-f0-9]+[^>]*href=["\']([^"\']*)["\'][^>]*>.*?<svg[^>]*>.*?<path[^>]*d="M9\.294 6\.928L14\.357.*?</svg>.*?</a>',
            
            # Generic pattern for social SVG icons within links
            r'<a[^>]*href=["\']([^"\']*(?:tiktok|twitter|x\.com|t\.me|discord|instagram|youtube)[^"\']*)["\'][^>]*>.*?<svg[^>]*>.*?</svg>.*?</a>',
        ]
        
        # Pattern 2: Generic social media links
        generic_patterns = [
            # Standard anchor tags
            r'<a[^>]*href=["\']([^"\']*(?:tiktok|twitter|x\.com|t\.me|discord|instagram|youtube)[^"\']*)["\'][^>]*>',
            
            # Button elements
            r'<button[^>]*(?:data-url|onclick)=["\']([^"\']*(?:tiktok|twitter|x\.com|t\.me|discord|instagram|youtube)[^"\']*)["\'][^>]*>',
            
            # Direct URL patterns in quotes
            r'["\']([^"\']*(?:https?://)?(?:www\.)?(?:tiktok|twitter|x)\.com/[^"\']+)["\']',
            r'["\']([^"\']*(?:https?://)?(?:www\.)?t\.me/[^"\']+)["\']',
            r'["\']([^"\']*(?:https?://)?(?:www\.)?discord\.(?:gg|com)/[^"\']+)["\']',
        ]
        
        all_patterns = letsbonk_patterns + generic_patterns
        
        for pattern in all_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                clean_url = self.clean_and_validate_url(match)
                if clean_url:
                    links.add(clean_url)
                    print(f"🔗 Pattern match: {clean_url}")
        
        return list(links)
    
    def clean_and_validate_url(self, url: str) -> str:
        """Clean and validate social media URL"""
        if not url:
            return ""
        
        # Handle URL decoding
        if '%' in url:
            try:
                url = unquote(url)
            except:
                pass
        
        # Clean HTML entities
        url = url.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            if any(domain in url.lower() for domain in self.social_domains):
                url = 'https://' + url
            else:
                return ""
        
        # Validate social domain
        if not any(domain in url.lower() for domain in self.social_domains):
            return ""
        
        # Minimum length check
        if len(url) < 15:
            return ""
        
        return url.strip()

async def test_enhanced_scraper():
    """Test the enhanced scraper with a known token"""
    scraper = EnhancedLetsBonkScraper()
    
    # Test with your provided HTML structure
    test_html = '''<a data-v-5dce20dc="" target="_blank" href="https://www.tiktok.com/@itsshee02/video/7529034101290994957?_t=ZT-8yDor0oJVeP&amp;_r=1" class="flex items-center">'''
    
    print("🧪 TESTING HTML PATTERN EXTRACTION")
    print("="*50)
    
    links = scraper.extract_enhanced_social_links(test_html)
    print(f"Found {len(links)} links from test HTML:")
    for link in links:
        print(f"  ✅ {link}")
    
    print("\n" + "="*50)
    
    # Test with a real token (you can replace with any token address)
    token_address = "9vFTZiXv8ZfAdLb7T9ef7Cf5QGgfLy8xVUQ29Jkcbonk"
    real_links = await scraper.get_social_links(token_address)
    
    return real_links

if __name__ == "__main__":
    asyncio.run(test_enhanced_scraper())