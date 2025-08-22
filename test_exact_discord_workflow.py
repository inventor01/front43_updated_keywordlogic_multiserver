#!/usr/bin/env python3
"""
Test Exact Discord Bot Workflow
Replicates the exact code path that Discord /list command takes
"""

import os
import sys
import logging
sys.path.append('.')

# Set up logging exactly like Discord bot
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def simulate_discord_list_command():
    """Simulate the exact Discord /list command execution"""
    
    print('🎮 SIMULATING DISCORD /LIST COMMAND EXECUTION')
    print('=' * 55)
    
    # Import exactly like Discord bot
    try:
        from config_manager import ConfigManager
        logger.info("✅ ConfigManager imported")
    except Exception as e:
        logger.error(f"❌ ConfigManager import failed: {e}")
        return
    
    # Initialize exactly like Discord bot
    try:
        config_manager = ConfigManager()
        logger.info("✅ ConfigManager initialized")
    except Exception as e:
        logger.error(f"❌ ConfigManager initialization failed: {e}")
        return
    
    # Environment check exactly like Discord bot
    database_url = os.getenv('DATABASE_URL')
    logger.info(f"🎮 /list command: using System for global keywords")
    logger.info(f"🔧 DATABASE_URL present: {bool(database_url)}")
    if database_url:
        logger.info(f"🔧 DATABASE_URL format: {database_url[:30]}...{database_url[-20:]}")
    
    # Get keywords exactly like Discord bot
    try:
        keywords = config_manager.list_keywords(user_id="System")
        logger.info(f"📊 Retrieved keywords for System: {len(keywords)} total")
        logger.info(f"🔍 System keywords: {keywords}")
        logger.info(f"🔧 Keywords type: {type(keywords)}")
    except Exception as e:
        logger.error(f"❌ ConfigManager.list_keywords() failed: {e}")
        keywords = []
    
    # Handle None or invalid results exactly like Discord bot
    if keywords is None:
        logger.warning("⚠️ Keywords is None")
        keywords = []
    elif not isinstance(keywords, list):
        logger.warning(f"⚠️ Keywords is not a list: {type(keywords)}")
        keywords = []
    
    # Test Discord bot decision logic
    if len(keywords) == 0:
        print("\n❌ DISCORD BOT RESULT: 'No monitoring configured'")
        print("   This explains why you see empty message")
        
        # Additional debugging for empty result
        database_url = os.getenv('DATABASE_URL')
        logger.error("❌ CRITICAL: No keywords found for System user")
        logger.error(f"❌ DATABASE_URL present: {bool(database_url)}")
        if database_url:
            logger.error(f"❌ DATABASE_URL host: {'railway.internal' if 'railway.internal' in database_url else 'external'}")
        logger.error(f"❌ Keywords type: {type(keywords)}, value: {keywords}")
        
        # Test direct database connection like Discord bot does
        try:
            import psycopg2
            conn = psycopg2.connect(database_url, connect_timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM keywords WHERE user_id = 'System'")
            count = cursor.fetchone()[0]
            logger.error(f"❌ Direct query result: {count} System keywords")
            cursor.close()
            conn.close()
            print(f"   Direct database query found: {count} System keywords")
        except Exception as db_error:
            logger.error(f"❌ Direct database test failed: {db_error}")
            print(f"   Direct database test failed: {db_error}")
            
    else:
        print(f"\n✅ DISCORD BOT RESULT: 'Showing {len(keywords)} keywords'")
        print(f"   Keywords: {keywords}")
    
    print("\n🎯 SIMULATION COMPLETE")

if __name__ == '__main__':
    simulate_discord_list_command()