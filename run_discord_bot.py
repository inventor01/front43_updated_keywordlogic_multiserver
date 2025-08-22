#!/usr/bin/env python3
"""
Standalone Discord Bot Runner for Railway
This file runs the Discord bot as a separate process
"""

import asyncio
import threading
import time
from complete_discord_bot_with_commands import bot
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_bot():
    """Run the Discord bot"""
    discord_token = os.getenv('DISCORD_TOKEN')
    
    if not discord_token:
        logger.error("❌ DISCORD_TOKEN environment variable is required")
        return
    
    logger.info("🤖 Starting Discord Bot with 35+ commands...")
    logger.info(f"🔑 Using token: {discord_token[:30]}...{discord_token[-10:]}")
    
    try:
        bot.run(discord_token)
    except Exception as e:
        logger.error(f"❌ Bot failed to start: {e}")
        logger.error("💡 Check if token is valid and bot has required permissions")

if __name__ == "__main__":
    run_bot()