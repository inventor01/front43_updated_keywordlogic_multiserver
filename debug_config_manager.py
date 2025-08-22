#!/usr/bin/env python3

import os
import psycopg2
from typing import List

def debug_config_manager():
    """Debug the ConfigManager issue step by step"""
    
    print("=== DEBUGGING CONFIGMANAGER STEP BY STEP ===")
    
    # Step 1: Check DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    print(f"Step 1: DATABASE_URL exists: {database_url is not None}")
    
    if not database_url:
        print("❌ ERROR: No DATABASE_URL found")
        return []
    
    try:
        # Step 2: Connect to database
        print("Step 2: Connecting to PostgreSQL...")
        conn = psycopg2.connect(database_url)
        print("✅ Connection successful")
        
        # Step 3: Create cursor
        cursor = conn.cursor()
        print("✅ Cursor created")
        
        # Step 4: Execute query
        print("Step 4: Executing query...")
        cursor.execute("SELECT keyword FROM keywords ORDER BY keyword")
        print("✅ Query executed")
        
        # Step 5: Fetch results
        print("Step 5: Fetching results...")
        results = cursor.fetchall()
        print(f"✅ Raw results: {results}")
        print(f"✅ Result count: {len(results)}")
        
        # Step 6: Process results
        if results:
            keywords = [row[0] for row in results]
            print(f"✅ Processed keywords: {keywords}")
            print(f"✅ Final count: {len(keywords)}")
        else:
            keywords = []
            print("❌ No results found")
        
        # Step 7: Cleanup
        cursor.close()
        conn.close()
        print("✅ Database connection closed")
        
        return keywords
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    result = debug_config_manager()
    print(f"\n=== FINAL RESULT ===")
    print(f"Keywords: {result}")
    print(f"Count: {len(result)}")
    print(f"Success: {len(result) > 0}")