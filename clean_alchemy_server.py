"""
Clean Alchemy Server - Fixed Version
Removes all broken imports and syntax errors for reliable operation
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
from typing import Dict, List, Any, Optional
import discord
from discord.ext import commands
from discord import app_commands
from solana.rpc.api import Client
from cachetools import TTLCache
import base58
from cryptography.fernet import Fernet
import psycopg2
import hashlib

# Import working components only
from alchemy_letsbonk_scraper import AlchemyLetsBonkScraper
from new_token_only_monitor import NewTokenOnlyMonitor
from config_manager import ConfigManager
from discord_notifier import DiscordNotifier
from trading_engine import trader
from enhanced_letsbonk_scraper import EnhancedLetsBonkScraper
from optimized_name_extractor import get_optimized_extractor
from high_success_integration import get_high_success_extractor

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Solana RPC client
ALCHEMY_API_KEY = os.getenv('ALCHEMY_API_KEY', '877gH4oJoW3wJcEZpK6OxPMPBIlJhpS8')

def get_solana_client():
    """Get Solana RPC client with fallback endpoints"""
    try:
        if ALCHEMY_API_KEY:
            alchemy_url = f"https://solana-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
            return Client(alchemy_url)
    except Exception as e:
        logger.warning(f"Alchemy RPC failed: {e}, using official Solana RPC")
    
    # Fallback to official RPC
    return Client("https://api.mainnet-beta.solana.com")

class CleanAlchemyServer:
    """
    Clean monitoring server with all syntax errors and broken connections fixed
    Focus on core functionality without problematic imports
    """
    
    def __init__(self):
        self.client = get_solana_client()
        self.config_manager = ConfigManager()
        self.discord_notifier = DiscordNotifier()
        
        # Initialize optimized components
        self.optimized_extractor = None
        self.high_success_extractor = None
        
        # Core monitoring components
        self.alchemy_scraper = AlchemyLetsBonkScraper()
        self.enhanced_scraper = EnhancedLetsBonkScraper()
        self.new_token_monitor = NewTokenOnlyMonitor()
        
        # Cache and storage
        self.processed_tokens = TTLCache(maxsize=10000, ttl=3600)
        self.keywords = set()
        
        # Flask app for health checks
        self.app = Flask(__name__)
        self.setup_flask_routes()
        
        # Discord bot setup
        self.bot_token = os.getenv('DISCORD_TOKEN')
        self.bot = None
        
        # Performance tracking
        self.stats = {
            'tokens_processed': 0,
            'notifications_sent': 0,
            'extraction_success_rate': 0.0,
            'start_time': time.time()
        }
        
    async def initialize_optimized_components(self):
        """Initialize optimized name extraction components"""
        try:
            self.optimized_extractor = await get_optimized_extractor()
            self.high_success_extractor = await get_high_success_extractor()
            logger.info("✅ Optimized components initialized for 70%+ success rate")
        except Exception as e:
            logger.error(f"❌ Optimized components initialization failed: {e}")
    
    async def extract_token_name_optimized(self, token_address: str) -> Dict[str, Any]:
        """Extract token name using optimized 70%+ success rate system"""
        if not self.high_success_extractor:
            await self.initialize_optimized_components()
        
        if self.high_success_extractor:
            return await self.high_success_extractor.extract_token_name_with_high_success(token_address)
        else:
            # Fallback to basic extraction
            return {
                'name': f'Token {token_address[:8]}',
                'confidence': 0.5,
                'source': 'fallback',
                'success': False,
                'extraction_time': 0.0
            }
    
    def load_keywords_from_database(self):
        """Load keywords from PostgreSQL database"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                logger.warning("No DATABASE_URL found")
                return
            
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT keyword FROM keywords WHERE keyword IS NOT NULL")
            keywords = [row[0] for row in cursor.fetchall()]
            
            self.keywords = set(keywords)
            logger.info(f"✅ Loaded {len(self.keywords)} keywords from database")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to load keywords: {e}")
            self.keywords = set()
    
    def matches_keywords(self, token_name: str) -> List[str]:
        """Check if token name matches any keywords (refined matching)"""
        if not token_name or not self.keywords:
            return []
        
        token_name_lower = token_name.lower()
        matched_keywords = []
        
        # Target keywords only (avoid generic words like 'coin')
        target_keywords = {'moon', 'pepe', 'doge', 'shib', 'pump', 'meme', 'bonk'}
        
        for keyword in self.keywords:
            if keyword and keyword.lower() in target_keywords:
                if keyword.lower() in token_name_lower:
                    matched_keywords.append(keyword)
        
        return matched_keywords
    
    async def process_token_detection(self, token_data: Dict[str, Any]) -> bool:
        """Process detected token with optimized extraction"""
        try:
            token_address = token_data.get('address')
            if not token_address or token_address in self.processed_tokens:
                return False
            
            # Extract name using optimized system
            extraction_result = await self.extract_token_name_optimized(token_address)
            token_name = extraction_result.get('name', f'Token {token_address[:8]}')
            
            # Check keyword matches
            matched_keywords = self.matches_keywords(token_name)
            
            if matched_keywords:
                # Send notification
                notification_data = {
                    'token_address': token_address,
                    'name': token_name,
                    'symbol': token_data.get('symbol', 'UNKNOWN'),
                    'keywords': matched_keywords,
                    'confidence': extraction_result.get('confidence', 0.5),
                    'source': extraction_result.get('source', 'unknown'),
                    'timestamp': datetime.now(),
                    'platform': 'letsbonk.fun'
                }
                
                await self.send_discord_notification(notification_data)
                self.stats['notifications_sent'] += 1
            
            # Cache processed token
            self.processed_tokens[token_address] = {
                'name': token_name,
                'processed_time': time.time(),
                'matched_keywords': matched_keywords
            }
            
            self.stats['tokens_processed'] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Token processing error: {e}")
            return False
    
    async def send_discord_notification(self, notification_data: Dict[str, Any]):
        """Send Discord notification for matched token"""
        try:
            message = f"""🚀 **Token Alert**
            
**Name**: {notification_data['name']}
**Symbol**: {notification_data['symbol']}
**Address**: `{notification_data['token_address']}`
**Keywords**: {', '.join(notification_data['keywords'])}
**Confidence**: {notification_data['confidence']:.2f}
**Source**: {notification_data['source']}
**Platform**: {notification_data['platform']}
"""
            
            # Use Discord notifier
            if hasattr(self.discord_notifier, 'send_message'):
                await self.discord_notifier.send_message(message)
            else:
                logger.info(f"📨 Notification: {notification_data['name']} - {', '.join(notification_data['keywords'])}")
                
        except Exception as e:
            logger.error(f"❌ Discord notification error: {e}")
    
    def setup_flask_routes(self):
        """Setup Flask routes for health checks and stats"""
        
        @self.app.route('/')
        def health_check():
            return jsonify({
                'status': 'healthy',
                'uptime': time.time() - self.stats['start_time'],
                'tokens_processed': self.stats['tokens_processed'],
                'notifications_sent': self.stats['notifications_sent'],
                'keywords_loaded': len(self.keywords)
            })
        
        @self.app.route('/stats')
        def get_stats():
            return jsonify(self.stats)
        
        @self.app.route('/keywords')
        def get_keywords():
            return jsonify(list(self.keywords))
    
    async def start_monitoring_loop(self):
        """Start the main monitoring loop"""
        logger.info("🚀 Starting clean monitoring loop...")
        
        # Load keywords
        self.load_keywords_from_database()
        
        # Initialize optimized components
        await self.initialize_optimized_components()
        
        while True:
            try:
                # Monitor LetsBonk tokens
                if hasattr(self.alchemy_scraper, 'get_latest_tokens'):
                    tokens = await self.alchemy_scraper.get_latest_tokens()
                    
                    for token in tokens:
                        await self.process_token_detection(token)
                
                # Short delay between checks
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"❌ Monitoring loop error: {e}")
                await asyncio.sleep(10)
    
    def start_flask_server(self):
        """Start Flask server in background thread"""
        def run_flask():
            serve(self.app, host='0.0.0.0', port=5000)
        
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info("✅ Flask server started on port 5000")
    
    def run(self):
        """Main entry point"""
        logger.info("🚀 Starting Clean Alchemy Server...")
        
        # Start Flask server
        self.start_flask_server()
        
        # Run monitoring loop
        try:
            asyncio.run(self.start_monitoring_loop())
        except KeyboardInterrupt:
            logger.info("🛑 Server stopped by user")
        except Exception as e:
            logger.error(f"❌ Server error: {e}")

# Global server instance
server = CleanAlchemyServer()

# Export Flask app for external access
app = server.app

def main():
    """Main function for Railway deployment"""
    server.run()

if __name__ == "__main__":
    main()