#!/usr/bin/env python3
"""
Test script to verify keyword synchronization system works properly
"""

import logging
from keyword_sync_manager import KeywordSyncManager
from config_manager import ConfigManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_keyword_synchronization():
    """Test the keyword synchronization system"""
    
    print("🧪 TESTING KEYWORD SYNCHRONIZATION SYSTEM")
    print("=" * 50)
    
    try:
        # Initialize managers
        sync_manager = KeywordSyncManager()
        config_manager = ConfigManager()
        
        # Initialize tables
        print("1. Initializing database tables...")
        sync_manager.create_required_tables()
        print("✅ Tables initialized")
        
        # Check current status  
        print("\n2. Checking current keyword status...")
        active_keywords = sync_manager.get_active_keywords()
        print(f"✅ Active keywords: {len(active_keywords)}")
        
        # Verify coin keyword is deactivated
        coin_active = 'coin' in active_keywords
        print(f"✅ 'coin' keyword active: {coin_active}")
        
        # Get sync status
        print("\n3. Getting synchronization status...")
        status = sync_manager.get_sync_status()
        print(f"✅ Active: {status['active_keywords']}")
        print(f"✅ Inactive: {status['inactive_keywords']}")
        print(f"✅ Sync healthy: {status['sync_healthy']}")
        
        # Test file sync  
        print("\n4. Testing file synchronization...")
        file_keywords = set(config_manager.list_keywords())
        db_keywords = active_keywords
        
        print(f"✅ File keywords: {len(file_keywords)}")
        print(f"✅ DB keywords: {len(db_keywords)}")
        print(f"✅ Files in sync: {file_keywords == db_keywords}")
        
        if file_keywords != db_keywords:
            missing_in_file = db_keywords - file_keywords
            extra_in_file = file_keywords - db_keywords
            
            if missing_in_file:
                print(f"⚠️ Missing in file: {list(missing_in_file)[:5]}")
            if extra_in_file:
                print(f"⚠️ Extra in file: {list(extra_in_file)[:5]}")
        
        print("\n" + "=" * 50)
        print("🎯 SYNCHRONIZATION TEST COMPLETE")
        
        # Summary
        if coin_active:
            print("❌ ISSUE: 'coin' keyword is still active!")
            return False
        else:
            print("✅ SUCCESS: 'coin' keyword is properly deactivated")
            print(f"✅ System monitoring {len(active_keywords)} keywords")
            return True
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_keyword_synchronization()
    exit(0 if success else 1)