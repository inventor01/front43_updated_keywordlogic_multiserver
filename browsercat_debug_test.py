#!/usr/bin/env python3
"""
BrowserCat Connection Debug Test
Tests various connection methods and DNS resolution
"""

import asyncio
import aiohttp
import os
import socket
import json

async def debug_browsercat_connection():
    """Debug BrowserCat API connectivity"""
    
    print("=== BrowserCat Connection Debug ===")
    
    # 1. Check API key
    api_key = os.getenv('BROWSERCAT_API_KEY')
    print(f"API Key present: {'Yes' if api_key else 'No'}")
    if api_key:
        print(f"API Key length: {len(api_key)}")
        print(f"API Key starts with: {api_key[:8]}...")
    
    # 2. Test DNS resolution
    print("\n=== DNS Resolution Test ===")
    try:
        ip = socket.gethostbyname('api.browsercat.ai')
        print(f"✅ DNS Resolution successful: api.browsercat.ai -> {ip}")
    except socket.gaierror as e:
        print(f"❌ DNS Resolution failed: {e}")
        
        # Try alternative DNS servers
        try:
            import subprocess
            result = subprocess.run(['dig', '+short', 'api.browsercat.ai'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                print(f"🔄 Alternative DNS lookup: {result.stdout.strip()}")
            else:
                print("❌ Alternative DNS lookup also failed")
        except Exception as dig_error:
            print(f"❌ dig command failed: {dig_error}")
    
    # 3. Test basic HTTP connectivity
    print("\n=== HTTP Connectivity Test ===")
    
    test_urls = [
        'https://httpbin.org/ip',
        'https://api.github.com/zen',
        'https://letsbonk.fun/api/health',  # Test LetsBonk connectivity
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in test_urls:
            try:
                async with session.get(url, timeout=10) as response:
                    print(f"✅ {url}: HTTP {response.status}")
            except Exception as e:
                print(f"❌ {url}: {e}")
    
    # 4. Test BrowserCat API with different methods
    print("\n=== BrowserCat API Tests ===")
    
    if not api_key:
        print("❌ Cannot test BrowserCat API - no API key")
        return
    
    base_urls = [
        'https://api.browsercat.ai',
        'https://browsercat.ai/api',  # Alternative endpoint
    ]
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    async with aiohttp.ClientSession() as session:
        for base_url in base_urls:
            test_endpoints = [
                f'{base_url}/health',
                f'{base_url}/v1/health',
                f'{base_url}/status',
                f'{base_url}/',
            ]
            
            for endpoint in test_endpoints:
                try:
                    async with session.get(endpoint, headers=headers, timeout=10) as response:
                        content = await response.text()
                        print(f"✅ {endpoint}: HTTP {response.status}")
                        if len(content) < 200:
                            print(f"   Response: {content[:100]}...")
                except Exception as e:
                    print(f"❌ {endpoint}: {e}")
    
    # 5. Test with minimal BrowserCat request
    print("\n=== Minimal BrowserCat Request Test ===")
    
    minimal_payload = {
        'url': 'https://httpbin.org/html',
        'script': 'document.title'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.browsercat.ai/v1/extract',
                headers=headers,
                json=minimal_payload,
                timeout=15
            ) as response:
                result = await response.json()
                print(f"✅ BrowserCat extraction test: HTTP {response.status}")
                print(f"   Result: {result}")
    except Exception as e:
        print(f"❌ BrowserCat extraction test failed: {e}")
    
    print("\n=== Debug Complete ===")

if __name__ == "__main__":
    asyncio.run(debug_browsercat_connection())