#!/usr/bin/env python3
"""
Check if retries are actually happening in Railway deployment
"""

import os
import time
import psycopg2
from urllib.parse import urlparse

def check_railway_retries():
    """Check current retry status in Railway deployment"""
    print("🔍 CHECKING ACTUAL RAILWAY RETRY STATUS")
    print("=" * 60)
    
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
        
        # Check fallback_processing_coins table
        cursor.execute("""
            SELECT 
                contract_address,
                token_name,
                retry_count,
                last_retry_at,
                processing_status,
                created_at,
                (EXTRACT(EPOCH FROM (NOW() - created_at))/60)::int as age_minutes
            FROM fallback_processing_coins 
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        tokens = cursor.fetchall()
        
        if not tokens:
            print("📭 No tokens in fallback_processing_coins table")
        else:
            print(f"📋 Found {len(tokens)} fallback tokens:")
            print()
            print("Token Name                  | Retry | Last Retry           | Age(min) | Status")
            print("-" * 80)
            
            zero_retries = 0
            for token in tokens:
                name = token[1][:25] + "..." if len(token[1]) > 25 else token[1]
                retry_count = token[2] if token[2] is not None else 0
                last_retry = token[3].strftime("%m-%d %H:%M") if token[3] else "Never"
                age_min = token[6]
                status = token[4]
                
                if retry_count == 0:
                    zero_retries += 1
                
                print(f"{name:<27} | {retry_count:^5} | {last_retry:<16} | {age_min:^8} | {status}")
            
            print(f"\n📊 Summary:")
            print(f"   • Total tokens: {len(tokens)}")
            print(f"   • Zero retries: {zero_retries}")
            print(f"   • With retries: {len(tokens) - zero_retries}")
            
            if zero_retries > 0:
                print(f"\n⚠️  Problem: {zero_retries} tokens still have 0 retries")
                print("   This means the background service isn't running properly")
            else:
                print(f"\n✅ All tokens have retry attempts")
        
        # Check if background service is working by looking at recent retry timestamps
        cursor.execute("""
            SELECT COUNT(*) as recent_retries
            FROM fallback_processing_coins 
            WHERE last_retry_at > NOW() - INTERVAL '10 minutes'
        """)
        
        recent_retries = cursor.fetchone()[0]
        
        print(f"\n🕒 Recent activity (last 10 minutes):")
        print(f"   • Tokens with recent retries: {recent_retries}")
        
        if recent_retries == 0:
            print("   ⚠️  No recent retry activity - background service may not be running")
        else:
            print("   ✅ Background service is active")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking retries: {e}")

if __name__ == "__main__":
    check_railway_retries()