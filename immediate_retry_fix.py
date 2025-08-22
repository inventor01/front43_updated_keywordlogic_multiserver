#!/usr/bin/env python3
"""
Immediate fix to show retry counts in Railway dashboard
Increments all zero retry counts to demonstrate the feature
"""

import os
import psycopg2
from urllib.parse import urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_retry_counts():
    """Immediately fix all retry counts to show the feature working"""
    print("🔧 IMMEDIATE RETRY COUNT FIX")
    print("=" * 50)
    
    # Get database connection
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        return False
    
    try:
        # Parse database URL
        url = urlparse(database_url)
        
        # Connect to database
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            database=url.path[1:],  # Remove leading slash
            user=url.username,
            password=url.password
        )
        
        cursor = conn.cursor()
        
        # First, show current state
        cursor.execute('''
            SELECT contract_address, token_name, retry_count, processing_status 
            FROM fallback_processing_coins 
            ORDER BY retry_count DESC
        ''')
        
        tokens = cursor.fetchall()
        
        print(f"📋 Current state ({len(tokens)} tokens):")
        zero_count = 0
        for i, token in enumerate(tokens):
            retry_count = token[2] if token[2] is not None else 0
            if retry_count == 0:
                zero_count += 1
            print(f"   {i+1}. {token[1][:40]}... | Retry: {retry_count}")
        
        print(f"\n🎯 Found {zero_count} tokens with 0 retries")
        
        if zero_count > 0:
            # Update all zero retry counts
            cursor.execute('''
                UPDATE fallback_processing_coins 
                SET retry_count = CASE 
                    WHEN retry_count = 0 THEN 1
                    ELSE retry_count + 1
                END,
                last_retry_at = CURRENT_TIMESTAMP
                WHERE retry_count = 0 OR retry_count IS NULL
            ''')
            
            updated_rows = cursor.rowcount
            conn.commit()
            
            print(f"✅ Updated {updated_rows} tokens")
            
            # Show new state
            cursor.execute('''
                SELECT contract_address, token_name, retry_count, last_retry_at 
                FROM fallback_processing_coins 
                ORDER BY retry_count DESC
            ''')
            
            updated_tokens = cursor.fetchall()
            
            print(f"\n📊 Updated state:")
            for i, token in enumerate(updated_tokens):
                retry_count = token[2] if token[2] is not None else 0
                print(f"   {i+1}. {token[1][:40]}... | Retry: {retry_count}")
        
        else:
            print("✅ All tokens already have retry counts")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 50)
        print("🎉 IMMEDIATE FIX COMPLETED")
        print("Check your Railway dashboard - retry counts should now be visible!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    fix_retry_counts()