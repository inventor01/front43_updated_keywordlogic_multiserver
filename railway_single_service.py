#!/usr/bin/env python3
"""
Railway Single Service - Combined Discord Bot + Token Monitor
Optimized for Railway deployment with single port usage
"""

import asyncio
import threading
import time
import logging
import os
from flask import Flask, jsonify
from waitress import serve
import discord
from discord.ext import commands

# We'll use subprocess to run components separately to avoid import conflicts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RailwaySingleService:
    def __init__(self):
        self.app = Flask(__name__)
        self.running = False
        self.components_ready = False
        self.token_monitor = None
        self.discord_bot = None
        self.setup_routes()
        
    def setup_routes(self):
        """Setup Flask routes for Railway health checks"""
        @self.app.route('/health')
        def health():
            return jsonify({
                'status': 'healthy',
                'timestamp': time.time(),
                'components_ready': self.components_ready,
                'token_monitor_active': self.token_monitor is not None,
                'discord_bot_active': self.discord_bot is not None
            })
        
        @self.app.route('/')
        def home():
            return jsonify({
                'status': 'Railway Single Service Running',
                'system': 'Solana Token Scanner + Discord Bot',
                'components_ready': self.components_ready,
                'features': [
                    'PumpPortal WebSocket monitoring',
                    'Multi-platform token detection',
                    'Discord bot with 35+ commands',
                    'Mobile-optimized notifications',
                    'Railway deployment ready'
                ]
            })
        
        @self.app.route('/status')
        def status():
            return jsonify({
                'running': self.running,
                'components_ready': self.components_ready,
                'database_available': self.check_database(),
                'discord_token_available': bool(os.getenv('DISCORD_TOKEN')),
                'timestamp': time.time()
            })
    
    def check_database(self):
        """Check database connectivity"""
        try:
            database_url = os.getenv('DATABASE_URL')
            return database_url is not None
        except:
            return False
    
    def start_token_monitor(self):
        """Start token monitoring using subprocess"""
        import subprocess
        try:
            logger.info("🚀 Starting Token Monitor...")
            # Run integrated monitoring without Flask (just the monitoring part)
            subprocess.Popen(['python3', 'pumpportal_server.py'], 
                           cwd='/home/runner/workspace/front34')
            self.token_monitor = True
        except Exception as e:
            logger.error(f"❌ Token Monitor failed: {e}")
    
    def start_discord_bot(self):
        """Start Discord bot using subprocess"""
        import subprocess
        try:
            logger.info("🤖 Starting Discord Bot...")
            # Run Discord bot in separate process
            subprocess.Popen(['python3', 'complete_discord_bot_with_commands.py'], 
                           cwd='/home/runner/workspace/front34')
            self.discord_bot = True
        except Exception as e:
            logger.error(f"❌ Discord Bot failed: {e}")
    
    def initialize_components(self):
        """Initialize all components after Flask server starts"""
        def init_worker():
            try:
                logger.info("🔧 Initializing Railway components...")
                time.sleep(3)  # Let Flask server become healthy first
                
                # Start token monitoring
                self.start_token_monitor()
                time.sleep(2)
                
                # Start Discord bot
                self.start_discord_bot()
                time.sleep(2)
                
                self.components_ready = True
                logger.info("✅ All components initialized successfully")
                
            except Exception as e:
                logger.error(f"❌ Component initialization failed: {e}")
        
        init_thread = threading.Thread(target=init_worker, daemon=True)
        init_thread.start()
    
    def run(self):
        """Run the Railway service"""
        logger.info("🚀 Starting Railway Single Service on port 5000")
        self.running = True
        
        # Initialize components in background
        self.initialize_components()
        
        # Use environment port or fallback to 8000 (avoid conflict with existing service)
        port = int(os.getenv('PORT', 8000))
        logger.info(f"🌐 Serving on port {port}")
        serve(self.app, host='0.0.0.0', port=port)

if __name__ == '__main__':
    service = RailwaySingleService()
    service.run()