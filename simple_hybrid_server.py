#!/usr/bin/env python3
"""
Simple Hybrid Token Processing Server
Runs token monitoring with background name resolution
"""

import os
import time
import threading
import logging
from flask import Flask, jsonify
from waitress import serve

from new_token_only_monitor import NewTokenOnlyMonitor
from retry_pending_names import PendingNameResolver

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleHybridServer:
    """Simple hybrid token processing server with Flask API"""
    
    def __init__(self):
        # Create Flask app
        self.app = Flask(__name__)
        self.setup_routes()
        
        # Initialize background name resolver
        self.name_resolver = PendingNameResolver()
        
        # Initialize token monitor
        self.token_monitor = NewTokenOnlyMonitor(callback_func=self.handle_new_token)
        
        # Background threads
        self.resolver_thread = None
        self.monitor_thread = None
        self.running = True
        
    def setup_routes(self):
        """Setup Flask routes"""
        @self.app.route('/')
        def home():
            return jsonify({
                'status': 'active',
                'system': 'Hybrid Token Processing Server',
                'features': [
                    'Instant token processing',
                    'Background name resolution',
                    'PostgreSQL tracking'
                ]
            })
        
        @self.app.route('/status')
        def status():
            return jsonify({
                'running': self.running,
                'resolver_active': self.resolver_thread and self.resolver_thread.is_alive(),
                'monitor_active': self.monitor_thread and self.monitor_thread.is_alive(),
                'pending_tokens': len(self.name_resolver.get_pending_tokens()) if self.name_resolver else 0
            })
    
    def handle_new_token(self, tokens):
        """Handle new tokens from monitor"""
        for token in tokens:
            logger.info(f"🎯 NEW TOKEN: {token['name']} ({token['address'][:10]}...)")
            
            # Store in database (if hybrid processing enabled)
            if token.get('name_status') == 'pending':
                logger.info(f"⚡ INSTANT PROCESSING: {token['name']} (name resolution queued)")
            else:
                logger.info(f"✅ COMPLETE TOKEN: {token['name']} (real name found)")
    
    def start_background_resolver(self):
        """Start background name resolution service"""
        def resolver_worker():
            while self.running:
                try:
                    # Create event loop for async operation
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Run async function in the loop
                    loop.run_until_complete(self.name_resolver.process_pending_tokens())
                    loop.close()
                    
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Background resolver error: {e}")
                    time.sleep(30)
        
        self.resolver_thread = threading.Thread(target=resolver_worker, daemon=True)
        self.resolver_thread.start()
        logger.info("✅ Background name resolver started")
    
    def start_token_monitor(self):
        """Start token monitoring"""
        def monitor_worker():
            try:
                self.token_monitor.start_monitoring()
            except Exception as e:
                logger.error(f"Token monitor error: {e}")
        
        self.monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
        self.monitor_thread.start()
        logger.info("✅ Token monitor started")
    
    def start_server(self, host='0.0.0.0', port=5000):
        """Start the complete hybrid system"""
        logger.info("🎯 SIMPLE HYBRID TOKEN PROCESSING SERVER")
        logger.info("=" * 60)
        logger.info("⚡ INSTANT PROCESSING: All tokens processed immediately")
        logger.info("🔄 BACKGROUND RESOLUTION: Names updated when available")
        logger.info("📄 DATABASE TRACKING: All tokens stored with status")
        logger.info("🌐 API ENDPOINTS: / and /status available")
        logger.info("=" * 60)
        
        # Start background services
        self.start_background_resolver()
        self.start_token_monitor()
        
        # Start Flask server with Waitress
        logger.info(f"🚀 Starting server on {host}:{port}")
        serve(self.app, host=host, port=port)
    
    def stop(self):
        """Stop the hybrid system"""
        logger.info("🛑 Stopping hybrid token processing system...")
        self.running = False
        
        if self.name_resolver:
            self.name_resolver.stop()

def main():
    """Run the simple hybrid server"""
    server = SimpleHybridServer()
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        server.stop()

if __name__ == "__main__":
    main()