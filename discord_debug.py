#!/usr/bin/env python3
"""
Discord Token Debug Helper
"""
import os

def check_discord_token():
    """Check Discord token format and provide help"""
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        print("❌ DISCORD_TOKEN not found in environment")
        return
        
    print("🔍 DISCORD TOKEN ANALYSIS:")
    print(f"   Length: {len(token)} characters")
    print(f"   First 20 chars: {token[:20]}...")
    print(f"   Last 10 chars: ...{token[-10:]}")
    print(f"   Number of dots: {token.count('.')}")
    
    if token.count('.') == 2:
        parts = token.split('.')
        print(f"   Part 1 (Bot ID): {len(parts[0])} chars - {parts[0][:10]}...")
        print(f"   Part 2 (Timestamp): {len(parts[1])} chars - {parts[1]}")
        print(f"   Part 3 (HMAC): {len(parts[2])} chars - {parts[2][:10]}...")
    
    print("\n🔧 TROUBLESHOOTING STEPS:")
    print("1. Go to https://discord.com/developers/applications")
    print("2. Select your bot application")  
    print("3. Go to 'Bot' tab on left sidebar")
    print("4. Under 'Token' section, click 'Reset Token'")
    print("5. Copy the NEW token (starts with 'MT' usually)")
    print("6. Paste it in Replit Secrets as DISCORD_TOKEN")
    print("\n⚠️ IMPORTANT: Token must be from 'Bot' section, not 'OAuth2'!")
    print("⚠️ Make sure bot is not disabled in Discord Developer Portal")

if __name__ == "__main__":
    check_discord_token()