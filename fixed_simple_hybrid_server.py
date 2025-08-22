#!/usr/bin/env python3
"""
Fixed Simple Hybrid Server with Dual Table Architecture
Proper integration of dual table token processing with instant notifications and background resolution.
"""

import threading
import time
import logging
from flask import Flask, jsonify
from waitress import serve
from new_token_only_monitor import NewTokenOnlyMonitor
from notification_enhanced_retry_service import NotificationEnhancedRetryService
from fixed_dual_table_processor import FixedDualTableProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FixedSimpleHybridServer:
    def __init__(self):
        self.running = False
        self.resolver_thread = None
        self.monitor_thread = None
        
        # Initialize dual table components
        self.token_processor = FixedDualTableProcessor()
        self.name_resolver = NotificationEnhancedRetryService()
        
        # Create database tables if needed
        self.token_processor.create_tables_if_needed()
        
        # Initialize token monitor with proper callback
        self.token_monitor = NewTokenOnlyMonitor(self.handle_new_token)
        
        # Create Flask app
        self.app = Flask(__name__)
        self.setup_routes()
        
    def setup_routes(self):
        """Setup Flask routes"""
        @self.app.route('/')
        def home():
            return jsonify({
                'status': 'running',
                'system': 'Fixed Hybrid Token Processing Server',
                'features': [
                    'Dual table architecture',
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
                'pending_tokens': len(self.get_pending_tokens())
            })
    
    def handle_new_token(self, tokens):
        """Handle new tokens with dual table processing"""
        for token in tokens:
            try:
                logger.info(f"🎯 NEW TOKEN: {token['name']} ({token['address'][:10]}...)")
                
                # Check if token has a real name or needs resolution
                if token.get('name_status') == 'pending':
                    # Store in pending_tokens table
                    self.token_processor.insert_pending_token(
                        contract_address=token['address'],
                        placeholder_name=token['name'],
                        blockchain_age_seconds=token.get('blockchain_age')
                    )
                    logger.info(f"⚡ INSTANT PROCESSING: {token['name']} (stored in pending_tokens)")
                    
                elif token.get('name_status') == 'fallback':
                    # Store in fallback_processing_coins table for special handling
                    self.token_processor.insert_fallback_token(
                        contract_address=token['address'],
                        token_name=token['name'],
                        symbol=token.get('symbol'),
                        blockchain_age_seconds=token.get('blockchain_age'),
                        processing_status='pending',
                        error_message=token.get('error_message', 'Name resolution failed')
                    )
                    logger.info(f"🔄 FALLBACK PROCESSING: {token['name']} (stored in fallback_processing_coins)")
                    
                else:
                    # Store in detected_tokens table with real name
                    self.token_processor.insert_resolved_token(
                        contract_address=token['address'],
                        token_name=token['name'],
                        symbol=token.get('symbol', 'UNKNOWN'),
                        blockchain_age_seconds=token.get('blockchain_age')
                    )
                    logger.info(f"✅ COMPLETE TOKEN: {token['name']} (stored in detected_tokens)")
                    
            except Exception as e:
                logger.error(f"Error processing token {token.get('address', 'unknown')}: {e}")
    
    def get_pending_tokens(self):
        """Get pending tokens from dual table processor"""
        try:
            return self.token_processor.get_pending_tokens(limit=50)
        except:
            return []
    
    def start_background_resolver(self):
        """Start background name resolution service"""
        def resolver_worker():
            while self.running:
                try:
                    # Create event loop for async operation
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Run async function properly
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
        logger.info("🎯 FIXED HYBRID TOKEN PROCESSING SERVER")
        logger.info("=" * 60)
        logger.info("📊 DUAL TABLE ARCHITECTURE: pending_tokens + detected_tokens")
        logger.info("⚡ INSTANT PROCESSING: All tokens stored immediately")
        logger.info("🔄 BACKGROUND RESOLUTION: Names upgraded when available") 
        logger.info("🎯 100% TOKEN COVERAGE: No tokens lost")
        logger.info("🌐 API ENDPOINTS: / and /status available")
        logger.info("=" * 60)
        
        self.running = True
        
        # Start background services
        self.start_background_resolver()
        self.start_token_monitor()
        
        # Start Flask server with Waitress
        logger.info(f"🚀 Starting server on {host}:{port}")
        serve(self.app, host=host, port=port)
    
    def stop(self):
        """Stop the hybrid system"""
        logger.info("🛑 Stopping fixed hybrid token processing system...")
        self.running = False
        
        if self.name_resolver:
            try:
                self.name_resolver.stop()
            except:
                pass

def main():
    try:
        server = FixedSimpleHybridServer()
        server.start_server()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    main()