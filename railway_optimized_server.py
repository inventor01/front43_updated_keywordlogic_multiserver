#!/usr/bin/env python3
"""
Railway Optimized Server - Simplified startup for faster deployment
Focuses on immediate health and gradual component initialization
"""

import threading
import time
import logging
import os
from flask import Flask, jsonify
from waitress import serve

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RailwayOptimizedServer:
    def __init__(self):
        self.running = False
        self.app = Flask(__name__)
        self.setup_immediate_routes()
        
        # Initialize components gradually after server starts
        self.components_ready = False
        self.token_processor = None
        self.token_monitor = None
        
    def setup_immediate_routes(self):
        """Setup immediate routes for health checks"""
        @self.app.route('/health')
        def health():
            return jsonify({
                'status': 'healthy',
                'timestamp': time.time(),
                'components_ready': self.components_ready
            })
        
        @self.app.route('/')
        def home():
            return jsonify({
                'status': 'running',
                'system': 'Railway Token Monitoring System',
                'components_ready': self.components_ready,
                'features': [
                    'Immediate health check response',
                    'Gradual component initialization',
                    'Railway optimized deployment',
                    'Fallback token processing ready'
                ]
            })
        
        @self.app.route('/status')
        def status():
            return jsonify({
                'running': self.running,
                'components_ready': self.components_ready,
                'database_available': self.check_database(),
                'timestamp': time.time()
            })
    
    def check_database(self):
        """Quick database connectivity check"""
        try:
            database_url = os.getenv('DATABASE_URL')
            return database_url is not None
        except:
            return False
    
    def initialize_components_gradually(self):
        """Initialize heavy components after server is healthy"""
        def init_worker():
            try:
                logger.info("🔧 Initializing components gradually...")
                time.sleep(2)  # Let server become healthy first
                
                # Import and initialize components one by one
                from fixed_dual_table_processor import FixedDualTableProcessor
                from new_token_only_monitor import NewTokenOnlyMonitor
                from notification_enhanced_retry_service import NotificationEnhancedRetryService
                from enhanced_notification_system import enhanced_notifier
                
                logger.info("📊 Initializing token processor...")
                self.token_processor = FixedDualTableProcessor()
                
                logger.info("🔍 Creating database tables...")
                self.token_processor.create_tables_if_needed()
                
                logger.info("🔔 Initializing notification system...")
                # Initialize enhanced notification system
                self.notifier = enhanced_notifier
                
                logger.info("🔧 Initializing retry demonstration...")
                try:
                    from railway_retry_startup import railway_startup_retries
                    railway_startup_retries()
                    logger.info("✅ Railway retry demonstration initialized")
                except Exception as e:
                    logger.warning(f"⚠️ Retry demonstration failed: {e}")
                
                logger.info("🎯 Initializing token monitor...")
                self.token_monitor = NewTokenOnlyMonitor(self.handle_new_token)
                
                logger.info("📡 Starting background services...")
                self.start_background_services()
                
                self.components_ready = True
                logger.info("✅ All components initialized successfully")
                
            except Exception as e:
                logger.error(f"Component initialization error: {e}")
                # Server stays healthy even if components fail
                logger.error("Server remains healthy - components will retry")
        
        init_thread = threading.Thread(target=init_worker, daemon=True)
        init_thread.start()
    
    def handle_new_token(self, tokens):
        """Handle new tokens with fallback routing"""
        if not self.components_ready:
            logger.warning("Components not ready, skipping token processing")
            return
            
        for token in tokens:
            try:
                token_name = token.get('name', '')
                
                # Route unnamed tokens to fallback processing
                if token_name.startswith('Unnamed Token'):
                    logger.info(f"🔄 FALLBACK: {token_name} → enhanced resolution")
                    if self.token_processor:
                        self.token_processor.insert_fallback_token(
                            contract_address=token['address'],
                            token_name=token['name'],
                            symbol=token.get('symbol'),
                            processing_status='name_pending'
                        )
                    # CRITICAL: Do not process unnamed tokens in detected_tokens
                    logger.warning(f"🚫 BLOCKED: Unnamed token '{token_name}' from detected_tokens")
                    continue  # Skip to next token
                else:
                    logger.info(f"✅ DIRECT: {token_name} → immediate processing")
                    if self.token_processor:
                        self.token_processor.insert_detected_token(
                            address=token['address'],
                            name=token['name'],
                            symbol=token.get('symbol'),
                            name_status='resolved'
                        )
                        
                        # Send enhanced notification with duplicate prevention
                        if hasattr(self, 'notifier'):
                            self.notifier.send_enhanced_token_notification(
                                token_data=token,
                                matched_keyword=token.get('matched_keyword')
                            )
                        
            except Exception as e:
                logger.error(f"Token processing error: {e}")
    
    def start_background_services(self):
        """Start background monitoring and resolution services"""
        try:
            # Start token monitoring
            def monitor_worker():
                if self.token_monitor:
                    self.token_monitor.start_monitoring()
            
            monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
            monitor_thread.start()
            logger.info("🔍 Token monitor started")
            
            # Start lightweight retry demonstration (non-blocking)
            def quick_retry_demo():
                try:
                    from railway_retry_startup import railway_startup_retries
                    railway_startup_retries()
                    logger.info("✅ Railway retry demonstration completed")
                except Exception as e:
                    logger.warning(f"⚠️ Retry demo failed (non-critical): {e}")
            
            # Start fallback processing service
            def fallback_migration_worker():
                try:
                    logger.info("🔄 Starting fallback token migration service...")
                    import requests
                    
                    while True:
                        try:
                            # Get fallback tokens that need processing
                            fallback_tokens = self.token_processor.get_fallback_tokens(limit=5) if self.token_processor else []
                            
                            if fallback_tokens:
                                logger.info(f"🎯 Processing {len(fallback_tokens)} fallback tokens...")
                                
                                for token in fallback_tokens:
                                    contract_address = token[0]
                                    current_name = token[1]
                                    
                                    # Skip test addresses
                                    if contract_address.startswith(('TEST_', 'DEMO', 'RETRY', 'INVALID', 'FAKE', 'RAILWAY')):
                                        continue
                                    
                                    try:
                                        # Try DexScreener resolution
                                        url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
                                        response = requests.get(url, timeout=10)
                                        
                                        if response.status_code == 200:
                                            data = response.json()
                                            pairs = data.get('pairs', [])
                                            
                                            name = None
                                            symbol = 'UNKNOWN'
                                            
                                            if pairs and len(pairs) > 0:
                                                token_info = pairs[0]
                                                name = token_info.get('baseToken', {}).get('name')
                                                symbol = token_info.get('baseToken', {}).get('symbol', 'UNKNOWN')
                                            else:
                                                # Try alternative API or give up gracefully
                                                logger.info(f"🔍 No DexScreener data for {contract_address[:10]}...")
                                                # Update retry count
                                                if self.token_processor:
                                                    self.token_processor.update_fallback_retry_count(contract_address)
                                                continue
                                                
                                                if name and not name.startswith('Unnamed'):
                                                    # Success - migrate to detected_tokens
                                                    success = self.token_processor.migrate_fallback_to_detected(
                                                        contract_address=contract_address,
                                                        token_name=name,
                                                        symbol=symbol,
                                                        matched_keywords=[]
                                                    ) if self.token_processor else False
                                                    
                                                    if success:
                                                        logger.info(f"✅ MIGRATED: {name} ({contract_address[:10]}...)")
                                                    
                                    except Exception as e:
                                        logger.debug(f"Migration attempt failed: {e}")
                                    
                                    time.sleep(2)  # Rate limiting
                            else:
                                logger.info("📭 No fallback tokens to process")
                            
                            # Sleep for 2 minutes between cycles (more frequent processing)
                            time.sleep(120)
                            
                        except Exception as e:
                            logger.error(f"❌ Fallback migration cycle error: {e}")
                            time.sleep(60)
                            
                except Exception as e:
                    logger.error(f"❌ Fallback migration worker error: {e}")
            
            retry_thread = threading.Thread(target=quick_retry_demo, daemon=True)
            retry_thread.start()
            logger.info("🔄 Railway retry demonstration started")
            
            fallback_thread = threading.Thread(target=fallback_migration_worker, daemon=True)
            fallback_thread.start()
            logger.info("🔄 Fallback migration service started")
            
            # Start Discord bot service
            def discord_bot_worker():
                try:
                    logger.info("🤖 Starting Discord bot service...")
                    discord_token = os.getenv('DISCORD_TOKEN')
                    
                    if not discord_token:
                        logger.warning("⚠️ DISCORD_TOKEN not found - Discord bot disabled")
                        return
                    
                    logger.info("🔑 Discord token found - initializing bot...")
                    
                    # Import and start Discord bot
                    from complete_discord_bot import TokenMonitorBot
                    
                    bot = TokenMonitorBot()
                    logger.info("🤖 Discord bot initialized - attempting connection...")
                    
                    # Run bot in this thread
                    bot.run(discord_token, log_handler=None)
                    
                except Exception as e:
                    logger.error(f"❌ Discord bot error: {e}")
                    logger.info("🔄 System continues without Discord bot")
            
            discord_thread = threading.Thread(target=discord_bot_worker, daemon=True)
            discord_thread.start()
            logger.info("🤖 Discord bot service started")
            
        except Exception as e:
            logger.error(f"Background services error: {e}")
    
    def start_server(self, host='0.0.0.0', port=5000):
        """Start Railway optimized server"""
        logger.info("🚀 RAILWAY OPTIMIZED TOKEN MONITORING")
        logger.info("=" * 60)
        logger.info("⚡ FAST STARTUP: Immediate health check availability")
        logger.info("🔧 GRADUAL INIT: Components load after health check")
        logger.info("🌐 RAILWAY READY: Optimized for Railway deployment")
        logger.info("=" * 60)
        
        self.running = True
        
        # Start gradual component initialization
        self.initialize_components_gradually()
        
        # Get Railway port
        actual_port = int(os.getenv('PORT', port))
        logger.info(f"🌐 Binding to Railway port: {actual_port}")
        
        try:
            # Start Waitress server with Railway optimized settings
            serve(
                self.app, 
                host=host, 
                port=actual_port,
                threads=4,
                connection_limit=100,
                cleanup_interval=30,
                channel_timeout=120
            )
        except Exception as e:
            logger.error(f"Server error: {e}")
            self.running = False

if __name__ == "__main__":
    server = RailwayOptimizedServer()
    server.start_server()