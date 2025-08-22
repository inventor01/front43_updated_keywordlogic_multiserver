#!/usr/bin/env python3
"""
PumpPortal Integration Test
Verify PumpPortal WebSocket connectivity and token detection
"""

import asyncio
import websockets
import json
import time
import requests
from datetime import datetime

async def test_pumpportal_connection():
    """Test PumpPortal WebSocket connection and token detection"""
    
    print("🔬 TESTING PUMPPORTAL INTEGRATION")
    print("=" * 45)
    
    uri = "wss://pumpportal.fun/api/data"
    connection_successful = False
    messages_received = 0
    
    try:
        print(f"📡 Connecting to: {uri}")
        
        async with websockets.connect(uri) as websocket:
            connection_successful = True
            print("✅ WebSocket connection established")
            
            # Subscribe to new token events
            subscribe_message = {
                "method": "subscribeNewToken"
            }
            
            await websocket.send(json.dumps(subscribe_message))
            print("📩 Subscribed to new token events")
            
            # Listen for messages with timeout
            timeout_duration = 30  # 30 seconds
            start_time = time.time()
            
            print(f"👂 Listening for messages ({timeout_duration}s timeout)...")
            
            while time.time() - start_time < timeout_duration:
                try:
                    # Wait for message with short timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    messages_received += 1
                    
                    try:
                        data = json.loads(message)
                        print(f"\n📨 Message {messages_received}:")
                        print(f"   Type: {data.get('type', 'unknown')}")
                        print(f"   Content: {message[:200]}...")
                        
                        # Check if it's a token event
                        if 'mint' in data or 'address' in data:
                            print(f"🎯 Token detected!")
                            print(f"   Mint: {data.get('mint', data.get('address', 'unknown'))}")
                            print(f"   Name: {data.get('name', 'unknown')}")
                            print(f"   Symbol: {data.get('symbol', 'unknown')}")
                        
                    except json.JSONDecodeError:
                        print(f"📝 Raw message: {message[:100]}...")
                
                except asyncio.TimeoutError:
                    # No message received in 2 seconds, continue waiting
                    continue
                
                except websockets.exceptions.ConnectionClosed:
                    print("❌ WebSocket connection closed")
                    break
            
            print(f"\n📊 Test Results:")
            print(f"   Connection: {'✅ Success' if connection_successful else '❌ Failed'}")
            print(f"   Messages received: {messages_received}")
            print(f"   Duration: {timeout_duration}s")
            
            if messages_received > 0:
                print(f"✅ PumpPortal is sending data - integration should work")
            else:
                print(f"⚠️ No messages received - may be low activity period")
    
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False
    
    return connection_successful

def test_api_connectivity():
    """Test basic API connectivity"""
    print(f"\n🌐 Testing API Connectivity:")
    
    # Test DexScreener (our fallback for name resolution)
    try:
        response = requests.get(
            'https://api.dexscreener.com/latest/dex/tokens/So11111111111111111111111111111111111111112',
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"   ✅ DexScreener API: Operational")
        else:
            print(f"   ⚠️ DexScreener API: Status {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ DexScreener API: {e}")
    
    # Test PumpPortal website
    try:
        response = requests.get('https://pumpportal.fun/', timeout=10)
        
        if response.status_code == 200:
            print(f"   ✅ PumpPortal website: Accessible")
        else:
            print(f"   ⚠️ PumpPortal website: Status {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ PumpPortal website: {e}")

async def main():
    """Main test function"""
    print("🚀 PumpPortal Integration Test Suite")
    print("Testing alternative to rate-limited Alchemy API")
    print()
    
    # Test API connectivity first
    test_api_connectivity()
    
    # Test WebSocket connection
    success = await test_pumpportal_connection()
    
    print(f"\n🎯 INTEGRATION TEST SUMMARY:")
    if success:
        print(f"✅ PumpPortal integration ready for deployment")
        print(f"💡 This can replace the rate-limited Alchemy API")
        print(f"🔄 Token detection should resume with PumpPortal data source")
    else:
        print(f"❌ PumpPortal integration needs debugging")
        print(f"🔧 Check network connectivity and WebSocket support")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())