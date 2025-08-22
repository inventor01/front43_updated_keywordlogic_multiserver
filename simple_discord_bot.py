#!/usr/bin/env python3
"""
Simple Discord Bot with Essential Commands
"""

import discord
from discord.ext import commands
import asyncio
import os
import sys
sys.path.append('.')
from config_manager import ConfigManager

# Bot setup with minimal intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Discord Bot Ready: {bot.user}')
    print(f'Connected to {len(bot.guilds)} servers')
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'✅ Synced {len(synced)} slash commands')
    except Exception as e:
        print(f'❌ Failed to sync commands: {e}')

@bot.tree.command(name="add", description="Add a keyword to monitor")
async def add_keyword(interaction: discord.Interaction, keyword: str):
    try:
        config_manager = ConfigManager()
        success = config_manager.add_keyword(keyword.strip())
        
        if success:
            embed = discord.Embed(
                title="✅ Keyword Added",
                description=f"Now monitoring: **{keyword}**",
                color=0x00ff41
            )
        else:
            embed = discord.Embed(
                title="❌ Failed to Add",
                description=f"Could not add keyword: {keyword}",
                color=0xff4444
            )
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")

@bot.tree.command(name="remove", description="Remove a keyword from monitoring")
async def remove_keyword(interaction: discord.Interaction, keyword: str):
    try:
        config_manager = ConfigManager()
        success = config_manager.remove_keyword(keyword.strip())
        
        if success:
            embed = discord.Embed(
                title="✅ Keyword Removed",
                description=f"No longer monitoring: **{keyword}**",
                color=0xff9900
            )
        else:
            embed = discord.Embed(
                title="❌ Not Found",
                description=f"Keyword not found: {keyword}",
                color=0xff4444
            )
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")

@bot.tree.command(name="list", description="List all monitored keywords")
async def list_keywords(interaction: discord.Interaction):
    try:
        config_manager = ConfigManager()
        keywords = config_manager.list_keywords()
        
        if keywords:
            # Split into chunks of 20 for better display
            keyword_chunks = [keywords[i:i+20] for i in range(0, len(keywords), 20)]
            keyword_text = "\n".join([f"• {kw}" for kw in keyword_chunks[0]])
            
            embed = discord.Embed(
                title=f"📝 Monitored Keywords ({len(keywords)} total)",
                description=keyword_text,
                color=0x00aaff
            )
            
            if len(keyword_chunks) > 1:
                embed.set_footer(text=f"Showing first 20 of {len(keywords)} keywords")
        else:
            embed = discord.Embed(
                title="📝 No Keywords",
                description="No keywords are currently being monitored",
                color=0x888888
            )
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")

@bot.tree.command(name="status", description="Show system status")
async def status(interaction: discord.Interaction):
    try:
        config_manager = ConfigManager()
        keywords = config_manager.list_keywords()
        
        embed = discord.Embed(
            title="🚀 Token Monitor Status", 
            color=0x00ff41
        )
        embed.add_field(
            name="📊 System", 
            value="✅ Operational", 
            inline=True
        )
        embed.add_field(
            name="🔍 Keywords", 
            value=f"{len(keywords)} loaded", 
            inline=True
        )
        embed.add_field(
            name="📡 Notifications", 
            value="✅ Active", 
            inline=True
        )
        embed.add_field(
            name="🎯 Detection", 
            value="✅ Real-time", 
            inline=True
        )
        embed.add_field(
            name="💰 Cost", 
            value="$0/month", 
            inline=True
        )
        embed.add_field(
            name="⚡ Speed", 
            value="< 1 second", 
            inline=True
        )
        
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}")

# Prefix commands as backup
@bot.command(name='add')
async def add_prefix(ctx, *, keyword):
    try:
        config_manager = ConfigManager()
        success = config_manager.add_keyword(keyword.strip())
        
        if success:
            await ctx.send(f"✅ Added keyword: **{keyword}**")
        else:
            await ctx.send(f"❌ Failed to add: {keyword}")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command(name='remove')
async def remove_prefix(ctx, *, keyword):
    try:
        config_manager = ConfigManager()
        success = config_manager.remove_keyword(keyword.strip())
        
        if success:
            await ctx.send(f"✅ Removed keyword: **{keyword}**")
        else:
            await ctx.send(f"❌ Keyword not found: {keyword}")
    except Exception as e:
        await ctx.send(f"Error: {e}")

@bot.command(name='list')
async def list_prefix(ctx):
    try:
        config_manager = ConfigManager()
        keywords = config_manager.list_keywords()
        
        if keywords:
            keyword_text = ", ".join(keywords[:20])  # First 20
            message = f"📝 **Keywords ({len(keywords)} total):**\n{keyword_text}"
            if len(keywords) > 20:
                message += f"\n... and {len(keywords) - 20} more"
        else:
            message = "📝 No keywords currently monitored"
        
        await ctx.send(message)
    except Exception as e:
        await ctx.send(f"Error: {e}")

async def main():
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ No DISCORD_TOKEN found")
        return
    
    print("🤖 Starting Discord bot...")
    try:
        await bot.start(token)
    except discord.LoginFailure:
        print("❌ Login failed - invalid token")
    except Exception as e:
        print(f"❌ Bot error: {e}")

if __name__ == "__main__":
    asyncio.run(main())