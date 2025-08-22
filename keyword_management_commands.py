#!/usr/bin/env python3
"""
Discord bot commands for keyword management with automatic synchronization
"""

import discord
from discord.ext import commands
from discord import app_commands
from keyword_sync_manager import KeywordSyncManager, deactivate_keyword_completely, sync_keywords_from_list
from config_manager import ConfigManager
import logging

logger = logging.getLogger(__name__)

class KeywordManagementCommands:
    """Discord commands for managing keywords with automatic database synchronization"""
    
    def __init__(self, bot):
        self.bot = bot
        self.sync_manager = KeywordSyncManager()
        self.config_manager = ConfigManager()
        
        # Initialize database tables
        try:
            self.sync_manager.create_required_tables()
        except Exception as e:
            logger.error(f"Failed to initialize keyword management tables: {e}")
    
    @app_commands.command(name="remove_keyword", description="Remove a keyword from all monitoring systems")
    async def remove_keyword(self, interaction: discord.Interaction, keyword: str):
        """Remove a keyword completely from all systems"""
        await interaction.response.defer()
        
        try:
            keyword = keyword.strip().lower()
            
            # Use comprehensive removal
            success = deactivate_keyword_completely(keyword)
            
            if success:
                embed = discord.Embed(
                    title="✅ Keyword Removed Successfully",
                    description=f"Keyword `{keyword}` has been completely removed from all systems:",
                    color=0x00ff00
                )
                embed.add_field(name="Actions Completed", value=(
                    "• Deactivated in database\n"
                    "• Removed from file watchlist\n"
                    "• Disabled related notifications\n"
                    "• Updated token history\n"
                    "• Added to removal audit log"
                ), inline=False)
                
                # Get updated stats
                status = self.sync_manager.get_sync_status()
                embed.add_field(name="Current Status", value=(
                    f"Active keywords: {status.get('active_keywords', 'Unknown')}\n"
                    f"System sync: {'✅ Healthy' if status.get('sync_healthy', False) else '❌ Issues detected'}"
                ), inline=False)
                
            else:
                embed = discord.Embed(
                    title="❌ Keyword Removal Failed",
                    description=f"Failed to remove keyword `{keyword}` from all systems. Check logs for details.",
                    color=0xff0000
                )
                
            await interaction.edit_original_response(embed=embed)
            
        except Exception as e:
            logger.error(f"Error removing keyword: {e}")
            await interaction.edit_original_response(content=f"❌ Error removing keyword: {str(e)}")
    
    @app_commands.command(name="add_keyword", description="Add a keyword to all monitoring systems")
    async def add_keyword(self, interaction: discord.Interaction, keyword: str):
        """Add a keyword to all systems"""
        await interaction.response.defer()
        
        try:
            keyword = keyword.strip().lower()
            user_id = str(interaction.user.id)
            
            # Use comprehensive addition
            success = self.sync_manager.activate_keyword(keyword, user_id)
            
            if success:
                embed = discord.Embed(
                    title="✅ Keyword Added Successfully",
                    description=f"Keyword `{keyword}` has been added to all monitoring systems:",
                    color=0x00ff00
                )
                embed.add_field(name="Actions Completed", value=(
                    "• Activated in database\n"
                    "• Added to file watchlist\n"
                    "• Ready for token monitoring\n"
                    "• Attributed to your user ID"
                ), inline=False)
                
                # Get updated stats
                status = self.sync_manager.get_sync_status()
                embed.add_field(name="Current Status", value=(
                    f"Active keywords: {status.get('active_keywords', 'Unknown')}\n"
                    f"System sync: {'✅ Healthy' if status.get('sync_healthy', False) else '❌ Issues detected'}"
                ), inline=False)
                
            else:
                embed = discord.Embed(
                    title="❌ Keyword Addition Failed",
                    description=f"Failed to add keyword `{keyword}` to all systems. Check logs for details.",
                    color=0xff0000
                )
                
            await interaction.edit_original_response(embed=embed)
            
        except Exception as e:
            logger.error(f"Error adding keyword: {e}")
            await interaction.edit_original_response(content=f"❌ Error adding keyword: {str(e)}")
    
    @app_commands.command(name="sync_keywords", description="Check and fix keyword synchronization across all systems")
    async def sync_keywords(self, interaction: discord.Interaction):
        """Check and fix keyword synchronization"""
        await interaction.response.defer()
        
        try:
            # Get sync status
            status = self.sync_manager.get_sync_status()
            
            embed = discord.Embed(
                title="🔄 Keyword Synchronization Status",
                color=0x0099ff
            )
            
            embed.add_field(name="Database Status", value=(
                f"Active keywords: {status.get('active_keywords', 'Unknown')}\n"
                f"Inactive keywords: {status.get('inactive_keywords', 'Unknown')}\n"
                f"Sync healthy: {'✅ Yes' if status.get('sync_healthy', False) else '❌ No'}"
            ), inline=False)
            
            # Show recent removals if any
            recent_removals = status.get('recent_removals', [])
            if recent_removals:
                removal_text = "\n".join([
                    f"• `{r['keyword']}` ({r['removed_at'].strftime('%H:%M:%S')})"
                    for r in recent_removals[:5]
                ])
                embed.add_field(name="Recent Removals (24h)", value=removal_text, inline=False)
            
            # Show any errors
            if 'error' in status:
                embed.add_field(name="❌ Error", value=status['error'], inline=False)
                embed.color = 0xff0000
            
            await interaction.edit_original_response(embed=embed)
            
        except Exception as e:
            logger.error(f"Error checking sync status: {e}")
            await interaction.edit_original_response(content=f"❌ Error checking sync: {str(e)}")
    
    @app_commands.command(name="list_keywords", description="List all active keywords")
    async def list_keywords(self, interaction: discord.Interaction):
        """List all active keywords"""
        await interaction.response.defer()
        
        try:
            keywords = list(self.sync_manager.get_active_keywords())
            
            if not keywords:
                embed = discord.Embed(
                    title="📝 Active Keywords",
                    description="No active keywords found.",
                    color=0xffaa00
                )
            else:
                # Split keywords into chunks for display
                keyword_chunks = [keywords[i:i+20] for i in range(0, len(keywords), 20)]
                
                embed = discord.Embed(
                    title=f"📝 Active Keywords ({len(keywords)} total)",
                    color=0x00ff00
                )
                
                for i, chunk in enumerate(keyword_chunks[:3]):  # Show max 3 chunks (60 keywords)
                    keywords_text = ", ".join([f"`{kw}`" for kw in chunk])
                    field_name = f"Keywords {i*20+1}-{min((i+1)*20, len(keywords))}"
                    embed.add_field(name=field_name, value=keywords_text, inline=False)
                
                if len(keywords) > 60:
                    embed.add_field(name="Note", value=f"Showing first 60 keywords. {len(keywords)-60} more available.", inline=False)
            
            await interaction.edit_original_response(embed=embed)
            
        except Exception as e:
            logger.error(f"Error listing keywords: {e}")
            await interaction.edit_original_response(content=f"❌ Error listing keywords: {str(e)}")

def setup_keyword_commands(bot):
    """Setup keyword management commands for the bot"""
    keyword_commands = KeywordManagementCommands(bot)
    
    # Add commands to bot
    bot.tree.add_command(keyword_commands.remove_keyword)
    bot.tree.add_command(keyword_commands.add_keyword) 
    bot.tree.add_command(keyword_commands.sync_keywords)
    bot.tree.add_command(keyword_commands.list_keywords)
    
    return keyword_commands