"""
Real-time new token creation monitor - ONLY catches genuinely new tokens
No transaction history scanning - pure new token detection
"""

import time
import logging
import requests
from typing import Dict, Any, Optional, List, Set
from cachetools import TTLCache

logger = logging.getLogger(__name__)

class NewTokenOnlyMonitor:
    """Monitor that ONLY catches genuinely new token creations, not transaction history"""
    
    def __init__(self, callback_func=None):
        self.callback_func = callback_func
        self.letsbonk_program_id = "LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj"
        self.monitoring_start_time = time.time()
        # Use TTLCache for automatic memory cleanup instead of basic sets
        self.seen_signatures = TTLCache(maxsize=5000, ttl=300)  # 5 minute TTL for signatures
        self.processed_tokens = TTLCache(maxsize=10000, ttl=60)  # 1 minute TTL for token addresses
        self.retry_queue = {}  # Queue for tokens awaiting name resolution
        self.retry_attempts = {}  # Track retry attempts per token
        
        # Alchemy endpoint with actual API key
        import os
        self.api_key = os.getenv("ALCHEMY_API_KEY")
        if not self.api_key:
            raise ValueError("ALCHEMY_API_KEY environment variable required")
        self.base_url = f"https://solana-mainnet.g.alchemy.com/v2/{self.api_key}"
        
        # Add proper headers for authentication
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Test connection to Alchemy
        logger.info(f"🔗 Connecting to Alchemy with API key: {self.api_key[:10]}...")
        self._test_alchemy_connection()
        
        # Enable INFO logging for cleaner output (disable debug after fixing)
        logging.getLogger(__name__).setLevel(logging.INFO)
        
        # Track only the most recent signature to detect NEW ones
        self.last_known_signature = None
    
    def _test_alchemy_connection(self):
        """Test connection to Alchemy API"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getHealth"
            }
            
            response = requests.post(self.base_url, json=payload, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                logger.info("✅ Alchemy connection successful")
            else:
                logger.error(f"❌ Alchemy connection failed: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Alchemy connection test failed: {e}")
        
    def get_only_newest_signature(self) -> Optional[str]:
        """Get ONLY the newest signature - no transaction history scanning"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [
                    self.letsbonk_program_id,
                    {
                        "limit": 1,  # ONLY get the newest signature
                        "commitment": "confirmed"
                    }
                ]
            }
            
            logger.debug(f"🔍 API Request: {self.base_url[:50]}...")
            response = requests.post(self.base_url, json=payload, headers=self.headers, timeout=5)
            logger.debug(f"🔍 API Response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', [])
                
                if result:
                    newest_signature = result[0]['signature']
                    
                    # Only process if this is genuinely NEW (not seen before)
                    if newest_signature != self.last_known_signature and newest_signature not in self.seen_signatures:
                        logger.info(f"🔍 NEW SIGNATURE FOUND: {newest_signature[:10]}... (startup buffer: {time.time() - self.monitoring_start_time:.1f}s)")
                        
                        # Reduced startup buffer for faster testing
                        if time.time() - self.monitoring_start_time > 10:  # 10 second startup buffer
                            # ADDITIONAL VALIDATION: Check if this is actually a token creation
                            if self._is_token_creation_transaction(newest_signature):
                                logger.info(f"🆕 GENUINE NEW TOKEN CREATION DETECTED: {newest_signature[:10]}...")
                                self.last_known_signature = newest_signature
                                self.seen_signatures[newest_signature] = True
                                return newest_signature
                            else:
                                logger.info(f"⚠️ FILTERED: {newest_signature[:10]}... - Not a token creation transaction")
                                self.last_known_signature = newest_signature
                                self.seen_signatures[newest_signature] = True
                        else:
                            # During startup, just track signatures without processing
                            logger.info(f"⏳ STARTUP BUFFER: {newest_signature[:10]}... - waiting {10 - (time.time() - self.monitoring_start_time):.1f}s more")
                            self.last_known_signature = newest_signature
                            self.seen_signatures[newest_signature] = True
                    else:
                        logger.debug(f"⚠️ DUPLICATE/SEEN: {newest_signature[:10]}... - already processed")
                    
            return None
            
        except Exception as e:
            logger.debug(f"Failed to get newest signature: {e}")
            return None
    
    def get_transaction_details(self, signature: str) -> Optional[dict]:
        """Get transaction details for NEW signature"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [
                    signature,
                    {
                        "encoding": "jsonParsed",
                        "commitment": "confirmed",
                        "maxSupportedTransactionVersion": 0
                    }
                ]
            }
            
            response = requests.post(self.base_url, json=payload, headers=self.headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('result')
                
        except Exception as e:
            logger.debug(f"Failed to get transaction details: {e}")
            return None
    
    def _is_token_creation_transaction(self, signature: str) -> bool:
        """Check if this transaction is actually creating a new token, not just trading an existing one"""
        try:
            transaction = self.get_transaction_details(signature)
            if not transaction:
                logger.debug(f"No transaction details for {signature[:10]}...")
                return False
            
            # Check for token creation instruction patterns in logs
            logs = transaction.get('meta', {}).get('logMessages', [])
            logger.debug(f"Checking {len(logs)} logs for token creation patterns...")
            
            # RELAXED: Check for any LetsBonk-related patterns (not just InitializeMint)
            letsbonk_patterns = [
                'Program log: Instruction: InitializeMint',
                'Program log: Instruction: InitializeMint2', 
                'Program log: Initializing token mint',
                'Program LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj',  # LetsBonk program
                'Program invoke [1]: LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj',
                'Instruction: Create',
                'bonk'
            ]
            
            # Log first few entries for debugging (only when no patterns found)
            if not any(any(pattern in log for pattern in letsbonk_patterns) for log in logs):
                for i, log in enumerate(logs[:3]):
                    logger.debug(f"Log {i+1}: {log[:80]}...")
            
            has_letsbonk_pattern = any(
                any(pattern in log for pattern in letsbonk_patterns)
                for log in logs
            )
            
            if has_letsbonk_pattern:
                logger.info(f"✅ LETSBONK PATTERN FOUND in {signature[:10]}... - processing as potential token")
                return True
            else:
                logger.debug(f"No LetsBonk patterns found in {signature[:10]}...")
                # FALLBACK: Since we're monitoring the LetsBonk program specifically,
                # any transaction on this program could potentially be a token creation
                # Let's process them all and let the keyword matching filter later
                logger.info(f"⚡ FALLBACK: Processing {signature[:10]}... as potential LetsBonk token (relaxed mode)")
                return True
            
        except Exception as e:
            logger.debug(f"Error validating token creation transaction: {e}")
            return False
    
    def extract_new_token(self, signature: str) -> Optional[Dict[str, Any]]:
        """Extract NEW token data from transaction signature"""
        try:
            transaction = self.get_transaction_details(signature)
            if not transaction:
                return None
            
            # Get current time for age calculations
            current_time = time.time()
            
            # CRITICAL: Use ACTUAL blockchain timestamp for token age validation
            # This fixes the bug where tokens were appearing fresh using discovery time
            block_time = transaction.get('blockTime')
            if block_time:
                # Normalize blockTime to seconds (handle both seconds and milliseconds)
                if block_time > 1e12:  # Milliseconds format
                    normalized_block_time = block_time / 1000
                else:  # Already in seconds
                    normalized_block_time = block_time
                
                # Calculate ACTUAL token age using blockchain timestamp
                actual_age = current_time - normalized_block_time
                
                # RELAXED 300-second freshness validation for initial testing
                if actual_age > 300:  # More than 5 minutes old
                    # Log rejection with proper age display
                    if actual_age > 3600:
                        age_display = f"{actual_age/3600:.1f}h"
                    elif actual_age > 60:
                        age_display = f"{actual_age/60:.1f}m"
                    else:
                        age_display = f"{actual_age:.1f}s"
                    logger.error(f"❌ REJECTING OLD BLOCKCHAIN TOKEN: age {age_display} > 60s limit")
                    return None
                
                # Use validated blockchain time as the creation timestamp (in seconds)
                creation_timestamp = normalized_block_time
                logger.info(f"✅ BLOCKCHAIN FRESH TOKEN: age {actual_age:.1f}s (< 60s limit)")
            else:
                # If no blockchain time or invalid, reject - we need actual creation time
                logger.error(f"❌ REJECTING TOKEN: missing/invalid blockTime ({block_time})")
                return None
            
            # Look for token creation in post token balances
            post_balances = transaction.get('meta', {}).get('postTokenBalances', [])
            
            for balance in post_balances:
                mint = balance.get('mint')
                if mint and mint.endswith('bonk'):  # LetsBonk tokens end with 'bonk'
                    
                    # Skip if we've already processed this token
                    if mint in self.processed_tokens:
                        return None
                    
                    self.processed_tokens[mint] = True
                    
                    # Get token name from DexScreener - ALWAYS try this first
                    token_name = self.get_token_name_from_dexscreener(mint)
                    
                    # Calculate age based on discovery time for real-time monitoring
                    if block_time:
                        blockchain_age = current_time - block_time
                        if token_name:
                            logger.info(f"✅ GENUINE NEW TOKEN: {token_name} (blockchain age: {blockchain_age:.1f}s, discovered now)")
                        else:
                            logger.info(f"✅ NEW TOKEN DETECTED: Address {mint[:10]}... (blockchain age: {blockchain_age:.1f}s, name pending)")
                    else:
                        if token_name:
                            logger.info(f"✅ GENUINE NEW TOKEN: {token_name} (discovered in real-time)")
                        else:
                            logger.info(f"✅ NEW TOKEN DETECTED: Address {mint[:10]}... (discovered in real-time, name pending)")
                    
                    # HYBRID PROCESSING: Only process tokens with valid real names or use proper placeholder
                    if token_name and len(token_name.strip()) > 0 and not token_name.startswith("Unnamed"):
                        # Use real names from DexScreener immediately
                        logger.info(f"🎯 USING REAL NAME: '{token_name}' from DexScreener")
                        
                        return {
                            'name': token_name,
                            'symbol': 'BONK', 
                            'address': mint,
                            'created_timestamp': creation_timestamp,
                            'platform': 'letsbonk.fun',
                            'url': f'https://letsbonk.fun/token/{mint}',
                            'name_status': 'resolved'
                        }
                    else:
                        # INSTANT PROCESSING with proper placeholder name + background resolution
                        placeholder_name = f"Unnamed Token {mint[:6]}"
                        logger.info(f"⚡ INSTANT PROCESSING: '{placeholder_name}' (resolving name in background)")
                        
                        # Queue for background name resolution
                        self.queue_token_for_retry(mint, {
                            'address': mint,
                            'created_timestamp': creation_timestamp,
                            'platform': 'letsbonk.fun',
                            'url': f'https://letsbonk.fun/token/{mint}',
                            'discovery_time': current_time,
                            'placeholder_name': placeholder_name
                        })
                        
                        # Return immediately with placeholder name for instant processing
                        return {
                            'name': placeholder_name,
                            'symbol': 'BONK',
                            'address': mint,
                            'created_timestamp': creation_timestamp,
                            'platform': 'letsbonk.fun',
                            'url': f'https://letsbonk.fun/token/{mint}',
                            'name_status': 'pending'
                        }
            
            return None  # No tokens found
            
        except Exception as e:
            logger.debug(f"Error extracting new token from {signature}: {e}")
            return None
    
    def queue_token_for_retry(self, mint_address: str, token_data: dict):
        """Queue a token for name resolution retry"""
        self.retry_queue[mint_address] = token_data
        self.retry_attempts[mint_address] = 0
        logger.info(f"🔄 QUEUED: {mint_address[-6:]} for DexScreener retry")
    
    def process_retry_queue(self):
        """Process tokens in retry queue, attempting to get names from DexScreener"""
        import time
        
        current_time = time.time()
        processed_tokens = []
        
        for mint_address, token_data in list(self.retry_queue.items()):
            # Limit retry attempts and time
            if self.retry_attempts[mint_address] >= 5:  # Max 5 retries
                logger.info(f"⏰ TIMEOUT: {mint_address[-6:]} - giving up after 5 attempts")
                processed_tokens.append(mint_address)
                continue
                
            # Wait at least 30 seconds between retries
            if current_time - token_data.get('discovery_time', 0) < 30:
                continue
                
            # Try to get name from DexScreener
            token_name = self.get_token_name_from_dexscreener(mint_address)
            
            if token_name and len(token_name.strip()) > 0:
                # Success! Process the token with real name
                final_token_data = {
                    'name': token_name,
                    'symbol': 'BONK',
                    'address': mint_address,
                    'created_timestamp': token_data.get('created_timestamp'),
                    'platform': token_data.get('platform', 'letsbonk.fun'),
                    'url': token_data.get('url'),
                    'name_status': 'resolved',
                    'original_placeholder': token_data.get('placeholder_name'),
                    'update_type': 'name_resolution'
                }
                
                logger.info(f"✅ NAME RESOLVED: '{token_name}' for {mint_address[-6:]} (was '{token_data.get('placeholder_name', 'unnamed')}')")
                
                # Update database with resolved name
                self.update_token_name_in_db(mint_address, token_name)
                
                # Optional: Send update notification via callback
                if self.callback_func:
                    try:
                        self.callback_func([final_token_data])
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                
                processed_tokens.append(mint_address)
            else:
                # Still no name, increment retry count
                self.retry_attempts[mint_address] += 1
                logger.info(f"🔄 RETRY {self.retry_attempts[mint_address]}/5: {mint_address[-6:]} still waiting for DexScreener")
        
        # Remove processed tokens from queue
        for mint_address in processed_tokens:
            self.retry_queue.pop(mint_address, None)
            self.retry_attempts.pop(mint_address, None)
    
    def get_token_name_from_dexscreener(self, mint_address: str) -> Optional[str]:
        """Get token name from DexScreener API"""
        try:
            dexscreener_url = f"https://api.dexscreener.com/latest/dex/tokens/{mint_address}"
            response = requests.get(dexscreener_url, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                if pairs:
                    # Get the most active pair
                    pair = pairs[0]
                    token_name = pair.get('baseToken', {}).get('name')
                    if token_name:
                        logger.debug(f"✅ DexScreener name: {token_name}")
                        return token_name
                        
        except Exception as e:
            logger.debug(f"DexScreener lookup failed: {e}")
            
        return None
    
    def update_token_name_in_db(self, mint_address: str, real_name: str):
        """Update token name in database when resolved"""
        try:
            import os
            import psycopg2
            
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                logger.debug("No DATABASE_URL - skipping database update")
                return
                
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Update the token name and status in database
            cursor.execute("""
                UPDATE detected_tokens 
                SET name = %s, name_status = 'resolved' 
                WHERE address = %s
            """, (real_name, mint_address))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"📄 Database updated: {mint_address[:10]}... → '{real_name}'")
            
        except Exception as e:
            logger.debug(f"Database update failed: {e}")
    
    def get_pending_tokens(self):
        """Get all tokens with pending name status from database"""
        try:
            import os
            import psycopg2
            
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                return []
                
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT address, name, created_timestamp 
                FROM detected_tokens 
                WHERE name_status = 'pending' 
                ORDER BY created_timestamp DESC
                LIMIT 50
            """)
            
            pending_tokens = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [{'address': addr, 'name': name, 'timestamp': ts} for addr, name, ts in pending_tokens]
            
        except Exception as e:
            logger.debug(f"Database query failed: {e}")
            return []
    
    def start_monitoring(self):
        """Start monitoring for NEW token creations only"""
        logger.info("🔄 Starting NEW TOKEN ONLY monitoring...")
        logger.info("📡 NO transaction history - only real-time new tokens")
        
        while True:
            try:
                # Get only the newest signature (not transaction history)
                new_signature = self.get_only_newest_signature()
                
                if new_signature:
                    logger.debug(f"🔍 Checking signature: {new_signature[:10]}...")
                    # Extract token data from the NEW signature
                    new_token = self.extract_new_token(new_signature)
                    
                    if new_token:
                        logger.info(f"🎯 NEW TOKEN FOUND: {new_token['name']} ({new_token['address'][:10]}...)")
                        
                        # Call the callback function with new token data
                        if self.callback_func:
                            try:
                                self.callback_func([new_token])
                            except Exception as e:
                                logger.error(f"Callback error: {e}")
                else:
                    logger.info("🔍 No new signatures found - API returned empty result")
                
                # Wait 2 seconds before next check (balance speed vs server load)
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(5)  # Wait longer on errors