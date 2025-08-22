#!/usr/bin/env python3
"""
Simple PumpPortal Monitor for Replit
Minimal version focused on token detection and basic web interface
"""

import os
import time
import threading
import logging
import json
from flask import Flask, jsonify, render_template_string
from waitress import serve
from pumpportal_integration import PumpPortalMonitor

class SimplePumpPortalServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.monitor = PumpPortalMonitor()
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        self.setup_routes()
        self.tokens_detected = 0
        self.start_time = time.time()
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def home():
            uptime = time.time() - self.start_time
            uptime_hours = uptime / 3600
            
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>PumpPortal Token Monitor</title>
                <meta http-equiv="refresh" content="30">
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a1a; color: #fff; }
                    .container { max-width: 800px; margin: 0 auto; }
                    .status { background: #2d2d2d; padding: 20px; border-radius: 8px; margin: 20px 0; }
                    .metric { display: inline-block; margin: 10px 20px 10px 0; }
                    .value { font-size: 24px; font-weight: bold; color: #4CAF50; }
                    .label { color: #ccc; font-size: 14px; }
                    .active { color: #4CAF50; }
                    .inactive { color: #f44336; }
                    .warning { color: #ff9800; }
                    h1 { color: #4CAF50; }
                    h2 { color: #2196F3; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🚀 PumpPortal Token Monitor</h1>
                    <h2>Real-time Pumpfun Token Detection</h2>
                    
                    <div class="status">
                        <h3>System Status</h3>
                        <div class="metric">
                            <div class="value {{ 'active' if status.connected else 'inactive' }}">
                                {{ 'CONNECTED' if status.connected else 'DISCONNECTED' }}
                            </div>
                            <div class="label">WebSocket Status</div>
                        </div>
                        
                        <div class="metric">
                            <div class="value">{{ status.tokens_processed }}</div>
                            <div class="label">Tokens Processed</div>
                        </div>
                        
                        <div class="metric">
                            <div class="value">{{ "%.1f"|format(status.uptime_hours) }}h</div>
                            <div class="label">Uptime</div>
                        </div>
                    </div>
                    
                    <div class="status">
                        <h3>PumpPortal Integration</h3>
                        <p><strong>WebSocket URL:</strong> wss://pumpportal.fun/api/data</p>
                        <p><strong>Data Source:</strong> Pumpfun (Real-time)</p>
                        <p><strong>Rate Limits:</strong> None (Free API)</p>
                        <p><strong>Alternative to:</strong> Rate-limited Alchemy API</p>
                    </div>
                    
                    <div class="status">
                        <h3>Recent Activity</h3>
                        <p>Last heartbeat: {{ status.last_heartbeat_ago }}s ago</p>
                        <p>Database: {{ 'Connected' if status.db_connected else 'Disconnected' }}</p>
                        <p>Auto-refresh: 30 seconds</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Get current status
            status = {
                'connected': self.monitor.running,
                'tokens_processed': len(self.monitor.processed_tokens),
                'uptime_hours': uptime_hours,
                'last_heartbeat_ago': int(time.time() - self.monitor.last_heartbeat),
                'db_connected': True  # Simplified for demo
            }
            
            return render_template_string(html_template, status=status)
        
        @self.app.route('/api/status')
        def api_status():
            uptime = time.time() - self.start_time
            
            return jsonify({
                'service': 'PumpPortal Token Monitor',
                'status': 'running',
                'uptime_seconds': uptime,
                'websocket_connected': self.monitor.running,
                'tokens_processed': len(self.monitor.processed_tokens),
                'last_heartbeat': self.monitor.last_heartbeat,
                'data_source': 'pumpportal'
            })
        
        @self.app.route('/api/restart')
        def restart_monitor():
            """Restart PumpPortal monitoring"""
            try:
                self.logger.info("🔄 Restarting PumpPortal monitor...")
                
                if self.monitor.ws:
                    self.monitor.ws.close()
                
                self.monitor.processed_tokens.clear()
                self.monitor.start_monitoring()
                
                return jsonify({'status': 'restarted'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def start_server(self):
        """Start the server"""
        self.logger.info("🚀 Starting PumpPortal Token Monitor on Replit")
        
        # Start PumpPortal monitoring
        self.logger.info("📡 Initializing PumpPortal WebSocket connection...")
        self.monitor.start_monitoring()
        
        # Start Flask server
        port = int(os.getenv('PORT', 5000))
        self.logger.info(f"🌐 Starting web interface on port {port}")
        
        serve(self.app, host='0.0.0.0', port=port, threads=4)

def main():
    server = SimplePumpPortalServer()
    server.start_server()

if __name__ == "__main__":
    main()