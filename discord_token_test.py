#!/usr/bin/env python3
"""
Quick Discord token validation test
"""

import os
import discord
import asyncio

async def test_discord_token():
    """Test Discord token validity"""
    try:
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            print("❌ No DISCORD_TOKEN found in environment")
            return False
            
        print(f"🔍 Token format check:")
        print(f"   Length: {len(token)}")
        print(f"   Starts with: {token[:10]}...")
        print(f"   Contains dots: {token.count('.')}")
        
        # Test basic format
        if not token.startswith(('MT', 'mT', 'MTA', 'MTF', 'MTE', 'MTM', 'MDL', 'ODI', 'NzY', 'ODA')):
            print("⚠️ Token doesn't start with expected prefixes (MT*, OD*, etc.)")
        
        if token.count('.') != 2:
            print("⚠️ Token should have exactly 2 dots")
            
        # Try to create bot instance
        intents = discord.Intents.default()
        client = discord.Client(intents=intents)
        
        @client.event
        async def on_ready():
            print(f"✅ Discord bot connected successfully as {client.user}")
            await client.close()
            
        print("🚀 Testing connection...")
        await client.start(token)
        return True
        
    except discord.errors.LoginFailure as e:
        print(f"❌ Login failed: {e}")
        print("This usually means:")
        print("1. Token is invalid/expired")  
        print("2. Token format is wrong")
        print("3. Bot permissions are revoked")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_discord_token())
    if result:
        print("✅ Discord token is working!")
    else:
        print("❌ Discord token needs to be fixed")