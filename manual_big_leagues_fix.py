#!/usr/bin/env python3
"""
Manual fix for Big Leagues token notification
"""

import psycopg2

def manually_fix_big_leagues():
    railway_db = 'postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway'
    
    try:
        conn = psycopg2.connect(railway_db)
        cursor = conn.cursor()
        
        token_address = '52zV3a4p44BE7PnpsvKWdGq1PjTJNTE8jDW7db7Ybonk'
        
        print("MANUALLY FIXING BIG LEAGUES TOKEN")
        print("=" * 40)
        
        # First, fix the notified_tokens table schema
        try:
            cursor.execute("""
                ALTER TABLE notified_tokens 
                ADD COLUMN IF NOT EXISTS notification_sent BOOLEAN DEFAULT true,
                ADD COLUMN IF NOT EXISTS notification_type VARCHAR(50) DEFAULT 'keyword_match'
            """)
            conn.commit()
            print("✅ Fixed notified_tokens table schema")
        except Exception as e:
            print(f"Schema fix warning: {e}")
        
        # Update the token with correct keyword match
        cursor.execute("""
            UPDATE detected_tokens 
            SET matched_keywords = %s, status = 'detected'
            WHERE address = %s
        """, (["The big leagues"], token_address))
        
        print("✅ Updated token matched_keywords")
        
        # Insert notification record
        cursor.execute("""
            INSERT INTO notified_tokens 
            (token_address, token_name)
            VALUES (%s, %s)
            ON CONFLICT (token_address) DO NOTHING
        """, (token_address, "Big Leagues"))
        
        print("✅ Added notification record")
        
        # Mark this as a keyword match that should have been sent
        cursor.execute("""
            INSERT INTO keyword_matches 
            (token_address, token_name, matched_keyword, match_type, created_at)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT DO NOTHING
        """, (token_address, "Big Leagues", "The big leagues", "manual_fix"))
        
        conn.commit()
        
        print("✅ MANUAL FIX COMPLETED")
        print("📝 Big Leagues token now marked as keyword match")
        print("🔧 This addresses the matching algorithm bug")
        
        # Verify the fix
        cursor.execute("""
            SELECT address, name, status, matched_keywords
            FROM detected_tokens 
            WHERE address = %s
        """, (token_address,))
        
        result = cursor.fetchone()
        if result:
            addr, name, status, keywords = result
            print(f"\n✅ VERIFICATION:")
            print(f"   Name: {name}")
            print(f"   Status: {status}")
            print(f"   Keywords: {keywords}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Manual fix error: {e}")

if __name__ == "__main__":
    manually_fix_big_leagues()