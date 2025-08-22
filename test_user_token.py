#!/usr/bin/env python3
"""
Test the token provided by user
"""

import requests

def test_user_token():
    # User provided token
    token = "MTM4OTY1Nzg5MDgzNDM1MDE0MA.GvzFGn.A1NpdkeKYWd4fIliZOtpiMYR3ff-B9OblcM2Gk"
    
    print(f"🔑 Testing user-provided token: {token[:30]}...{token[-10:]}")
    
    headers = {
        'Authorization': f'Bot {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get('https://discord.com/api/users/@me', headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Token is VALID!")
            print(f"🤖 Bot Name: {data.get('username')}#{data.get('discriminator')}")
            print(f"🆔 Bot ID: {data.get('id')}")
            return True
        else:
            print(f"❌ Token is INVALID - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing token: {e}")
        return False

if __name__ == "__main__":
    test_user_token()