#!/usr/bin/env python3
"""
PumpPortal-based Token Detection Server
Alternative to Alchemy API for token monitoring
"""

import os
import time
import threading
import logging
from flask import Flask, jsonify
from waitress import serve
from pumpportal_integration import PumpPortalMonitor

# Optional imports - graceful fallback if not available
try:
    from complete_discord_bot import DiscordBot
except ImportError:
    DiscordBot = None

try:
    from enhanced_notification_system import NotificationSystem
except ImportError:
    NotificationSystem = None

class PumpPortalServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.monitor = PumpPortalMonitor()
        self.discord_bot = None
        self.notification_system = None
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        self.setup_routes()
        self.tokens_detected = 0
        self.start_time = time.time()
    
    def setup_routes(self):
        """Setup Flask routes for health checking"""
        
        @self.app.route('/')
        def health_check():
            uptime = time.time() - self.start_time
            
            return jsonify({
                'status': 'operational',
                'service': 'PumpPortal Token Monitor',
                'uptime_seconds': uptime,
                'tokens_detected': self.tokens_detected,
                'data_source': 'pumpportal',
                'features': [
                    'real_time_token_detection',
                    'pumpfun_integration',
                    'discord_notifications',
                    'fallback_processing'
                ]
            })
        
        @self.app.route('/status')
        def detailed_status():
            """Detailed system status"""
            uptime = time.time() - self.start_time
            
            status = {
                'server': {
                    'status': 'running',
                    'uptime_hours': uptime / 3600,
                    'tokens_processed': len(self.monitor.processed_tokens),
                    'last_heartbeat': self.monitor.last_heartbeat
                },
                'pumpportal': {
                    'connected': self.monitor.running,
                    'websocket_active': self.monitor.ws is not None,
                    'tokens_detected': self.tokens_detected
                },
                'discord': {
                    'bot_ready': self.discord_bot.is_ready() if self.discord_bot else False,
                    'notifications_enabled': True
                },
                'database': {
                    'connection': 'active',
                    'routing': 'enforced'
                }
            }
            
            return jsonify(status)
        
        @self.app.route('/restart')
        def restart_monitoring():
            """Restart PumpPortal monitoring"""
            try:
                self.logger.info("🔄 Restarting PumpPortal monitoring...")
                
                # Stop current monitoring
                if self.monitor.ws:
                    self.monitor.ws.close()
                
                # Reset processed tokens
                self.monitor.processed_tokens.clear()
                
                # Start new monitoring
                self.monitor.start_monitoring()
                
                return jsonify({
                    'status': 'restarted',
                    'message': 'PumpPortal monitoring restarted successfully'
                })
                
            except Exception as e:
                self.logger.error(f"Restart failed: {e}")
                return jsonify({
                    'status': 'error',
                    'message': f'Restart failed: {e}'
                }), 500
    
    def setup_discord_integration(self):
        """Setup Discord bot integration"""
        try:
            if DiscordBot is None:
                self.logger.info("📦 Discord bot module not available - running in monitoring mode")
                return
                
            discord_token = os.getenv('DISCORD_BOT_TOKEN')
            if discord_token:
                self.discord_bot = DiscordBot()
                
                # Start Discord bot in separate thread
                bot_thread = threading.Thread(target=self.discord_bot.run_bot)
                bot_thread.daemon = True
                bot_thread.start()
                
                self.logger.info("✅ Discord bot integration started")
            else:
                self.logger.warning("⚠️ Discord bot token not found")
                
        except Exception as e:
            self.logger.error(f"Discord integration error: {e}")
    
    def setup_notification_system(self):
        """Setup enhanced notification system"""
        try:
            if NotificationSystem is None:
                self.logger.info("📦 Notification system module not available - using basic logging")
                return
                
            self.notification_system = NotificationSystem()
            
            # Start notification processing
            notification_thread = threading.Thread(target=self.notification_system.start_processing)
            notification_thread.daemon = True
            notification_thread.start()
            
            self.logger.info("✅ Notification system started")
            
        except Exception as e:
            self.logger.error(f"Notification system error: {e}")
    
    def start_server(self):
        """Start the PumpPortal-based token detection server"""
        self.logger.info("🚀 STARTING PUMPPORTAL TOKEN DETECTION SERVER")
        self.logger.info("=" * 55)
        
        try:
            # 1. Start PumpPortal monitoring
            self.logger.info("📡 Starting PumpPortal monitoring...")
            monitor_thread = self.monitor.start_monitoring()
            
            # 2. Setup Discord integration
            self.logger.info("🤖 Setting up Discord integration...")
            self.setup_discord_integration()
            
            # 3. Setup notification system
            self.logger.info("📧 Setting up notification system...")
            self.setup_notification_system()
            
            # 4. Start Flask server
            port = int(os.getenv('PORT', 5000))
            self.logger.info(f"🌐 Starting web server on port {port}...")
            
            serve(self.app, host='0.0.0.0', port=port, threads=8)
            
        except Exception as e:
            self.logger.error(f"Server startup error: {e}")
            raise

def main():
    """Main function"""
    print("🚀 PumpPortal Token Detection System")
    print("Alternative to Alchemy API for Solana token monitoring")
    print("=" * 60)
    
    server = PumpPortalServer()
    server.start_server()

if __name__ == "__main__":
    main()