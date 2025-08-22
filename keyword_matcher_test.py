#!/usr/bin/env python3
"""
Test keyword matching for Big Leagues token
"""

import psycopg2

def test_keyword_matching():
    railway_db = 'postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway'
    
    try:
        conn = psycopg2.connect(railway_db)
        cursor = conn.cursor()
        
        # Get active keywords
        cursor.execute("SELECT keyword FROM keywords WHERE status = 'active'")
        keywords = [row[0] for row in cursor.fetchall()]
        
        token_name = "Big Leagues"
        token_name_lower = token_name.lower()
        
        print(f"🔍 TESTING KEYWORD MATCHING")
        print(f"Token name: '{token_name}'")
        print(f"Active keywords: {len(keywords)}")
        print("=" * 50)
        
        matches = []
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Test different matching strategies
            if keyword_lower in token_name_lower:
                matches.append(f"'{keyword}' found in '{token_name}'")
            elif token_name_lower in keyword_lower:
                matches.append(f"'{token_name}' found in '{keyword}'")
            elif any(word in keyword_lower for word in token_name_lower.split()):
                matches.append(f"Word match: '{keyword}' <-> '{token_name}'")
        
        if matches:
            print(f"✅ MATCHES FOUND ({len(matches)}):")
            for match in matches:
                print(f"   - {match}")
            print(f"\n💡 This token SHOULD have been notified")
        else:
            print(f"❌ NO MATCHES FOUND")
            print(f"💡 This explains why the token was not sent")
            
            # Show some example keywords for reference
            print(f"\nSample keywords (first 10):")
            for keyword in keywords[:10]:
                print(f"   - {keyword}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_keyword_matching()