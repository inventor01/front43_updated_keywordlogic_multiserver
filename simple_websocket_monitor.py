#!/usr/bin/env python3
"""
Simple WebSocket Monitor using asyncio and websockets
Alternative implementation for Replit compatibility
"""

import asyncio
import websockets
import json
import time
import threading
import psycopg2
import os
import requests
from datetime import datetime
import logging
from flask import Flask, jsonify, render_template_string
from waitress import serve

class SimpleWebSocketMonitor:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            self.database_url = 'postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway'
        
        self.websocket_url = "wss://pumpportal.fun/api/data"
        self.running = False
        self.processed_tokens = set()
        self.last_heartbeat = time.time()
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def connect_and_monitor(self):
        """Connect to PumpPortal and monitor for tokens"""
        try:
            self.logger.info(f"🔗 Connecting to {self.websocket_url}")
            
            async with websockets.connect(self.websocket_url) as websocket:
                self.running = True
                self.logger.info("✅ Connected to PumpPortal")
                
                # Subscribe to new token events
                subscribe_message = json.dumps({"method": "subscribeNewToken"})
                await websocket.send(subscribe_message)
                self.logger.info("📡 Subscribed to new token events")
                
                # Listen for messages
                async for message in websocket:
                    try:
                        self.last_heartbeat = time.time()
                        data = json.loads(message)
                        await self.process_token_data(data)
                        
                    except json.JSONDecodeError:
                        self.logger.warning(f"Invalid JSON: {message[:100]}")
                    except Exception as e:
                        self.logger.error(f"Message processing error: {e}")
        
        except Exception as e:
            self.logger.error(f"WebSocket connection error: {e}")
            self.running = False
    
    async def process_token_data(self, data):
        """Process incoming token data"""
        try:
            # Check for new token events
            if data.get('type') == 'new_token' or 'mint' in data:
                token_address = data.get('mint') or data.get('address')
                token_name = data.get('name', 'Unknown')
                token_symbol = data.get('symbol', '')
                
                if token_address and token_address not in self.processed_tokens:
                    self.processed_tokens.add(token_address)
                    
                    self.logger.info(f"🆕 New token: {token_name} ({token_symbol}) - {token_address}")
                    
                    # Enhanced name resolution
                    enhanced_name = await self.enhance_token_name(token_address, token_name)
                    
                    # Insert to database
                    await self.insert_token_to_database(token_address, enhanced_name, token_symbol)
        
        except Exception as e:
            self.logger.error(f"Token processing error: {e}")
    
    async def enhance_token_name(self, address, raw_name):
        """Enhance token name using DexScreener"""
        try:
            if raw_name and raw_name != 'Unknown' and not raw_name.startswith('Unnamed'):
                return raw_name
            
            # Fallback to DexScreener
            url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                if pairs:
                    enhanced_name = pairs[0].get('baseToken', {}).get('name')
                    if enhanced_name and enhanced_name != raw_name:
                        self.logger.info(f"🔍 Enhanced: {raw_name} → {enhanced_name}")
                        return enhanced_name
        
        except Exception as e:
            self.logger.warning(f"Name enhancement failed: {e}")
        
        return raw_name
    
    async def insert_token_to_database(self, address, name, symbol):
        """Insert token to database"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # Determine which table based on name quality
            if self.is_valid_token_name(name):
                cursor.execute("""
                    INSERT INTO detected_tokens (address, name, symbol, created_at, name_status, status, data_source)
                    VALUES (%s, %s, %s, %s, 'resolved', 'detected', 'pumpportal')
                    ON CONFLICT (address) DO NOTHING
                """, (address, name, symbol, datetime.now()))
                
                if cursor.rowcount > 0:
                    self.logger.info(f"✅ Added to detected_tokens: {name}")
            else:
                cursor.execute("""
                    INSERT INTO fallback_processing_coins (address, name, symbol, created_at, status, data_source)
                    VALUES (%s, %s, %s, %s, 'pending', 'pumpportal')
                    ON CONFLICT (address) DO NOTHING
                """, (address, name, symbol, datetime.now()))
                
                if cursor.rowcount > 0:
                    self.logger.info(f"📦 Added to fallback: {name}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Database error: {e}")
    
    def is_valid_token_name(self, name):
        """Check if token name is valid"""
        if not name or name == 'Unknown':
            return False
        
        invalid_patterns = ['Unnamed Token', 'Unknown Token', 'letsbonk']
        return not any(pattern.lower() in name.lower() for pattern in invalid_patterns)
    
    def start_monitoring(self):
        """Start monitoring in a separate thread"""
        def run_asyncio_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            while True:
                try:
                    loop.run_until_complete(self.connect_and_monitor())
                except Exception as e:
                    self.logger.error(f"Monitor error: {e}")
                
                # Reconnect after delay
                time.sleep(5)
                self.logger.info("🔄 Attempting reconnection...")
        
        monitor_thread = threading.Thread(target=run_asyncio_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        return monitor_thread

class SimpleMonitorServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.monitor = SimpleWebSocketMonitor()
        self.start_time = time.time()
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def home():
            uptime = time.time() - self.start_time
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>PumpPortal Monitor</title>
                <meta http-equiv="refresh" content="30">
                <style>
                    body { font-family: Arial; margin: 40px; background: #1a1a1a; color: #fff; }
                    .container { max-width: 800px; margin: 0 auto; }
                    .status { background: #2d2d2d; padding: 20px; border-radius: 8px; margin: 20px 0; }
                    .metric { display: inline-block; margin: 10px 20px; }
                    .value { font-size: 24px; font-weight: bold; color: #4CAF50; }
                    .label { color: #ccc; font-size: 14px; }
                    h1 { color: #4CAF50; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🚀 PumpPortal Token Monitor</h1>
                    
                    <div class="status">
                        <h3>System Status</h3>
                        <div class="metric">
                            <div class="value">{{ 'ACTIVE' if status.running else 'STOPPED' }}</div>
                            <div class="label">Monitor Status</div>
                        </div>
                        <div class="metric">
                            <div class="value">{{ status.tokens_count }}</div>
                            <div class="label">Tokens Processed</div>
                        </div>
                        <div class="metric">
                            <div class="value">{{ "%.1f"|format(status.uptime_hours) }}h</div>
                            <div class="label">Uptime</div>
                        </div>
                    </div>
                    
                    <div class="status">
                        <h3>PumpPortal Integration</h3>
                        <p><strong>Status:</strong> {{ 'Connected' if status.running else 'Disconnected' }}</p>
                        <p><strong>Data Source:</strong> Pumpfun WebSocket (wss://pumpportal.fun/api/data)</p>
                        <p><strong>Alternative to:</strong> Rate-limited Alchemy API</p>
                        <p><strong>Last Activity:</strong> {{ status.last_activity }}s ago</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            status = {
                'running': self.monitor.running,
                'tokens_count': len(self.monitor.processed_tokens),
                'uptime_hours': uptime / 3600,
                'last_activity': int(time.time() - self.monitor.last_heartbeat)
            }
            
            return render_template_string(html, status=status)
        
        @self.app.route('/api/status')
        def api_status():
            return jsonify({
                'service': 'PumpPortal Monitor',
                'running': self.monitor.running,
                'tokens_processed': len(self.monitor.processed_tokens),
                'uptime': time.time() - self.start_time,
                'last_heartbeat': self.monitor.last_heartbeat
            })
    
    def start_server(self):
        """Start the server"""
        self.logger.info("🚀 Starting Simple PumpPortal Monitor")
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        # Start web server
        port = int(os.getenv('PORT', 5000))
        self.logger.info(f"🌐 Web interface on port {port}")
        
        serve(self.app, host='0.0.0.0', port=port, threads=4)

def main():
    server = SimpleMonitorServer()
    server.start_server()

if __name__ == "__main__":
    main()