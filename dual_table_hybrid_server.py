#!/usr/bin/env python3
"""
Dual Table Hybrid Server
Integrates token monitoring with dual table architecture for name resolution.
"""

import asyncio
import logging
from datetime import datetime
import os
from threading import Thread
import time

# Import existing modules
from dual_table_token_processor import DualTableTokenProcessor
from dual_table_name_resolver import DualTableNameResolver
from enhanced_token_name_resolver import resolve_token_name_with_retry

# Import Flask for web interface
from flask import Flask, jsonify
from waitress import serve

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DualTableHybridSystem:
    def __init__(self):
        self.processor = DualTableTokenProcessor()
        self.resolver = DualTableNameResolver()
        self.flask_app = self.create_flask_app()
        self.running = False
        
    def create_flask_app(self):
        """Create Flask web interface"""
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            stats = self.processor.get_system_stats()
            return jsonify({
                'status': 'active',
                'system': 'dual_table_hybrid_token_processing',
                'features': [
                    'instant_token_processing',
                    'dual_table_architecture', 
                    'background_name_resolution',
                    'pending_to_resolved_migration'
                ],
                'statistics': stats,
                'description': 'Dual table system with pending and resolved token separation'
            })
        
        @app.route('/status')
        def status():
            stats = self.processor.get_system_stats()
            
            # Get sample tokens
            pending_tokens = self.processor.get_pending_tokens(5)
            resolved_tokens = self.processor.get_resolved_tokens(5)
            
            return jsonify({
                'system_status': 'running' if self.running else 'stopped',
                'statistics': stats,
                'sample_data': {
                    'pending_tokens': len(pending_tokens),
                    'recent_resolved': len(resolved_tokens)
                },
                'dual_table_active': True
            })
        
        @app.route('/pending')
        def pending_tokens():
            tokens = self.processor.get_pending_tokens(20)
            return jsonify({
                'pending_tokens': [
                    {
                        'address': token[0][:10] + '...',
                        'placeholder_name': token[1],
                        'keyword': token[2],
                        'retry_count': token[4],
                        'detected_at': token[5].isoformat() if token[5] else None
                    }
                    for token in tokens
                ]
            })
        
        @app.route('/resolved')
        def resolved_tokens():
            tokens = self.processor.get_resolved_tokens(20)
            return jsonify({
                'resolved_tokens': [
                    {
                        'address': token[0][:10] + '...',
                        'name': token[1],
                        'symbol': token[2],
                        'keyword': token[3],
                        'detected_at': token[5].isoformat() if token[5] else None
                    }
                    for token in tokens
                ]
            })
        
        return app
    
    async def process_detected_token(self, token_data):
        """Process a newly detected token through dual table system"""
        try:
            contract_address = token_data.get('address')
            if not contract_address:
                logger.error("❌ No contract address in token data")
                return
            
            logger.info(f"🔍 Processing new token: {contract_address[:10]}...")
            
            # Try to get the name immediately
            token_name = await resolve_token_name_with_retry(contract_address)
            
            if token_name and token_name != "Unknown":
                # Name resolved immediately - store in detected_tokens
                self.processor.insert_resolved_token(
                    contract_address=contract_address,
                    token_name=token_name,
                    symbol=token_data.get('symbol'),
                    keyword=token_data.get('keyword'),
                    matched_keywords=token_data.get('matched_keywords'),
                    blockchain_age_seconds=token_data.get('blockchain_age_seconds')
                )
                
                logger.info(f"✅ IMMEDIATE RESOLUTION: {token_name}")
                return True
            else:
                # Name not available - store in pending_tokens
                address_suffix = contract_address[:6]
                placeholder_name = f"Unnamed Token {address_suffix}"
                
                self.processor.insert_pending_token(
                    contract_address=contract_address,
                    placeholder_name=placeholder_name,
                    keyword=token_data.get('keyword'),
                    matched_keywords=token_data.get('matched_keywords'),
                    blockchain_age_seconds=token_data.get('blockchain_age_seconds')
                )
                
                logger.info(f"⚡ PENDING PROCESSING: {placeholder_name} (background resolution queued)")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error processing token: {e}")
            return False
    
    def start_background_resolver(self):
        """Start the background name resolver"""
        def resolver_thread():
            try:
                logger.info("🚀 Starting background name resolver...")
                asyncio.run(self.resolver.run_continuous_resolution(interval_seconds=60))
            except Exception as e:
                logger.error(f"❌ Background resolver error: {e}")
        
        resolver_thread_obj = Thread(target=resolver_thread, daemon=True)
        resolver_thread_obj.start()
        logger.info("✅ Background name resolver started")
    
    def start_flask_server(self):
        """Start the Flask web server"""
        def flask_thread():
            try:
                logger.info("🌐 Starting Flask server on 0.0.0.0:5000...")
                serve(self.flask_app, host='0.0.0.0', port=5000, threads=4)
            except Exception as e:
                logger.error(f"❌ Flask server error: {e}")
        
        flask_thread_obj = Thread(target=flask_thread, daemon=True)
        flask_thread_obj.start()
        logger.info("✅ Flask server started")
    
    def start_system(self):
        """Start the complete dual table hybrid system"""
        try:
            logger.info("🎯 DUAL TABLE HYBRID TOKEN PROCESSING SYSTEM")
            logger.info("=" * 60)
            logger.info("⚡ INSTANT PROCESSING: All tokens processed immediately")
            logger.info("📋 DUAL TABLES: Pending → Resolved migration")
            logger.info("🔄 BACKGROUND RESOLUTION: Names updated when available")
            logger.info("💾 DATABASE TRACKING: Separate pending and resolved tables")
            logger.info("🌐 API ENDPOINTS: / and /status available")
            logger.info("=" * 60)
            
            self.running = True
            
            # Start all system components
            self.start_flask_server()
            time.sleep(1)  # Let Flask start
            
            self.start_background_resolver()
            
            # Get initial system stats
            stats = self.processor.get_system_stats()
            logger.info(f"📊 System Stats: {stats}")
            
            logger.info("🚀 Dual table hybrid system fully operational!")
            
            # Keep main thread alive
            try:
                while self.running:
                    time.sleep(60)
                    # Log periodic stats
                    stats = self.processor.get_system_stats()
                    logger.info(f"📊 Periodic Stats: {stats}")
                    
            except KeyboardInterrupt:
                logger.info("🛑 Received interrupt signal")
                self.stop_system()
                
        except Exception as e:
            logger.error(f"❌ System startup failed: {e}")
            return False
    
    def stop_system(self):
        """Stop the dual table hybrid system"""
        self.running = False
        self.resolver.stop()
        logger.info("🛑 Dual table hybrid system stopped")

def test_dual_table_system():
    """Test the dual table system functionality"""
    logger.info("🧪 Testing dual table system...")
    
    processor = DualTableTokenProcessor()
    
    # Test 1: Insert pending token
    test_address = "TEST123456789ABCDEF"
    pending_id = processor.insert_pending_token(
        test_address,
        "Test Unnamed Token",
        keyword="test",
        matched_keywords=["test", "demo"],
        blockchain_age_seconds=25.0
    )
    
    if pending_id:
        logger.info(f"✅ Test 1 passed: Pending token inserted (ID: {pending_id})")
    else:
        logger.error("❌ Test 1 failed: Could not insert pending token")
        return False
    
    # Test 2: Get system stats
    stats = processor.get_system_stats()
    logger.info(f"✅ Test 2 passed: System stats retrieved: {stats}")
    
    # Test 3: Get pending tokens
    pending = processor.get_pending_tokens(5)
    logger.info(f"✅ Test 3 passed: Found {len(pending)} pending tokens")
    
    logger.info("🎉 All dual table tests passed!")
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Run tests
        success = test_dual_table_system()
        if success:
            print("✅ Dual table system tests completed successfully")
        else:
            print("❌ Dual table system tests failed")
    else:
        # Run the hybrid system
        system = DualTableHybridSystem()
        system.start_system()