#!/usr/bin/env python3
"""
Railway Environment Checker
Checks exactly what environment Railway deployment sees
"""

import os
import sys
import logging
sys.path.append('.')

def check_railway_environment():
    """Check Railway deployment environment"""
    
    print('🚂 RAILWAY ENVIRONMENT CHECK')
    print('=' * 40)
    
    # Check all environment variables
    print('1. ENVIRONMENT VARIABLES:')
    env_vars = ['DATABASE_URL', 'POSTGRES_URL', 'POSTGRESQL_URL', 'DB_URL']
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f'   {var}: {value[:40]}...{value[-15:]}')
        else:
            print(f'   {var}: NOT SET')
    
    # Check Railway-specific variables
    print('\n2. RAILWAY VARIABLES:')
    railway_vars = ['RAILWAY_ENVIRONMENT', 'RAILWAY_PROJECT_ID', 'RAILWAY_SERVICE_ID']
    for var in railway_vars:
        value = os.getenv(var)
        print(f'   {var}: {value or "NOT SET"}')
    
    # Test database connection
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print(f'\n3. DATABASE CONNECTION TEST:')
        try:
            import psycopg2
            conn = psycopg2.connect(database_url, connect_timeout=5)
            cursor = conn.cursor()
            
            cursor.execute('SELECT current_database(), current_user, version()')
            db_info = cursor.fetchone()
            print(f'   ✅ Connected to: {db_info[0]} as {db_info[1]}')
            
            cursor.execute("SELECT COUNT(*) FROM keywords WHERE user_id = 'System'")
            count = cursor.fetchone()[0]
            print(f'   ✅ System keywords: {count}')
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f'   ❌ Connection failed: {e}')
    else:
        print('\n3. DATABASE CONNECTION TEST:')
        print('   ❌ No DATABASE_URL environment variable')
    
    # Test ConfigManager
    print('\n4. CONFIGMANAGER TEST:')
    try:
        from config_manager import ConfigManager
        config = ConfigManager()
        keywords = config.list_keywords(user_id='System')
        print(f'   ✅ ConfigManager returned {len(keywords)} keywords')
        print(f'   ✅ Keywords: {keywords}')
    except Exception as e:
        print(f'   ❌ ConfigManager failed: {e}')
    
    print('\n🎯 ENVIRONMENT CHECK COMPLETE')

if __name__ == '__main__':
    check_railway_environment()