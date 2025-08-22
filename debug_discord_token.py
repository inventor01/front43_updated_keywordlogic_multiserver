#!/usr/bin/env python3
"""
Debug Discord token format and connection
"""

import os
import requests

def debug_discord_token():
    """Debug Discord token and check format"""
    
    print("🔍 DEBUGGING DISCORD TOKEN")
    print("=" * 50)
    
    # Check if token exists
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ No DISCORD_TOKEN found")
        return False
    
    print(f"✅ Token exists")
    print(f"📏 Token length: {len(token)}")
    print(f"🔤 Token starts with: {token[:10]}...")
    print(f"🔤 Token ends with: ...{token[-10:]}")
    
    # Check token format
    if len(token) < 50:
        print("⚠️ Token seems too short (should be ~70 characters)")
    elif len(token) > 100:
        print("⚠️ Token seems too long (should be ~70 characters)")
    else:
        print("✅ Token length looks correct")
    
    # Check for common token patterns
    if token.startswith('Bot '):
        print("⚠️ Token starts with 'Bot ' - remove this prefix")
        token = token[4:]  # Remove 'Bot ' prefix
    
    if '.' not in token:
        print("❌ Token missing dots (invalid format)")
        return False
    
    parts = token.split('.')
    if len(parts) != 3:
        print(f"❌ Token should have 3 parts separated by dots, found {len(parts)}")
        return False
    
    print(f"✅ Token has correct 3-part structure")
    print(f"   Part 1 length: {len(parts[0])}")
    print(f"   Part 2 length: {len(parts[1])}")  
    print(f"   Part 3 length: {len(parts[2])}")
    
    # Test token with Discord API
    print("\n🔄 Testing token with Discord API...")
    
    try:
        headers = {
            'Authorization': f'Bot {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get('https://discord.com/api/users/@me', headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ TOKEN VALID - Bot: {data.get('username')}#{data.get('discriminator')}")
            print(f"   Bot ID: {data.get('id')}")
            return True
        elif response.status_code == 401:
            print("❌ TOKEN INVALID - Authentication failed")
            print(f"   Response: {response.text}")
            return False
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def fix_token_format():
    """Provide guidance for token format issues"""
    print("\n💡 DISCORD TOKEN TROUBLESHOOTING:")
    print("1. Go to https://discord.com/developers/applications")
    print("2. Select your bot application")
    print("3. Go to 'Bot' section")
    print("4. Click 'Reset Token'")
    print("5. Copy the ENTIRE token (should be ~70 characters)")
    print("6. DO NOT include 'Bot ' prefix")
    print("7. Token format: XXXXXXXXX.XXXXXX.XXXXXXXXXXXXXXXXXXXXXXXXXXX")

if __name__ == "__main__":
    is_valid = debug_discord_token()
    
    if not is_valid:
        fix_token_format()
    
    print("\n" + "=" * 50)
    print("TOKEN DEBUG COMPLETE")