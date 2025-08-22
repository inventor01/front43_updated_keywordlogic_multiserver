"""
Social media commands for Discord bot without external API dependencies
"""

import logging
from typing import Dict, List, Optional
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

class APIFreeSocialCommands:
    """Social media related Discord commands using free methods"""
    
    def __init__(self, bot, monitoring_server):
        self.bot = bot
        self.monitoring_server = monitoring_server
    
    def setup_commands(self):
        """Set up social media Discord commands"""
        
        @self.bot.tree.command(name="add_social_link", description="Add a social media link to monitor")
        async def add_social_link(interaction: discord.Interaction, url: str):
            """Add a social media link for monitoring"""
            try:
                user_id = str(interaction.user.id)
                
                # Validate URL
                if not url.startswith(('http://', 'https://')):
                    await interaction.response.send_message("❌ Please provide a valid URL starting with http:// or https://", ephemeral=True)
                    return
                
                # Store the link (simplified storage)
                if not hasattr(self.monitoring_server, 'social_links'):
                    self.monitoring_server.social_links = {}
                
                if user_id not in self.monitoring_server.social_links:
                    self.monitoring_server.social_links[user_id] = []
                
                self.monitoring_server.social_links[user_id].append(url)
                
                embed = discord.Embed(
                    title="✅ Social Link Added",
                    description=f"Now monitoring: {url}",
                    color=0x00ff00
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f"Error adding social link: {e}")
                await interaction.response.send_message("❌ Error adding social link", ephemeral=True)
        
        @self.bot.tree.command(name="list_social_links", description="List your monitored social media links")
        async def list_social_links(interaction: discord.Interaction):
            """List monitored social media links"""
            try:
                user_id = str(interaction.user.id)
                
                if not hasattr(self.monitoring_server, 'social_links'):
                    self.monitoring_server.social_links = {}
                
                user_links = self.monitoring_server.social_links.get(user_id, [])
                
                if not user_links:
                    await interaction.response.send_message("📭 You have no social media links being monitored.", ephemeral=True)
                    return
                
                embed = discord.Embed(
                    title="📱 Your Monitored Social Links",
                    color=0x3498db
                )
                
                for i, link in enumerate(user_links, 1):
                    embed.add_field(
                        name=f"Link {i}",
                        value=link,
                        inline=False
                    )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f"Error listing social links: {e}")
                await interaction.response.send_message("❌ Error retrieving social links", ephemeral=True)
        
        @self.bot.tree.command(name="remove_social_link", description="Remove a social media link from monitoring")
        async def remove_social_link(interaction: discord.Interaction, url: str):
            """Remove a social media link from monitoring"""
            try:
                user_id = str(interaction.user.id)
                
                if not hasattr(self.monitoring_server, 'social_links'):
                    self.monitoring_server.social_links = {}
                
                user_links = self.monitoring_server.social_links.get(user_id, [])
                
                if url in user_links:
                    user_links.remove(url)
                    embed = discord.Embed(
                        title="✅ Social Link Removed",
                        description=f"Stopped monitoring: {url}",
                        color=0x00ff00
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Link Not Found",
                        description=f"URL not found in your monitored links: {url}",
                        color=0xff0000
                    )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except Exception as e:
                logger.error(f"Error removing social link: {e}")
                await interaction.response.send_message("❌ Error removing social link", ephemeral=True)


def setup_api_free_social_commands(bot, monitoring_server):
    """Setup function that the main server expects to import"""
    try:
        social_commands = APIFreeSocialCommands(bot, monitoring_server)
        social_commands.setup_commands()
        logger.info("✅ API-free social media commands initialized successfully")
        return social_commands
    except Exception as e:
        logger.error(f"❌ Failed to setup API-free social commands: {e}")
        return None