#!/usr/bin/env python3
"""
Automatic Keyword Synchronization Service
Ensures real-time synchronization between file-based keywords and database
"""

import os
import time
import logging
import threading
from typing import Set, List
from keyword_sync_manager import KeywordSyncManager
from config_manager import ConfigManager

logger = logging.getLogger(__name__)

class AutoKeywordSync:
    """Automatic synchronization service for keywords"""
    
    def __init__(self, sync_interval: int = 30):
        self.sync_interval = sync_interval
        
        # Check for DATABASE_URL before initializing KeywordSyncManager
        if not os.getenv('DATABASE_URL'):
            raise ValueError("DATABASE_URL environment variable not found")
            
        self.sync_manager = KeywordSyncManager()
        self.config_manager = ConfigManager()
        self.running = False
        self.sync_thread = None
        self.last_file_keywords = set()
        self.last_db_keywords = set()
        
    def start(self):
        """Start the automatic synchronization service"""
        if self.running:
            logger.warning("Auto sync service already running")
            return
            
        self.running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
        logger.info(f"🔄 Auto keyword sync started (interval: {self.sync_interval}s)")
        
    def stop(self):
        """Stop the automatic synchronization service"""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=5)
        logger.info("⏹️ Auto keyword sync stopped")
        
    def _sync_loop(self):
        """Main synchronization loop"""
        logger.info("🔄 Auto sync loop started")
        
        # Initialize tables
        try:
            self.sync_manager.create_required_tables()
        except Exception as e:
            logger.error(f"Failed to initialize sync tables: {e}")
            return
            
        while self.running:
            try:
                self._perform_sync_check()
                time.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                time.sleep(5)  # Brief pause before retrying
                
    def _perform_sync_check(self):
        """Perform a single synchronization check"""
        try:
            # Get current state from both sources
            file_keywords = set(self.config_manager.list_keywords())
            db_keywords = self.sync_manager.get_active_keywords()
            
            # Check if there are differences
            if file_keywords != db_keywords:
                logger.info(f"🔍 Keyword differences detected:")
                logger.info(f"   File keywords: {len(file_keywords)}")
                logger.info(f"   DB keywords: {len(db_keywords)}")
                
                # Use database as source of truth and sync file if needed
                missing_in_file = db_keywords - file_keywords
                extra_in_file = file_keywords - db_keywords
                
                if missing_in_file:
                    logger.info(f"   Missing in file: {list(missing_in_file)[:5]}{'...' if len(missing_in_file) > 5 else ''}")
                    
                if extra_in_file:
                    logger.info(f"   Extra in file: {list(extra_in_file)[:5]}{'...' if len(extra_in_file) > 5 else ''}")
                
                # Sync file to match database (database is source of truth)
                self._sync_file_to_database(db_keywords)
                
            # Update tracking
            self.last_file_keywords = file_keywords
            self.last_db_keywords = db_keywords
            
        except Exception as e:
            logger.error(f"Error performing sync check: {e}")
            
    def _sync_file_to_database(self, db_keywords: Set[str]):
        """Sync file keywords to match database keywords"""
        try:
            # Update file to match database
            success = self.config_manager.save_watchlist(list(db_keywords))
            if success:
                logger.info(f"✅ File synchronized with database ({len(db_keywords)} keywords)")
            else:
                logger.error("❌ Failed to sync file with database")
        except Exception as e:
            logger.error(f"Error syncing file to database: {e}")
            
    def force_sync_from_database(self):
        """Force immediate synchronization from database to all other sources"""
        try:
            logger.info("🔄 Forcing sync from database...")
            db_keywords = self.sync_manager.get_active_keywords()
            self._sync_file_to_database(db_keywords)
            logger.info("✅ Force sync completed")
        except Exception as e:
            logger.error(f"Error in force sync: {e}")
            
    def get_sync_status(self) -> dict:
        """Get current synchronization status"""
        try:
            file_keywords = set(self.config_manager.list_keywords())
            db_keywords = self.sync_manager.get_active_keywords()
            
            return {
                'running': self.running,
                'file_keyword_count': len(file_keywords),
                'db_keyword_count': len(db_keywords),
                'in_sync': file_keywords == db_keywords,
                'differences': {
                    'missing_in_file': list(db_keywords - file_keywords),
                    'extra_in_file': list(file_keywords - db_keywords)
                },
                'last_sync_interval': self.sync_interval
            }
        except Exception as e:
            return {
                'running': self.running,
                'error': str(e)
            }

# Global instance for easy access (with environment fallback)
try:
    auto_sync_service = AutoKeywordSync()
except Exception as e:
    logger.warning(f"Auto sync service disabled due to environment issue: {e}")
    auto_sync_service = None

def start_auto_sync(interval: int = 30):
    """Start the automatic keyword synchronization service"""
    if auto_sync_service is None:
        logger.warning("Auto sync service not available - DATABASE_URL required")
        return False
    auto_sync_service.sync_interval = interval
    auto_sync_service.start()
    return True
    
def stop_auto_sync():
    """Stop the automatic keyword synchronization service"""
    if auto_sync_service is None:
        return False
    auto_sync_service.stop()
    return True
    
def force_sync_now():
    """Force immediate synchronization"""
    if auto_sync_service is None:
        logger.warning("Force sync not available - DATABASE_URL required")
        return False
    auto_sync_service.force_sync_from_database()
    return True
    
def get_auto_sync_status():
    """Get current auto sync status"""
    if auto_sync_service is None:
        return {
            'running': False,
            'error': 'Auto sync service not available - DATABASE_URL environment variable required',
            'file_keyword_count': 0,
            'db_keyword_count': 0,
            'in_sync': False
        }
    return auto_sync_service.get_sync_status()

if __name__ == "__main__":
    # Test the auto sync service
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    print("Starting auto sync service for testing...")
    start_auto_sync(10)  # 10 second interval for testing
    
    try:
        time.sleep(60)  # Run for 1 minute
    except KeyboardInterrupt:
        print("Stopping auto sync service...")
        
    stop_auto_sync()
    print("Auto sync service stopped.")