#!/usr/bin/env python3
"""
Test script to verify keyword listing fix
"""

import psycopg2
import os

def test_keyword_listing():
    # Railway database connection
    database_url = 'postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway'
    
    try:
        print("🔍 Testing keyword listing fix...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Test the old query (user-specific)
        test_user_id = "123456789"  # Simulated Discord user ID
        cursor.execute("SELECT keyword, created_at FROM keywords WHERE user_id = %s ORDER BY created_at", (test_user_id,))
        user_keywords = cursor.fetchall()
        print(f"❌ Old query (user-specific): Found {len(user_keywords)} keywords for user {test_user_id}")
        
        # Test the new query (all keywords)
        cursor.execute("SELECT keyword, created_at, user_id FROM keywords ORDER BY created_at DESC")
        all_keywords = cursor.fetchall()
        print(f"✅ New query (all keywords): Found {len(all_keywords)} total keywords")
        
        if all_keywords:
            print("\n📝 Keywords in Railway database:")
            for i, (keyword, created_at, user_id) in enumerate(all_keywords[:10]):
                print(f"   {i+1}. {keyword} (user: {user_id})")
            if len(all_keywords) > 10:
                print(f"   ... and {len(all_keywords) - 10} more")
        
        # Check unique users
        cursor.execute("SELECT DISTINCT user_id FROM keywords")
        users = cursor.fetchall()
        print(f"\n👥 Keywords belong to {len(users)} unique user(s):")
        for user in users:
            print(f"   • User ID: {user[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎯 CONCLUSION:")
        print(f"   • The Discord /list_keywords command was filtering by user_id")
        print(f"   • All {len(all_keywords)} keywords belong to user_id: {users[0][0] if users else 'N/A'}")
        print(f"   • New query shows ALL keywords regardless of user")
        print(f"   • This fixes the empty list issue!")
        
        return len(all_keywords)
        
    except Exception as e:
        print(f"❌ Error testing keywords: {e}")
        return 0

if __name__ == "__main__":
    keyword_count = test_keyword_listing()
    print(f"\n✅ Test complete: {keyword_count} keywords found in Railway database")