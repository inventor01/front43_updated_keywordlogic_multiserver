#!/usr/bin/env python3
"""
Working Discord Bot - Direct Integration with Token Monitor
"""

import discord
from discord.ext import commands
import asyncio
import os
import sys
import json
import requests
sys.path.append('.')
from config_manager import ConfigManager

class TokenMonitorBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
    async def setup_hook(self):
        # Sync slash commands on startup
        try:
            synced = await self.tree.sync()
            print(f'✅ Synced {len(synced)} slash commands')
        except Exception as e:
            print(f'❌ Command sync failed: {e}')

    async def on_ready(self):
        print(f'✅ DISCORD BOT ACTIVE: {self.user}')
        print(f'📊 Connected to {len(self.guilds)} servers')
        print(f'🎯 Bot ID: {self.user.id}')
        
        # Environment check on startup
        database_url = os.getenv('DATABASE_URL')
        print(f'🔧 DATABASE_URL present: {bool(database_url)}')
        if database_url:
            if 'railway.internal' in database_url:
                print('🚂 Using Railway internal database')
            else:
                print('🔗 Using external database')
        
        # Test ConfigManager on startup
        try:
            from config_manager import ConfigManager
            config = ConfigManager()
            keywords = config.list_keywords(user_id='System')
            print(f'🔍 System keywords at startup: {len(keywords)} found')
            print(f'📝 Keywords: {keywords}')
        except Exception as e:
            print(f'❌ ConfigManager startup test failed: {e}')
        
        # Send success notification
        webhook_url = 'https://discord.com/api/webhooks/1390545562746490971/zODF3Er5XaSykD6Jl5IkxKiNqr_ArUCzj0DeH8PaDybGD1fXKKg3vr9xsxt_2jPti9yJ'
        
        embed = {
            'title': '🤖 Discord Bot ACTIVATED!',
            'description': 'Slash commands are now available',
            'color': 0x00ff41,
            'fields': [
                {'name': '✅ Available Commands', 'value': '/add, /remove, /list, /status', 'inline': False},
                {'name': '🎯 Status', 'value': 'Bot connected and ready', 'inline': False}
            ]
        }
        
        try:
            requests.post(webhook_url, json={'embeds': [embed]})
        except:
            pass

bot = TokenMonitorBot()

@bot.tree.command(name="add", description="Add a keyword to monitor for new tokens")
async def add_keyword(interaction: discord.Interaction, keyword: str):
    """Add a keyword to the monitoring system"""
    try:
        await interaction.response.defer()
        
        keyword = keyword.strip().lower()
        logger.info(f"🎮 /add command: keyword='{keyword}' (using System)")
        
        config_manager = ConfigManager()
        success, reason = config_manager.add_keyword(keyword, user_id="System")
        
        if success:
            embed = discord.Embed(
                title="✅ Keyword Added Successfully",
                description=f"Now monitoring for: **{keyword}**",
                color=0x00ff41
            )
            embed.add_field(
                name="📊 Total Keywords", 
                value=f"{len(config_manager.list_keywords(user_id='System'))} active",
                inline=True
            )
        else:
            if reason == "already_exists":
                embed = discord.Embed(
                    title="⚠️ Keyword Already Exists",
                    description=f"**{keyword}** is already being monitored",
                    color=0xffaa00
                )
            elif reason == "no_database":
                embed = discord.Embed(
                    title="❌ Database Error",
                    description="Database connection not available",
                    color=0xff4444
                )
            else:
                embed = discord.Embed(
                    title="❌ Failed to Add Keyword",
                    description=f"Could not add: **{keyword}**\n{reason}",
                    color=0xff4444
                )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Error",
            description=f"Failed to add keyword: {str(e)}",
            color=0xff4444
        )
        await interaction.followup.send(embed=error_embed)

@bot.tree.command(name="remove", description="Remove a keyword from monitoring")
async def remove_keyword(interaction: discord.Interaction, keyword: str):
    """Remove a keyword from the monitoring system"""
    try:
        await interaction.response.defer()
        
        keyword = keyword.strip().lower()
        config_manager = ConfigManager()
        success = config_manager.remove_keyword(keyword, user_id="System")
        
        if success:
            embed = discord.Embed(
                title="✅ Keyword Removed",
                description=f"No longer monitoring: **{keyword}**",
                color=0xff9900
            )
            embed.add_field(
                name="📊 Remaining Keywords", 
                value=f"{len(config_manager.list_keywords(user_id='System'))} active",
                inline=True
            )
        else:
            embed = discord.Embed(
                title="❌ Keyword Not Found",
                description=f"**{keyword}** was not in the monitoring list",
                color=0xff4444
            )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Error",
            description=f"Failed to remove keyword: {str(e)}",
            color=0xff4444
        )
        await interaction.followup.send(embed=error_embed)

@bot.tree.command(name="list", description="Show all monitored keywords")
async def list_keywords(interaction: discord.Interaction):
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
        
        # Get keywords with detailed logging (using System for global keywords)
        database_url = os.getenv('DATABASE_URL')
        logger.info(f"🎮 /list command: using System for global keywords")
        logger.info(f"🔧 DATABASE_URL present: {bool(database_url)}")
        if database_url:
            logger.info(f"🔧 DATABASE_URL format: {database_url[:30]}...{database_url[-20:]}")
        
        try:
            keywords = config_manager.list_keywords(user_id="System")
            logger.info(f"📊 Retrieved keywords for System: {len(keywords)} total")
            logger.info(f"🔍 System keywords: {keywords}")
            logger.info(f"🔧 Keywords type: {type(keywords)}")
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
            database_url = os.getenv('DATABASE_URL')
            logger.error("❌ CRITICAL: No keywords found for System user")
            logger.error(f"❌ DATABASE_URL present: {bool(database_url)}")
            if database_url:
                logger.error(f"❌ DATABASE_URL host: {'railway.internal' if 'railway.internal' in database_url else 'external'}")
            logger.error(f"❌ Keywords type: {type(keywords)}, value: {keywords}")
            
            # Test direct database connection
            try:
                import psycopg2
                conn = psycopg2.connect(database_url, connect_timeout=5)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM keywords WHERE user_id = 'System'")
                count = cursor.fetchone()[0]
                logger.error(f"❌ Direct query result: {count} System keywords")
                cursor.close()
                conn.close()
            except Exception as db_error:
                logger.error(f"❌ Direct database test failed: {db_error}")
            
            embed = discord.Embed(
                title="❌ Database Connection Issue",
                description="Cannot retrieve keywords from database.\n\nCheck Railway logs for connection details.",
                color=0xff4444
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

@bot.tree.command(name="status", description="Show token monitoring system status")
async def system_status(interaction: discord.Interaction):
    """Show current system status and statistics"""
    try:
        await interaction.response.defer()
        
        config_manager = ConfigManager()
        keywords = config_manager.list_keywords()
        
        embed = discord.Embed(
            title="🚀 Token Monitor System Status",
            description="Real-time Solana token monitoring system",
            color=0x00ff41
        )
        
        embed.add_field(
            name="📊 System Status",
            value="✅ Operational",
            inline=True
        )
        embed.add_field(
            name="🔍 Keywords Active",
            value=f"{len(keywords)}",
            inline=True
        )
        embed.add_field(
            name="📡 Notifications",
            value="✅ Discord Webhook",
            inline=True
        )
        embed.add_field(
            name="🎯 Detection Speed",
            value="< 1 second",
            inline=True
        )
        embed.add_field(
            name="💰 Operating Cost",
            value="$0/month",
            inline=True
        )
        embed.add_field(
            name="🔗 Data Source",
            value="DexScreener API",
            inline=True
        )
        
        embed.set_footer(text="Use /add to monitor new keywords • Use /list to see all keywords")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        error_embed = discord.Embed(
            title="❌ Error",
            description=f"Failed to get status: {str(e)}",
            color=0xff4444
        )
        await interaction.followup.send(embed=error_embed)

# Prefix commands as backup
@bot.command(name='add')
async def add_prefix_command(ctx, *, keyword):
    """Add keyword via prefix command"""
    try:
        keyword = keyword.strip().lower()
        config_manager = ConfigManager()
        success, reason = config_manager.add_keyword(keyword)
        
        if success:
            await ctx.send(f"✅ Added keyword: **{keyword}**")
        else:
            if reason == "already_exists":
                await ctx.send(f"⚠️ Keyword **{keyword}** already exists")
            else:
                await ctx.send(f"❌ Failed to add keyword: **{keyword}** - {reason}")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name='remove')
async def remove_prefix_command(ctx, *, keyword):
    """Remove keyword via prefix command"""
    try:
        keyword = keyword.strip().lower()
        config_manager = ConfigManager()
        success = config_manager.remove_keyword(keyword)
        
        if success:
            await ctx.send(f"✅ Removed keyword: **{keyword}**")
        else:
            await ctx.send(f"❌ Keyword not found: **{keyword}**")
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

@bot.command(name='list')
async def list_prefix_command(ctx):
    """List keywords via prefix command"""
    try:
        config_manager = ConfigManager()
        keywords = config_manager.list_keywords()
        
        if keywords:
            keyword_list = ", ".join(keywords[:20])
            message = f"📝 **Keywords ({len(keywords)} total):** {keyword_list}"
            if len(keywords) > 20:
                message += f"\n... and {len(keywords) - 20} more"
        else:
            message = "📝 No keywords currently monitored"
        
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"❌ Error: {e}")

async def run_bot():
    """Run the Discord bot"""
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        print("❌ No DISCORD_TOKEN environment variable found")
        return
    
    print(f"🤖 Starting Discord bot with token: {token[:30]}...")
    
    try:
        await bot.start(token)
    except discord.LoginFailure:
        print("❌ Discord login failed - invalid token")
        print("💡 Create a new Discord bot application and provide fresh token")
    except Exception as e:
        print(f"❌ Bot startup error: {e}")

if __name__ == "__main__":
    asyncio.run(run_bot())