#!/usr/bin/env python3
"""
Comprehensive Debug for Discord /list Command
Simulates exact Discord bot workflow to identify failure point
"""

import os
import sys
import logging
import traceback
sys.path.append('.')

# Set up logging exactly like Discord bot
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_list_command():
    """Debug the exact /list command workflow"""
    
    print('🔍 DISCORD /LIST COMMAND DEBUG')
    print('=' * 50)
    
    # Step 1: Check environment
    print('\n1. ENVIRONMENT CHECK:')
    database_url = os.getenv('DATABASE_URL')
    print(f'   DATABASE_URL present: {bool(database_url)}')
    
    if database_url:
        if 'railway.internal' in database_url:
            print('   ✅ Using Railway internal URL (deployment)')
        elif 'proxy.rlwy.net' in database_url:
            print('   🔗 Using Railway external URL (testing)')
        else:
            print('   ❓ Using other database URL')
        print(f'   URL format: {database_url[:40]}...{database_url[-20:]}')
    else:
        print('   ❌ No DATABASE_URL found')
        return
    
    # Step 2: Test ConfigManager import and initialization
    print('\n2. CONFIGMANAGER INITIALIZATION:')
    try:
        from config_manager import ConfigManager
        print('   ✅ ConfigManager imported successfully')
        
        config_manager = ConfigManager()
        print('   ✅ ConfigManager initialized successfully')
        
    except Exception as e:
        print(f'   ❌ ConfigManager initialization failed: {e}')
        traceback.print_exc()
        return
    
    # Step 3: Test database connection directly
    print('\n3. DIRECT DATABASE CONNECTION TEST:')
    try:
        import psycopg2
        
        # Test with timeout like Discord bot
        conn = psycopg2.connect(
            database_url,
            connect_timeout=10,
            application_name='debug_list_command'
        )
        cursor = conn.cursor()
        
        # Test basic connection
        cursor.execute('SELECT current_database(), current_user')
        db_info = cursor.fetchone()
        print(f'   ✅ Connected to database: {db_info[0]} as {db_info[1]}')
        
        # Test keywords table exists
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'keywords'")
        table_exists = cursor.fetchone()
        if table_exists:
            print('   ✅ Keywords table exists')
        else:
            print('   ❌ Keywords table does not exist')
            cursor.close()
            conn.close()
            return
        
        # Test System keywords count
        cursor.execute("SELECT COUNT(*) FROM keywords WHERE user_id = 'System'")
        system_count = cursor.fetchone()[0]
        print(f'   📊 System keywords in database: {system_count}')
        
        if system_count > 0:
            # Get actual keywords
            cursor.execute("SELECT keyword FROM keywords WHERE user_id = 'System' ORDER BY keyword")
            keywords = [row[0] for row in cursor.fetchall()]
            print(f'   📝 System keywords: {keywords}')
        else:
            print('   ❌ No System keywords found in database')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'   ❌ Direct database connection failed: {e}')
        traceback.print_exc()
        return
    
    # Step 4: Test ConfigManager.list_keywords() exactly like Discord bot
    print('\n4. CONFIGMANAGER.LIST_KEYWORDS() TEST:')
    try:
        # This is the exact call Discord bot makes
        keywords = config_manager.list_keywords(user_id="System")
        
        print(f'   📊 ConfigManager returned: {len(keywords)} keywords')
        print(f'   🔍 Keywords type: {type(keywords)}')
        print(f'   📝 Keywords: {keywords}')
        
        # Test the exact Discord bot logic
        if keywords is None:
            print('   ❌ Keywords is None - Discord would show error')
        elif not isinstance(keywords, list):
            print(f'   ❌ Keywords not a list: {type(keywords)} - Discord would show error')
        elif len(keywords) == 0:
            print('   ❌ Empty keyword list - Discord shows "No monitoring configured"')
        else:
            print(f'   ✅ SUCCESS: Discord would show {len(keywords)} keywords')
            
    except Exception as e:
        print(f'   ❌ ConfigManager.list_keywords() failed: {e}')
        traceback.print_exc()
        
    # Step 5: Test all user_ids in database
    print('\n5. ALL USER_IDS IN DATABASE:')
    try:
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id, COUNT(*) FROM keywords GROUP BY user_id ORDER BY user_id")
        user_counts = cursor.fetchall()
        
        for user_id, count in user_counts:
            print(f'   {user_id}: {count} keywords')
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'   ❌ User enumeration failed: {e}')
    
    print('\n🎯 DEBUG COMPLETE')
    print('   Check results above to identify the failure point')

if __name__ == '__main__':
    debug_list_command()