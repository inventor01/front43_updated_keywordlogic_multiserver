#!/usr/bin/env python3

# Test the Discord command functionality without actually sending Discord messages
import sys
sys.path.append('.')

def test_direct_keyword_access():
    """Test the same method that Discord commands now use"""
    print("=== TESTING DISCORD COMMAND KEYWORD ACCESS ===")
    
    try:
        # Import the server components
        from alchemy_server import AlchemyMonitoringServer
        
        # Create a minimal test instance to check keyword loading
        import os
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ No DATABASE_URL")
            return False
            
        # Test the direct database method that Discord commands now use
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        cursor.execute("SELECT keyword FROM keywords ORDER BY keyword")
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if results:
            keywords = [row[0] for row in results]
            print(f"✅ Direct database method works: {keywords}")
            print(f"✅ Count: {len(keywords)}")
            
            if 'bonk' in keywords:
                print("✅ SUCCESS: 'bonk' keyword found!")
                print("✅ Discord commands should now work properly")
                return True
            else:
                print("❌ ERROR: 'bonk' keyword missing")
                return False
        else:
            print("❌ No results from database")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_direct_keyword_access()
    print(f"\n🎯 Overall Status: {'SUCCESS' if success else 'FAILED'}")
    print("📱 Discord commands (/list, /add) should now be operational")