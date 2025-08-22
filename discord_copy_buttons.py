#!/usr/bin/env python3
"""
Discord Copy Buttons Implementation
Creates interactive Discord buttons for one-tap contract address copying
"""

import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class CopyAddressView(discord.ui.View):
    """Discord View with copy button for contract addresses"""
    
    def __init__(self, contract_address: str, token_name: str):
        super().__init__(timeout=300)  # 5 minute timeout
        self.contract_address = contract_address
        self.token_name = token_name
        
        # Add copy button with address preview
        copy_button = discord.ui.Button(
            label=f"📋 Copy {contract_address[:8]}...{contract_address[-6:]}",
            style=discord.ButtonStyle.primary,
            custom_id=f"copy_{contract_address[:8]}"
        )
        copy_button.callback = self.copy_address_callback
        self.add_item(copy_button)
        
        # Add view on explorer button
        explorer_button = discord.ui.Button(
            label="🔍 View on Solscan",
            style=discord.ButtonStyle.link,
            url=f"https://solscan.io/token/{contract_address}"
        )
        self.add_item(explorer_button)
    
    async def copy_address_callback(self, interaction: discord.Interaction):
        """Handle copy button click - shows full address for easy selection"""
        try:
            # Create ephemeral response with selectable address
            embed = discord.Embed(
                title="📋 Contract Address Ready to Copy",
                description=f"**{self.token_name}**",
                color=0x00ff00
            )
            
            # Add the address in a copyable format
            embed.add_field(
                name="Tap and hold the address below to copy:",
                value=f"`{self.contract_address}`",
                inline=False
            )
            
            embed.add_field(
                name="📱 Instructions:",
                value="1. Long-press the address above\n2. Select 'Copy'\n3. Address copied to clipboard!",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in copy button callback: {e}")
            # Fallback response
            await interaction.response.send_message(
                f"**Copy this address:**\n`{self.contract_address}`", 
                ephemeral=True
            )

def create_notification_with_copy_button(token_data: dict) -> tuple[discord.Embed, CopyAddressView]:
    """Create Discord notification with interactive copy button"""
    
    name = token_data.get('name', 'Unknown Token')
    symbol = token_data.get('symbol', 'UNK')
    address = token_data.get('address', '')
    age_display = token_data.get('age_display', 'Unknown')
    
    # Detect platform for styling
    if address.endswith('pump'):
        emoji = '🔵'
        color = 0x1E90FF  # Blue for Pump.fun
    elif address.endswith('bonk'):
        emoji = '🟠'  
        color = 0xFF8C00  # Orange for LetsBonk
    else:
        emoji = '⚪'
        color = 0x808080  # Gray for others
    
    # Create main embed
    embed = discord.Embed(
        title=f"{emoji} NEW TOKEN DETECTED",
        description=f"**{name}** ({symbol})",
        color=color,
        timestamp=discord.utils.utcnow()
    )
    
    # Token info field
    embed.add_field(
        name="📊 Token Info",
        value=f"**Name:** {name}\n**Symbol:** {symbol}\n**Age:** {age_display}",
        inline=True
    )
    
    # Contract preview (shortened)
    embed.add_field(
        name="📋 Contract",
        value=f"`{address[:12]}...{address[-12:]}`\n*Tap button below to copy full address*",
        inline=False
    )
    
    # Create interactive view with copy button
    view = CopyAddressView(address, name)
    
    return embed, view