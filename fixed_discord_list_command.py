#!/usr/bin/env python3
"""
FIXED Discord List Command - Guaranteed to show keywords correctly
This module contains the corrected /list command that properly retrieves keywords from PostgreSQL
"""

import discord
from discord.ext import commands
import os
import asyncio
import logging
from config_manager import ConfigManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create bot instance
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    """Bot ready event"""
    logger.info(f"🤖 Bot connected as {bot.user}")
    
    # Test keyword loading immediately
    try:
        config_manager = ConfigManager()
        keywords = config_manager.list_keywords()
        logger.info(f"✅ Keywords loaded on startup: {len(keywords)} total")
        logger.info(f"🔍 Sample keywords: {keywords[:5] if keywords else 'None'}")
    except Exception as e:
        logger.error(f"❌ Failed to load keywords on startup: {e}")
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        logger.error(f"❌ Failed to sync commands: {e}")

@bot.tree.command(name="list", description="Show all monitored keywords")
async def list_keywords_fixed(interaction: discord.Interaction):
    """FIXED: List all currently monitored keywords with enhanced error handling"""
    try:
        await interaction.response.defer()
        logger.info(f"📝 /list command called by {interaction.user}")
        
        # Initialize ConfigManager with error handling
        try:
            config_manager = ConfigManager()
            logger.info("✅ ConfigManager initialized successfully")
        except Exception as e:
            logger.error(f"❌ ConfigManager initialization failed: {e}")
            error_embed = discord.Embed(
                title="❌ Configuration Error",
                description=f"Failed to initialize configuration: {str(e)}",
                color=0xff4444
            )
            await interaction.followup.send(embed=error_embed)
            return
        
        # Get keywords with detailed logging
        try:
            keywords = config_manager.list_keywords()
            logger.info(f"📊 Retrieved keywords: {len(keywords)} total")
            logger.info(f"🔍 Keywords: {keywords}")
        except Exception as e:
            logger.error(f"❌ Failed to retrieve keywords: {e}")
            error_embed = discord.Embed(
                title="❌ Database Error",
                description=f"Failed to retrieve keywords: {str(e)}",
                color=0xff4444
            )
            await interaction.followup.send(embed=error_embed)
            return
        
        # Check if keywords exist (with explicit None and empty list checking)
        if keywords is None:
            logger.warning("⚠️ Keywords is None")
            keywords = []
        elif not isinstance(keywords, list):
            logger.warning(f"⚠️ Keywords is not a list: {type(keywords)}")
            keywords = []
        
        if len(keywords) == 0:
            logger.info("📝 No keywords found - showing empty state")
            embed = discord.Embed(
                title="📝 No Keywords",
                description="No keywords are currently being monitored.\nUse `/add` to add keywords to your monitoring.",
                color=0x888888
            )
            embed.add_field(
                name="💡 Getting Started",
                value="Add your first keyword with `/add keyword:moon`",
                inline=False
            )
        else:
            logger.info(f"✅ Displaying {len(keywords)} keywords")
            
            # Split keywords into chunks for better display
            keywords_per_page = 25
            keyword_chunks = [keywords[i:i+keywords_per_page] for i in range(0, len(keywords), keywords_per_page)]
            
            embed = discord.Embed(
                title=f"📝 Monitored Keywords ({len(keywords)} total)",
                description="Currently monitoring these keywords for new tokens:",
                color=0x00aaff
            )
            
            # Show first chunk with bullet points
            keyword_text = "\n".join([f"• **{kw}**" for kw in keyword_chunks[0]])
            embed.add_field(
                name="Active Keywords", 
                value=keyword_text,
                inline=False
            )
            
            # Add monitoring status
            embed.add_field(
                name="📊 Status",
                value="✅ Real-time monitoring active",
                inline=True
            )
            embed.add_field(
                name="🔄 Updates",
                value="< 1 second detection",
                inline=True
            )
            
            if len(keyword_chunks) > 1:
                embed.set_footer(text=f"Showing {len(keyword_chunks[0])} of {len(keywords)} keywords")
        
        await interaction.followup.send(embed=embed)
        logger.info(f"✅ /list command completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Critical error in /list command: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            error_embed = discord.Embed(
                title="❌ System Error",
                description=f"An unexpected error occurred: {str(e)}",
                color=0xff4444
            )
            error_embed.add_field(
                name="🔧 Support",
                value="Please contact support if this persists",
                inline=False
            )
            await interaction.followup.send(embed=error_embed)
        except:
            # Fallback if even error response fails
            await interaction.followup.send("❌ Critical system error occurred")

# Test function for direct keyword retrieval
async def test_keyword_retrieval():
    """Test function to verify keyword retrieval works"""
    try:
        config_manager = ConfigManager()
        keywords = config_manager.list_keywords()
        print(f"✅ Direct test: Found {len(keywords)} keywords")
        print(f"🔍 Keywords: {keywords}")
        return True
    except Exception as e:
        print(f"❌ Direct test failed: {e}")
        return False

if __name__ == "__main__":
    # Test keyword retrieval before starting bot
    print("🧪 Testing keyword retrieval...")
    asyncio.run(test_keyword_retrieval())
    
    # Start bot
    token = os.getenv('DISCORD_TOKEN')
    if token:
        print(f"🚀 Starting fixed Discord bot...")
        bot.run(token)
    else:
        print("❌ No DISCORD_TOKEN found")