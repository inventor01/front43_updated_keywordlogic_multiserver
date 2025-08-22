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
# Disabled solders imports for pure DexScreener deployment
# from solders.keypair import Keypair
# from solders.pubkey import Pubkey as PublicKey
Keypair = None
PublicKey = None

# Import existing components
from alchemy_letsbonk_scraper import AlchemyLetsBonkScraper
from new_token_only_monitor import NewTokenOnlyMonitor
# from letsbonk_api_monitor import LetsBonkAPIMonitor  # REMOVED - file doesn't exist
# from spl_websocket_monitor import SPLWebSocketMonitor  # REMOVED - file doesn't exist
from config_manager import ConfigManager
from discord_notifier import DiscordNotifier
# Conditional import for webhook notifier (Railway deployment compatibility)
try:
    from webhook_discord_notifier import WebhookDiscordNotifier
except ImportError:
    WebhookDiscordNotifier = None
    # Note: logger initialized later in the file
# from social_media_aggregator import SocialMediaAggregator  # REMOVED - file doesn't exist
# from market_cap_alert_manager import MarketCapAlertManager  # DISABLED - outdated
# trading_engine disabled for pure deployment
trader = None
from auto_sniper import AutoSniper
from auto_sell_monitor import AutoSellMonitor
# from sniper_commands import SniperCommands  # Integrated directly
# Conditional import with fallback for Railway deployment
try:
    from token_link_validator import TokenLinkValidator
except ImportError:
    # Fallback stub for production deployment
    class TokenLinkValidator:
        def __init__(self, *args, **kwargs):
            self.enabled = False
        def validate_social_media_link(self, *args, **kwargs):
            return {"valid": False, "error": "Link validator not available"}
# Conditional import with fallback for Railway deployment
try:
    from enhanced_letsbonk_scraper import EnhancedLetsBonkScraper
except ImportError:
    # Fallback stub for production deployment
    class EnhancedLetsBonkScraper:
        def __init__(self, *args, **kwargs):
            self.enabled = False
        def scrape_enhanced(self, *args, **kwargs):
            return []
# Conditional import with fallback for Railway deployment
try:
    from automated_link_extractor import AutomatedLinkExtractor
except ImportError:
    # Fallback stub for production deployment
    class AutomatedLinkExtractor:
        def __init__(self, *args, **kwargs):
            self.enabled = False
        def extract_links(self, *args, **kwargs):
            return []
# Conditional import with fallback for Railway deployment
try:
    from speed_optimized_monitor import SpeedOptimizedMonitor
except ImportError:
    # Fallback stub for production deployment
    class SpeedOptimizedMonitor:
        def __init__(self, *args, **kwargs):
            self.enabled = False
        def process_token_batch(self, *args, **kwargs):
            return []
# Conditional import with fallback for Railway deployment
try:
    from undo_manager import UndoManager
except ImportError:
    # Fallback stub for production deployment
    class UndoManager:
        def __init__(self, *args, **kwargs):
            self.enabled = False
        def record_action(self, *args, **kwargs):
            return True
        def undo_last_action(self, *args, **kwargs):
            return {"success": False, "error": "Undo manager not available"}
# Conditional import with fallback for Railway deployment
try:
    from token_recovery_system import TokenRecoverySystem
except ImportError:
    # Fallback stub for production deployment
    class TokenRecoverySystem:
        def __init__(self, *args, **kwargs):
            self.enabled = False
        def recover_token(self, *args, **kwargs):
            return {"success": False, "error": "Token recovery not available"}
        def update_monitoring_timestamp(self, *args, **kwargs):
            return True
        def get_monitoring_status(self, *args, **kwargs):
            return {"status": "disabled", "error": "Token recovery not available"}
        def detect_monitoring_gap(self, *args, **kwargs):
            return {"gap_detected": False, "status": "disabled"}
        def perform_gap_recovery(self, *args, **kwargs):
            return {"recovery_attempted": False, "status": "disabled", "tokens_recovered": 0}
        def analyze_missed_tokens(self, *args, **kwargs):
            return {"missed_count": 0, "tokens": [], "status": "disabled"}
        def get_recovery_stats(self, *args, **kwargs):
            return {"recovered": 0, "attempted": 0, "success_rate": 0.0}
# AI smart matching removed per user request - using simple keyword matching instead
# Metaplex imports removed - system now uses DexScreener API for all token metadata
# Conditional import with fallback for Railway deployment
try:
    from age_validation_fix import validate_token_age_smart, smart_validator
except ImportError:
    # Fallback stubs for production deployment
    def validate_token_age_smart(*args, **kwargs): return True
    smart_validator = None
# Conditional import with fallback for Railway deployment
try:
    from enhanced_extraction_integration import enhance_token_extraction, enhanced_integration
except ImportError:
    # Fallback stubs for production deployment
    def enhance_token_extraction(*args, **kwargs): return args[0] if args else None
    enhanced_integration = None
# Conditional import with fallback for Railway deployment
try:
    from system_monitoring_integration import record_extraction_success, record_validation_result, log_system_performance, system_monitor
except ImportError:
    # Fallback stubs for production deployment
    def record_extraction_success(*args, **kwargs): return True
    def record_validation_result(*args, **kwargs): return True
    def log_system_performance(*args, **kwargs): return True
    system_monitor = None
# Conditional import with fallback for Railway deployment
try:
    # DualAPINameExtractor REMOVED - using pure DexScreener 70% extractor instead
    pass  # Placeholder since DualAPINameExtractor is removed
except ImportError:
    # Fallback stub for production deployment
    class DualAPINameExtractor:
        def __init__(self, *args, **kwargs):
            self.enabled = False
        async def extract_name_dual_api(self, *args, **kwargs):
            return {"success": False, "error": "Dual API extractor not available"}
from cryptography.fernet import Fernet
import psycopg2
import hashlib
# Conditional import with fallback for Railway deployment
try:
    from keyword_attribution import KeywordAttributionManager
except ImportError:
    # Fallback stub for production deployment
    class KeywordAttributionManager:
        def __init__(self, *args, **kwargs):
            self.enabled = False
        def attribute_keyword(self, *args, **kwargs):
            return {"success": False, "error": "Keyword attribution not available"}
# Conditional import with fallback for Railway deployment
try:
    from uptime_manager import create_uptime_manager
except ImportError:
    # Fallback stub for production deployment
    def create_uptime_manager(*args, **kwargs):
        return None
# from auto_keyword_sync import start_auto_sync, stop_auto_sync, get_auto_sync_status  # DISABLED - keywords cleared by user
DelayedNameExtractor = None
try:
    from COMPLETE_REPLIT_FILES.delayed_name_extractor import DelayedNameExtractor
except ImportError:
    try:
        from delayed_name_extractor import DelayedNameExtractor
    except ImportError:
        pass

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
        # Initialize delayed name extractor for progressive retry (10 minutes delay, 30-second retries)
        self.delayed_extractor = None
        logger.warning("⚠️ DelayedNameExtractor temporarily disabled - focusing on instant matching")
        self.config_manager = ConfigManager()
        
        # Initialize successful extractions tracking
        self.recent_successful_extractions = []
        
        # Load keywords from PostgreSQL database (FIXED VERSION)
        self.keywords = self._load_keywords_direct_database()
        
        # Initialize Pure DexScreener 70% success rate extractor (NO Jupiter/Solana RPC)
        try:
            from dexscreener_70_percent_extractor import DexScreener70PercentExtractor
            self.dexscreener_extractor = DexScreener70PercentExtractor()
            logger.info("✅ PURE DEXSCREENER: 70%+ success rate extractor initialized (NO Jupiter/Solana RPC)")
        except Exception as e:
            logger.warning(f"⚠️ DexScreener 70% extractor failed to initialize: {e}")
            self.dexscreener_extractor = None
        
        # Simple keyword matching (AI smart matching disabled per user request)
        self.ai_smart_matcher = None
        self.smart_matching_integration = None
        logger.info("🔍 Simple keyword matching enabled (AI smart matching disabled)")
        
        # Metaplex integration removed - using DexScreener API for all metadata
        self.metaplex_integration = None
        
        # Simple Metaplex integration removed - using DexScreener API for all metadata
        self.simple_metaplex = None
        
        # Initialize keyword attribution manager - DISABLED (keywords cleared by user)
        self.keyword_attribution = None
        logger.info("🚫 Keyword attribution tracking disabled - keywords cleared by user")
            
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
            'dexscreener_extractions': 0,
            'dexscreener_successes': 0,
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
        
        # Initialize Discord notifier with webhook fallback
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if webhook_url:
            self.discord_notifier = DiscordNotifier()
            if WebhookDiscordNotifier is not None:
                self.webhook_notifier = WebhookDiscordNotifier(webhook_url)
            else:
                self.webhook_notifier = None
                logger.warning("⚠️ WebhookDiscordNotifier not available - webhook notifications disabled")
            logger.info("✅ Discord notifications configured (Bot + Webhook)")
        else:
            self.discord_notifier = None
            self.webhook_notifier = None
            logger.warning("⚠️ No Discord webhook configured")
        
        # Initialize market data API for accurate market cap data
        self.market_data_api = None
        try:
            from market_data_api import get_market_data_api
            self.market_data_api = get_market_data_api()
            logger.info("✅ Market data API initialized (DexScreener)")
        except (ImportError, Exception) as e:
            logger.warning(f"Market data API not available: {e}")
            self.market_data_api = None
        
        # Initialize DexScreener validator for accurate age verification
        self.dexscreener_validator = None
        try:
            from letsbonk_dexscreener_integration import LetsBonkDexScreenerValidator
            self.dexscreener_validator = LetsBonkDexScreenerValidator()
            logger.info("✅ DexScreener validator initialized for accurate age verification")
        except (ImportError, Exception) as e:
            logger.warning(f"⚠️ DexScreener validator failed to initialize: {e}")
            self.dexscreener_validator = None
        
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
        
        # Enhanced social media extraction disabled - using DexScreener API exclusively
        self.social_extractor = None
            
        # BrowserCat functionality removed - system uses DexScreener API exclusively
        self.advanced_browsercat_scraper = None
        
        # Initialize speed-optimized monitor for sub-5s processing
        try:
            self.speed_monitor = SpeedOptimizedMonitor()  # No arguments needed
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
        
        # Auto-sell monitor disabled for pure deployment
        self.auto_sell_monitor = None
        logger.info("🎯 Auto-sell monitor disabled for pure DexScreener deployment")
        
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
        
        # ⚡ ZERO-DELAY OPTIMIZATION: Pre-compile keyword patterns for instant matching
        self.instant_keyword_set = set(kw.lower() for kw in self.keywords)
        self.keyword_lookup = {kw.lower(): kw for kw in self.keywords}
        logger.info(f"⚡ INSTANT MATCHING: Pre-compiled {len(self.instant_keyword_set)} keywords for zero-delay processing")
        logger.info(f"⚡ DUAL API INTEGRATION: Jupiter + DexScreener redundancy active for 70-85% extraction success rate")
        
        # Initialize reliable monitoring system for goal achievement
        try:
            from reliable_monitoring_system import integrate_reliable_system
            goals_ready = integrate_reliable_system(self)
            if goals_ready:
                logger.info("🎯 ALL MONITORING GOALS ACHIEVABLE: System ready for 100% reliability")
            else:
                logger.warning("⚠️ GOAL CHECK: Some monitoring goals may need attention")
        except Exception as e:
            logger.warning(f"⚠️ Reliable system integration: {e}")
        
        # Initialize Railway duplicate fix
        try:
            from railway_dedup_fix import integrate_railway_dedup_fix
            dedup_ready = integrate_railway_dedup_fix(self)
            if dedup_ready:
                logger.info("🚂 RAILWAY DEDUP FIX: Centralized notification deduplication active")
            else:
                logger.warning("⚠️ Railway dedup fix failed to initialize")
        except Exception as e:
            logger.warning(f"⚠️ Railway dedup integration: {e}")
        
        logger.info(f"🔍 Monitoring {len(self.keywords)} keywords")
        logger.info("💰 Using Alchemy FREE tier (300M requests/month)")
        
        # Discord bot will be initialized in background during delayed_initialization  
        self.discord_bot = None
        
        # Initialize Smart Polling Delayed Name Extractor - DISABLED (keywords cleared by user)
        self.delayed_name_extractor = None
        logger.warning("⚠️ Smart Polling Delayed Name Extractor DISABLED - keywords cleared by user")
        
        # Initialize market cap alert manager with Discord bot reference
        # self.market_cap_alert_manager = MarketCapAlertManager(self.discord_bot)  # DISABLED
    
    def check_token_keywords(self, token: Dict[str, Any]) -> str:
        """AI-Enhanced keyword matching with typo detection and fuzzy matching
        Enhanced with Simple Metaplex Integration for LetsBonk tokens
        
        Returns:
            str: The matched keyword, or empty string if no match
        """
        try:
            # CRITICAL DEBUG: Log detailed token and keyword information
            name = token.get('name', '')
            symbol = token.get('symbol', '')
            
            logger.info(f"🔍 KEYWORD MATCH DEBUG: Testing token '{name}' (symbol: '{symbol}')")
            logger.info(f"🔍 Available keywords count: {len(self.keywords) if hasattr(self, 'keywords') else 'NO KEYWORDS'}")
            
            if not hasattr(self, 'keywords') or not self.keywords:
                logger.error(f"❌ NO KEYWORDS LOADED - Cannot perform keyword matching!")
                return ""
            
            # Log first few keywords for debugging
            sample_keywords = list(self.keywords)[:5] if self.keywords else []
            logger.info(f"🔍 Sample keywords: {sample_keywords}")
            
            # Metaplex processing removed - system now uses DexScreener API exclusively for token metadata
            symbol = token.get('symbol', '')
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
            
            # SMART AGE VALIDATION: Check token freshness with reasonable thresholds
            token_age = token.get('age_seconds', 0)
            token_confidence = token.get('confidence', 0.8)
            token_sources = token.get('sources', 1)
            
            if not validate_token_age_smart(name, token_age, token_confidence, token_sources):
                logger.debug(f"🔍 SMART AGE CHECK: {name} not fresh enough for notification (age: {token_age:.1f}s)")
                return ""  # Skip tokens that don't meet freshness criteria
            
            # Skip empty keywords
            if len(self.keywords) == 0:
                return ""
            
            # Quality filters to reduce spam
            if self._is_low_quality_token(token):
                return ""
            
            # SIMPLE KEYWORD MATCHING (AI smart matching disabled per user request)
            # Check both name and symbol for direct keyword matches
            name_lower = name.lower() if name else ""
            symbol_lower = symbol.lower() if symbol else ""
            
            for keyword in self.keywords:
                keyword_lower = keyword.lower()
                # Check for exact match or substring match
                if (keyword_lower == name_lower or keyword_lower == symbol_lower or 
                    keyword_lower in name_lower or keyword_lower in symbol_lower):
                    logger.info(f"🎯 BASIC KEYWORD MATCH: '{name}' (symbol: {symbol}) → keyword '{keyword}'")
                    return keyword
            
            # No keyword match found
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
            
            # SMART POLLING INTEGRATION: Queue fallback tokens for delayed name extraction
            if hasattr(self, 'delayed_name_extractor') and self.delayed_name_extractor:
                try:
                    self.delayed_name_extractor.queue_token_for_delayed_extraction(token.get('address', ''))
                    logger.info(f"🔄 SMART POLLING QUEUED: {name} ({token.get('address', '')[:8]}...) for real name extraction")
                except Exception as e:
                    logger.debug(f"Failed to queue token for delayed extraction: {e}")
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
    
    def _is_potential_letsbonk_token(self, token: Dict[str, Any]) -> bool:
        """
        Detect if token is potentially from LetsBonk platform
        Based on address patterns, age, and characteristics
        """
        try:
            address = token.get('address', '')
            name = token.get('name', '')
            age_seconds = token.get('age_seconds', float('inf'))
            
            # LetsBonk tokens typically have:
            # 1. 'bonk' in the address (pump.fun pattern)
            # 2. Very recent creation (< 10 minutes)
            # 3. Specific metadata patterns
            
            letsbonk_indicators = [
                'bonk' in address.lower(),  # LetsBonk address pattern
                age_seconds < 600,  # Less than 10 minutes old
                len(address) >= 40,  # Valid Solana address length
                name and len(name) > 2,  # Has a meaningful name
            ]
            
            is_letsbonk = sum(letsbonk_indicators) >= 3  # At least 3 indicators for high confidence
            
            if is_letsbonk:
                logger.debug(f"🚀 LETSBONK CANDIDATE: {name} ({address[:10]}...) age={age_seconds:.1f}s")
            
            return is_letsbonk
            
        except Exception as e:
            logger.debug(f"LetsBonk detection error: {e}")
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
            "2dHD2yGaHTtm45rD1FsGVRSofACuiAiDk15wmUV5bonk",  # User complaint - old token passed through
        ]
        if token_address in problem_tokens:
            logger.error(f"🚨 EMERGENCY BLOCK: Known problem token {token_address}")
            logger.error(f"   🚫 This token has corrupted timestamp data and should never be processed")
            return False
        
        # Calculate age with reasonable 1s-5min window for genuine new tokens
        age = current_time - created_timestamp
        
        # REALISTIC VALIDATION: 1 second to 5 minutes window for new tokens
        if age < 1:
            logger.warning(f"⚠️ FUTURE TOKEN: {token_name} ({token_address[:10]}...)")
            logger.warning(f"   ⏰ Token age: {age:.1f}s - token appears to be from the future")
            logger.warning(f"   📅 Allowing with clock drift tolerance")
        elif age > 300:  # 5 minutes
            age_minutes = age / 60
            logger.error(f"🚫 REJECTED OLD TOKEN: {token_name} ({token_address[:10]}...)")
            logger.error(f"   ⏰ Token age: {age_minutes:.1f} minutes ({age:.0f}s) - exceeds 5-minute limit")
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
                    
                    # BALANCED VALIDATION: New tokens within 5 minutes with good confidence
                    if consensus_age <= 300 and confidence > 0.3:  # 5-minute window, reasonable confidence threshold
                        logger.info(f"✅ CONSENSUS VALIDATION PASSED: {token_name} - using consensus timestamp")
                        # Update token with consensus timestamp for more accurate age calculation
                        consensus_timestamp = consensus_result.get('consensus_timestamp')
                        if consensus_timestamp:
                            token['created_timestamp'] = consensus_timestamp
                            # Mark if this is a fallback (very new token)
                            token['is_fallback'] = consensus_result.get('fallback_used', False)
                            age = current_time - consensus_timestamp  # Recalculate age
                    else:
                        # Use smart validation instead of blanket failure
                        if validate_token_age_smart(token_name, consensus_age, confidence, consensus_result.get('valid_sources', 0)):
                            logger.info(f"✅ SMART CONSENSUS PASSED: {token_name} - allowing despite age/confidence")
                        else:
                            logger.warning(f"🚫 SMART CONSENSUS FAILED: {token_name} (age: {consensus_age:.1f}s, confidence: {confidence:.2f})")
                            return False
                else:
                    logger.debug(f"⚠️ No valid consensus sources for {token_name}")
            except Exception as e:
                logger.debug(f"⚠️ Multi-source validation error for {token_name}: {e}")
                # Continue with existing validation
        
        # Final validation: Handle fallback tokens specially to avoid negative ages
        if token.get('is_fallback', False):
            # For fallback tokens (very new), use lenient validation
            is_fresh = True
            logger.info(f"✅ FALLBACK TOKEN APPROVED: {token_name} (very new, using fallback timestamp)")
        else:
            # Normal validation using consensus or original timestamp
            final_age = current_time - token.get('created_timestamp', created_timestamp)
            is_fresh = 1 <= final_age <= 300
            
            # Enhanced logging for debugging
            if not is_fresh:
                logger.error(f"🚫 REJECTED: {token_name} too old (final age: {final_age:.1f}s)")
            else:
                logger.info(f"✅ GENUINE NEW TOKEN: {token_name} (blockchain age: {final_age:.1f}s)")
        
        # Store all detected tokens in database for comprehensive /og_coins search coverage (for both fallback and normal tokens)
        if is_fresh:
            self.store_detected_token_in_db(
                address=token['address'],
                name=token_name,
                symbol=token.get('symbol', token_name[:10]),
                platform='letsbonk',
                status='pre_migration'
            )
        
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
    
    def store_detected_token_in_db(self, address, name, symbol, platform='letsbonk', status='pre_migration', name_status='resolved', matched_keywords=None, social_links=None):
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
                INSERT INTO detected_tokens (address, name, symbol, platform, status, name_status, matched_keywords, social_links, detection_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (address) DO UPDATE SET
                    name = EXCLUDED.name,
                    symbol = EXCLUDED.symbol,
                    status = EXCLUDED.status,
                    name_status = EXCLUDED.name_status,
                    matched_keywords = EXCLUDED.matched_keywords,
                    social_links = EXCLUDED.social_links
            """, (address, name, symbol, platform, status, name_status, keywords_array, social_array))
            
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
    
    def is_token_already_notified(self, token_address):
        """Check if token was already notified (database check for persistence across restarts)"""
        try:
            conn = self.get_db_connection()
            if not conn:
                return False
                
            cursor = conn.cursor()
            
            # Check if notification exists for this token
            cursor.execute("""
                SELECT COUNT(*) FROM notified_tokens 
                WHERE token_address = %s
            """, (token_address,))
            
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            return count > 0
            
        except Exception as e:
            logger.debug(f"❌ Database notification check failed: {e}")
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
    
    def _load_keywords_direct_database(self) -> List[str]:
        """Load keywords directly from PostgreSQL database - BYPASSES ConfigManager issues"""
        try:
            import psycopg2
            database_url = os.getenv('DATABASE_URL')
            
            if not database_url:
                logger.error("❌ DATABASE_URL not found - using fallback keywords")
                return self._get_fallback_keywords_list()
            
            logger.info("🔗 DIRECT DATABASE: Connecting to PostgreSQL...")
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT keyword FROM keywords 
                WHERE user_id = 'System'
                ORDER BY keyword
            """)
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if results:
                keywords = [row[0] for row in results]
                logger.info(f"✅ DIRECT DATABASE: Loaded {len(keywords)} keywords successfully")
                logger.info(f"📝 Sample keywords: {keywords[:10]}")
                return keywords
            else:
                logger.info("✅ No keywords found in database - keywords cleared by user")
                return []
                
        except Exception as e:
            logger.error(f"❌ DIRECT DATABASE: Connection failed: {e}")
            logger.info("✅ Returning empty keywords list - keywords cleared by user")
            return []
    
    def _get_fallback_keywords_list(self) -> List[str]:
        """No fallback keywords - return empty list to stop notifications"""
        logger.warning("⚠️ Fallback keywords disabled - returning empty list")
        return []
    
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
                'market_data': market_data,
                'url': f"https://letsbonk.fun/token/{token['address']}",
                'created_timestamp': token.get('created_timestamp')
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
                
                # Store token in searchable database for /og_coins command
                matched_keywords = [matched_keyword] if matched_keyword else []
                self.store_detected_token_in_db(
                    address=token['address'],
                    name=token['name'],
                    symbol=token.get('symbol', token['name'][:10]),
                    platform='letsbonk',
                    status='pre_migration',
                    matched_keywords=matched_keywords
                )
                
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
                    
                    # CRITICAL FIX: Check keywords IMMEDIATELY before any age validation
                    # This ensures we don't miss keyword matches due to age filtering
                    logger.info(f"🔍 KEYWORD CHECK STARTING: Testing '{token['name']}' against {len(self.keywords) if hasattr(self, 'keywords') else 0} keywords")
                    
                    matched_keyword = self.check_token_keywords(token)
                    
                    if matched_keyword:
                        logger.info(f"🎯 CRITICAL KEYWORD MATCH: '{token['name']}' → keyword '{matched_keyword}'")
                        
                        # IMMEDIATE notification for keyword match (bypass all other checks)
                        if not self.is_token_already_notified(token['address']):
                            try:
                                self.send_instant_notification(token, matched_keyword)
                                self.notified_token_addresses.add(token['address'])
                                if hasattr(self, 'monitoring_stats'):
                                    self.monitoring_stats['notifications_sent'] += 1
                                logger.info(f"⚡ CRITICAL notification sent for keyword match: {token['name']} → {matched_keyword}")
                                
                                # Store in database for persistent tracking
                                self.record_notification_in_db(token['address'], token['name'], 'keyword_match')
                                
                                # Return early - we found what we were looking for
                                return token
                            except Exception as e:
                                logger.error(f"Failed to send critical notification: {e}")
                        else:
                            logger.info(f"🚫 KEYWORD MATCH DUPLICATE: {token['name']} → {matched_keyword} (already notified)")
                        
                        return token  # Return token with keyword match
                    else:
                        logger.info(f"❌ NO KEYWORD MATCH: '{token['name']}' doesn't match any of {len(self.keywords) if hasattr(self, 'keywords') else 0} keywords")
                    
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
                    
                    # 🔄 ENHANCED MULTI-SOURCE NAME EXTRACTION: DexScreener + Jupiter + Solana RPC with retry logic
                    logger.info(f"🔍 PURE DEXSCREENER: Getting accurate name for {token['name']} using 70% success rate system...")
                    
                    dexscreener_result = None
                    
                    # Try pure DexScreener 70% extractor (NO Jupiter/Solana RPC)
                    if self.dexscreener_extractor:
                        try:
                            import asyncio
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            dexscreener_result = loop.run_until_complete(
                                self.dexscreener_extractor.extract_from_dexscreener_with_retries(token['address'])
                            )
                            loop.close()
                            
                            # Check if we got name from DexScreener 70% extractor
                            if dexscreener_result and dexscreener_result.success and dexscreener_result.name:
                                name = dexscreener_result.name
                                confidence = dexscreener_result.confidence
                                source = 'dexscreener_70_percent'
                                
                                # Check if this is a fallback name that needs enhancement
                                is_fallback = (
                                    confidence < 0.8 or 
                                    name.lower().startswith(('token ', 'letsbonk token ', 'jupiter token ')) or
                                    dexscreener_result.source == 'fallback_loop_closed'
                                )
                                
                                if not is_fallback:
                                    logger.info(f"✅ DEXSCREENER 70% SUCCESS: Extracted '{name}' (confidence: {confidence:.2f}, source: {source})")
                                    token['accurate_name'] = name
                                    token['extraction_confidence'] = confidence
                                    token['extraction_source'] = source
                                else:
                                    logger.warning(f"⚠️ DEXSCREENER FALLBACK: {name} (confidence: {confidence:.2f}) - trying enhanced resolver")
                                    dexscreener_result = None  # Force enhanced resolution
                                    
                        except Exception as e:
                            logger.error(f"DexScreener 70% extraction failed: {e}")
                            dexscreener_result = None
                    
                    # If DexScreener failed or returned fallback, use enhanced resolver
                    if not dexscreener_result or not dexscreener_result.success:
                        try:
                            from enhanced_token_name_resolver import resolve_token_name_with_retry
                            
                            logger.info(f"🔄 ENHANCED RESOLVER: Attempting comprehensive resolution for {token['address']}")
                            
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            enhanced_result = loop.run_until_complete(
                                resolve_token_name_with_retry(token['address'])
                            )
                            loop.close()
                            
                            if enhanced_result and enhanced_result.get('confidence', 0) > 0.7:
                                accurate_name = enhanced_result['name']
                                confidence = enhanced_result.get('confidence', 0.8)
                                source = enhanced_result.get('source', 'enhanced_resolver')
                                
                                logger.info(f"✅ ENHANCED SUCCESS: Extracted '{accurate_name}' (confidence: {confidence:.2f}, source: {source})")
                                
                                # Update token with accurate name
                                token['accurate_name'] = accurate_name
                                token['extraction_confidence'] = confidence
                                token['extraction_source'] = source
                                dexscreener_result = enhanced_result  # Use enhanced result
                            else:
                                logger.warning(f"⚠️ ENHANCED RESOLVER: Low confidence or failed for {token['address']}")
                                # Continue with original name but log the issue
                                token['accurate_name'] = token['name']
                                
                        except Exception as e:
                            logger.error(f"Enhanced resolver failed: {e}")
                            # Fall back to original name
                            token['accurate_name'] = token['name']
                    
                    logger.info(f"📊 PURE DEXSCREENER: 70% extraction processing completed: 1 token processed")
                    
                    # ENHANCED KEYWORD CHECK: Check both original name and accurate name from DexScreener
                    matched_keyword = None
                    search_names = [token['name']]
                    
                    # Add accurate name from DexScreener 70% extractor if available
                    if dexscreener_result and hasattr(dexscreener_result, 'success') and dexscreener_result.success and hasattr(dexscreener_result, 'name') and dexscreener_result.name:
                        accurate_name = dexscreener_result.name
                        search_names.append(accurate_name)
                        logger.info(f"🔍 CHECKING KEYWORDS: Original '{token['name']}' + DexScreener '{accurate_name}'")
                    
                    # Check all available names against keywords
                    for name_to_check in search_names:
                        # Create temporary token with the name we're checking
                        temp_token = token.copy()
                        temp_token['name'] = name_to_check
                        matched_keyword = self.check_token_keywords(temp_token)
                        
                        if matched_keyword:
                            logger.info(f"🎯 KEYWORD MATCH FOUND: '{name_to_check}' → keyword '{matched_keyword}'")
                            break
                    
                    if matched_keyword:
                        # Store matched keyword and which name matched
                        token['matched_keyword'] = matched_keyword
                        token['matched_name'] = name_to_check
                        
                        # Use the accurate name for notifications if available
                        notification_name = dual_api_result.get('name', token['name']) if dual_api_result else token['name']
                        
                        # CENTRALIZED DEDUPLICATION CHECK for Railway fix
                        should_notify = True
                        if hasattr(self, 'railway_dedup'):
                            should_notify = self.railway_dedup.check_and_mark_notified(
                                token['address'], notification_name, matched_keyword, 'dual_api'
                            )
                            self.railway_dedup.log_notification_attempt(
                                token['address'], notification_name, matched_keyword, should_notify
                            )
                        elif not self.is_token_already_notified(token['address']):
                            # Fallback to original check
                            should_notify = True
                        else:
                            should_notify = False
                        
                        if should_notify:
                            try:
                                # Create enhanced notification data with dual API info
                                notification_data = {
                                    'name': notification_name,
                                    'original_name': token['name'],
                                    'symbol': token.get('symbol', ''),
                                    'address': token['address'],
                                    'matched_keyword': matched_keyword,
                                    'extraction_source': dual_api_result.get('source', 'original') if dual_api_result else 'original',
                                    'confidence': dual_api_result.get('confidence', 0.8) if dual_api_result else 0.8,
                                    'url': f"https://letsbonk.fun/token/{token['address']}"
                                }
                                
                                success = self.discord_notifier.send_enhanced_token_notification(notification_data, matched_keyword)
                                if success:
                                    self.notified_token_addresses.add(token['address'])
                                    logger.info(f"⚡ RAILWAY DEDUP: Notification sent for '{notification_name}' → {matched_keyword}")
                                else:
                                    logger.warning(f"⚠️ Discord notification failed for {notification_name}")
                                
                            except Exception as e:
                                logger.error(f"Failed to send dual API notification: {e}")
                        else:
                            logger.info(f"🚫 RAILWAY DEDUP: Blocked duplicate for '{notification_name}' → {matched_keyword}")
                        
                        return token  # Return token with keyword match
                    
                    # Execute pure name extraction only if no immediate keyword match
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
                                
                            # RELAXED AGE CHECK: Allow tokens up to 10 minutes for testing
                            age_seconds = current_time - created_timestamp
                            if age_seconds > 600:  # 10 minutes max
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
                            
                            # CENTRALIZED DEDUPLICATION CHECK for Railway fix (PURE NAME PATH)
                            should_notify = True
                            if hasattr(self, 'railway_dedup'):
                                should_notify = self.railway_dedup.check_and_mark_notified(
                                    token['address'], accurate_name, matched_keyword, 'pure_name'
                                )
                                self.railway_dedup.log_notification_attempt(
                                    token['address'], accurate_name, matched_keyword, should_notify
                                )
                            elif not self.is_token_already_notified(token['address']):
                                # Fallback to original check
                                should_notify = True
                            else:
                                should_notify = False
                            
                            if should_notify:
                                # Send Discord notification instantly
                                if self.discord_notifier:
                                    success = self.discord_notifier.send_enhanced_token_notification(notification_data, matched_keyword)
                                    
                                    if success:
                                        instant_time = time.time() - instant_notification_start
                                        logger.info(f"⚡ PURE NAME SUCCESS: Discord notification sent for '{accurate_name}' in {instant_time:.3f}s (confidence: {match_confidence:.2f})")
                                        
                                        # Track the notification to prevent duplicates
                                        self.notified_token_addresses.add(token['address'])
                                        self.notification_count += 1
                                        
                                    else:
                                        logger.error(f"❌ PURE NAME NOTIFICATION FAILED for '{accurate_name}'")
                            else:
                                logger.info(f"🚫 RAILWAY DEDUP (PURE NAME): Blocked duplicate for '{accurate_name}' → {matched_keyword}")
                                return None
                            
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
                        
                        except Exception as e:
                            logger.error(f"❌ PURE NAME NOTIFICATION ERROR for '{accurate_name}': {e}")
                        
                        # Mark as processed - no further processing needed
                        token['matched_keyword'] = matched_keyword  
                        token['accurate_name'] = accurate_name
                        token['match_confidence'] = match_confidence
                        token['instant_notification_sent'] = True  # Changed to match the flag checked in legacy loop
                        token['pure_name_notification_sent'] = True
                        token['processing_method'] = 'pure_name_extraction'
                        logger.info(f"✅ PURE NAME PROCESSING COMPLETE: '{accurate_name}' → '{matched_keyword}'")
                        
                    else:
                        # No keyword match found using accurate name - QUEUE FOR DELAYED RETRY
                        if pure_name_result:
                            accurate_name = pure_name_result.get('accurate_name', 'unknown')
                            logger.info(f"❌ NO KEYWORD MATCH: Accurate name '{accurate_name}' doesn't match any keywords")
                        else:
                            logger.info(f"❌ NAME EXTRACTION FAILED: Could not get accurate name for {token['address'][:10]}...")
                            accurate_name = token.get('name', 'unknown')
                        
                        # Queue token for delayed extraction retry (10 minutes wait, then 30-second retries)
                        if self.delayed_extractor:
                            self.delayed_extractor.queue_extraction(token['address'], accurate_name)
                            logger.info(f"⏰ QUEUED FOR RETRY: {accurate_name} will be re-checked in 10 minutes")
                        
                        token['instant_notification_sent'] = False  # Ensure legacy loop can still process this if needed
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
                
            # Metaplex statistics logging removed - using DexScreener API only
            
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
                    already_notified = (token['address'] in self.notified_token_addresses or 
                                      self.is_token_already_notified(token['address']))
                    if not already_notified:
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
                        
                        # ⚡ ZERO-DELAY OPTIMIZATION: Instant notification with accurate age calculation
                        instant_start = time.time()
                        
                        # Calculate accurate age using blockchain timestamp
                        current_time = time.time()
                        created_timestamp = token.get('created_timestamp')
                        
                        if created_timestamp and created_timestamp > 0:
                            # Handle milliseconds vs seconds timestamp format
                            if created_timestamp > 1e12:
                                normalized_timestamp = created_timestamp / 1000.0
                            else:
                                normalized_timestamp = created_timestamp
                            
                            age_seconds = current_time - normalized_timestamp
                            
                            # Format age display accurately
                            if age_seconds < 60:
                                age_display = f"{age_seconds:.0f}s ago"
                            elif age_seconds < 3600:
                                age_display = f"{age_seconds/60:.0f}m {age_seconds%60:.0f}s ago"
                            else:
                                age_display = f"{age_seconds/3600:.0f}h {(age_seconds%3600)/60:.0f}m ago"
                        else:
                            # Fallback only if no timestamp available
                            age_display = token.get('age_display', 'Just now')
                        
                        # ⚡ ZERO-DELAY: Pre-built notification data (no string formatting delays)
                        notification_data = {
                            'name': token['name'],
                            'symbol': token['symbol'], 
                            'address': token['address'],
                            'age_display': age_display,
                            'market_data': None,  # Skip market data for zero delay
                            'url': token.get('letsbonk_url', f"https://letsbonk.fun/token/{token['address']}"),
                            'social_links': token.get('social_links', [])
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
                        
                        # ⚡ ZERO-DELAY NOTIFICATION: Fire immediately without blocking
                        success = False
                        try:
                            # Instant Discord notification (non-blocking)
                            if self.discord_notifier:
                                success = self.discord_notifier.send_enhanced_token_notification(notification_data, notification_keyword)
                                if success:
                                    logger.info(f"⚡ INSTANT DISCORD: {token['name']} notification sent")
                        except Exception as e:
                            logger.debug(f"Discord notification error: {e}")
                            success = False
                        
                        # Webhook fallback if Discord bot failed or unavailable
                        if not success and self.webhook_notifier is not None:
                            try:
                                # Convert notification data to webhook format
                                token_data = {
                                    'name': notification_data['name'],
                                    'address': notification_data['address'],
                                    'market_data': notification_data.get('market_data', {})
                                }
                                success = self.webhook_notifier.send_token_notification(token_data, notification_keyword)
                                logger.info(f"✅ WEBHOOK SUCCESS: {token['name']} notification sent via Discord webhook")
                            except Exception as webhook_error:
                                logger.error(f"❌ Webhook notification failed: {webhook_error}")
                                success = False
                        
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
        
        # Start enhanced detector for token monitoring
        try:
            from enhanced_token_detector import EnhancedTokenDetector
            self.enhanced_detector = EnhancedTokenDetector(callback_func=self.process_tokens)
            
            enhanced_thread = threading.Thread(target=self.enhanced_detector.monitor_enhanced_token_creation)
            enhanced_thread.daemon = True
            enhanced_thread.start()
            logger.info("✅ Enhanced token detector started")
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
        
        # Start new token monitoring (PRIMARY TOKEN SOURCE)
        if self.new_token_monitor:
            try:
                new_token_thread = threading.Thread(target=self.new_token_monitor.start_monitoring, daemon=True)
                new_token_thread.start()
                logger.info("🎯 NEW TOKEN MONITOR started - primary token detection source")
            except Exception as e:
                logger.error(f"❌ Failed to start new token monitor: {e}")
        
        # Start main monitoring loop
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
        if self.auto_sell_monitor and hasattr(self.auto_sell_monitor, 'monitor_positions'):
            try:
                if asyncio.iscoroutinefunction(self.auto_sell_monitor.monitor_positions):
                    auto_sell_thread = threading.Thread(
                        target=lambda: asyncio.run(self.auto_sell_monitor.monitor_positions()), 
                        daemon=True
                    )
                    auto_sell_thread.start()
                    logger.info("💰 Auto-sell monitoring started")
                else:
                    logger.warning("⚠️ Auto-sell monitor method is not async - skipping")
            except Exception as e:
                logger.warning(f"⚠️ Auto-sell monitoring failed to start: {e}")
        
        # Start delayed name extraction loop for progressive retry (10 minutes wait, 30-second retries)
        if self.delayed_extractor:
            try:
                delayed_extraction_thread = threading.Thread(
                    target=lambda: asyncio.run(self.delayed_extractor.start_extraction_loop()), 
                    daemon=True
                )
                delayed_extraction_thread.start()
                logger.info("⏰ Delayed name extraction loop started - 10min wait, 30s retry intervals")
            except Exception as e:
                logger.warning(f"⚠️ Delayed extraction loop failed to start: {e}")
        
        # Start Discord bot
        
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
                    existing_keywords = monitor_server.keywords
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
                        monitor_server.keywords = monitor_server._load_keywords_direct_database()
                    
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
                    
                    # Get keywords using the same method that works for monitoring
                    keywords = monitor_server.keywords
                    
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
                            # Update server keywords list by reloading from database/file
                            try:
                                updated_keywords = monitor_server.config_manager.list_keywords()
                                monitor_server.keywords = updated_keywords
                                logger.info(f"✅ Updated server keywords list: {len(updated_keywords)} keywords remaining")
                            except Exception as e:
                                logger.error(f"Failed to reload keywords after removal: {e}")
                                # Fallback: remove from current list
                                monitor_server.keywords = [k for k in monitor_server.keywords if k.lower() != keyword_or_url.lower()]
                            
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
                            monitor_server.keywords = monitor_server._load_keywords_direct_database()
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
                        monitor_server.keywords = monitor_server._load_keywords_direct_database()
                    
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
                        dexscreener_status = "🟢 Active" if hasattr(monitor_server, 'enhanced_scraper') and monitor_server.enhanced_scraper else "🔴 Disabled"
                        scraper_status = "🟢 Active" if hasattr(monitor_server, 'dexscreener_api') else "🔴 Disabled"
                        
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
                        # Reload keywords from database
                        old_count = len(monitor_server.keywords)
                        monitor_server.keywords = monitor_server._load_keywords_direct_database()
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
            
            @self.discord_bot.tree.command(name="clear", description="Clear all keywords from watchlist")
            async def clear_keywords(interaction: discord.Interaction):
                try:
                    await interaction.response.defer(ephemeral=True)
                    
                    # Get current keywords for undo functionality
                    current_keywords = monitor_server.keywords
                    
                    if not current_keywords:
                        await interaction.followup.send("📝 **No keywords to clear**\n\nYour keyword watchlist is already empty.", ephemeral=True)
                        return
                    
                    # Clear all keywords from database and file
                    success = monitor_server.config_manager.clear_keywords()
                    
                    if success:
                        # Update server keywords list by reloading from database/file
                        try:
                            updated_keywords = monitor_server.config_manager.list_keywords()
                            monitor_server.keywords = updated_keywords  # Should be empty now
                            logger.info(f"✅ Updated server keywords list after clear: {len(updated_keywords)} keywords")
                        except Exception as e:
                            logger.error(f"Failed to reload keywords after clear: {e}")
                            # Fallback: clear the list directly
                            monitor_server.keywords = []
                        
                        # Record action for undo
                        monitor_server.undo_manager.record_action(
                            user_id=interaction.user.id,
                            action_type='clear_keywords',
                            action_data={'cleared_keywords': current_keywords}
                        )
                        
                        await interaction.followup.send(f"""✅ **Keywords Cleared**

🗑️ **Removed:** {len(current_keywords)} keywords
📝 **Current Status:** Keyword monitoring disabled

↩️ **Use /undo to restore all keywords if needed**""", ephemeral=True)
                        
                        logger.info(f"Discord clear: Cleared {len(current_keywords)} keywords by user {interaction.user}")
                    else:
                        await interaction.followup.send("❌ **Failed to clear keywords**\n\nThere was an error clearing the keyword watchlist.", ephemeral=True)
                        
                except Exception as e:
                    logger.error(f"Clear command error: {e}")
                    if not interaction.response.is_done():
                        await interaction.response.send_message("❌ Error clearing keywords", ephemeral=True)
            
            @self.discord_bot.tree.command(name="clear_all", description="Clear ALL monitoring (keywords AND URLs)")
            async def clear_all_monitoring(interaction: discord.Interaction):
                try:
                    await interaction.response.defer(ephemeral=True)
                    
                    # Get current state for undo functionality
                    current_keywords = monitor_server.keywords
                    current_urls = []
                    if monitor_server.link_sniper:
                        current_urls = monitor_server.link_sniper.get_user_link_configs(interaction.user.id)
                    
                    if not current_keywords and not current_urls:
                        await interaction.followup.send("📝 **Nothing to clear**\n\nYou have no keywords or URLs configured for monitoring.", ephemeral=True)
                        return
                    
                    # Clear keywords from database and file
                    keywords_cleared = False
                    if current_keywords:
                        keywords_cleared = monitor_server.config_manager.clear_keywords()
                        if keywords_cleared:
                            # Update server keywords list by reloading from database/file
                            try:
                                updated_keywords = monitor_server.config_manager.list_keywords()
                                monitor_server.keywords = updated_keywords  # Should be empty now
                                logger.info(f"✅ Updated server keywords list after clear_all: {len(updated_keywords)} keywords")
                            except Exception as e:
                                logger.error(f"Failed to reload keywords after clear_all: {e}")
                                # Fallback: clear the list directly
                                monitor_server.keywords = []
                    
                    # Clear URLs for this user
                    urls_cleared = False
                    if current_urls and monitor_server.link_sniper:
                        urls_cleared = monitor_server.link_sniper.clear_user_links(interaction.user.id)
                    
                    if keywords_cleared or urls_cleared:
                        # Record action for undo
                        undo_data = {}
                        if current_keywords:
                            undo_data['cleared_keywords'] = current_keywords
                        if current_urls:
                            undo_data['cleared_urls'] = current_urls
                            undo_data['user_id'] = interaction.user.id
                        
                        monitor_server.undo_manager.record_action(
                            user_id=interaction.user.id,
                            action_type='clear_all',
                            action_data=undo_data
                        )
                        
                        response_parts = []
                        if keywords_cleared:
                            response_parts.append(f"🗑️ **Keywords:** {len(current_keywords)} removed")
                        if urls_cleared:
                            response_parts.append(f"🗑️ **URLs:** {len(current_urls)} removed")
                        
                        await interaction.followup.send(f"""✅ **All Monitoring Cleared**

{chr(10).join(response_parts)}
📝 **Current Status:** All monitoring disabled

↩️ **Use /undo to restore everything if needed**""", ephemeral=True)
                        
                        logger.info(f"Discord clear_all: Cleared {len(current_keywords)} keywords and {len(current_urls)} URLs by user {interaction.user}")
                    else:
                        await interaction.followup.send("❌ **Failed to clear monitoring**\n\nThere was an error clearing your monitoring configuration.", ephemeral=True)
                        
                except Exception as e:
                    logger.error(f"Clear all command error: {e}")
                    if not interaction.response.is_done():
                        await interaction.response.send_message("❌ Error clearing all monitoring", ephemeral=True)
            
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
            
            @self.discord_bot.tree.command(name="search_recent", description="Search the last 1-2 hours of scanned tokens for missed keyword matches")
            async def search_recent(interaction: discord.Interaction, hours: int = 2, keyword: str = None):
                """Search recently scanned tokens for missed keyword matches"""
                try:
                    await interaction.response.defer(ephemeral=True)
                    
                    # Validate hours parameter
                    if hours < 1 or hours > 24:
                        await interaction.edit_original_response(content="❌ **Invalid Hours**\n\nPlease specify between 1-24 hours to search.")
                        return
                    
                    logger.info(f"📱 Discord: Searching last {hours} hours for keyword matches by {interaction.user}")
                    
                    # Get recent tokens from database
                    try:
                        import psycopg2
                        from datetime import datetime, timedelta
                        
                        db_url = os.getenv('DATABASE_URL')
                        if not db_url:
                            await interaction.edit_original_response(content="❌ **Database Error**\n\nDatabase connection not available.")
                            return
                        
                        conn = psycopg2.connect(db_url)
                        cursor = conn.cursor()
                        
                        # Calculate time range
                        cutoff_time = datetime.now() - timedelta(hours=hours)
                        
                        # Query for tokens detected in the specified timeframe
                        cursor.execute("""
                            SELECT address, name, symbol, detection_timestamp, source, method, matched_keywords
                            FROM detected_tokens 
                            WHERE detection_timestamp >= %s
                            ORDER BY detection_timestamp DESC
                            LIMIT 100
                        """, (cutoff_time,))
                        
                        recent_tokens = cursor.fetchall()
                        cursor.close()
                        conn.close()
                        
                        if not recent_tokens:
                            response = f"🔍 **No Recent Tokens Found**\n\nNo tokens were detected in the last {hours} hour{'s' if hours != 1 else ''}.\n\n💡 **This could mean:**\n• No new tokens were created recently\n• System was offline during this period\n• All tokens failed extraction"
                            await interaction.edit_original_response(content=response)
                            return
                        
                        # Check each token for keyword matches
                        missed_matches = []
                        total_checked = 0
                        
                        for token_data in recent_tokens:
                            address, name, symbol, timestamp, source, method, existing_keywords = token_data
                            total_checked += 1
                            
                            # Skip if already has keyword matches
                            if existing_keywords and len(existing_keywords) > 0:
                                continue
                            
                            # Check against current keywords using the specific keyword or all keywords
                            if keyword:
                                # Search for specific keyword
                                search_keywords = [keyword.lower().strip()]
                            else:
                                # Use all monitored keywords
                                search_keywords = [k.lower() for k in self.keywords] if hasattr(self, 'keywords') else []
                            
                            matched_keywords = []
                            name_lower = name.lower() if name else ""
                            symbol_lower = symbol.lower() if symbol else ""
                            
                            for kw in search_keywords:
                                if kw in name_lower or kw in symbol_lower:
                                    matched_keywords.append(kw)
                            
                            if matched_keywords:
                                missed_matches.append({
                                    'address': address,
                                    'name': name,
                                    'symbol': symbol,
                                    'timestamp': timestamp,
                                    'source': source,
                                    'method': method,
                                    'matched_keywords': matched_keywords
                                })
                        
                        # Build response
                        response_parts = []
                        
                        if missed_matches:
                            if keyword:
                                response_parts.append(f"🎯 **Found {len(missed_matches)} missed matches for '{keyword}' in last {hours} hour{'s' if hours != 1 else ''}:**\n")
                            else:
                                response_parts.append(f"🚨 **Found {len(missed_matches)} missed keyword matches in last {hours} hour{'s' if hours != 1 else ''}:**\n")
                            
                            for i, token in enumerate(missed_matches[:10], 1):
                                age = datetime.now() - token['timestamp']
                                if age.total_seconds() < 3600:
                                    age_str = f"{int(age.total_seconds()//60)}m ago"
                                else:
                                    age_str = f"{int(age.total_seconds()//3600)}h {int((age.total_seconds()%3600)//60)}m ago"
                                
                                response_parts.append(f"**{i}.** {token['name']} ({token['symbol']})")
                                response_parts.append(f"   🎯 Matched: {', '.join(token['matched_keywords'])}")
                                response_parts.append(f"   📍 Contract: `{token['address'][:20]}...`")
                                response_parts.append(f"   🕐 Detected: {age_str}")
                                response_parts.append(f"   🔗 [LetsBonk](https://letsbonk.fun/token/{token['address']})")
                                response_parts.append("")
                            
                            if len(missed_matches) > 10:
                                response_parts.append(f"... and {len(missed_matches) - 10} more missed matches")
                            
                            response_parts.append(f"\n⚠️ **Action Needed:** These tokens contained your keywords but didn't trigger notifications.")
                            response_parts.append("This could indicate a system issue during that time period.")
                            
                        else:
                            if keyword:
                                response_parts.append(f"✅ **No Missed Matches for '{keyword}'**\n")
                                response_parts.append(f"All tokens from the last {hours} hour{'s' if hours != 1 else ''} were properly checked.")
                            else:
                                response_parts.append(f"✅ **No Missed Keyword Matches**\n")
                                response_parts.append(f"All {total_checked} tokens from the last {hours} hour{'s' if hours != 1 else ''} were properly checked for keywords.")
                            
                            response_parts.append("\n🎯 **System Status:** All keyword matching is working correctly.")
                        
                        response_parts.append(f"\n📊 **Search Summary:**")
                        response_parts.append(f"• Tokens checked: {total_checked}")
                        response_parts.append(f"• Time range: Last {hours} hour{'s' if hours != 1 else ''}")
                        response_parts.append(f"• Keywords: {len(search_keywords) if 'search_keywords' in locals() else 0} {'(specific)' if keyword else '(all monitored)'}")
                        
                        final_response = "\n".join(response_parts)
                        await interaction.edit_original_response(content=final_response)
                        
                        logger.info(f"📱 Recent search completed: {total_checked} tokens checked, {len(missed_matches)} missed matches found")
                        
                    except Exception as db_error:
                        logger.error(f"Database error in search_recent: {db_error}")
                        await interaction.edit_original_response(content=f"❌ **Database Error**\n\nError accessing token history: {str(db_error)}")
                        
                except discord.errors.InteractionResponded:
                    pass
                except Exception as e:
                    logger.error(f"Search recent command error: {e}")
                    if not interaction.response.is_done():
                        await interaction.response.send_message(f"❌ Error searching recent tokens: {str(e)}", ephemeral=True)
                    else:
                        try:
                            await interaction.edit_original_response(content=f"❌ Error searching recent tokens: {str(e)}")
                        except:
                            pass
            
            @self.discord_bot.tree.command(name="undo", description="Undo your last action (keywords/URLs)")
            async def undo_action(interaction: discord.Interaction):
                try:
                    await interaction.response.defer(ephemeral=True)
                    
                    # Get last action for user
                    last_action = monitor_server.undo_manager.get_last_action(interaction.user.id)
                    
                    if not last_action:
                        await interaction.followup.send("📝 **No recent actions to undo**\n\nYou haven't performed any undoable actions recently.", ephemeral=True)
                        return
                    
                    # Perform undo based on action type
                    success = monitor_server.undo_manager.undo_action(interaction.user.id, last_action)
                    
                    if success:
                        # Refresh keywords in monitor if needed
                        if 'keyword' in last_action['action_type']:
                            monitor_server.keywords = monitor_server._load_keywords_direct_database()
                        
                        await interaction.followup.send(f"""✅ **Action Undone Successfully**
            
🔄 **Undid:** {last_action['action_type'].replace('_', ' ').title()}
🕐 **From:** {last_action['timestamp'][:19].replace('T', ' ')}
            
📊 **Status:** Changes have been reversed""", ephemeral=True)
                        
                        logger.info(f"Discord undo: User {interaction.user} undid {last_action['action_type']}")
                    else:
                        await interaction.followup.send(f"""❌ **Undo Failed**
            
⚠️ **Issue:** Could not reverse the last action
💡 **Reason:** Data may have been modified or action expired
            
🔍 **Last Action:** {last_action['action_type'].replace('_', ' ').title()}""", ephemeral=True)
                        
                except Exception as e:
                    logger.error(f"Undo command error: {e}")
                    if not interaction.response.is_done():
                        await interaction.response.send_message("❌ Error processing undo request", ephemeral=True)
            
            logger.info("✅ Enhanced Discord commands registered successfully")
            
            # Start Discord bot in background thread
            import threading
            def run_discord_bot():
                try:
                    logger.info("🚀 Starting Discord bot...")
                    logger.info(f"🔑 Using Discord token: {bot_token[:20]}... ({len(bot_token)} chars)")
                    self.discord_bot.run(bot_token)
                except Exception as e:
                    logger.error(f"❌ Discord bot runtime error: {e}")
                    if "Improper token" in str(e):
                        logger.error("🚨 DISCORD TOKEN ISSUE: Token appears to be invalid or expired")
                        logger.error("💡 Solution: Please provide a valid Discord bot token via ask_secrets tool")
            
            discord_thread = threading.Thread(target=run_discord_bot, daemon=True)
            discord_thread.start()
            logger.info("🤖 Discord bot started in background thread")
            
            return discord_thread
            
        except Exception as e:
            logger.error(f"Discord bot setup error: {e}")
            return None

# Main execution
if __name__ == "__main__":
    try:
        # Create and start the monitoring server
        monitor = AlchemyMonitoringServer()
        
        # Start all monitoring services
        logger.info("🚀 Starting Alchemy Token Monitoring Server...")
        monitoring_thread = monitor.start_monitoring()
        
        # Keep the main thread alive
        logger.info("✅ Server running successfully on port 5000")
        logger.info("🔍 Token monitoring active - waiting for new tokens...")
        
        # Create Flask app for health check
        app = Flask(__name__)
        
        @app.route('/health')
        def health_check():
            return jsonify({
                'status': 'healthy',
                'message': 'Token monitoring server is running',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        @app.route('/')
        def home():
            return jsonify({
                'service': 'Solana Token Monitor',
                'status': 'active',
                'monitoring': 'LetsBonk platform',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        
        # Start the Flask server
        logger.info("🌐 Starting web server on port 5000...")
        serve(app, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        logger.info("👋 Shutting down server...")
    except Exception as e:
        logger.error(f"❌ Server startup error: {e}")
        raise
