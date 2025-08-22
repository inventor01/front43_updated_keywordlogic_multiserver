#!/usr/bin/env python3
"""
Quick Discord token validation test
"""

import requests
import os

def test_discord_token():
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        print("❌ No DISCORD_TOKEN found")
        return False
    
    print(f"🔑 Testing token: {token[:20]}...")
    
    # Test Discord API with token
    headers = {
        'Authorization': f'Bot {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get('https://discord.com/api/users/@me', headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Token is VALID!")
            print(f"🤖 Bot Name: {data.get('username')}#{data.get('discriminator')}")
            print(f"🆔 Bot ID: {data.get('id')}")
            return True
        else:
            print(f"❌ Token is INVALID - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing token: {e}")
        return False

if __name__ == "__main__":
    test_discord_token()