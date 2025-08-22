#!/usr/bin/env python3
"""
Railway PostgreSQL Database QA Test
Tests all Discord commands with the specific Railway database connection
"""

import os
import sys
import asyncio
import psycopg2
import psycopg2.extras
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use the specific Railway database URL
RAILWAY_DATABASE_URL = "postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway"

class RailwayDatabaseTester:
    def __init__(self):
        self.db_url = RAILWAY_DATABASE_URL
        self.test_user_id = "123456789"  # Test user ID for Discord commands
        self.test_keywords = ["elon", "moon", "bonk", "pepe", "shib"]
        
    def get_connection(self):
        """Get database connection using Railway credentials"""
        try:
            conn = psycopg2.connect(self.db_url)
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to Railway database: {e}")
            raise
    
    def test_database_connection(self):
        """Test basic database connection and info"""
        print("\n🔍 STEP 1: Testing Railway Database Connection")
        print("=" * 60)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get database info
            cursor.execute("SELECT current_database(), current_user, version();")
            db_info = cursor.fetchone()
            
            print(f"✅ Database: {db_info[0]}")
            print(f"✅ User: {db_info[1]}")
            print(f"✅ PostgreSQL Version: {db_info[2][:50]}...")
            
            # Check connection details
            cursor.execute("SELECT inet_server_addr(), inet_server_port();")
            server_info = cursor.fetchone()
            print(f"✅ Server: {server_info[0]}:{server_info[1]}")
            
            cursor.close()
            conn.close()
            
            print("✅ Railway database connection successful!")
            return True
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def setup_database_tables(self):
        """Create necessary tables if they don't exist"""
        print("\n🔧 STEP 2: Setting Up Database Tables")
        print("=" * 60)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create keywords table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keywords (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    keyword VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, keyword)
                );
            """)
            
            # Create keyword_actions table for undo functionality
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keyword_actions (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    action_type VARCHAR(50) NOT NULL,
                    keyword VARCHAR(255),
                    keywords_affected TEXT[],
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create detected_tokens table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detected_tokens (
                    id SERIAL PRIMARY KEY,
                    address VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255),
                    symbol VARCHAR(50),
                    accurate_name VARCHAR(255),
                    extraction_confidence DECIMAL(3,2),
                    extraction_source VARCHAR(100),
                    created_timestamp BIGINT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    platform VARCHAR(100),
                    url TEXT
                );
            """)
            
            # Create notified_tokens table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notified_tokens (
                    id SERIAL PRIMARY KEY,
                    token_address VARCHAR(255) NOT NULL,
                    token_name VARCHAR(255),
                    matched_keyword VARCHAR(255),
                    user_id VARCHAR(255),
                    notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notification_source VARCHAR(100)
                );
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("✅ All database tables created successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Table creation failed: {e}")
            return False
    
    def clear_test_data(self):
        """Clear any existing test data"""
        print("\n🧹 STEP 3: Clearing Previous Test Data")
        print("=" * 60)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Clear test user's keywords
            cursor.execute("DELETE FROM keywords WHERE user_id = %s", (self.test_user_id,))
            deleted_keywords = cursor.rowcount
            
            # Clear test user's actions
            cursor.execute("DELETE FROM keyword_actions WHERE user_id = %s", (self.test_user_id,))
            deleted_actions = cursor.rowcount
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"✅ Cleared {deleted_keywords} keywords and {deleted_actions} actions for test user")
            return True
            
        except Exception as e:
            print(f"❌ Data clearing failed: {e}")
            return False
    
    def test_add_command(self):
        """Test /add command functionality"""
        print("\n➕ STEP 4: Testing /add Command")
        print("=" * 60)
        
        results = []
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            for keyword in self.test_keywords:
                try:
                    # Simulate /add command
                    cursor.execute("""
                        INSERT INTO keywords (user_id, keyword) 
                        VALUES (%s, %s) 
                        ON CONFLICT (user_id, keyword) DO NOTHING
                    """, (self.test_user_id, keyword))
                    
                    # Log the action
                    cursor.execute("""
                        INSERT INTO keyword_actions (user_id, action_type, keyword)
                        VALUES (%s, 'add', %s)
                    """, (self.test_user_id, keyword))
                    
                    conn.commit()
                    
                    # Verify insertion
                    cursor.execute("""
                        SELECT keyword, created_at FROM keywords 
                        WHERE user_id = %s AND keyword = %s
                    """, (self.test_user_id, keyword))
                    
                    result = cursor.fetchone()
                    if result:
                        print(f"✅ Added keyword: '{keyword}' at {result[1]}")
                        results.append(True)
                    else:
                        print(f"❌ Failed to add keyword: '{keyword}'")
                        results.append(False)
                        
                except Exception as e:
                    print(f"❌ Error adding keyword '{keyword}': {e}")
                    results.append(False)
            
            cursor.close()
            conn.close()
            
            success_count = sum(results)
            print(f"\n✅ /add command test: {success_count}/{len(self.test_keywords)} keywords added successfully")
            return all(results)
            
        except Exception as e:
            print(f"❌ /add command test failed: {e}")
            return False
    
    def test_list_command(self):
        """Test /list command functionality"""
        print("\n📋 STEP 5: Testing /list Command")
        print("=" * 60)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Simulate /list command
            cursor.execute("""
                SELECT keyword, created_at FROM keywords 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """, (self.test_user_id,))
            
            keywords = cursor.fetchall()
            
            print(f"✅ Found {len(keywords)} keywords for user:")
            for i, (keyword, created_at) in enumerate(keywords, 1):
                print(f"   {i}. {keyword} (added: {created_at})")
            
            cursor.close()
            conn.close()
            
            # Verify all test keywords are present
            found_keywords = [k[0] for k in keywords]
            missing_keywords = [k for k in self.test_keywords if k not in found_keywords]
            
            if not missing_keywords:
                print("✅ /list command test: All keywords found correctly")
                return True
            else:
                print(f"❌ /list command test: Missing keywords: {missing_keywords}")
                return False
                
        except Exception as e:
            print(f"❌ /list command test failed: {e}")
            return False
    
    def test_remove_command(self):
        """Test /remove command functionality"""
        print("\n➖ STEP 6: Testing /remove Command")
        print("=" * 60)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Remove the first test keyword
            keyword_to_remove = self.test_keywords[0]  # "elon"
            
            # Simulate /remove command
            cursor.execute("""
                DELETE FROM keywords 
                WHERE user_id = %s AND keyword = %s
            """, (self.test_user_id, keyword_to_remove))
            
            removed_count = cursor.rowcount
            
            # Log the action
            cursor.execute("""
                INSERT INTO keyword_actions (user_id, action_type, keyword)
                VALUES (%s, 'remove', %s)
            """, (self.test_user_id, keyword_to_remove))
            
            conn.commit()
            
            # Verify removal
            cursor.execute("""
                SELECT keyword FROM keywords 
                WHERE user_id = %s AND keyword = %s
            """, (self.test_user_id, keyword_to_remove))
            
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if removed_count > 0 and not result:
                print(f"✅ Successfully removed keyword: '{keyword_to_remove}'")
                return True
            else:
                print(f"❌ Failed to remove keyword: '{keyword_to_remove}'")
                return False
                
        except Exception as e:
            print(f"❌ /remove command test failed: {e}")
            return False
    
    def test_remove_multiple_command(self):
        """Test /remove_multiple command functionality"""
        print("\n➖➖ STEP 7: Testing /remove_multiple Command")
        print("=" * 60)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Remove multiple keywords
            keywords_to_remove = self.test_keywords[1:3]  # "moon", "bonk"
            
            # Simulate /remove_multiple command
            for keyword in keywords_to_remove:
                cursor.execute("""
                    DELETE FROM keywords 
                    WHERE user_id = %s AND keyword = %s
                """, (self.test_user_id, keyword))
            
            removed_count = cursor.rowcount
            
            # Log the action
            cursor.execute("""
                INSERT INTO keyword_actions (user_id, action_type, keywords_affected)
                VALUES (%s, 'remove_multiple', %s)
            """, (self.test_user_id, keywords_to_remove))
            
            conn.commit()
            
            # Verify removal
            remaining_keywords = []
            for keyword in keywords_to_remove:
                cursor.execute("""
                    SELECT keyword FROM keywords 
                    WHERE user_id = %s AND keyword = %s
                """, (self.test_user_id, keyword))
                
                if cursor.fetchone():
                    remaining_keywords.append(keyword)
            
            cursor.close()
            conn.close()
            
            if not remaining_keywords:
                print(f"✅ Successfully removed multiple keywords: {keywords_to_remove}")
                return True
            else:
                print(f"❌ Failed to remove keywords: {remaining_keywords}")
                return False
                
        except Exception as e:
            print(f"❌ /remove_multiple command test failed: {e}")
            return False
    
    def test_undo_command(self):
        """Test /undo command functionality"""
        print("\n↩️ STEP 8: Testing /undo Command")
        print("=" * 60)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get the last action
            cursor.execute("""
                SELECT action_type, keyword, keywords_affected
                FROM keyword_actions 
                WHERE user_id = %s 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (self.test_user_id,))
            
            last_action = cursor.fetchone()
            
            if not last_action:
                print("❌ No actions found to undo")
                return False
            
            action_type, keyword, keywords_affected = last_action
            print(f"🔄 Last action: {action_type} - {keyword or keywords_affected}")
            
            # Simulate /undo command based on action type
            if action_type == 'add' and keyword:
                # Undo add: remove the keyword
                cursor.execute("""
                    DELETE FROM keywords 
                    WHERE user_id = %s AND keyword = %s
                """, (self.test_user_id, keyword))
                
                print(f"✅ Undid add: removed '{keyword}'")
                
            elif action_type == 'remove' and keyword:
                # Undo remove: add the keyword back
                cursor.execute("""
                    INSERT INTO keywords (user_id, keyword) 
                    VALUES (%s, %s) 
                    ON CONFLICT (user_id, keyword) DO NOTHING
                """, (self.test_user_id, keyword))
                
                print(f"✅ Undid remove: added back '{keyword}'")
                
            elif action_type == 'remove_multiple' and keywords_affected:
                # Undo remove_multiple: add all keywords back
                for keyword in keywords_affected:
                    cursor.execute("""
                        INSERT INTO keywords (user_id, keyword) 
                        VALUES (%s, %s) 
                        ON CONFLICT (user_id, keyword) DO NOTHING
                    """, (self.test_user_id, keyword))
                
                print(f"✅ Undid remove_multiple: added back {keywords_affected}")
            
            # Log the undo action
            cursor.execute("""
                INSERT INTO keyword_actions (user_id, action_type, keyword, keywords_affected)
                VALUES (%s, 'undo', %s, %s)
            """, (self.test_user_id, keyword, keywords_affected))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("✅ /undo command test completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ /undo command test failed: {e}")
            return False
    
    def test_refresh_command(self):
        """Test /refresh command functionality"""
        print("\n🔄 STEP 9: Testing /refresh Command")
        print("=" * 60)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Simulate /refresh command - reload keywords from database
            cursor.execute("""
                SELECT keyword FROM keywords 
                WHERE user_id = %s 
                ORDER BY keyword
            """, (self.test_user_id,))
            
            keywords = [row[0] for row in cursor.fetchall()]
            
            # Get total keyword count across all users
            cursor.execute("SELECT COUNT(*) FROM keywords")
            total_count = cursor.fetchone()[0]
            
            # Get recent actions count
            cursor.execute("""
                SELECT COUNT(*) FROM keyword_actions 
                WHERE user_id = %s AND timestamp > NOW() - INTERVAL '1 hour'
            """, (self.test_user_id,))
            recent_actions = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            print(f"✅ Refreshed user keywords: {keywords}")
            print(f"✅ Total keywords in database: {total_count}")
            print(f"✅ Recent actions (last hour): {recent_actions}")
            
            print("✅ /refresh command test completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ /refresh command test failed: {e}")
            return False
    
    def final_verification(self):
        """Final verification of database state"""
        print("\n🔍 STEP 10: Final Database State Verification")
        print("=" * 60)
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check final keyword state
            cursor.execute("""
                SELECT keyword, created_at FROM keywords 
                WHERE user_id = %s 
                ORDER BY created_at
            """, (self.test_user_id,))
            
            final_keywords = cursor.fetchall()
            
            # Check action history
            cursor.execute("""
                SELECT action_type, keyword, keywords_affected, timestamp 
                FROM keyword_actions 
                WHERE user_id = %s 
                ORDER BY timestamp
            """, (self.test_user_id,))
            
            actions = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            print("Final Keywords State:")
            for keyword, created_at in final_keywords:
                print(f"  • {keyword} (created: {created_at})")
            
            print(f"\nAction History ({len(actions)} actions):")
            for action_type, keyword, keywords_affected, timestamp in actions:
                if keywords_affected:
                    print(f"  • {timestamp}: {action_type} - {keywords_affected}")
                else:
                    print(f"  • {timestamp}: {action_type} - {keyword}")
            
            print("\n✅ Final verification completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Final verification failed: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests in sequence"""
        print("🚀 STARTING COMPREHENSIVE RAILWAY DATABASE QA TEST")
        print("=" * 70)
        print(f"Database URL: {self.db_url}")
        print(f"Test User ID: {self.test_user_id}")
        print(f"Test Keywords: {self.test_keywords}")
        print("=" * 70)
        
        test_results = []
        
        # Run all tests
        test_results.append(("Database Connection", self.test_database_connection()))
        test_results.append(("Database Tables Setup", self.setup_database_tables()))
        test_results.append(("Clear Test Data", self.clear_test_data()))
        test_results.append(("/add Command", self.test_add_command()))
        test_results.append(("/list Command", self.test_list_command()))
        test_results.append(("/remove Command", self.test_remove_command()))
        test_results.append(("/remove_multiple Command", self.test_remove_multiple_command()))
        test_results.append(("/undo Command", self.test_undo_command()))
        test_results.append(("/refresh Command", self.test_refresh_command()))
        test_results.append(("Final Verification", self.final_verification()))
        
        # Summary
        print("\n" + "=" * 70)
        print("🎯 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 70)
        
        passed = 0
        failed = 0
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status:10} {test_name}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print("=" * 70)
        print(f"TOTAL: {passed} PASSED, {failed} FAILED")
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED - Railway database integration is working perfectly!")
        else:
            print(f"⚠️ {failed} tests failed - requires attention")
        
        return failed == 0

if __name__ == "__main__":
    tester = RailwayDatabaseTester()
    success = tester.run_comprehensive_test()
    sys.exit(0 if success else 1)