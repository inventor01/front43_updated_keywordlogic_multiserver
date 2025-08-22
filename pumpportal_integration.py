#!/usr/bin/env python3
"""
PumpPortal Integration for Pumpfun Token Detection
Alternative data source to replace rate-limited Alchemy API
"""

from websocket import WebSocketApp
import json
import time
import threading
import psycopg2
import os
import requests
from datetime import datetime, timedelta
import logging

class PumpPortalMonitor:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            self.database_url = 'postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway'
        
        self.websocket_url = "wss://pumpportal.fun/api/data"
        self.ws = None
        self.running = False
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.processed_tokens = set()
        self.last_heartbeat = time.time()
    
    def connect_websocket(self):
        """Connect to PumpPortal WebSocket for real-time token data"""
        try:
            self.ws = WebSocketApp(
                self.websocket_url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            
            self.logger.info("Connecting to PumpPortal WebSocket...")
            self.ws.run_forever()
            
        except Exception as e:
            self.logger.error(f"WebSocket connection error: {e}")
    
    def on_open(self, ws):
        """WebSocket connection opened"""
        self.logger.info("✅ Connected to PumpPortal")
        self.running = True
        
        # Subscribe to new token creations
        subscribe_message = {
            "method": "subscribeNewToken"
        }
        
        ws.send(json.dumps(subscribe_message))
        self.logger.info("📡 Subscribed to new token events")
    
    def on_message(self, ws, message):
        """Process incoming token data"""
        try:
            data = json.loads(message)
            
            # Update heartbeat
            self.last_heartbeat = time.time()
            
            # Process new token creation events
            if data.get('type') == 'new_token':
                self.process_new_token(data)
            
            # Handle pumpfun specific events
            elif data.get('source') == 'pumpfun':
                self.process_pumpfun_token(data)
                
        except json.JSONDecodeError:
            self.logger.warning(f"Invalid JSON received: {message}")
        except Exception as e:
            self.logger.error(f"Message processing error: {e}")
    
    def process_new_token(self, token_data):
        """Process new token creation from PumpPortal"""
        try:
            # Extract token information
            token_address = token_data.get('mint')
            token_name = token_data.get('name', 'Unknown')
            token_symbol = token_data.get('symbol', '')
            created_timestamp = token_data.get('timestamp')
            
            if not token_address:
                self.logger.warning("Token data missing address")
                return
            
            # Avoid duplicate processing
            if token_address in self.processed_tokens:
                return
            
            self.processed_tokens.add(token_address)
            
            self.logger.info(f"🆕 New token detected: {token_name} ({token_symbol}) - {token_address}")
            
            # Enhanced name resolution for pumpfun tokens
            resolved_name = self.enhance_token_name(token_address, token_name)
            
            # Route to appropriate table based on name quality
            if self.is_valid_token_name(resolved_name):
                self.insert_detected_token(token_address, resolved_name, token_symbol, created_timestamp)
            else:
                self.insert_fallback_token(token_address, token_name, token_symbol, created_timestamp)
            
        except Exception as e:
            self.logger.error(f"New token processing error: {e}")
    
    def process_pumpfun_token(self, token_data):
        """Process pumpfun-specific token data"""
        try:
            # Pumpfun tokens often have better metadata
            token_address = token_data.get('mint') or token_data.get('address')
            metadata = token_data.get('metadata', {})
            
            token_name = metadata.get('name') or token_data.get('name', 'Unknown')
            token_symbol = metadata.get('symbol') or token_data.get('symbol', '')
            
            # Pumpfun tokens are generally higher quality
            if token_address and not token_address in self.processed_tokens:
                self.processed_tokens.add(token_address)
                
                self.logger.info(f"🚀 Pumpfun token: {token_name} ({token_symbol}) - {token_address}")
                
                # Enhanced metadata from pumpfun
                enhanced_name = self.enhance_pumpfun_name(token_data)
                
                # Most pumpfun tokens go directly to detected_tokens
                self.insert_detected_token(token_address, enhanced_name, token_symbol, token_data.get('timestamp'))
                
        except Exception as e:
            self.logger.error(f"Pumpfun token processing error: {e}")
    
    def enhance_token_name(self, address, raw_name):
        """Enhance token name using DexScreener API"""
        try:
            if raw_name and raw_name != 'Unknown' and not raw_name.startswith('Unnamed'):
                return raw_name
            
            # Fallback to DexScreener for name resolution
            url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                if pairs:
                    token_info = pairs[0].get('baseToken', {})
                    enhanced_name = token_info.get('name')
                    
                    if enhanced_name and enhanced_name != raw_name:
                        self.logger.info(f"🔍 Enhanced name: {raw_name} → {enhanced_name}")
                        return enhanced_name
            
        except Exception as e:
            self.logger.warning(f"Name enhancement failed for {address}: {e}")
        
        return raw_name
    
    def enhance_pumpfun_name(self, token_data):
        """Extract enhanced name from pumpfun metadata"""
        try:
            # Try multiple name sources from pumpfun data
            metadata = token_data.get('metadata', {})
            
            # Priority order for name extraction
            name_sources = [
                metadata.get('name'),
                token_data.get('name'),
                metadata.get('title'),
                token_data.get('title')
            ]
            
            for name in name_sources:
                if name and isinstance(name, str) and len(name.strip()) > 0:
                    cleaned_name = name.strip()
                    if not cleaned_name.startswith('Unnamed') and cleaned_name != 'Unknown':
                        return cleaned_name
            
            # Fallback to address-based naming
            return f"Pumpfun Token {token_data.get('mint', '')[:8]}"
            
        except Exception as e:
            self.logger.warning(f"Pumpfun name enhancement error: {e}")
            return token_data.get('name', 'Unknown Pumpfun Token')
    
    def is_valid_token_name(self, name):
        """Check if token name is valid for immediate processing"""
        if not name or name == 'Unknown':
            return False
        
        invalid_patterns = ['Unnamed Token', 'Unknown Token', 'letsbonk', 'token_']
        
        for pattern in invalid_patterns:
            if pattern.lower() in name.lower():
                return False
        
        return len(name.strip()) > 2
    
    def insert_detected_token(self, address, name, symbol, timestamp):
        """Insert token into detected_tokens table"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # Convert timestamp if needed
            created_at = datetime.now()
            if timestamp:
                try:
                    created_at = datetime.fromtimestamp(timestamp / 1000) if timestamp > 1000000000000 else datetime.fromtimestamp(timestamp)
                except:
                    pass
            
            cursor.execute("""
                INSERT INTO detected_tokens (address, name, symbol, created_at, name_status, status, data_source)
                VALUES (%s, %s, %s, %s, 'resolved', 'detected', 'pumpportal')
                ON CONFLICT (address) DO NOTHING
            """, (address, name, symbol, created_at))
            
            if cursor.rowcount > 0:
                self.logger.info(f"✅ Inserted to detected_tokens: {name}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Database insert error (detected): {e}")
    
    def insert_fallback_token(self, address, name, symbol, timestamp):
        """Insert token into fallback_processing_coins table"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            created_at = datetime.now()
            if timestamp:
                try:
                    created_at = datetime.fromtimestamp(timestamp / 1000) if timestamp > 1000000000000 else datetime.fromtimestamp(timestamp)
                except:
                    pass
            
            cursor.execute("""
                INSERT INTO fallback_processing_coins (address, name, symbol, created_at, status, data_source)
                VALUES (%s, %s, %s, %s, 'pending', 'pumpportal')
                ON CONFLICT (address) DO NOTHING
            """, (address, name, symbol, created_at))
            
            if cursor.rowcount > 0:
                self.logger.info(f"📦 Inserted to fallback: {name}")
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Database insert error (fallback): {e}")
    
    def on_error(self, ws, error):
        """WebSocket error handler"""
        self.logger.error(f"WebSocket error: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """WebSocket connection closed"""
        self.logger.warning(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        self.running = False
        
        # Attempt reconnection after delay
        time.sleep(5)
        if not self.running:
            self.logger.info("Attempting reconnection...")
            self.connect_websocket()
    
    def start_monitoring(self):
        """Start PumpPortal monitoring"""
        self.logger.info("🚀 Starting PumpPortal token monitoring...")
        
        # Start websocket in separate thread
        ws_thread = threading.Thread(target=self.connect_websocket)
        ws_thread.daemon = True
        ws_thread.start()
        
        # Start heartbeat monitoring
        heartbeat_thread = threading.Thread(target=self.monitor_heartbeat)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        
        return ws_thread
    
    def monitor_heartbeat(self):
        """Monitor connection health"""
        while True:
            time.sleep(30)  # Check every 30 seconds
            
            if time.time() - self.last_heartbeat > 120:  # 2 minutes without data
                self.logger.warning("Heartbeat timeout - connection may be stale")
                if self.ws:
                    self.ws.close()
            
            if self.running:
                self.logger.info(f"📡 PumpPortal status: Active ({len(self.processed_tokens)} tokens processed)")

def main():
    """Main function to start PumpPortal monitoring"""
    monitor = PumpPortalMonitor()
    
    try:
        ws_thread = monitor.start_monitoring()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        monitor.logger.info("Shutting down PumpPortal monitor...")
        monitor.running = False
        if monitor.ws:
            monitor.ws.close()

if __name__ == "__main__":
    main()