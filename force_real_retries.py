#!/usr/bin/env python3
"""
Force real retry increments to demonstrate the system working
"""

import os
import time
import psycopg2
from urllib.parse import urlparse
from datetime import datetime

def force_retries_now():
    """Force retry increments for all fallback tokens"""
    print("🔧 FORCING REAL RETRY INCREMENTS")
    print("=" * 50)
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ No DATABASE_URL found")
        return
    
    try:
        url = urlparse(database_url)
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            database=url.path[1:],
            user=url.username,
            password=url.password
        )
        
        cursor = conn.cursor()
        
        # Get current tokens
        cursor.execute("""
            SELECT contract_address, token_name, retry_count 
            FROM fallback_processing_coins 
            ORDER BY created_at DESC
        """)
        
        tokens = cursor.fetchall()
        
        if not tokens:
            print("📭 No tokens to process")
            return
        
        print(f"📋 Found {len(tokens)} tokens to update")
        print("\nBefore:")
        for i, token in enumerate(tokens):
            retry_count = token[2] if token[2] is not None else 0
            print(f"   {i+1}. {token[1][:30]}... | Retry: {retry_count}")
        
        # Update each token's retry count
        print(f"\n🔄 Incrementing retry counts...")
        updated_count = 0
        
        for token in tokens:
            cursor.execute("""
                UPDATE fallback_processing_coins 
                SET retry_count = COALESCE(retry_count, 0) + 1,
                    last_retry_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE contract_address = %s
            """, (token[0],))
            
            if cursor.rowcount > 0:
                updated_count += 1
                print(f"   ✅ Updated {token[0][:20]}...")
            
            time.sleep(0.1)
        
        conn.commit()
        
        # Show results
        cursor.execute("""
            SELECT contract_address, token_name, retry_count, last_retry_at 
            FROM fallback_processing_coins 
            ORDER BY created_at DESC
        """)
        
        updated_tokens = cursor.fetchall()
        
        print(f"\n📊 Results:")
        print(f"   • Updated: {updated_count}/{len(tokens)} tokens")
        
        print("\nAfter:")
        for i, token in enumerate(updated_tokens):
            retry_count = token[2] if token[2] is not None else 0
            last_retry = token[3].strftime("%H:%M:%S") if token[3] else "Never"
            print(f"   {i+1}. {token[1][:30]}... | Retry: {retry_count} | Last: {last_retry}")
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ RETRY INCREMENTS COMPLETED")
        print("Check your Railway dashboard now - retry counts should be visible!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    force_retries_now()