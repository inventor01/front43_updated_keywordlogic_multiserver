#!/usr/bin/env python3
"""
Hybrid Token Processing Server
Integrates instant token processing with background name resolution
"""

import os
import time
import threading
import logging
from datetime import datetime

# Import the main server and background resolver
from alchemy_server import AlchemyMonitoringServer
from retry_pending_names import PendingNameResolver

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HybridTokenServer:
    """Complete hybrid token processing system"""
    
    def __init__(self):
        # Initialize main server
        self.server = AlchemyMonitoringServer()
        
        # Initialize background name resolver
        self.name_resolver = PendingNameResolver(update_callback=self.handle_name_update)
        
        # Background thread for name resolution
        self.resolver_thread = None
        self.running = True
        
    def handle_name_update(self, update_data):
        """Handle name resolution updates from background service"""
        try:
            address = update_data['address']
            old_name = update_data['old_name'] 
            new_name = update_data['new_name']
            
            logger.info(f"🔄 NAME UPDATE: {address[:10]}... '{old_name}' → '{new_name}'")
            
            # Optional: Send Discord update notification
            if hasattr(self.server, 'send_name_update_notification'):
                self.server.send_name_update_notification(update_data)
                
        except Exception as e:
            logger.debug(f"Name update handler error: {e}")
    
    def start_background_resolver(self):
        """Start the background name resolution service"""
        logger.info("🚀 Starting background name resolution service...")
        
        def resolver_worker():
            while self.running:
                try:
                    self.name_resolver.process_pending_tokens()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Background resolver error: {e}")
                    time.sleep(30)
        
        self.resolver_thread = threading.Thread(target=resolver_worker, daemon=True)
        self.resolver_thread.start()
        logger.info("✅ Background name resolver started")
    
    def start_server(self, host='0.0.0.0', port=5000):
        """Start the complete hybrid system"""
        logger.info("🎯 HYBRID TOKEN PROCESSING SYSTEM")
        logger.info("=" * 60)
        logger.info("⚡ INSTANT PROCESSING: All tokens processed immediately")
        logger.info("🔄 BACKGROUND RESOLUTION: Names updated when available")
        logger.info("📄 DATABASE TRACKING: All tokens stored with status")
        logger.info("=" * 60)
        
        # Start background name resolution
        self.start_background_resolver()
        
        # Start main server
        logger.info(f"🚀 Starting hybrid server on {host}:{port}")
        self.server.start_monitoring()
    
    def stop(self):
        """Stop the hybrid system"""
        logger.info("🛑 Stopping hybrid token processing system...")
        self.running = False
        
        if self.name_resolver:
            self.name_resolver.stop()
            
        if self.resolver_thread:
            self.resolver_thread.join(timeout=5)
            
        logger.info("✅ Hybrid system stopped")

def main():
    """Run the hybrid token processing server"""
    hybrid_server = HybridTokenServer()
    
    try:
        hybrid_server.start_server()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        hybrid_server.stop()

if __name__ == "__main__":
    main()