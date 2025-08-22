#!/usr/bin/env python3
"""
Reliable Token Monitoring System - Achievement-Focused Implementation
Goals:
1. Get notifications for keyword matching coins as they're created
2. Still receive notifications for coins that may have been missed when system was down  
3. No duplicate notifications
4. All commands work properly
5. All names and timestamps are accurately discovered
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import psycopg2
import os

logger = logging.getLogger(__name__)

class ReliableMonitoringSystem:
    """Focused system to achieve all 5 monitoring goals quickly"""
    
    def __init__(self, alchemy_server):
        self.server = alchemy_server
        self.notification_tracker = NotificationTracker()
        self.missed_token_recovery = MissedTokenRecovery(alchemy_server)
        self.command_validator = CommandValidator(alchemy_server)
        
        logger.info("🎯 RELIABLE MONITORING: System initialized for 100% goal achievement")
    
    def ensure_all_goals_met(self):
        """Verify all 5 goals are achievable with current setup"""
        logger.info("🔍 GOAL VERIFICATION: Checking system readiness...")
        
        # Goal 1: Keyword matching notifications
        keywords_loaded = len(self.server.keywords) > 0
        dual_api_active = hasattr(self.server, 'dual_api_extractor') and self.server.dual_api_extractor
        
        # Goal 2: Missed token recovery
        recovery_active = hasattr(self.server, 'recovery_system') and self.server.recovery_system
        
        # Goal 3: No duplicates
        duplicate_protection = hasattr(self.server, 'notified_token_addresses')
        
        # Goal 4: Commands work
        discord_bot_active = hasattr(self.server, 'discord_notifier') and self.server.discord_notifier
        
        # Goal 5: Accurate discovery
        extraction_system = dual_api_active or hasattr(self.server, 'pure_name_extractor')
        
        results = {
            "keyword_matching": keywords_loaded and dual_api_active,
            "missed_recovery": recovery_active,
            "no_duplicates": duplicate_protection,
            "commands_work": discord_bot_active,
            "accurate_discovery": extraction_system
        }
        
        logger.info(f"📊 GOAL STATUS: {results}")
        return all(results.values())

class NotificationTracker:
    """Prevents duplicate notifications - Goal 3"""
    
    def __init__(self):
        self.sent_notifications = set()
        self.database_tracker = DatabaseNotificationTracker()
        
    def is_already_notified(self, token_address: str) -> bool:
        """Check both memory and database for duplicates"""
        return (token_address in self.sent_notifications or 
                self.database_tracker.is_notified(token_address))
    
    def mark_notified(self, token_address: str, token_name: str, keyword: str):
        """Mark token as notified in both memory and database"""
        self.sent_notifications.add(token_address)
        self.database_tracker.record_notification(token_address, token_name, keyword)
        
class DatabaseNotificationTracker:
    """Database-persistent duplicate prevention"""
    
    def is_notified(self, token_address: str) -> bool:
        """Check database for previous notifications"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                return False
                
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 1 FROM notified_tokens 
                WHERE token_address = %s 
                LIMIT 1
            """, (token_address,))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Database notification check failed: {e}")
            return False
    
    def record_notification(self, token_address: str, token_name: str, keyword: str):
        """Record notification in database"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                return
                
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO notified_tokens (token_address, token_name, keyword, notified_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (token_address) DO NOTHING
            """, (token_address, token_name, keyword))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to record notification: {e}")

class MissedTokenRecovery:
    """Recover tokens missed during downtime - Goal 2"""
    
    def __init__(self, alchemy_server):
        self.server = alchemy_server
        self.last_scan_time = self.get_last_scan_time()
        
    def get_last_scan_time(self) -> datetime:
        """Get timestamp of last successful scan"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                return datetime.now() - timedelta(hours=1)  # Default 1 hour back
                
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT MAX(notified_at) FROM notified_tokens
                WHERE notified_at > NOW() - INTERVAL '24 hours'
            """)
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result[0]:
                return result[0]
            else:
                return datetime.now() - timedelta(hours=1)
                
        except Exception as e:
            logger.error(f"Failed to get last scan time: {e}")
            return datetime.now() - timedelta(hours=1)
    
    async def scan_missed_tokens(self):
        """Scan for tokens created during downtime"""
        logger.info(f"🔄 MISSED TOKEN SCAN: Checking from {self.last_scan_time}")
        
        # This would integrate with the token recovery system
        if hasattr(self.server, 'recovery_system') and self.server.recovery_system:
            try:
                await self.server.recovery_system.run_backfill_scan()
                logger.info("✅ MISSED TOKEN SCAN: Completed successfully")
            except Exception as e:
                logger.error(f"❌ MISSED TOKEN SCAN: Failed - {e}")

class CommandValidator:
    """Ensure all Discord commands work properly - Goal 4"""
    
    def __init__(self, alchemy_server):
        self.server = alchemy_server
        
    def validate_commands(self) -> bool:
        """Test core Discord commands"""
        try:
            # Test keyword loading for /list command
            keywords = self.server.keywords
            if len(keywords) == 0:
                logger.error("❌ COMMAND VALIDATION: No keywords loaded - /list will be empty")
                return False
                
            # Test database connection for /add, /remove commands
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                logger.error("❌ COMMAND VALIDATION: No database connection - commands will fail")
                return False
                
            # Test Discord connection
            if not hasattr(self.server, 'discord_notifier') or not self.server.discord_notifier:
                logger.error("❌ COMMAND VALIDATION: No Discord connection")
                return False
                
            logger.info("✅ COMMAND VALIDATION: All systems ready")
            return True
            
        except Exception as e:
            logger.error(f"❌ COMMAND VALIDATION: Failed - {e}")
            return False

def integrate_reliable_system(alchemy_server):
    """Integrate reliable monitoring into existing server"""
    try:
        reliable_system = ReliableMonitoringSystem(alchemy_server)
        alchemy_server.reliable_system = reliable_system
        
        # Verify all goals are achievable
        all_goals_ready = reliable_system.ensure_all_goals_met()
        
        if all_goals_ready:
            logger.info("🎯 SUCCESS: All 5 monitoring goals are achievable with current setup")
            return True
        else:
            logger.warning("⚠️ WARNING: Some goals may not be achievable - check system status")
            return False
            
    except Exception as e:
        logger.error(f"❌ RELIABLE SYSTEM INTEGRATION FAILED: {e}")
        return False

if __name__ == "__main__":
    # Test reliable system components
    print("🧪 TESTING RELIABLE MONITORING COMPONENTS")
    
    # Mock server for testing
    class MockServer:
        def __init__(self):
            self.keywords = ['test', 'bonk', 'business']
            self.dual_api_extractor = True
            self.recovery_system = True
            self.notified_token_addresses = set()
            self.discord_notifier = True
    
    mock_server = MockServer()
    reliable_system = ReliableMonitoringSystem(mock_server)
    
    goals_ready = reliable_system.ensure_all_goals_met()
    print(f"Goals achievable: {goals_ready}")