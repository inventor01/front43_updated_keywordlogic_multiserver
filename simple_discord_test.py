#!/usr/bin/env python3
"""
Simple Discord bot test with slash commands
"""
import os
import asyncio
import discord
from discord.ext import commands
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_discord_commands():
    """Test Discord bot with slash commands"""
    
    # Get token from environment
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        logger.error("❌ No DISCORD_TOKEN found in environment")
        return False
    
    logger.info(f"🔑 Testing Discord token: {token[:20]}... ({len(token)} chars)")
    
    # Create bot with slash commands
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = commands.Bot(command_prefix='!', intents=intents)
    
    @bot.event
    async def on_ready():
        logger.info(f"✅ Discord bot connected: {bot.user.name} (ID: {bot.user.id})")
        logger.info(f"🏠 Connected to {len(bot.guilds)} servers")
        
        # Sync slash commands
        try:
            synced = await bot.tree.sync()
            logger.info(f"✅ Synced {len(synced)} slash commands")
            for cmd in synced:
                logger.info(f"  • /{cmd.name}: {cmd.description}")
        except Exception as e:
            logger.error(f"❌ Failed to sync commands: {e}")
        
        # Test completed - shutdown
        logger.info("🎯 Test completed successfully - shutting down")
        await bot.close()

    # Add test slash command
    @bot.tree.command(name="test_search", description="Test search functionality (simplified version)")
    async def test_search(interaction: discord.Interaction, keyword: str = "bonk"):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Simple response to test command registration
            response = f"🔍 **Test Search Command Working!**\n\n"
            response += f"Keyword: '{keyword}'\n"
            response += f"Status: Command registration successful\n"
            response += f"Note: This confirms Discord slash commands are working"
            
            await interaction.followup.send(response, ephemeral=True)
            logger.info(f"✅ Test command executed for keyword: {keyword}")
            
        except Exception as e:
            logger.error(f"❌ Test command error: {e}")
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
    
    try:
        # Start bot with timeout
        await asyncio.wait_for(bot.start(token), timeout=30.0)
        return True
    except discord.LoginFailure as e:
        logger.error(f"❌ Discord login failed: {e}")
        return False
    except asyncio.TimeoutError:
        logger.error("❌ Discord connection timeout")
        return False
    except Exception as e:
        logger.error(f"❌ Discord error: {e}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(test_discord_commands())
        if success:
            logger.info("✅ Discord slash commands test completed successfully")
        else:
            logger.error("❌ Discord slash commands test failed")
    except Exception as e:
        logger.error(f"❌ Test script error: {e}")