#!/usr/bin/env python3
"""
LetsBonk Token Monitor
Dedicated monitoring for LetsBonk platform tokens using Solana WebSocket subscriptions
"""

import asyncio
import websockets
import json
import logging
import time
import psycopg2
import os
import requests
from datetime import datetime
from typing import Dict, Optional
from solana.rpc.websocket_api import connect
from solana.rpc.commitment import Confirmed
from solders.pubkey import Pubkey

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LetsBonkMonitor:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway')
        self.helius_rpc = "https://mainnet.helius-rpc.com/?api-key=demo-key"
        self.letsbonk_program_id = "BondingCurveProgramId"  # Replace with actual LetsBonk program ID
        self.running = False
        self.processed_signatures = set()
        
    def get_db_connection(self):
        try:
            return psycopg2.connect(self.database_url)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    async def start_monitoring(self):
        """Start monitoring LetsBonk tokens via periodic scanning"""
        logger.info("🟠 Starting LetsBonk token monitor (DexScreener + API scanning)")
        
        while True:
            try:
                # Use periodic polling instead of WebSocket to avoid rate limits
                await self.poll_letsbonk_tokens()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"LetsBonk monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def monitor_letsbonk_via_api(self):
        """Monitor LetsBonk tokens using API calls instead of WebSocket"""
        try:
            logger.info("🟠 Scanning for new LetsBonk tokens via API")
            
            # Check multiple sources for LetsBonk tokens
            await self.scan_dexscreener_for_bonk_tokens()
            await self.check_recent_solana_tokens()
            
        except Exception as e:
            logger.error(f"API monitoring failed: {e}")
            
    async def poll_letsbonk_tokens(self):
        """Poll for new LetsBonk tokens using API/RPC calls"""
        try:
            # Method 1: Check recent transactions on Solana
            await self.check_recent_transactions()
            
            # Method 2: Use DexScreener to find new tokens with 'bonk' addresses
            await self.scan_dexscreener_for_bonk_tokens()
            
        except Exception as e:
            logger.error(f"Polling error: {e}")
    
    async def check_recent_transactions(self):
        """Check recent Solana transactions for LetsBonk token creations"""
        try:
            # Get recent signatures from Solana RPC
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [
                    "11111111111111111111111111111112",  # System program
                    {"limit": 100}
                ]
            }
            
            response = requests.post(self.helius_rpc, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                signatures = data.get('result', [])
                
                for sig_info in signatures[:20]:  # Check latest 20
                    signature = sig_info.get('signature')
                    if signature and signature not in self.processed_signatures:
                        await self.analyze_transaction(signature)
                        self.processed_signatures.add(signature)
                        
                        # Keep only recent signatures to prevent memory growth
                        if len(self.processed_signatures) > 1000:
                            self.processed_signatures = set(list(self.processed_signatures)[-500:])
                            
        except Exception as e:
            logger.debug(f"Transaction check error: {e}")
    
    async def scan_dexscreener_for_bonk_tokens(self):
        """Scan DexScreener for recently created tokens with 'bonk' addresses"""
        try:
            # Get latest Solana tokens from DexScreener
            url = "https://api.dexscreener.com/latest/dex/tokens/solana"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                for pair in pairs[:50]:  # Check latest 50 pairs
                    token_address = pair.get('baseToken', {}).get('address', '')
                    
                    if token_address.endswith('bonk'):
                        # Found a LetsBonk token!
                        await self.process_letsbonk_token(pair)
                        
        except Exception as e:
            logger.debug(f"DexScreener scan error: {e}")
    
    async def analyze_transaction(self, signature: str):
        """Analyze a transaction to see if it's a LetsBonk token creation"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [
                    signature,
                    {"encoding": "json", "maxSupportedTransactionVersion": 0}
                ]
            }
            
            response = requests.post(self.helius_rpc, json=payload, timeout=5)
            if response.status_code == 200:
                data = response.json()
                transaction = data.get('result')
                
                if transaction:
                    # Look for token creation patterns
                    instructions = transaction.get('transaction', {}).get('message', {}).get('instructions', [])
                    
                    for instruction in instructions:
                        # Check if this might be a token creation
                        if self.is_token_creation_instruction(instruction):
                            await self.extract_token_from_transaction(transaction)
                            
        except Exception as e:
            logger.debug(f"Transaction analysis error: {e}")
    
    def is_token_creation_instruction(self, instruction):
        """Check if instruction looks like token creation"""
        # This is a simplified check - would need actual LetsBonk program analysis
        program_id = instruction.get('programId', '')
        data = instruction.get('data', '')
        
        # Look for token creation patterns
        return 'token' in data.lower() or 'mint' in data.lower()
    
    async def extract_token_from_transaction(self, transaction):
        """Extract token information from transaction"""
        try:
            # This would need proper transaction parsing
            # For now, we'll use the hybrid scanning approach
            pass
        except Exception as e:
            logger.debug(f"Token extraction error: {e}")
    
    async def process_letsbonk_token(self, pair_data):
        """Process a discovered LetsBonk token"""
        try:
            token_address = pair_data.get('baseToken', {}).get('address', '')
            token_name = pair_data.get('baseToken', {}).get('name', 'Unknown')
            token_symbol = pair_data.get('baseToken', {}).get('symbol', '')
            
            if not token_address or not token_address.endswith('bonk'):
                return
            
            # Check if we already have this token
            conn = self.get_db_connection()
            if not conn:
                return
                
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM detected_tokens WHERE address = %s", (token_address,))
            
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return  # Already processed
            
            # Insert new LetsBonk token
            cursor.execute("""
                INSERT INTO detected_tokens (address, name, symbol, created_at, name_status, status, data_source, platform)
                VALUES (%s, %s, %s, %s, 'resolved', 'detected', 'letsbonk_monitor', 'LetsBonk')
                ON CONFLICT (address) DO NOTHING
            """, (token_address, token_name, token_symbol, datetime.now()))
            
            if cursor.rowcount > 0:
                logger.info(f"🟠 NEW LETSBONK TOKEN: {token_name} ({token_address})")
                
                # Trigger keyword matching (import from main system)
                try:
                    from integrated_monitoring_system import IntegratedTokenMonitor
                    monitor = IntegratedTokenMonitor()
                    matches = monitor.check_keyword_matches(token_name, token_address)
                    
                    if matches:
                        logger.info(f"🟠 LetsBonk keyword matches found: {len(matches)}")
                        await monitor.process_keyword_matches(matches)
                        
                except Exception as e:
                    logger.error(f"Keyword matching error: {e}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"LetsBonk token processing error: {e}")

async def main():
    """Main entry point for LetsBonk monitoring"""
    monitor = LetsBonkMonitor()
    
    logger.info("🟠 LetsBonk Monitor Starting...")
    logger.info("📡 Monitoring for LetsBonk tokens (addresses ending in 'bonk')")
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("🟠 LetsBonk monitor stopped")
    except Exception as e:
        logger.error(f"Monitor error: {e}")

if __name__ == "__main__":
    asyncio.run(main())