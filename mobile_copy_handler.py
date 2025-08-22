#!/usr/bin/env python3
"""
Mobile Copy Handler - Optimized Discord formatting for mobile contract address copying
"""

def create_mobile_optimized_notification(token_data: dict) -> dict:
    """Create Discord embed optimized for mobile address copying"""
    
    name = token_data.get('name', 'Unknown Token')
    symbol = token_data.get('symbol', 'UNK')
    address = token_data.get('address', '')
    age_display = token_data.get('age_display', 'Unknown')
    
    # Platform detection
    if address.endswith('pump'):
        emoji = '🔵'
        color = 0x1E90FF  # Blue for Pump.fun
    elif address.endswith('bonk'):
        emoji = '🟠'  
        color = 0xFF8C00  # Orange for LetsBonk
    else:
        emoji = '⚪'
        color = 0x808080  # Gray for others
    
    # Create mobile-optimized embed structure
    embed_data = {
        "title": f"{emoji} NEW TOKEN DETECTED",
        "description": f"**{name}** ({symbol})",
        "color": color,
        "fields": [
            {
                "name": "📊 Token Info",
                "value": f"**Name:** {name}\n**Symbol:** {symbol}\n**Age:** {age_display}",
                "inline": True
            },
            {
                "name": "📱 Contract Address",
                "value": f"**Long-press this line to copy:**\n{address}",
                "inline": False
            },
            {
                "name": "💡 Mobile Copy Tips",
                "value": "• Long-press the address above\n• Select 'Copy' from menu\n• Address copied to clipboard!",
                "inline": False
            }
        ]
    }
    
    return embed_data

def format_for_mobile_selection(address: str, token_name: str) -> str:
    """Format address string for optimal mobile selection"""
    
    # Create multiple format options for different mobile behaviors
    formats = {
        'plain': address,
        'spaced': f" {address} ",
        'line_breaks': f"\n{address}\n",
        'with_label': f"Address: {address}",
        'isolated': f"Copy this → {address} ← Copy this"
    }
    
    # Return the most mobile-friendly format
    return formats['plain']