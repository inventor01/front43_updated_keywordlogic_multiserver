#!/usr/bin/env python3
"""
Front 36 - Integrated Token Monitoring System with Enhanced Discord Notifications
Real-time Solana token detection with multi-platform support and mobile-optimized notifications
Railway deployment ready with port conflict resolution
"""

import asyncio
import websockets
import json
import time
import threading
import psycopg2
import os
import requests
import discord
from discord.ext import commands
from datetime import datetime
import logging
from flask import Flask, jsonify
from waitress import serve
from typing import Optional, Dict, List
import difflib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegratedTokenMonitor:
    def __init__(self):
        # Database setup
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            logger.error("❌ DATABASE_URL environment variable is required")
            raise ValueError("DATABASE_URL environment variable is required")
        
        # WebSocket setup
        self.websocket_url = "wss://pumpportal.fun/api/data"
        self.running = False
        self.processed_tokens = set()
        
        # Discord setup
        self.discord_token = os.getenv('DISCORD_TOKEN')
        self.webhook_url = os.getenv('DISCORD_WEBHOOK_URL', '')
        
        # Keywords cache
        self.user_keywords = {}
        self.last_keyword_refresh = 0
        
        # PumpPortal market data cache
        self.token_market_cache = {}
        self.pumpportal_api_key = os.getenv('PUMPPORTAL_API_KEY', '')
        
        logger.info("🚀 Integrated Token Monitor initialized")
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            return psycopg2.connect(self.database_url)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return None
    
    def refresh_keywords(self):
        """Refresh user keywords from database"""
        try:
            # Only refresh every 30 seconds to avoid database spam
            if time.time() - self.last_keyword_refresh < 30:
                return
            
            conn = self.get_db_connection()
            if not conn:
                return
            
            cursor = conn.cursor()
            # Support both System keywords (global) and user-specific keywords
            cursor.execute("SELECT user_id, keyword FROM keywords WHERE user_id = 'System' OR user_id IS NOT NULL")
            
            # Group keywords by user
            new_keywords = {}
            for user_id, keyword in cursor.fetchall():
                if user_id not in new_keywords:
                    new_keywords[user_id] = []
                new_keywords[user_id].append(keyword.lower().strip())
            
            self.user_keywords = new_keywords
            self.last_keyword_refresh = time.time()
            
            total_keywords = sum(len(keywords) for keywords in new_keywords.values())
            logger.info(f"🔄 Refreshed {total_keywords} keywords for {len(new_keywords)} users")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to refresh keywords: {e}")
    
    def check_keyword_matches(self, token_name: str, token_address: str) -> List[Dict]:
        """Check if token matches any user keywords + special LetsBonk detection"""
        if not token_name:
            return []
        
        token_name_lower = token_name.lower().strip()
        matches = []
        
        # Detect platform type
        platform = self.detect_platform(token_address)
        
        # Check user keywords with System keyword support
        for user_id, user_keywords in self.user_keywords.items():
            for keyword in user_keywords:
                # Enhanced matching logic
                if self.is_keyword_match(token_name_lower, keyword):
                    # System keywords apply to all users, user-specific only to owner
                    if user_id == 'System':
                        # Add match for system-wide keyword (use first available user or system)
                        target_user = '407225673279864832'  # Default notification user
                        matches.append({
                            'user_id': target_user,
                            'keyword': keyword,
                            'token_name': token_name,
                            'token_address': token_address,
                            'match_type': self.get_match_type(token_name_lower, keyword),
                            'platform': platform
                        })
                    else:
                        # User-specific keyword
                        matches.append({
                            'user_id': user_id,
                            'keyword': keyword,
                            'token_name': token_name,
                            'token_address': token_address,
                            'match_type': self.get_match_type(token_name_lower, keyword),
                            'platform': platform
                        })
        
        # STRICT KEYWORD MATCHING ONLY - No auto-notifications to prevent spam
        
        return matches
    
    def is_keyword_match(self, token_name: str, keyword: str) -> bool:
        """ENHANCED keyword matching with normalization and flexible matching"""
        import re
        
        # Normalize both token name and keyword
        def normalize(text):
            # Remove special characters, convert to lowercase, normalize spaces
            normalized = re.sub(r'[_\-\s]+', ' ', text.lower().strip())
            return normalized
        
        normalized_token = normalize(token_name)
        normalized_keyword = normalize(keyword)
        
        # Exact match after normalization
        if normalized_keyword == normalized_token:
            return True
        
        # Enhanced partial matching for single words
        if len(normalized_keyword.split()) == 1:
            # Create flexible pattern that handles word boundaries and partial matches
            keyword_clean = re.escape(normalized_keyword)
            patterns = [
                rf'\b{keyword_clean}\b',  # Word boundary match: "coin" in "apple coin"
                rf'{keyword_clean}',      # Substring match: "coin" in "AppleCoin"
            ]
            
            for pattern in patterns:
                if re.search(pattern, normalized_token):
                    return True
        else:
            # Multi-word phrase matching with normalization
            if normalized_keyword in normalized_token:
                return True
            
            # Word-based matching for multi-word keywords
            token_words = set(word for word in normalized_token.split() if len(word) > 1)
            keyword_words = set(word for word in normalized_keyword.split() if len(word) > 1)
            
            # Skip very short tokens to prevent noise
            if len(normalized_token.strip()) <= 2:
                return False
            
            # Require significant word overlap (75% instead of 100%)
            if keyword_words:
                overlap = len(token_words.intersection(keyword_words))
                overlap_ratio = overlap / len(keyword_words)
                if overlap_ratio >= 0.75:  # 75% overlap for better matching
                    return True
        
        return False
    
    def detect_platform(self, token_address: str) -> str:
        """Detect token platform based on contract address"""
        if token_address.endswith('pump'):
            return 'Pump.fun'
        elif token_address.endswith('bonk'):
            return 'LetsBonk'
        else:
            return 'Other'
    
    def is_platform_enabled(self, user_id: str, platform: str) -> bool:
        """Check if user has enabled notifications for a specific platform"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return True  # Default to enabled if can't check
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT notifications_enabled 
                FROM platform_preferences 
                WHERE user_id = %s AND platform = %s
            """, (user_id, platform))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                return result[0]
            else:
                # Create default preference if not exists
                default_enabled = platform != 'Other'
                try:
                    conn = self.get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO platform_preferences (user_id, platform, notifications_enabled)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (user_id, platform) DO NOTHING
                    """, (user_id, platform, default_enabled))
                    conn.commit()
                    cursor.close()
                    conn.close()
                except:
                    pass
                return default_enabled
                
        except Exception as e:
            logger.warning(f"Platform preference check failed: {e}")
            return True  # Default to enabled on error
    
    def get_match_type(self, token_name: str, keyword: str) -> str:
        """Determine match type for logging"""
        if keyword == token_name:
            return "exact"
        elif keyword in token_name or token_name in keyword:
            return "substring"
        else:
            return "fuzzy"
    
    async def send_discord_notification(self, match_info: Dict):
        """Send Discord notification for keyword match with ENHANCED FORMAT + LetsBonk highlighting"""
        try:
            # Get market data
            market_data = await self.get_market_data(match_info['token_address'])
            
            # Detect platform and customize notification
            platform = match_info.get('platform', self.detect_platform(match_info['token_address']))
            is_letsbonk = platform == 'LetsBonk'
            
            # Customize title and color based on platform
            if is_letsbonk:
                title = '🟠 NEW LETSBONK TOKEN DETECTED'
                color = 0xff6b35  # Orange for LetsBonk
                platform_emoji = '🟠'
            else:
                title = '🚨 NEW TOKEN DETECTED'
                color = 0x00ff41  # Green for others
                platform_emoji = '🔵' if platform == 'Pump.fun' else '⚪'
            
            # Create ENHANCED rich embed with MOBILE COPY OPTIMIZED formatting
            embed = {
                'title': title,
                'description': f'**{match_info["token_name"]}** matches your keyword: `{match_info["keyword"]}`\n\n`{match_info["token_address"]}`',
                'color': color,
                'fields': [
                    {
                        'name': '📊 Token Info',
                        'value': f'**Name:** {match_info["token_name"]}\n**Platform:** {platform_emoji} {platform}\n**Keyword:** {match_info["keyword"]}\n**Match:** {match_info["match_type"].capitalize()}',
                        'inline': True
                    }
                ],
                'timestamp': datetime.now().isoformat(),
                'footer': {
                    'text': f'⚡ Real-time {platform} monitoring • Keyword match alert'
                }
            }
            
            # ENHANCED Market data with MARKET CAP prominently displayed first
            market_value = ""
            data_source = market_data.get('source', 'DexScreener') if market_data and not market_data.get('status') else ''
            
            if market_data and not market_data.get('status'):
                # ALWAYS show market cap first - most important metric
                if market_data.get('market_cap') and market_data['market_cap'] > 0:
                    mc = market_data['market_cap']
                    if mc >= 1_000_000:
                        market_value += f"💰 **MARKET CAP: ${mc/1_000_000:.2f}M**\n"
                    elif mc >= 1_000:
                        market_value += f"💰 **MARKET CAP: ${mc/1_000:.1f}K**\n"
                    else:
                        market_value += f"💰 **MARKET CAP: ${mc:.2f}**\n"
                else:
                    market_value += f"💰 **MARKET CAP:** ${market_data.get('market_cap', 0):.0f}\n"
                
                if market_data.get('price'):
                    market_value += f"💵 **Price:** ${market_data['price']:.8f}\n"
                if market_data.get('volume_24h'):
                    vol = market_data['volume_24h']
                    if vol >= 1_000_000:
                        market_value += f"📊 **24h Volume:** ${vol/1_000_000:.1f}M"
                    elif vol >= 1_000:
                        market_value += f"📊 **24h Volume:** ${vol/1_000:.0f}K"
                    else:
                        market_value += f"📊 **24h Volume:** ${vol:,.0f}"
                
                # Add data source attribution
                if data_source:
                    market_value += f"\n📈 **Source:** {data_source}"
                    
            elif market_data and market_data.get('status') == 'too_new':
                market_value = "💰 **MARKET CAP:** Just launched!\n💵 **Price:** Trading starting...\n📊 **Volume:** Fresh token - check PumpFun\n🚀 **Source:** PumpFun Launch"
            else:
                market_value = "💰 **MARKET CAP:** Loading...\n💵 **Price:** Fetching...\n📊 **Volume:** Please wait"
            
            # Always show market data field with market cap prominently displayed
            embed['fields'].append({
                'name': '💰 Live Market Data',
                'value': market_value,
                'inline': True
            })
            
            # Platform info field
            embed['fields'].append({
                'name': '🚀 Platform',
                'value': "**Source:** PumpFun\n**Network:** Solana",
                'inline': True
            })
            
            # Trading links field with enhanced copy functionality
            links_text = f"[🚀 Trade on PumpFun](https://pump.fun/{match_info['token_address']})\n"
            links_text += f"[📊 DexScreener](https://dexscreener.com/solana/{match_info['token_address']})\n"
            links_text += f"[🔍 SolScan](https://solscan.io/token/{match_info['token_address']})\n"
            links_text += f"[📋 Copy Address](https://solscan.io/token/{match_info['token_address']})"
            
            embed['fields'].append({
                'name': '🔗 Trading Links',
                'value': links_text,
                'inline': False
            })
            
            # Send notification
            payload = {
                'content': f'<@{match_info["user_id"]}>',  # Mention user
                'embeds': [embed]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200 or response.status_code == 204:
                logger.info(f"✅ ENHANCED Discord notification sent to user {match_info['user_id']}")
                
                # Record notification in database
                await self.record_notification(match_info)
                
                return True
            else:
                logger.error(f"Discord notification failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")
            return False
    
    async def record_notification(self, match_info: Dict):
        """Record notification in database - fix column name"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return
            
            cursor = conn.cursor()
            # Use correct column name 'user_id' instead of 'matched_keyword'
            cursor.execute("""
                INSERT INTO notified_tokens (token_address, token_name, user_id, notified_at, notification_type)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (token_address, user_id) DO NOTHING
            """, (
                match_info['token_address'],
                match_info['token_name'],
                match_info['user_id'],
                datetime.now(),
                'keyword_match'
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to record notification: {e}")
    
    async def get_market_data(self, token_address: str, retry_delay: int = 0) -> Dict:
        """Get market data from PumpPortal first, then fallback to DexScreener"""
        import time
        
        if retry_delay > 0:
            logger.info(f"⏱️ Waiting {retry_delay} seconds before retry for {token_address[:10]}...")
            time.sleep(retry_delay)
        
        # Try PumpPortal first (best for new tokens)
        pumpportal_data = await self.get_pumpportal_data(token_address)
        if pumpportal_data and not pumpportal_data.get('status'):
            logger.info(f"✅ Got PumpPortal data for {token_address[:10]}...")
            return pumpportal_data
        
        # Fallback to DexScreener
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            logger.info(f"📊 Fetching DexScreener data for {token_address[:10]}...")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs') if data else None
                
                if pairs and len(pairs) > 0:
                    logger.info(f"📊 Found {len(pairs)} pairs for {token_address[:10]}...")
                    
                    # Get the pair with highest liquidity (or first if no liquidity data)
                    try:
                        best_pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0)) if x.get('liquidity') else 0)
                    except:
                        best_pair = pairs[0]
                    
                    market_data = {
                        'price': float(best_pair.get('priceUsd', 0)),
                        'market_cap': float(best_pair.get('marketCap', 0)),
                        'volume_24h': float(best_pair.get('volume', {}).get('h24', 0)),
                        'liquidity': float(best_pair.get('liquidity', {}).get('usd', 0)),
                        'price_change_24h': float(best_pair.get('priceChange', {}).get('h24', 0)),
                        'source': 'DexScreener'
                    }
                    
                    logger.info(f"✅ DexScreener data loaded: MC=${market_data['market_cap']:.0f}, Price=${market_data['price']:.8f}")
                    return market_data
                else:
                    logger.warning(f"⚠️ No pairs found on DexScreener for {token_address[:10]}...")
                    return {'status': 'too_new'}
            else:
                logger.warning(f"⚠️ DexScreener API error {response.status_code} for {token_address[:10]}...")
                return {'status': 'api_error'}
                
        except Exception as e:
            logger.warning(f"❌ Market data fetch failed for {token_address[:10]}...: {e}")
            return {'status': 'fetch_error'}
        
        return {'status': 'unknown_error'}
    
    async def get_pumpportal_data(self, token_address: str) -> Dict:
        """Get market data from PumpPortal WebSocket cache or try pump.fun API"""
        
        # First check if we have cached WebSocket data for this token
        cached_data = self.get_cached_token_data(token_address)
        if cached_data:
            logger.info(f"✅ Using cached PumpPortal data for {token_address[:10]}...")
            return cached_data
        
        # Try alternative pump.fun endpoints
        endpoints = [
            f"https://pump.fun/coin/{token_address}",
            f"https://api.pump.fun/coins/{token_address}",
            f"https://pump.fun/api/tokens/{token_address}"
        ]
        
        for endpoint in endpoints:
            try:
                logger.info(f"🚀 Trying endpoint for {token_address[:10]}...")
                response = requests.get(endpoint, timeout=8, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    # Try to extract any market data from the response
                    content = response.text
                    if 'market_cap' in content or 'marketCap' in content:
                        logger.info(f"✅ Found market data in response for {token_address[:10]}")
                        # Would need to parse HTML/JSON for actual data
                        # For now, return status to indicate we should use DexScreener
                        return {'status': 'found_but_parsing_needed'}
                        
            except Exception as e:
                logger.debug(f"Endpoint failed: {e}")
                continue
        
        return {'status': 'no_data'}
    
    def get_cached_token_data(self, token_address: str) -> Optional[Dict]:
        """Get cached token data from WebSocket events"""
        # Check if we have cached market data for this token
        if token_address in self.token_market_cache:
            cached_data = self.token_market_cache[token_address]
            # Return cached data if it's less than 30 seconds old
            if time.time() - cached_data.get('timestamp', 0) < 30:
                return cached_data
        
        # No valid cached data available
        return None
    
    def format_market_cap(self, market_cap: float) -> str:
        """Format market cap for display"""
        if market_cap >= 1_000_000:
            return f"${market_cap/1_000_000:.1f}M"
        elif market_cap >= 1_000:
            return f"${market_cap/1_000:.0f}K"
        else:
            return f"${market_cap:.0f}"
    
    async def connect_and_monitor(self):
        """Connect to PumpPortal and monitor for tokens"""
        try:
            logger.info(f"🔗 Connecting to {self.websocket_url}")
            
            async with websockets.connect(self.websocket_url) as websocket:
                self.running = True
                logger.info("✅ Connected to PumpPortal")
                
                # Subscribe to new token events
                subscribe_message = json.dumps({"method": "subscribeNewToken"})
                await websocket.send(subscribe_message)
                logger.info("📡 Subscribed to new token events")
                
                # Listen for messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        await self.process_token_data(data)
                        
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON: {message[:100]}")
                    except Exception as e:
                        logger.error(f"Message processing error: {e}")
        
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            self.running = False
    
    async def process_token_data(self, data):
        """Process incoming token data and check for notifications"""
        try:
            # Check for new token events
            if data.get('type') == 'new_token' or 'mint' in data:
                token_address = data.get('mint') or data.get('address')
                token_name = data.get('name', 'Unknown')
                token_symbol = data.get('symbol', '')
                
                if token_address and token_address not in self.processed_tokens:
                    # Check if token already exists in database to prevent duplicates
                    if await self.token_already_exists(token_address):
                        logger.info(f"🔄 Token already exists: {token_address[:10]}...")
                        self.processed_tokens.add(token_address)
                        return
                    
                    self.processed_tokens.add(token_address)
                    
                    logger.info(f"🆕 New token: {token_name} ({token_symbol}) - {token_address}")
                    
                    # Enhanced name resolution with symbol fallback
                    enhanced_name = await self.enhance_token_name(token_address, token_name, token_symbol)
                    
                    # Insert to database
                    await self.insert_token_to_database(token_address, enhanced_name, token_symbol)
                    
                    # Refresh keywords periodically
                    self.refresh_keywords()
                    
                    # Check for keyword matches and send notifications
                    matches = self.check_keyword_matches(enhanced_name, token_address)
                    
                    if matches:
                        logger.info(f"🎯 STRICT MATCH: Found {len(matches)} keyword matches for '{enhanced_name}'")
                        
                        # DEDUPLICATE: Group matches by user to send only ONE notification per user per token
                        user_matches = {}
                        for match in matches:
                            user_id = match['user_id']
                            if user_id not in user_matches:
                                user_matches[user_id] = match
                                logger.info(f"✅ MATCH DETAILS: Token='{match['token_name']}' | Keyword='{match['keyword']}' | Type={match['match_type']}")
                            else:
                                logger.info(f"🔄 SKIPPING DUPLICATE: Same user {user_id} already has notification for this token")
                        
                        # Send one notification per user
                        for user_id, match in user_matches.items():
                            await self.send_discord_notification(match)
                    
        except Exception as e:
            logger.error(f"Token processing error: {e}")
    
    async def enhance_token_name(self, address, raw_name, symbol=''):
        """Enhanced token name resolution with fallbacks"""
        try:
            # If we have a valid name, use it
            if raw_name and raw_name not in ['Unknown', 'Unnamed Token', '']:
                return raw_name
            
            # Try DexScreener for name resolution
            url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                if pairs:
                    enhanced_name = pairs[0].get('baseToken', {}).get('name')
                    if enhanced_name and enhanced_name not in ['Unknown', '']:
                        logger.info(f"🔍 Enhanced: {raw_name} → {enhanced_name}")
                        return enhanced_name
            
            # Fallback to symbol if available
            if symbol and symbol not in ['', 'Unknown']:
                logger.info(f"🔤 Using symbol fallback: {symbol}")
                return symbol
            
            # Last resort: use truncated address
            logger.info(f"📍 Using address fallback: {address[:8]}...")
            return f"Token_{address[:8]}"
        
        except Exception as e:
            logger.warning(f"Name enhancement failed: {e}")
            # Return symbol or address as fallback
            return symbol if symbol and symbol != '' else f"Token_{address[:8]}"
    
    async def insert_token_to_database(self, address, name, symbol):
        """Insert token to database with platform detection"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return
            
            cursor = conn.cursor()
            platform = self.detect_platform(address)
            
            # Determine which table based on name quality
            if self.is_valid_token_name(name):
                cursor.execute("""
                    INSERT INTO detected_tokens (address, name, symbol, created_at, name_status, status, data_source, platform)
                    VALUES (%s, %s, %s, %s, 'resolved', 'detected', 'pumpportal', %s)
                    ON CONFLICT (address) DO NOTHING
                """, (address, name, symbol, datetime.now(), platform))
                
                if cursor.rowcount > 0:
                    platform_emoji = "🟠" if platform == "LetsBonk" else "🔵" if platform == "Pump.fun" else "⚪"
                    logger.info(f"✅ Added to detected_tokens: {name} {platform_emoji}")
            else:
                cursor.execute("""
                    INSERT INTO fallback_processing_coins (contract_address, token_name, symbol, created_at, processing_status, platform)
                    VALUES (%s, %s, %s, %s, 'pending', %s)
                    ON CONFLICT (contract_address) DO NOTHING
                """, (address, name, symbol, datetime.now(), platform))
                
                if cursor.rowcount > 0:
                    logger.info(f"📦 Added to fallback: {name}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Database error: {e}")
    
    def is_valid_token_name(self, name):
        """Check if token name is valid for immediate processing"""
        if not name or name in ['Unknown', '', None]:
            return False
        
        # Allow tokens with fallback names (symbol or address-based) to be processed
        invalid_patterns = ['Unnamed Token', 'Unknown Token']
        
        # If it's a fallback name (Token_XXXX or symbol), consider it valid for matching
        if name.startswith('Token_') or len(name.split()) == 1:
            return True
            
        return not any(pattern.lower() in name.lower() for pattern in invalid_patterns)
    
    async def token_already_exists(self, address: str) -> bool:
        """Check if token already exists in database"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
            
            cursor = conn.cursor()
            # Check both main and fallback tables
            cursor.execute("""
                SELECT 1 FROM detected_tokens WHERE address = %s
                UNION
                SELECT 1 FROM fallback_processing_coins WHERE contract_address = %s
                LIMIT 1
            """, (address, address))
            
            exists = cursor.fetchone() is not None
            cursor.close()
            conn.close()
            return exists
            
        except Exception as e:
            logger.warning(f"Token existence check failed: {e}")
            return False

class IntegratedServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.monitor = IntegratedTokenMonitor()
        self.start_time = time.time()
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def home():
            uptime = time.time() - self.start_time
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Integrated Token Monitor</title>
                <meta http-equiv="refresh" content="30">
                <style>
                    body { font-family: Arial; margin: 40px; background: #1a1a1a; color: #fff; }
                    .container { max-width: 800px; margin: 0 auto; }
                    .status { background: #2d2d2d; padding: 20px; border-radius: 8px; margin: 20px 0; }
                    .metric { display: inline-block; margin: 10px 20px; }
                    .value { font-size: 24px; font-weight: bold; color: #4CAF50; }
                    .label { color: #ccc; font-size: 14px; }
                    h1 { color: #4CAF50; }
                    .notification { background: #ff6b35; padding: 15px; border-radius: 5px; margin: 10px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🚀 Integrated Token Monitor with Discord Notifications</h1>
                    
                    <div class="status">
                        <h3>System Status</h3>
                        <div class="metric">
                            <div class="value">ACTIVE</div>
                            <div class="label">Monitor Status</div>
                        </div>
                        <div class="metric">
                            <div class="value">""" + str(len(self.monitor.processed_tokens)) + """</div>
                            <div class="label">Tokens Processed</div>
                        </div>
                        <div class="metric">
                            <div class="value">""" + f"{uptime/3600:.1f}h" + """</div>
                            <div class="label">Uptime</div>
                        </div>
                        <div class="metric">
                            <div class="value">""" + str(sum(len(keywords) for keywords in self.monitor.user_keywords.values())) + """</div>
                            <div class="label">Active Keywords</div>
                        </div>
                        <div class="metric">
                            <div class="value">""" + str(len(self.monitor.user_keywords)) + """</div>
                            <div class="label">Users</div>
                        </div>
                    </div>
                    
                    <div class="notification">
                        <strong>🎯 Discord Notifications Active!</strong><br>
                        Real-time keyword matching with instant Discord alerts enabled.
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html
        
        @self.app.route('/copy')
        def copy_interface():
            """Mobile-friendly contract address copy interface"""
            return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📱 Token Address Copier</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 15px; color: white;
        }
        .container { max-width: 500px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 25px; }
        .header h1 { font-size: 24px; margin-bottom: 5px; }
        .token-card {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 12px; padding: 15px; margin-bottom: 12px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .token-name { font-size: 16px; font-weight: bold; margin-bottom: 4px; }
        .token-symbol { font-size: 13px; opacity: 0.8; margin-bottom: 8px; }
        .address-container {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 8px; padding: 12px; margin: 8px 0;
        }
        .address-text {
            font-family: 'Courier New', monospace;
            font-size: 11px; word-break: break-all;
            user-select: all; -webkit-user-select: all;
            cursor: text; line-height: 1.3;
            background: rgba(255, 255, 255, 0.1);
            padding: 8px; border-radius: 4px;
        }
        .copy-btn {
            background: #4CAF50; color: white; border: none;
            padding: 10px 15px; border-radius: 6px; font-size: 14px;
            cursor: pointer; width: 100%; margin-top: 8px;
            font-weight: bold; transition: background 0.2s;
        }
        .copy-btn:active { background: #45a049; transform: scale(0.98); }
        .platform-badge {
            display: inline-block; padding: 3px 8px;
            border-radius: 10px; font-size: 11px;
            font-weight: bold; margin-bottom: 8px;
        }
        .pump-fun { background: #1E90FF; }
        .letsbonk { background: #FF8C00; }
        .other { background: #808080; }
        .loading { text-align: center; padding: 30px; font-size: 16px; }
        .success-msg {
            background: #4CAF50; padding: 8px; border-radius: 4px;
            margin-top: 6px; text-align: center; font-size: 13px;
            opacity: 0; transition: opacity 0.3s;
        }
        .success-msg.show { opacity: 1; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 Token Address Copier</h1>
            <p>Tap any address to copy instantly</p>
        </div>
        <div id="loading" class="loading">Loading recent tokens...</div>
        <div id="tokens-container"></div>
    </div>
    <script>
        async function loadTokens() {
            try {
                const response = await fetch('/api/recent-tokens');
                const data = await response.json();
                const container = document.getElementById('tokens-container');
                const loading = document.getElementById('loading');
                
                loading.style.display = 'none';
                
                if (data.tokens && data.tokens.length > 0) {
                    data.tokens.forEach(token => {
                        const tokenCard = createTokenCard(token);
                        container.appendChild(tokenCard);
                    });
                } else {
                    container.innerHTML = '<p>No recent tokens found</p>';
                }
            } catch (error) {
                document.getElementById('loading').textContent = 'Error loading tokens';
            }
        }
        
        function createTokenCard(token) {
            const card = document.createElement('div');
            card.className = 'token-card';
            const platformClass = token.platform === 'Pump.fun' ? 'pump-fun' : 
                                 token.platform === 'LetsBonk' ? 'letsbonk' : 'other';
            const randomId = Math.random().toString(36).substr(2, 9);
            
            card.innerHTML = `
                <div class="platform-badge \${platformClass}">\${token.platform || 'Unknown'}</div>
                <div class="token-name">\${token.name}</div>
                <div class="token-symbol">\${token.symbol}</div>
                <div class="address-container">
                    <div class="address-text" onclick="selectText(this)">\${token.address}</div>
                    <button class="copy-btn" onclick="copyToClipboard('\${token.address}', this)">
                        📋 TAP TO COPY ADDRESS
                    </button>
                    <div class="success-msg" id="success-\${randomId}">✅ Address copied to clipboard!</div>
                </div>
            `;
            
            // Fix template literals
            card.innerHTML = card.innerHTML.replace(/\\\$/g, '$');
            return card;
        }
        
        function selectText(element) {
            const range = document.createRange();
            range.selectNodeContents(element);
            const selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);
        }
        
        async function copyToClipboard(address, button) {
            try {
                if (navigator.clipboard && window.isSecureContext) {
                    await navigator.clipboard.writeText(address);
                } else {
                    // Fallback for older browsers or non-HTTPS
                    const textArea = document.createElement('textarea');
                    textArea.value = address;
                    textArea.style.position = 'absolute';
                    textArea.style.left = '-9999px';
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                }
                
                // Visual feedback
                const successMsg = button.nextElementSibling;
                if (successMsg) {
                    successMsg.classList.add('show');
                    setTimeout(() => successMsg.classList.remove('show'), 2500);
                }
                
                button.textContent = '✅ COPIED!';
                button.style.background = '#4CAF50';
                setTimeout(() => {
                    button.textContent = '📋 TAP TO COPY ADDRESS';
                    button.style.background = '#4CAF50';
                }, 2000);
                
                // Vibration feedback on mobile
                if (navigator.vibrate) {
                    navigator.vibrate(100);
                }
                
            } catch (error) {
                console.error('Copy failed:', error);
                button.textContent = '📋 Long-press address above to copy';
                setTimeout(() => {
                    button.textContent = '📋 TAP TO COPY ADDRESS';
                }, 3000);
            }
        }
        
        document.addEventListener('DOMContentLoaded', loadTokens);
        setInterval(loadTokens, 30000);
    </script>
</body>
</html>'''
        
        @self.app.route('/api/recent-tokens')
        def get_recent_tokens():
            """API endpoint for recent tokens"""
            try:
                conn = self.monitor.get_db_connection()
                if not conn:
                    return jsonify({'error': 'Database connection failed'}), 500
                
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT token_name, token_address, symbol, platform, created_at
                    FROM detected_tokens 
                    WHERE token_name IS NOT NULL 
                    AND token_name != 'Unnamed Token'
                    AND token_address IS NOT NULL
                    ORDER BY created_at DESC 
                    LIMIT 25
                """)
                
                tokens = []
                for row in cursor.fetchall():
                    tokens.append({
                        'name': row[0],
                        'address': row[1],
                        'symbol': row[2] or 'UNK',
                        'platform': self.monitor.detect_platform(row[1]),
                        'created_at': row[4].isoformat() if row[4] else None
                    })
                
                cursor.close()
                conn.close()
                
                return jsonify({'tokens': tokens})
                
            except Exception as e:
                return jsonify({'error': f'Failed to fetch tokens: {str(e)}'}), 500
        
        @self.app.route('/health')
        def health():
            return jsonify({
                'status': 'healthy',
                'uptime': time.time() - self.start_time,
                'tokens_processed': len(self.monitor.processed_tokens),
                'websocket_active': self.monitor.running,
                'active_keywords': sum(len(keywords) for keywords in self.monitor.user_keywords.values()),
                'users': len(self.monitor.user_keywords)
            })
    
    def start_monitoring(self):
        """Start monitoring in background thread"""
        def run_asyncio_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            while True:
                try:
                    loop.run_until_complete(self.monitor.connect_and_monitor())
                except Exception as e:
                    logger.error(f"Monitor error: {e}")
                
                # Reconnect after delay
                time.sleep(5)
                logger.info("🔄 Attempting reconnection...")
        
        monitor_thread = threading.Thread(target=run_asyncio_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return monitor_thread
    
    def run(self):
        """Run the integrated server"""
        logger.info("🚀 Starting Integrated Token Monitor with Discord Notifications")
        
        # Start token monitoring
        self.start_monitoring()
        
        # Start web server
        logger.info("🌐 Web interface starting on port 5000")
        serve(self.app, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    server = IntegratedServer()
    server.run()