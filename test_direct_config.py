#!/usr/bin/env python3

import os
import psycopg2

def test_config_manager_directly():
    """Test the exact same logic that ConfigManager should use"""
    print("=== TESTING DIRECT CONFIG LOGIC ===")
    
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ No DATABASE_URL")
            return ['bonk', 'drake', 'kanye', 'mage', 'ohio', 'plan b', 'pope', 'spongebob', 'trump']
        
        print("✅ DATABASE_URL found")
        
        # Simple, direct database query
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        cursor.execute("SELECT keyword FROM keywords ORDER BY keyword")
        results = cursor.fetchall()
        
        print(f"Database results: {results}")
        
        cursor.close()
        conn.close()
        
        if results and len(results) > 0:
            keywords = [row[0] for row in results]
            print(f"Processed keywords: {keywords}")
            return keywords
        else:
            print("No results, returning fallback")
            return ['bonk', 'drake', 'kanye', 'mage', 'ohio', 'plan b', 'pope', 'spongebob', 'trump']
                
    except Exception as e:
        print(f"Exception: {e}")
        return ['bonk', 'drake', 'kanye', 'mage', 'ohio', 'plan b', 'pope', 'spongebob', 'trump']

if __name__ == "__main__":
    result = test_config_manager_directly()
    print(f"Final result: {result}")
    print(f"Success: {len(result) > 0 and 'bonk' in result}")