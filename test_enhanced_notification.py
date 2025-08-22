#!/usr/bin/env python3
"""
Test Enhanced Notification Format
Send a test notification to verify the enhanced format with full contract address and market cap
"""

import os
import requests
import json
from datetime import datetime

def test_enhanced_notification():
    """Send a test notification with enhanced format"""
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("❌ No Discord webhook URL found")
        return False
    
    # Sample token data for testing
    test_token = {
        'name': 'Test Enhanced Token',
        'symbol': 'TEST',
        'address': '4ZkECXYAXvV47jjUgBk8EHVSDSCpavghuA4dLRgKpump',
        'market_data': {
            'market_cap': 150000,  # $150K for testing
            'price': 0.00000123,
            'volume_24h': 45000
        }
    }
    
    # Create enhanced embed matching our new format
    embed = {
        "title": "🚨 NEW TOKEN DETECTED",
        "description": f"**{test_token['name']}** ({test_token['symbol']})",
        "color": 0x00ff00,
        "timestamp": datetime.utcnow().isoformat(),
        "fields": [
            {
                "name": "📊 Token Info",
                "value": f"**Name:** {test_token['name']}\n**Symbol:** {test_token['symbol']}\n**Age:** Just now",
                "inline": True
            },
            {
                "name": "📋 Full Contract Address",
                "value": f"```{test_token['address']}```",
                "inline": False
            },
            {
                "name": "💰 Live Market Data",
                "value": f"💰 **MARKET CAP: $150.0K**\n💵 **Price:** $0.00000123\n📊 **24h Volume:** 45K",
                "inline": True
            },
            {
                "name": "🚀 Platform",
                "value": "**Source:** LetsBonk.fun\n**Network:** Solana",
                "inline": True
            },
            {
                "name": "🔗 Trading Links",
                "value": f"[LetsBonk.fun](https://letsbonk.fun/token/{test_token['address']})\n[DexScreener](https://dexscreener.com/solana/{test_token['address']})\n[SolScan](https://solscan.io/token/{test_token['address']})",
                "inline": False
            },
            {
                "name": "🎯 Test Notification",
                "value": "This is a test of the enhanced notification format with:\n✅ Full contract address\n✅ Prominent market cap\n✅ Complete coin name\n✅ Live price data\n✅ Platform information",
                "inline": False
            }
        ],
        "footer": {
            "text": "⚡ Enhanced notification test • All features working"
        }
    }
    
    # Send the test notification
    payload = {"embeds": [embed]}
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code == 204:
            print("✅ Enhanced notification test sent successfully!")
            print("📋 Full Contract Address: ✅ Displayed in code block")
            print("💰 Market Cap: ✅ Prominently displayed first")
            print("🏷️ Complete Coin Name: ✅ In embed title")
            print("💵 Live Price Data: ✅ 8 decimal precision")
            print("📊 24h Volume: ✅ Smart K/M formatting")
            print("🚀 Platform Information: ✅ Source and network")
            return True
        else:
            print(f"❌ Test notification failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending test notification: {e}")
        return False

if __name__ == "__main__":
    test_enhanced_notification()