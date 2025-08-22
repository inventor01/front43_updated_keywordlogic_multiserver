#!/usr/bin/env python3
"""
Debug script to check Discord bot environment on Railway
This helps diagnose why /add works but /list doesn't
"""

import os
import logging
from config_manager import ConfigManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment():
    """Check all environment variables and database connectivity"""
    print("🔍 DISCORD BOT ENVIRONMENT DIAGNOSTIC")
    print("=" * 50)
    
    # Check critical environment variables
    discord_token = os.getenv('DISCORD_TOKEN')
    database_url = os.getenv('DATABASE_URL')
    
    print(f"🔑 DISCORD_TOKEN: {'✅ SET' if discord_token else '❌ MISSING'}")
    print(f"🗄️ DATABASE_URL: {'✅ SET' if database_url else '❌ MISSING'}")
    
    if discord_token:
        print(f"   Token preview: {discord_token[:10]}...")
    
    if database_url:
        print(f"   Database host: {database_url.split('@')[1].split('/')[0] if '@' in database_url else 'Unknown'}")
    
    # Test ConfigManager functionality
    print("\n🔧 TESTING CONFIG MANAGER:")
    try:
        config = ConfigManager()
        print("   ✅ ConfigManager initialized")
        
        # Test database connection
        test_user = "environment_test_user"
        test_keyword = "environment_test"
        
        # Test add
        success, reason = config.add_keyword(test_keyword, user_id=test_user)
        print(f"   Add test: {'✅' if success else '❌'} {reason}")
        
        # Test list
        keywords = config.list_keywords(user_id=test_user)
        print(f"   List test: {'✅' if keywords else '❌'} Found {len(keywords) if keywords else 0} keywords")
        
        if success and keywords and test_keyword in keywords:
            print("   🎯 Add->List workflow: ✅ WORKING")
            # Clean up
            config.remove_keyword(test_keyword, user_id=test_user)
        else:
            print("   🎯 Add->List workflow: ❌ BROKEN")
            
    except Exception as e:
        print(f"   ❌ ConfigManager failed: {e}")
    
    # Environment recommendations
    print("\n💡 RECOMMENDATIONS:")
    if not discord_token:
        print("   1. Add DISCORD_TOKEN to Railway environment variables")
    if not database_url:
        print("   2. Add DATABASE_URL to Railway environment variables")
        print("   3. This is why /add succeeds but /list fails - no database persistence")
    
    if discord_token and database_url:
        print("   ✅ Environment looks good - Discord bot should work properly")

if __name__ == "__main__":
    check_environment()