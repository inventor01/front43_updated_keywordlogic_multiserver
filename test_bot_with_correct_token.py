#!/usr/bin/env python3
"""
Test Discord bot with the correct token directly
"""

import discord
from discord.ext import commands
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
    async def setup_hook(self):
        try:
            synced = await self.tree.sync()
            logger.info(f'✅ Synced {len(synced)} slash commands')
        except Exception as e:
            logger.error(f'Command sync failed: {e}')

    async def on_ready(self):
        logger.info(f'✅ Discord Bot Connected: {self.user}')
        logger.info(f'✅ Connected to {len(self.guilds)} servers')
        
        # Stop after confirming connection
        await asyncio.sleep(2)
        await self.close()

@commands.slash_command(name="test", description="Test command to verify bot is working")
async def test_command(ctx):
    await ctx.respond("✅ Bot is working! Slash commands are active!")

if __name__ == "__main__":
    # Use the correct token directly
    correct_token = "MTM4OTY1Nzg5MDgzNDM1MDE0MA.GvzFGn.A1NpdkeKYWd4fIliZOtpiMYR3ff-B9OblcM2Gk"
    
    bot = TestBot()
    bot.tree.add_command(test_command)
    
    logger.info("🧪 Testing Discord connection with correct token...")
    
    try:
        bot.run(correct_token)
        logger.info("✅ TOKEN WORKS! Bot connected successfully!")
    except Exception as e:
        logger.error(f"❌ Error: {e}")