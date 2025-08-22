#!/usr/bin/env python3
"""
Diagnose why tokens aren't reaching detected_tokens table
"""

import time
import logging
from railway_optimized_server import RailwayOptimizedServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_token_processing_flow():
    """Test the complete token processing flow"""
    print("🔍 DIAGNOSING TOKEN PROCESSING FLOW")
    print("=" * 60)
    
    # Create server instance
    server = RailwayOptimizedServer()
    
    # Wait for components to initialize
    print("⏳ Waiting for components to initialize...")
    max_wait = 30
    wait_time = 0
    
    while not server.components_ready and wait_time < max_wait:
        time.sleep(1)
        wait_time += 1
        print(f"   Waiting... {wait_time}s")
    
    if not server.components_ready:
        print("❌ ISSUE: Components not ready after 30 seconds")
        print("   This could cause token processing to be skipped")
        return
    
    print("✅ Components are ready!")
    
    # Test token processing directly
    test_token = {
        'address': 'TEST123456789',
        'name': 'Test Token',
        'symbol': 'TEST'
    }
    
    print(f"\n📝 Testing direct token processing with: {test_token['name']}")
    
    try:
        server.handle_new_token([test_token])
        print("✅ Token processing completed without errors")
        
        # Check if it was stored
        from fixed_dual_table_processor import FixedDualTableProcessor
        processor = FixedDualTableProcessor()
        
        # Check recent entries
        import psycopg2
        import os
        
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT address, name FROM detected_tokens 
            WHERE address = %s OR name = %s
        """, (test_token['address'], test_token['name']))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            print(f"✅ SUCCESS: Token found in database - {result[1]}")
        else:
            print("❌ ISSUE: Token not found in detected_tokens table")
            print("   Token processing is working but storage is failing")
        
    except Exception as e:
        print(f"❌ ERROR in token processing: {e}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")

if __name__ == "__main__":
    test_token_processing_flow()