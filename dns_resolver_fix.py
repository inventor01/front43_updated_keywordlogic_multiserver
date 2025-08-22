#!/usr/bin/env python3
"""
DNS Resolution Fix for BrowserCat API
Attempts to resolve api.browsercat.ai using various methods
"""

import asyncio
import aiohttp
import socket
import json

async def resolve_browsercat_ip():
    """Try multiple methods to resolve BrowserCat API IP address"""
    
    print("=== DNS Resolution Attempts ===")
    
    # Method 1: Try public DNS resolvers
    dns_servers = [
        "8.8.8.8",  # Google
        "1.1.1.1",  # Cloudflare  
        "9.9.9.9",  # Quad9
        "208.67.222.222"  # OpenDNS
    ]
    
    for dns_server in dns_servers:
        try:
            # Use aiohttp to query DNS-over-HTTPS
            async with aiohttp.ClientSession() as session:
                # Try Cloudflare DNS-over-HTTPS
                if dns_server == "1.1.1.1":
                    url = "https://cloudflare-dns.com/dns-query"
                    headers = {"Accept": "application/dns-json"}
                    params = {"name": "api.browsercat.ai", "type": "A"}
                    
                    async with session.get(url, headers=headers, params=params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            if "Answer" in data and data["Answer"]:
                                ip = data["Answer"][0]["data"]
                                print(f"✅ Cloudflare DNS-over-HTTPS: api.browsercat.ai -> {ip}")
                                return ip
                
                # Try Google DNS-over-HTTPS  
                elif dns_server == "8.8.8.8":
                    url = "https://dns.google/resolve"
                    params = {"name": "api.browsercat.ai", "type": "A"}
                    
                    async with session.get(url, params=params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            if "Answer" in data and data["Answer"]:
                                ip = data["Answer"][0]["data"]
                                print(f"✅ Google DNS-over-HTTPS: api.browsercat.ai -> {ip}")
                                return ip
                                
        except Exception as e:
            print(f"❌ DNS-over-HTTPS failed for {dns_server}: {e}")
    
    # Method 2: Try alternative domain resolution
    alternative_domains = [
        "browsercat.ai",
        "api.browsercat.com", 
        "browsercat.com"
    ]
    
    for domain in alternative_domains:
        try:
            ip = socket.gethostbyname(domain)
            print(f"✅ Alternative domain resolution: {domain} -> {ip}")
            
            # Test if this IP works for BrowserCat API
            try:
                async with aiohttp.ClientSession() as session:
                    test_url = f"https://{ip}/"
                    headers = {"Host": "api.browsercat.ai"}
                    async with session.get(test_url, headers=headers, timeout=10, ssl=False) as response:
                        print(f"✅ IP {ip} responds to HTTP requests")
                        return ip
            except Exception as test_error:
                print(f"❌ IP {ip} not responding: {test_error}")
                
        except Exception as e:
            print(f"❌ Alternative domain {domain} failed: {e}")
    
    # Method 3: Try known IP ranges
    known_ips = [
        "104.21.0.0",   # Cloudflare range
        "172.67.0.0",   # Cloudflare range  
        "185.199.108.0" # GitHub Pages range
    ]
    
    for base_ip in known_ips:
        for i in range(1, 255):
            test_ip = f"{base_ip[:-1]}{i}"
            try:
                async with aiohttp.ClientSession() as session:
                    test_url = f"https://{test_ip}/"
                    headers = {"Host": "api.browsercat.ai"}
                    async with session.get(test_url, headers=headers, timeout=2, ssl=False) as response:
                        if response.status < 500:
                            print(f"✅ Found working IP: {test_ip}")
                            return test_ip
            except:
                continue
                
    print("❌ All DNS resolution methods failed")
    return None

async def test_browsercat_with_ip(ip_address):
    """Test BrowserCat API using resolved IP address"""
    
    if not ip_address:
        return False
        
    print(f"\n=== Testing BrowserCat API with IP {ip_address} ===")
    
    # Test with IP address and Host header
    headers = {
        "Host": "api.browsercat.ai",
        "Authorization": f"Bearer {os.getenv('BROWSERCAT_API_KEY', '')}",
        "Content-Type": "application/json"
    }
    
    test_payload = {
        "url": "https://httpbin.org/html",
        "script": "document.title"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Try HTTPS with IP and Host header
            test_url = f"https://{ip_address}/v1/extract"
            async with session.post(test_url, headers=headers, json=test_payload, 
                                  timeout=15, ssl=False) as response:
                result = await response.json()
                print(f"✅ BrowserCat API working with IP {ip_address}: {result}")
                return True
                
    except Exception as e:
        print(f"❌ BrowserCat API test failed with IP {ip_address}: {e}")
        return False

if __name__ == "__main__":
    import os
    
    async def main():
        ip = await resolve_browsercat_ip()
        if ip:
            success = await test_browsercat_with_ip(ip)
            if success:
                print(f"\n🎉 SUCCESS: BrowserCat accessible via IP {ip}")
                print(f"Add this to your /etc/hosts file:")
                print(f"{ip} api.browsercat.ai")
            else:
                print(f"\n❌ IP {ip} found but BrowserCat API not responding")
        else:
            print("\n❌ Could not resolve api.browsercat.ai")
    
    asyncio.run(main())