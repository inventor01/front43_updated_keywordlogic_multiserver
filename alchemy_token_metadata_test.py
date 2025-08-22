#!/usr/bin/env python3
"""
Test Alchemy API for token metadata extraction
Check what token information Alchemy can provide
"""

import asyncio
import aiohttp
import json
import os

async def test_alchemy_token_metadata():
    """Test what token metadata Alchemy can provide"""
    
    # Recent token addresses from the logs
    test_tokens = [
        "FbC32L5EiLhqDgLHVDj4bDFLx51f8cp4JCBCX4ymbonk",  # ymbonk
        "7rs3jfcjbpKapNBo5Jjjn8Dqxu3Xw7bggBQGUDAebonk",  # Aebonk
        "2AdboqsiUB93mcWJuZYJmGceWJbnjishH3ff8pFQbonk",  # FQbonk
    ]
    
    alchemy_api_key = os.getenv('ALCHEMY_API_KEY', '877gH4oJoW0HVbh6LuJ46d8oqZJHHQ5q')
    rpc_url = f"https://solana-mainnet.g.alchemy.com/v2/{alchemy_api_key}"
    
    async with aiohttp.ClientSession() as session:
        for token_address in test_tokens:
            print(f"\n=== Testing Token: {token_address[:10]}... ===")
            
            # Method 1: Get Token Account Info
            payload1 = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [
                    token_address,
                    {"encoding": "jsonParsed"}
                ]
            }
            
            try:
                async with session.post(rpc_url, json=payload1) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'result' in data and data['result'] and 'value' in data['result']:
                            account_data = data['result']['value']
                            if account_data and 'data' in account_data:
                                parsed_data = account_data['data']
                                print(f"Account Info: {json.dumps(parsed_data, indent=2)}")
                            else:
                                print("No account data found")
                        else:
                            print("No account info available")
                    else:
                        print(f"HTTP Error: {response.status}")
            except Exception as e:
                print(f"Error getting account info: {e}")
            
            # Method 2: Get Token Supply (for SPL tokens)
            payload2 = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "getTokenSupply",
                "params": [token_address]
            }
            
            try:
                async with session.post(rpc_url, json=payload2) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"Token Supply: {json.dumps(data, indent=2)}")
                    else:
                        print(f"Supply HTTP Error: {response.status}")
            except Exception as e:
                print(f"Error getting token supply: {e}")
                
            # Method 3: Get Multiple Accounts (batch)
            payload3 = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "getMultipleAccounts",
                "params": [
                    [token_address],
                    {"encoding": "jsonParsed"}
                ]
            }
            
            try:
                async with session.post(rpc_url, json=payload3) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"Multiple Accounts: {json.dumps(data, indent=2)}")
                    else:
                        print(f"Multiple Accounts HTTP Error: {response.status}")
            except Exception as e:
                print(f"Error getting multiple accounts: {e}")

if __name__ == "__main__":
    asyncio.run(test_alchemy_token_metadata())