#!/usr/bin/env python3
"""
Railway Duplicate Notification Fix
Problem: Same coin being sent multiple times due to multiple notification paths
Solution: Centralized deduplication system with Railway-specific fixes
"""

import logging
import time
import os
import psycopg2
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class RailwayDedupFix:
    """Centralized deduplication to fix Railway duplicate notifications"""
    
    def __init__(self, alchemy_server):
        self.server = alchemy_server
        self.startup_logging()
        
    def startup_logging(self):
        """Add Railway-specific startup logging as requested in debug checklist"""
        database_url = os.getenv('DATABASE_URL')
        
        # Check Railway environment
        railway_env = os.getenv('RAILWAY_ENVIRONMENT', 'Unknown')
        repl_id = os.getenv('REPL_ID', 'Not in Replit')
        pid = os.getpid()
        
        logger.info(f"🚂 RAILWAY STARTUP: Environment={railway_env}, PID={pid}")
        logger.info(f"🗄️ DATABASE: Connected to: {database_url[:50]}..." if database_url else "❌ No DATABASE_URL")
        
        # Verify database table structure
        if database_url:
            try:
                conn = psycopg2.connect(database_url)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'notified_tokens'
                    ORDER BY ordinal_position
                """)
                
                columns = cursor.fetchall()
                logger.info(f"✅ NOTIFIED_TOKENS TABLE: {len(columns)} columns found")
                for col_name, col_type in columns:
                    logger.info(f"   - {col_name}: {col_type}")
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                logger.error(f"❌ DATABASE VERIFICATION FAILED: {e}")

    def check_and_mark_notified(self, token_address: str, token_name: str, keyword: str, notification_source: str) -> bool:
        """
        Centralized check-and-mark for Railway deduplication
        Returns True if notification should be sent, False if already notified
        """
        try:
            # First check memory (fastest)
            if hasattr(self.server, 'notified_token_addresses') and token_address in self.server.notified_token_addresses:
                logger.debug(f"🔄 DEDUP: {token_address} already in memory - BLOCKED")
                return False
            
            # Check database (persistent across restarts)
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                logger.warning("⚠️ DEDUP: No database connection - allowing notification")
                return True
                
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Check if already notified
            cursor.execute("""
                SELECT COUNT(*) FROM notified_tokens 
                WHERE token_address = %s
            """, (token_address,))
            
            count = cursor.fetchone()[0]
            
            if count > 0:
                logger.info(f"🚫 DEDUP: {token_name} ({token_address[:8]}...) already notified - BLOCKED")
                cursor.close()
                conn.close()
                return False
            
            # Not yet notified - record it immediately using INSERT with conflict handling
            # Use INSERT ... WHERE NOT EXISTS to handle missing unique constraint
            cursor.execute("""
                INSERT INTO notified_tokens (token_address, token_name, notification_type, notified_at)
                SELECT %s, %s, %s, NOW()
                WHERE NOT EXISTS (
                    SELECT 1 FROM notified_tokens WHERE token_address = %s
                )
            """, (token_address, token_name, f"{notification_source}:{keyword}", token_address))
            
            rows_inserted = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            if rows_inserted > 0:
                # Successfully inserted - add to memory cache
                if hasattr(self.server, 'notified_token_addresses'):
                    self.server.notified_token_addresses.add(token_address)
                
                logger.info(f"✅ DEDUP: {token_name} ({token_address[:8]}...) marked as notified - ALLOWING")
                return True
            else:
                # Conflict occurred (another process already inserted)
                logger.info(f"🚫 DEDUP: {token_name} ({token_address[:8]}...) conflict detected - BLOCKED")
                return False
                
        except Exception as e:
            logger.error(f"❌ DEDUP ERROR: {e} - ALLOWING notification (fail-safe)")
            return True

    def log_notification_attempt(self, token_address: str, token_name: str, keyword: str, allowed: bool):
        """Debug logging for notification attempts as requested"""
        pid = os.getpid()
        status = "ALLOWED" if allowed else "BLOCKED"
        logger.info(f"[DEBUG] Processing {token_address[:8]}... ({token_name}) → {keyword} in PID {pid}: {status}")

def integrate_railway_dedup_fix(alchemy_server):
    """Integrate Railway dedup fix into existing server"""
    try:
        dedup_fix = RailwayDedupFix(alchemy_server)
        alchemy_server.railway_dedup = dedup_fix
        
        # Replace the existing notification check function
        original_check_func = getattr(alchemy_server, 'is_token_already_notified', None)
        
        def centralized_notification_check(token_address, token_name="", keyword="", source="unknown"):
            """Centralized replacement for all notification checks"""
            return not dedup_fix.check_and_mark_notified(token_address, token_name, keyword, source)
        
        # Override the check function
        alchemy_server.is_token_already_notified = centralized_notification_check
        
        logger.info("🎯 RAILWAY DEDUP FIX: Centralized notification system active")
        return True
        
    except Exception as e:
        logger.error(f"❌ RAILWAY DEDUP INTEGRATION FAILED: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTING RAILWAY DEDUP FIX")
    
    # Mock test
    class MockServer:
        def __init__(self):
            self.notified_token_addresses = set()
    
    mock_server = MockServer()
    dedup_fix = RailwayDedupFix(mock_server)
    
    # Test address
    test_address = "CvcdAYeVy5qYvomDNHteJBcz4ZXgHLwMg2W9KFZZbonk"
    
    # First check should allow
    allowed1 = dedup_fix.check_and_mark_notified(test_address, "Test Token", "test", "unit_test")
    print(f"First notification: {allowed1}")
    
    # Second check should block
    allowed2 = dedup_fix.check_and_mark_notified(test_address, "Test Token", "test", "unit_test") 
    print(f"Duplicate notification: {allowed2}")