import psycopg2
import os
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class KeywordAttributionManager:
    def __init__(self, database_url=None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        self.init_database()
    
    def init_database(self):
        """Initialize the keyword attribution database table"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # Create keyword_attribution table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS keyword_attribution (
                    id SERIAL PRIMARY KEY,
                    keyword VARCHAR(255) NOT NULL UNIQUE,
                    added_by_user VARCHAR(255) NOT NULL,
                    added_by_username VARCHAR(255),
                    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                );
            """)
            
            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_keyword_active 
                ON keyword_attribution(keyword, is_active);
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("✅ Keyword attribution database initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize keyword attribution database: {e}")
            raise
    
    def add_keyword_attribution(self, keyword, user_id, username=None, preserve_existing=False):
        """Add keyword attribution tracking"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            if preserve_existing:
                # Only insert if keyword doesn't exist (for system sync)
                cursor.execute("""
                    INSERT INTO keyword_attribution (keyword, added_by_user, added_by_username, added_at, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (keyword) DO NOTHING
                """, (keyword.lower(), str(user_id), username, datetime.now(timezone.utc), True))
            else:
                # Insert or update keyword attribution (for Discord user additions)
                cursor.execute("""
                    INSERT INTO keyword_attribution (keyword, added_by_user, added_by_username, added_at, is_active)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (keyword) 
                    DO UPDATE SET 
                        added_by_user = EXCLUDED.added_by_user,
                        added_by_username = EXCLUDED.added_by_username,
                        added_at = EXCLUDED.added_at,
                        is_active = TRUE
                """, (keyword.lower(), str(user_id), username, datetime.now(timezone.utc), True))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"✅ Added keyword attribution: '{keyword}' by {username or user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to add keyword attribution for '{keyword}': {e}")
            return False
    
    def remove_keyword_attribution(self, keyword):
        """Mark keyword as inactive instead of deleting"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE keyword_attribution 
                SET is_active = FALSE 
                WHERE keyword = %s
            """, (keyword.lower(),))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"✅ Removed keyword attribution: '{keyword}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to remove keyword attribution for '{keyword}': {e}")
            return False
    
    def get_keyword_attribution(self, keyword):
        """Get attribution info for a specific keyword"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT added_by_user, added_by_username, added_at 
                FROM keyword_attribution 
                WHERE keyword = %s AND is_active = TRUE
            """, (keyword.lower(),))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                return {
                    'added_by_user': result[0],
                    'added_by_username': result[1],
                    'added_at': result[2]
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get keyword attribution for '{keyword}': {e}")
            return None
    
    def get_all_keyword_attributions(self):
        """Get all active keyword attributions"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT keyword, added_by_user, added_by_username, added_at 
                FROM keyword_attribution 
                WHERE is_active = TRUE
                ORDER BY added_at DESC
            """)
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            attributions = []
            for row in results:
                attributions.append({
                    'keyword': row[0],
                    'added_by_user': row[1],
                    'added_by_username': row[2],
                    'added_at': row[3]
                })
            
            return attributions
            
        except Exception as e:
            logger.error(f"❌ Failed to get all keyword attributions: {e}")
            return []
    
    def get_keywords_by_user(self, user_id):
        """Get all keywords added by a specific user"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT keyword, added_at 
                FROM keyword_attribution 
                WHERE added_by_user = %s AND is_active = TRUE
                ORDER BY added_at DESC
            """, (str(user_id),))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return [{'keyword': row[0], 'added_at': row[1]} for row in results]
            
        except Exception as e:
            logger.error(f"❌ Failed to get keywords by user {user_id}: {e}")
            return []
    
    def clear_all_attributions(self):
        """Mark all keywords as inactive"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            cursor.execute("UPDATE keyword_attribution SET is_active = FALSE")
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info("✅ Cleared all keyword attributions")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to clear all keyword attributions: {e}")
            return False
    
    def sync_with_existing_keywords(self, existing_keywords, default_user="system", default_username="System"):
        """Sync existing keywords with attribution tracking (only adds attribution for keywords without existing attribution)"""
        try:
            added_count = 0
            for keyword in existing_keywords:
                # Use preserve_existing=True to avoid overriding existing user attributions
                if self.add_keyword_attribution(keyword, default_user, default_username, preserve_existing=True):
                    added_count += 1
            
            logger.info(f"✅ Synced {added_count}/{len(existing_keywords)} keywords with system attribution (existing attributions preserved)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to sync existing keywords: {e}")
            return False