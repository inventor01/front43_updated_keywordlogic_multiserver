#!/usr/bin/env python3
"""
Enhanced Notification System with Duplicate Prevention
Combines the best features from multiple notification systems with robust deduplication
"""

import logging
import psycopg2
import os
import time
import json
import requests
from typing import Dict, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EnhancedNotificationSystem:
    """Enhanced notification system with comprehensive duplicate prevention and rich formatting"""
    
    def __init__(self, webhook_url: str = None):
        self.database_url = os.getenv('DATABASE_URL')
        self.webhook_url = webhook_url or os.getenv('DISCORD_WEBHOOK_URL')
        self.last_send_time = 0
        
        # Blocked tokens list (from original discord_notifier.py)
        self.blocked_tokens = {
            "EK7Ko9zmrfanDz98UnbWB9zkDPFV3Mcpx84t1DS2bonk",
            "7Zje1wV3r5sq8JEvJ1jFWifmSZe6CSBLRz4prFSXbonk", 
            "AHX7mj5Re2AwfvDgQUdVqEidQKHfH4tuxhdaLyLnbonk",
            "AVMMEP3WRxU63kyL5tAMCFPkwui36ZND932bBDXUbonk",
            "4EPMN1CVGmWmxF4bBP4Nt4TjD2m5KTjWGMDDrt38bonk",
            "3ZWWatVxckSWHm1avfC5UFyHa4nN9x46KfhWq4Tqbonk"
        }
    
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url)
    
    def _rate_limit(self) -> None:
        """Implement rate limiting for Discord webhooks"""
        current_time = time.time()
        time_since_last = current_time - self.last_send_time
        min_interval = 1.0  # Minimum 1 second between Discord messages
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
            
        self.last_send_time = time.time()
    
    def has_been_notified(self, token_address: str, notification_type: str = 'discord', 
                         user_id: str = 'system') -> bool:
        """Check if token has already been notified to prevent duplicates"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Check if notification already exists
            cursor.execute('''
                SELECT token_address FROM notified_tokens 
                WHERE token_address = %s 
                AND notification_type = %s 
                AND user_id = %s
            ''', (token_address, notification_type, user_id))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error checking notification status: {e}")
            # If we can't check, assume not notified to avoid missing notifications
            return False
    
    def mark_as_notified(self, token_address: str, token_name: str, 
                        notification_type: str = 'discord', user_id: str = 'system') -> bool:
        """Mark token as notified to prevent future duplicates"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO notified_tokens 
                (token_address, token_name, notification_type, user_id, notified_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (token_address, notification_type, user_id) 
                DO NOTHING
            ''', (token_address, token_name, notification_type, user_id, datetime.now()))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking token as notified: {e}")
            return False
    
    def fetch_market_data(self, token_address: str) -> Dict:
        """Fetch real-time market data from DexScreener with enhanced logging"""
        try:
            dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            logger.info(f"📊 Fetching market data for {token_address[:10]}...")
            
            response = requests.get(dex_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs') if data else None
                
                if pairs and len(pairs) > 0:
                    logger.info(f"📊 Found {len(pairs)} pairs for {token_address[:10]}...")
                    
                    # Get the pair with highest liquidity (or first if no liquidity)
                    try:
                        best_pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0)) if x.get('liquidity') else 0)
                    except:
                        best_pair = pairs[0]
                    
                    market_data = {
                        'price': float(best_pair.get('priceUsd', 0)),
                        'market_cap': float(best_pair.get('marketCap', 0)),
                        'volume_24h': float(best_pair.get('volume', {}).get('h24', 0)),
                        'liquidity': float(best_pair.get('liquidity', {}).get('usd', 0)),
                        'price_change_24h': float(best_pair.get('priceChange', {}).get('h24', 0))
                    }
                    
                    logger.info(f"✅ Market data loaded: MC=${market_data['market_cap']:.0f}, Price=${market_data['price']:.8f}")
                    return market_data
                else:
                    logger.warning(f"⚠️ No pairs found for {token_address[:10]}... (token might be too new)")
            else:
                logger.warning(f"⚠️ DexScreener API error {response.status_code} for {token_address[:10]}...")
                    
        except Exception as e:
            logger.warning(f"❌ Market data fetch failed for {token_address[:10]}...: {e}")
        
        return {}
    
    def calculate_age_display(self, created_timestamp: float) -> str:
        """Calculate accurate age display"""
        if not created_timestamp or created_timestamp <= 0:
            return "Unknown"
        
        current_time = time.time()
        
        # Handle milliseconds vs seconds
        if created_timestamp > 1e12:
            normalized_timestamp = created_timestamp / 1000.0
        else:
            normalized_timestamp = created_timestamp
        
        age_seconds = current_time - normalized_timestamp
        
        # Calculate age display
        if age_seconds < 60:
            return f"{age_seconds:.0f}s ago"
        elif age_seconds < 3600:
            return f"{age_seconds/60:.0f}m {age_seconds%60:.0f}s ago"
        else:
            return f"{age_seconds/3600:.0f}h {(age_seconds%3600)/60:.0f}m ago"
    
    def format_market_cap(self, market_cap: float) -> str:
        """Format market cap for display"""
        if market_cap >= 1_000_000:
            return f"${market_cap/1_000_000:.1f}M"
        elif market_cap >= 1_000:
            return f"${market_cap/1_000:.0f}K"
        else:
            return f"${market_cap:.0f}"
    
    def send_enhanced_token_notification(self, token_data: Dict, matched_keyword: str = None) -> bool:
        """
        Send enhanced token notification with comprehensive duplicate prevention
        
        Args:
            token_data: Dictionary containing token information
            matched_keyword: The keyword that matched this token
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        try:
            token_address = token_data.get('address', '')
            token_name = token_data.get('name', f'Token {token_address[-6:] if token_address else "Unknown"}')
            
            # STEP 1: Emergency block check
            if token_address in self.blocked_tokens:
                logger.error(f"🚨 BLOCKED TOKEN: {token_address} ({token_name}) - USER COMPLAINED")
                return False
            
            # STEP 2: Duplicate check
            if self.has_been_notified(token_address):
                logger.info(f"⚠️ DUPLICATE PREVENTED: {token_name} ({token_address[:10]}...) already notified")
                return False
            
            # STEP 3: Rate limiting
            self._rate_limit()
            
            # STEP 4: Prepare token information
            symbol = token_data.get('symbol', 'UNK')
            age_display = self.calculate_age_display(token_data.get('created_timestamp', 0))
            
            # STEP 5: Fetch real-time market data
            market_data = self.fetch_market_data(token_address)
            
            # STEP 6: Create rich embed with enhanced formatting
            embed = {
                "title": f"🚨 NEW TOKEN DETECTED",
                "description": f"**{token_name}** ({symbol})\n\n`{token_address}`",
                "color": 0x00ff00,
                "timestamp": datetime.utcnow().isoformat(),
                "fields": [
                    {
                        "name": "📊 Token Info",
                        "value": f"**Name:** {token_name}\n**Symbol:** {symbol}\n**Age:** {age_display}",
                        "inline": True
                    }

                ]
            }
            
            # Market data field with MARKET CAP prominently displayed first
            market_value = ""
            if market_data:
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
                    market_value += f"💰 **MARKET CAP:** Loading...\n"
                
                if market_data.get('price'):
                    market_value += f"💵 **Price:** ${market_data['price']:.8f}\n"
                if market_data.get('volume_24h'):
                    vol = market_data['volume_24h']
                    if vol >= 1_000_000:
                        market_value += f"📊 **24h Volume:** ${vol/1_000_000:.1f}M\n"
                    elif vol >= 1_000:
                        market_value += f"📊 **24h Volume:** ${vol/1_000:.0f}K\n"
                    else:
                        market_value += f"📊 **24h Volume:** ${vol:,.0f}\n"
                if market_data.get('price_change_24h'):
                    change = market_data['price_change_24h']
                    change_emoji = "📈" if change >= 0 else "📉"
                    market_value += f"📈 **24h Change:** {change_emoji} {change:+.2f}%"
            
            # Always show market data field with market cap prominently displayed
            embed["fields"].append({
                "name": "💰 Live Market Data",
                "value": market_value or "💰 **MARKET CAP:** Fetching...\n💵 **Price:** Loading...\n📊 **Volume:** Check DexScreener",
                "inline": True
            })
            
            # Platform info field (corrected source attribution)
            embed["fields"].append({
                "name": "🚀 Platform",
                "value": "**Source:** PumpFun\n**Network:** Solana",
                "inline": True
            })
            
            # Trading links field with PumpFun (corrected source attribution)
            links_text = f"[🚀 Trade on PumpFun](https://pump.fun/{token_address})\n"
            links_text += f"[📊 DexScreener](https://dexscreener.com/solana/{token_address})\n"
            links_text += f"[🔍 SolScan](https://solscan.io/token/{token_address})\n"
            links_text += f"[📋 Copy Address](https://solscan.io/token/{token_address})"
            
            embed["fields"].append({
                "name": "🔗 Trading Links",
                "value": links_text,
                "inline": False
            })
            
            # Social media links (if available)
            social_links = token_data.get('social_links', [])
            if social_links:
                social_text = ""
                for link in social_links[:5]:  # Limit to 5 links
                    if "x.com" in link or "twitter.com" in link:
                        social_text += f"[Twitter/X]({link})\n"
                    elif "tiktok.com" in link:
                        social_text += f"[TikTok]({link})\n"
                    elif "t.me" in link:
                        social_text += f"[Telegram]({link})\n"
                    elif "discord" in link:
                        social_text += f"[Discord]({link})\n"
                    elif "instagram.com" in link:
                        social_text += f"[Instagram]({link})\n"
                    elif "youtube.com" in link:
                        social_text += f"[YouTube]({link})\n"
                    else:
                        domain = link.split("//")[-1].split("/")[0]
                        social_text += f"[{domain}]({link})\n"
                
                if social_text:
                    embed["fields"].append({
                        "name": "📱 Social Media Links", 
                        "value": social_text.strip(),
                        "inline": False
                    })
            
            # Matched keyword field
            if matched_keyword:
                embed["fields"].append({
                    "name": "🎯 Matched Keyword",
                    "value": f"`{matched_keyword}`",
                    "inline": True
                })
            
            # Footer
            embed["footer"] = {
                "text": "⚡ Real-time token monitoring • $0/month monitoring cost"
            }
            
            # STEP 7: Send webhook notification
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 204:
                # STEP 8: Mark as notified to prevent duplicates
                self.mark_as_notified(token_address, token_name)
                
                logger.info(f"✅ NOTIFICATION SENT: {token_name} ({token_address[:10]}...)")
                if matched_keyword:
                    logger.info(f"🎯 KEYWORD MATCH: {matched_keyword}")
                
                return True
            else:
                logger.error(f"❌ Webhook failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Notification error: {e}")
            return False
    
    def cleanup_old_notifications(self, days_old: int = 7) -> None:
        """Clean up old notification records to prevent database bloat"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            cursor.execute('''
                DELETE FROM notified_tokens 
                WHERE notified_at < %s
            ''', (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            if deleted_count > 0:
                logger.info(f"🧹 Cleaned up {deleted_count} old notification records")
                
        except Exception as e:
            logger.error(f"Error cleaning up notifications: {e}")
    
    def get_notification_stats(self) -> Dict:
        """Get notification statistics"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Total notifications today
            cursor.execute('''
                SELECT COUNT(*) FROM notified_tokens 
                WHERE notified_at >= CURRENT_DATE
            ''')
            today_count = cursor.fetchone()[0]
            
            # Total notifications this week
            cursor.execute('''
                SELECT COUNT(*) FROM notified_tokens 
                WHERE notified_at >= CURRENT_DATE - INTERVAL '7 days'
            ''')
            week_count = cursor.fetchone()[0]
            
            # Most recent notification
            cursor.execute('''
                SELECT token_name, notified_at FROM notified_tokens 
                ORDER BY notified_at DESC LIMIT 1
            ''')
            recent = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return {
                'today': today_count,
                'week': week_count,
                'recent_token': recent[0] if recent else None,
                'recent_time': recent[1] if recent else None
            }
            
        except Exception as e:
            logger.error(f"Error getting notification stats: {e}")
            return {}

# Create a singleton instance for easy import
enhanced_notifier = EnhancedNotificationSystem()