#!/usr/bin/env python3
"""
IP-based BrowserCat connector that bypasses DNS resolution
"""

import asyncio
import aiohttp
import os

class IPBasedBrowserCat:
    """BrowserCat client that uses IP address instead of domain name"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        # Try common Cloudflare IP ranges for BrowserCat
        self.potential_ips = [
            "104.21.14.67",   # Common Cloudflare IP
            "172.67.74.226",  # Common Cloudflare IP
            "104.26.14.67",   # Cloudflare range
            "172.67.182.82",  # Cloudflare range
        ]
        self.working_ip = None
    
    async def find_working_ip(self):
        """Find a working IP for api.browsercat.ai"""
        
        headers = {
            "Host": "api.browsercat.ai",
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        test_payload = {
            "url": "https://httpbin.org/html",
            "script": "document.title"
        }
        
        for ip in self.potential_ips:
            try:
                print(f"Testing IP: {ip}")
                async with aiohttp.ClientSession() as session:
                    url = f"https://{ip}/v1/extract"
                    async with session.post(url, headers=headers, json=test_payload, 
                                          timeout=10, ssl=False) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"✅ Found working IP: {ip}")
                            print(f"Test result: {result}")
                            self.working_ip = ip
                            return ip
                        else:
                            print(f"❌ IP {ip} returned status {response.status}")
                            
            except Exception as e:
                print(f"❌ IP {ip} failed: {e}")
                continue
                
        print("❌ No working IP found")
        return None
    
    async def extract_token_name(self, token_address):
        """Extract token name using working IP"""
        
        if not self.working_ip:
            working_ip = await self.find_working_ip()
            if not working_ip:
                return None
        
        url = f"https://letsbonk.fun/token/{token_address}"
        script = '''
        (function() {
            const nameElement = document.querySelector('span.text-xl.font-semibold');
            if (nameElement) {
                return nameElement.textContent.trim();
            }
            
            const titleElement = document.querySelector('h1');
            if (titleElement) {
                return titleElement.textContent.trim();
            }
            
            return null;
        })()
        '''
        
        headers = {
            "Host": "api.browsercat.ai",
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": url,
            "script": script,
            "options": {
                "waitForSelector": True,
                "timeout": 10000
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                api_url = f"https://{self.working_ip}/v1/extract"
                async with session.post(api_url, headers=headers, json=payload, 
                                      timeout=15, ssl=False) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result and 'result' in result:
                            name = result['result']
                            if name and len(name) > 1:
                                print(f"✅ IP-based extraction: {name}")
                                return name
                        
        except Exception as e:
            print(f"❌ IP-based extraction failed: {e}")
            return None

async def test_ip_based_browsercat():
    """Test the IP-based BrowserCat approach"""
    
    api_key = os.getenv('BROWSERCAT_API_KEY')
    if not api_key:
        print("❌ No BrowserCat API key found")
        return
        
    client = IPBasedBrowserCat(api_key)
    
    # Test with a recent token
    test_token = "HffaaHRfZR2iGvVNjyry7Mv2XRD3JrjMDDnW5dFLbonk"  # Recent token from logs
    print(f"Testing token name extraction for: {test_token}")
    
    name = await client.extract_token_name(test_token)
    if name:
        print(f"🎉 Successfully extracted name: {name}")
    else:
        print("❌ Name extraction failed")

if __name__ == "__main__":
    asyncio.run(test_ip_based_browsercat())