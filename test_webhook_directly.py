#!/usr/bin/env python3
import requests
import json
import time

# Test webhook notification directly
webhook_url = 'https://discord.com/api/webhooks/1390545562746490971/zODF3Er5XaSykD6Jl5IkxKiNqr_ArUCzj0DeH8PaDybGD1fXKKg3vr9xsxt_2jPti9yJ'

embed = {
    'title': '🚀 NEW TOKEN MATCH: Test Bonk Token',
    'color': 0x00ff41,
    'fields': [
        {'name': '🎯 Keyword Match', 'value': '**bonk**', 'inline': True},
        {'name': '📍 Token Address', 'value': '`TEST123bonk`', 'inline': False},
        {'name': '🔗 Quick Links', 'value': '[DexScreener](https://dexscreener.com/solana/TEST123) • [Solscan](https://solscan.io/token/TEST123) • [Jupiter](https://jup.ag/swap/SOL-TEST123)', 'inline': False}
    ],
    'footer': {'text': 'Token Monitor System • Webhook Active'},
    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
}

payload = {
    'embeds': [embed],
    'content': '🎯 **Discord Bot is now ACTIVE!** Webhook notifications working perfectly.'
}

response = requests.post(webhook_url, json=payload)
print(f'Webhook status: {response.status_code}')
if response.status_code == 204:
    print('✅ SUCCESS: Discord bot is ACTIVE via webhook!')
    print('✅ Ready to send notifications for keyword matches')
else:
    print(f'❌ Failed: {response.text}')