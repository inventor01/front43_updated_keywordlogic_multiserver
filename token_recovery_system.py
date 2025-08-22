"""
Token Recovery System - Catch missed tokens while maintaining early detection

This system provides multiple layers of token detection:
1. Real-time monitoring (current system)
2. Historical backfill scanning
3. Continuous gap detection
4. Smart retry mechanisms
"""

import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
import requests
from enhanced_token_detector import EnhancedTokenDetector
from market_data_api import MarketDataAPI

class TokenRecoverySystem:
    def __init__(self, alchemy_scraper, discord_notifier, config_manager):
        self.alchemy_scraper = alchemy_scraper
        self.discord_notifier = discord_notifier
        self.config_manager = config_manager
        self.market_data_api = MarketDataAPI()
        self.detected_tokens = set()
        self.last_scan_time = None
        self.logger = logging.getLogger(__name__)
        
        # Recovery settings
        self.max_recovery_age = 3600  # 1 hour max recovery window
        self.backfill_interval = 300   # 5 minutes between backfill scans
        self.gap_threshold = 180       # 3 minutes gap triggers recovery
        
    def start_recovery_monitoring(self):
        """Start continuous recovery monitoring alongside real-time detection"""
        self.logger.info("🔄 Starting Token Recovery System")
        self.logger.info(f"   📅 Recovery window: {self.max_recovery_age/60:.0f} minutes")
        self.logger.info(f"   🔍 Backfill interval: {self.backfill_interval/60:.0f} minutes")
        self.logger.info(f"   ⚠️ Gap threshold: {self.gap_threshold/60:.0f} minutes")
        
        # Initial backfill on startup
        self.perform_startup_backfill()
        
        # Set ongoing recovery monitoring
        self.last_scan_time = time.time()
        
    def perform_startup_backfill(self):
        """Perform backfill scan when system starts to catch missed tokens"""
        self.logger.info("🚀 STARTUP BACKFILL: Scanning for missed tokens")
        
        # Calculate backfill window (1 hour max)
        current_time = time.time()
        backfill_start = current_time - self.max_recovery_age
        
        self.logger.info(f"   📅 Backfill window: {datetime.fromtimestamp(backfill_start)} to {datetime.fromtimestamp(current_time)}")
        
        # Scan recent transactions for missed tokens
        missed_tokens = self.scan_historical_tokens(backfill_start, current_time)
        
        if missed_tokens:
            self.logger.info(f"🎯 RECOVERY: Found {len(missed_tokens)} potentially missed tokens")
            self.process_recovered_tokens(missed_tokens, recovery_type="startup_backfill")
        else:
            self.logger.info("✅ RECOVERY: No missed tokens found in backfill window")
    
    def detect_monitoring_gap(self, current_time: float) -> bool:
        """Detect if there was a gap in monitoring that needs recovery"""
        if not self.last_scan_time:
            return False
            
        gap_duration = current_time - self.last_scan_time
        
        if gap_duration > self.gap_threshold:
            self.logger.warning(f"⚠️ MONITORING GAP DETECTED: {gap_duration:.1f}s gap (threshold: {self.gap_threshold}s)")
            return True
            
        return False
    
    def perform_gap_recovery(self):
        """Recover tokens missed during a monitoring gap"""
        current_time = time.time()
        gap_start = self.last_scan_time
        
        self.logger.info(f"🔧 GAP RECOVERY: Scanning {gap_start} to {current_time}")
        
        # Scan the gap period for missed tokens
        missed_tokens = self.scan_historical_tokens(gap_start, current_time)
        
        if missed_tokens:
            self.logger.info(f"🎯 GAP RECOVERY: Found {len(missed_tokens)} missed tokens")
            self.process_recovered_tokens(missed_tokens, recovery_type="gap_recovery")
        
        self.last_scan_time = current_time
    
    def scan_historical_tokens(self, start_time: float, end_time: float) -> List[Dict]:
        """Scan historical period for tokens that might have been missed"""
        try:
            # Use DexScreener to find tokens created in the time window
            missed_tokens = []
            
            # Convert timestamps to DexScreener format
            start_ms = int(start_time * 1000)
            end_ms = int(end_time * 1000)
            
            # Search for LetsBonk tokens in the time window
            search_url = "https://api.dexscreener.com/latest/dex/search"
            params = {
                'q': 'bonk',
                'chainIds': 'solana'
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                for pair in pairs:
                    try:
                        # Check if token is LetsBonk (address ends with 'bonk')
                        token_address = pair.get('baseToken', {}).get('address', '')
                        if not token_address.endswith('bonk'):
                            continue
                        
                        # Check if token was created in our time window
                        created_at = pair.get('pairCreatedAt', 0)
                        if start_ms <= created_at <= end_ms:
                            # Check if we already detected this token
                            if token_address not in self.detected_tokens:
                                token_info = {
                                    'address': token_address,
                                    'name': pair.get('baseToken', {}).get('name', 'Unknown'),
                                    'symbol': pair.get('baseToken', {}).get('symbol', 'TOKEN'),
                                    'created_timestamp': created_at / 1000,
                                    'market_cap': pair.get('fdv', 0),
                                    'recovery_age': time.time() - (created_at / 1000)
                                }
                                missed_tokens.append(token_info)
                                
                    except Exception as e:
                        self.logger.error(f"Error processing pair: {e}")
                        continue
                        
            return missed_tokens
            
        except Exception as e:
            self.logger.error(f"Error scanning historical tokens: {e}")
            return []
    
    def process_recovered_tokens(self, tokens: List[Dict], recovery_type: str):
        """Process tokens found during recovery with appropriate notifications"""
        keywords = self.config_manager.get_keywords()
        
        for token in tokens:
            try:
                # Check keyword matching
                token_name = token['name'].lower()
                matched_keywords = []
                
                for keyword in keywords:
                    if keyword.lower() in token_name:
                        matched_keywords.append(keyword)
                
                if matched_keywords:
                    # Calculate recovery metrics
                    recovery_age_minutes = token['recovery_age'] / 60
                    
                    # Send recovery notification
                    self.send_recovery_notification(token, matched_keywords, recovery_type, recovery_age_minutes)
                    
                    # Mark as detected to avoid duplicates
                    self.detected_tokens.add(token['address'])
                    
                    self.logger.info(f"📢 RECOVERY NOTIFICATION: {token['name']} (age: {recovery_age_minutes:.1f}m)")
                
            except Exception as e:
                self.logger.error(f"Error processing recovered token {token.get('address', 'unknown')}: {e}")
    
    async def send_recovery_notification(self, token: Dict, keywords: List[str], recovery_type: str, age_minutes: float):
        """Send Discord notification for recovered token"""
        try:
            # Enhanced notification with recovery context
            embed_data = {
                'title': f"🔄 RECOVERED TOKEN: {token['name']}",
                'description': f"Token missed during {recovery_type.replace('_', ' ').title()}",
                'color': 0xFFA500,  # Orange for recovery
                'fields': [
                    {
                        'name': '🎯 Matched Keywords',
                        'value': ', '.join(keywords),
                        'inline': False
                    },
                    {
                        'name': '⏰ Recovery Age',
                        'value': f"{age_minutes:.1f} minutes old when recovered",
                        'inline': True
                    },
                    {
                        'name': '💰 Market Cap',
                        'value': f"${token.get('market_cap', 0):,.0f}",
                        'inline': True
                    },
                    {
                        'name': '📍 Contract Address',
                        'value': f"`{token['address']}`",
                        'inline': False
                    },
                    {
                        'name': '🔗 Trading Links',
                        'value': f"• [LetsBonk.fun](https://letsbonk.fun/trade/{token['address']})\n"
                                f"• [DexScreener](https://dexscreener.com/solana/{token['address']})\n"
                                f"• [SolScan](https://solscan.io/token/{token['address']})",
                        'inline': False
                    }
                ],
                'footer': {
                    'text': f"Recovery System • {recovery_type.replace('_', ' ').title()}"
                }
            }
            
            await self.discord_notifier.send_embed_notification(embed_data)
            
        except Exception as e:
            self.logger.error(f"Error sending recovery notification: {e}")
    
    def should_perform_backfill(self) -> bool:
        """Check if it's time to perform periodic backfill"""
        if not hasattr(self, 'last_backfill_time'):
            self.last_backfill_time = 0
            
        current_time = time.time()
        return (current_time - self.last_backfill_time) > self.backfill_interval
    
    def perform_periodic_backfill(self):
        """Perform periodic backfill to catch any missed tokens"""
        current_time = time.time()
        backfill_start = current_time - self.backfill_interval
        
        self.logger.info(f"🔄 PERIODIC BACKFILL: Scanning last {self.backfill_interval/60:.0f} minutes")
        
        missed_tokens = self.scan_historical_tokens(backfill_start, current_time)
        
        if missed_tokens:
            self.logger.info(f"🎯 PERIODIC RECOVERY: Found {len(missed_tokens)} missed tokens")
            self.process_recovered_tokens(missed_tokens, recovery_type="periodic_backfill")
        
        self.last_backfill_time = current_time
    
    def update_monitoring_timestamp(self):
        """Update last monitoring timestamp to track gaps"""
        self.last_scan_time = time.time()
    
    def get_recovery_stats(self) -> Dict:
        """Get recovery system statistics"""
        return {
            'detected_tokens_count': len(self.detected_tokens),
            'last_scan_time': self.last_scan_time,
            'max_recovery_age_minutes': self.max_recovery_age / 60,
            'backfill_interval_minutes': self.backfill_interval / 60,
            'gap_threshold_minutes': self.gap_threshold / 60
        }