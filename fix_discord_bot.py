#!/usr/bin/env python3
"""
Fix Discord bot connection issues by testing different approaches
"""
import os
import asyncio
import discord
from discord.ext import commands

async def test_different_discord_approaches():
    """Test various Discord connection methods"""
    
    token = os.getenv('DISCORD_TOKEN', 'MTM4OTY1Nzg5MDgzNDM1MDE0MA.GnoXWs.BSJoUVHv1lP48pwfyAwHmBJ2HfvfYesHMbTfzg')
    
    print("=== DISCORD CONNECTION DIAGNOSTICS ===")
    print(f"Token length: {len(token)}")
    print(f"Token format: {token[:30]}...")
    
    # Test 1: Basic Client
    print("\n1. Testing basic Discord Client...")
    try:
        intents = discord.Intents.default()
        client = discord.Client(intents=intents)
        
        @client.event
        async def on_ready():
            print(f"✅ Basic Client: Connected as {client.user}")
            await client.close()
        
        await asyncio.wait_for(client.start(token), timeout=10)
        
    except asyncio.TimeoutError:
        print("❌ Basic Client: Connection timeout")
    except discord.LoginFailure:
        print("❌ Basic Client: Login failure - token invalid")
    except Exception as e:
        print(f"❌ Basic Client error: {e}")
    
    # Test 2: Bot with Commands
    print("\n2. Testing Bot with Commands...")
    try:
        intents = discord.Intents.default()
        intents.message_content = True
        bot = commands.Bot(command_prefix='!', intents=intents)
        
        @bot.event
        async def on_ready():
            print(f"✅ Commands Bot: Connected as {bot.user}")
            await bot.close()
        
        await asyncio.wait_for(bot.start(token), timeout=10)
        
    except asyncio.TimeoutError:
        print("❌ Commands Bot: Connection timeout")  
    except discord.LoginFailure:
        print("❌ Commands Bot: Login failure - token invalid")
    except Exception as e:
        print(f"❌ Commands Bot error: {e}")
    
    # Test 3: Minimal intents
    print("\n3. Testing with minimal intents...")
    try:
        intents = discord.Intents.none()
        intents.guilds = True
        client = discord.Client(intents=intents)
        
        @client.event
        async def on_ready():
            print(f"✅ Minimal Intents: Connected as {client.user}")
            await client.close()
        
        await asyncio.wait_for(client.start(token), timeout=10)
        
    except asyncio.TimeoutError:
        print("❌ Minimal Intents: Connection timeout")
    except discord.LoginFailure:
        print("❌ Minimal Intents: Login failure - token invalid")
    except Exception as e:
        print(f"❌ Minimal Intents error: {e}")

if __name__ == "__main__":
    asyncio.run(test_different_discord_approaches())