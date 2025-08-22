import os
import psycopg2

try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    cur.execute("SELECT keyword FROM keywords ORDER BY keyword;")
    keywords = [row[0] for row in cur.fetchall()]
    print(f"Total keywords: {len(keywords)}")
    
    # Check for mage-related keywords
    mage_keywords = [k for k in keywords if 'mage' in k.lower()]
    if mage_keywords:
        print(f"MAGE-related keywords found: {mage_keywords}")
    else:
        print("❌ NO 'mage' keyword found in your list!")
    
    # Show first 10 keywords for reference
    print(f"\nFirst 10 keywords: {keywords[:10]}")
    
    conn.close()
except Exception as e:
    print(f"Database error: {e}")
