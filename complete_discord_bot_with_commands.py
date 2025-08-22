#!/usr/bin/env python3
"""
Front 43_updated_keywordlogic - Enhanced Discord Bot with Bidirectional Keyword Matching
Commands: add, remove, undo, list, clear
Features: Enhanced bidirectional matching for improved token detection
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
        # Use environment DATABASE_URL if available, fallback to Railway
        self.database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway')
    
    def get_connection(self):
        try:
            return psycopg2.connect(self.database_url)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def init_server_tables(self):
        """Initialize server-specific tables for keywords and webhooks"""
        conn = self.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Server webhooks table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS server_webhooks (
                        server_id VARCHAR(50) PRIMARY KEY,
                        webhook_url TEXT NOT NULL,
                        server_name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Server keywords table (separate from global keywords)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS server_keywords (
                        id SERIAL PRIMARY KEY,
                        server_id VARCHAR(50) NOT NULL,
                        user_id VARCHAR(50) NOT NULL,
                        keyword TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(server_id, user_id, keyword)
                    )
                """)
                
                # Server notifications table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS server_notifications (
                        id SERIAL PRIMARY KEY,
                        server_id VARCHAR(50) NOT NULL,
                        token_address TEXT NOT NULL,
                        token_name TEXT,
                        matched_keyword TEXT,
                        user_id VARCHAR(50),
                        notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info("✅ Server-specific database tables initialized")
                
            except Exception as e:
                logger.error(f"Database initialization failed: {e}")
                conn.rollback()
            finally:
                cursor.close()
                conn.close()

class TokenMonitorBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.db = DatabaseManager()
        # Initialize server-specific database tables
        self.db.init_server_tables()
        # Default webhook - can be overridden per server
        self.default_webhook_url = 'https://discord.com/api/webhooks/1390545562746490971/zODF3Er5XaSykD6Jl5IkxKiNqr_ArUCzj0DeH8PaDybGD1fXKKg3vr9xsxt_2jPti9yJ'
        self.server_webhooks = {}  # Cache per-server webhooks
        self.undo_history = {}  # Track all actions per user per server for comprehensive undo
        
    async def setup_hook(self):
        try:
            synced = await self.tree.sync()
            logger.info(f'✅ Synced {len(synced)} slash commands')
            
            # Send startup notification
            embed = {
                'title': '🤖 Front 43_updated_keywordlogic Bot ACTIVATED!',
                'description': f'5 Essential commands ready to use',
                'color': 0x00ff41,
                'fields': [
                    {'name': '✅ Status', 'value': 'Bot connected and ready', 'inline': False},
                    {'name': '📊 Commands', 'value': 'add, remove, undo, list, clear', 'inline': False}
                ]
            }
            
            try:
                requests.post(self.default_webhook_url, json={'embeds': [embed]})
            except:
                pass
                
        except Exception as e:
            logger.error(f'Command sync failed: {e}')

    async def on_ready(self):
        logger.info(f'Front 43_updated_keywordlogic Discord Bot Active: {self.user}')
        logger.info(f'Connected to {len(self.guilds)} servers')
        
        # Load server webhooks into cache
        await self.load_server_webhooks()
    
    async def load_server_webhooks(self):
        """Load all server webhooks into memory for fast access"""
        conn = self.db.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT server_id, webhook_url FROM server_webhooks")
                for server_id, webhook_url in cursor.fetchall():
                    self.server_webhooks[server_id] = webhook_url
                logger.info(f"📡 Loaded webhooks for {len(self.server_webhooks)} servers")
            except Exception as e:
                logger.error(f"Failed to load server webhooks: {e}")
            finally:
                cursor.close()
                conn.close()
    
    def get_server_webhook(self, server_id: str) -> str:
        """Get webhook URL for a specific server"""
        return self.server_webhooks.get(server_id, self.default_webhook_url)
    
    def set_server_webhook(self, server_id: str, webhook_url: str, server_name: str = None):
        """Set webhook URL for a specific server"""
        conn = self.db.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO server_webhooks (server_id, webhook_url, server_name)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (server_id) DO UPDATE SET
                        webhook_url = EXCLUDED.webhook_url,
                        server_name = EXCLUDED.server_name
                """, (server_id, webhook_url, server_name))
                conn.commit()
                self.server_webhooks[server_id] = webhook_url
                logger.info(f"✅ Updated webhook for server {server_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to set server webhook: {e}")
                conn.rollback()
                return False
            finally:
                cursor.close()
                conn.close()
        return False
    
    def get_server_keywords(self, server_id: str) -> List[Dict]:
        """Get all keywords for a specific server"""
        conn = self.get_connection()
        keywords = []
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, keyword FROM server_keywords 
                    WHERE server_id = %s
                """, (server_id,))
                for user_id, keyword in cursor.fetchall():
                    keywords.append({'user_id': user_id, 'keyword': keyword})
            except Exception as e:
                logger.error(f"Failed to get server keywords: {e}")
            finally:
                cursor.close()
                conn.close()
        return keywords
    
    def is_keyword_match(self, token_name: str, keyword: str) -> bool:
        """
        Enhanced bidirectional keyword matching algorithm for Front 43_updated_keywordlogic
        Allows both subset and superset matching with 75% word overlap
        """
        if not token_name or not keyword:
            return False
        
        # Normalize both strings
        normalized_token = token_name.lower().strip()
        normalized_keyword = keyword.lower().strip()
        
        # Remove special characters and normalize
        import re
        normalized_token = re.sub(r'[^\w\s]', ' ', normalized_token)
        normalized_keyword = re.sub(r'[^\w\s]', ' ', normalized_keyword)
        
        # Clean up extra whitespace
        normalized_token = ' '.join(normalized_token.split())
        normalized_keyword = ' '.join(normalized_keyword.split())
        
        # Exact match
        if normalized_keyword == normalized_token:
            return True
        
        # Single word keyword matching (for backwards compatibility)
        if len(normalized_keyword.split()) == 1:
            # Multi-word phrase matching with normalization
            if normalized_keyword in normalized_token:
                return True
            
            # Word-based matching for multi-word keywords  
            token_words = set(word for word in normalized_token.split() if len(word) > 1)
            keyword_words = set(word for word in normalized_keyword.split() if len(word) > 1)
            
            # Skip very short tokens to prevent noise
            if len(normalized_token.strip()) <= 2:
                return False
            
            # ENHANCED BIDIRECTIONAL MATCHING:
            # 1. Original: keyword words must be in token (75% overlap)
            # 2. New: token words must be in keyword (allows subset matching)
            if keyword_words and token_words:
                # Method 1: Traditional - keyword words found in token
                overlap_ratio_1 = len(token_words.intersection(keyword_words)) / len(keyword_words)
                
                # Method 2: Bidirectional - token words found in keyword (for subset matching)
                overlap_ratio_2 = len(token_words.intersection(keyword_words)) / len(token_words)
                
                # Match if EITHER direction has sufficient overlap
                if overlap_ratio_1 >= 0.75 or overlap_ratio_2 >= 0.75:
                    return True
            
            # Word boundaries for single keywords
            token_words = set(word for word in normalized_token.split() if len(word) > 1)
            if normalized_keyword in token_words:
                return True
        
        else:
            # Multi-word phrase matching with normalization
            if normalized_keyword in normalized_token:
                return True
            
            # Word-based matching for multi-word keywords
            token_words = set(word for word in normalized_token.split() if len(word) > 1)
            keyword_words = set(word for word in normalized_keyword.split() if len(word) > 1)
            
            # Skip very short tokens to prevent noise
            if len(normalized_token.strip()) <= 2:
                return False
            
            # ENHANCED BIDIRECTIONAL MATCHING:
            # 1. Original: keyword words must be in token (75% overlap)
            # 2. New: token words must be in keyword (allows subset matching)
            if keyword_words and token_words:
                # Method 1: Traditional - keyword words found in token
                overlap_ratio_1 = len(token_words.intersection(keyword_words)) / len(keyword_words)
                
                # Method 2: Bidirectional - token words found in keyword (for subset matching)
                overlap_ratio_2 = len(token_words.intersection(keyword_words)) / len(token_words)
                
                # Match if EITHER direction has sufficient overlap
                if overlap_ratio_1 >= 0.75 or overlap_ratio_2 >= 0.75:
                    return True
        
        return False

bot = TokenMonitorBot()

# ==================== 6 ESSENTIAL COMMANDS ====================

@bot.tree.command(name="add", description="Add a keyword to monitor for this server")
async def add_keyword(interaction: discord.Interaction, keyword: str):
    """Add a keyword for token monitoring in this server"""
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        server_id = str(interaction.guild.id)
        keyword = keyword.lower().strip()
        
        if not keyword or len(keyword) < 2:
            await interaction.followup.send("❌ Keyword must be at least 2 characters long")
            return
        
        conn = bot.db.get_connection()
        if not conn:
            await interaction.followup.send("❌ Database connection failed")
            return
            
        cursor = conn.cursor()
        
        # Check if keyword already exists for this user in this server
        cursor.execute("SELECT 1 FROM server_keywords WHERE server_id = %s AND user_id = %s AND keyword = %s", (server_id, user_id, keyword))
        if cursor.fetchone():
            await interaction.followup.send(f"⚠️ Keyword '{keyword}' already exists in this server")
            cursor.close()
            conn.close()
            return
        
        # Add keyword for this server
        cursor.execute(
            "INSERT INTO server_keywords (server_id, user_id, keyword, created_at) VALUES (%s, %s, %s, %s)",
            (server_id, user_id, keyword, datetime.now())
        )
        conn.commit()
        
        # Count total keywords for user in this server
        cursor.execute("SELECT COUNT(*) FROM server_keywords WHERE server_id = %s AND user_id = %s", (server_id, user_id))
        total_keywords = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        embed = discord.Embed(
            title="✅ Keyword Added",
            description=f"Now monitoring: **{keyword}**",
            color=0x00ff41,
            timestamp=datetime.now()
        )
        embed.add_field(name="📊 Total Keywords", value=f"{total_keywords}", inline=True)
        embed.add_field(name="👤 User", value=f"<@{interaction.user.id}>", inline=True)
        
        # Store action for undo (include server context)
        undo_key = f"{server_id}_{user_id}"
        bot.undo_history[undo_key] = {
            'action': 'add',
            'keyword': keyword,
            'server_id': server_id,
            'timestamp': datetime.now()
        }
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error adding keyword: {str(e)}")

@bot.tree.command(name="remove", description="Remove a keyword from monitoring in this server")
async def remove_keyword(interaction: discord.Interaction, keyword: str):
    """Remove a keyword from monitoring in this server"""
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        server_id = str(interaction.guild.id)
        keyword = keyword.lower().strip()
        
        conn = bot.db.get_connection()
        if not conn:
            await interaction.followup.send("❌ Database connection failed")
            return
            
        cursor = conn.cursor()
        
        # Check if keyword exists in this server
        cursor.execute("SELECT keyword FROM server_keywords WHERE server_id = %s AND user_id = %s AND keyword = %s", (server_id, user_id, keyword))
        existing = cursor.fetchone()
        
        if not existing:
            await interaction.followup.send(f"❌ Keyword '{keyword}' not found in this server")
            cursor.close()
            conn.close()
            return
        
        # Store action for undo (include server context)
        undo_key = f"{server_id}_{user_id}"
        bot.undo_history[undo_key] = {
            'action': 'remove',
            'keyword': keyword,
            'server_id': server_id,
            'timestamp': datetime.now()
        }
        
        # Remove keyword from this server
        cursor.execute("DELETE FROM server_keywords WHERE server_id = %s AND user_id = %s AND keyword = %s", (server_id, user_id, keyword))
        conn.commit()
        
        # Count remaining keywords in this server
        cursor.execute("SELECT COUNT(*) FROM server_keywords WHERE server_id = %s AND user_id = %s", (server_id, user_id))
        remaining_keywords = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        embed = discord.Embed(
            title="🗑️ Keyword Removed",
            description=f"Stopped monitoring: **{keyword}**",
            color=0xff6b6b,
            timestamp=datetime.now()
        )
        embed.add_field(name="📊 Remaining Keywords", value=f"{remaining_keywords}", inline=True)
        embed.add_field(name="↩️ Tip", value="Use `/undo` to restore this keyword", inline=True)
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error removing keyword: {str(e)}")

@bot.tree.command(name="undo", description="Undo the last action (add, remove, or clear)")
async def undo_keyword(interaction: discord.Interaction):
    """Undo the last action (add, remove, or clear)"""
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        
        if user_id not in bot.undo_history:
            await interaction.followup.send("❌ No recent action to undo")
            return
            
        last_action = bot.undo_history[user_id]
        action_type = last_action['action']
        
        conn = bot.db.get_connection()
        if not conn:
            await interaction.followup.send("❌ Database connection failed")
            return
            
        cursor = conn.cursor()
        
        if action_type == 'add':
            # Undo an add action (remove the keyword)
            keyword = last_action['keyword']
            cursor.execute("DELETE FROM keywords WHERE user_id = %s AND keyword = %s", (user_id, keyword))
            conn.commit()
            
            cursor.execute("SELECT COUNT(*) FROM keywords WHERE user_id = %s", (user_id,))
            remaining_keywords = cursor.fetchone()[0]
            
            embed = discord.Embed(
                title="↩️ Add Action Undone",
                description=f"Removed recently added keyword: **{keyword}**",
                color=0xff6b6b,
                timestamp=datetime.now()
            )
            embed.add_field(name="📊 Remaining Keywords", value=f"{remaining_keywords}", inline=True)
            
        elif action_type == 'remove':
            # Undo a remove action (restore the keyword)
            keyword = last_action['keyword']
            
            # Check if keyword was re-added manually
            cursor.execute("SELECT 1 FROM keywords WHERE user_id = %s AND keyword = %s", (user_id, keyword))
            if cursor.fetchone():
                await interaction.followup.send(f"⚠️ Keyword '{keyword}' already exists")
                cursor.close()
                conn.close()
                return
            
            cursor.execute(
                "INSERT INTO keywords (user_id, keyword, created_at) VALUES (%s, %s, %s)",
                (user_id, keyword, datetime.now())
            )
            conn.commit()
            
            cursor.execute("SELECT COUNT(*) FROM keywords WHERE user_id = %s", (user_id,))
            total_keywords = cursor.fetchone()[0]
            
            embed = discord.Embed(
                title="↩️ Removal Undone",
                description=f"Restored keyword: **{keyword}**",
                color=0x00ff41,
                timestamp=datetime.now()
            )
            embed.add_field(name="📊 Total Keywords", value=f"{total_keywords}", inline=True)
            
        elif action_type == 'clear':
            # Undo a clear action (restore all keywords)
            keywords_to_restore = last_action['keywords']
            
            for keyword in keywords_to_restore:
                cursor.execute(
                    "INSERT INTO keywords (user_id, keyword, created_at) VALUES (%s, %s, %s)",
                    (user_id, keyword, datetime.now())
                )
            conn.commit()
            
            cursor.execute("SELECT COUNT(*) FROM keywords WHERE user_id = %s", (user_id,))
            total_keywords = cursor.fetchone()[0]
            
            embed = discord.Embed(
                title="↩️ Clear Action Undone",
                description=f"Restored **{len(keywords_to_restore)}** keywords from clear operation",
                color=0x00ff41,
                timestamp=datetime.now()
            )
            embed.add_field(name="📊 Total Keywords", value=f"{total_keywords}", inline=True)
            embed.add_field(name="📝 Restored", value=f"{', '.join(keywords_to_restore[:5])}{'...' if len(keywords_to_restore) > 5 else ''}", inline=False)
        
        # Clear undo history after successful undo
        del bot.undo_history[user_id]
        
        cursor.close()
        conn.close()
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error restoring keyword: {str(e)}")

@bot.tree.command(name="list", description="List all your monitored keywords for this server")
async def list_keywords(interaction: discord.Interaction):
    """List all keywords being monitored by the user in this server"""
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        server_id = str(interaction.guild.id)
        
        conn = bot.db.get_connection()
        if not conn:
            await interaction.followup.send("❌ Database connection failed")
            return
            
        cursor = conn.cursor()
        cursor.execute(
            "SELECT keyword, created_at FROM server_keywords WHERE server_id = %s AND user_id = %s ORDER BY created_at DESC",
            (server_id, user_id)
        )
        keywords = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not keywords:
            await interaction.followup.send("📝 No keywords found. Use `/add <keyword>` to start monitoring.")
            return
        
        # Format keywords for display
        keyword_list = []
        for i, (keyword, created_at) in enumerate(keywords, 1):
            formatted_date = created_at.strftime("%m/%d")
            keyword_list.append(f"{i}. **{keyword}** *(added {formatted_date})*")
        
        # Split into chunks if too many keywords
        chunks = [keyword_list[i:i+10] for i in range(0, len(keyword_list), 10)]
        
        for chunk_idx, chunk in enumerate(chunks):
            embed = discord.Embed(
                title=f"📝 Your Keywords {f'(Page {chunk_idx + 1})' if len(chunks) > 1 else ''}",
                description="\n".join(chunk),
                color=0x3498db,
                timestamp=datetime.now()
            )
            embed.add_field(name="📊 Total", value=f"{len(keywords)} keywords", inline=True)
            embed.add_field(name="👤 User", value=f"<@{interaction.user.id}>", inline=True)
            
            if chunk_idx == 0:
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error listing keywords: {str(e)}")

@bot.tree.command(name="clear", description="Remove ALL your keywords (use with caution)")
async def clear_keywords(interaction: discord.Interaction, confirm: str):
    """Clear all keywords for the user (requires confirmation)"""
    try:
        await interaction.response.defer()
        
        user_id = str(interaction.user.id)
        
        # Require exact confirmation
        if confirm.lower() != "yes i want to delete all":
            embed = discord.Embed(
                title="⚠️ Confirmation Required",
                description="To clear ALL your keywords, use:\n`/clear confirm: yes i want to delete all`",
                color=0xffa500
            )
            embed.add_field(name="⚠️ Warning", value="This action cannot be undone", inline=False)
            await interaction.followup.send(embed=embed)
            return
        
        conn = bot.db.get_connection()
        if not conn:
            await interaction.followup.send("❌ Database connection failed")
            return
            
        cursor = conn.cursor()
        
        # Get all keywords before deletion for undo functionality
        cursor.execute("SELECT keyword FROM keywords WHERE user_id = %s", (user_id,))
        keywords_to_delete = [row[0] for row in cursor.fetchall()]
        
        if not keywords_to_delete:
            await interaction.followup.send("📝 No keywords to clear")
            cursor.close()
            conn.close()
            return
        
        # Store action for undo before deletion
        bot.undo_history[user_id] = {
            'action': 'clear',
            'keywords': keywords_to_delete,
            'timestamp': datetime.now()
        }
        
        # Delete all keywords for user
        cursor.execute("DELETE FROM keywords WHERE user_id = %s", (user_id,))
        conn.commit()
        keyword_count = len(keywords_to_delete)
        
        cursor.close()
        conn.close()
        
        # Note: Undo history is preserved for clear operations
        
        embed = discord.Embed(
            title="🗑️ Keywords Cleared",
            description=f"Removed **{keyword_count}** keywords from monitoring",
            color=0xff6b6b,
            timestamp=datetime.now()
        )
        embed.add_field(name="📊 Status", value="No keywords active", inline=True)
        embed.add_field(name="➕ Next Step", value="Use `/add` to start monitoring", inline=True)
        embed.add_field(name="↩️ Tip", value="Use `/undo` to restore all keywords", inline=True)
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"❌ Error clearing keywords: {str(e)}")

@bot.tree.command(name="webhook", description="Configure webhook URL for this server (Admin only)")
async def set_webhook(interaction: discord.Interaction, webhook_url: str):
    """Set the webhook URL for token notifications in this server"""
    try:
        await interaction.response.defer()
        
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ Only server administrators can configure webhooks")
            return
        
        server_id = str(interaction.guild.id)
        server_name = interaction.guild.name
        
        # Validate webhook URL format
        if not webhook_url.startswith('https://discord.com/api/webhooks/'):
            await interaction.followup.send("❌ Invalid webhook URL format. Use Discord webhook URL.")
            return
        
        # Set the webhook for this server
        success = bot.set_server_webhook(server_id, webhook_url, server_name)
        
        if success:
            embed = discord.Embed(
                title="✅ Webhook Configured",
                description=f"Token notifications will be sent to this server's configured channel.",
                color=0x00ff41,
                timestamp=datetime.now()
            )
            embed.add_field(name="🏢 Server", value=server_name, inline=True)
            embed.add_field(name="👤 Admin", value=f"<@{interaction.user.id}>", inline=True)
            embed.add_field(name="🔔 Status", value="Ready for notifications", inline=False)
            
            await interaction.followup.send(embed=embed)
            
            # Test the webhook with a notification
            try:
                test_embed = {
                    'title': '🧪 Webhook Test Successful',
                    'description': f'Token notifications are now active for **{server_name}**',
                    'color': 0x00ff41,
                    'fields': [
                        {'name': '🏢 Server', 'value': server_name, 'inline': True},
                        {'name': '⚙️ Setup', 'value': 'Webhook configured successfully', 'inline': True}
                    ]
                }
                requests.post(webhook_url, json={'embeds': [test_embed]})
            except:
                pass  # Silent fail for test notification
                
        else:
            await interaction.followup.send("❌ Failed to configure webhook. Please try again.")
            
    except Exception as e:
        await interaction.followup.send(f"❌ Error configuring webhook: {str(e)}")

# ==================== BOT STARTUP ====================

async def main():
    """Main function to start the bot"""
    try:
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            logger.error("❌ DISCORD_TOKEN environment variable not found")
            return
        
        logger.info("🤖 Starting Front 43_updated_keywordlogic Discord Bot with 5 commands...")
        logger.info(f"🔑 Using token: {token[:30]}...{token[-10:]}")
        
        await bot.start(token)
        
    except discord.errors.LoginFailure:
        logger.error("❌ Bot failed to start: Improper token has been passed.")
        logger.error("💡 Check if token is valid and bot has required permissions")
    except Exception as e:
        logger.error(f"❌ Bot startup failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())