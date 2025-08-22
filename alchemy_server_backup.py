"""
Ultra-cost-optimized monitoring server using Alchemy API
Reduces costs from $100s/month to $0 while maintaining detection speed
"""

import os
import time
import logging
import threading
import json
import asyncio
from datetime import datetime, timezone
from flask import Flask, jsonify, request
from waitress import serve
from typing import Dict, List, Any
import discord
from discord.ext import commands
from discord import app_commands
from solana.rpc.api import Client
from cachetools import TTLCache
import base58
from solders.keypair import Keypair
from solders.pubkey import Pubkey as PublicKey

# Import existing components
from alchemy_letsbonk_scraper import AlchemyLetsBonkScraper
from new_token_only_monitor import NewTokenOnlyMonitor
# from letsbonk_api_monitor import LetsBonkAPIMonitor  # REMOVED - file doesn't exist
# from spl_websocket_monitor import SPLWebSocketMonitor  # REMOVED - file doesn't exist
from config_manager import ConfigManager
from discord_notifier import DiscordNotifier
# from social_media_aggregator import SocialMediaAggregator  # REMOVED - file doesn't exist
# from market_cap_alert_manager import MarketCapAlertManager  # DISABLED - outdated
from trading_engine import trader
from auto_sniper import AutoSniper
from auto_sell_monitor import AutoSellMonitor
# from sniper_commands import SniperCommands  # Integrated directly
from token_link_validator import TokenLinkValidator
from enhanced_letsbonk_scraper import EnhancedLetsBonkScraper
from automated_link_extractor import AutomatedLinkExtractor
from speed_optimized_monitor import SpeedOptimizedMonitor
from undo_manager import UndoManager
from token_recovery_system import TokenRecoverySystem
from cryptography.fernet import Fernet
import psycopg2
import hashlib
from keyword_attribution import KeywordAttributionManager
from uptime_manager import create_uptime_manager

# Initialize Solana RPC client with fallback endpoints
ALCHEMY_API_KEY = os.getenv('ALCHEMY_API_KEY', '877gH4oJoW3wJcEZpK6OxPMPBIlJhpS8')

def get_solana_client():
    """Get Solana RPC client with fallback endpoints"""
    endpoints = [
        f"https://solana-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}",
        "https://api.mainnet-beta.solana.com",
        "https://solana-api.projectserum.com",
        "https://rpc.ankr.com/solana"
    ]
    
    for endpoint in endpoints:
        try:
            test_client = Client(endpoint)
            # Test the connection
            test_client.get_slot()
            return test_client
        except Exception as e:
            logger.warning(f"RPC endpoint {endpoint} failed: {e}")
            continue
    
    # If all fail, return the primary endpoint anyway
    return Client(f"https://solana-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}")

client = get_solana_client()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alchemy_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AlchemyMonitoringServer:
    """Cost-optimized monitoring server using Alchemy's free tier"""
    
    def __init__(self):
        self.running = False
        self.monitoring_start_time = time.time()
        
        # Add missing Alchemy API key attribute
        self.alchemy_api_key = ALCHEMY_API_KEY
        
        # Initialize TTL cache system for memory management
        self.seen_token_addresses = TTLCache(maxsize=10000, ttl=60)  # 1-minute TTL
        self.processed_signatures = TTLCache(maxsize=5000, ttl=300)  # 5-minute TTL for signatures
        self.websocket_signatures = TTLCache(maxsize=5000, ttl=60)   # 1-minute TTL for WebSocket events
        self.permanently_rejected_tokens = set()  # Permanent blocklist for old tokens (prevents TTL cache reprocessing)
        
        # User wallet storage system with persistent database storage
        self.connected_wallets = {}  # user_id -> {'address': str, 'keypair': Keypair, 'connected_at': timestamp}
        
        # Initialize persistent wallet storage
        self.init_wallet_persistence()
        
        # Restore previously connected wallets from database
        self.restore_connected_wallets()
        
        # Initialize components
        self.config_manager = ConfigManager()
        
        # Initialize successful extractions tracking
        self.recent_successful_extractions = []
        
        # Load keywords from PostgreSQL first, fallback to file
        self.keywords = self._load_keywords_postgres_first()
        
        # Initialize keyword attribution manager
        try:
            self.keyword_attribution = KeywordAttributionManager()
            # Sync existing keywords with default attribution (only for keywords without existing attribution)
            self.keyword_attribution.sync_with_existing_keywords(self.keywords, "system", "System")
            logger.info("✅ Keyword attribution tracking initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize keyword attribution: {e}")
            self.keyword_attribution = None
            
        # Initialize uptime manager for 100% availability
        try:
            self.uptime_manager = create_uptime_manager(self)
            logger.info("✅ Uptime manager initialized - targeting 100% availability")
        except Exception as e:
            logger.error(f"❌ Failed to initialize uptime manager: {e}")
            self.uptime_manager = None
        
        # Initialize Alchemy scraper for token recovery system
        self.alchemy_scraper = AlchemyLetsBonkScraper()
        
        # Initialize link scraping statistics tracking
        self.link_scraping_stats = {
            'total_extractions_attempted': 0,
            'total_extractions_successful': 0,
            'browsercat_extractions': 0,
            'browsercat_successes': 0,
            'fallback_extractions': 0,
            'fallback_successes': 0,
            'url_matches_found': 0,
            'total_links_extracted': 0,
            'tokens_with_social_links': 0,
            'last_extraction_time': None,
            'extraction_errors': 0
        }
        
        # Initialize NEW TOKEN ONLY monitoring system (no transaction history)
        try:
            self.new_token_monitor = NewTokenOnlyMonitor(callback_func=self.process_tokens)
            logger.info("✅ NEW TOKEN ONLY monitor initialized - no transaction history scanning")
            logger.info("📡 Monitoring ONLY genuine new token creations as they happen")
        except Exception as e:
            logger.error(f"❌ Failed to initialize new token monitoring: {e}")
            raise
            
        # Initialize API-Free Social Media Scraper for cross-feed functionality
        try:
            from api_free_social_scraper import APIFreeSocialScraper
            self.api_free_social_scraper = APIFreeSocialScraper()
            logger.info("✅ API-Free Social Media Scraper initialized - Twitter, TikTok, Instagram, Reddit monitoring")
            logger.info("🔥 Cross-feed: 100k+ views/hour in last 3 hours threshold (no API keys required)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize API-free social media scraper: {e}")
            self.api_free_social_scraper = None
        
        # Initialize SPL Token Program WebSocket monitor for ultra-fast detection (DISABLED - module not available)
        # try:
        #     self.spl_websocket_monitor = SPLWebSocketMonitor(callback_func=self.process_spl_token_event)
        #     logger.info("✅ SPL WebSocket monitor initialized - real-time token program monitoring")
        #     logger.info("📡 WebSocket subscription to SPL Token Program for sub-second detection")
        # except Exception as e:
        #     logger.error(f"❌ Failed to initialize SPL WebSocket monitoring: {e}")
        self.spl_websocket_monitor = None  # Module not available in deployment
        
        # Initialize Discord notifier
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if webhook_url:
            self.discord_notifier = DiscordNotifier()
            logger.info("✅ Discord notifications configured")
        else:
            self.discord_notifier = None
            logger.warning("⚠️ No Discord webhook configured")
        
        # Initialize market data API for accurate market cap data
        self.market_data_api = None
        try:
            from market_data_api import MarketDataAPI
            self.market_data_api = MarketDataAPI()
            logger.info("✅ Market data API initialized (DexScreener)")
        except ImportError:
            logger.warning("Market data API not available")
        
        # Initialize DexScreener integration for new token detection
        self.dexscreener_integration = None
        try:
            from letsbonk_dexscreener_integration import LetsBonkDexScreenerIntegration
            self.dexscreener_integration = LetsBonkDexScreenerIntegration()
            logger.info("✅ DexScreener integration initialized for new token detection")
        except Exception as e:
            logger.warning(f"⚠️ DexScreener integration failed to initialize: {e}")
        
        # Initialize multi-source timestamp validator for consensus validation
        self.multi_source_validator = None
        try:
            from multi_source_timestamp_validator import MultiSourceTimestampValidator
            self.multi_source_validator = MultiSourceTimestampValidator()
            logger.info("✅ Multi-source timestamp validator initialized for consensus validation")
        except Exception as e:
            logger.warning(f"⚠️ Multi-source validator failed to initialize: {e}")
        
        # Initialize token link validator for social media validation
        self.token_link_validator = None
        try:
            self.token_link_validator = TokenLinkValidator()
            logger.info("✅ Token link validator initialized for social media checking")
        except Exception as e:
            logger.warning(f"⚠️ Token link validator failed to initialize: {e}")
        
        # Initialize LetsBonk enhanced scraper for advanced link detection
        self.letsbonk_scraper = None
        
        # Initialize automated link extractor for real-time social media monitoring
        self.automated_extractor = AutomatedLinkExtractor()
        logger.info("✅ Automated link extractor initialized for real-time social media monitoring")
        try:
            self.enhanced_scraper = EnhancedLetsBonkScraper()
            logger.info("✅ Enhanced LetsBonk scraper initialized with improved social media detection patterns")
        except Exception as e:
            logger.warning(f"⚠️ Enhanced LetsBonk scraper failed to initialize: {e}")
        
        # Initialize Enhanced Social Media Extractor (includes BrowserCat)
        self.social_extractor = None
        try:
            from enhanced_social_media_extractor import EnhancedSocialMediaExtractor
            self.social_extractor = EnhancedSocialMediaExtractor()
            browsercat_api_key = os.getenv('BROWSERCAT_API_KEY', 'e7MEbRx603vMtEJbqkCez2COCKkCT8IRPZZrKqmYCXs1MlOKJKDEbdSUzarmVCGR')
            if browsercat_api_key:
                logger.info("✅ Enhanced social media extractor initialized with BrowserCat Vue.js SPA rendering")
                logger.info("🎯 Will solve 'No social links found' issue for LetsBonk tokens using multiple methods")
            else:
                logger.info("💡 Enhanced social media extractor initialized with pattern detection only")
        except Exception as e:
            logger.warning(f"⚠️ Enhanced social media extractor failed to initialize: {e}")
            
        # Initialize NEW Advanced BrowserCat scraper for Vue.js SPA extraction
        self.advanced_browsercat_scraper = None
        try:
            from enhanced_browsercat_scraper import EnhancedBrowserCatScraper
            self.advanced_browsercat_scraper = EnhancedBrowserCatScraper()
            logger.info("✅ ADVANCED BROWSERCAT SCRAPER initialized - Vue.js SPA optimized with Playwright WebSocket")
            logger.info("🚀 Enhanced social media detection with JavaScript execution and multi-strategy extraction")
            logger.info("🎯 BREAKTHROUGH: Advanced BrowserCat successfully finds social links on Vue.js SPAs")
            logger.info("📊 Tested successfully: found 2 social links on disguise token (6CLbaDwo...)")
        except Exception as e:
            logger.error(f"❌ Advanced BrowserCat scraper failed to initialize: {e}")
            self.advanced_browsercat_scraper = None
        
        # Initialize speed-optimized monitor for sub-5s processing
        try:
            self.speed_monitor = SpeedOptimizedMonitor(callback_func=self.send_fast_notification)
            logger.info("🚀 Speed-optimized monitor initialized - targeting <5s processing with link detection")
        except Exception as e:
            logger.warning(f"⚠️ Speed monitor failed to initialize: {e}")
            self.speed_monitor = None
        
        # Market cap alerts temporarily disabled due to API compatibility issues
        self.market_cap_manager = None
        
        # Initialize auto-sniper
        try:
            self.auto_sniper = AutoSniper(
                trading_engine=trader,
                market_data_api=self.market_data_api,
                discord_notifier=self.discord_notifier
            )
            self.auto_sniper.update_connected_wallets(self.connected_wallets)
            self.auto_sniper.load_all_sniper_configs()
            logger.info("✅ Auto-sniper initialized with database integration and Discord notifications")
        except Exception as e:
            logger.error(f"❌ Failed to initialize auto-sniper: {e}")
            self.auto_sniper = None
        
        # Initialize link sniper for URL-based token monitoring
        try:
            from link_sniper import LinkSniper
            self.link_sniper = LinkSniper(discord_notifier=self.discord_notifier)
            logger.info("✅ Link sniper initialized for URL-based token monitoring")
        except Exception as e:
            logger.error(f"❌ Failed to initialize link sniper: {e}")
            self.link_sniper = None
        
        # Initialize undo manager
        self.undo_manager = UndoManager(
            config_manager=self.config_manager,
            link_sniper=self.link_sniper,
            max_history=50
        )
        logger.info("↩️ Undo manager initialized successfully")
        
        # Initialize Token Recovery System
        try:
            self.recovery_system = TokenRecoverySystem(
                alchemy_scraper=self.alchemy_scraper,
                discord_notifier=self.discord_notifier,
                config_manager=self.config_manager
            )
            logger.info("🔄 Token Recovery System initialized successfully")
            logger.info("   📅 Recovery window: 1 hour for missed tokens")
            logger.info("   🔍 Backfill interval: 5 minutes for continuous monitoring")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Token Recovery System: {e}")
            self.recovery_system = None
        
        # Initialize auto-sell monitor
        try:
            self.auto_sell_monitor = AutoSellMonitor(
                trading_engine=trader,
                market_data_api=self.market_data_api,
                discord_notifier=self.discord_notifier
            )
            self.auto_sell_monitor.connected_wallets = self.connected_wallets
            logger.info("✅ Auto-sell monitor initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize auto-sell monitor: {e}")
            self.auto_sell_monitor = None
        
        # Tracking with persistent database storage to prevent duplicates across restarts
        self.notified_token_addresses = set()  # Track tokens we've already sent notifications for in memory
        self.notification_count = 0
        
        # Initialize persistent notification tracking in database
        self.init_persistent_notification_tracking()
        self.monitoring_stats = {
            'total_tokens_processed': 0,
            'notifications_sent': 0,
            'api_calls_made': 0,
            'uptime_start': datetime.now().isoformat()
        }
        
        logger.info(f"🔍 Monitoring {len(self.keywords)} keywords")
        logger.info("💰 Using Alchemy FREE tier (300M requests/month)")
        
        # Discord bot will be initialized in background during delayed_initialization  
        self.discord_bot = None
        
        # Initialize market cap alert manager with Discord bot reference
        # self.market_cap_alert_manager = MarketCapAlertManager(self.discord_bot)  # DISABLED
    
    def check_token_keywords(self, token: Dict[str, Any]) -> str:
        """Check if token matches any keywords and meets quality standards
        
        Returns:
            str: The matched keyword, or empty string if no match
        """
        try:
            name = token.get('name', '').lower()
            symbol = token.get('symbol', '').lower()
            token_address = token.get('address', '')
            
            # EMERGENCY BLOCK: Stop these specific old tokens from getting notifications
            blocked_tokens = [
                "EK7Ko9zmrfanDz98UnbWB9zkDPFV3Mcpx84t1DS2bonk",
                "7Zje1wV3r5sq8JEvJ1jFWifmSZe6CSBLRz4prFSXbonk", 
                "AHX7mj5Re2AwfvDgQUdVqEidQKHfH4tuxhdaLyLnbonk",
                "AVMMEP3WRxU63kyL5tAMCFPkwui36ZND932bBDXUbonk",
                "4EPMN1CVGmWmxF4bBP4Nt4TjD2m5KTjWGMDDrt38bonk",
                "3ZWWatVxckSWHm1avfC5UFyHa4nN9x46KfhWq4Tqbonk"
            ]
            
            if token_address in blocked_tokens:
                logger.error(f"🚨🚨🚨 EMERGENCY BLOCK: {token_address} is in BLOCKED TOKENS LIST")
                logger.error(f"   ⚠️ User complained about these old tokens - BLOCKING ALL NOTIFICATIONS")
                logger.error(f"   🚫 Token name: {token.get('name', 'unknown')}")
                return ""  # Block notification completely
            
            # NUCLEAR AGE VALIDATION: Check token age BEFORE keyword matching
            if not self.is_ultra_fresh_token(token):
                logger.error(f"🚫 NUCLEAR BLOCK: {token.get('name', 'unknown')} failed age validation - BLOCKING notification")
                return ""  # Block old tokens from notifications
            
            # Skip empty keywords
            if len(self.keywords) == 0:
                return ""
            
            # Quality filters to reduce spam
            if self._is_low_quality_token(token):
                return ""
            
            # Ultra-fast keyword checking with optimizations
            logger.debug(f"🔍 Checking '{name}' against {len(self.keywords)} keywords")
            
            # Early exit for very short names
            if len(name) < 3:
                return ""
            
            # Group keywords by length for faster processing
            short_keywords = [k for k in self.keywords if len(k) <= 5]
            long_keywords = [k for k in self.keywords if len(k) > 5]
            
            # Check short keywords first (faster)
            for keyword in short_keywords:
                keyword_lower = keyword.lower()
                if self._is_generic_match(keyword_lower, name, symbol):
                    continue
                if keyword_lower in name or keyword_lower in symbol:
                    logger.info(f"🎯 MATCH: '{keyword}' in '{name}'")
                    return keyword
            
            # Then check long keywords
            for keyword in long_keywords:
                keyword_lower = keyword.lower()
                if self._is_generic_match(keyword_lower, name, symbol):
                    continue
                if keyword_lower in name or keyword_lower in symbol:
                    logger.info(f"🎯 MATCH: '{keyword}' in '{name}'")
                    return keyword
            
            return ""
            
        except Exception as e:
            logger.debug(f"Keyword check error: {e}")
            return ""
    
    def check_token_social_urls(self, token: Dict[str, Any]) -> str:
        """Extract and check token's social media URLs against watchlist URLs"""
        try:
            if not self.link_sniper:
                logger.debug("🔍 No link_sniper initialized for URL monitoring")
                return ""
            
            # Get watchlist URLs from link_sniper database
            watchlist_urls = []
            try:
                from link_sniper import LinkSniper
                db_url = os.getenv('DATABASE_URL')
                if db_url:
                    import psycopg2
                    conn = psycopg2.connect(db_url)
                    cursor = conn.cursor()
                    cursor.execute("SELECT DISTINCT target_link FROM link_sniper_configs WHERE enabled = true")
                    results = cursor.fetchall()
                    watchlist_urls = [row[0] for row in results]
                    cursor.close()
                    conn.close()
            except Exception as e:
                logger.debug(f"Error getting watchlist URLs from database: {e}")
                return ""
            
            if not watchlist_urls:
                logger.debug(f"🔍 No URL watchlist configured for monitoring")
                return ""
            
            # Extract social media URLs from token
            token_urls = self.extract_token_social_urls(token)
            if not token_urls:
                logger.debug(f"🔍 No social URLs found for {token['name']}")
                return ""
            
            logger.info(f"🔍 URL MONITORING: Checking {len(token_urls)} URLs for {token['name']} against {len(watchlist_urls)} watchlist URLs")
            logger.info(f"📋 Watchlist URLs: {watchlist_urls[:3]}...")  # Show first 3 URLs
            logger.info(f"📎 Token URLs: {token_urls[:3]}...")  # Show first 3 URLs
            
            # Check each extracted URL against watchlist
            for token_url in token_urls:
                for watchlist_url in watchlist_urls:
                    # Normalize URLs for comparison (remove trailing slashes, convert to lowercase)
                    token_url_clean = token_url.lower().rstrip('/')
                    watchlist_url_clean = watchlist_url.lower().rstrip('/')
                    
                    # Check for exact match or partial match
                    if token_url_clean == watchlist_url_clean or watchlist_url_clean in token_url_clean:
                        logger.info(f"🎯 URL MATCH FOUND: {token_url} matches watchlist URL: {watchlist_url}")
                        return watchlist_url
            
            return ""
            
        except Exception as e:
            logger.debug(f"Error checking token social URLs: {e}")
            return ""
    
    def extract_token_social_urls(self, token: Dict[str, Any]) -> List[str]:
        """Extract social media URLs from token using multiple methods"""
        urls = []
        
        try:
            # Method 1: Enhanced social media extractor (BrowserCat)
            if self.social_extractor and token['address'].endswith('bonk'):
                try:
                    logger.debug(f"🔍 Extracting social URLs for {token['name']} using enhanced scraper")
                    
                    # Run async extraction in thread-safe way
                    import asyncio
                    import threading
                    
                    def run_extraction():
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                result = loop.run_until_complete(
                                    self.social_extractor.get_social_links(token['address'])
                                )
                                return result.get('social_links', []) if result else []
                            finally:
                                loop.close()
                        except Exception as e:
                            logger.debug(f"Enhanced extraction failed: {e}")
                            return []
                    
                    social_links = run_extraction()
                    if social_links:
                        urls.extend(social_links)
                        logger.info(f"✅ Enhanced extractor found {len(social_links)} URLs for {token['name']}")
                
                except Exception as e:
                    logger.debug(f"Enhanced social extraction failed: {e}")
            
            # Method 2: Token link validator
            if self.token_link_validator:
                try:
                    logger.debug(f"🔍 Getting token links for {token['name']} using validator")
                    links_data = self.token_link_validator.get_token_links(token['address'], token['name'])
                    if links_data and not links_data.get('error'):
                        verified_links = links_data.get('verified_links', [])
                        for link in verified_links:
                            if link.get('working') and link.get('url'):
                                urls.append(link['url'])
                        logger.info(f"✅ Token validator found {len(verified_links)} URLs for {token['name']}")
                
                except Exception as e:
                    logger.debug(f"Token link validation failed: {e}")
            
            # Method 3: LetsBonk enhanced scraper
            if self.enhanced_scraper and token['address'].endswith('bonk'):
                try:
                    logger.debug(f"🔍 Using LetsBonk enhanced scraper for {token['name']}")
                    enhanced_links = self.enhanced_scraper.extract_social_links(token['address'])
                    if enhanced_links:
                        urls.extend(enhanced_links)
                        logger.info(f"✅ LetsBonk scraper found {len(enhanced_links)} URLs for {token['name']}")
                
                except Exception as e:
                    logger.debug(f"LetsBonk enhanced scraper failed: {e}")
            
            # Remove duplicates and clean URLs
            unique_urls = list(set(urls))
            logger.info(f"🔍 EXTRACTED URLS: Found {len(unique_urls)} unique social URLs for {token['name']}: {unique_urls[:3]}...")
            
            return unique_urls
            
        except Exception as e:
            logger.error(f"❌ Error extracting social URLs for {token['name']}: {e}")
            return []
    
    def _is_low_quality_token(self, token: Dict[str, Any]) -> bool:
        """Filter out low-quality/spam tokens"""
        name = token.get('name', '').lower()
        symbol = token.get('symbol', '').lower()
        
        # Skip tokens with generic fallback names (but allow them for keyword testing)
        if name.startswith('letsbonk token ') and len(name.split()) == 3:
            logger.info(f"⚠️ Generic fallback name detected: {name} - allowing for keyword testing")
            # Don't filter these out - let them through for keyword matching
            return False
            
        # Skip tokens with offensive/spam content
        spam_indicators = ['retarded', 'nigger', 'faggot', 'bitch', 'fuck', 'shit', 'damn']
        for indicator in spam_indicators:
            if indicator in name or indicator in symbol:
                return True
        
        # Skip tokens with random character sequences
        if len(name) > 0 and (name.count('x') > 3 or name.count('z') > 2):
            return True
            
        # Skip very short meaningless names
        if len(name.strip()) < 3 and not name in ['ai', 'btc', 'eth', 'sol']:
            return True
            
        return False
    
    def _is_generic_match(self, keyword: str, name: str, symbol: str) -> bool:
        """Check if the keyword match is too generic/common"""
        
        # Skip generic "bonk" matches since all LetsBonk tokens have BONK symbol
        if keyword == "bonk" and symbol == "bonk" and "bonk" not in name.lower():
            return True
            
        # Skip "token" matches in generic fallback names
        if keyword == "token" and name.startswith("letsbonk token "):
            logger.info(f"⚠️ Skipping generic 'token' match in fallback name: {name}")
            return True
            
        # CRITICAL FIX: Skip "ai" matches unless it's a standalone word
        if keyword == "ai":
            # Only match "ai" if it appears as a standalone word, not part of another word
            import re
            if not re.search(r'\bai\b', name.lower()):
                logger.info(f"⚠️ Skipping partial 'ai' match in '{name}' - not standalone")
                return True
            
        # Skip single letter/number keywords unless they're crypto tickers
        if len(keyword) <= 1:
            return True
            
        # Only skip very generic words if they're the ONLY match
        overly_generic = ['the', 'and', 'or', 'a', 'an', 'is', 'it']
        if keyword in overly_generic:
            return True
            
        return False
    
    def is_ultra_fresh_token(self, token: Dict[str, Any]) -> bool:
        """Check if token is ultra-fresh using multiple validation sources
        
        ENHANCED WITH DEXSCREENER VALIDATION:
        - Primary: Blockchain timestamp validation
        - Secondary: DexScreener API cross-validation
        - Reasonable 2-minute age limit for effective monitoring
        """
        current_time = time.time()
        created_timestamp = token.get('created_timestamp')
        token_name = token.get('name', 'unknown')
        token_address = token.get('address', '')
        
        # CRITICAL FIX: Reject tokens without valid blockchain timestamp - NO FALLBACK ALLOWED
        if created_timestamp is None or created_timestamp <= 0:
            logger.error(f"🚫 ABSOLUTELY REJECTED: {token_name} ({token_address[:10]}...)")
            logger.error(f"   ❌ NO BLOCKCHAIN TIMESTAMP - Cannot verify token age")
            logger.error(f"   🚫 This token will be COMPLETELY BLOCKED from processing")
            logger.error(f"   ⚠️  Preventing fallback behavior that treats unverifiable tokens as 'new'")
            return False
            
        # Handle milliseconds format timestamps  
        if created_timestamp > 1e12:
            created_timestamp = created_timestamp / 1000.0
            logger.debug(f"🔄 Converted milliseconds timestamp for {token_name}: {created_timestamp}")
        
        # Reject ancient timestamps (>7 days old = blockchain corruption)
        seven_days_ago = current_time - (7 * 24 * 60 * 60)
        if created_timestamp < seven_days_ago:
            age_days = (current_time - created_timestamp) / (24 * 60 * 60)
            logger.debug(f"🚫 REJECTED: {token_name} impossibly old ({age_days:.1f} days)")
            return False
        
        # CRITICAL FIX: Reject future timestamps (clock drift protection)
        if created_timestamp > current_time + 120:  # Allow 120s clock drift
            logger.error(f"🚫 REJECTED FUTURE TIMESTAMP: {token_name} ({token_address[:10]}...)")
            logger.error(f"   ⚠️  Token timestamp: {created_timestamp} vs current: {current_time}")
            logger.error(f"   📅 This indicates corrupted/stale timestamp data from DexScreener API")
            return False
            
        # EMERGENCY BLOCK: Specific problematic token addresses
        problem_tokens = [
            "AVMMEP3WRxU63kyL5tAMCFPkwui36ZND932bBDXUbonk",  # Original complaint token
            "CvcdAYeVy5qYvomDNHteJBcz4ZXgHLwMg2W9KFZZbonk",  # New complaint token (Jubilee Debates)
        ]
        if token_address in problem_tokens:
            logger.error(f"🚨 EMERGENCY BLOCK: Known problem token {token_address}")
            logger.error(f"   🚫 This token has corrupted timestamp data and should never be processed")
            return False
        
        # Calculate age with 5-minute limit for broader capture
        age = current_time - created_timestamp
        
        # CRITICAL FIX: Expanded 5-minute window for better token capture
        if age > 300:
            age_minutes = age / 60
            logger.error(f"🚫 REJECTED OLD TOKEN: {token_name} ({token_address[:10]}...)")
            logger.error(f"   ⏰ Token age: {age_minutes:.1f} minutes ({age:.0f}s) - exceeds 3-minute limit")
            logger.error(f"   📅 Token timestamp: {created_timestamp}, Current time: {current_time}")
            logger.error(f"   🚫 This token is too old to be considered 'new' for real-time monitoring")
            return False
        
        # TEMPORARILY DISABLED: DexScreener validation to enable social media extraction testing
        # Re-enable this after social media extraction is confirmed working
        if False and self.dexscreener_validator and token_address.endswith('bonk'):
            try:
                is_dex_fresh = self.dexscreener_validator.is_token_genuinely_fresh(token_address, max_age_seconds=180)
                if not is_dex_fresh:
                    logger.warning(f"🚫 DEXSCREENER VALIDATION FAILED: {token_name} failed DexScreener freshness check")
                    return False
                else:
                    logger.info(f"✅ DEXSCREENER VALIDATION PASSED: {token_name} confirmed fresh")
            except Exception as e:
                logger.debug(f"⚠️ DexScreener validation error for {token_name}: {e}")
                # Continue with blockchain validation only
        
        # ULTIMATE: Multi-source consensus validation for maximum accuracy
        if self.multi_source_validator and token_address.endswith('bonk'):
            try:
                import asyncio
                
                # CRITICAL FIX: Use proper async context manager for session
                async def run_consensus_validation():
                    async with self.multi_source_validator:
                        return await self.multi_source_validator.validate_token_timestamp(token_address)
                
                consensus_result = asyncio.run(run_consensus_validation())
                
                if consensus_result and consensus_result.get('valid_sources', 0) >= 1:  # Allow single source
                    consensus_age = consensus_result.get('age_seconds', float('inf'))
                    confidence = consensus_result.get('confidence', 0)
                    
                    logger.info(f"🔍 CONSENSUS VALIDATION: {token_name} (age: {consensus_age:.1f}s, confidence: {confidence:.2f}, sources: {consensus_result.get('valid_sources', 0)})")
                    
                    # Use consensus timestamp if available and reasonable (RELAXED VALIDATION)
                    if consensus_age <= 300 and confidence > 0.3:  # 5-minute window, lower confidence threshold
                        logger.info(f"✅ CONSENSUS VALIDATION PASSED: {token_name} - using consensus timestamp")
                        # Update token with consensus timestamp for more accurate age calculation
                        consensus_timestamp = consensus_result.get('consensus_timestamp')
                        if consensus_timestamp:
                            token['created_timestamp'] = consensus_timestamp
                            age = current_time - consensus_timestamp  # Recalculate age
                    else:
                        logger.warning(f"🚫 CONSENSUS VALIDATION FAILED: {token_name} (age too old or low confidence)")
                        return False
                else:
                    logger.debug(f"⚠️ No valid consensus sources for {token_name}")
            except Exception as e:
                logger.debug(f"⚠️ Multi-source validation error for {token_name}: {e}")
                # Continue with existing validation
        
        is_fresh = age <= 300  # RELAXED: Allow up to 5-minute old tokens
        
        # Enhanced logging for debugging
        if not is_fresh:
            logger.error(f"🚫 REJECTED: {token_name} too old (age: {age:.1f}s)")
        else:
            logger.info(f"✅ GENUINE NEW TOKEN: {token_name} (blockchain age: {age:.1f}s)")
        
        return is_fresh
    
    def init_persistent_notification_tracking(self):
        """Initialize database table for persistent notification tracking across restarts"""
        try:
            conn = self.get_db_connection()
            if not conn:
                logger.warning("⚠️ No database connection - notification deduplication will be memory-only")
                return
                
            cursor = conn.cursor()
            
            # Create table for tracking notified tokens
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notified_tokens (
                    token_address VARCHAR(255) PRIMARY KEY,
                    token_name VARCHAR(255),
                    notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notification_type VARCHAR(50) DEFAULT 'keyword_match'
                )
            """)
            
            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notified_tokens_address 
                ON notified_tokens(token_address)
            """)
            
            # Create index for cleanup queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_notified_tokens_timestamp 
                ON notified_tokens(notified_at)
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Load recently notified tokens into memory cache (last 24 hours)
            self.load_recent_notifications()
            
            # Schedule periodic cleanup of old notifications (every 6 hours)
            import threading
            import time
            def periodic_cleanup():
                while True:
                    try:
                        time.sleep(6 * 60 * 60)  # 6 hours
                        self.cleanup_old_notifications()
                    except Exception as e:
                        logger.error(f"❌ Periodic cleanup error: {e}")
            
            cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
            cleanup_thread.start()
            
            logger.info("✅ Persistent notification tracking initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize persistent notification tracking: {e}")
    
    def load_recent_notifications(self):
        """Load recently notified tokens from database into memory cache"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return
                
            cursor = conn.cursor()
            
            # Load tokens notified in last 24 hours to prevent immediate re-notifications
            cursor.execute("""
                SELECT token_address FROM notified_tokens 
                WHERE notified_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'
            """)
            
            recent_tokens = cursor.fetchall()
            for (token_address,) in recent_tokens:
                self.notified_token_addresses.add(token_address)
            
            cursor.close()
            conn.close()
            
            logger.info(f"📋 Loaded {len(recent_tokens)} recently notified tokens from database")
            
        except Exception as e:
            logger.error(f"❌ Failed to load recent notifications: {e}")
    
    def store_detected_token_in_db(self, address, name, symbol, platform='letsbonk', status='pre_migration', matched_keywords=None, social_links=None):
        """Store detected token in searchable database for /og coin command"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return
                
            cursor = conn.cursor()
            
            # Convert lists to PostgreSQL arrays
            keywords_array = matched_keywords if matched_keywords else []
            social_array = social_links if social_links else []
            
            # Insert or update token data
            cursor.execute("""
                INSERT INTO detected_tokens (address, name, symbol, platform, status, matched_keywords, social_links, detection_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (address) DO UPDATE SET
                    name = EXCLUDED.name,
                    symbol = EXCLUDED.symbol,
                    status = EXCLUDED.status,
                    matched_keywords = EXCLUDED.matched_keywords,
                    social_links = EXCLUDED.social_links,
                    updated_at = NOW()
            """, (address, name, symbol, platform, status, keywords_array, social_array))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Stored token in searchable database: {name} ({address[:8]}...)")
            
        except Exception as e:
            logger.error(f"Error storing detected token: {e}")
    
    def search_detected_tokens(self, search_term, limit=10):
        """Search both pre-migration tokens and external APIs"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return []
                
            cursor = conn.cursor()
            
            # Search for tokens in our database (including pre-migration)
            search_pattern = f"%{search_term.lower()}%"
            cursor.execute("""
                SELECT address, name, symbol, platform, status, matched_keywords, social_links, 
                       detection_timestamp, migrated_to_raydium, market_cap
                FROM detected_tokens 
                WHERE LOWER(name) LIKE %s OR LOWER(symbol) LIKE %s
                ORDER BY detection_timestamp DESC
                LIMIT %s
            """, (search_pattern, search_pattern, limit))
            
            internal_results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            # Format internal results
            internal_tokens = []
            for row in internal_results:
                address, name, symbol, platform, status, keywords, social_links, detection_time, migrated, market_cap = row
                internal_tokens.append({
                    'address': address,
                    'name': name,
                    'symbol': symbol,
                    'platform': platform,
                    'status': status,
                    'matched_keywords': keywords or [],
                    'social_links': social_links or [],
                    'detection_timestamp': detection_time,
                    'migrated_to_raydium': migrated,
                    'market_cap': float(market_cap) if market_cap else 0,
                    'source': 'internal_db'
                })
            
            return internal_tokens
            
        except Exception as e:
            logger.error(f"Error searching detected tokens: {e}")
            return []
    
    def record_notification_in_db(self, token_address, token_name, notification_type='keyword_match'):
        """Record token notification in database for persistent deduplication"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Insert notification record (ignore if already exists)
            cursor.execute("""
                INSERT INTO notified_tokens (token_address, token_name, notification_type)
                VALUES (%s, %s, %s)
                ON CONFLICT (token_address) DO NOTHING
            """, (token_address, token_name, notification_type))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to record notification in database: {e}")
            return False
    
    def cleanup_old_notifications(self):
        """Clean up old notification records (keep last 7 days only)"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return
                
            cursor = conn.cursor()
            
            # Delete notifications older than 7 days
            cursor.execute("""
                DELETE FROM notified_tokens 
                WHERE notified_at < CURRENT_TIMESTAMP - INTERVAL '7 days'
            """)
            
            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            if deleted_count > 0:
                logger.info(f"🧹 Cleaned up {deleted_count} old notification records")
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old notifications: {e}")
    
    def _load_keywords_postgres_first(self) -> List[str]:
        """Load keywords directly from PostgreSQL, fallback to ConfigManager if needed"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                logger.info("🔍 AlchemyServer: Loading keywords from PostgreSQL...")
                conn = psycopg2.connect(database_url)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT keyword FROM keyword_attribution 
                    WHERE is_active = TRUE
                    ORDER BY keyword
                """)
                
                results = cursor.fetchall()
                cursor.close()
                conn.close()
                
                if results:
                    keywords = [row[0] for row in results]
                    logger.info(f"✅ AlchemyServer: Loaded {len(keywords)} keywords from PostgreSQL")
                    return keywords
                else:
                    logger.warning("⚠️ AlchemyServer: No active keywords found in PostgreSQL")
                    
        except Exception as e:
            logger.error(f"❌ AlchemyServer: PostgreSQL keyword loading failed: {e}")
        
        # Fallback to ConfigManager
        logger.info("📁 AlchemyServer: Using ConfigManager fallback")
        return self.config_manager.list_keywords()
    
    def init_wallet_persistence(self):
        """Initialize encryption key and database connection for persistent wallet storage"""
        try:
            # Use persistent key stored in file to survive restarts
            key_file = ".wallet_encryption_key"
            
            try:
                # Try to load existing key from file
                with open(key_file, 'r') as f:
                    encryption_key = f.read().strip()
                logger.info("🔑 Loaded existing wallet encryption key from file")
            except FileNotFoundError:
                # Generate new key and save it for persistence
                encryption_key = Fernet.generate_key().decode()
                with open(key_file, 'w') as f:
                    f.write(encryption_key)
                logger.info("🔐 Generated new wallet encryption key and saved to file")
            
            # Check environment variable override
            env_key = os.getenv('WALLET_ENCRYPTION_KEY')
            if env_key:
                encryption_key = env_key
                logger.info("🔑 Using wallet encryption key from environment")
                
            self.cipher_suite = Fernet(encryption_key.encode())
            logger.info("✅ Wallet encryption initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize wallet encryption: {e}")
            self.cipher_suite = None
    
    def get_db_connection(self):
        """Get database connection for wallet storage"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                return psycopg2.connect(database_url)
            else:
                logger.warning("⚠️ No DATABASE_URL found for wallet persistence")
                return None
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return None
    
    def encrypt_private_key(self, private_key_bytes):
        """Encrypt private key for secure storage"""
        try:
            if self.cipher_suite:
                return self.cipher_suite.encrypt(private_key_bytes).decode()
            return None
        except Exception as e:
            logger.error(f"❌ Failed to encrypt private key: {e}")
            return None
    
    def decrypt_private_key(self, encrypted_key):
        """Decrypt private key from storage"""
        try:
            if self.cipher_suite:
                return self.cipher_suite.decrypt(encrypted_key.encode())
            return None
        except Exception as e:
            logger.error(f"❌ Failed to decrypt private key: {e}")
            return None
    
    def save_wallet_to_db(self, user_id, wallet_address, keypair):
        """Save connected wallet to database with encryption"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            # Encrypt private key
            private_key_bytes = bytes(keypair)
            encrypted_key = self.encrypt_private_key(private_key_bytes)
            if not encrypted_key:
                return False
            
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO connected_wallets (user_id, wallet_address, encrypted_private_key, connected_at, last_used)
                VALUES (%s, %s, %s, NOW(), NOW())
                ON CONFLICT (user_id) 
                DO UPDATE SET 
                    wallet_address = EXCLUDED.wallet_address,
                    encrypted_private_key = EXCLUDED.encrypted_private_key,
                    last_used = NOW()
            """, (user_id, wallet_address, encrypted_key))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"💾 Saved wallet {wallet_address[:8]}... to database for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save wallet to database: {e}")
            return False
    
    def restore_connected_wallets(self):
        """Restore connected wallets from database on server startup"""
        try:
            conn = self.get_db_connection()
            if not conn:
                logger.info("📝 No database connection - wallets will not persist across restarts")
                return
                
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, wallet_address, encrypted_private_key, connected_at 
                FROM connected_wallets 
                WHERE last_used > NOW() - INTERVAL '7 days'
                ORDER BY last_used DESC
            """)
            
            rows = cursor.fetchall()
            restored_count = 0
            
            for user_id, wallet_address, encrypted_key, connected_at in rows:
                try:
                    # Decrypt private key
                    private_key_bytes = self.decrypt_private_key(encrypted_key)
                    if not private_key_bytes:
                        continue
                        
                    # Recreate keypair
                    keypair = Keypair.from_bytes(private_key_bytes)
                    
                    # Restore to memory
                    self.connected_wallets[user_id] = {
                        'address': wallet_address,
                        'keypair': keypair,
                        'connected_at': connected_at.timestamp()
                    }
                    
                    restored_count += 1
                    logger.info(f"🔄 Restored wallet {wallet_address[:8]}... for user {user_id}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to restore wallet for user {user_id}: {e}")
                    continue
            
            cursor.close()
            conn.close()
            
            if restored_count > 0:
                logger.info(f"✅ Restored {restored_count} connected wallets from database")
            else:
                logger.info("📝 No wallets to restore from database")
                
        except Exception as e:
            logger.error(f"❌ Failed to restore wallets from database: {e}")

    def get_block_time(self, tx_signature):
        """Get block time for a transaction signature using Solana RPC client"""
        try:
            tx = client.get_transaction(tx_signature, commitment="finalized").value
            if tx and tx.block_time:
                block_time = tx.block_time
                logger.info(f"Transaction {tx_signature}: block_time={block_time}")
                return block_time
            else:
                logger.warning(f"No block time found for transaction {tx_signature}")
                return None
        except Exception as e:
            logger.error(f"Failed to fetch block time for {tx_signature}: {e}")
            return None
    
    def send_token_notification(self, token: Dict[str, Any], matched_keyword: str = ""):
        """Send Discord notification for matched token"""
        try:
            if not self.discord_notifier:
                return
            
            # FETCH MARKET DATA for enhanced notifications
            start_time = time.time()
            market_data = None
            
            # Get market data from DexScreener API
            if self.market_data_api:
                try:
                    market_data = self.market_data_api.get_market_data(token['address'])
                    if market_data:
                        logger.info(f"📈 Market data fetched: {token['name']} - ${market_data.get('market_cap', 0):,.0f} cap")
                    else:
                        logger.debug(f"📊 No market data available for {token['name']}")
                except Exception as e:
                    logger.debug(f"Market data fetch failed for {token['name']}: {e}")
                    market_data = None
            
            # Calculate token age - CRITICAL FIX: No fallback to current time
            created_timestamp = token.get('created_timestamp')
            current_time = time.time()
            token_address = token.get('address', '')
            
            # EMERGENCY BLOCK FOR USER'S SPECIFIC COMPLAINT TOKENS
            blocked_tokens = [
                "AVMMEP3WRxU63kyL5tAMCFPkwui36ZND932bBDXUbonk",  # Original complaint token
                "CvcdAYeVy5qYvomDNHteJBcz4ZXgHLwMg2W9KFZZbonk",  # New complaint token (Jubilee Debates)
            ]
            if token_address in blocked_tokens:
                logger.error(f"🚨🚨🚨 EMERGENCY BLOCK: USER COMPLAINT TOKEN {token_address} DETECTED")
                logger.error(f"   🚫 BLOCKING DISCORD NOTIFICATION FOR OLD TOKEN")
                logger.error(f"   📅 This token was created much earlier - SHOULD NEVER REACH NOTIFICATIONS")
                logger.error(f"   🔍 Token name: {token.get('name', 'unknown')}")
                return
            
            # CRITICAL: Reject tokens without valid blockchain timestamp
            if created_timestamp is None or created_timestamp <= 0:
                logger.error(f"❌ Token {token.get('name', 'unknown')} missing valid created_timestamp - SKIPPING notification")
                return
                
            # Handle milliseconds vs seconds timestamp format
            if created_timestamp > 1e12:  # Milliseconds format (timestamp > year 2001 in milliseconds)
                normalized_timestamp = created_timestamp / 1000.0
            else:
                normalized_timestamp = created_timestamp
            
            # STRICT VALIDATION: Reject invalid timestamps
            if normalized_timestamp <= 0:
                logger.error(f"❌ REJECTED: Invalid timestamp <= 0: {normalized_timestamp}")
                return
            
            if normalized_timestamp > current_time + 300:  # Future timestamp (5 min tolerance)
                logger.error(f"❌ REJECTED: Future timestamp: {normalized_timestamp} vs current {current_time}")
                return
            
            age_seconds = current_time - normalized_timestamp
            
            # CRITICAL FIX: Reject tokens older than 5 minutes (300 seconds) - REGULAR notifications  
            if age_seconds > 300:  # Expanded to 5 minute window for better capture
                age_minutes = age_seconds / 60
                logger.error(f"❌ REJECTED OLD TOKEN (REGULAR): {token.get('name', 'unknown')} ({token_address[:10]}...)")
                logger.error(f"   ⏰ Token age: {age_minutes:.1f} minutes ({age_seconds:.0f}s) - exceeds 5-minute limit for regular notifications")
                return
            
            if age_seconds < 60:
                age_display = f"{age_seconds:.0f}s ago"
            elif age_seconds < 3600:
                age_display = f"{age_seconds/60:.0f}m {age_seconds%60:.0f}s ago"
            else:
                age_display = f"{age_seconds/3600:.0f}h {(age_seconds%3600)/60:.0f}m ago"
            
            # Create Discord embed
            embed_data = {
                "title": f"🚀 New LetsBonk Token: {token['name']}",
                "description": f"**{token['symbol']}** detected on LetsBonk.fun",
                "color": 0x00ff00,
                "fields": [
                    {
                        "name": "📊 Token Info",
                        "value": f"**Name:** {token['name']}\n**Symbol:** {token['symbol']}\n**Age:** {age_display}",
                        "inline": True
                    },
                    {
                        "name": "🔗 Links",
                        "value": f"[LetsBonk]({token['url']})\n[Contract](https://solscan.io/account/{token['address']})",
                        "inline": True
                    }
                ]
            }
            
            # Add market data if available
            if market_data:
                market_value = ""
                if market_data.get('market_cap'):
                    market_value += f"**Market Cap:** ${market_data['market_cap']:,.0f}\n"
                if market_data.get('price'):
                    market_value += f"**Price:** ${market_data['price']:.8f}\n"
                if market_data.get('volume_24h'):
                    market_value += f"**24h Volume:** ${market_data['volume_24h']:,.0f}"
                
                if market_value:
                    embed_data["fields"].append({
                        "name": "💰 Market Data",
                        "value": market_value,
                        "inline": False
                    })
            
            # Add social media links if available
            if self.token_link_validator:
                try:
                    links_summary = self.token_link_validator.get_link_summary(token['address'], token['name'])
                    if links_summary and "No social media links found" not in links_summary:
                        embed_data["fields"].append({
                            "name": "🔗 Social Media",
                            "value": links_summary.replace("🔗 **Social Links:**\n", ""),
                            "inline": False
                        })
                except Exception as e:
                    logger.debug(f"Failed to fetch social links for {token['name']}: {e}")
            
            embed_data["footer"] = {
                "text": f"Powered by Alchemy API (FREE) • Detection: {age_display}"
            }
            
            # Prepare enhanced notification data
            notification_data = {
                'name': token['name'],
                'symbol': token['symbol'],
                'address': token['address'],
                'age_display': age_display,
                'market_data': market_data
            }
            
            # Send enhanced notification with matched keyword AND quick buy buttons
            notification_start = time.time()
            if self.discord_bot:
                success = self.discord_notifier.send_enhanced_token_notification_with_buttons(
                    notification_data, matched_keyword, self.discord_bot
                )
                logger.info(f"📱 Sent notification with quick buy buttons for {token['name']}")
            else:
                success = self.discord_notifier.send_enhanced_token_notification(notification_data, matched_keyword)
                logger.info(f"📡 Sent webhook notification for {token['name']}")
            notification_time = time.time() - notification_start
            
            if success:
                self.notification_count += 1
                self.monitoring_stats['notifications_sent'] += 1
                logger.info(f"✅ Discord notification sent: {token['name']} (#{self.notification_count})")
                logger.info(f"📤 Sent Discord notification for {token['name']} in {notification_time:.2f}s")
            else:
                logger.warning(f"❌ Failed to send Discord notification for {token['name']}")
                
        except Exception as e:
            logger.error(f"Notification error: {e}")
    
    def send_instant_notification(self, token: Dict[str, Any], matched_keyword: str = ""):
        """Send INSTANT notification WITH market data (optimized for speed)"""
        try:
            if not self.discord_notifier:
                return
            
            # Calculate basic age - CRITICAL FIX: No fallback to current time
            created_timestamp = token.get('created_timestamp')
            current_time = time.time()
            token_address = token.get('address', '')
            
            # EMERGENCY BLOCK FOR USER'S SPECIFIC COMPLAINT TOKENS
            blocked_tokens = [
                "AVMMEP3WRxU63kyL5tAMCFPkwui36ZND932bBDXUbonk",  # Original complaint token
                "CvcdAYeVy5qYvomDNHteJBcz4ZXgHLwMg2W9KFZZbonk",  # New complaint token (Jubilee Debates)
            ]
            if token_address in blocked_tokens:
                logger.error(f"🚨🚨🚨 EMERGENCY BLOCK: USER COMPLAINT TOKEN {token_address} DETECTED IN INSTANT NOTIFICATION")
                logger.error(f"   🚫 BLOCKING INSTANT DISCORD NOTIFICATION FOR OLD TOKEN")  
                logger.error(f"   📅 This token was created much earlier - SHOULD NEVER REACH NOTIFICATIONS")
                logger.error(f"   🔍 Token name: {token.get('name', 'unknown')}")
                return
            
            # CRITICAL: Reject tokens without valid blockchain timestamp
            if created_timestamp is None or created_timestamp <= 0:
                logger.error(f"❌ Token {token.get('name', 'unknown')} missing valid created_timestamp - SKIPPING notification")
                return
                
            # Handle milliseconds vs seconds timestamp format
            if created_timestamp > 1e12:  # Milliseconds format (timestamp > year 2001 in milliseconds)
                normalized_timestamp = created_timestamp / 1000.0
            else:
                normalized_timestamp = created_timestamp
            
            # STRICT VALIDATION: Reject invalid timestamps
            if normalized_timestamp <= 0:
                logger.error(f"❌ REJECTED: Invalid timestamp <= 0: {normalized_timestamp}")
                return
            
            if normalized_timestamp > current_time + 300:  # Future timestamp (5 min tolerance)
                logger.error(f"❌ REJECTED: Future timestamp: {normalized_timestamp} vs current {current_time}")
                return
            
            age_seconds = current_time - normalized_timestamp
            
            # CRITICAL FIX: Reject tokens older than 3 minutes (180 seconds) - INSTANT notifications  
            if age_seconds > 180:  # Stricter than 60 seconds - 3 minute window
                age_minutes = age_seconds / 60
                logger.error(f"❌ REJECTED OLD TOKEN (INSTANT): {token.get('name', 'unknown')} ({token_address[:10]}...)")
                logger.error(f"   ⏰ Token age: {age_minutes:.1f} minutes ({age_seconds:.0f}s) - exceeds 3-minute limit for instant notifications")
                return
            
            if age_seconds < 60:
                age_display = f"{age_seconds:.0f}s ago"
            elif age_seconds < 3600:
                age_display = f"{age_seconds/60:.0f}m ago"
            else:
                age_display = f"{age_seconds/3600:.0f}h ago"
            
            # FETCH MARKET DATA with quick timeout for instant notifications
            market_data = None
            if self.market_data_api:
                try:
                    market_data = self.market_data_api.get_market_data(token['address'])
                    if market_data:
                        logger.info(f"📈 INSTANT market data: {token['name']} - ${market_data.get('market_cap', 0):,.0f} cap")
                    else:
                        logger.debug(f"📊 No market data available for {token['name']}")
                except Exception as e:
                    logger.debug(f"Market data fetch failed: {e}")
                    market_data = None
            
            # Create notification with market data if available
            notification_data = {
                'name': token['name'],
                'symbol': token['symbol'],
                'address': token['address'],
                'age_display': age_display,
                'market_data': market_data,
                'url': f"https://letsbonk.fun/token/{token['address']}"
            }
            
            # Send notification with market data AND quick buy buttons
            notification_start = time.time()
            if self.discord_bot:
                success = self.discord_notifier.send_enhanced_token_notification_with_buttons(
                    notification_data, matched_keyword, self.discord_bot
                )
                logger.info(f"📱 Sent instant notification with quick buy buttons for {token['name']}")
            else:
                success = self.discord_notifier.send_enhanced_token_notification(notification_data, matched_keyword)
                logger.info(f"📡 Sent instant webhook notification for {token['name']}")
            notification_time = time.time() - notification_start
            
            if success:
                self.notification_count += 1
                self.monitoring_stats['notifications_sent'] += 1
                cap_info = f"${market_data.get('market_cap', 0):,.0f}" if market_data and market_data.get('market_cap') else "No cap data"
                logger.info(f"⚡ INSTANT Discord alert sent: {token['name']} (#{self.notification_count}) - {age_display} - {cap_info}")
                logger.info(f"📤 Sent Discord notification for {token['name']} in {notification_time:.2f}s")
            else:
                logger.warning(f"❌ Failed to send instant Discord notification for {token['name']}")
                
        except Exception as e:
            logger.error(f"Instant notification error: {e}")
    
    def send_fast_notification(self, token: Dict[str, Any], matched_keyword: str = ""):
        """Fast notification callback for speed-optimized monitor"""
        try:
            # Send immediate notification without delays
            if self.discord_notifier:
                success = self.discord_notifier.send_embed_notification(
                    message=f"⚡ SPEED ALERT: {token['name']} matched '{matched_keyword}'\n"
                           f"📍 Contract: {token['address']}\n" 
                           f"⏰ Ultra-fast detection (<5s processing)",
                    title="Speed-Optimized Detection"
                )
                
                if success:
                    self.notification_count += 1
                    logger.info(f"⚡ SPEED NOTIFICATION: {token['name']} matched '{matched_keyword}' (#{self.notification_count})")
                    
        except Exception as e:
            logger.error(f"Fast notification error: {e}")
    
    def enhance_notification_background(self, token: Dict[str, Any], matched_keyword: str = ""):
        """Enhance notification with market data in background (non-blocking)"""
        try:
            # Wait a moment to let market APIs index the token
            import time
            time.sleep(1)  # Reduced from 3s to 1s for faster background enhancement
            
            # Get market data
            market_data = None
            if self.market_data_api:
                try:
                    market_data = self.market_data_api.get_market_data(token['address'])
                    if market_data:
                        logger.info(f"📈 Market data retrieved for {token['name']}: ${market_data.get('market_cap', 0):,.0f} cap")
                except Exception as e:
                    logger.debug(f"Market data enhancement failed: {e}")
            
        except Exception as e:
            logger.debug(f"Background enhancement error: {e}")
    
    def process_spl_token_event(self, spl_data: Dict[str, Any]):
        """Process SPL token creation event from WebSocket"""
        if not spl_data:
            return
            
        signature = spl_data.get('signature', '')
        logger.info(f"🚀 SPL TOKEN EVENT: {signature[:10]}... (WebSocket detection)")
        
        # Extract transaction details for further analysis
        logs = spl_data.get('logs', [])
        
        # Look for specific token creation patterns
        token_creation_found = False
        for log in logs:
            if any(pattern in log.lower() for pattern in [
                'initializemint',
                'initialize mint',
                'tokenkeg'
            ]):
                token_creation_found = True
                break
        
        if token_creation_found:
            logger.info(f"✅ SPL Token creation confirmed: {signature[:10]}...")
            
            # This would typically trigger further analysis to get token details
            # For now, we log the detection - full implementation would extract token address
            # and fetch metadata through additional RPC calls
            
            # Future enhancement: Extract token mint address and fetch metadata
            # formatted_token = self.analyze_spl_transaction(signature)
            # if formatted_token:
            #     self.process_tokens([formatted_token])
        else:
            logger.debug(f"⚠️ SPL event {signature[:10]}... not a token creation")
    
    def process_tokens(self, tokens: List[Dict[str, Any]]):
        """Process multiple tokens simultaneously for keyword matches and notifications"""
        try:
            new_tokens = []
            logger.info(f"🔄 BATCH PROCESSING: {len(tokens)} tokens simultaneously")
            
            # PARALLEL PROCESSING: Process tokens in batches for efficiency
            import concurrent.futures
            from concurrent.futures import ThreadPoolExecutor
            
            def process_single_token(token):
                """Process individual token in parallel thread"""
                try:
                    # Initialize deduplication structures if they don't exist (fix for missing attributes)
                    if not hasattr(self, 'permanently_rejected_tokens'):
                        self.permanently_rejected_tokens = set()
                    if not hasattr(self, 'seen_token_addresses'):
                        from cachetools import TTLCache
                        self.seen_token_addresses = TTLCache(maxsize=10000, ttl=300)  # 5-minute cache
                    
                    # Check permanent blocklist first (prevents reprocessing old tokens when TTL cache expires)
                    if token['address'] in self.permanently_rejected_tokens:
                        logger.debug(f"🚫 PERMANENTLY BLOCKED: {token['name']} - {token['address'][:10]}... (old token)")
                        return None
                    
                    # Skip already seen tokens using TTL cache (reduce log spam)  
                    if token['address'] in self.seen_token_addresses:
                        logger.debug(f"🔁 ALREADY PROCESSED: {token['name']} - {token['address'][:10]}...")
                        return None
                    
                    # Check if genuinely new token (ultra-strict 60-second filtering)
                    # BUT ALLOW URL MATCHING for older tokens with social media links
                    is_fresh = self.is_ultra_fresh_token(token)
                    
                    if not is_fresh:
                        # SPECIAL CASE: Allow URL matching even for older tokens
                        # This ensures we don't miss tokens that match saved social media URLs
                        logger.info(f"⏰ OLD TOKEN DETECTED: {token['name']} (addr: {token['address'][:10]}...) - checking for URL matches before skipping")
                        
                        # CREDIT OPTIMIZATION: Skip old tokens immediately - no URL checking needed
                        # Old tokens should only proceed if they have actual extracted social media links
                        # which requires expensive BrowserCat operations we want to avoid
                        logger.info(f"⏰ SKIPPING OLD TOKEN: {token['name']} - failed freshness check")
                        self.permanently_rejected_tokens.add(token['address'])
                        return None
                    
                    # Mark as seen in TTL cache (auto-expires in 5 minutes)
                    self.seen_token_addresses[token['address']] = True
                    
                    # Log the token being processed with full address (only for genuinely new tokens)
                    logger.info(f"   📍 NEW: {token['name']} - {token['address']}")
                    
                    # 🔄 PURE NAME EXTRACTION: Get accurate token name from LetsBonk page
                    # This replaces the old dual approach (keywords + URLs) with 100% accurate name matching
                    logger.info(f"🔍 PURE NAME EXTRACTION: Getting accurate name for {token['name']} from LetsBonk page...")
                    
                    # Initialize pure name extractor if not exists
                    if not hasattr(self, 'pure_name_extractor'):
                        from pure_name_extractor import PureTokenNameExtractor, OptimizedKeywordMatcher, PureNameTokenProcessor
                        browsercat_api_key = os.getenv('BROWSERCAT_API_KEY', 'e7MEbRx603vMtEJbqkCez2COCKkCT8IRPZZrKqmYCXs1MlOKJKDEbdSUzarmVCGR')
                        
                        self.pure_name_extractor = PureTokenNameExtractor(browsercat_api_key)
                        self.pure_name_extractor.monitoring_server = self  # Connect for tracking extractions
                        self.optimized_keyword_matcher = OptimizedKeywordMatcher(self.keywords)
                        self.pure_name_processor = PureNameTokenProcessor(self.pure_name_extractor, self.optimized_keyword_matcher)
                        logger.info("✅ Pure name extraction system initialized with tracking")
                    
                    # Process token using pure name approach
                    import asyncio
                    import threading
                    
                    def run_pure_name_extraction():
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                return loop.run_until_complete(
                                    self.pure_name_processor.process_token_for_keywords(token)
                                )
                            finally:
                                loop.close()
                        except Exception as e:
                            logger.error(f"Pure name extraction error: {e}")
                            return None
                    
                    # Execute pure name extraction 
                    pure_name_result = run_pure_name_extraction()
                    
                    # Check if we found a keyword match using accurate name  
                    if pure_name_result and pure_name_result.get('matched_keyword'):
                        matched_keyword = pure_name_result['matched_keyword']
                        accurate_name = pure_name_result['accurate_name']
                        match_confidence = pure_name_result['match_confidence']
                        
                        logger.info(f"🎯 PURE NAME MATCH: '{accurate_name}' → keyword '{matched_keyword}' (confidence: {match_confidence:.2f})")
                        
                        # IMMEDIATELY send Discord notification for keyword match
                        instant_notification_start = time.time()
                        try:
                            # CRITICAL FIX: Proper timestamp validation for instant notifications
                            current_time = time.time()
                            created_timestamp = token.get('created_timestamp')
                            
                            # EMERGENCY BLOCK FOR KNOWN BAD TOKENS
                            if token['address'] in ["AVMMEP3WRxU63kyL5tAMCFPkwui36ZND932bBDXUbonk", "CvcdAYeVy5qYvomDNHteJBcz4ZXgHLwMg2W9KFZZbonk"]:
                                logger.error(f"🚨 BLOCKED INSTANT NOTIFICATION: {token['name']} ({token['address']}) - Known old token")
                                return None
                            
                            # STRICT VALIDATION: No fallback to current time!
                            if created_timestamp is None or created_timestamp <= 0:
                                logger.error(f"❌ BLOCKED INSTANT: {token['name']} - No valid timestamp, cannot verify age")
                                return None
                                
                            if created_timestamp > 1e12:
                                created_timestamp = created_timestamp / 1000.0
                                
                            # STRICT AGE CHECK: Reject tokens older than 3 minutes
                            age_seconds = current_time - created_timestamp
                            if age_seconds > 180:  # 3 minutes max
                                age_minutes = age_seconds / 60
                                logger.error(f"❌ BLOCKED INSTANT: {token['name']} is {age_minutes:.1f} minutes old - too old for instant notification")
                                return None
                                
                            age_display = f"{age_seconds:.0f}s ago"
                            
                            notification_data = {
                                'name': accurate_name,  # Use accurate name from LetsBonk page
                                'original_name': token['name'],  # Keep original for comparison
                                'symbol': token['symbol'], 
                                'address': token['address'],
                                'age_display': age_display,
                                'market_data': None,  # No market data for instant speed
                                'url': f"https://letsbonk.fun/token/{token['address']}",
                                'social_links': [],  # No social links needed for pure name approach
                                'match_confidence': match_confidence,
                                'processing_method': 'pure_name_extraction'
                            }
                            
                            # Send Discord notification instantly
                            if self.discord_notifier:
                                success = self.discord_notifier.send_enhanced_token_notification(notification_data, matched_keyword)
                                
                                if success:
                                    instant_time = time.time() - instant_notification_start
                                    logger.info(f"⚡ PURE NAME SUCCESS: Discord notification sent for '{accurate_name}' in {instant_time:.3f}s (confidence: {match_confidence:.2f})")
                                    
                                    # Track the notification to prevent duplicates
                                    self.notified_token_addresses.add(token['address'])
                                    self.notification_count += 1
                                    
                                    # Record in database for persistence
                                    self.record_notification_in_db(
                                        token['address'], 
                                        accurate_name,  # Use accurate name for database
                                        f'pure_name_match:{matched_keyword}:confidence_{match_confidence:.2f}'
                                    )
                                    
                                    # STORE TOKEN IN SEARCHABLE DATABASE
                                    self.store_detected_token_in_db(
                                        address=token['address'],
                                        name=accurate_name,
                                        symbol=token['symbol'],
                                        platform='letsbonk',
                                        status='pre_migration',
                                        matched_keywords=[matched_keyword],
                                        social_links=token.get('social_links', [])
                                    )
                                else:
                                    logger.error(f"❌ PURE NAME NOTIFICATION FAILED for '{accurate_name}'")
                        
                        except Exception as e:
                            logger.error(f"❌ PURE NAME NOTIFICATION ERROR for '{accurate_name}': {e}")
                        
                        # Mark as processed - no further processing needed
                        token['matched_keyword'] = matched_keyword  
                        token['accurate_name'] = accurate_name
                        token['match_confidence'] = match_confidence
                        token['pure_name_notification_sent'] = True
                        token['processing_method'] = 'pure_name_extraction'
                        logger.info(f"✅ PURE NAME PROCESSING COMPLETE: '{accurate_name}' → '{matched_keyword}'")
                        
                    else:
                        # No keyword match found using accurate name
                        if pure_name_result:
                            accurate_name = pure_name_result.get('accurate_name', 'unknown')
                            logger.info(f"❌ NO KEYWORD MATCH: Accurate name '{accurate_name}' doesn't match any keywords")
                        else:
                            logger.info(f"❌ NAME EXTRACTION FAILED: Could not get accurate name for {token['address'][:10]}...")
                        
                        token['pure_name_notification_sent'] = False
                        token['processing_method'] = 'pure_name_extraction_no_match'
                    
                    return token
                    
                except Exception as e:
                    logger.debug(f"Error processing token {token.get('name', 'unknown')}: {e}")
                    return None
            
            # 🚀 ENHANCED INITIAL PROCESSING: Increased batch size for better throughput
            valid_tokens = []
            initial_batch_size = min(len(tokens), 10)  # Process up to 10 tokens simultaneously in initial phase
            
            logger.info(f"🔄 INITIAL BATCH PROCESSING: {len(tokens)} tokens with {initial_batch_size} workers")
            
            with ThreadPoolExecutor(max_workers=initial_batch_size) as executor:
                future_to_token = {executor.submit(process_single_token, token): token for token in tokens}
                
                processed = 0
                for future in concurrent.futures.as_completed(future_to_token):
                    result = future.result()
                    processed += 1
                    if result is not None:
                        valid_tokens.append(result)
                        logger.debug(f"✅ INITIAL BATCH {processed}/{len(tokens)}: {result['name']} validated")
                    else:
                        logger.debug(f"⏭️ INITIAL BATCH {processed}/{len(tokens)}: Token rejected")
            
            new_tokens = valid_tokens
                
            # 📊 PURE NAME PROCESSING COMPLETE: No URL extraction needed
            logger.info(f"📊 Pure name processing completed: {len(new_tokens)} tokens processed")
            
            # Log pure name processing statistics
            if hasattr(self, 'pure_name_processor'):
                self.pure_name_processor.log_statistics()
            
            # OLD URL-BASED PROCESSING REMOVED: No longer needed with pure name approach
            # Pure name extraction provides 100% accurate keyword matching without social media complexity
            
            # Process notifications for tokens with keyword matches only (no URL processing needed)
            for token in new_tokens:
                # Skip tokens that already received instant notifications
                if token.get('instant_notification_sent', False):
                    logger.info(f"⏭️ SKIPPING: {token['name']} already received instant notification")
                    continue
                
                # Process tokens with keyword matches, URL matches, or link matches
                matched_keyword = token.get('matched_keyword')  # Retrieve stored keyword match
                matched_url = token.get('matched_url', '')  # Retrieve stored URL match
                link_match = None  # No link matching in pure name extraction approach
                if matched_keyword or matched_url:
                    # Check if we've already sent notification for this token (both memory and database)
                    if token['address'] not in self.notified_token_addresses:
                        if matched_keyword:
                            logger.info(f"🎯 KEYWORD MATCH NOTIFICATION: {token['name']} ({token['symbol']}) - {matched_keyword}")
                        elif matched_url:
                            logger.info(f"🔗 URL MATCH NOTIFICATION: {token['name']} ({token['symbol']}) - {matched_url}")
                        else:
                            logger.info(f"🎯 PROCESSING NOTIFICATION: {token['name']} ({token['symbol']})")
                        
                        # Check for sniper opportunities before sending notification
                        if self.auto_sniper:
                            try:
                                snipe_opportunities = self.auto_sniper.check_snipe_opportunity(
                                    {
                                        'name': token['name'],
                                        'address': token['address'],
                                        'symbol': token['symbol']
                                    },
                                    matched_keyword
                                )
                                
                                if snipe_opportunities:
                                    for opportunity in snipe_opportunities:
                                        # Execute snipe in background using thread-safe approach
                                        try:
                                            # Try to get the current event loop or create a new one
                                            try:
                                                loop = asyncio.get_event_loop()
                                                if loop.is_closed():
                                                    raise RuntimeError("Event loop is closed")
                                            except RuntimeError:
                                                # No event loop running, create a new one for this thread
                                                loop = asyncio.new_event_loop()
                                                asyncio.set_event_loop(loop)
                                            
                                            # Execute snipe using run_coroutine_threadsafe for thread safety
                                            future = asyncio.run_coroutine_threadsafe(
                                                self.auto_sniper.execute_snipe(
                                                    {
                                                        'name': token['name'],
                                                        'address': token['address'],
                                                        'symbol': token['symbol']
                                                    },
                                                    opportunity
                                                ),
                                                loop
                                            )
                                            logger.info(f"🎯 SNIPER ACTIVATED: {token['name']} for user {opportunity['user_id']}")
                                            
                                        except Exception as snipe_exec_error:
                                            logger.error(f"❌ Failed to execute snipe: {snipe_exec_error}")
                                            # Fall back to synchronous execution if async fails
                                            import threading
                                            def run_snipe():
                                                try:
                                                    # Create a new event loop in the thread
                                                    loop = asyncio.new_event_loop()
                                                    asyncio.set_event_loop(loop)
                                                    try:
                                                        loop.run_until_complete(self.auto_sniper.execute_snipe(
                                                            {
                                                                'name': token['name'],
                                                                'address': token['address'],
                                                                'symbol': token['symbol']
                                                            },
                                                            opportunity
                                                        ))
                                                        logger.info(f"✅ SNIPER PURCHASE SUCCESSFUL: {token['name']} for user {opportunity['user_id']}")
                                                    finally:
                                                        loop.close()
                                                except Exception as e:
                                                    logger.error(f"❌ Sync snipe execution failed: {e}")
                                            
                                            thread = threading.Thread(target=run_snipe)
                                            thread.daemon = True
                                            thread.start()
                                            logger.info(f"🎯 SNIPER ACTIVATED (fallback): {token['name']} for user {opportunity['user_id']}")
                            except Exception as e:
                                logger.error(f"❌ Error checking snipe opportunity: {e}")
                        
                        # SPEED OPTIMIZATION: Send notification INSTANTLY without waiting for market data
                        instant_start = time.time()
                        
                        # Create minimal notification data for instant sending
                        current_time = time.time()
                        created_timestamp = token.get('created_timestamp', current_time)
                        if created_timestamp > 1e12:
                            created_timestamp = created_timestamp / 1000.0
                        age_seconds = current_time - created_timestamp
                        age_display = f"{age_seconds:.0f}s ago"
                        
                        # Send instant minimal notification with social links
                        notification_data = {
                            'name': token['name'],
                            'symbol': token['symbol'], 
                            'address': token['address'],
                            'age_display': age_display,
                            'market_data': None,  # No market data for instant speed
                            'url': f"https://letsbonk.fun/token/{token['address']}",
                            'social_links': token.get('social_links', [])  # Include extracted social links
                        }
                        
                        # DEBUG: Log social links in notification data
                        social_links = token.get('social_links', [])
                        if social_links:
                            logger.info(f"📱 DISCORD NOTIFICATION including {len(social_links)} social links for {token['name']}")
                            for i, link in enumerate(social_links[:3], 1):
                                logger.info(f"   🔗 Link {i}: {link}")
                        else:
                            logger.info(f"📱 DISCORD NOTIFICATION: No social links found for {token['name']}")
                            # Check if social links are being stored correctly
                            logger.debug(f"   📊 Token data keys: {list(token.keys())}")
                            logger.debug(f"   📊 Social links value: {token.get('social_links', 'NOT_SET')}")
                        
                        # Check for URL matches using new URL monitoring system  
                        matched_url = token.get('matched_url', '')
                        
                        # Send SINGLE notification (consolidate all paths to prevent duplicates)
                        if matched_keyword:
                            notification_keyword = matched_keyword
                        elif matched_url:
                            notification_keyword = f"URL: {matched_url[:30]}..."
                        elif link_match:
                            notification_keyword = f"Link: {link_match['matched_link'][:30]}..."
                        else:
                            notification_keyword = "Match"
                        
                        success = False
                        
                        try:
                            if self.discord_bot:
                                success = self.discord_notifier.send_enhanced_token_notification_with_buttons(
                                    notification_data, notification_keyword, self.discord_bot
                                )
                                logger.info(f"📱 Sent notification with quick buy buttons for {token['name']}")
                            else:
                                success = self.discord_notifier.send_enhanced_token_notification(notification_data, notification_keyword)
                                logger.info(f"📡 Sent webhook notification for {token['name']}")
                        except Exception as e:
                            logger.debug(f"Discord notification error: {e}")
                            # Fallback only if first method failed
                            success = self.discord_notifier.send_enhanced_token_notification(notification_data, notification_keyword)
                            logger.info(f"📡 Sent fallback webhook notification for {token['name']}")
                        
                        # Execute link snipe if applicable (not in notify-only mode)
                        if link_match and link_match['config']['enabled'] and not link_match['config']['notify_only']:
                            try:
                                import threading
                                def run_link_snipe():
                                    try:
                                        loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(loop)
                                        try:
                                            # Execute link-based purchase
                                            logger.info(f"🔗 LINK SNIPER ACTIVATED: {token['name']} for URL: {link_match['matched_link'][:50]}...")
                                            # Implementation would go here - for now just log
                                        finally:
                                            loop.close()
                                    except Exception as e:
                                        logger.error(f"❌ Link snipe execution failed: {e}")
                                
                                thread = threading.Thread(target=run_link_snipe)
                                thread.daemon = True
                                thread.start()
                            except Exception as e:
                                logger.error(f"❌ Error executing link snipe: {e}")
                        elif link_match and link_match['config']['notify_only']:
                            logger.info(f"📢 LINK NOTIFICATION: {token['name']} - notify-only mode, no purchase executed")
                        instant_time = time.time() - instant_start
                        
                        # Mark token as notified to prevent future duplicates with PERSISTENT DATABASE TRACKING
                        if success:
                            self.notification_count += 1
                            self.notified_token_addresses.add(token['address'])  # Memory cache for current session
                            
                            # CRITICAL: Store in database for persistent deduplication across system restarts
                            notification_type = 'keyword_match' if matched_keyword else 'url_match'
                            db_success = self.record_notification_in_db(token['address'], token['name'], notification_type)
                            if db_success:
                                logger.info(f"💾 PERSISTENT TRACKING: {token['name']} recorded in database to prevent duplicate notifications")
                            else:
                                logger.warning(f"⚠️ Database tracking failed for {token['name']} - relying on memory cache only")
                            
                            self.monitoring_stats['notifications_sent'] += 1
                            logger.info(f"⚡ LIGHTNING FAST: {token['name']} notification sent in {instant_time:.3f}s")
                            
                            # Fetch market data in background for logging only (non-blocking)
                            import threading
                            def fetch_market_cap_background():
                                try:
                                    time.sleep(0.5)  # Small delay to let APIs catch up
                                    if self.market_data_api:
                                        market_data = self.market_data_api.get_market_data(token['address'])
                                        if market_data and market_data.get('market_cap'):
                                            logger.info(f"📈 Market cap update: {token['name']} - ${market_data['market_cap']:,.0f}")
                                except:
                                    pass
                            
                            threading.Thread(target=fetch_market_cap_background, daemon=True).start()
                        else:
                            logger.warning(f"❌ Failed instant notification: {token['name']}")
                    else:
                        logger.info(f"🚫 DUPLICATE NOTIFICATION BLOCKED: {token['name']} - already notified")
                else:
                    # Log keyword mismatches for debugging
                    logger.debug(f"❌ No keyword match: {token['name']} ({token['symbol']}) - checked {len(self.keywords)} keywords")
            
            self.monitoring_stats['total_tokens_processed'] += len(new_tokens)
            
            # Enhanced logging for debugging
            if new_tokens:
                logger.info(f"📊 Processed {len(new_tokens)} new tokens, {len(tokens)} total from API")
                for token in new_tokens:
                    logger.info(f"   🆕 {token['name']} - {token['address']}")
            else:
                logger.info(f"📊 Processed {len(new_tokens)} new tokens, {len(tokens)} total from API")
            
        except Exception as e:
            logger.error(f"Token processing error: {e}")
    
    def monitoring_loop(self):
        """Start real-time WebSocket monitoring for NEW token creations only"""
        logger.info("🚀 Starting REAL-TIME WebSocket monitoring")
        logger.info("📡 Monitoring ONLY new token creation events (not transaction history)")
        logger.info("⚡ Target: 1-5 second detection speed for genuinely new tokens")
        logger.info("💰 Cost: $0/month (using real-time WebSocket)")
        
        # CRITICAL BUG FIX: Disable new_token_monitor that was creating fake timestamps
        # The new_token_monitor was using discovery time instead of blockchain timestamps
        # This caused 6-hour-old tokens to appear as "3.2 seconds" fresh
        # Only use EnhancedTokenDetector which properly validates blockchain timestamps
        logger.info("🚫 Standard token monitor DISABLED (was creating fake timestamps)")
        
        # Also start enhanced detector for comparison (non-blocking)
        try:
            from enhanced_token_detector import EnhancedTokenDetector
            self.enhanced_detector = EnhancedTokenDetector(callback_func=self.process_tokens)
            
            enhanced_thread = threading.Thread(target=self.enhanced_detector.monitor_enhanced_token_creation)
            enhanced_thread.daemon = True
            enhanced_thread.start()
            logger.info("✅ Enhanced detector also started for comparison")
        except Exception as e:
            logger.warning(f"Enhanced detector failed: {e}")
        
        # Keep monitoring thread alive
        while self.running:
            try:
                current_time = time.time()
                
                # Update recovery system monitoring timestamp
                if self.recovery_system:
                    self.recovery_system.update_monitoring_timestamp()
                    
                    # Check for monitoring gaps and perform recovery if needed
                    if self.recovery_system.detect_monitoring_gap(current_time):
                        logger.warning("🔧 Monitoring gap detected - starting recovery process")
                        self.recovery_system.perform_gap_recovery()
                    
                    # Perform periodic backfill if needed
                    if self.recovery_system.should_perform_backfill():
                        logger.info("🔄 Performing periodic backfill scan")
                        self.recovery_system.perform_periodic_backfill()
                
                time.sleep(10)  # Check every 10 seconds (optimized monitoring)
                self.log_monitoring_summary()
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(2)  # Faster recovery time for auto-sell monitoring
    
    def log_monitoring_summary(self):
        """Log monitoring statistics including recent successful extractions"""
        uptime = time.time() - self.monitoring_start_time
        uptime_hours = uptime / 3600
        
        logger.info(f"📊 MONITORING SUMMARY:")
        logger.info(f"   ⏰ Uptime: {uptime_hours:.1f} hours")
        logger.info(f"   🎯 Tokens processed: {self.monitoring_stats['total_tokens_processed']}")
        logger.info(f"   📢 Notifications sent: {self.monitoring_stats['notifications_sent']}")
        logger.info(f"   🔍 Keywords: {len(self.keywords)}")
        logger.info(f"   💰 API Cost: $0 (Alchemy FREE tier)")
        
        # Show recent successful extractions to make them more visible
        if hasattr(self, 'recent_successful_extractions'):
            if self.recent_successful_extractions:
                logger.info(f"   ✨ Recent successful extractions:")
                for extraction in self.recent_successful_extractions[-5:]:  # Show last 5
                    logger.info(f"      → '{extraction['name']}' ({extraction['method']})")
        
        # Show progressive retry queue status
        if hasattr(self, 'pure_name_extractor') and self.pure_name_extractor:
            pending_retries = getattr(self.pure_name_extractor, 'pending_retry_count', 0)
            if pending_retries > 0:
                logger.info(f"   ⏳ Progressive retries pending: {pending_retries} (expected names in 30s-5min)")
    

    
    def start_monitoring(self):
        """Start all monitoring threads"""
        self.running = True
        
        # Start Token Recovery System
        if self.recovery_system:
            try:
                self.recovery_system.start_recovery_monitoring()
                logger.info("🔄 Token Recovery System started - catching missed tokens during downtime")
            except Exception as e:
                logger.error(f"❌ Failed to start Token Recovery System: {e}")
        
        # Start token monitoring
        monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        monitoring_thread.start()
        logger.info("🔍 Token monitoring thread started")
        
        # Start SPL WebSocket monitoring if available (DISABLED - module not available in deployment)
        # if self.spl_websocket_monitor:
        #     try:
        #         self.spl_websocket_monitor.start_monitoring()
        #         logger.info("🚀 SPL WebSocket monitor started - ultra-fast token detection")
        #     except Exception as e:
        #         logger.error(f"❌ Failed to start SPL WebSocket monitor: {e}")
        # else:
        logger.warning("⚠️ SPL WebSocket monitor not available - using primary monitoring only")
        
        # Market cap alert monitoring disabled (outdated feature)
        
        # Start auto-sell monitoring if available
        if self.auto_sell_monitor:
            auto_sell_thread = threading.Thread(
                target=lambda: asyncio.run(self.auto_sell_monitor.monitor_positions()), 
                daemon=True
            )
            auto_sell_thread.start()
            logger.info("💰 Auto-sell monitoring started")
        
        # Start Discord bot
        discord_thread = self.start_discord_bot()
        
        return monitoring_thread
    
    def setup_discord_bot(self):
        """Setup Discord bot with slash commands"""
        try:
            bot_token = os.getenv("DISCORD_TOKEN")
            if not bot_token:
                logger.warning("⚠️ No Discord bot token found")
                return
            
            # Create bot instance with reference to monitor server
            intents = discord.Intents.default()
            intents.message_content = True
            self.discord_bot = commands.Bot(command_prefix='!', intents=intents)
            
            # Initialize API-free social media cross-feed commands
            if hasattr(self, 'api_free_social_scraper') and self.api_free_social_scraper:
                try:
                    from api_free_social_commands import setup_api_free_social_commands
                    self.api_free_social_commands = setup_api_free_social_commands(self.discord_bot, self.api_free_social_scraper)
                    logger.info("✅ API-free social media cross-feed commands initialized")
                except Exception as e:
                    logger.error(f"❌ Failed to initialize API-free social media commands: {e}")
            
            # Store reference to monitor server for commands
            monitor_server = self
            
            @self.discord_bot.event
            async def on_ready():
                logger.info(f"✅ Discord bot connected as {self.discord_bot.user}")
                
                # Sync slash commands with error handling
                try:
                    synced = await self.discord_bot.tree.sync()
                    logger.info(f"✅ Synced {len(synced)} Discord slash commands")
                    for cmd in synced:
                        logger.info(f"  • /{cmd.name}: {cmd.description}")
                except Exception as e:
                    logger.error(f"❌ Failed to sync Discord commands: {e}")
                    logger.error("This prevents commands from showing up in Discord")
            
            # Add slash commands
            @self.discord_bot.tree.command(name="add", description="Add keyword(s) or URL(s) to monitoring (supports comma-separated bulk additions)")
            @app_commands.describe(
                items="Keyword(s) or URL(s) to monitor (comma-separated for bulk additions)",
                notify_only="For URLs only: True for notifications, False for auto-buy (default: True)",
                max_market_cap="For URLs only: Maximum market cap in USD (optional, no limit if not set)",
                buy_amount="For URLs only: Amount in SOL to buy (default: 0.01)"
            )
            async def add_keyword(interaction: discord.Interaction, items: str, 
                                notify_only: bool = True, max_market_cap: float = None, 
                                buy_amount: float = 0.01):
                try:
                    await interaction.response.defer(ephemeral=True)
                    
                    # Parse multiple items (comma-separated)
                    items_list = [item.strip() for item in items.split(',') if item.strip()]
                    
                    if not items_list:
                        await interaction.followup.send("❌ No items provided to add", ephemeral=True)
                        return
                    
                    if len(items_list) > 20:
                        await interaction.followup.send("❌ Maximum 20 items can be added at once", ephemeral=True)
                        return
                    
                    # Validate parameters for URLs
                    if (max_market_cap is not None and max_market_cap <= 0) or buy_amount <= 0:
                        await interaction.followup.send("❌ Invalid parameters. Market cap (if set) and buy amount must be positive.", ephemeral=True)
                        return
                    
                    added_keywords = []
                    added_urls = []
                    failed_keywords = []
                    failed_urls = []
                    duplicate_keywords = []
                    duplicate_urls = []
                    
                    # Get existing data once for efficiency
                    existing_keywords = monitor_server.config_manager.list_keywords()
                    existing_configs = []
                    if monitor_server.link_sniper:
                        existing_configs = monitor_server.link_sniper.get_user_link_configs(interaction.user.id)
                    
                    # Process each item
                    for item in items_list:
                        # Check if it's a URL
                        if item.startswith(('http://', 'https://')):
                            # Handle URL addition
                            if not monitor_server.link_sniper:
                                failed_urls.append(item)
                                continue
                            
                            # Check if URL already exists
                            url_exists = any(config['target_link'].lower() == item.lower() for config in existing_configs)
                            if url_exists:
                                duplicate_urls.append(item)
                                continue
                            
                            # Add link configuration
                            logger.info(f"🔗 Adding link config for user {interaction.user.id}: {item[:50]}...")
                            success = monitor_server.link_sniper.add_link_config(
                                user_id=interaction.user.id,
                                target_link=item,
                                max_market_cap=max_market_cap,
                                buy_amount=buy_amount,
                                notify_only=notify_only
                            )
                            logger.info(f"🔗 Link config result: {success}")
                            
                            if success:
                                added_urls.append(item)
                                # Update existing configs list to prevent duplicate checking
                                existing_configs.append({'target_link': item})
                            else:
                                failed_urls.append(item)
                        
                        else:
                            # Handle keyword addition
                            # Check if keyword already exists
                            if item.lower() in [k.lower() for k in existing_keywords]:
                                duplicate_keywords.append(item)
                                continue
                            
                            success = monitor_server.config_manager.add_keyword(item)
                            if success:
                                added_keywords.append(item)
                                existing_keywords.append(item)  # Update existing list to prevent duplicates
                                
                                # Track keyword attribution
                                if monitor_server.keyword_attribution:
                                    monitor_server.keyword_attribution.add_keyword_attribution(
                                        item, 
                                        interaction.user.id, 
                                        interaction.user.display_name
                                    )
                            else:
                                failed_keywords.append(item)
                    
                    # Refresh keywords if any were added
                    if added_keywords:
                        monitor_server.keywords = monitor_server.config_manager.list_keywords()
                    
                    # Record action for undo functionality
                    if added_keywords or added_urls:
                        undo_data = {}
                        if added_keywords:
                            undo_data['added_keywords'] = added_keywords
                        if added_urls:
                            undo_data['added_urls'] = added_urls
                            undo_data['user_id'] = interaction.user.id
                        
                        action_type = 'add_keywords' if added_keywords and not added_urls else 'add_urls' if added_urls and not added_keywords else 'add_mixed'
                        monitor_server.undo_manager.record_action(
                            user_id=interaction.user.id,
                            action_type=action_type,
                            action_data=undo_data
                        )
                    
                    # Build response message
                    response_parts = []
                    
                    if added_keywords:
                        response_parts.append(f"✅ **Keywords Added ({len(added_keywords)}):**\n" + 
                                            "\n".join([f"• {kw}" for kw in added_keywords]))
                    
                    if added_urls:
                        mode = "📢 Notifications" if notify_only else "🎯 Auto-buy"
                        response_parts.append(f"✅ **URLs Added ({len(added_urls)}) - {mode}:**\n" + 
                                            "\n".join([f"• {url[:50]}{'...' if len(url) > 50 else ''}" for url in added_urls]))
                        
                        # Add configuration details for URLs
                        if added_urls and not notify_only:
                            config_details = f"💎 **Buy Amount:** {buy_amount} SOL"
                            if max_market_cap is not None:
                                config_details += f" | 💰 **Max Market Cap:** ${max_market_cap:,.0f}"
                            else:
                                config_details += f" | 💰 **Max Market Cap:** No limit"
                            response_parts.append(config_details)
                    
                    if duplicate_keywords:
                        response_parts.append(f"⚠️ **Duplicate Keywords Skipped ({len(duplicate_keywords)}):**\n" + 
                                            "\n".join([f"• {kw}" for kw in duplicate_keywords]))
                    
                    if duplicate_urls:
                        response_parts.append(f"⚠️ **Duplicate URLs Skipped ({len(duplicate_urls)}):**\n" + 
                                            "\n".join([f"• {url[:50]}{'...' if len(url) > 50 else ''}" for url in duplicate_urls]))
                    
                    if failed_keywords:
                        response_parts.append(f"❌ **Failed Keywords ({len(failed_keywords)}):**\n" + 
                                            "\n".join([f"• {kw}" for kw in failed_keywords]))
                    
                    if failed_urls:
                        response_parts.append(f"❌ **Failed URLs ({len(failed_urls)}):**\n" + 
                                            "\n".join([f"• {url[:50]}{'...' if len(url) > 50 else ''}" for url in failed_urls]))
                    
                    if response_parts:
                        # Send response with automatic message splitting for large responses
                        message = "\n\n".join(response_parts)
                        
                        if len(message) <= 1900:
                            await interaction.followup.send(message, ephemeral=True)
                        else:
                            # Send header first
                            total_added = len(added_keywords) + len(added_urls)
                            total_failed = len(duplicate_keywords) + len(duplicate_urls) + len(failed_keywords) + len(failed_urls)
                            await interaction.followup.send(f"📊 **Bulk Add Results: {total_added} added, {total_failed} skipped/failed**", ephemeral=True)
                            
                            # Send each part separately
                            for part in response_parts:
                                if len(part) <= 1900:
                                    await interaction.followup.send(part, ephemeral=True)
                                else:
                                    # Further split if needed
                                    lines = part.split('\n')
                                    current_chunk = lines[0] + '\n'  # Header
                                    for line in lines[1:]:
                                        if len(current_chunk + line + '\n') <= 1900:
                                            current_chunk += line + '\n'
                                        else:
                                            await interaction.followup.send(current_chunk.strip(), ephemeral=True)
                                            current_chunk = line + '\n'
                                    if current_chunk.strip():
                                        await interaction.followup.send(current_chunk.strip(), ephemeral=True)
                    else:
                        await interaction.followup.send("❌ No items were successfully added", ephemeral=True)
                            
                except Exception as e:
                    logger.error(f"Add command error: {e}")
                    if not interaction.response.is_done():
                        await interaction.response.send_message("❌ Error processing your request", ephemeral=True)
            
            @self.discord_bot.tree.command(name="list", description="List all monitoring keywords and URLs")
            async def list_keywords(interaction: discord.Interaction):
                try:
                    await interaction.response.defer(ephemeral=True)
                    
                    # Get keywords
                    keywords = monitor_server.config_manager.list_keywords()
                    
                    # Get user's link configurations
                    link_configs = []
                    if monitor_server.link_sniper:
                        link_configs = monitor_server.link_sniper.get_user_link_configs(interaction.user.id)
                    
                    # Build response
                    response_parts = []
                    
                    if keywords:
                        if monitor_server.keyword_attribution:
                            # Show keywords with attribution info
                            keyword_lines = []
                            for keyword in keywords:
                                attribution = monitor_server.keyword_attribution.get_keyword_attribution(keyword)
                                if attribution:
                                    added_by = attribution['added_by_username'] or f"User {attribution['added_by_user']}"
                                    keyword_lines.append(f"• {keyword} (added by {added_by})")
                                else:
                                    keyword_lines.append(f"• {keyword} (added by System)")
                            response_parts.append(f"🔍 **Keywords ({len(keywords)}):**\n" + "\n".join(keyword_lines))
                        else:
                            keyword_text = ", ".join(keywords)
                            response_parts.append(f"🔍 **Keywords ({len(keywords)}):**\n{keyword_text}")
                    
                    if link_configs:
                        url_text = []
                        for config in link_configs:
                            mode = "📢" if config.get('notify_only') else "🎯"
                            # Show full URL for accurate copying (no truncation for removal)
                            full_url = config['target_link']
                            url_text.append(f"{mode} {full_url}")
                        response_parts.append(f"🔗 **URLs ({len(link_configs)}):**\n" + "\n".join(url_text))
                    
                    if response_parts:
                        message = "\n\n".join(response_parts)
                        
                        # Handle long messages
                        if len(message) <= 1900:
                            await interaction.followup.send(message, ephemeral=True)
                        else:
                            # Send each part separately if too long
                            await interaction.followup.send("📋 **Your Monitoring Configuration:**", ephemeral=True)
                            for part in response_parts:
                                if len(part) <= 1900:
                                    await interaction.followup.send(part, ephemeral=True)
                                else:
                                    # Further split if needed
                                    lines = part.split('\n')
                                    current_chunk = lines[0] + '\n'  # Header
                                    for line in lines[1:]:
                                        if len(current_chunk + line + '\n') <= 1900:
                                            current_chunk += line + '\n'
                                        else:
                                            await interaction.followup.send(current_chunk.strip(), ephemeral=True)
                                            current_chunk = line + '\n'
                                    if current_chunk.strip():
                                        await interaction.followup.send(current_chunk.strip(), ephemeral=True)
                    else:
                        await interaction.followup.send("📝 **No monitoring configured**\n\nUse `/add` to add keywords or URLs to your monitoring.", ephemeral=True)
                        
                except Exception as e:
                    logger.error(f"List command error: {e}")
                    if not interaction.response.is_done():
                        await interaction.response.send_message("❌ Error listing monitoring configuration", ephemeral=True)
            
            @self.discord_bot.tree.command(name="remove", description="Remove keyword or URL from monitoring")
            @app_commands.describe(keyword_or_url="Keyword or URL to remove from monitoring")
            async def remove_keyword(interaction: discord.Interaction, keyword_or_url: str):
                try:
                    await interaction.response.defer(ephemeral=True)
                    
                    keyword_or_url = keyword_or_url.strip()
                    
                    # Check if it's a URL
                    if keyword_or_url.startswith(('http://', 'https://')):
                        # Handle URL removal
                        if not monitor_server.link_sniper:
                            await interaction.followup.send("❌ Link sniper not available", ephemeral=True)
                            return
                        
                        success = monitor_server.link_sniper.remove_link_config(interaction.user.id, keyword_or_url)
                        
                        if success:
                            # Record action for undo
                            monitor_server.undo_manager.record_action(
                                user_id=interaction.user.id,
                                action_type='remove_urls',
                                action_data={
                                    'removed_urls': [keyword_or_url],
                                    'user_id': interaction.user.id
                                }
                            )
                            await interaction.followup.send(f"✅ **URL Removed**\n\n🔗 **Removed:** {keyword_or_url[:60]}{'...' if len(keyword_or_url) > 60 else ''}\n\n↩️ **Use /undo to reverse this removal if needed**", ephemeral=True)
                        else:
                            await interaction.followup.send(f"❌ URL not found in your monitoring list", ephemeral=True)
                    
                    else:
                        # Handle keyword removal
                        success = monitor_server.config_manager.remove_keyword(keyword_or_url)
                        if success:
                            # Record keyword removal in attribution tracking
                            if monitor_server.keyword_attribution:
                                monitor_server.keyword_attribution.remove_keyword_attribution(
                                    keyword_or_url, 
                                    interaction.user.id, 
                                    interaction.user.display_name
                                )
                            
                            # Record action for undo
                            monitor_server.undo_manager.record_action(
                                user_id=interaction.user.id,
                                action_type='remove_keywords',
                                action_data={'removed_keywords': [keyword_or_url]}
                            )
                            # Refresh keywords in monitor
                            monitor_server.keywords = monitor_server.config_manager.list_keywords()
                            await interaction.followup.send(f"✅ **Keyword Removed**\n\n🔍 **Removed:** '{keyword_or_url}'\n\n↩️ **Use /undo to reverse this removal if needed**", ephemeral=True)
                        else:
                            await interaction.followup.send(f"❌ Keyword not found: '{keyword_or_url}'", ephemeral=True)
                            
                except Exception as e:
                    logger.error(f"Remove command error: {e}")
                    if not interaction.response.is_done():
                        await interaction.response.send_message("❌ Error processing removal request", ephemeral=True)
            
            @self.discord_bot.tree.command(name="remove_multiple", description="Remove multiple keywords or URLs at once")
            @app_commands.describe(items="Comma-separated list of keywords or URLs to remove")
            async def remove_multiple(interaction: discord.Interaction, items: str):
                try:
                    await interaction.response.defer(ephemeral=True)
                    
                    # Parse multiple items (comma-separated)
                    items_list = [item.strip() for item in items.split(',') if item.strip()]
                    
                    if not items_list:
                        await interaction.followup.send("❌ No items provided to remove", ephemeral=True)
                        return
                    
                    if len(items_list) > 20:
                        await interaction.followup.send("❌ Maximum 20 items can be removed at once", ephemeral=True)
                        return
                    
                    removed_keywords = []
                    removed_urls = []
                    failed_keywords = []
                    failed_urls = []
                    
                    # Separate keywords and URLs
                    keywords_to_remove = []
                    urls_to_remove = []
                    
                    for item in items_list:
                        if item.startswith(('http://', 'https://')):
                            urls_to_remove.append(item)
                        else:
                            keywords_to_remove.append(item)
                    
                    # Bulk remove keywords
                    if keywords_to_remove:
                        removed_kw, failed_kw = monitor_server.config_manager.remove_multiple_keywords(keywords_to_remove)
                        removed_keywords.extend(removed_kw)
                        failed_keywords.extend(failed_kw)
                        
                        # Track keyword removal attribution for successfully removed keywords
                        if monitor_server.keyword_attribution and removed_kw:
                            for keyword in removed_kw:
                                monitor_server.keyword_attribution.remove_keyword_attribution(
                                    keyword, 
                                    interaction.user.id, 
                                    interaction.user.display_name
                                )
                    
                    # Bulk remove URLs
                    if urls_to_remove and monitor_server.link_sniper:
                        removed_url, failed_url = monitor_server.link_sniper.remove_multiple_link_configs(interaction.user.id, urls_to_remove)
                        removed_urls.extend(removed_url)
                        failed_urls.extend(failed_url)
                    elif urls_to_remove:
                        failed_urls.extend(urls_to_remove)
                    
                    # Refresh keywords if any were removed
                    if removed_keywords:
                        monitor_server.keywords = monitor_server.config_manager.list_keywords()
                    
                    # Build response message
                    response_parts = []
                    
                    if removed_keywords:
                        response_parts.append(f"✅ **Keywords Removed ({len(removed_keywords)}):**\n" + 
                                            "\n".join([f"• {kw}" for kw in removed_keywords]))
                    
                    if removed_urls:
                        response_parts.append(f"✅ **URLs Removed ({len(removed_urls)}):**\n" + 
                                            "\n".join([f"• {url[:50]}{'...' if len(url) > 50 else ''}" for url in removed_urls]))
                    
                    if failed_keywords:
                        response_parts.append(f"❌ **Keywords Not Found ({len(failed_keywords)}):**\n" + 
                                            "\n".join([f"• {kw}" for kw in failed_keywords]))
                    
                    if failed_urls:
                        response_parts.append(f"❌ **URLs Not Found ({len(failed_urls)}):**\n" + 
                                            "\n".join([f"• {url[:50]}{'...' if len(url) > 50 else ''}" for url in failed_urls]))
                    
                    if not response_parts:
                        await interaction.followup.send("❌ No items were removed", ephemeral=True)
                    else:
                        # Record action for undo if anything was removed
                        if removed_keywords or removed_urls:
                            undo_data = {}
                            if removed_keywords:
                                undo_data['removed_keywords'] = removed_keywords
                            if removed_urls:
                                undo_data['removed_urls'] = removed_urls
                                undo_data['user_id'] = interaction.user.id
                            
                            action_type = 'remove_keywords' if removed_keywords and not removed_urls else 'remove_urls' if removed_urls and not removed_keywords else 'remove_mixed'
                            monitor_server.undo_manager.record_action(
                                user_id=interaction.user.id,
                                action_type=action_type,
                                action_data=undo_data
                            )
                        
                        total_removed = len(removed_keywords) + len(removed_urls)
                        total_failed = len(failed_keywords) + len(failed_urls)
                        
                        header = f"🗑️ **Bulk Removal Complete**\n\n📊 **Summary:** {total_removed} removed, {total_failed} failed\n\n"
                        
                        # Add undo tip if anything was removed
                        if total_removed > 0:
                            header += "↩️ **Use /undo to reverse this removal if needed**\n\n"
                        
                        response = header + "\n\n".join(response_parts)
                        
                        # Split response if too long
                        if len(response) <= 1900:
                            await interaction.followup.send(response, ephemeral=True)
                        else:
                            # Send header first
                            await interaction.followup.send(header, ephemeral=True)
                            # Send each part separately
                            for part in response_parts:
                                if len(part) <= 1900:
                                    await interaction.followup.send(part, ephemeral=True)
                                
                except Exception as e:
                    logger.error(f"Remove multiple command error: {e}")
                    if not interaction.response.is_done():
                        await interaction.response.send_message("❌ Error processing bulk removal request", ephemeral=True)
            
            @self.discord_bot.tree.command(name="status", description="Show monitoring status")
            async def status(interaction: discord.Interaction):
                try:
                    if not interaction.response.is_done():
                        uptime = time.time() - monitor_server.monitoring_start_time
                        uptime_hours = uptime / 3600
                        
                        # Get link scraping statistics
                        link_configs_count = 0
                        active_users = 0
                        if monitor_server.link_sniper and monitor_server.link_sniper.link_configs:
                            active_users = len(monitor_server.link_sniper.link_configs)
                            link_configs_count = sum(len(configs) for configs in monitor_server.link_sniper.link_configs.values())
                        
                        # Get BrowserCat scraping status
                        browsercat_status = "🟢 Active" if hasattr(monitor_server, 'enhanced_scraper') and monitor_server.enhanced_scraper else "🔴 Disabled"
                        scraper_status = "🟢 Active" if hasattr(monitor_server, 'browsercat_scraper') and monitor_server.browsercat_scraper else "🔴 Disabled"
                        
                        status_msg = f"""🤖 **Alchemy Monitor Status**

**📊 Core Monitoring:**
⏰ **Uptime:** {uptime_hours:.1f} hours
🔍 **Keywords:** {len(monitor_server.keywords)}
📊 **Tokens Processed:** {monitor_server.monitoring_stats['total_tokens_processed']}
📢 **Notifications:** {monitor_server.monitoring_stats['notifications_sent']}
💰 **Cost:** $0 (Alchemy FREE tier)
⚡ **Speed:** 1-5 second detection

**🔗 Link Scraping System:**
📋 **URL Watchlist:** {link_configs_count} URLs from {active_users} users
🚀 **BrowserCat Extractor:** {browsercat_status}
🌐 **Enhanced Scraper:** {scraper_status}
🎯 **Vue.js SPA Support:** ✅ Enabled
📱 **Social Platforms:** X.com, TikTok, Telegram, Discord

**📊 Scraping Performance:**
🔍 **Total Extractions:** {monitor_server.link_scraping_stats['total_extractions_attempted']}
✅ **Successful Extractions:** {monitor_server.link_scraping_stats['total_extractions_successful']}
🎯 **URL Matches Found:** {monitor_server.link_scraping_stats['url_matches_found']}
📎 **Links Extracted:** {monitor_server.link_scraping_stats['total_links_extracted']}
🌐 **Tokens with Social Links:** {monitor_server.link_scraping_stats['tokens_with_social_links']}
🤖 **BrowserCat Success Rate:** {f"{(monitor_server.link_scraping_stats['browsercat_successes'] / max(1, monitor_server.link_scraping_stats['browsercat_extractions']) * 100):.1f}%" if monitor_server.link_scraping_stats['browsercat_extractions'] > 0 else "N/A"}

**🔧 Extraction Methods:**
• BrowserCat WebSocket (Primary)
• Enhanced social media scraper (Fallback)
• Embedded URL detection (Metadata)
• Multi-method URL matching with normalization"""
                        
                        await interaction.response.send_message(status_msg)
                except discord.errors.InteractionResponded:
                    pass
                except Exception as e:
                    logger.error(f"Status command error: {e}")
            
            @self.discord_bot.tree.command(name="ping", description="Test bot connection")
            async def ping(interaction: discord.Interaction):
                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message("🏓 Pong! Ultra-fast Alchemy monitor is running!")
                except discord.errors.InteractionResponded:
                    pass
                except Exception as e:
                    logger.error(f"Ping command error: {e}")
            
            @self.discord_bot.tree.command(name="refresh", description="Refresh watchlist keywords from file")
            async def refresh_keywords(interaction: discord.Interaction):
                try:
                    if not interaction.response.is_done():
                        # Reload keywords from file
                        old_count = len(monitor_server.keywords)
                        monitor_server.keywords = monitor_server.config_manager.list_keywords()
                        new_count = len(monitor_server.keywords)
                        
                        if new_count != old_count:
                            await interaction.response.send_message(f"✅ Keywords refreshed: {old_count} → {new_count} keywords")
                        else:
                            await interaction.response.send_message(f"✅ Keywords refreshed: {new_count} keywords loaded")
                        
                        logger.info(f"Discord refresh: Reloaded {new_count} keywords")
                except discord.errors.InteractionResponded:
                    pass
                except Exception as e:
                    logger.error(f"Refresh command error: {e}")
            
            @self.discord_bot.tree.command(name="create_wallet", description="Create a new Solana wallet")
            async def create_wallet(interaction: discord.Interaction):
                try:
                    if not interaction.response.is_done():
                        # Generate new Solana keypair
                        keypair = Keypair()
                        
                        # Get public key (wallet address)
                        public_key = str(keypair.pubkey())
                        
                        # Get private key in base58 format
                        private_key_bytes = bytes(keypair)
                        private_key_base58 = base58.b58encode(private_key_bytes).decode('utf-8')
                        
                        # Get SOL balance with better error handling
                        try:
                            pubkey = PublicKey.from_string(public_key)
                            balance_response = client.get_balance(pubkey)
                            balance_lamports = balance_response.value
                            balance_sol = balance_lamports / 1_000_000_000
                            balance_status = f"{balance_sol:.4f} SOL"
                        except Exception as e:
                            balance_sol = 0.0
                            balance_status = "0.0000 SOL (new wallet)"
                        
                        # AUTOMATICALLY CONNECT THE WALLET IN MEMORY AND DATABASE
                        user_id = interaction.user.id
                        monitor_server.connected_wallets[user_id] = {
                            'address': public_key,
                            'keypair': keypair,
                            'connected_at': time.time()
                        }
                        
                        # Save to database for persistence across restarts
                        monitor_server.save_wallet_to_db(user_id, public_key, keypair)
                        
                        # Create secure response (ephemeral message)
                        response = f"""🆕 **New Solana Wallet Created & Connected**

📍 **Wallet Address:**
`{public_key}`

🔑 **Private Key:**
`{private_key_base58}`

💰 **Balance:** {balance_status}
✅ **Status:** Automatically connected and ready for trading!

⚠️ **SECURITY IMPORTANT:**
• Save your private key securely - you need it to access your wallet
• Never share your private key with anyone
• Fund your wallet with SOL before trading
• Your wallet is now connected automatically

🔗 **Solana Explorer:**
https://explorer.solana.com/address/{public_key}

💡 **Next Steps:**
• Use /wallet_balance to check your balance anytime
• Use /my_wallet to see your connected wallet info"""
                        
                        await interaction.response.send_message(response, ephemeral=True)
                        logger.info(f"📱 Discord: Created & auto-connected wallet {public_key[:8]}... for user {interaction.user}")
                        
                except discord.errors.InteractionResponded:
                    pass
                except Exception as e:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(f"❌ Error creating wallet: {str(e)}", ephemeral=True)
                    logger.error(f"Create wallet command error: {e}")
            
            @self.discord_bot.tree.command(name="connect_wallet", description="Connect existing wallet with private key")
            async def connect_wallet(interaction: discord.Interaction, private_key: str):
                try:
                    if not interaction.response.is_done():
                        # Send initial processing message
                        await interaction.response.send_message("🔍 **Connecting Wallet...**\n\n⏳ Validating private key and checking wallet status...", ephemeral=True)
                        
                        # Validate and decode private key with detailed error handling
                        try:
                            # Clean the private key input
                            cleaned_key = private_key.strip()
                            
                            # Check if key looks like base58
                            if len(cleaned_key) < 80 or len(cleaned_key) > 90:
                                await interaction.edit_original_response(content=f"""❌ **Invalid Private Key Length**

Your private key length: {len(cleaned_key)} characters
Expected length: 88 characters (base58 format)

💡 **Common Issues:**
• Make sure you copied the entire private key
• Remove any extra spaces or line breaks
• Private keys should be exactly 88 characters long

🔑 **Example Format:**
`5Kj3N4kM2...` (88 characters total)""")
                                return
                            
                            # Try to decode the private key
                            private_key_bytes = base58.b58decode(cleaned_key)
                            
                            # Check if decoded bytes are correct length
                            if len(private_key_bytes) != 64:
                                await interaction.edit_original_response(content=f"""❌ **Invalid Private Key Format**

Decoded bytes length: {len(private_key_bytes)}
Expected: 64 bytes

💡 **This usually means:**
• The private key contains invalid characters
• The private key is corrupted or incomplete
• Wrong format (not Solana base58 private key)

🔑 **Make sure you're using:**
• A Solana wallet private key (not Ethereum or other chains)
• Base58 encoded format (not hex or other formats)""")
                                return
                            
                            # Create keypair from bytes with enhanced error handling
                            try:
                                keypair = Keypair.from_bytes(private_key_bytes)
                                wallet_address = str(keypair.pubkey())
                            except Exception as keypair_error:
                                # Handle specific Edwards point decompression errors
                                if "decompress Edwards point" in str(keypair_error).lower() or "edwards" in str(keypair_error).lower():
                                    await interaction.edit_original_response(content=f"""❌ **Invalid Solana Private Key**

Error: Cannot create valid Solana keypair from this private key

💡 **This specific error means:**
• Private key is not a valid Solana private key
• Key may be from different blockchain (Ethereum, Bitcoin, etc.)
• Key format is corrupted or modified
• Wrong private key type (seed phrase vs private key)

🔧 **Solutions:**
• Verify this is a Solana private key (not Ethereum/other chains)
• Check if you copied a seed phrase instead of private key
• Use /create_wallet to generate a new Solana wallet
• Export private key from Phantom/Solflare correctly

**Technical:** Edwards curve point decompression failed - invalid key format""")
                                    return
                                else:
                                    # Re-raise other keypair creation errors
                                    raise keypair_error
                            
                        except ValueError as e:
                            # Handle base58 decoding errors (ValueError is what base58 actually raises)
                            if "base58" in str(e).lower() or "invalid" in str(e).lower():
                                await interaction.edit_original_response(content=f"""❌ **Base58 Decoding Error**

Error: {str(e)}

💡 **This means your private key contains invalid characters for base58:**
• Only use: 1-9, A-H, J-N, P-Z, a-k, m-z
• No: 0, I, O, l (zero, capital i, capital o, lowercase L)

🔑 **Double-check your private key for:**
• Typos in characters
• Missing or extra characters
• Copy/paste errors""")
                            else:
                                await interaction.edit_original_response(content=f"""❌ **Private Key Validation Error**

Error: {str(e)}

💡 **Common issues:**
• Invalid private key format
• Corrupted or incomplete key
• Wrong key type (not Solana)""")
                            return
                        except Exception as e:
                            await interaction.edit_original_response(content=f"""❌ **Private Key Validation Failed**

Error: {str(e)}

💡 **Common Solutions:**
• Make sure this is a Solana private key (not Ethereum/Bitcoin)
• Check for copy/paste errors
• Ensure the key is in base58 format
• Try copying the key again from your wallet

🔑 **Need Help?**
• Use /create_wallet to make a new wallet instead
• Contact support if you're sure the key is correct""")
                            return
                        
                        # Test wallet connection to Solana network with enhanced error handling
                        try:
                            pubkey = PublicKey.from_string(wallet_address)
                            
                            # Try multiple RPC endpoints for reliability
                            balance_response = None
                            last_error = None
                            
                            for attempt in range(3):
                                try:
                                    # Get fresh client for each attempt
                                    test_client = get_solana_client()
                                    balance_response = test_client.get_balance(pubkey)
                                    break
                                except Exception as e:
                                    last_error = e
                                    if attempt < 2:  # Don't sleep on last attempt
                                        await asyncio.sleep(1)
                                    continue
                            
                            if balance_response is None:
                                await interaction.edit_original_response(content=f"""❌ **Network Connection Failed**

Error connecting to Solana network: {str(last_error)}

💡 **Network Issue Details:**
• Multiple RPC endpoint attempts failed
• This appears to be a temporary connectivity issue
• Your wallet address was generated successfully

🔧 **Solutions:**
• Wait 30-60 seconds and try again
• Your private key is valid - save it safely
• Try /ping to test bot connectivity
• Use /create_wallet if you prefer a new wallet

Your wallet address: `{wallet_address}`
(This is valid even though network check failed)""")
                                return
                            
                            balance_lamports = balance_response.value
                            balance_sol = balance_lamports / 1_000_000_000
                            
                            # Check if wallet has been used
                            wallet_status = "New wallet" if balance_sol == 0 else "Active wallet"
                            
                        except Exception as e:
                            await interaction.edit_original_response(content=f"""❌ **Wallet Validation Failed**

Error validating wallet: {str(e)}

💡 **This could mean:**
• Invalid wallet address format
• Private key generated incorrect address
• System error in address validation

🔧 **Try:**
• Use /create_wallet to generate a new wallet
• Double-check your private key format
• Contact support if issue persists

Technical details: {str(e)[:100]}...""")
                            return
                        
                        # STORE CONNECTED WALLET IN MEMORY AND DATABASE
                        user_id = interaction.user.id
                        monitor_server.connected_wallets[user_id] = {
                            'address': wallet_address,
                            'keypair': keypair,
                            'connected_at': time.time()
                        }
                        
                        # Save to database for persistence across restarts
                        monitor_server.save_wallet_to_db(user_id, wallet_address, keypair)
                        
                        response = f"""✅ **Wallet Connected Successfully**

📍 **Address:** `{wallet_address}`
💰 **Balance:** {balance_sol:.4f} SOL
🔗 **Status:** {wallet_status} - Connected and ready for trading

🔗 **Solana Explorer:**
https://explorer.solana.com/address/{wallet_address}

⚡ **Trading Ready!** Your wallet is now connected.

💡 **Available Commands:**
• /wallet_balance - Check balance anytime
• /my_wallet - View wallet details
• /buy_token - Purchase tokens with SOL
• /sell_token - Sell tokens for SOL
• /disconnect_wallet - Safely disconnect"""
                        
                        await interaction.edit_original_response(content=response)
                        logger.info(f"📱 Discord: Connected wallet {wallet_address[:8]}... for user {interaction.user}")
                        
                except discord.errors.InteractionResponded:
                    pass
                except Exception as e:
                    try:
                        await interaction.edit_original_response(content=f"❌ Unexpected error: {str(e)}")
                    except:
                        pass
                    logger.error(f"Connect wallet command error: {e}")
            
            @self.discord_bot.tree.command(name="wallet_balance", description="Check wallet balance (uses connected wallet if no address provided)")
            async def wallet_balance(interaction: discord.Interaction, wallet_address: str = None):
                try:
                    if not interaction.response.is_done():
                        user_id = interaction.user.id
                        
                        # Determine which address to check
                        if wallet_address:
                            # User provided specific address
                            source = "provided address"
                            is_connected = False
                        else:
                            # Use connected wallet
                            if user_id not in monitor_server.connected_wallets:
                                response = """❌ **No Wallet Connected**

You need to either:
• Connect a wallet first using /create_wallet or /connect_wallet
• Or provide a specific address: /wallet_balance wallet_address:YOUR_ADDRESS

💡 **Quick Setup:**
• /create_wallet - Creates and connects new wallet
• /connect_wallet - Connects existing wallet with private key"""
                                
                                await interaction.response.send_message(response, ephemeral=True)
                                return
                            
                            wallet_info = monitor_server.connected_wallets[user_id]
                            wallet_address = wallet_info['address']
                            source = "your connected wallet"
                            is_connected = True
                        
                        # Send checking message first
                        await interaction.response.send_message(f"🔍 **Checking Balance**\n\n📍 Address: `{wallet_address[:8]}...`\n⏳ Fetching balance from Solana blockchain...", ephemeral=True)
                        
                        # Validate wallet address format
                        try:
                            public_key = PublicKey.from_string(wallet_address.strip())
                        except Exception:
                            await interaction.edit_original_response(content="❌ **Invalid Address Format**\n\nPlease provide a valid Solana wallet address.")
                            return
                        
                        # Get balance
                        try:
                            balance_response = client.get_balance(public_key)
                            balance_lamports = balance_response.value
                            balance_sol = balance_lamports / 1_000_000_000
                            usd_value = balance_sol * 100  # Approximate SOL price
                            
                            # Format connection status
                            if is_connected:
                                connection_status = "✅ Connected & Ready for Trading"
                                trading_info = """💡 **Trading Available:**
• /buy_token - Purchase tokens with SOL
• /sell_token - Sell tokens for SOL
• /token_price - Check token prices
• /disconnect_wallet - Disconnect this wallet"""
                            else:
                                connection_status = "📋 Address Lookup Only"
                                trading_info = """💡 **For Trading:**
• Use /connect_wallet to enable trading
• Or /create_wallet for new wallet"""
                            
                            response = f"""💰 **Wallet Balance**

📍 **Address:** `{wallet_address}`
💎 **Balance:** {balance_sol:.4f} SOL
💵 **USD Value:** ~${usd_value:.2f} USD
📊 **Source:** {source}
🔗 **Status:** {connection_status}

🔗 **Solana Explorer:**
https://explorer.solana.com/address/{wallet_address}

{trading_info}"""
                            
                            await interaction.edit_original_response(content=response)
                            logger.info(f"📱 Discord: Balance check for user {interaction.user} - {balance_sol:.4f} SOL")
                            
                        except Exception as e:
                            await interaction.edit_original_response(content=f"❌ **Balance Check Failed**\n\nError: {str(e)}\n\n💡 **Common Issues:**\n• Invalid wallet address format\n• Network connectivity issues\n• Temporary API errors")
                            return
                        
                except discord.errors.InteractionResponded:
                    pass
                except Exception as e:
                    try:
                        await interaction.edit_original_response(content=f"❌ Error checking balance: {str(e)}")
                    except:
                        pass
                    logger.error(f"Wallet balance command error: {e}")
            
            @self.discord_bot.tree.command(name="my_wallet", description="Show your connected wallet information")
            async def my_wallet(interaction: discord.Interaction):
                try:
                    if not interaction.response.is_done():
                        user_id = interaction.user.id
                        
                        if user_id not in monitor_server.connected_wallets:
                            response = """❌ **No Wallet Connected**

You don't have a wallet connected yet.

💡 **Get Started:**
• Use /create_wallet to create a new wallet
• Use /connect_wallet to connect existing wallet
• Both commands automatically connect your wallet"""
                            
                            await interaction.response.send_message(response, ephemeral=True)
                            return
                        
                        wallet_info = monitor_server.connected_wallets[user_id]
                        wallet_address = wallet_info['address']
                        connected_at = wallet_info['connected_at']
                        
                        # Get current balance
                        try:
                            pubkey = PublicKey.from_string(wallet_address)
                            balance_response = client.get_balance(pubkey)
                            balance_lamports = balance_response.value
                            balance_sol = balance_lamports / 1_000_000_000
                            balance_status = f"{balance_sol:.4f} SOL"
                            usd_value = f"~${balance_sol * 100:.2f} USD"
                        except:
                            balance_status = "Error fetching balance"
                            usd_value = "Unknown"
                        
                        # Calculate connection time
                        connected_time = time.time() - connected_at
                        if connected_time < 60:
                            time_ago = f"{int(connected_time)} seconds ago"
                        elif connected_time < 3600:
                            time_ago = f"{int(connected_time/60)} minutes ago"
                        else:
                            time_ago = f"{int(connected_time/3600)} hours ago"
                        
                        response = f"""✅ **Your Connected Wallet**

📍 **Address:** `{wallet_address}`
💰 **Balance:** {balance_status}
💵 **USD Value:** {usd_value}
🕒 **Connected:** {time_ago}
✅ **Status:** Ready for trading

🔗 **Solana Explorer:**
https://explorer.solana.com/address/{wallet_address}

💡 **Quick Commands:**
• /wallet_balance - Check current balance
• /create_wallet - Create a new wallet
• /connect_wallet - Connect different wallet"""
                        
                        await interaction.response.send_message(response, ephemeral=True)
                        logger.info(f"📱 Discord: Showed wallet info for user {interaction.user}")
                        
                except discord.errors.InteractionResponded:
                    pass
                except Exception as e:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(f"❌ Error getting wallet info: {str(e)}", ephemeral=True)
                    logger.error(f"My wallet command error: {e}")

            @self.discord_bot.tree.command(name="wallet_holdings", description="Check all token holdings in your connected wallet")
            async def wallet_holdings(interaction: discord.Interaction, address: str = None):
                try:
                    # Immediately defer to prevent timeout
                    await interaction.response.defer(ephemeral=True)
                    
                    user_id = interaction.user.id
                    
                    if address is None:
                        # Use connected wallet
                        if user_id in monitor_server.connected_wallets:
                            address = monitor_server.connected_wallets[user_id]['address']
                        else:
                            await interaction.edit_original_response(content="❌ No wallet connected. Use `/connect_wallet` first or provide an address.")
                            return
                        
                        # Get wallet holdings with timeout protection
                        try:
                            import json
                            import requests
                            import time
                            import asyncio
                            from concurrent.futures import ThreadPoolExecutor, as_completed
                            
                            start_time = time.time()
                            MAX_PROCESSING_TIME = 25  # 25 seconds max to avoid Discord timeout
                            
                            # Use Alchemy RPC for better reliability  
                            alchemy_url = f"https://solana-mainnet.g.alchemy.com/v2/{monitor_server.alchemy_api_key}"
                            
                            await interaction.edit_original_response(content="🔍 Fetching wallet holdings and token data...")
                            
                            # Get SOL balance first
                            sol_payload = {
                                "jsonrpc": "2.0",
                                "id": 1,
                                "method": "getBalance",
                                "params": [address]
                            }
                            sol_response = requests.post(alchemy_url, headers={"Content-Type": "application/json"}, json=sol_payload, timeout=10)
                            sol_balance = 0
                            if sol_response.status_code == 200:
                                sol_data = sol_response.json()
                                if "result" in sol_data:
                                    sol_balance = sol_data["result"]["value"] / 1e9  # Convert lamports to SOL
                            
                            # Make direct RPC call to get token accounts
                            headers = {"Content-Type": "application/json"}
                            payload = {
                                "jsonrpc": "2.0",
                                "id": 1,
                                "method": "getTokenAccountsByOwner",
                                "params": [
                                    address,
                                    {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                                    {"encoding": "jsonParsed"}
                                ]
                            }
                            
                            response = requests.post(alchemy_url, headers=headers, json=payload, timeout=15)
                            response.raise_for_status()
                            rpc_result = response.json()
                            
                            if "error" in rpc_result:
                                raise Exception(f"RPC Error: {rpc_result['error']['message']}")
                            
                            token_accounts = rpc_result.get("result", {}).get("value", [])
                            
                            await interaction.edit_original_response(content=f"🔍 Analyzing {len(token_accounts)} token accounts...")
                            
                            # Fast token metadata resolution with timeout protection
                            def get_token_data_fast(mint, amount):
                                """Get token data with speed optimization"""
                                token_data = {
                                    'name': mint[:8],
                                    'symbol': 'UNKNOWN',
                                    'amount': amount,
                                    'mint': mint,
                                    'value_usd': 0,
                                    'price_usd': 0,
                                    'market_cap': 0,
                                    'source': 'fallback'
                                }
                                
                                # Try DexScreener with shorter timeout for speed
                                try:
                                    dex_url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
                                    dex_response = requests.get(dex_url, timeout=2)  # Reduced timeout
                                    if dex_response.status_code == 200:
                                        dex_data = dex_response.json()
                                        pairs = dex_data.get('pairs', [])
                                        if pairs:
                                            pair = pairs[0]
                                            base_token = pair.get('baseToken', {})
                                            
                                            token_data.update({
                                                'name': base_token.get('name', mint[:8]),
                                                'symbol': base_token.get('symbol', 'UNKNOWN'),
                                                'price_usd': float(pair.get('priceUsd', 0)),
                                                'market_cap': pair.get('fdv', 0) or pair.get('marketCap', 0),
                                                'source': 'dexscreener'
                                            })
                                            token_data['value_usd'] = amount * token_data['price_usd']
                                            return token_data
                                except:
                                    pass
                                
                                return token_data
                            
                            holdings = []
                            processed_count = 0
                            
                            # Process token accounts with timeout protection
                            for account in token_accounts:
                                # Check timeout to prevent Discord timeout
                                if time.time() - start_time > MAX_PROCESSING_TIME:
                                    logger.warning(f"Wallet holdings processing timeout - processed {processed_count}/{len(token_accounts)} tokens")
                                    break
                                    
                                try:
                                    account_data = account['account']['data']
                                    # Parse token account data
                                    mint = account_data['parsed']['info']['mint']
                                    raw_amount = account_data['parsed']['info']['tokenAmount']
                                    amount = float(raw_amount.get('uiAmount', 0) or 0)
                                    decimals = raw_amount.get('decimals', 0)
                                    
                                    if amount > 0:  # Only process non-zero balances
                                        token_data = get_token_data_fast(mint, amount)
                                        token_data['decimals'] = decimals
                                        holdings.append(token_data)
                                        
                                    processed_count += 1
                                    if processed_count % 15 == 0:  # Update progress less frequently
                                        await interaction.edit_original_response(content=f"🔍 Processed {processed_count}/{len(token_accounts)} tokens...")
                                        
                                except Exception as e:
                                    logger.warning(f"Error processing token account: {e}")
                                    continue
                            
                            # Sort by USD value (highest first)
                            holdings.sort(key=lambda x: x['value_usd'], reverse=True)
                            
                            if holdings or sol_balance > 0:
                                # Calculate portfolio analytics
                                total_token_value = sum(h['value_usd'] for h in holdings)
                                sol_price_usd = 0
                                
                                # Get SOL price with timeout protection
                                try:
                                    sol_price_response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd", timeout=2)
                                    if sol_price_response.status_code == 200:
                                        sol_price_data = sol_price_response.json()
                                        sol_price_usd = sol_price_data.get('solana', {}).get('usd', 150)  # Default fallback
                                except:
                                    sol_price_usd = 150  # Fallback price
                                
                                sol_value_usd = sol_balance * sol_price_usd
                                total_portfolio_value = total_token_value + sol_value_usd
                                
                                # Build enhanced response
                                response = f"💰 **Portfolio Summary**\n\n"
                                response += f"📍 **Wallet:** `{address[:8]}...{address[-8:]}`\n"
                                response += f"💵 **Total Value:** ${total_portfolio_value:.2f}\n\n"
                                
                                # SOL holdings
                                if sol_balance > 0:
                                    sol_percentage = (sol_value_usd / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
                                    response += f"◉ **SOL**: {sol_balance:.4f} SOL (${sol_value_usd:.2f}) - {sol_percentage:.1f}%\n"
                                    if sol_price_usd > 0:
                                        response += f"   Price: ${sol_price_usd:.2f}/SOL\n\n"
                                    else:
                                        response += "\n"
                                
                                # Token holdings (top 8 to stay under Discord limits)
                                if holdings:
                                    response += f"🎯 **Token Holdings** ({len(holdings)} tokens):\n\n"
                                    
                                    for i, holding in enumerate(holdings[:8]):
                                        percentage = (holding['value_usd'] / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
                                        
                                        # Enhanced display with more info
                                        response += f"• **{holding['symbol']}** ({holding['name']})\n"
                                        response += f"  💳 Amount: {holding['amount']:,.6f}\n"
                                        
                                        if holding['value_usd'] > 0:
                                            response += f"  💰 Value: ${holding['value_usd']:.2f} ({percentage:.1f}%)\n"
                                            response += f"  💵 Price: ${holding['price_usd']:.8f}\n"
                                            
                                            if holding.get('market_cap', 0) > 0:
                                                response += f"  📊 Market Cap: ${holding['market_cap']:,.0f}\n"
                                        else:
                                            response += f"  💰 Value: No price data\n"
                                        
                                        # Contract address (clickable for easy copying)
                                        response += f"  📄 Contract: `{holding['mint']}`\n"
                                        
                                        # Data source indicator
                                        source_emoji = {"dexscreener": "🔥", "market_api": "📈", "rpc_mint": "⚡", "fallback": "❓"}
                                        response += f"  🔍 Source: {source_emoji.get(holding['source'], '❓')} {holding['source']}\n\n"
                                    
                                    if len(holdings) > 8:
                                        remaining_value = sum(h['value_usd'] for h in holdings[8:])
                                        response += f"... and {len(holdings) - 8} more tokens (${remaining_value:.2f})\n\n"
                                
                                # Portfolio insights
                                if total_portfolio_value > 0:
                                    response += f"📈 **Portfolio Insights:**\n"
                                    if total_token_value > 0:
                                        response += f"• Token allocation: {(total_token_value/total_portfolio_value*100):.1f}%\n"
                                    if sol_value_usd > 0:
                                        response += f"• SOL allocation: {(sol_value_usd/total_portfolio_value*100):.1f}%\n"
                                    response += f"• Active positions: {len(holdings)} tokens\n"
                                    
                                    # Price data quality
                                    priced_tokens = len([h for h in holdings if h['value_usd'] > 0])
                                    if priced_tokens > 0:
                                        response += f"• Price data: {priced_tokens}/{len(holdings)} tokens"
                                
                            else:
                                response = f"""📊 **Token Holdings**

📍 **Wallet:** `{address[:8]}...{address[-8:]}`

💡 **Empty Wallet**
This wallet contains no SOL or token balances."""
                            
                        except Exception as e:
                            logger.error(f"Wallet holdings error: {e}")
                            response = f"""❌ **Holdings Check Failed**
                            
Could not fetch holdings for: `{address[:8]}...{address[-8:]}`

**Error:** {str(e)[:100]}

💡 **Possible Issues:**
• Invalid wallet address format
• Network connectivity issues  
• Solana RPC temporarily unavailable
• Try again in a few moments"""
                        
                        await interaction.edit_original_response(content=response)
                        
                except discord.errors.InteractionResponded:
                    pass
                except Exception as e:
                    try:
                        await interaction.edit_original_response(content=f"❌ Error checking holdings: {str(e)}")
                    except:
                        pass
                    logger.error(f"Wallet holdings command error: {e}")
            
            @self.discord_bot.tree.command(name="disconnect_wallet", description="Disconnect your current wallet")
            async def disconnect_wallet(interaction: discord.Interaction):
                try:
                    if not interaction.response.is_done():
                        user_id = interaction.user.id
                        
                        if user_id not in monitor_server.connected_wallets:
                            response = """❌ **No Wallet Connected**

You don't have a wallet connected to disconnect.

💡 **Available Actions:**
• Use /create_wallet to create a new wallet
• Use /connect_wallet to connect existing wallet"""
                            
                            await interaction.response.send_message(response, ephemeral=True)
                            return
                        
                        # Get wallet info before disconnecting
                        wallet_info = monitor_server.connected_wallets[user_id]
                        wallet_address = wallet_info['address']
                        
                        # Remove wallet from connected wallets
                        del monitor_server.connected_wallets[user_id]
                        
                        response = f"""✅ **Wallet Disconnected Successfully**

📍 **Disconnected Wallet:** `{wallet_address}`
🔒 **Security:** Private key removed from memory
✅ **Status:** Safe to connect different wallet

💡 **Next Steps:**
• Use /create_wallet to create new wallet
• Use /connect_wallet to connect different wallet
• Your old wallet is safe - only the connection was removed

⚠️ **Note:** Save your private key securely if you want to reconnect this wallet later."""
                        
                        await interaction.response.send_message(response, ephemeral=True)
                        logger.info(f"📱 Discord: Disconnected wallet for user {interaction.user}")
                        
                except discord.errors.InteractionResponded:
                    pass
                except Exception as e:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(f"❌ Error disconnecting wallet: {str(e)}", ephemeral=True)
                    logger.error(f"Disconnect wallet command error: {e}")
            
            def format_timestamp_age(self, timestamp):
                """Format timestamp to human readable age"""
                if not timestamp or timestamp == 0:
                    return "Unknown"
                
                import datetime
                try:
                    # Convert milliseconds to seconds if needed
                    if timestamp > 1e12:
                        timestamp = timestamp / 1000
                        
                    creation_time = datetime.datetime.fromtimestamp(timestamp)
                    current_time = datetime.datetime.now()
                    age = current_time - creation_time
                    
                    if age.days > 0:
                        return f"{age.days}d {age.seconds//3600}h ago"
                    elif age.seconds >= 3600:
                        return f"{age.seconds//3600}h {(age.seconds%3600)//60}m ago"
                    elif age.seconds >= 60:
                        return f"{age.seconds//60}m ago"
                    else:
                        return f"{age.seconds}s ago"
                except:
                    return "Unknown"
            
            @self.discord_bot.tree.command(name="og_coins", description="Check if OG coins already exist for a URL, keyword, or contract address")
            async def og_coins(interaction: discord.Interaction, search_term: str):
                """Check if existing coins match a URL, keyword, or contract address - includes pre-migration tokens"""
                try:
                    await interaction.response.defer(ephemeral=True)
                    
                    logger.info(f"📱 Discord: Enhanced search for: {search_term}")
                    
                    # FIRST: Search our internal database for pre-migration tokens
                    internal_tokens = monitor_server.search_detected_tokens(search_term, limit=15)
                    
                    # Determine search type: contract address, URL, or keyword
                    is_contract_address = len(search_term) >= 32 and len(search_term) <= 44 and search_term.replace('_', '').replace('-', '').isalnum()
                    is_url = search_term.startswith(('http://', 'https://'))
                    
                    # Build response starting with internal results
                    response_parts = []
                    
                    if internal_tokens:
                        response_parts.append(f"🚀 **Found {len(internal_tokens)} tokens in our database:**\n")
                        
                        for i, token in enumerate(internal_tokens[:5], 1):
                            status_emoji = "🔄" if token['status'] == 'pre_migration' else "✅"
                            migration_status = "Pre-Migration (not on Raydium yet)" if token['status'] == 'pre_migration' else "Migrated to Raydium"
                            
                            response_parts.append(f"**{i}.** {token['name']} ({token['symbol']})")
                            response_parts.append(f"   {status_emoji} Status: {migration_status}")
                            response_parts.append(f"   📍 Contract: `{token['address']}`")
                            response_parts.append(f"   🕐 Detected: {token['detection_timestamp'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(token['detection_timestamp'], 'strftime') else str(token['detection_timestamp'])}")
                            
                            if token.get('matched_keywords'):
                                response_parts.append(f"   🎯 Keywords: {', '.join(token['matched_keywords'])}")
                            
                            if token['status'] == 'pre_migration':
                                response_parts.append(f"   🔗 [LetsBonk.fun](https://letsbonk.fun/token/{token['address']})")
                            elif token.get('market_cap', 0) > 0:
                                response_parts.append(f"   💰 Market Cap: ${token['market_cap']:,.0f}")
                                response_parts.append(f"   📊 [DexScreener](https://dexscreener.com/solana/{token['address']})")
                            
                            response_parts.append("")  # Empty line for spacing
                        
                        if len(internal_tokens) > 5:
                            response_parts.append(f"... and {len(internal_tokens) - 5} more results from our database\n")
                    
                    # Compile final response
                    if not internal_tokens and not is_contract_address:
                        # No internal results for keyword/name search - search external APIs
                        response_parts.append(f"🔍 **No pre-migration tokens found for '{search_term}'**\n")
                        response_parts.append("This could mean:")
                        response_parts.append("• Token hasn't been detected by our monitoring system yet")
                        response_parts.append("• Token may only exist on external platforms")
                        response_parts.append("• Search term doesn't match any token names")
                        response_parts.append("")
                        response_parts.append("💡 **Try searching:**")
                        response_parts.append("• Contract address if you have it") 
                        response_parts.append("• Alternative spellings or abbreviations")
                        response_parts.append("• Social media URL if available")
                    
                    # Build final response
                    if response_parts:
                        final_response = "\n".join(response_parts)
                        
                        # Add helpful footer
                        final_response += "\n\n" + "="*40 + "\n"
                        final_response += "🚀 **System Enhancement:** This search now includes pre-migration tokens!\n"
                        final_response += "✅ Pre-migration tokens are detected immediately when created\n" 
                        final_response += "🔄 They become searchable even before hitting 70k market cap\n"
                        final_response += "📈 No more missing early opportunities like 'plan b'!\n"
                    else:
                        final_response = f"❌ **No results found for '{search_term}'**\n\nTry searching with a different term or contract address."
                    
                    await interaction.edit_original_response(content=final_response)
                    logger.info(f"📱 Enhanced search completed for: {search_term} - Found {len(internal_tokens)} internal results")
                    
                except Exception as e:
                    logger.error(f"Enhanced og_coins search error: {e}")
                    await interaction.edit_original_response(content=f"❌ Search error: {str(e)}")
            
            logger.info("✅ Enhanced Discord commands registered successfully")
                                    
                                    time.sleep(0.1)  # Rate limiting
                                except:
                                    continue
                            
                        except Exception as e:
                            logger.error(f"Error searching for URL matches: {e}")
                        
                        # Build response for URL search
                        if found_tokens:
                            response = f"🎯 **Found {len(found_tokens)} coins with matching URLs**\n\n"
                            response += f"🔗 **Search URL:** {search_term[:60]}{'...' if len(search_term) > 60 else ''}\n\n"
                            
                            for i, token in enumerate(found_tokens[:5], 1):  # Show top 5
                                response += f"**{i}.** {token['name']}\n"
                                response += f"   📍 **Contract:** `{token['address']}`\n"
                                response += f"   🔗 Matching URL: {token['matching_url'][:50]}{'...' if len(token['matching_url']) > 50 else ''}\n"
                                response += f"   📊 [DexScreener](https://dexscreener.com/solana/{token['address']})\n\n"
                            
                            if len(found_tokens) > 5:
                                response += f"... and {len(found_tokens) - 5} more matches\n\n"
                            
                            response += "💡 **Note:** These tokens have social media links matching your URL"
                        else:
                            response = f"❌ **No coins found with matching URLs**\n\n"
                            response += f"🔗 **Searched URL:** {search_term[:60]}{'...' if len(search_term) > 60 else ''}\n\n"
                            response += "💡 **This URL appears to be unique!** You can set up monitoring for it:\n"
                            response += f"• Use `/add {search_term}` to monitor for new tokens with this URL\n"
                            response += "• The system will notify you when a token is created with this social media link"
                    
                    else:
                        # Keyword search - check against DexScreener and recent tokens
                        await interaction.edit_original_response(content="🔍 Searching for coins with matching keywords...")
                        
                        found_tokens = []
                        
                        try:
                            import requests
                            
                            # Search DexScreener for tokens matching the keyword
                            search_url = f"https://api.dexscreener.com/latest/dex/search/?q={search_term}"
                            
                            response_data = requests.get(search_url, timeout=10)
                            if response_data.status_code == 200:
                                search_results = response_data.json()
                                
                                # Filter for Solana tokens
                                for pair in search_results.get('pairs', []):
                                    if pair.get('chainId') == 'solana':
                                        token = pair.get('baseToken', {})
                                        token_name = token.get('name', '').lower()
                                        token_symbol = token.get('symbol', '').lower()
                                        
                                        # Check if keyword matches - improved matching logic
                                        keyword_lower = search_term.lower()
                                        search_words = keyword_lower.split()
                                        
                                        # Check for exact substring match first
                                        exact_match = keyword_lower in token_name or keyword_lower in token_symbol
                                        
                                        # Check for partial word matches (any word in search term matches token)
                                        partial_match = False
                                        if not exact_match and len(search_words) > 1:
                                            for word in search_words:
                                                if len(word) >= 2 and (word in token_name or word in token_symbol):
                                                    partial_match = True
                                                    break
                                        
                                        # Check for reverse match (token name words in search term)
                                        reverse_match = False
                                        if not exact_match and not partial_match:
                                            token_words = token_name.split() + token_symbol.split()
                                            for token_word in token_words:
                                                if len(token_word) >= 2 and token_word in keyword_lower:
                                                    reverse_match = True
                                                    break
                                        
                                        if exact_match or partial_match or reverse_match:
                                            # Check if it's a LetsBonk token
                                            token_address = token.get('address', '')
                                            is_letsbonk = token_address.endswith('bonk')
                                            
                                            found_tokens.append({
                                                'address': token_address,
                                                'name': token.get('name', 'Unknown'),
                                                'symbol': token.get('symbol', 'TOKEN'),
                                                'market_cap': pair.get('fdv', 0),
                                                'price': pair.get('priceUsd', '0'),
                                                'volume_24h': pair.get('volume', {}).get('h24', 0),
                                                'is_letsbonk': is_letsbonk,
                                                'created_at': pair.get('pairCreatedAt', 0)
                                            })
                            
                            # Sort by market cap (highest first)
                            found_tokens.sort(key=lambda x: x.get('market_cap', 0), reverse=True)
                            
                        except Exception as e:
                            logger.error(f"Error searching DexScreener: {e}")
                        
                        # Build response for keyword search
                        if found_tokens:
                            letsbonk_tokens = [t for t in found_tokens if t['is_letsbonk']]
                            other_tokens = [t for t in found_tokens if not t['is_letsbonk']]
                            
                            response = f"📊 **Found {len(found_tokens)} coins matching '{search_term}'**\n\n"
                            
                            if letsbonk_tokens:
                                response += f"🎯 **LetsBonk.fun Tokens ({len(letsbonk_tokens)}):**\n"
                                for i, token in enumerate(letsbonk_tokens[:3], 1):
                                    market_cap = token.get('market_cap', 0)
                                    market_cap_str = f"${market_cap:,.0f}" if market_cap > 0 else "Unknown"
                                    response += f"**{i}.** {token['name']} ({token['symbol']})\n"
                                    response += f"   💰 Market Cap: {market_cap_str}\n"
                                    response += f"   📍 **Contract:** `{token['address']}`\n"
                                    response += f"   📊 [Trade](https://dexscreener.com/solana/{token['address']})\n\n"
                                
                                if len(letsbonk_tokens) > 3:
                                    response += f"   ... and {len(letsbonk_tokens) - 3} more LetsBonk tokens\n\n"
                            
                            if other_tokens:
                                response += f"🔹 **Other Solana Tokens ({len(other_tokens)}):**\n"
                                for i, token in enumerate(other_tokens[:2], 1):
                                    market_cap = token.get('market_cap', 0)
                                    market_cap_str = f"${market_cap:,.0f}" if market_cap > 0 else "Unknown"
                                    response += f"**{i}.** {token['name']} ({token['symbol']})\n"
                                    response += f"   💰 Market Cap: {market_cap_str}\n"
                                    response += f"   📍 **Contract:** `{token['address']}`\n\n"
                            
                            response += f"💡 **Monitoring Tip:** Use `/add {search_term}` to get notified of new tokens with this keyword"
                        else:
                            response = f"❌ **No existing coins found for '{search_term}'**\n\n"
                            response += "💡 **This keyword appears to be unique!** Perfect for monitoring:\n"
                            response += f"• Use `/add {search_term}` to monitor for new tokens with this keyword\n"
                            response += "• You'll get instant notifications when matching tokens are created\n"
                            response += "• This gives you first-mover advantage on fresh tokens!"
                    
                    await interaction.edit_original_response(content=response)
                    logger.info(f"📱 Discord: Completed coin search for user {interaction.user}")
                    
                except Exception as e:
                    error_msg = f"❌ Error searching for existing coins: {str(e)}"
                    try:
                        await interaction.edit_original_response(content=error_msg)
                    except:
                        if not interaction.response.is_done():
                            await interaction.response.send_message(error_msg, ephemeral=True)
                    logger.error(f"Check existing coins command error: {e}")

            @self.discord_bot.tree.command(name="buy_token", description="Buy token with SOL")
            async def buy_token(interaction: discord.Interaction, token_address: str, sol_amount: float, slippage: int = 1):
                try:
                    if not interaction.response.is_done():
                        user_id = interaction.user.id
                        
                        # Check if user has connected wallet
                        if user_id not in monitor_server.connected_wallets:
                            await interaction.response.send_message("❌ No wallet connected. Use /create_wallet or /connect_wallet first.", ephemeral=True)
                            return
                        
                        # Validate inputs
                        if sol_amount <= 0:
                            await interaction.response.send_message("❌ SOL amount must be greater than 0.", ephemeral=True)
                            return
                        
                        if slippage < 0 or slippage > 50:
                            await interaction.response.send_message("❌ Slippage must be between 0% and 50%.", ephemeral=True)
                            return
                        
                        # Get user's keypair
                        wallet_info = monitor_server.connected_wallets[user_id]
                        user_keypair = wallet_info['keypair']
                        wallet_address = wallet_info['address']
                        
                        # Check SOL balance
                        try:
                            pubkey = PublicKey.from_string(wallet_address)
                            balance_response = client.get_balance(pubkey)
                            balance_lamports = balance_response.value
                            balance_sol = balance_lamports / 1_000_000_000
                            
                            if balance_sol < sol_amount:
                                await interaction.response.send_message(f"❌ Insufficient SOL balance. You have {balance_sol:.4f} SOL, but need {sol_amount} SOL.", ephemeral=True)
                                return
                            
                        except Exception as e:
                            await interaction.response.send_message(f"❌ Error checking balance: {str(e)}", ephemeral=True)
                            return
                        
                        # Send initial response
                        await interaction.response.send_message(f"🔄 **Processing Buy Order**\n\n💰 Buying with {sol_amount} SOL\n📍 Token: `{token_address[:8]}...`\n⚡ Slippage: {slippage}%\n\n⏳ Getting quote and executing trade...", ephemeral=True)
                        
                        # Execute trade
                        slippage_bps = slippage * 100  # Convert percentage to basis points
                        success, message, trade_info = trader.buy_token(user_keypair, token_address, sol_amount, slippage_bps)
                        
                        if success:
                            # Get token info for better display
                            try:
                                from market_data_api import market_data_api
                                token_data = market_data_api.get_token_data(token_address)
                                token_name = token_data.get('name', 'Unknown Token') if token_data else 'Unknown Token'
                                token_symbol = token_data.get('symbol', 'TOKEN') if token_data else 'TOKEN'
                            except:
                                token_name = 'Unknown Token'
                                token_symbol = 'TOKEN'
                            
                            response = f"""✅ **Buy Order Successful!**

📊 **Trade Details:**
• Token: {token_name} ({token_symbol})
• Spent: {trade_info.get('input_amount', sol_amount)} SOL
• Received: {trade_info.get('output_amount', 0):.6f} {token_symbol}
• Slippage: {slippage}%

🔗 **Transaction:**
https://explorer.solana.com/tx/{trade_info.get('signature', 'unknown')}

🔗 **Token Info:**
https://dexscreener.com/solana/{token_address}

💡 **Next Steps:**
• Use /wallet_balance to check updated balance
• Use /sell_token to sell when ready"""
                            
                        else:
                            response = f"""❌ **Buy Order Failed**

{message}

💡 **Common Issues:**
• Insufficient SOL for transaction fees
• Token not tradeable on Jupiter DEX
• Network congestion - try again
• Invalid token address"""
                        
                        # Edit the original response
                        await interaction.edit_original_response(content=response)
                        logger.info(f"📱 Discord: Buy order for user {interaction.user} - Success: {success}")
                        
                except discord.errors.InteractionResponded:
                    pass
                except Exception as e:
                    try:
                        await interaction.edit_original_response(content=f"❌ Error executing buy order: {str(e)}")
                    except:
                        pass
                    logger.error(f"Buy token command error: {e}")
            
            @self.discord_bot.tree.command(name="sell_token", description="Sell token for SOL")
            async def sell_token(interaction: discord.Interaction, token_address: str, amount: float, slippage: int = 1):
                try:
                    if not interaction.response.is_done():
                        user_id = interaction.user.id
                        
                        # Check if user has connected wallet
                        if user_id not in monitor_server.connected_wallets:
                            await interaction.response.send_message("❌ No wallet connected. Use /create_wallet or /connect_wallet first.", ephemeral=True)
                            return
                        
                        # Validate inputs
                        if amount <= 0:
                            await interaction.response.send_message("❌ Token amount must be greater than 0.", ephemeral=True)
                            return
                        
                        if slippage < 0 or slippage > 50:
                            await interaction.response.send_message("❌ Slippage must be between 0% and 50%.", ephemeral=True)
                            return
                        
                        # Get user's keypair
                        wallet_info = monitor_server.connected_wallets[user_id]
                        user_keypair = wallet_info['keypair']
                        wallet_address = wallet_info['address']
                        
                        # Check token balance
                        token_balance = trader.get_token_balance(wallet_address, token_address)
                        if token_balance < amount:
                            await interaction.response.send_message(f"❌ Insufficient token balance. You have {token_balance:.6f} tokens, but need {amount} tokens.", ephemeral=True)
                            return
                        
                        # Send initial response
                        await interaction.response.send_message(f"🔄 **Processing Sell Order**\n\n🪙 Selling {amount} tokens\n📍 Token: `{token_address[:8]}...`\n⚡ Slippage: {slippage}%\n\n⏳ Getting quote and executing trade...", ephemeral=True)
                        
                        # Execute trade
                        slippage_bps = slippage * 100  # Convert percentage to basis points
                        success, message, trade_info = trader.sell_token(user_keypair, token_address, amount, slippage_bps)
                        
                        if success:
                            # Get token info for better display
                            try:
                                from market_data_api import market_data_api
                                token_data = market_data_api.get_token_data(token_address)
                                token_name = token_data.get('name', 'Unknown Token') if token_data else 'Unknown Token'
                                token_symbol = token_data.get('symbol', 'TOKEN') if token_data else 'TOKEN'
                            except:
                                token_name = 'Unknown Token'
                                token_symbol = 'TOKEN'
                            
                            response = f"""✅ **Sell Order Successful!**

📊 **Trade Details:**
• Token: {token_name} ({token_symbol})
• Sold: {trade_info.get('input_amount', amount)} {token_symbol}
• Received: {trade_info.get('output_amount', 0):.6f} SOL
• Slippage: {slippage}%

🔗 **Transaction:**
https://explorer.solana.com/tx/{trade_info.get('signature', 'unknown')}

💡 **Next Steps:**
• Use /wallet_balance to check updated balance
• Profits are now in SOL in your wallet"""
                            
                        else:
                            response = f"""❌ **Sell Order Failed**

{message}

💡 **Common Issues:**
• Insufficient tokens to sell
• Token not tradeable on Jupiter DEX
• Network congestion - try again
• No liquidity for this token"""
                        
                        # Edit the original response
                        await interaction.edit_original_response(content=response)
                        logger.info(f"📱 Discord: Sell order for user {interaction.user} - Success: {success}")
                        
                except discord.errors.InteractionResponded:
                    pass
                except Exception as e:
                    try:
                        await interaction.edit_original_response(content=f"❌ Error executing sell order: {str(e)}")
                    except:
                        pass
                    logger.error(f"Sell token command error: {e}")
            
            @self.discord_bot.tree.command(name="token_price", description="Get current token price in SOL")
            async def token_price(interaction: discord.Interaction, token_address: str):
                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(f"🔍 **Getting Token Price**\n\n📍 Token: `{token_address[:8]}...`\n⏳ Fetching current market data...", ephemeral=True)
                        
                        # Get token price
                        price_sol = trader.get_token_price(token_address)
                        
                        if price_sol is not None:
                            # Get token info for better display
                            try:
                                from market_data_api import market_data_api
                                token_data = market_data_api.get_token_data(token_address)
                                if token_data:
                                    token_name = token_data.get('name', 'Unknown Token')
                                    token_symbol = token_data.get('symbol', 'TOKEN')
                                    market_cap = token_data.get('market_cap', 0)
                                    volume_24h = token_data.get('volume_24h', 0)
                                else:
                                    token_name = 'Unknown Token'
                                    token_symbol = 'TOKEN'
                                    market_cap = 0
                                    volume_24h = 0
                            except:
                                token_name = 'Unknown Token'
                                token_symbol = 'TOKEN'
                                market_cap = 0
                                volume_24h = 0
                            
                            price_usd = price_sol * 100  # Approximate SOL price
                            
                            response = f"""💰 **Token Price Info**

📊 **{token_name} ({token_symbol})**
💎 **Price:** {price_sol:.8f} SOL
💵 **Price USD:** ~${price_usd:.6f}
📈 **Market Cap:** ${market_cap:,.0f}
📊 **24h Volume:** ${volume_24h:,.0f}

🔗 **Links:**
• [DexScreener](https://dexscreener.com/solana/{token_address})
• [Solana Explorer](https://explorer.solana.com/address/{token_address})

💡 **Trading:**
• Use /buy_token to purchase with SOL
• Use /sell_token to sell for SOL"""
                            
                        else:
                            response = f"""❌ **Price Not Available**

Could not fetch price for token: `{token_address}`

💡 **Possible Reasons:**
• Token not tradeable on Jupiter DEX
• No liquidity pools available
• Invalid token address
• Network issues"""
                        
                        # Edit the original response
                        await interaction.edit_original_response(content=response)
                        
                except discord.errors.InteractionResponded:
                    pass
                except Exception as e:
                    try:
                        await interaction.edit_original_response(content=f"❌ Error getting token price: {str(e)}")
                    except:
                        pass
                    logger.error(f"Token price command error: {e}")
                    logger.error(f"Wallet balance command error: {e}")

            @self.discord_bot.tree.command(name="clear", description="Clear all keywords from watchlist")
            async def clear_keywords(interaction: discord.Interaction):
                try:
                    if not interaction.response.is_done():
                        # Clear all keywords
                        success = monitor_server.config_manager.clear_keywords()
                        if success:
                            monitor_server.keywords = []
                            await interaction.response.send_message("✅ All keywords cleared from watchlist")
                        else:
                            await interaction.response.send_message("❌ Failed to clear keywords")
                except discord.errors.InteractionResponded:
                    pass
                except Exception as e:
                    logger.error(f"Clear command error: {e}")
            
            @self.discord_bot.tree.command(name="clear_all", description="Clear ALL monitoring (keywords AND URLs)")
            async def clear_all_monitoring(interaction: discord.Interaction):
                try:
                    await interaction.response.defer(ephemeral=True)
                    
                    # Get current state for undo
                    current_keywords = monitor_server.config_manager.list_keywords()
                    current_configs = []
                    if monitor_server.link_sniper:
                        current_configs = monitor_server.link_sniper.get_user_link_configs(interaction.user.id)
                    
                    cleared_keywords = 0
                    cleared_urls = 0
                    
                    # Clear keywords
                    keyword_success = monitor_server.config_manager.clear_keywords()
                    if keyword_success:
                        cleared_keywords = len(monitor_server.keywords)
                        
                        # Track keyword removal attribution for all cleared keywords
                        if monitor_server.keyword_attribution and current_keywords:
                            for keyword in current_keywords:
                                monitor_server.keyword_attribution.remove_keyword_attribution(
                                    keyword, 
                                    interaction.user.id, 
                                    interaction.user.display_name
                                )
                        
                        monitor_server.keywords = []
                    
                    # Clear URLs
                    if monitor_server.link_sniper:
                        cleared_urls = monitor_server.link_sniper.clear_user_link_configs(interaction.user.id)
                    
                    # Record action for undo
                    if cleared_keywords > 0 or cleared_urls > 0:
                        monitor_server.undo_manager.record_action(
                            user_id=interaction.user.id,
                            action_type='clear_all',
                            action_data={
                                'cleared_keywords': current_keywords,
                                'cleared_configs': current_configs,
                                'user_id': interaction.user.id
                            }
                        )
                    
                    if keyword_success or cleared_urls > 0:
                        response = f"""✅ **Complete Monitoring Clear**

🔍 **Keywords Removed:** {cleared_keywords}
🔗 **URLs Removed:** {cleared_urls}

Your monitoring system has been completely reset.

↩️ **Use /undo to reverse this action if needed**"""
                        await interaction.followup.send(response, ephemeral=True)
                    else:
                        await interaction.followup.send("❌ No monitoring configurations found to clear", ephemeral=True)
                        
                except Exception as e:
                    logger.error(f"Clear all command error: {e}")
                    if not interaction.response.is_done():
                        await interaction.response.send_message("❌ Error clearing all monitoring", ephemeral=True)
            
            @self.discord_bot.tree.command(name="undo", description="Undo your last action (add, remove, clear)")
            async def undo_last_action(interaction: discord.Interaction):
                try:
                    await interaction.response.defer(ephemeral=True)
                    
                    # Get last action for user
                    last_action = monitor_server.undo_manager.get_last_action(interaction.user.id)
                    
                    if not last_action:
                        await interaction.followup.send("❌ No recent actions to undo", ephemeral=True)
                        return
                    
                    # Show what will be undone
                    action_desc = monitor_server.undo_manager._format_action_description(
                        last_action['action_type'], 
                        last_action['data']
                    )
                    
                    # Perform undo
                    result = monitor_server.undo_manager.undo_last_action(interaction.user.id)
                    
                    if result['success']:
                        # Refresh keywords if any were changed
                        monitor_server.keywords = monitor_server.config_manager.list_keywords()
                        
                        response = f"""↩️ **Action Undone Successfully**

📝 **Reversed Action:** {action_desc}

{result['message']}

💡 Your monitoring configuration has been restored to its previous state."""
                    else:
                        response = f"""❌ **Undo Failed**

{result['message']}"""
                    
                    await interaction.followup.send(response, ephemeral=True)
                    
                except Exception as e:
                    logger.error(f"Undo command error: {e}")
                    await interaction.followup.send("❌ Error performing undo operation", ephemeral=True)
            
            @self.discord_bot.tree.command(name="keyword_attribution", description="View who added each keyword")
            async def keyword_attribution_command(interaction: discord.Interaction):
                try:
                    await interaction.response.defer(ephemeral=True)
                    
                    if not monitor_server.keyword_attribution:
                        await interaction.followup.send("❌ Keyword attribution tracking is not available", ephemeral=True)
                        return
                    
                    # Get all keyword attributions
                    attributions = monitor_server.keyword_attribution.get_all_keyword_attributions()
                    
                    if not attributions:
                        await interaction.followup.send("📝 No keyword attributions found", ephemeral=True)
                        return
                    
                    # Group by user
                    users_keywords = {}
                    for attr in attributions:
                        username = attr['added_by_username'] or f"User {attr['added_by_user']}"
                        if username not in users_keywords:
                            users_keywords[username] = []
                        users_keywords[username].append(attr['keyword'])
                    
                    # Format response
                    response_parts = [f"👥 **Keyword Attribution ({len(attributions)} total keywords):**\n"]
                    
                    for username, keywords in users_keywords.items():
                        keywords_text = ", ".join(keywords[:10])  # Limit to first 10 keywords per user
                        if len(keywords) > 10:
                            keywords_text += f" ... and {len(keywords) - 10} more"
                        response_parts.append(f"**{username}** ({len(keywords)}):\n{keywords_text}")
                    
                    message = "\n\n".join(response_parts)
                    
                    # Handle long messages
                    if len(message) <= 1900:
                        await interaction.followup.send(message, ephemeral=True)
                    else:
                        # Send summary first
                        summary = f"👥 **Keyword Attribution Summary:**\n\n"
                        for username, keywords in users_keywords.items():
                            summary += f"• **{username}**: {len(keywords)} keywords\n"
                        
                        await interaction.followup.send(summary, ephemeral=True)
                        await interaction.followup.send("💡 **Use /list to see detailed keyword attributions**", ephemeral=True)
                    
                except Exception as e:
                    logger.error(f"Keyword attribution command error: {e}")
                    await interaction.followup.send("❌ Error retrieving keyword attributions", ephemeral=True)

            @self.discord_bot.tree.command(name="history", description="View your recent action history")
            async def view_action_history(interaction: discord.Interaction):
                try:
                    await interaction.response.defer(ephemeral=True)
                    
                    # Get user's action history
                    history = monitor_server.undo_manager.get_user_history(interaction.user.id, limit=10)
                    
                    if not history:
                        await interaction.followup.send("📝 No recent actions found", ephemeral=True)
                        return
                    
                    # Format history display
                    history_text = []
                    for i, entry in enumerate(reversed(history), 1):
                        timestamp = entry['timestamp']
                        action = entry['action']
                        
                        # Parse timestamp for relative time
                        from datetime import datetime
                        try:
                            action_time = datetime.fromisoformat(timestamp)
                            time_ago = datetime.now() - action_time
                            
                            if time_ago.total_seconds() < 60:
                                time_str = "just now"
                            elif time_ago.total_seconds() < 3600:
                                mins = int(time_ago.total_seconds() / 60)
                                time_str = f"{mins}m ago"
                            else:
                                hours = int(time_ago.total_seconds() / 3600)
                                time_str = f"{hours}h ago"
                        except:
                            time_str = "unknown time"
                        
                        history_text.append(f"{i}. {action} ({time_str})")
                    
                    response = f"""📋 **Your Recent Actions**

{chr(10).join(history_text)}

↩️ **Use /undo to reverse your most recent action**
📝 **Tip:** Only the last action can be undone"""
                    
                    await interaction.followup.send(response, ephemeral=True)
                    
                except Exception as e:
                    logger.error(f"History command error: {e}")
                    await interaction.followup.send("❌ Error retrieving action history", ephemeral=True)

            @self.discord_bot.tree.command(name="trading_settings", description="Configure your trading settings")
            async def trading_settings(interaction: discord.Interaction, 
                                     setting: str = None, 
                                     value: str = None):
                try:
                    if not interaction.response.is_done():
                        from trading_settings import TradingSettingsManager
                        settings_manager = TradingSettingsManager()
                        user_id = str(interaction.user.id)
                        
                        if setting is None:
                            # Show current settings
                            user_settings = settings_manager.get_user_settings(user_id)
                            quick_amounts = user_settings.get('quick_buy_amounts', [0.1, 0.5, 1.0])
                            sell_percentages = user_settings.get('quick_sell_percentages', [10.0, 25.0, 50.0, 100.0])
                            slippage = user_settings.get('default_slippage', 1.0)
                            priority_fee = user_settings.get('priority_fee', 0.001)
                            mev_protection = user_settings.get('mev_protection', True)
                            compute_units = user_settings.get('compute_units', 200000)
                            
                            response = f"""⚙️ **Your Trading Settings**

💰 **Quick Buy Amounts:**
• Button 1: {quick_amounts[0]} SOL
• Button 2: {quick_amounts[1]} SOL  
• Button 3: {quick_amounts[2]} SOL

📊 **Quick Sell Percentages:**
• Button 1: {sell_percentages[0]}%
• Button 2: {sell_percentages[1]}%
• Button 3: {sell_percentages[2]}%
• Button 4: {sell_percentages[3]}%

⚙️ **Advanced Settings:**
• Slippage: {slippage}%
• Priority Fee: {priority_fee} SOL
• MEV Protection: {"✅ Enabled" if mev_protection else "❌ Disabled"}
• Compute Units: {compute_units:,}

🔧 **How to Update:**
• `/trading_settings amounts "0.05,0.2,0.8"` - Set buy amounts
• `/trading_settings percentages "5,15,30,75"` - Set sell percentages
• `/trading_settings slippage "2.5"` - Set slippage percentage
• `/trading_settings priority_fee "0.002"` - Set priority fee in SOL
• `/trading_settings mev_protection "true"` - Enable/disable MEV protection
• `/trading_settings compute_units "300000"` - Set compute units"""
                            
                            await interaction.response.send_message(response, ephemeral=True)
                            return
                        
                        # Update settings
                        if setting.lower() == "amounts" and value:
                            try:
                                amounts = [float(x.strip()) for x in value.split(',')]
                                if len(amounts) == 3 and all(0.01 <= x <= 10 for x in amounts):
                                    success = settings_manager.set_quick_buy_amounts(user_id, amounts)
                                    if success:
                                        await interaction.response.send_message(
                                            f"✅ **Updated Quick Buy Amounts**\n• {amounts[0]} SOL, {amounts[1]} SOL, {amounts[2]} SOL",
                                            ephemeral=True
                                        )
                                    else:
                                        await interaction.response.send_message("❌ Failed to update settings", ephemeral=True)
                                else:
                                    await interaction.response.send_message(
                                        "❌ Invalid amounts. Use 3 values between 0.01-10 SOL\nExample: `0.1,0.5,1.0`",
                                        ephemeral=True
                                    )
                            except ValueError:
                                await interaction.response.send_message(
                                    "❌ Invalid format. Use: `0.1,0.5,1.0`",
                                    ephemeral=True
                                )
                        
                        elif setting.lower() == "percentages" and value:
                            try:
                                percentages = [float(x.strip()) for x in value.split(',')]
                                if len(percentages) == 4 and all(0.1 <= x <= 100 for x in percentages):
                                    success = settings_manager.set_quick_sell_percentages(user_id, percentages)
                                    if success:
                                        await interaction.response.send_message(
                                            f"✅ **Updated Quick Sell Percentages**\n• {percentages[0]}%, {percentages[1]}%, {percentages[2]}%, {percentages[3]}%",
                                            ephemeral=True
                                        )
                                    else:
                                        await interaction.response.send_message("❌ Failed to update settings", ephemeral=True)
                                else:
                                    await interaction.response.send_message(
                                        "❌ Invalid percentages. Use 4 values between 0.1-100%\nExample: `10,25,50,100`",
                                        ephemeral=True
                                    )
                            except ValueError:
                                await interaction.response.send_message(
                                    "❌ Invalid format. Use: `10,25,50,100`",
                                    ephemeral=True
                                )
                        
                        elif setting.lower() == "slippage" and value:
                            try:
                                slippage = float(value)
                                if 0.1 <= slippage <= 50:
                                    success = settings_manager.set_slippage(user_id, slippage)
                                    if success:
                                        await interaction.response.send_message(
                                            f"✅ **Updated Default Slippage**\n• {slippage}%",
                                            ephemeral=True
                                        )
                                    else:
                                        await interaction.response.send_message("❌ Failed to update slippage", ephemeral=True)
                                else:
                                    await interaction.response.send_message(
                                        "❌ Slippage must be between 0.1% and 50%",
                                        ephemeral=True
                                    )
                            except ValueError:
                                await interaction.response.send_message(
                                    "❌ Invalid slippage value. Use a number like: `1.5`",
                                    ephemeral=True
                                )
                        
                        elif setting.lower() == "priority_fee" and value:
                            try:
                                priority_fee = float(value)
                                if 0 <= priority_fee <= 0.1:
                                    success = settings_manager.set_priority_fee(user_id, priority_fee)
                                    if success:
                                        await interaction.response.send_message(
                                            f"✅ **Updated Priority Fee**\n• {priority_fee} SOL",
                                            ephemeral=True
                                        )
                                    else:
                                        await interaction.response.send_message("❌ Failed to update priority fee", ephemeral=True)
                                else:
                                    await interaction.response.send_message(
                                        "❌ Priority fee must be between 0 and 0.1 SOL",
                                        ephemeral=True
                                    )
                            except ValueError:
                                await interaction.response.send_message(
                                    "❌ Invalid priority fee. Use a number like: `0.002`",
                                    ephemeral=True
                                )
                        
                        elif setting.lower() == "mev_protection" and value:
                            try:
                                enabled = value.lower() in ['true', 'yes', '1', 'on', 'enabled']
                                success = settings_manager.set_mev_protection(user_id, enabled)
                                if success:
                                    status = "✅ Enabled" if enabled else "❌ Disabled"
                                    await interaction.response.send_message(
                                        f"✅ **Updated MEV Protection**\n• {status}",
                                        ephemeral=True
                                    )
                                else:
                                    await interaction.response.send_message("❌ Failed to update MEV protection", ephemeral=True)
                            except Exception:
                                await interaction.response.send_message(
                                    "❌ Invalid MEV protection value. Use: `true` or `false`",
                                    ephemeral=True
                                )
                        
                        elif setting.lower() == "compute_units" and value:
                            try:
                                compute_units = int(value)
                                if 100000 <= compute_units <= 1000000:
                                    success = settings_manager.set_compute_units(user_id, compute_units)
                                    if success:
                                        await interaction.response.send_message(
                                            f"✅ **Updated Compute Units**\n• {compute_units:,} units",
                                            ephemeral=True
                                        )
                                    else:
                                        await interaction.response.send_message("❌ Failed to update compute units", ephemeral=True)
                                else:
                                    await interaction.response.send_message(
                                        "❌ Compute units must be between 100,000 and 1,000,000",
                                        ephemeral=True
                                    )
                            except ValueError:
                                await interaction.response.send_message(
                                    "❌ Invalid compute units. Use a number like: `300000`",
                                    ephemeral=True
                                )
                        else:
                            await interaction.response.send_message(
                                "❌ Invalid setting. Available options:\n• `amounts` - Set buy amounts\n• `percentages` - Set sell percentages\n• `slippage` - Set slippage %\n• `priority_fee` - Set priority fee\n• `mev_protection` - Enable/disable MEV protection\n• `compute_units` - Set compute units",
                                ephemeral=True
                            )
                            
                except discord.errors.InteractionResponded:
                    pass
                except Exception as e:
                    logger.error(f"Trading settings command error: {e}")
                    if not interaction.response.is_done():
                        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
            
            # Quick Trading Commands
            @self.discord_bot.tree.command(name="quick_buy_01", description="Quick buy 0.01 SOL worth of tokens")
            async def quick_buy_01(interaction: discord.Interaction, contract_address: str):
                await self.quick_buy_handler(interaction, contract_address, 0.01, monitor_server, trader)
            
            @self.discord_bot.tree.command(name="quick_buy_05", description="Quick buy 0.02 SOL worth of tokens")
            async def quick_buy_05(interaction: discord.Interaction, contract_address: str):
                await self.quick_buy_handler(interaction, contract_address, 0.02, monitor_server, trader)
            
            @self.discord_bot.tree.command(name="quick_buy_1", description="Quick buy 0.03 SOL worth of tokens")
            async def quick_buy_1(interaction: discord.Interaction, contract_address: str):
                await self.quick_buy_handler(interaction, contract_address, 0.03, monitor_server, trader)
            
            @self.discord_bot.tree.command(name="quick_sell_10", description="Quick sell 10% of token holdings")
            async def quick_sell_10(interaction: discord.Interaction, contract_address: str):
                await self.quick_sell_handler(interaction, contract_address, 0.10, monitor_server, trader)
            
            @self.discord_bot.tree.command(name="quick_sell_25", description="Quick sell 25% of token holdings")
            async def quick_sell_25(interaction: discord.Interaction, contract_address: str):
                await self.quick_sell_handler(interaction, contract_address, 0.25, monitor_server, trader)
            
            @self.discord_bot.tree.command(name="quick_sell_50", description="Quick sell 50% of token holdings")
            async def quick_sell_50(interaction: discord.Interaction, contract_address: str):
                await self.quick_sell_handler(interaction, contract_address, 0.50, monitor_server, trader)
            
            @self.discord_bot.tree.command(name="quick_sell_all", description="Quick sell 100% of token holdings")
            async def quick_sell_all(interaction: discord.Interaction, contract_address: str):
                await self.quick_sell_handler(interaction, contract_address, 1.0, monitor_server, trader)

            # Auto-Sell Commands
            @self.discord_bot.tree.command(name="set_auto_sell", description="Set auto-sell order for a token")
            async def set_auto_sell(interaction: discord.Interaction, 
                                  contract_address: str,
                                  sell_percentage: float,
                                  target_gain_percentage: float = None,
                                  max_loss_percentage: float = None,
                                  target_market_cap: int = None):
                await self.auto_sell_setup_handler(interaction, contract_address, sell_percentage, 
                                                 target_gain_percentage, max_loss_percentage, target_market_cap)
            
            @self.discord_bot.tree.command(name="list_auto_sells", description="List your active auto-sell orders")
            async def list_auto_sells(interaction: discord.Interaction):
                await self.list_auto_sells_handler(interaction)
            
            @self.discord_bot.tree.command(name="remove_auto_sell", description="Remove an auto-sell order")
            async def remove_auto_sell(interaction: discord.Interaction, contract_address: str):
                await self.remove_auto_sell_handler(interaction, contract_address)
            
            @self.discord_bot.tree.command(name="set_auto_sell_market_cap", description="Set market cap-based auto-sell order for token")
            @app_commands.describe(
                contract_address="Token contract address (e.g., ABC123...xyz)",
                sell_percentage="Percentage of holdings to sell (1-100)",
                target_market_cap="Target market cap to trigger sell (e.g., 1000000 for $1M)"
            )
            async def set_auto_sell_market_cap(interaction: discord.Interaction, contract_address: str, 
                                             sell_percentage: float, target_market_cap: int):
                """Set market cap-based auto-sell order for specific token"""
                try:
                    await interaction.response.defer(ephemeral=True)
                    
                    if not monitor_server or not hasattr(monitor_server, 'auto_sell_monitor'):
                        await interaction.followup.send("❌ Auto-sell system not available", ephemeral=True)
                        return
                    
                    # Validate parameters
                    if not contract_address or len(contract_address) < 32:
                        await interaction.followup.send("❌ Invalid contract address format", ephemeral=True)
                        return
                    
                    if not (1 <= sell_percentage <= 100):
                        await interaction.followup.send("❌ Sell percentage must be between 1-100%", ephemeral=True)
                        return
                    
                    if target_market_cap <= 0:
                        await interaction.followup.send("❌ Target market cap must be positive", ephemeral=True)
                        return
                    
                    # Check if user has a connected wallet
                    user_id = interaction.user.id
                    if user_id not in monitor_server.connected_wallets:
                        await interaction.followup.send(
                            "❌ **Wallet Required**\n\n"
                            "You need to connect a wallet first to set auto-sell orders.\n"
                            "Use `/connect_wallet` or `/create_wallet` to get started.",
                            ephemeral=True
                        )
                        return
                    
                    # Get token info for confirmation
                    try:
                        from market_data_api import get_market_data_api
                        market_api = get_market_data_api()
                        token_info = market_api.get_token_info(contract_address)
                        token_name = token_info.get('name', f"{contract_address[:8]}...{contract_address[-8:]}")
                        current_market_cap = token_info.get('market_cap', 0)
                        
                        # Store auto-sell configuration in database (market cap version)
                        success = monitor_server.auto_sell_monitor.add_auto_sell_order(
                            user_id=user_id,
                            contract_address=contract_address,
                            sell_percentage=sell_percentage,
                            target_market_cap=target_market_cap,
                            token_name=token_name,
                            entry_market_cap=current_market_cap
                        )
                        
                        if success:
                            await interaction.followup.send(
                                f"✅ **Market Cap Auto-Sell Order Set**\n\n"
                                f"**Token:** {token_name}\n"
                                f"**Contract:** `{contract_address[:8]}...{contract_address[-8:]}`\n"
                                f"**Sell Amount:** {sell_percentage}% of holdings\n"
                                f"**Target Market Cap:** ${target_market_cap:,}\n"
                                f"**Current Market Cap:** ${current_market_cap:,}\n\n"
                                f"🤖 **Auto-sell will trigger when market cap reaches ${target_market_cap:,}**",
                                ephemeral=True
                            )
                            logger.info(f"💰 Market cap auto-sell order set for user {user_id}: {token_name} at ${target_market_cap:,}")
                        else:
                            await interaction.followup.send("❌ Failed to set auto-sell order", ephemeral=True)
                            
                    except Exception as e:
                        logger.error(f"❌ Error getting token info: {e}")
                        await interaction.followup.send("❌ Error retrieving token information", ephemeral=True)
                        
                except Exception as e:
                    logger.error(f"❌ Error in set_auto_sell_market_cap command: {e}")
                    if not interaction.response.is_done():
                        await interaction.response.send_message("❌ Error setting market cap auto-sell order", ephemeral=True)
            
            logger.info("✅ Discord bot commands configured (core monitoring and trading commands only)")
            
            # Duplicate on_ready handler removed to prevent conflicts
            
        except Exception as e:
            logger.error(f"Discord bot setup error: {e}")
    
    def start_discord_bot(self):
        """Start Discord bot in separate thread"""
        if not self.discord_bot:
            return
        
        async def bot_loop():
            try:
                # Use the correct Discord bot token from environment
                bot_token = os.getenv("DISCORD_TOKEN")
                if bot_token and len(bot_token.strip()) > 50:  # Valid Discord tokens are much longer
                    logger.info(f"✅ Discord bot token loaded (length: {len(bot_token)})")
                    try:
                        await self.discord_bot.start(bot_token.strip())
                    except discord.LoginFailure:
                        logger.error("❌ Discord bot login failed - token is invalid")
                        logger.error("Please verify your Discord bot token is correct")
                    except Exception as e:
                        logger.error(f"❌ Discord bot connection error: {e}")
                else:
                    logger.error(f"❌ Invalid DISCORD_TOKEN (length: {len(bot_token) if bot_token else 0})")
            except Exception as e:
                logger.error(f"Discord bot error: {e}")
        
        def sync_bot_loop():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(bot_loop())
            loop.close()
        
        bot_thread = threading.Thread(target=sync_bot_loop, daemon=True)
        bot_thread.start()
        logger.info("🤖 Discord bot thread started")
        return bot_thread
    
    async def quick_buy_handler(self, interaction, contract_address: str, amount_sol: float, monitor_server, trader):
        """Handle quick buy operations"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            if user_id not in monitor_server.connected_wallets:
                await interaction.followup.send("❌ **No Wallet Connected**\nPlease use `/connect_wallet` or `/create_wallet` first.", ephemeral=True)
                return
            
            wallet_info = monitor_server.connected_wallets[user_id]
            user_keypair = wallet_info['keypair']
            
            slippage_bps = 200  # 2% slippage for quick trades
            
            await interaction.followup.send(
                f"🚀 **Quick Buy Started**\nBuying {amount_sol} SOL worth of tokens...\nContract: `{contract_address[:8]}...`\nSlippage: 2%", 
                ephemeral=True
            )
            
            success, message, trade_info = trader.buy_token(user_keypair, contract_address, amount_sol, slippage_bps)
            
            if success:
                response = f"""✅ **Quick Buy Successful!**
                
• Amount: {amount_sol} SOL
• Tokens: {trade_info.get('output_amount', 0):.6f}
• Contract: `{contract_address[:8]}...`

🔗 https://explorer.solana.com/tx/{trade_info.get('signature', 'unknown')}

💡 Use `/sell_token` to sell when ready"""
                await interaction.followup.send(response, ephemeral=True)
            else:
                await interaction.followup.send(f"❌ **Quick Buy Failed**\n{message}", ephemeral=True)
        except Exception as e:
            try:
                await interaction.followup.send(f"❌ **Quick Buy Error**\nError: {str(e)}", ephemeral=True)
            except:
                pass
            logger.error(f"Quick buy error: {e}")

    async def auto_sell_setup_handler(self, interaction, contract_address: str, sell_percentage: float,
                                    target_gain_percentage: float = None, max_loss_percentage: float = None,
                                    target_market_cap: int = None):
        """Handle auto-sell setup command"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            # Validate inputs
            if sell_percentage <= 0 or sell_percentage > 100:
                await interaction.followup.send("❌ Sell percentage must be between 0.1 and 100", ephemeral=True)
                return
            
            if not target_gain_percentage and not max_loss_percentage and not target_market_cap:
                await interaction.followup.send("❌ Must specify at least one trigger: target_gain_percentage, max_loss_percentage, or target_market_cap", ephemeral=True)
                return
            
            # Get token name
            token_name = "Unknown Token"
            try:
                from market_data_api import MarketDataAPI
                market_api = MarketDataAPI()
                token_data = market_api.get_token_data(contract_address)
                if token_data:
                    token_name = token_data.get('name', 'Unknown Token')
            except Exception as e:
                logger.warning(f"Could not get token name: {e}")
            
            # Create auto-sell order
            if hasattr(self, 'auto_sell_monitor') and self.auto_sell_monitor:
                success = self.auto_sell_monitor.create_auto_sell_order(
                    user_id, contract_address, token_name, sell_percentage,
                    target_gain_percentage, max_loss_percentage, target_market_cap
                )
                
                if success:
                    response = f"✅ **Auto-Sell Order Created**\n\n"
                    response += f"🪙 **Token:** {token_name}\n"
                    response += f"📊 **Sell Amount:** {sell_percentage}%\n"
                    
                    if target_gain_percentage:
                        response += f"📈 **Target Gain:** {target_gain_percentage}%\n"
                    
                    if max_loss_percentage:
                        response += f"📉 **Stop Loss:** {max_loss_percentage}%\n"
                    
                    if target_market_cap:
                        response += f"💰 **Target Market Cap:** ${target_market_cap:,}\n"
                    
                    response += f"\n💡 The system will automatically sell when any condition is met."
                    
                    await interaction.followup.send(response, ephemeral=True)
                else:
                    await interaction.followup.send("❌ Failed to create auto-sell order. May already exist.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Auto-sell system not available", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Auto-sell setup error: {e}")
            try:
                await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
            except:
                pass

    async def list_auto_sells_handler(self, interaction):
        """Handle list auto-sells command"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            if hasattr(self, 'auto_sell_monitor') and self.auto_sell_monitor:
                orders = self.auto_sell_monitor.get_user_auto_sell_orders(user_id)
                
                if not orders:
                    await interaction.followup.send("📋 **No Auto-Sell Orders**\n\nYou don't have any active auto-sell orders.\nUse `/set_auto_sell` to create one.", ephemeral=True)
                    return
                
                response = f"📋 **Your Auto-Sell Orders** ({len(orders)})\n\n"
                
                for i, order in enumerate(orders, 1):
                    response += f"**{i}. {order['token_name']}**\n"
                    response += f"   • Contract: `{order['contract_address'][:8]}...`\n"
                    response += f"   • Sell Amount: {order['sell_percentage']}%\n"
                    
                    if order['target_gain_percentage']:
                        response += f"   • Target Gain: {order['target_gain_percentage']}%\n"
                    
                    if order['max_loss_percentage']:
                        response += f"   • Stop Loss: {order['max_loss_percentage']}%\n"
                    
                    if order['target_market_cap']:
                        response += f"   • Target Market Cap: ${order['target_market_cap']:,}\n"
                    
                    response += f"   • Created: {order['created_at'].strftime('%Y-%m-%d %H:%M')}\n\n"
                
                # Split long messages
                if len(response) > 1900:
                    await interaction.followup.send(response[:1900] + "...", ephemeral=True)
                else:
                    await interaction.followup.send(response, ephemeral=True)
            else:
                await interaction.followup.send("❌ Auto-sell system not available", ephemeral=True)
                
        except Exception as e:
            logger.error(f"List auto-sells error: {e}")
            try:
                await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
            except:
                pass

    async def remove_auto_sell_handler(self, interaction, contract_address: str):
        """Handle remove auto-sell command"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            
            if hasattr(self, 'auto_sell_monitor') and self.auto_sell_monitor:
                success = self.auto_sell_monitor.remove_auto_sell_order(user_id, contract_address)
                
                if success:
                    await interaction.followup.send(f"✅ **Auto-Sell Order Removed**\n\nRemoved auto-sell order for contract `{contract_address[:8]}...`", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ **No Order Found**\n\nNo active auto-sell order found for contract `{contract_address[:8]}...`", ephemeral=True)
            else:
                await interaction.followup.send("❌ Auto-sell system not available", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Remove auto-sell error: {e}")
            try:
                await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
            except:
                pass

    async def quick_sell_handler(self, interaction, contract_address: str, percentage: float, monitor_server, trader):
        """Handle quick sell operations"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            user_id = interaction.user.id
            if user_id not in monitor_server.connected_wallets:
                await interaction.followup.send("❌ **No Wallet Connected**\nPlease use `/connect_wallet` or `/create_wallet` first.", ephemeral=True)
                return
            
            wallet_info = monitor_server.connected_wallets[user_id]
            user_keypair = wallet_info['keypair']
            wallet_address = wallet_info['address']
            
            # Get current token balance
            try:
                token_balance = trader.get_token_balance(wallet_address, contract_address)
                if token_balance is None or token_balance <= 0:
                    await interaction.followup.send("❌ **No Tokens Found**\nYou don't have any tokens to sell for this contract.", ephemeral=True)
                    return
            except Exception as balance_error:
                await interaction.followup.send(f"❌ **Balance Check Failed**\n{str(balance_error)}", ephemeral=True)
                return
            
            # Calculate amount to sell
            amount_to_sell = float(token_balance) * percentage
            percentage_display = f"{int(percentage * 100)}%"
            
            if amount_to_sell <= 0:
                await interaction.followup.send("❌ **Invalid Amount**\nToken balance is too low to sell.", ephemeral=True)
                return
            
            await interaction.followup.send(
                f"🔄 **Quick Sell Started**\nSelling {percentage_display} of holdings...\nTokens: {amount_to_sell:.6f}\nContract: `{contract_address[:8]}...`", 
                ephemeral=True
            )
            
            # Use customizable slippage from user settings
            from trading_settings import TradingSettingsManager
            settings_manager = TradingSettingsManager()
            user_settings = settings_manager.get_user_settings(str(user_id))
            slippage = user_settings.get('default_slippage', 2.0)
            slippage_bps = int(slippage * 100)  # Convert to basis points
            
            success, message, trade_info = trader.sell_token(user_keypair, contract_address, amount_to_sell, slippage_bps)
            
            if success and trade_info:
                output_amount = trade_info.get('output_amount', 0)
                signature = trade_info.get('signature', 'unknown')
                
                response = f"""✅ **Quick Sell Successful!**

• Sold: {percentage_display} ({amount_to_sell:.6f} tokens)
• Received: {output_amount:.6f} SOL
• Contract: `{contract_address[:8]}...`

🔗 https://explorer.solana.com/tx/{signature}

💰 Use `/wallet_balance` to check balance"""
                await interaction.followup.send(response, ephemeral=True)
            else:
                error_msg = message if message else "Unknown error occurred"
                await interaction.followup.send(f"❌ **Quick Sell Failed**\n{error_msg}", ephemeral=True)
                
        except discord.errors.InteractionResponded:
            # Interaction already responded to
            pass
        except Exception as e:
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(f"❌ **Quick Sell Error**\nError: {str(e)}", ephemeral=True)
                else:
                    await interaction.followup.send(f"❌ **Quick Sell Error**\nError: {str(e)}", ephemeral=True)
            except:
                pass
            logger.error(f"Quick sell error: {e}")
    
        # Additional Discord commands
        if self.discord_bot:
            @self.discord_bot.tree.command(name="check_token_links", description="Check social media links for a token")
            async def check_token_links(interaction: discord.Interaction, token_address: str):
                """Check social media and website links for a token"""
                try:
                    if not interaction.response.is_done():
                        await interaction.response.send_message(
                            f"🔍 **Checking Social Links**\n\nSearching for social media links for token `{token_address[:8]}...`\nThis may take a few seconds...", 
                            ephemeral=True
                        )
                        
                        if self.token_link_validator:
                            # Get token links
                            links_data = self.token_link_validator.get_token_links(token_address)
                            
                            if links_data.get('error'):
                                await interaction.edit_original_response(content=f"❌ **Error checking links**: {links_data['error']}")
                                return
                            
                            # Build response message
                            if not links_data.get('has_social'):
                                response = f"""🔗 **Social Media Check Results**

**Token:** `{token_address[:8]}...{token_address[-8:]}`
**Status:** No social media links found

This token doesn't appear to have associated social media accounts."""
                            else:
                                verified_links = links_data.get('verified_links', [])
                                working_links = [link for link in verified_links if link.get('working')]
                                broken_links = [link for link in verified_links if not link.get('working')]
                                
                                response = f"""🔗 **Social Media Check Results**

**Token:** `{token_address[:8]}...{token_address[-8:]}`
**Total Links Found:** {links_data.get('total_links', 0)}

"""
                                
                                if working_links:
                                    response += "✅ **Working Links:**\n"
                                    for link in working_links[:5]:  # Limit to 5 links
                                        platform = link['platform'].title()
                                        url = link['url']
                                        response += f"• [{platform}]({url})\n"
                                    response += "\n"
                                
                                if broken_links:
                                    response += "❌ **Broken/Inaccessible Links:**\n"
                                    for link in broken_links[:3]:  # Limit to 3 broken links
                                        platform = link['platform'].title()
                                        response += f"• {platform} (Error: {link.get('error', 'Not accessible')})\n"
                                
                                response += f"\n💡 **Note:** Links verified at {datetime.now().strftime('%H:%M UTC')}"
                            
                            await interaction.edit_original_response(content=response)
                            logger.info(f"📱 Discord: Checked token links for {token_address[:8]}... - found {links_data.get('total_links', 0)} links")
                        else:
                            await interaction.edit_original_response(content="❌ **Link validator not available**\nContact support if this issue persists.")
                            
                except discord.errors.InteractionResponded:
                    pass
                except Exception as e:
                    logger.error(f"❌ Error in check_token_links command: {e}")
                    if not interaction.response.is_done():
                        await interaction.response.send_message(
                            "❌ An error occurred while checking token links.",
                            ephemeral=True
                        )
            
            # Auto-sell command handlers have been completely cleaned up
            
            @self.discord_bot.tree.command(name="list_auto_sells", description="View all your active auto-sell orders")
            async def list_auto_sells(interaction: discord.Interaction):
                """List user's auto-sell orders"""
                try:
                    await interaction.response.defer(ephemeral=True)
                    
                    if not monitor_server or not hasattr(monitor_server, 'auto_sell_monitor'):
                        await interaction.followup.send("❌ Auto-sell system not available", ephemeral=True)
                        return
                    
                    user_id = interaction.user.id
                    orders = monitor_server.auto_sell_monitor.get_user_auto_sell_orders(user_id)
                    
                    if not orders:
                        await interaction.followup.send(
                            "📝 **No Auto-Sell Orders**\n\n"
                            "You don't have any active auto-sell orders.\n"
                            "Use `/set_auto_sell` to create one.",
                            ephemeral=True
                        )
                        return
                    
                    message = f"📊 **Your Auto-Sell Orders ({len(orders)})**\n\n"
                    
                    for i, order in enumerate(orders[:10], 1):  # Limit to 10 orders
                        contract = order.get('contract_address', 'Unknown')
                        token_name = order.get('token_name', f"{contract[:8]}...{contract[-8:]}")
                        sell_pct = order.get('sell_percentage', 0)
                        gain_pct = order.get('target_gain_percentage', 0)
                        loss_pct = order.get('max_loss_percentage')
                        
                        message += f"**{i}.** {token_name}\n"
                        message += f"   📝 `{contract[:8]}...{contract[-8:]}`\n"
                        message += f"   💰 Sell: {sell_pct}% | 📈 Target: +{gain_pct}%"
                        
                        if loss_pct:
                            message += f" | 🛡️ Stop: -{loss_pct}%"
                        
                        message += "\n\n"
                    
                    if len(orders) > 10:
                        message += f"... and {len(orders) - 10} more orders\n\n"
                    
                    message += "💡 Use `/remove_auto_sell` to cancel specific orders"
                    
                    await interaction.followup.send(message, ephemeral=True)
                    
                except Exception as e:
                    logger.error(f"❌ Error in list_auto_sells command: {e}")
                    if not interaction.response.is_done():
                        await interaction.response.send_message("❌ Error fetching auto-sell orders", ephemeral=True)
            
            @self.discord_bot.tree.command(name="remove_auto_sell", description="Remove specific auto-sell order")
            @app_commands.describe(contract_address="Token contract address to remove auto-sell for")
            async def remove_auto_sell(interaction: discord.Interaction, contract_address: str):
                """Remove auto-sell order"""
                try:
                    await interaction.response.defer(ephemeral=True)
                    
                    if not monitor_server or not hasattr(monitor_server, 'auto_sell_monitor'):
                        await interaction.followup.send("❌ Auto-sell system not available", ephemeral=True)
                        return
                    
                    user_id = interaction.user.id
                    success = monitor_server.auto_sell_monitor.remove_auto_sell_order(user_id, contract_address)
                    
                    if success:
                        await interaction.followup.send(
                            f"✅ **Auto-Sell Order Removed**\n\n"
                            f"Removed auto-sell order for `{contract_address[:8]}...{contract_address[-8:]}`",
                            ephemeral=True
                        )
                        logger.info(f"🗑️ Auto-sell order removed for user {user_id}: {contract_address[:8]}...")
                    else:
                        await interaction.followup.send(
                            f"❌ **No Order Found**\n\n"
                            f"No auto-sell order found for `{contract_address[:8]}...{contract_address[-8:]}`",
                            ephemeral=True
                        )
                        
                except Exception as e:
                    logger.error(f"❌ Error in remove_auto_sell command: {e}")
                    if not interaction.response.is_done():
                        await interaction.response.send_message("❌ Error removing auto-sell order", ephemeral=True)
            

    
    # Alert checking removed - outdated feature

    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        if self.discord_bot:
            self.discord_bot.close()
        # Market cap alert system removed
        logger.info("🛑 Monitoring stopped")

# Flask web server for health checks
app = Flask(__name__)
monitor_server = None

@app.route('/')
def index():
    return jsonify({
        "status": "running",
        "service": "Alchemy Token Monitor",
        "cost": "$0/month (FREE tier)",
        "stats": monitor_server.monitoring_stats if monitor_server else {}
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "seen_tokens": len(monitor_server.seen_token_addresses) if hasattr(monitor_server, 'seen_token_addresses') else 0,
        "websocket_signatures": len(getattr(monitor_server, 'websocket_signatures', [])),
        "last_processed": getattr(monitor_server, 'last_processed_time', None),
        "total_tokens_processed": monitor_server.monitoring_stats.get('total_tokens_processed', 0) if monitor_server else 0,
        "notifications_sent": monitor_server.monitoring_stats.get('notifications_sent', 0) if monitor_server else 0,
        "keywords_count": len(monitor_server.keywords) if monitor_server else 0,
        "uptime_hours": round((time.time() - monitor_server.monitoring_start_time) / 3600, 2) if monitor_server else 0
    })

@app.route('/status')
def status():
    if monitor_server:
        return jsonify({
            "monitoring": monitor_server.running,
            "keywords": len(monitor_server.keywords),
            "notifications_sent": monitor_server.notification_count,
            "stats": monitor_server.monitoring_stats
        })
    return jsonify({"error": "Monitor not initialized"})

@app.route('/uptime')
def uptime_stats():
    """Get comprehensive uptime statistics for 100% availability tracking"""
    global monitor_server
    if monitor_server and hasattr(monitor_server, 'uptime_manager') and monitor_server.uptime_manager:
        return jsonify(monitor_server.uptime_manager.get_uptime_statistics())
    else:
        # Fallback uptime calculation if uptime manager not available
        uptime_hours = (time.time() - monitor_server.monitoring_start_time) / 3600 if monitor_server else 0
        return jsonify({
            "uptime_hours": round(uptime_hours, 2),
            "uptime_days": round(uptime_hours / 24, 2),
            "status": "running",
            "error": "Uptime manager not fully initialized"
        })

# Chrome Extension API Endpoints
@app.route('/api/extension/add-url', methods=['POST'])
def extension_add_url():
    """Add URL to monitoring via Chrome extension"""
    try:
        data = request.get_json()
        url = data.get('url')
        notify_only = data.get('notify_only', True)
        source = data.get('source', 'chrome_extension')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Use existing link_sniper functionality
        from link_sniper import add_link_config
        success = add_link_config(url, notify_only=notify_only, max_market_cap=None, buy_amount=None)
        
        if success:
            logger.info(f"🔗 Chrome Extension: Added URL {url[:50]}... (notify_only: {notify_only})")
            return jsonify({'success': True, 'message': 'URL added to monitoring'})
        else:
            return jsonify({'error': 'Failed to add URL or URL already exists'}), 400
            
    except Exception as e:
        logger.error(f"❌ Chrome Extension URL add error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/extension/add-keywords', methods=['POST'])
def extension_add_keywords():
    """Add keywords to monitoring via Chrome extension"""
    try:
        data = request.get_json()
        keywords = data.get('keywords', [])
        source = data.get('source', 'chrome_extension')
        
        if not keywords:
            return jsonify({'error': 'Keywords are required'}), 400
        
        # Use existing config manager functionality
        added_count = 0
        for keyword in keywords:
            if monitor_server and monitor_server.config_manager:
                success = monitor_server.config_manager.add_keyword(keyword.strip().lower())
                if success:
                    added_count += 1
        
        if added_count > 0:
            # Refresh watchlist in monitor
            if monitor_server:
                monitor_server.keywords = monitor_server.config_manager.get_keywords()
            
            logger.info(f"🎯 Chrome Extension: Added {added_count} keywords from {source}")
            return jsonify({
                'success': True, 
                'message': f'Added {added_count} keywords to monitoring',
                'added_count': added_count
            })
        else:
            return jsonify({'error': 'No new keywords added (may already exist)'}), 400
            
    except Exception as e:
        logger.error(f"❌ Chrome Extension keywords add error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/extension/related-tokens', methods=['POST'])
def extension_related_tokens():
    """Get related tokens for keywords via Chrome extension"""
    try:
        data = request.get_json()
        keywords = data.get('keywords', [])
        
        if not keywords:
            return jsonify({'tokens': []})
        
        # Use existing market data API to find related tokens
        related_tokens = []
        
        # Search for tokens with similar keywords using DexScreener
        for keyword in keywords[:3]:  # Limit to top 3 keywords
            try:
                from market_data_api import MarketDataAPI
                market_api = MarketDataAPI()
                
                # Search for tokens containing the keyword
                search_results = market_api.search_tokens_by_keyword(keyword)
                
                for token in search_results[:5]:  # Top 5 results per keyword
                    if token not in related_tokens:
                        related_tokens.append({
                            'name': token.get('name', 'Unknown'),
                            'symbol': token.get('symbol', 'N/A'),
                            'market_cap': format_market_cap(token.get('market_cap', 0)),
                            'price': f"{token.get('price_sol', 0):.8f}",
                            'age': calculate_token_age(token.get('created_at')),
                            'dexscreener_url': token.get('dexscreener_url', '#'),
                            'letsbonk_url': token.get('letsbonk_url', '#')
                        })
                        
            except Exception as e:
                logger.warning(f"⚠️ Error searching tokens for keyword '{keyword}': {e}")
                continue
        
        return jsonify({'tokens': related_tokens[:10]})  # Return top 10 overall
        
    except Exception as e:
        logger.error(f"❌ Chrome Extension related tokens error: {e}")
        return jsonify({'tokens': []})

@app.route('/api/extension/recent-activity', methods=['GET', 'POST'])
def extension_recent_activity():
    """Get recent monitoring activity for Chrome extension"""
    try:
        activities = []
        
        # Add recent monitoring stats
        if monitor_server:
            stats = monitor_server.monitoring_stats
            uptime_hours = (time.time() - monitor_server.monitoring_start_time) / 3600
            
            activities.extend([
                {
                    'action': f"Processed {stats.get('total_tokens_processed', 0)} tokens",
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'action': f"Running for {uptime_hours:.1f} hours",
                    'timestamp': monitor_server.monitoring_start_time
                },
                {
                    'action': f"Monitoring {len(monitor_server.keywords)} keywords",
                    'timestamp': datetime.now().isoformat()
                }
            ])
        
        return jsonify({'activities': activities[:10]})  # Return latest 10
        
    except Exception as e:
        logger.error(f"❌ Chrome Extension recent activity error: {e}")
        return jsonify({'activities': []})

def format_market_cap(market_cap):
    """Format market cap for display"""
    if market_cap >= 1000000:
        return f"{market_cap/1000000:.1f}M"
    elif market_cap >= 1000:
        return f"{market_cap/1000:.1f}K"
    else:
        return f"{market_cap:.0f}"

def calculate_token_age(created_at):
    """Calculate human-readable token age"""
    if not created_at:
        return "Unknown"
    
    try:
        created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        now = datetime.now(created_time.tzinfo)
        diff = now - created_time
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds//3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds//60}m ago"
        else:
            return "Just now"
    except:
        return "Unknown"

# All Discord commands are now properly integrated into the main Discord bot setup above

def main():
    """Main entry point - optimized for fast startup"""
    global monitor_server
    
    try:
        logger.info("🚀 FAST STARTUP: Starting web server first, then initializing monitoring...")
        
        # Start web server FIRST to pass deployment port check
        port = int(os.getenv('PORT', 5000))
        max_retries = 10
        
        # Initialize minimal server for immediate port binding
        import threading
        from waitress import serve
        
        def delayed_initialization():
            """Initialize monitoring server after web server starts"""
            global monitor_server
            try:
                # Delay initialization to allow web server to start first
                import time
                time.sleep(2)  # Allow web server to bind to port
                
                logger.info("📡 Initializing monitoring server (background)...")
                monitor_server = AlchemyMonitoringServer()
                
                # Initialize Discord bot in background to avoid blocking startup
                if monitor_server:
                    logger.info("🤖 Initializing Discord bot (background)...")
                    monitor_server.setup_discord_bot()
                    logger.info("✅ Discord bot initialized with all commands")
                
                # Start monitoring
                monitoring_thread = monitor_server.start_monitoring()
                logger.info("✅ Monitoring system fully initialized")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize monitoring: {e}")
        
        # Start initialization in background thread
        init_thread = threading.Thread(target=delayed_initialization, daemon=True)
        init_thread.start()
        
        # Start web server immediately for deployment port check
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 PRIORITY: Starting web server on 0.0.0.0:{port} (monitoring initializing in background)")
                serve(app, host='0.0.0.0', port=port, threads=4)
                break  # If successful, break out of loop
            except OSError as e:
                if e.errno == 98:  # Address already in use
                    port += 1
                    logger.warning(f"⚠️ Port {port-1} in use, trying {port}")
                    if attempt == max_retries - 1:
                        logger.error(f"❌ Could not find available port after {max_retries} attempts")
                        return
                else:
                    raise e
                    
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested...")
        if monitor_server:
            monitor_server.stop_monitoring()
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()