#!/usr/bin/env python3
"""
Keyword Synchronization Manager
Ensures keyword changes are automatically propagated across all database tables
"""

import os
import logging
import psycopg2
from typing import List, Set, Dict, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class KeywordSyncManager:
    """Manages automatic keyword synchronization across all database tables"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not found")
    
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url)
    
    def get_active_keywords(self) -> Set[str]:
        """Get all currently active keywords from database"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT keyword FROM keyword_attribution 
                        WHERE is_active = TRUE 
                        ORDER BY keyword
                    """)
                    results = cursor.fetchall()
                    return {row[0].lower().strip() for row in results}
        except Exception as e:
            logger.error(f"Failed to get active keywords: {e}")
            return set()
    
    def deactivate_keyword(self, keyword: str) -> bool:
        """
        Deactivate a keyword across ALL database tables and related systems
        """
        keyword = keyword.lower().strip()
        logger.info(f"🔄 Starting comprehensive keyword deactivation for: '{keyword}'")
        
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 1. Deactivate in keyword_attribution table
                    cursor.execute("""
                        UPDATE keyword_attribution 
                        SET is_active = FALSE, 
                            updated_at = NOW(),
                            deactivated_reason = 'User removed keyword'
                        WHERE keyword = %s
                    """, (keyword,))
                    
                    affected_rows = cursor.rowcount
                    logger.info(f"✅ Deactivated {affected_rows} entries in keyword_attribution")
                    
                    # 2. Add to keyword removal log for audit trail
                    cursor.execute("""
                        INSERT INTO keyword_removal_log (keyword, removed_at, reason)
                        VALUES (%s, NOW(), 'User deactivation request')
                        ON CONFLICT (keyword) DO UPDATE SET
                            removed_at = NOW(),
                            reason = 'User deactivation request'
                    """, (keyword,))
                    
                    # 3. Mark related notifications as disabled (skip if column doesn't exist)
                    try:
                        cursor.execute("""
                            UPDATE notified_tokens 
                            SET is_disabled = TRUE 
                            WHERE token_name ILIKE %s OR token_symbol ILIKE %s
                        """, (f'%{keyword}%', f'%{keyword}%'))
                        
                        notified_disabled = cursor.rowcount
                        logger.info(f"✅ Disabled {notified_disabled} related notifications")
                    except psycopg2.errors.UndefinedColumn:
                        logger.info("⏭️ Skipping notification disable (column doesn't exist)")
                    
                    # 4. Update detected tokens to mark keyword matches as inactive (skip if column doesn't exist)
                    try:
                        cursor.execute("""
                            UPDATE detected_tokens 
                            SET keywords = array_remove(keywords, %s)
                            WHERE %s = ANY(keywords)
                        """, (keyword, keyword))
                        
                        detected_updated = cursor.rowcount
                        logger.info(f"✅ Updated {detected_updated} detected token entries")
                    except psycopg2.errors.UndefinedColumn:
                        logger.info("⏭️ Skipping detected tokens update (column doesn't exist)")
                    
                    conn.commit()
                    
                    logger.info(f"🎯 Keyword '{keyword}' completely deactivated across all systems")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Failed to deactivate keyword '{keyword}': {e}")
            return False
    
    def activate_keyword(self, keyword: str, user_id: Optional[str] = None) -> bool:
        """
        Activate a keyword and ensure it's properly set up across all systems
        """
        keyword = keyword.lower().strip()
        logger.info(f"🔄 Starting comprehensive keyword activation for: '{keyword}'")
        
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 1. Activate in keyword_attribution table
                    cursor.execute("""
                        INSERT INTO keyword_attribution (keyword, is_active, user_id, created_at, updated_at)
                        VALUES (%s, TRUE, %s, NOW(), NOW())
                        ON CONFLICT (keyword) DO UPDATE SET
                            is_active = TRUE,
                            user_id = COALESCE(EXCLUDED.user_id, keyword_attribution.user_id),
                            updated_at = NOW(),
                            deactivated_reason = NULL
                    """, (keyword, user_id))
                    
                    # 2. Remove from removal log if exists
                    cursor.execute("""
                        DELETE FROM keyword_removal_log WHERE keyword = %s
                    """, (keyword,))
                    
                    conn.commit()
                    
                    logger.info(f"🎯 Keyword '{keyword}' successfully activated")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Failed to activate keyword '{keyword}': {e}")
            return False
    
    def sync_keywords_from_list(self, new_keywords: List[str], user_id: Optional[str] = None) -> Dict[str, any]:
        """
        Synchronize keywords from a new list - activate new ones, deactivate removed ones
        """
        new_keywords_set = {kw.lower().strip() for kw in new_keywords if kw.strip()}
        current_keywords = self.get_active_keywords()
        
        # Find changes
        to_activate = new_keywords_set - current_keywords
        to_deactivate = current_keywords - new_keywords_set
        
        results = {
            'activated': [],
            'deactivated': [],
            'errors': []
        }
        
        logger.info(f"🔄 Syncing keywords: {len(to_activate)} to activate, {len(to_deactivate)} to deactivate")
        
        # Activate new keywords
        for keyword in to_activate:
            if self.activate_keyword(keyword, user_id):
                results['activated'].append(keyword)
            else:
                results['errors'].append(f"Failed to activate: {keyword}")
        
        # Deactivate removed keywords
        for keyword in to_deactivate:
            if self.deactivate_keyword(keyword):
                results['deactivated'].append(keyword)
            else:
                results['errors'].append(f"Failed to deactivate: {keyword}")
        
        logger.info(f"✅ Sync complete: {len(results['activated'])} activated, {len(results['deactivated'])} deactivated")
        return results
    
    def create_required_tables(self):
        """Create any missing tables needed for keyword synchronization"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Create keyword removal log table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS keyword_removal_log (
                            id SERIAL PRIMARY KEY,
                            keyword VARCHAR(100) UNIQUE NOT NULL,
                            removed_at TIMESTAMP DEFAULT NOW(),
                            reason TEXT,
                            created_at TIMESTAMP DEFAULT NOW()
                        );
                    """)
                    
                    # Add columns to existing tables if they don't exist
                    cursor.execute("""
                        ALTER TABLE keyword_attribution 
                        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW(),
                        ADD COLUMN IF NOT EXISTS deactivated_reason TEXT;
                    """)
                    
                    try:
                        cursor.execute("""
                            ALTER TABLE notified_tokens 
                            ADD COLUMN IF NOT EXISTS is_disabled BOOLEAN DEFAULT FALSE;
                        """)
                    except Exception as e:
                        logger.debug(f"Column addition skipped: {e}")
                    
                    conn.commit()
                    logger.info("✅ Database tables updated for keyword synchronization")
                    
        except Exception as e:
            logger.error(f"❌ Failed to create required tables: {e}")
    
    def get_sync_status(self) -> Dict[str, any]:
        """Get current synchronization status and statistics"""
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Get active keywords count
                    cursor.execute("SELECT COUNT(*) FROM keyword_attribution WHERE is_active = TRUE")
                    active_count = cursor.fetchone()[0]
                    
                    # Get deactivated keywords count
                    cursor.execute("SELECT COUNT(*) FROM keyword_attribution WHERE is_active = FALSE")
                    inactive_count = cursor.fetchone()[0]
                    
                    # Get recent removals
                    cursor.execute("""
                        SELECT keyword, removed_at FROM keyword_removal_log 
                        WHERE removed_at > NOW() - INTERVAL '24 hours'
                        ORDER BY removed_at DESC LIMIT 10
                    """)
                    recent_removals = cursor.fetchall()
                    
                    return {
                        'active_keywords': active_count,
                        'inactive_keywords': inactive_count,
                        'recent_removals': [{'keyword': r[0], 'removed_at': r[1]} for r in recent_removals],
                        'sync_healthy': True
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {'sync_healthy': False, 'error': str(e)}

# Convenience functions for easy import
def deactivate_keyword_completely(keyword: str) -> bool:
    """Completely deactivate a keyword across all systems"""
    try:
        sync_manager = KeywordSyncManager()
        sync_manager.create_required_tables()
        return sync_manager.deactivate_keyword(keyword)
    except Exception as e:
        logger.error(f"Failed to deactivate keyword completely: {e}")
        return False

def sync_keywords_from_list(keywords: List[str], user_id: Optional[str] = None) -> Dict[str, any]:
    """Sync keywords from a complete list"""
    try:
        sync_manager = KeywordSyncManager()
        sync_manager.create_required_tables()
        return sync_manager.sync_keywords_from_list(keywords, user_id)
    except Exception as e:
        logger.error(f"Failed to sync keywords: {e}")
        return {'errors': [str(e)]}

if __name__ == "__main__":
    # Test the sync manager
    logging.basicConfig(level=logging.INFO)
    sync_manager = KeywordSyncManager()
    sync_manager.create_required_tables()
    
    status = sync_manager.get_sync_status()
    print(f"Sync Status: {json.dumps(status, indent=2, default=str)}")