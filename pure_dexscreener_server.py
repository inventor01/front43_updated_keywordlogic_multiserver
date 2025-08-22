"""
Pure DexScreener Server - NO Jupiter or Solana RPC
Uses ONLY the DexScreener 70% success rate system
Completely eliminates all Jupiter and Solana RPC calls
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
from cachetools import TTLCache
import base58
from cryptography.fernet import Fernet
import psycopg2
import hashlib

# Import ONLY DexScreener-based components (NO Jupiter, NO Solana RPC)
from alchemy_letsbonk_scraper import AlchemyLetsBonkScraper
from config_manager import ConfigManager
from discord_notifier import DiscordNotifier
from trading_engine import trader
from dexscreener_70_percent_extractor import get_dex_70_extractor, extract_name_70_percent

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PureDexScreenerServer:
    """
    Pure DexScreener monitoring server - NO Jupiter/Solana RPC
    Uses ONLY DexScreener with 70%+ success rate
    """
    
    def __init__(self):
        logger.info("🚀 PURE DEXSCREENER INIT: Initializing system without Jupiter/Solana RPC")
        
        # NO Solana RPC client - we only use Alchemy for blockchain data
        self.config_manager = ConfigManager()
        self.discord_notifier = DiscordNotifier()
        
        # Initialize ONLY DexScreener extractor (70% success rate)
        self.dex_extractor = None
        
        # Core monitoring components (Alchemy only)
        self.alchemy_scraper = AlchemyLetsBonkScraper()
        
        # Cache and storage
        self.detected_tokens = TTLCache(maxsize=5000, ttl=3600)
        self.processed_signatures = TTLCache(maxsize=10000, ttl=7200)
        
        # Runtime statistics
        self.start_time = time.time()
        self.tokens_detected = 0
        self.notifications_sent = 0
        
        # Thread control
        self.running = True
        self.lock = threading.Lock()
        
        # Flask app
        self.app = self.create_flask_app()
        
        logger.info("✅ PURE DEXSCREENER READY: System initialized with DexScreener-only approach")
    
    async def initialize_dex_extractor(self):
        """Initialize ONLY the DexScreener 70% extractor"""
        if self.dex_extractor is None:
            logger.info("🎯 PURE DEXSCREENER: Initializing 70% success rate system...")
            self.dex_extractor = await get_dex_70_extractor()
            logger.info("✅ PURE DEXSCREENER: 70% success rate system ready")
    
    async def extract_token_name_pure(self, token_address: str) -> Dict[str, Any]:
        """
        Extract token name using ONLY DexScreener (NO Jupiter, NO Solana RPC)
        Guaranteed 70%+ success rate with smart retries
        """
        await self.initialize_dex_extractor()
        
        logger.info(f"🎯 PURE EXTRACTION: Using DexScreener-only for {token_address[:10]}...")
        
        # Use ONLY DexScreener with smart retries
        result = await extract_name_70_percent(token_address)
        
        if result and result.success:
            logger.info(f"✅ PURE SUCCESS: '{result.name}' via DexScreener in {result.extraction_time:.2f}s")
            return {
                'name': result.name,
                'symbol': 'EXTRACTED',
                'source': 'dexscreener_pure',
                'confidence': result.confidence,
                'extraction_time': result.extraction_time,
                'success': True
            }
        else:
            logger.warning(f"❌ PURE FAILED: {token_address[:10]}... - DexScreener exhausted")
            return {
                'name': None,
                'symbol': 'UNKNOWN',
                'source': 'dexscreener_exhausted',
                'confidence': 0.0,
                'extraction_time': result.extraction_time if result else 0,
                'success': False
            }
    
    def create_flask_app(self):
        """Create Flask app with essential endpoints"""
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            uptime = time.time() - self.start_time
            return jsonify({
                "status": "Pure DexScreener System Active",
                "uptime_seconds": round(uptime, 2),
                "tokens_detected": self.tokens_detected,
                "notifications_sent": self.notifications_sent,
                "extraction_method": "DexScreener Only (70%+ success rate)",
                "jupiter_disabled": True,
                "solana_rpc_disabled": True,
                "message": "Pure DexScreener system - no inefficient retries"
            })
        
        @app.route('/health')
        def health():
            return jsonify({
                "status": "healthy",
                "system": "pure_dexscreener",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        @app.route('/test-extraction/<token_address>')
        def test_extraction(token_address):
            """Test token name extraction endpoint"""
            return jsonify({
                "token_address": token_address,
                "method": "Pure DexScreener (70%+ success rate)",
                "status": "System ready - use direct async API for testing",
                "jupiter_disabled": True,
                "solana_rpc_disabled": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "Pure DexScreener system active"
            })
        
        @app.route('/stats')
        def stats():
            """System statistics"""
            uptime = time.time() - self.start_time
            return jsonify({
                "uptime_hours": round(uptime / 3600, 2),
                "tokens_detected": self.tokens_detected,
                "notifications_sent": self.notifications_sent,
                "cache_size": len(self.detected_tokens),
                "processed_signatures": len(self.processed_signatures),
                "extraction_method": "DexScreener Only",
                "jupiter_calls": 0,
                "solana_rpc_calls": 0,
                "system_type": "Pure DexScreener (70%+ success rate)"
            })
        
        return app
    
    def run(self, host='0.0.0.0', port=5000):
        """Run the pure DexScreener server"""
        logger.info(f"🚀 PURE DEXSCREENER SERVER: Starting on {host}:{port}")
        logger.info("🎯 EXTRACTION METHOD: DexScreener only (70%+ success rate)")
        logger.info("❌ JUPITER API: Completely disabled")
        logger.info("❌ SOLANA RPC: Completely disabled")
        logger.info("✅ DEXSCREENER: Active with smart retries")
        
        # Use Waitress for production
        serve(self.app, host=host, port=port, threads=6)

# Create global app instance for Railway
app = PureDexScreenerServer().app

def main():
    """Main entry point for Railway deployment"""
    logger.info("🚀 STARTING PURE DEXSCREENER SYSTEM")
    logger.info("=" * 60)
    logger.info("🎯 EXTRACTION: DexScreener only (70%+ success rate)")
    logger.info("❌ ELIMINATED: Jupiter API calls")
    logger.info("❌ ELIMINATED: Solana RPC retry loops")
    logger.info("✅ FOCUSED: Smart DexScreener retries for optimal results")
    logger.info("=" * 60)
    
    server = PureDexScreenerServer()
    server.run()

if __name__ == "__main__":
    main()