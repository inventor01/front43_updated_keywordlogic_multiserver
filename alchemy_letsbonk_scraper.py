"""
Alchemy API-based LetsBonk token scraper
Replaces expensive Helius API with free Alchemy (300M requests/month)
"""

import requests
import time
import json
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class AlchemyLetsBonkScraper:
    """Cost-effective LetsBonk scraper using Alchemy's free tier"""
    
    def __init__(self):
        self.api_key = os.getenv("ALCHEMY_API_KEY")
        if not self.api_key:
            raise ValueError("ALCHEMY_API_KEY environment variable required")
        
        self.base_url = f"https://solana-mainnet.g.alchemy.com/v2/{self.api_key}"
        self.letsbonk_program_id = "LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj"
        
        # Ultra-fast rate limiting for maximum speed
        self.last_request_time = 0
        self.min_request_interval = 0.05  # 50ms between requests (20 requests/second)
        
        # Caching to reduce API calls
        self.processed_signatures = {}
        self.metadata_cache = {}
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Alchemy-Token-Monitor/1.0'
        })
        
        logger.info("🔄 Initialized Alchemy LetsBonk scraper (FREE tier - 300M requests/month)")
    
    def _rate_limit(self):
        """Conservative rate limiting for Alchemy free tier"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def _make_rpc_call(self, method: str, params: list) -> Optional[dict]:
        """Make RPC call to Alchemy with error handling"""
        try:
            self._rate_limit()
            
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params
            }
            
            response = self.session.post(self.base_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data:
                    return data['result']
                else:
                    logger.debug(f"Alchemy RPC error: {data.get('error', 'Unknown error')}")
                    return None
            else:
                logger.warning(f"Alchemy HTTP error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.debug(f"Alchemy RPC call failed: {e}")
            return None
    
    def get_recent_signatures(self, limit: int = 25) -> List[str]:
        """Get recent transaction signatures for LetsBonk program - focusing ONLY on last 15 seconds"""
        try:
            # Get minimal signatures but focus on ULTRA-recent ones only
            result = self._make_rpc_call("getSignaturesForAddress", [
                self.letsbonk_program_id,
                {
                    "limit": limit,  # Minimal to focus on most recent
                    "commitment": "confirmed"
                }
            ])
            
            if result:
                # Filter for only ULTRA-recent signatures (last 15 seconds max)
                current_time = time.time()
                recent_signatures = []
                
                for sig_info in result:
                    block_time = sig_info.get('blockTime')
                    if block_time and (current_time - block_time) <= 15:  # Only 15 seconds for ultra-fresh tokens
                        recent_signatures.append(sig_info['signature'])
                
                logger.debug(f"📊 Retrieved {len(recent_signatures)} recent signatures (last 15s) from Alchemy")
                return recent_signatures
            
            return []
            
        except Exception as e:
            logger.debug(f"Failed to get signatures: {e}")
            return []
    
    def get_transaction_details(self, signature: str) -> Optional[dict]:
        """Get transaction details using Alchemy"""
        if signature in self.processed_signatures:
            return None
        
        try:
            result = self._make_rpc_call("getTransaction", [
                signature,
                {
                    "encoding": "jsonParsed",
                    "commitment": "confirmed",
                    "maxSupportedTransactionVersion": 0
                }
            ])
            
            if result:
                self.processed_signatures[signature] = time.time()
                return result
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to get transaction {signature}: {e}")
            return None
    
    def extract_token_from_transaction(self, transaction: dict) -> Optional[Dict[str, Any]]:
        """Extract token information from transaction - ONLY for token CREATION events"""
        try:
            # CRITICAL: Validate blockchain timestamp with STRICT requirements
            block_time = transaction.get('blockTime')
            current_time = time.time()
            
            if block_time and block_time > 0:
                # Handle milliseconds vs seconds timestamp format
                if block_time > 1e12:  # Milliseconds format (timestamp > year 2001 in milliseconds)
                    normalized_block_time = block_time / 1000.0
                else:
                    normalized_block_time = block_time
                
                # STRICT VALIDATION: Reject invalid timestamps
                if normalized_block_time <= 0:
                    logger.debug(f"❌ REJECTED: Invalid timestamp <= 0: {normalized_block_time}")
                    return None
                
                if normalized_block_time > current_time + 300:  # Future timestamp (5 min tolerance)
                    logger.debug(f"❌ REJECTED: Future timestamp: {normalized_block_time} vs current {current_time}")
                    return None
                
                # NUCLEAR AGE VALIDATION: Only tokens < 2 minutes old
                transaction_age = current_time - normalized_block_time
                if transaction_age > 120:  # 2 minutes maximum
                    hours_old = transaction_age / 3600
                    logger.debug(f"❌ REJECTED: Transaction is {hours_old:.1f} hours old - COMPLETELY UNACCEPTABLE")
                    return None
                
                # Use normalized timestamp
                block_time = normalized_block_time
                logger.debug(f"✅ ULTRA-FRESH TRANSACTION (age: {transaction_age:.1f}s)")
            else:
                # No timestamp = definitely old, reject immediately
                logger.debug(f"❌ REJECTED: No blockTime timestamp")
                return None
            
            # Check if this is actually a TOKEN CREATION transaction
            if not self._is_token_creation_transaction(transaction):
                logger.debug(f"🚫 REJECTED: Not a token creation transaction")
                return None
            
            meta = transaction.get('meta', {})
            message = transaction.get('transaction', {}).get('message', {})
            
            # Look for new token mint in post token balances
            post_token_balances = meta.get('postTokenBalances', [])
            
            mint_addresses = []
            for balance in post_token_balances:
                mint = balance.get('mint', '')
                if mint and mint.lower().endswith('bonk'):
                    mint_addresses.append(mint)
            
            if not mint_addresses:
                return None
            
            mint_address = mint_addresses[0]
            
            # Get basic metadata using Alchemy
            metadata = self._get_token_metadata(mint_address)
            if not metadata:
                # ENHANCED FALLBACK: Use comprehensive name resolver instead of generic fallback
                try:
                    from enhanced_token_name_resolver import resolve_token_name_with_retry
                    import asyncio
                    
                    # Attempt enhanced resolution
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        enhanced_result = loop.run_until_complete(
                            resolve_token_name_with_retry(mint_address, block_time)
                        )
                        
                        if enhanced_result and enhanced_result.get('confidence', 0) > 0.8:
                            metadata = {
                                'name': enhanced_result.get('name'),
                                'symbol': enhanced_result.get('symbol', mint_address[-4:].upper()),
                                'decimals': 9,
                                'extraction_source': enhanced_result.get('source'),
                                'confidence': enhanced_result.get('confidence')
                            }
                            logger.info(f"✅ ENHANCED RESOLUTION: {enhanced_result.get('name')} (confidence: {enhanced_result.get('confidence')})")
                        else:
                            # NO FALLBACK - Return None to trigger smart retry
                            logger.info(f"🔄 NO NAME FOUND: {mint_address[-6:]} - queuing for smart retry")
                            return None
                    finally:
                        loop.close()
                        
                except Exception as e:
                    logger.error(f"Enhanced resolver failed: {e}")
                    # NO FALLBACK - Return None to trigger smart retry
                    logger.info(f"🔄 NO NAME FOUND: {mint_address[-6:]} - queuing for smart retry")
                    return None
            
            # Use the verified blockTime (we already checked it exists and is recent)
            signatures = transaction.get('transaction', {}).get('signatures', [''])
            
            # Log token creation for verification
            token_age = current_time - block_time
            logger.info(f"🎯 CREATING TOKEN ENTRY: {metadata.get('name', 'Unknown')} (blockchain age: {token_age:.1f}s)")
            
            return {
                'mint': mint_address,
                'address': mint_address,
                'name': metadata.get('name', 'Unknown Token'),
                'symbol': metadata.get('symbol', 'UNK'),
                'decimals': metadata.get('decimals', 9),
                'supply': 1000000000,
                'created_timestamp': block_time,  # Now guaranteed to be within 2 minutes
                'signature': signatures[0] if signatures else '',
                'platform': 'letsbonk.fun',
                'source': 'alchemy-api',
                'url': f"https://letsbonk.fun/token/{mint_address}"
            }
            
        except Exception as e:
            logger.debug(f"Token extraction error: {e}")
            return None
    
    def _is_token_creation_transaction(self, transaction: dict) -> bool:
        """Check if transaction is a token creation transaction for LetsBonk"""
        try:
            # Get transaction message
            message = transaction.get('transaction', {}).get('message', {})
            instructions = message.get('instructions', [])
            
            # Look for LetsBonk program instruction and token creation patterns
            for instruction in instructions:
                program_id = instruction.get('programId', '')
                
                # Check if it's a LetsBonk program instruction
                if program_id == self.letsbonk_program_id:
                    # Check instruction data for token creation patterns
                    data = instruction.get('data', '')
                    
                    # LetsBonk token creation usually has specific instruction patterns
                    # Look for mint creation or token initialization
                    if data and len(data) > 0:
                        # This is a LetsBonk program transaction
                        logger.debug(f"✅ Found LetsBonk program instruction")
                        return True
                
                # Also check for SPL Token program instructions (CreateMint, InitializeMint)
                elif program_id == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":
                    # SPL Token program - check for mint creation
                    data = instruction.get('data', '')
                    if data and data.startswith('0'):  # CreateMint instruction starts with 0
                        logger.debug(f"✅ Found SPL Token mint creation")
                        return True
            
            # Check post token balances for new mints (another indicator)
            meta = transaction.get('meta', {})
            post_token_balances = meta.get('postTokenBalances', [])
            pre_token_balances = meta.get('preTokenBalances', [])
            
            # New token creation usually has post balances but no pre balances
            if post_token_balances and not pre_token_balances:
                logger.debug(f"✅ Found new token balances (likely creation)")
                return True
            
            # Check for new mint addresses in post balances
            if post_token_balances:
                for balance in post_token_balances:
                    mint = balance.get('mint', '')
                    if mint and mint.endswith('bonk'):  # LetsBonk tokens end with 'bonk'
                        logger.debug(f"✅ Found LetsBonk token mint: {mint}")
                        return True
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking if token creation: {e}")
            return False
    
    def _get_token_metadata(self, mint_address: str) -> dict:
        """Get token metadata using Alchemy and Metaplex (cached)"""
        if mint_address in self.metadata_cache:
            return self.metadata_cache[mint_address]
        
        try:
            # Method 1: Try DexScreener API first (most reliable for LetsBonk tokens)
            dex_metadata = self._get_dexscreener_metadata(mint_address)
            if dex_metadata and dex_metadata.get('name') and len(dex_metadata['name'].strip()) > 0:
                logger.info(f"✅ Got real name from DexScreener: {dex_metadata['name']}")
                self.metadata_cache[mint_address] = dex_metadata
                return dex_metadata
            
            # Method 2: Try LetsBonk API (sometimes has unique data)
            letsbonk_metadata = self._get_letsbonk_metadata(mint_address)
            if letsbonk_metadata and letsbonk_metadata.get('name') and len(letsbonk_metadata['name'].strip()) > 0:
                logger.info(f"✅ Got real name from LetsBonk API: {letsbonk_metadata['name']}")
                self.metadata_cache[mint_address] = letsbonk_metadata
                return letsbonk_metadata
            
            # Method 3: Try Metaplex metadata (most accurate for real names)
            metadata = self._get_metaplex_metadata(mint_address)
            if metadata and metadata.get('name') and len(metadata['name'].strip()) > 0:
                logger.info(f"✅ Got real name from Metaplex: {metadata['name']}")
                self.metadata_cache[mint_address] = metadata
                return metadata
            
            # NO FALLBACK - Return None to trigger smart retry system
            logger.info(f"🔄 NO NAME FOUND: {mint_address[-6:]} - will queue for smart retry")
            return None
            
        except Exception as e:
            logger.debug(f"Metadata fetch error for {mint_address}: {e}")
            return None
            
        except Exception as e:
            logger.debug(f"Metadata fetch error for {mint_address}: {e}")
            return {}
    
    def _get_metaplex_metadata(self, mint_address: str) -> dict:
        """Get metadata from Metaplex metadata program"""
        try:
            import base58
            import struct
            
            # Metaplex metadata program ID
            metadata_program_id = "metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s"
            
            # Derive the metadata account PDA
            # This is a simplified PDA derivation for Metaplex metadata
            try:
                # Use getProgramAccounts to find metadata accounts for this mint
                result = self._make_rpc_call("getProgramAccounts", [
                    metadata_program_id,
                    {
                        "encoding": "base64",
                        "filters": [
                            {
                                "memcmp": {
                                    "offset": 33,  # Mint address offset in metadata account
                                    "bytes": mint_address
                                }
                            }
                        ]
                    }
                ])
                
                if result and len(result) > 0:
                    # Get the metadata account data
                    metadata_account = result[0]
                    account_data = metadata_account.get('account', {}).get('data')
                    
                    if account_data:
                        # Decode the metadata from base64
                        import base64
                        decoded_data = base64.b64decode(account_data[0])
                        
                        # Parse the metadata structure (simplified)
                        # Metaplex metadata has a specific structure
                        try:
                            # Skip the first few bytes (discriminator, etc.)
                            # The name usually starts around byte 69
                            offset = 69
                            
                            # Read name length (4 bytes)
                            if len(decoded_data) > offset + 4:
                                name_len = struct.unpack('<I', decoded_data[offset:offset+4])[0]
                                if name_len > 0 and name_len < 200:  # Reasonable name length
                                    name_start = offset + 4
                                    name_end = name_start + name_len
                                    if len(decoded_data) > name_end:
                                        name = decoded_data[name_start:name_end].decode('utf-8', errors='ignore').strip('\x00')
                                        
                                        # Read symbol length and symbol
                                        symbol_offset = name_end
                                        if len(decoded_data) > symbol_offset + 4:
                                            symbol_len = struct.unpack('<I', decoded_data[symbol_offset:symbol_offset+4])[0]
                                            if symbol_len > 0 and symbol_len < 50:
                                                symbol_start = symbol_offset + 4
                                                symbol_end = symbol_start + symbol_len
                                                if len(decoded_data) > symbol_end:
                                                    symbol = decoded_data[symbol_start:symbol_end].decode('utf-8', errors='ignore').strip('\x00')
                                                    
                                                    if name and len(name) > 0:
                                                        logger.info(f"🎯 Found real token name: {name} ({symbol})")
                                                        return {
                                                            'name': name,
                                                            'symbol': symbol,
                                                            'decimals': 9
                                                        }
                        except Exception as parse_error:
                            logger.debug(f"Metadata parsing error: {parse_error}")
                
            except Exception as rpc_error:
                logger.debug(f"RPC call failed: {rpc_error}")
            
            return None
            
        except Exception as e:
            logger.debug(f"Metaplex metadata fetch failed for {mint_address}: {e}")
            return None
    
    def _get_dexscreener_metadata(self, mint_address: str) -> dict:
        """Get token metadata from DexScreener API with better rate limiting"""
        try:
            import requests
            import time
            
            # Conservative delay to avoid DexScreener rate limiting
            time.sleep(0.2)  # Reduced from 0.5s to 0.2s for faster processing
            
            url = f"https://api.dexscreener.com/latest/dex/tokens/{mint_address}"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                if pairs:
                    pair = pairs[0]  # Take first pair
                    base_token = pair.get('baseToken', {})
                    
                    name = base_token.get('name', '')
                    symbol = base_token.get('symbol', '')
                    
                    if name and name != mint_address[:6] and len(name.strip()) > 0:
                        return {
                            'name': name,
                            'symbol': symbol or 'BONK',
                            'decimals': 9
                        }
            
            return None
            
        except Exception as e:
            logger.debug(f"DexScreener metadata fetch failed for {mint_address}: {e}")
            return None
    
    def _get_letsbonk_metadata(self, mint_address: str) -> dict:
        """Try to get metadata from LetsBonk API and website scraping"""
        try:
            # Method 1: Try LetsBonk API endpoints
            api_endpoints = [
                f"https://api.letsbonk.fun/token/{mint_address}",
                f"https://letsbonk.fun/api/token/{mint_address}",
                f"https://api.letsbonk.fun/v1/token/{mint_address}"
            ]
            
            for endpoint in api_endpoints:
                try:
                    response = self.session.get(endpoint, timeout=3)
                    if response.status_code == 200:
                        data = response.json()
                        name = data.get('name', data.get('tokenName', ''))
                        symbol = data.get('symbol', data.get('tokenSymbol', ''))
                        
                        if name and len(name.strip()) > 0:
                            logger.info(f"✅ Found real token name from LetsBonk API: {name}")
                            return {
                                'name': name,
                                'symbol': symbol or 'BONK',
                                'decimals': data.get('decimals', 9),
                                'supply': data.get('supply', '1000000000')
                            }
                except:
                    continue
            
            # Method 2: Try web scraping LetsBonk token page
            try:
                page_url = f"https://letsbonk.fun/token/{mint_address}"
                response = self.session.get(page_url, timeout=3)
                
                if response.status_code == 200:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for token name in common selectors
                    name_selectors = [
                        'h1.token-name',
                        '.token-title',
                        'h1',
                        '.name',
                        '[data-testid="token-name"]'
                    ]
                    
                    for selector in name_selectors:
                        element = soup.select_one(selector)
                        if element and element.text.strip():
                            name = element.text.strip()
                            if name != mint_address[:6] and len(name) > 0:
                                logger.info(f"✅ Found real token name from web scraping: {name}")
                                return {
                                    'name': name,
                                    'symbol': 'BONK',
                                    'decimals': 9
                                }
                            break
            except:
                pass
            
            return None
            
        except Exception as e:
            logger.debug(f"LetsBonk metadata fetch failed for {mint_address}: {e}")
            return None
    
    def get_latest_tokens(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get latest LetsBonk tokens using Alchemy API"""
        try:
            # Get recent signatures
            signatures = self.get_recent_signatures(limit)
            
            tokens = []
            processed_count = 0
            
            for signature in signatures:
                if processed_count >= limit:
                    break
                
                # Get transaction details
                transaction = self.get_transaction_details(signature)
                if not transaction:
                    continue
                
                # Extract token data
                token_data = self.extract_token_from_transaction(transaction)
                if token_data:
                    tokens.append(token_data)
                    processed_count += 1
            
            # Show ALL found tokens with full names and addresses
            if tokens:
                token_preview = [f"{t['name']} - {t['address']}" for t in tokens]
                logger.info(f"🎯 Found {len(tokens)} LetsBonk tokens:")
                for token in tokens:
                    logger.debug(f"   📍 {token['name']} - {token['address']}")
            else:
                logger.debug("📊 No new LetsBonk tokens found in recent transactions")
            
            return tokens
            
        except Exception as e:
            logger.error(f"Alchemy token fetching failed: {e}")
            return []
    
    def is_newly_created_token(self, token: Dict[str, Any], monitoring_start_time: float) -> bool:
        """Check if token was created within the last 2 minutes (ultra-fresh tokens only)"""
        try:
            created_timestamp = token.get('created_timestamp', 0)
            current_time = time.time()
            
            # If no valid timestamp, try to get token creation time from blockchain
            if not created_timestamp or created_timestamp == 0:
                # Try to get actual token creation time from mint address
                try:
                    mint_address = token.get('address', '')
                    if mint_address:
                        # Use getTokenLargestAccounts to check if token is very new
                        result = self._make_rpc_call("getTokenLargestAccounts", [mint_address])
                        if result and result.get('value'):
                            # If token has accounts, it's likely been around for a while
                            # Real new tokens typically have very few or no large accounts
                            accounts = result['value']
                            if len(accounts) > 3:
                                logger.debug(f"⏰ Token has {len(accounts)} accounts, likely old: {token['name']}")
                                return False
                        
                        # For tokens without proper timestamps, be VERY strict
                        # Only allow if monitoring started within last 2 minutes
                        time_since_start = current_time - monitoring_start_time
                        if time_since_start > 120:  # 2 minutes max
                            logger.debug(f"⏰ No timestamp and monitoring running >2min, treating as old: {token['name']}")
                            return False
                        
                        # Even without timestamp, still reject if token has many accounts
                        # This prevents old tokens from slipping through
                        logger.debug(f"⚠️ No timestamp available, likely old token: {token['name']}")
                        return False
                except Exception as e:
                    logger.debug(f"Error checking token accounts: {e}")
                    return False
            
            # Only consider tokens created within last 2 minutes as "new" 
            # This ensures ONLY ultra-fresh tokens are alerted
            two_minutes_ago = current_time - 120  # 2 minutes max age
            
            is_recent = created_timestamp >= two_minutes_ago
            is_after_start = created_timestamp >= monitoring_start_time
            
            if is_recent and is_after_start:
                age_seconds = current_time - created_timestamp
                logger.info(f"🆕 ULTRA-FRESH TOKEN: {token['name']} (age: {age_seconds:.1f} seconds)")
                return True
            else:
                age_seconds = current_time - created_timestamp
                if age_seconds > 60:
                    age_minutes = age_seconds / 60
                    logger.debug(f"⏰ Token TOO OLD: {token['name']} (age: {age_minutes:.1f} minutes) - REJECTED")
                else:
                    logger.debug(f"⏰ Token before monitoring start: {token['name']} (age: {age_seconds:.1f}s)")
                return False
            
        except Exception as e:
            logger.debug(f"Age check error: {e}")
            return False

def test_alchemy_scraper():
    """Test the Alchemy scraper functionality"""
    try:
        scraper = AlchemyLetsBonkScraper()
        logger.info("🧪 Testing Alchemy LetsBonk scraper...")
        
        # Test getting recent signatures
        signatures = scraper.get_recent_signatures(10)
        logger.info(f"📊 Retrieved {len(signatures)} signatures")
        
        # Test getting tokens
        tokens = scraper.get_latest_tokens(5)
        logger.info(f"🎯 Found {len(tokens)} tokens")
        
        for token in tokens:
            logger.info(f"   - {token['name']} ({token['symbol']}) - {token['address']}")
        
        logger.info("✅ Alchemy scraper test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Alchemy scraper test failed: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_alchemy_scraper()