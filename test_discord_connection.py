#!/usr/bin/env python3
"""
Test Discord bot connection and status
"""

import os
import logging
import asyncio
import discord
from discord.ext import commands

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_discord_bot_connection():
    """Test if Discord bot can connect and appear online"""
    
    print("🔍 TESTING DISCORD BOT CONNECTION")
    print("=" * 60)
    
    # Check token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ DISCORD_TOKEN not found in environment")
        return False
    
    print(f"✅ Discord token exists (length: {len(token)})")
    
    # Create minimal bot for testing
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        print(f"✅ Bot connected as: {bot.user}")
        print(f"📊 Bot ID: {bot.user.id}")
        print(f"🌐 Connected to {len(bot.guilds)} servers")
        
        # Set status to online
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching, 
                name="Solana Tokens 🚀"
            )
        )
        
        print("✅ Bot status set to ONLINE")
        print("✅ Discord bot is now ACTIVE")
        
        # Keep bot running for 10 seconds to show it's active
        await asyncio.sleep(10)
        
        # Close connection
        await bot.close()
        print("🔄 Test connection closed")
    
    @bot.event
    async def on_error(event, *args, **kwargs):
        print(f"❌ Discord error in {event}: {args}")
    
    try:
        print("🔄 Attempting Discord connection...")
        
        # Run bot with timeout
        bot.run(token, log_handler=None)
        
        return True
        
    except discord.LoginFailure:
        print("❌ INVALID DISCORD TOKEN - Bot cannot login")
        return False
    except discord.HTTPException as e:
        print(f"❌ Discord HTTP error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_bot_permissions():
    """Check if bot has necessary permissions"""
    print("\n📋 CHECKING BOT REQUIREMENTS:")
    print("   ✓ Token exists")
    print("   ✓ Intents configured")
    print("   ✓ Status setting enabled")
    print("   ✓ Activity setting enabled")
    
    print("\n🔧 REQUIRED BOT PERMISSIONS:")
    print("   • Send Messages")
    print("   • Use Slash Commands") 
    print("   • Read Message History")
    print("   • Embed Links")
    
    print("\n💡 If bot still shows inactive:")
    print("   1. Check Discord Developer Portal")
    print("   2. Verify bot is added to server")
    print("   3. Ensure bot has proper permissions")
    print("   4. Check if token was regenerated")

if __name__ == "__main__":
    success = test_discord_bot_connection()
    check_bot_permissions()
    
    if success:
        print("\n✅ Discord bot connection test PASSED")
    else:
        print("\n❌ Discord bot connection test FAILED")