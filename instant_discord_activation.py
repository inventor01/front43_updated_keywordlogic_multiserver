#!/usr/bin/env python3
"""
Instant Discord Bot Activation - Comprehensive Solution
"""

import discord
import asyncio
import os
import requests
import sys

async def test_discord_bot_comprehensive():
    """
    Comprehensive Discord bot test with multiple approaches
    """
    token = os.getenv('DISCORD_TOKEN')
    print(f"🧪 COMPREHENSIVE DISCORD BOT TEST")
    print(f"Token length: {len(token) if token else 'None'}")
    
    # Test 1: REST API Direct
    print("\n📡 TEST 1: REST API Direct")
    headers = {'Authorization': f'Bot {token}'}
    try:
        response = requests.get('https://discord.com/api/v10/users/@me', headers=headers)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Bot: {data.get('username')} (ID: {data.get('id')})")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ REST API failed: {e}")
    
    # Test 2: Discord.py with different intents
    print("\n🤖 TEST 2: Discord.py with minimal intents")
    try:
        intents = discord.Intents.none()  # Minimal intents
        client = discord.Client(intents=intents)
        
        @client.event
        async def on_ready():
            print(f"✅ SUCCESS: {client.user} connected!")
            print(f"Bot ID: {client.user.id}")
            print(f"Guilds: {len(client.guilds)}")
            await client.close()
        
        await asyncio.wait_for(client.start(token), timeout=10)
        print("✅ Discord.py connection successful!")
        
    except asyncio.TimeoutError:
        print("⏰ Connection timeout (10s)")
    except discord.LoginFailure as e:
        print(f"❌ Login failure: {e}")
    except Exception as e:
        print(f"❌ Discord.py error: {e}")
    
    # Test 3: Gateway info
    print("\n🌐 TEST 3: Gateway Information")
    try:
        response = requests.get('https://discord.com/api/v10/gateway/bot', headers=headers)
        if response.status_code == 200:
            gateway_data = response.json()
            print(f"✅ Gateway URL: {gateway_data.get('url')}")
            print(f"Shards: {gateway_data.get('shards', 1)}")
            print(f"Session limit: {gateway_data.get('session_start_limit', {}).get('remaining', 'Unknown')}")
        else:
            print(f"❌ Gateway error: {response.status_code}")
    except Exception as e:
        print(f"❌ Gateway test failed: {e}")

    print("\n📋 DIAGNOSIS:")
    print("If REST API works but Discord.py fails:")
    print("1. Token format might be incorrect")
    print("2. Bot might need to be invited to a server")
    print("3. Bot permissions might be insufficient")
    print("4. Rate limiting or temporary Discord issues")
    
    print("\n🔧 SOLUTIONS:")
    print("1. Create completely new bot application")
    print("2. Generate fresh token")
    print("3. Invite bot with Administrator permissions")
    print("4. Wait 24 hours for Discord propagation")

if __name__ == "__main__":
    asyncio.run(test_discord_bot_comprehensive())