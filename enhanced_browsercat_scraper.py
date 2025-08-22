#!/usr/bin/env python3
"""
Enhanced BrowserCat scraper specifically designed for LetsBonk.fun Vue.js applications
Optimized for accurate social media link extraction from SPAs
"""

import asyncio
import aiohttp
import logging
import os
import re
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class EnhancedBrowserCatScraper:
    """Enhanced BrowserCat scraper for Vue.js SPA social media extraction"""
    
    def __init__(self):
        self.api_key = os.getenv("BROWSERCAT_API_KEY")
        if not self.api_key:
            raise ValueError("BROWSERCAT_API_KEY environment variable required")
        
        self.browsercat_endpoint = "https://api.browsercat.com/page"
        self.social_patterns = {
            'twitter': [r'https?://(?:www\.)?(?:twitter\.com|x\.com)/\S+'],
            'telegram': [r'https?://t\.me/\S+'],
            'discord': [r'https?://(?:www\.)?discord\.(?:gg|com)/\S+'],
            'tiktok': [r'https?://(?:www\.)?tiktok\.com/\S+'],
            'instagram': [r'https?://(?:www\.)?instagram\.com/\S+'],
            'youtube': [r'https?://(?:www\.)?youtube\.com/\S+'],
            'reddit': [r'https?://(?:www\.)?reddit\.com/\S+'],
            'facebook': [r'https?://(?:www\.)?facebook\.com/\S+']
        }
        
    async def extract_social_links_batch(self, token_addresses: List[str]) -> Dict[str, List[str]]:
        """
        🚀 BATCH PROCESSING: Extract social media links for multiple tokens simultaneously
        """
        if not token_addresses:
            return {}
            
        logger.info(f"🚀 BATCH BROWSERCAT: Processing {len(token_addresses)} tokens simultaneously")
        
        try:
            # Process multiple tokens concurrently with intelligent worker scaling
            worker_count = min(len(token_addresses), 8)  # Up to 8 concurrent extractions
            
            async def extract_single(address):
                try:
                    links = await self.extract_social_links_advanced(address)
                    return address, links
                except Exception as e:
                    logger.error(f"❌ Batch extraction failed for {address[:8]}...: {e}")
                    return address, []
            
            # Use asyncio.gather for concurrent processing
            results = await asyncio.gather(*[extract_single(addr) for addr in token_addresses], return_exceptions=True)
            
            # Process results
            batch_results = {}
            success_count = 0
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"❌ Batch processing exception: {result}")
                    continue
                    
                if isinstance(result, tuple) and len(result) == 2:
                    address, links = result
                    batch_results[address] = links if links else []
                    if links:
                        success_count += 1
                        logger.info(f"✅ BATCH SUCCESS: {address[:8]}... found {len(links)} social links")
            
            logger.info(f"🎯 BATCH COMPLETE: {success_count}/{len(token_addresses)} tokens with social links found")
            return batch_results
            
        except Exception as e:
            logger.error(f"❌ Batch social extraction failed: {e}")
            return {}
    
    def extract_social_links(self, letsbonk_url: str) -> List[str]:
        """
        Extract social media links from a LetsBonk.fun token page
        This is the main method used by the monitoring system
        """
        try:
            # For now, use a simple web scraping approach since BrowserCat API has been problematic
            import requests
            from bs4 import BeautifulSoup
            
            logger.info(f"🔍 Extracting social links from: {letsbonk_url}")
            
            # Get the page content
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(letsbonk_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all links in the page
            all_links = soup.find_all('a', href=True)
            
            social_links = []
            
            # Extract social media links using patterns
            for link in all_links:
                href = link.get('href', '')
                if not href:
                    continue
                
                # Check against all social media patterns
                for platform, patterns in self.social_patterns.items():
                    for pattern in patterns:
                        if re.match(pattern, str(href)):
                            if href not in social_links:
                                social_links.append(href)
                                logger.info(f"✅ Found {platform} link: {href}")
            
            # Also check for social links in the page text/script content
            page_text = soup.get_text()
            for platform, patterns in self.social_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, page_text)
                    for match in matches:
                        if match not in social_links:
                            social_links.append(match)
                            logger.info(f"✅ Found {platform} link in text: {match}")
            
            logger.info(f"📊 Total social links found: {len(social_links)}")
            return social_links
            
        except Exception as e:
            logger.error(f"❌ Social link extraction failed: {e}")
            return []
    
    async def extract_social_links_advanced(self, token_address: str) -> List[str]:
        """
        Advanced social media extraction using BrowserCat with multiple strategies
        Specifically designed for Vue.js SPAs like LetsBonk.fun
        """
        url = f"https://letsbonk.fun/token/{token_address}"
        logger.info(f"🚀 ENHANCED BROWSERCAT: Extracting social links from {url}")
        
        try:
            # Strategy 1: Use BrowserCat with JavaScript execution
            social_links = await self._extract_with_browsercat(url, token_address)
            
            if social_links:
                logger.info(f"✅ BrowserCat found {len(social_links)} social links")
                return social_links
            else:
                logger.warning("⚠️ BrowserCat found no social links, trying fallback method...")
                # Strategy 2: Fallback to enhanced static scraping
                return await self._extract_with_static_fallback(url)
                
        except Exception as e:
            logger.error(f"❌ BrowserCat extraction failed: {e}")
            # Strategy 3: Final fallback
            return await self._extract_with_static_fallback(url)
    
    async def _extract_with_browsercat(self, url: str, token_address: str) -> List[str]:
        """Extract using BrowserCat WebSocket with Playwright (correct approach)"""
        
        try:
            # Import playwright for WebSocket connection
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                logger.error("❌ Playwright not installed. Install with: pip install playwright")
                return []
            
            logger.info(f"🚀 BrowserCat WebSocket extraction starting: {url}")
            
            async with async_playwright() as p:
                # Connect to BrowserCat WebSocket (correct approach)
                browser = await p.chromium.connect(
                    "wss://api.browsercat.com/connect",
                    headers={'Api-Key': self.api_key}
                )
                
                # Create new page context
                context = await browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                page = await context.new_page()
                
                try:
                    # Navigate to LetsBonk token page
                    logger.info(f"📄 Loading page: {url}")
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    
                    # OPTIMIZED: Faster Vue.js loading with progressive detection
                    logger.info("⚡ FAST Vue.js loading with progressive detection...")
                    
                    # Phase 1: Quick detection attempt (3 seconds)
                    vue_loaded = False
                    try:
                        await page.wait_for_selector('[data-v-], a[href], h1, h2, h3', timeout=3000)
                        logger.info("✅ Fast: Content detected in 3s")
                        vue_loaded = True
                        # Short additional wait for dynamic content
                        await page.wait_for_timeout(2000)
                    except:
                        # Phase 2: Medium wait for slower connections (7 seconds total)
                        try:
                            await page.wait_for_selector('[data-v-]', timeout=4000)
                            logger.info("✅ Medium: Vue.js content detected in 7s")
                            vue_loaded = True
                            await page.wait_for_timeout(3000)
                        except:
                            # Phase 3: Extended wait only if necessary (12 seconds total)
                            try:
                                await page.wait_for_timeout(5000)
                                logger.info("⚠️ Slow: Using extended wait time")
                                vue_loaded = True
                            except:
                                pass
                        
                    except:
                        logger.warning("⚠️ Vue.js app content not fully loaded, trying alternative strategies...")
                        
                        # Try waiting for common LetsBonk elements
                        selectors_to_try = [
                            'a[target="_blank"]',
                            'button',
                            '[class*="social"]',
                            '[class*="link"]'
                        ]
                        
                        for selector in selectors_to_try:
                            try:
                                await page.wait_for_selector(selector, timeout=8000)
                                logger.info(f"✅ Found content via selector: {selector}")
                                vue_loaded = True
                                break
                            except:
                                continue
                    
                    # Advanced JavaScript-based social media extraction - targeting creator section
                    social_links = await page.evaluate("""
                        () => {
                            const socialDomains = ['twitter.com', 'x.com', 't.me', 'discord.gg', 'discord.com', 
                                                 'tiktok.com', 'instagram.com', 'youtube.com', 'reddit.com', 'facebook.com'];
                            const foundLinks = new Set();
                            
                            // Priority Method 1: Extract from creator section (near token info/time created)
                            // Look for token info section, creator details, or areas near timestamp
                            const creatorSections = document.querySelectorAll([
                                '[class*="creator"]',
                                '[class*="token-info"]', 
                                '[class*="details"]',
                                '[class*="meta"]',
                                '[class*="header"]',
                                '[data-v-] > div:first-child',  // Top sections in Vue components
                                '[data-v-] .flex:first-child'   // First flex containers in Vue
                            ].join(', '));
                            
                            creatorSections.forEach(section => {
                                const links = section.querySelectorAll('a[href]');
                                links.forEach(link => {
                                    const href = link.href;
                                    if (href && socialDomains.some(domain => href.includes(domain))) {
                                        // Exclude footer links by checking if they're in main content area
                                        const rect = link.getBoundingClientRect();
                                        if (rect.top < window.innerHeight * 0.8) { // Only links in top 80% of page
                                            foundLinks.add(href);
                                        }
                                    }
                                });
                            });
                            
                            // Priority Method 2: Look for links near time/creation date elements
                            const timeElements = document.querySelectorAll([
                                '[class*="time"]',
                                '[class*="date"]', 
                                '[class*="created"]',
                                '[class*="ago"]'
                            ].join(', '));
                            
                            timeElements.forEach(timeEl => {
                                // Look for social links in the same container or nearby
                                const container = timeEl.closest('[data-v-]') || timeEl.parentElement;
                                if (container) {
                                    const nearbyLinks = container.querySelectorAll('a[href]');
                                    nearbyLinks.forEach(link => {
                                        const href = link.href;
                                        if (href && socialDomains.some(domain => href.includes(domain))) {
                                            foundLinks.add(href);
                                        }
                                    });
                                }
                            });
                            
                            // Method 4: Explicit footer exclusion - skip known footer patterns
                            const footerElements = document.querySelectorAll([
                                'footer',
                                '[class*="footer"]',
                                '[id*="footer"]',
                                '[class*="bottom"]',
                                '.sticky-bottom',
                                '[class*="nav-bottom"]'
                            ].join(', '));
                            
                            // Remove any links found in footer areas
                            footerElements.forEach(footer => {
                                const footerLinks = footer.querySelectorAll('a[href]');
                                footerLinks.forEach(link => {
                                    if (foundLinks.has(link.href)) {
                                        foundLinks.delete(link.href);
                                    }
                                });
                            });
                            
                            // Fallback Method 5: Extract from top area only (avoiding footer)
                            if (foundLinks.size === 0) {
                                const topAreaLinks = document.querySelectorAll('a[href]');
                                topAreaLinks.forEach(link => {
                                    const href = link.href;
                                    if (href && socialDomains.some(domain => href.includes(domain))) {
                                        const rect = link.getBoundingClientRect();
                                        // Only include links in top 40% of page to avoid footer
                                        if (rect.top < window.innerHeight * 0.4) {
                                            // Additional check: exclude links that appear to be in footer-like containers
                                            const parent = link.closest('[class*="footer"], footer, [class*="bottom"], [class*="nav"]');
                                            if (!parent) {
                                                foundLinks.add(href);
                                            }
                                        }
                                    }
                                });
                            }

                            
                            return Array.from(foundLinks);
                        }
                    """)
                    
                    # Clean and validate all found links
                    cleaned_links = []
                    for link in social_links:
                        cleaned = self._clean_and_validate_url(link)
                        if cleaned:
                            cleaned_links.append(cleaned)
                    
                    if cleaned_links:
                        logger.info(f"🎯 ADVANCED BROWSERCAT found {len(cleaned_links)} Vue.js rendered social links for {token_address[-8:]}")
                        for link in cleaned_links:
                            logger.info(f"   🔗 BROWSERCAT: {link}")
                    else:
                        logger.info(f"⚠️ ADVANCED BROWSERCAT found no creator section social links for {token_address[-8:]}")
                    
                    return cleaned_links
                
                finally:
                    await context.close()
                    await browser.close()
                    
        except Exception as e:
            logger.error(f"❌ BrowserCat WebSocket extraction failed: {e}")
            return []
    
    async def _extract_with_static_fallback(self, url: str) -> List[str]:
        """Fallback static extraction method"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.info(f"📄 Fallback: Got {len(content)} chars of HTML")
                        
                        # Extract using patterns
                        links = set()
                        for platform, patterns in self.social_patterns.items():
                            for pattern in patterns:
                                matches = re.findall(pattern, content, re.IGNORECASE)
                                for match in matches:
                                    cleaned = self._clean_and_validate_url(match)
                                    if cleaned:
                                        links.add(cleaned)
                        
                        logger.info(f"📊 Fallback found {len(links)} social links")
                        return list(links)
                    else:
                        return []
        except Exception as e:
            logger.error(f"❌ Fallback extraction failed: {e}")
            return []
    
    def _clean_and_validate_url(self, url: str) -> Optional[str]:
        """Clean and validate a social media URL"""
        if not url or not isinstance(url, str):
            return None
        
        # Remove common trailing characters
        url = url.rstrip('.,;)>]}"\'')
        
        # URL decode
        try:
            from urllib.parse import unquote
            url = unquote(url)
        except:
            pass
        
        # Basic validation
        if not url.startswith(('http://', 'https://')):
            return None
        
        # Length validation
        if len(url) < 10 or len(url) > 500:
            return None
        
        # Check if it contains social media domains
        social_domains = ['twitter.com', 'x.com', 't.me', 'discord.gg', 'discord.com', 
                         'tiktok.com', 'instagram.com', 'youtube.com', 'reddit.com', 'facebook.com']
        
        if not any(domain in url.lower() for domain in social_domains):
            return None
        
        return url

# Usage example and test function
async def test_enhanced_scraper():
    """Test function for the enhanced scraper"""
    scraper = EnhancedBrowserCatScraper()
    
    # Test with a known token (replace with actual token address)
    test_address = "5mBhef7mKPYcAdzb8Hzg8sT2k6tQRXKX2REvPruYbonk"  # Recent token
    
    links = await scraper.extract_social_links_advanced(test_address)
    
    print(f"\n🎯 ENHANCED BROWSERCAT RESULTS:")
    print(f"Token: {test_address}")
    print(f"Social Links Found: {len(links)}")
    for i, link in enumerate(links, 1):
        print(f"  {i}. {link}")
    
    return links

if __name__ == "__main__":
    asyncio.run(test_enhanced_scraper())