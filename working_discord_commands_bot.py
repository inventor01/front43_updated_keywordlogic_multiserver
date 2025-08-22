#!/usr/bin/env python3
"""
Working Discord Bot with Slash Commands for Token Monitoring
Fixed version with proper error handling and command sync
"""

import discord
from discord.ext import commands
import asyncio
import psycopg2
import os
import requests
import json
import time
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            self.database_url = 'postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway'
    
    def get_connection(self):
        try:
            return psycopg2.connect(self.database_url)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None

class TokenMonitorBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.db = DatabaseManager()
        self.webhook_url = 'https://discord.com/api/webhooks/1390545562746490971/zODF3Er5XaSykD6Jl5IkxKiNqr_ArUCzj0DeH8PaDybGD1fXKKg3vr9xsxt_2jPti9yJ'
        
    async def setup_hook(self):
        try:
            logger.info("🔄 Starting command synchronization...")
            synced = await self.tree.sync()
            logger.info(f'✅ Successfully synced {len(synced)} slash commands')
            
            # Send startup notification
            embed = {
                'title': '🤖 Discord Bot ACTIVATED!',
                'description': f'All {len(synced)} slash commands are now available',
                'color': 0x00ff41,
                'fields': [
                    {'name': '✅ Status', 'value': 'Bot connected and ready', 'inline': False},
                    {'name': '📊 Commands', 'value': f'{len(synced)} slash commands available', 'inline': False},
                    {'name': '🔗 Invite URL', 'value': 'https://discord.com/api/oauth2/authorize?client_id=1389657890834350140&permissions=16853000&scope=bot%20applications.commands', 'inline': False}
                ]
            }
            
            try:
                response = requests.post(self.webhook_url, json={'embeds': [embed]})
                logger.info(f"Startup notification sent: {response.status_code}")
            except Exception as e:
                logger.error(f"Failed to send startup notification: {e}")
                
        except Exception as e:
            logger.error(f'Command sync failed: {e}')
            logger.error("❗ Bot may not have correct permissions. Re-invite with applications.commands scope!")

    async def on_ready(self):
        logger.info(f'🤖 Discord Bot Active: {self.user}')
        logger.info(f'🌐 Connected to {len(self.guilds)} servers')
        logger.info(f'🆔 Bot ID: {self.user.id}')

# Initialize bot
bot = TokenMonitorBot()

# ==================== CORE COMMANDS ====================

@bot.tree.command(name="ping", description="Check if the bot is responsive")
async def ping(interaction: discord.Interaction):
    """Simple ping command to test bot responsiveness"""
    try:
        start_time = time.time()
        await interaction.response.defer()
        end_time = time.time()
        
        latency = round((end_time - start_time) * 1000, 2)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot is responsive",
            color=0x00ff41
        )
        embed.add_field(name="⚡ Response Time", value=f"{latency}ms", inline=True)
        embed.add_field(name="📶 WebSocket Latency", value=f"{round(bot.latency * 1000, 2)}ms", inline=True)
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Ping command error: {e}")
        try:
            await interaction.followup.send("❌ Error in ping command")
        except:
            pass

@bot.tree.command(name="status", description="Check bot and system status")
async def status(interaction: discord.Interaction):
    """Check bot and monitoring system status"""
    try:
        await interaction.response.defer()
        
        # Test database connection
        conn = bot.db.get_connection()
        db_status = "✅ Connected" if conn else "❌ Disconnected"
        
        keyword_count = 0
        tokens_24h = 0
        user_count = 0
        
        if conn:
            try:
                cursor = conn.cursor()
                
                # Get keyword count
                cursor.execute("SELECT COUNT(*) FROM keywords")
                result = cursor.fetchone()
                keyword_count = result[0] if result else 0
                
                # Get 24h token count
                cursor.execute("SELECT COUNT(*) FROM detected_tokens WHERE created_at > NOW() - INTERVAL '24 hours'")
                result = cursor.fetchone()
                tokens_24h = result[0] if result else 0
                
                # Get user count
                cursor.execute("SELECT COUNT(DISTINCT user_id) FROM keywords")
                result = cursor.fetchone()
                user_count = result[0] if result else 0
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                logger.error(f"Database query error: {e}")
        
        embed = discord.Embed(
            title="🤖 System Status",
            color=0x00ff41,
            timestamp=datetime.now()
        )
        embed.add_field(name="🔌 Bot Status", value="✅ Online", inline=True)
        embed.add_field(name="🗄️ Database", value=db_status, inline=True)
        embed.add_field(name="📊 Servers", value=f"{len(bot.guilds)}", inline=True)
        embed.add_field(name="🔍 Keywords", value=f"{keyword_count} active", inline=True)
        embed.add_field(name="👥 Users", value=f"{user_count} monitoring", inline=True)
        embed.add_field(name="📈 Tokens (24h)", value=f"{tokens_24h} detected", inline=True)
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Status command error: {e}")
        try:
            await interaction.followup.send(f"❌ Error checking status: {str(e)}")
        except:
            pass

@bot.tree.command(name="help", description="Show all available commands")
async def help_command(interaction: discord.Interaction):
    """Display help information for all available commands"""
    try:
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🤖 Discord Bot Commands",
            description="Complete list of available slash commands",
            color=0x3498db
        )
        
        # Core Commands
        embed.add_field(
            name="🔧 Core Commands",
            value="`/ping` - Test bot responsiveness\n"
                  "`/status` - Check system status\n"
                  "`/help` - Show this help message",
            inline=False
        )
        
        # Keyword Commands
        embed.add_field(
            name="🔍 Keyword Management",
            value="`/add_keyword` - Add keyword to monitor\n"
                  "`/remove_keyword` - Remove keyword\n"
                  "`/list_keywords` - Show your keywords\n"
                  "`/clear_keywords` - Remove all keywords",
            inline=False
        )
        
        # Token Commands
        embed.add_field(
            name="📊 Token Information",
            value="`/recent_tokens` - Show recent detections\n"
                  "`/token_info` - Get token details\n"
                  "`/search_tokens` - Search token history",
            inline=False
        )
        
        # Market Commands
        embed.add_field(
            name="💰 Market Data",
            value="`/market_data` - Get token market info\n"
                  "`/price_alert` - Set price alerts\n"
                  "`/trending` - Show trending tokens",
            inline=False
        )
        
        embed.add_field(
            name="🔗 Useful Links",
            value="[Re-invite Bot](https://discord.com/api/oauth2/authorize?client_id=1389657890834350140&permissions=16853000&scope=bot%20applications.commands)\n"
                  "[Support Server](https://discord.gg/your-support-server)",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Help command error: {e}")
        try:
            await interaction.followup.send("❌ Error displaying help")
        except:
            pass

# ==================== KEYWORD MANAGEMENT ====================

@bot.tree.command(name="add_keyword", description="Add a keyword to monitor for new tokens")
async def add_keyword(interaction: discord.Interaction, keyword: str):
    """Add a keyword to the user's monitoring list"""
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        keyword = keyword.strip().lower()
        
        if not keyword:
            await interaction.followup.send("❌ Please provide a valid keyword")
            return
        
        conn = bot.db.get_connection()
        if not conn:
            await interaction.followup.send("❌ Database connection failed")
            return
        
        try:
            cursor = conn.cursor()
            
            # Check if keyword already exists for this user
            cursor.execute(
                "SELECT COUNT(*) FROM keywords WHERE user_id = %s AND keyword = %s",
                (user_id, keyword)
            )
            result = cursor.fetchone()
            
            if result and result[0] > 0:
                await interaction.followup.send(f"⚠️ Keyword '{keyword}' is already in your list")
                return
            
            # Add the keyword
            cursor.execute(
                "INSERT INTO keywords (user_id, keyword, created_at) VALUES (%s, %s, NOW())",
                (user_id, keyword)
            )
            conn.commit()
            
            # Get total keyword count for user
            cursor.execute("SELECT COUNT(*) FROM keywords WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            total_keywords = result[0] if result else 0
            
            cursor.close()
            conn.close()
            
            embed = discord.Embed(
                title="✅ Keyword Added",
                description=f"Now monitoring: **{keyword}**",
                color=0x00ff41
            )
            embed.add_field(name="👤 User", value=interaction.user.mention, inline=True)
            embed.add_field(name="📊 Total Keywords", value=f"{total_keywords}", inline=True)
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Database error in add_keyword: {e}")
            await interaction.followup.send(f"❌ Database error: {str(e)}")
        finally:
            if conn:
                conn.close()
        
    except Exception as e:
        logger.error(f"Add keyword command error: {e}")
        try:
            await interaction.followup.send(f"❌ Error adding keyword: {str(e)}")
        except:
            pass

@bot.tree.command(name="list_keywords", description="Show all your monitored keywords")
async def list_keywords(interaction: discord.Interaction):
    """Display all keywords for the current user"""
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        
        conn = bot.db.get_connection()
        if not conn:
            await interaction.followup.send("❌ Database connection failed")
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT keyword, created_at FROM keywords WHERE user_id = %s ORDER BY created_at DESC",
                (user_id,)
            )
            keywords = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            if not keywords:
                embed = discord.Embed(
                    title="📝 Your Keywords",
                    description="You haven't added any keywords yet.\nUse `/add_keyword` to start monitoring!",
                    color=0xffa500
                )
            else:
                keyword_list = []
                for i, (keyword, created_at) in enumerate(keywords, 1):
                    # Format date
                    date_str = created_at.strftime("%Y-%m-%d") if created_at else "Unknown"
                    keyword_list.append(f"{i}. **{keyword}** _(added {date_str})_")
                
                # Split into chunks if too many keywords
                if len(keyword_list) <= 20:
                    description = "\n".join(keyword_list)
                else:
                    description = "\n".join(keyword_list[:20]) + f"\n... and {len(keyword_list) - 20} more"
                
                embed = discord.Embed(
                    title="📝 Your Keywords",
                    description=description,
                    color=0x3498db
                )
                embed.add_field(name="📊 Total", value=f"{len(keywords)} keywords", inline=True)
            
            embed.add_field(name="👤 User", value=interaction.user.mention, inline=True)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Database error in list_keywords: {e}")
            await interaction.followup.send(f"❌ Database error: {str(e)}")
        finally:
            if conn:
                conn.close()
        
    except Exception as e:
        logger.error(f"List keywords command error: {e}")
        try:
            await interaction.followup.send(f"❌ Error listing keywords: {str(e)}")
        except:
            pass

@bot.tree.command(name="recent_tokens", description="Show recently detected tokens")
async def recent_tokens(interaction: discord.Interaction, limit: int = 10):
    """Show recently detected tokens"""
    try:
        await interaction.response.defer()
        
        if limit > 20:
            limit = 20
        
        conn = bot.db.get_connection()
        if not conn:
            await interaction.followup.send("❌ Database connection failed")
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, symbol, contract_address, created_at 
                FROM detected_tokens 
                WHERE name IS NOT NULL AND name != 'Unnamed Token'
                ORDER BY created_at DESC 
                LIMIT %s
            """, (limit,))
            
            tokens = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if not tokens:
                embed = discord.Embed(
                    title="📊 Recent Tokens",
                    description="No tokens detected recently",
                    color=0xffa500
                )
            else:
                token_list = []
                for i, (name, symbol, contract, created_at) in enumerate(tokens, 1):
                    # Format time
                    if created_at:
                        time_ago = datetime.now() - created_at
                        if time_ago.seconds < 3600:
                            time_str = f"{time_ago.seconds // 60}m ago"
                        elif time_ago.seconds < 86400:
                            time_str = f"{time_ago.seconds // 3600}h ago"
                        else:
                            time_str = f"{time_ago.days}d ago"
                    else:
                        time_str = "Unknown"
                    
                    # Truncate long names
                    display_name = name[:30] + "..." if len(name) > 30 else name
                    token_list.append(f"{i}. **{display_name}** ({symbol}) - _{time_str}_")
                
                embed = discord.Embed(
                    title="📊 Recent Tokens",
                    description="\n".join(token_list),
                    color=0x3498db
                )
            
            embed.add_field(name="🕒 Updated", value="Just now", inline=True)
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Database error in recent_tokens: {e}")
            await interaction.followup.send(f"❌ Database error: {str(e)}")
        finally:
            if conn:
                conn.close()
        
    except Exception as e:
        logger.error(f"Recent tokens command error: {e}")
        try:
            await interaction.followup.send(f"❌ Error getting recent tokens: {str(e)}")
        except:
            pass

# ==================== BOT STARTUP ====================

def main():
    """Main function to start the Discord bot"""
    discord_token = os.getenv('DISCORD_TOKEN')
    if not discord_token:
        logger.error("❌ DISCORD_TOKEN environment variable not found!")
        return
    
    logger.info("🚀 Starting Discord Bot...")
    logger.info(f"🔗 Bot invite URL: https://discord.com/api/oauth2/authorize?client_id=1389657890834350140&permissions=16853000&scope=bot%20applications.commands")
    
    try:
        bot.run(discord_token)
    except discord.LoginFailure:
        logger.error("❌ Invalid Discord token!")
    except Exception as e:
        logger.error(f"❌ Bot startup failed: {e}")

if __name__ == "__main__":
    main()