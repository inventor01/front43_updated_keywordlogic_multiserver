#!/usr/bin/env python3
"""
Railway Database Connection Test
Tests the exact DATABASE_URL that Railway deployment uses
"""

import psycopg2
import os
import sys
sys.path.append('.')
from config_manager import ConfigManager

def test_railway_database():
    """Test Railway database connection and keyword retrieval"""
    
    print('🚂 RAILWAY DATABASE CONNECTION TEST')
    print('=' * 45)
    
    # Use Railway internal database URL
    database_url = os.getenv('DATABASE_URL')
    print(f'DATABASE_URL present: {bool(database_url)}')
    
    if database_url:
        if 'railway.internal' in database_url:
            print('✅ Using Railway internal URL (deployment environment)')
        elif 'proxy.rlwy.net' in database_url:
            print('🔗 Using Railway external URL (testing environment)')
        else:
            print('❓ Using other database URL')
    
    # Test ConfigManager (Discord bot method)
    print('\n📊 Testing ConfigManager.list_keywords():')
    try:
        config = ConfigManager()
        
        # Test System keywords (what Discord /list uses)
        system_keywords = config.list_keywords(user_id='System')
        print(f'✅ System keywords found: {len(system_keywords)}')
        print(f'✅ Keywords: {system_keywords}')
        
        if len(system_keywords) == 0:
            print('❌ PROBLEM: No System keywords found')
            print('❌ This explains why Discord /list shows empty')
        else:
            print('✅ SUCCESS: Keywords exist, Discord /list should work')
            
    except Exception as e:
        print(f'❌ ConfigManager error: {e}')
        print('❌ This explains why Discord /list fails')
    
    # Test direct database connection
    print('\n🔗 Testing direct database connection:')
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Basic connection test
        cursor.execute('SELECT current_database(), version()')
        db_info = cursor.fetchone()
        print(f'✅ Connected to: {db_info[0]}')
        
        # Check System keywords
        cursor.execute('SELECT COUNT(*) FROM keywords WHERE user_id = %s', ('System',))
        count = cursor.fetchone()[0]
        print(f'✅ System keywords in DB: {count}')
        
        if count > 0:
            cursor.execute('SELECT keyword FROM keywords WHERE user_id = %s ORDER BY keyword', ('System',))
            keywords = [row[0] for row in cursor.fetchall()]
            print(f'✅ Keyword list: {keywords}')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'❌ Database connection error: {e}')
    
    print('\n🎯 TEST COMPLETE')

if __name__ == '__main__':
    test_railway_database()