#!/usr/bin/env python3
"""
Link Sniper System - Monitor tokens for specific social media links
Similar to keyword sniper but searches for exact URL matches (1:1)
"""

import psycopg2
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
import time
import asyncio

logger = logging.getLogger(__name__)

class LinkSniper:
    """Monitor new tokens for specific social media links and auto-buy when found"""
    
    def __init__(self, discord_notifier=None):
        self.discord_notifier = discord_notifier
        self.database_url = os.getenv('DATABASE_URL')
        self.link_configs = {}  # Cache for active link configurations
        self.init_database()
        self.load_link_configs()
        
    def init_database(self):
        """Initialize database tables for link sniper"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # Create link_sniper_configs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS link_sniper_configs (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    target_link TEXT NOT NULL,
                    max_market_cap DECIMAL(15,2) DEFAULT NULL,
                    buy_amount DECIMAL(10,6) DEFAULT 0.01,
                    enabled BOOLEAN DEFAULT true,
                    notify_only BOOLEAN DEFAULT false,
                    slippage DECIMAL(5,2) DEFAULT 10.0,
                    priority_fee DECIMAL(10,6) DEFAULT 0.001,
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_used TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_id, target_link)
                )
            """)
            
            # Create link_sniper_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS link_sniper_history (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    target_link TEXT NOT NULL,
                    token_address TEXT NOT NULL,
                    token_name TEXT,
                    token_symbol TEXT,
                    matched_link TEXT,
                    buy_amount DECIMAL(10,6),
                    market_cap DECIMAL(15,2),
                    transaction_hash TEXT,
                    success BOOLEAN DEFAULT false,
                    error_message TEXT,
                    executed_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("✅ Link sniper database tables initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize link sniper database: {e}")
    
    def load_link_configs(self):
        """Load active link configurations from database"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, target_link, max_market_cap, buy_amount, enabled, notify_only, slippage, priority_fee
                FROM link_sniper_configs 
                WHERE enabled = true
            """)
            
            rows = cursor.fetchall()
            self.link_configs.clear()
            
            for user_id, target_link, max_market_cap, buy_amount, enabled, notify_only, slippage, priority_fee in rows:
                if user_id not in self.link_configs:
                    self.link_configs[user_id] = []
                
                self.link_configs[user_id].append({
                    'target_link': target_link,
                    'max_market_cap': float(max_market_cap) if max_market_cap is not None else None,
                    'buy_amount': float(buy_amount),
                    'enabled': enabled,
                    'notify_only': notify_only,
                    'slippage': float(slippage),
                    'priority_fee': float(priority_fee)
                })
            
            total_configs = sum(len(configs) for configs in self.link_configs.values())
            logger.info(f"📋 Loaded {total_configs} active link sniper configs for {len(self.link_configs)} users")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to load link configurations: {e}")
    
    def add_link_config(self, user_id: int, target_link: str, max_market_cap: Optional[float] = None, 
                       buy_amount: float = 0.01, notify_only: bool = True, slippage: float = 10.0, 
                       priority_fee: float = 0.001) -> bool:
        """Add new link sniper configuration"""
        try:
            # Check for duplicates first
            existing_configs = self.get_user_link_configs(user_id)
            for config in existing_configs:
                if config['target_link'].lower() == target_link.lower():
                    logger.info(f"URL '{target_link}' already exists for user {user_id}")
                    return False  # Return False to indicate duplicate
            
            # No default market cap limits - user must explicitly set them
            # max_market_cap remains None (no limit) unless user specifies otherwise
            
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO link_sniper_configs 
                (user_id, target_link, max_market_cap, buy_amount, notify_only, slippage, priority_fee, enabled)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, target_link) 
                DO UPDATE SET 
                    max_market_cap = EXCLUDED.max_market_cap,
                    buy_amount = EXCLUDED.buy_amount,
                    notify_only = EXCLUDED.notify_only,
                    slippage = EXCLUDED.slippage,
                    priority_fee = EXCLUDED.priority_fee,
                    enabled = EXCLUDED.enabled,
                    last_used = NOW()
            """, (user_id, target_link, max_market_cap, buy_amount, notify_only, slippage, priority_fee, True))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Reload configurations
            self.load_link_configs()
            
            logger.info(f"✅ Added link sniper config for user {user_id}: {target_link[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add link configuration: {e}")
            return False
    
    def remove_link_config(self, user_id: int, target_link: str) -> bool:
        """Remove link sniper configuration using normalized URL matching"""
        try:
            # Normalize the input URL for matching
            normalized_input = self._normalize_url(target_link)
            
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # First, try exact match
            cursor.execute("""
                DELETE FROM link_sniper_configs 
                WHERE user_id = %s AND target_link = %s
            """, (user_id, target_link))
            
            deleted_count = cursor.rowcount
            
            # If no exact match, try normalized matching
            if deleted_count == 0:
                # Get all URLs for this user and find normalized match
                cursor.execute("""
                    SELECT target_link FROM link_sniper_configs 
                    WHERE user_id = %s
                """, (user_id,))
                
                user_urls = cursor.fetchall()
                matched_url = None
                
                for (stored_url,) in user_urls:
                    if self._normalize_url(stored_url) == normalized_input:
                        matched_url = stored_url
                        break
                
                if matched_url:
                    cursor.execute("""
                        DELETE FROM link_sniper_configs 
                        WHERE user_id = %s AND target_link = %s
                    """, (user_id, matched_url))
                    deleted_count = cursor.rowcount
                    logger.info(f"🔍 Found normalized match: '{target_link}' → '{matched_url}'")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if deleted_count > 0:
                self.load_link_configs()
                logger.info(f"✅ Removed link sniper config for user {user_id}: {target_link[:50]}...")
                return True
            else:
                logger.warning(f"⚠️ No link config found to remove for user {user_id}: {target_link[:50]}...")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to remove link configuration: {e}")
            return False
    
    def remove_multiple_link_configs(self, user_id: int, target_links: List[str]) -> tuple:
        """Remove multiple link sniper configurations using normalized URL matching"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            removed_links = []
            failed_links = []
            
            # Get all existing URLs for this user once
            cursor.execute("""
                SELECT target_link FROM link_sniper_configs 
                WHERE user_id = %s
            """, (user_id,))
            
            existing_urls = [row[0] for row in cursor.fetchall()]
            
            for target_link in target_links:
                # Try exact match first
                cursor.execute("""
                    DELETE FROM link_sniper_configs 
                    WHERE user_id = %s AND target_link = %s
                """, (user_id, target_link))
                
                if cursor.rowcount > 0:
                    removed_links.append(target_link)
                else:
                    # Try normalized matching
                    normalized_input = self._normalize_url(target_link)
                    matched_url = None
                    
                    for stored_url in existing_urls:
                        if self._normalize_url(stored_url) == normalized_input:
                            matched_url = stored_url
                            break
                    
                    if matched_url:
                        cursor.execute("""
                            DELETE FROM link_sniper_configs 
                            WHERE user_id = %s AND target_link = %s
                        """, (user_id, matched_url))
                        
                        if cursor.rowcount > 0:
                            removed_links.append(target_link)
                            existing_urls.remove(matched_url)  # Remove from list to avoid double-deletion
                            logger.info(f"🔍 Normalized match: '{target_link}' → '{matched_url}'")
                        else:
                            failed_links.append(target_link)
                    else:
                        failed_links.append(target_link)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            if removed_links:
                self.load_link_configs()
                logger.info(f"✅ Bulk removed {len(removed_links)} link sniper configs for user {user_id}")
            
            return removed_links, failed_links
                
        except Exception as e:
            logger.error(f"❌ Failed to remove multiple link configurations: {e}")
            return [], target_links
    
    def get_user_link_configs(self, user_id: int) -> List[Dict]:
        """Get all link configurations for a user"""
        return self.link_configs.get(user_id, [])
    
    def clear_user_link_configs(self, user_id: int) -> int:
        """Clear all link configurations for a user"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM link_sniper_configs 
                WHERE user_id = %s
            """, (user_id,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            if deleted_count > 0:
                self.load_link_configs()
                logger.info(f"✅ Cleared {deleted_count} link sniper configs for user {user_id}")
            
            return deleted_count
                
        except Exception as e:
            logger.error(f"❌ Failed to clear link configurations: {e}")
            return 0
    
    def toggle_user_link_sniper(self, user_id: int, enabled: bool) -> bool:
        """Enable or disable all link sniper configs for a user"""
        return self.toggle_link_sniper(user_id, enabled)
    
    def toggle_link_sniper(self, user_id: int, enabled: bool) -> bool:
        """Enable or disable all link sniper configs for a user"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE link_sniper_configs 
                SET enabled = %s, last_used = NOW()
                WHERE user_id = %s
            """, (enabled, user_id))
            
            updated_count = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            if updated_count > 0:
                self.load_link_configs()
                status = "enabled" if enabled else "disabled"
                logger.info(f"✅ {status.title()} link sniper for user {user_id} ({updated_count} configs)")
                return True
            else:
                logger.warning(f"⚠️ No link configs found for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to toggle link sniper: {e}")
            return False
    
    def check_token_for_links(self, token: Dict[str, Any], token_links: List[str]) -> Optional[Dict]:
        """Check if token contains any monitored links with enhanced URL matching"""
        try:
            if not token_links or not self.link_configs:
                return None
            
            # Check each user's link configurations
            for user_id, user_configs in self.link_configs.items():
                for config in user_configs:
                    if not config['enabled']:
                        continue
                    
                    target_link = config['target_link']
                    normalized_target = self._normalize_url(target_link)
                    
                    # Enhanced URL matching with normalization
                    for token_link in token_links:
                        normalized_token = self._normalize_url(token_link)
                        
                        # Method 1: Exact match after normalization
                        if normalized_target == normalized_token:
                            logger.info(f"🎯 EXACT LINK MATCH: {target_link[:50]}... in token {token.get('name', 'unknown')}")
                            return self._create_match_result(user_id, config, target_link, token)
                        
                        # Method 2: Check if URLs are from same post/status (for X.com/Twitter)
                        if self._are_same_social_post(normalized_target, normalized_token):
                            logger.info(f"🎯 SOCIAL POST MATCH: {target_link[:50]}... in token {token.get('name', 'unknown')}")
                            return self._create_match_result(user_id, config, target_link, token)
                        
                        # Method 3: Check if target is substring of token link (for parameter variations)
                        if normalized_target in normalized_token or normalized_token in normalized_target:
                            # Additional validation to ensure it's actually the same content
                            if self._validate_substring_match(normalized_target, normalized_token):
                                logger.info(f"🎯 SUBSTRING LINK MATCH: {target_link[:50]}... in token {token.get('name', 'unknown')}")
                                return self._create_match_result(user_id, config, target_link, token)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error checking token for links: {e}")
            return None
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for consistent matching by removing tracking parameters and fragments"""
        if not url:
            return ""
        
        normalized = url.strip()
        
        # Remove fragment identifiers first
        if '#' in normalized:
            normalized = normalized.split('#')[0]
        
        # Handle query parameters
        if '?' in normalized:
            base_url, query_string = normalized.split('?', 1)
            
            # Remove trailing slash from base URL before processing
            base_url = base_url.rstrip('/')
            
            # Split query parameters
            params = query_string.split('&')
            clean_params = []
            
            for param in params:
                # Skip common tracking parameters but preserve others
                if not any(param.startswith(track) for track in ['s=', 't=', 'utm_', '_t=', '_r=']):
                    clean_params.append(param)
            
            # Rebuild URL
            if clean_params:
                normalized = base_url + '?' + '&'.join(clean_params)
            else:
                normalized = base_url
        else:
            # No query parameters, just remove trailing slash
            normalized = normalized.rstrip('/')
        
        return normalized
    
    def _are_same_social_post(self, url1: str, url2: str) -> bool:
        """Check if two URLs point to the same social media post"""
        # Extract status/post IDs for Twitter/X posts
        if 'x.com' in url1 or 'twitter.com' in url1:
            status_id1 = self._extract_twitter_status_id(url1)
            status_id2 = self._extract_twitter_status_id(url2)
            if status_id1 and status_id2:
                return status_id1 == status_id2
        
        # Extract TikTok video IDs
        if 'tiktok.com' in url1:
            tiktok_id1 = self._extract_tiktok_video_id(url1)
            tiktok_id2 = self._extract_tiktok_video_id(url2)
            if tiktok_id1 and tiktok_id2:
                return tiktok_id1 == tiktok_id2
        
        return False
    
    def _extract_twitter_status_id(self, url: str) -> str:
        """Extract Twitter/X status ID from URL"""
        import re
        match = re.search(r'/status/(\d+)', url)
        return match.group(1) if match else ""
    
    def _extract_tiktok_video_id(self, url: str) -> str:
        """Extract TikTok video ID from URL"""
        import re
        match = re.search(r'/video/(\d+)', url)
        return match.group(1) if match else ""
    
    def _validate_substring_match(self, target: str, token: str) -> bool:
        """Validate that substring match is meaningful (not just domain match)"""
        # Ensure the match includes more than just the domain
        if len(target) < 20 or len(token) < 20:
            return False
        
        # Check if they share a significant portion (at least 80% overlap)
        shorter = min(len(target), len(token))
        longer = max(len(target), len(token))
        
        # If length difference is too large, probably not the same content
        if longer / shorter > 1.5:
            return False
        
        return True
    
    def _create_match_result(self, user_id: int, config: Dict, target_link: str, token: Dict) -> Dict:
        """Create match result with market cap validation"""
        # Check market cap limit (only for auto-buy, not notifications)
        market_cap = token.get('market_cap', 0)
        if not config['notify_only'] and config['max_market_cap'] is not None and market_cap > config['max_market_cap']:
            logger.info(f"⚠️ Market cap ${market_cap:,.0f} exceeds limit ${config['max_market_cap']:,.0f}")
            return {}
        
        return {
            'user_id': user_id,
            'config': config,
            'matched_link': target_link,
            'target_link': target_link
        }
    
    def record_snipe_attempt(self, user_id: int, target_link: str, token: Dict, 
                           matched_link: str, success: bool, transaction_hash: str = "", 
                           error_message: str = "", buy_amount: float = 0.0):
        """Record link sniper attempt in database"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO link_sniper_history 
                (user_id, target_link, token_address, token_name, token_symbol, 
                 matched_link, buy_amount, market_cap, transaction_hash, success, error_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, target_link, token.get('address', ''), token.get('name', ''),
                token.get('symbol', ''), matched_link, float(buy_amount or 0.0), float(token.get('market_cap', 0)),
                str(transaction_hash or ''), success, str(error_message or '')
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"📝 Recorded link snipe attempt for {token.get('name', 'unknown')}")
            
        except Exception as e:
            logger.error(f"❌ Failed to record snipe attempt: {e}")
    
    def get_user_snipe_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get recent link sniper history for a user"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT target_link, token_name, token_symbol, token_address, matched_link,
                       buy_amount, market_cap, transaction_hash, success, error_message, executed_at
                FROM link_sniper_history 
                WHERE user_id = %s 
                ORDER BY executed_at DESC 
                LIMIT %s
            """, (user_id, limit))
            
            rows = cursor.fetchall()
            history = []
            
            for row in rows:
                history.append({
                    'target_link': row[0],
                    'token_name': row[1],
                    'token_symbol': row[2],
                    'token_address': row[3],
                    'matched_link': row[4],
                    'buy_amount': float(row[5]) if row[5] else 0,
                    'market_cap': float(row[6]) if row[6] else 0,
                    'transaction_hash': row[7],
                    'success': row[8],
                    'error_message': row[9],
                    'executed_at': row[10]
                })
            
            cursor.close()
            conn.close()
            
            return history
            
        except Exception as e:
            logger.error(f"❌ Failed to get snipe history: {e}")
            return []
    
    async def send_link_snipe_notification(self, user_id: int, token: Dict, matched_link: str, 
                                         transaction_hash: str, buy_amount: float, success: bool):
        """Send Discord notification for successful link snipe"""
        try:
            if not self.discord_notifier:
                return
            
            token_name = token.get('name', 'Unknown Token')
            token_symbol = token.get('symbol', 'UNK')
            token_address = token.get('address', '')
            market_cap = token.get('market_cap', 0)
            
            # Create embed for link snipe notification
            embed_data = {
                "title": "🔗 Link Sniper Success!",
                "description": f"Successfully purchased **{token_name}** ({token_symbol})",
                "color": 0x00ff00 if success else 0xff0000,
                "fields": [
                    {
                        "name": "🎯 Matched Link",
                        "value": f"[{matched_link[:50]}...]({matched_link})",
                        "inline": False
                    },
                    {
                        "name": "💰 Purchase Details",
                        "value": f"**Amount:** {buy_amount} SOL\n**Market Cap:** ${market_cap:,.0f}",
                        "inline": True
                    },
                    {
                        "name": "📊 Token Info",
                        "value": f"**Name:** {token_name}\n**Symbol:** {token_symbol}",
                        "inline": True
                    }
                ]
            }
            
            if transaction_hash:
                embed_data["fields"].append({
                    "name": "🔗 Transaction",
                    "value": f"[View on Solscan](https://solscan.io/tx/{transaction_hash})",
                    "inline": False
                })
            
            embed_data["footer"] = {
                "text": f"Link Sniper • {datetime.now().strftime('%H:%M:%S UTC')}"
            }
            
            # Send notification
            success = await self.discord_notifier.send_embed_async(embed_data)
            
            if success:
                logger.info(f"✅ Sent link snipe notification for {token_name}")
            else:
                logger.warning(f"❌ Failed to send link snipe notification")
                
        except Exception as e:
            logger.error(f"❌ Error sending link snipe notification: {e}")
    
    def clear_user_links(self, user_id: int) -> bool:
        """Clear all link configurations for a user"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM link_sniper_configs 
                WHERE user_id = %s
            """, (user_id,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            if deleted_count > 0:
                self.load_link_configs()
                logger.info(f"✅ Cleared {deleted_count} link configs for user {user_id}")
                return True
            else:
                logger.warning(f"⚠️ No link configs found for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to clear link configurations: {e}")
            return False