#!/usr/bin/env python3
"""
Working BrowserCat fix using the discovered IP address
"""

import asyncio
import aiohttp
import os

async def test_browsercat_with_resolved_ip():
    """Test BrowserCat API using the IP we resolved"""
    
    # We found that browsercat.ai resolves to 162.255.119.94
    browsercat_ip = "162.255.119.94"
    api_key = os.getenv('BROWSERCAT_API_KEY')
    
    if not api_key:
        print("❌ No BrowserCat API key found")
        return False
    
    print(f"Testing BrowserCat API with IP: {browsercat_ip}")
    
    # Test different URL patterns
    test_urls = [
        f"https://{browsercat_ip}/v1/extract",
        f"https://{browsercat_ip}/extract", 
        f"http://{browsercat_ip}/v1/extract",
        f"http://{browsercat_ip}/extract"
    ]
    
    headers = {
        "Host": "api.browsercat.ai",  # Important: Use original hostname
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    test_payload = {
        "url": "https://httpbin.org/html", 
        "script": "document.title"
    }
    
    for url in test_urls:
        try:
            print(f"Testing: {url}")
            
            connector = aiohttp.TCPConnector(ssl=False) if url.startswith('http://') else None
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, headers=headers, json=test_payload, 
                                      timeout=15) as response:
                    
                    print(f"Response status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ SUCCESS! BrowserCat working at: {url}")
                        print(f"Test result: {result}")
                        return url
                    else:
                        error_text = await response.text()
                        print(f"❌ Status {response.status}: {error_text[:200]}...")
                        
        except Exception as e:
            print(f"❌ {url} failed: {e}")
    
    print("❌ All URL patterns failed")
    return False

async def test_token_extraction():
    """Test actual token name extraction"""
    
    browsercat_ip = "162.255.119.94"
    api_key = os.getenv('BROWSERCAT_API_KEY')
    
    # Test with recent token from logs
    token_address = "Q7wUyQk5NfqyAbVM5GMgQCPv2Pki3aALwdB3VEabonk"
    letsbonk_url = f"https://letsbonk.fun/token/{token_address}"
    
    script = '''
    (function() {
        // Look for the exact selector provided by user
        const nameElement = document.querySelector('span.text-xl.font-semibold');
        if (nameElement && nameElement.textContent) {
            return nameElement.textContent.trim();
        }
        
        // Fallback selectors
        const fallbacks = [
            'h1', 'h2', '.token-name', '[data-testid="token-name"]'
        ];
        
        for (const selector of fallbacks) {
            const element = document.querySelector(selector);
            if (element && element.textContent) {
                return element.textContent.trim();
            }
        }
        
        return null;
    })()
    '''
    
    headers = {
        "Host": "api.browsercat.ai",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "url": letsbonk_url,
        "script": script,
        "options": {
            "waitForSelector": True,
            "timeout": 10000,
            "viewport": {"width": 1280, "height": 720}
        }
    }
    
    # Try both HTTPS and HTTP with the working IP
    test_urls = [
        f"https://{browsercat_ip}/v1/extract",
        f"http://{browsercat_ip}/v1/extract"
    ]
    
    for url in test_urls:
        try:
            print(f"Testing token extraction with: {url}")
            
            connector = aiohttp.TCPConnector(ssl=False) if url.startswith('http://') else None
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(url, headers=headers, json=payload, 
                                      timeout=20) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Token extraction successful!")
                        print(f"Result: {result}")
                        
                        if 'result' in result and result['result']:
                            token_name = result['result']
                            print(f"🎉 Extracted token name: '{token_name}'")
                            return token_name
                    else:
                        error_text = await response.text()
                        print(f"❌ Status {response.status}: {error_text}")
                        
        except Exception as e:
            print(f"❌ Token extraction failed with {url}: {e}")
    
    return None

if __name__ == "__main__":
    async def main():
        print("=== Testing BrowserCat API Access ===")
        working_url = await test_browsercat_with_resolved_ip()
        
        if working_url:
            print(f"\n=== Testing Token Name Extraction ===")
            token_name = await test_token_extraction()
            
            if token_name:
                print(f"\n🎉 COMPLETE SUCCESS!")
                print(f"BrowserCat is accessible and token extraction works")
                print(f"Working URL: {working_url}")
                print(f"Extracted token name: {token_name}")
            else:
                print(f"\n⚠️ PARTIAL SUCCESS")
                print(f"BrowserCat API accessible but token extraction needs work")
        else:
            print(f"\n❌ BrowserCat API not accessible with IP resolution")
    
    asyncio.run(main())