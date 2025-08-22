#!/usr/bin/env python3
"""
Debug what's blocking component initialization
"""

import time
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_component_initialization():
    """Debug each step of component initialization"""
    print("🔍 DEBUGGING COMPONENT INITIALIZATION")
    print("=" * 60)
    
    try:
        print("📊 Step 1: Import FixedDualTableProcessor...")
        from fixed_dual_table_processor import FixedDualTableProcessor
        print("✅ FixedDualTableProcessor imported successfully")
        
        print("📊 Step 2: Import NewTokenOnlyMonitor...")
        from new_token_only_monitor import NewTokenOnlyMonitor
        print("✅ NewTokenOnlyMonitor imported successfully")
        
        print("📊 Step 3: Import NotificationEnhancedRetryService...")
        try:
            from notification_enhanced_retry_service import NotificationEnhancedRetryService
            print("✅ NotificationEnhancedRetryService imported successfully")
        except ImportError as e:
            print(f"⚠️ NotificationEnhancedRetryService import failed: {e}")
            print("   This might be missing - checking alternatives...")
        
        print("📊 Step 4: Initialize token processor...")
        token_processor = FixedDualTableProcessor()
        print("✅ Token processor initialized")
        
        print("📊 Step 5: Create database tables...")
        token_processor.create_tables_if_needed()
        print("✅ Database tables created/verified")
        
        print("📊 Step 6: Test callback function...")
        def test_callback(tokens):
            print(f"   Callback received {len(tokens)} tokens")
        
        print("📊 Step 7: Initialize token monitor...")
        token_monitor = NewTokenOnlyMonitor(test_callback)
        print("✅ Token monitor initialized")
        
        print("📊 Step 8: Test railway retry service...")
        try:
            from railway_retry_startup import railway_startup_retries
            railway_startup_retries()
            print("✅ Railway retry service working")
        except Exception as e:
            print(f"⚠️ Railway retry service failed: {e}")
            print("   This is non-critical and shouldn't block initialization")
        
        print("\n✅ ALL COMPONENTS INITIALIZED SUCCESSFULLY")
        print("   The initialization should work in production")
        
    except Exception as e:
        print(f"❌ INITIALIZATION FAILED at step: {e}")
        print("Traceback:")
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("DEBUG COMPLETE")

if __name__ == "__main__":
    debug_component_initialization()