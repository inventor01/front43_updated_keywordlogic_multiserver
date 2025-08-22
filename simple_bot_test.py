#!/usr/bin/env python3
"""
Simple Discord bot test with correct token
"""

import discord
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleBot(discord.Client):
    async def on_ready(self):
        logger.info(f'✅ SUCCESS! Bot logged in as: {self.user}')
        logger.info(f'✅ Connected to {len(self.guilds)} servers')
        logger.info('✅ Token is VALID and working!')
        
        # Close after 3 seconds to confirm it works
        await asyncio.sleep(3)
        await self.close()

if __name__ == "__main__":
    # Test with the correct token
    correct_token = "MTM4OTY1Nzg5MDgzNDM1MDE0MA.GvzFGn.A1NpdkeKYWd4fIliZOtpiMYR3ff-B9OblcM2Gk"
    
    intents = discord.Intents.default()
    bot = SimpleBot(intents=intents)
    
    logger.info("🧪 Testing connection with correct token...")
    
    try:
        bot.run(correct_token)
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")