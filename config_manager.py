"""
Configuration management module for watchlist and settings.
"""

import os
import logging
import psycopg2
from typing import Set, List
from config import Config

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages watchlist and configuration file operations."""
    
    def __init__(self):
        self.watchlist_file = Config.WATCHLIST_FILE
        
    def load_watchlist(self) -> Set[str]:
        """
        Load watchlist keywords from file.
        
        Returns:
            Set of keywords (lowercased and stripped)
        """
        keywords = set()
        
        try:
            if not os.path.exists(self.watchlist_file):
                logger.warning(f"Watchlist file {self.watchlist_file} does not exist, creating empty file")
                self.save_watchlist([])
                return keywords
                
            with open(self.watchlist_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                        
                    # Basic validation
                    if len(line) < 2:
                        logger.warning(f"Skipping short keyword on line {line_num}: '{line}'")
                        continue
                        
                    if len(line) > 100:
                        logger.warning(f"Skipping long keyword on line {line_num}: '{line[:50]}...'")
                        continue
                        
                    keywords.add(line.lower())
                    
            logger.debug(f"Loaded {len(keywords)} keywords from {self.watchlist_file}")
            return keywords
            
        except Exception as e:
            logger.error(f"Error loading watchlist from {self.watchlist_file}: {e}")
            return set()
            
    def save_watchlist(self, keywords: List[str]) -> bool:
        """
        Save watchlist keywords to file.
        
        Args:
            keywords: List of keywords to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.watchlist_file) if os.path.dirname(self.watchlist_file) else '.', exist_ok=True)
            
            with open(self.watchlist_file, 'w', encoding='utf-8') as f:
                f.write("# Pump.fun Coin Watchlist\n")
                f.write("# Add one keyword per line\n")
                f.write("\n")
                
                for keyword in sorted(keywords):
                    f.write(f"{keyword}\n")
                    
            logger.info(f"Saved {len(keywords)} keywords to {self.watchlist_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving watchlist to {self.watchlist_file}: {e}")
            return False
    
    def list_keywords(self, user_id: str = None) -> List[str]:
        """Get list of keywords from PostgreSQL database with optional user filtering"""
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            try:
                import psycopg2
                
                # Enhanced connection with timeout for Railway
                conn = psycopg2.connect(
                    database_url,
                    connect_timeout=10,
                    application_name='discord_bot_keyword_list'
                )
                cursor = conn.cursor()
                
                if user_id:
                    # Filter by specific user
                    cursor.execute("SELECT keyword FROM keywords WHERE user_id = %s ORDER BY keyword", (user_id,))
                else:
                    # Return all keywords (for backward compatibility)
                    cursor.execute("SELECT keyword FROM keywords ORDER BY keyword")
                
                results = cursor.fetchall()
                cursor.close()
                conn.close()
                
                if results:
                    keywords = [row[0] for row in results]
                    logger.info(f"✅ Retrieved {len(keywords)} keywords for user_id={user_id}")
                    return keywords
                else:
                    logger.warning(f"⚠️ No keywords found for user_id={user_id}")
                    return []
                    
            except psycopg2.OperationalError as e:
                logger.error(f"❌ Database connection failed: {e}")
                return []
            except Exception as e:
                logger.error(f"❌ Error retrieving keywords: {e}")
                return []
        else:
            logger.error("❌ No DATABASE_URL environment variable found")
            return []
    
    def _get_fallback_keywords(self) -> List[str]:
        """Get fallback keyword list - now returns empty list to stop random notifications"""
        logger.warning("⚠️ ConfigManager: Fallback keywords disabled - returning empty list")
        return []
    
    def clear_all_keywords(self) -> bool:
        """Clear all keywords from both database and file"""
        try:
            # Clear from database first
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                conn = psycopg2.connect(database_url)
                cursor = conn.cursor()
                
                # Deactivate all keywords in database
                cursor.execute("UPDATE keyword_attribution SET is_active = FALSE, deactivated_reason = 'bulk_clear'")
                conn.commit()
                cursor.close()
                conn.close()
                logger.info("✅ ConfigManager: Cleared all keywords from database")
            
            # Clear from file as well
            success = self.save_watchlist([])
            if success:
                logger.info("✅ ConfigManager: Cleared all keywords from file")
                return True
            else:
                logger.error("❌ ConfigManager: Failed to clear keywords from file")
                return False
                
        except Exception as e:
            logger.error(f"❌ ConfigManager: Error clearing all keywords: {e}")
            # Try to clear file only as fallback
            return self.save_watchlist([])
    
    def get_keywords(self) -> Set[str]:
        """Get keywords as set (for backward compatibility)"""
        return self.load_watchlist()
    
    def add_keyword(self, keyword: str, user_id: str = "System") -> tuple:
        """Add a keyword directly to PostgreSQL database"""
        try:
            # Direct database addition - same method that worked for "ready or not"
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                conn = psycopg2.connect(database_url)
                cursor = conn.cursor()
                
                # Check if keyword already exists for this user
                cursor.execute("SELECT keyword FROM keywords WHERE LOWER(keyword) = LOWER(%s) AND user_id = %s", (keyword, user_id))
                if cursor.fetchone():
                    logger.info(f"⚠️ Keyword '{keyword}' already exists for user '{user_id}'")
                    cursor.close()
                    conn.close()
                    return (False, "already_exists")
                
                # Insert new keyword
                cursor.execute("INSERT INTO keywords (keyword, user_id) VALUES (%s, %s)", (keyword, user_id))
                conn.commit()
                cursor.close()
                conn.close()
                
                logger.info(f"✅ Keyword '{keyword}' added to database successfully")
                return (True, "success")
            else:
                logger.error("❌ No DATABASE_URL available for keyword addition")
                return (False, "no_database")
                
        except Exception as e:
            logger.error(f"❌ Error adding keyword '{keyword}' to database: {e}")
            return (False, f"error: {str(e)}")
    
    def remove_keyword(self, keyword: str, user_id: str = None) -> bool:
        """Remove a keyword from the watchlist AND database (Railway-compatible)"""
        keyword = keyword.lower().strip()
        logger.info(f"🔄 Removing keyword '{keyword}' from all systems (user: {user_id})")
        
        try:
            # Remove from database first
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                conn = psycopg2.connect(database_url)
                cursor = conn.cursor()
                
                # Check which tables exist and remove from all of them
                tables_to_check = [
                    ('keyword_attribution', 'keyword'),
                    ('keywords', 'keyword'),
                    ('user_keywords', 'keyword')
                ]
                
                removed_count = 0
                for table_name, column_name in tables_to_check:
                    try:
                        # Check if table exists
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_name = %s
                            )
                        """, (table_name,))
                        
                        result = cursor.fetchone()
                        if result and result[0]:
                            # Remove from this table
                            if table_name == 'keyword_attribution':
                                cursor.execute(f"""
                                    UPDATE {table_name} 
                                    SET is_active = FALSE, 
                                        updated_at = NOW(),
                                        deactivated_reason = 'User removed keyword'
                                    WHERE LOWER({column_name}) = %s
                                """, (keyword,))
                            else:
                                if user_id and table_name == 'keywords':
                                    # User-specific removal for keywords table
                                    cursor.execute(f"DELETE FROM {table_name} WHERE LOWER({column_name}) = %s AND user_id = %s", (keyword, user_id))
                                else:
                                    # Global removal for other tables or when no user_id specified
                                    cursor.execute(f"DELETE FROM {table_name} WHERE LOWER({column_name}) = %s", (keyword,))
                            
                            affected = cursor.rowcount
                            if affected > 0:
                                removed_count += affected
                                logger.info(f"✅ Removed {affected} entries from {table_name}")
                    except Exception as e:
                        logger.warning(f"Could not remove from {table_name}: {e}")
                        continue
                
                conn.commit()
                cursor.close()
                conn.close()
                
                if removed_count > 0:
                    logger.info(f"✅ Successfully removed keyword '{keyword}' from {removed_count} database entries")
                else:
                    logger.warning(f"⚠️ Keyword '{keyword}' not found in database tables")
            
            # Remove from file as well
            keywords = self.load_watchlist()
            if keyword in keywords:
                keywords.discard(keyword)
                file_success = self.save_watchlist(list(keywords))
                if file_success:
                    logger.info(f"✅ Removed keyword '{keyword}' from file")
                return file_success
            else:
                logger.info(f"⚠️ Keyword '{keyword}' not found in file")
                return True  # Consider success if not in file
                
        except Exception as e:
            logger.error(f"❌ Error removing keyword '{keyword}': {e}")
            # Fallback to file-only removal
            try:
                keywords = self.load_watchlist()
                keywords.discard(keyword)
                return self.save_watchlist(list(keywords))
            except Exception as fallback_error:
                logger.error(f"❌ Fallback removal also failed: {fallback_error}")
                return False
    
    def remove_keywords_bulk(self, keywords: List[str]) -> tuple:
        """
        Remove multiple keywords from the watchlist.
        
        Args:
            keywords: List of keywords to remove
            
        Returns:
            Tuple of (removed_keywords, failed_keywords)
        """
        try:
            current_keywords = self.load_watchlist()
            removed_keywords = []
            failed_keywords = []
            
            for keyword in keywords:
                keyword_lower = keyword.strip().lower()
                if keyword_lower in current_keywords:
                    current_keywords.remove(keyword_lower)
                    removed_keywords.append(keyword)
                else:
                    failed_keywords.append(keyword)
            
            if removed_keywords:
                result = self.save_watchlist(list(current_keywords))
                if result:
                    logger.info(f"Bulk removed {len(removed_keywords)} keywords from watchlist")
                else:
                    # If save failed, return all as failed
                    failed_keywords.extend(removed_keywords)
                    removed_keywords = []
            
            return removed_keywords, failed_keywords
                
        except Exception as e:
            logger.error(f"Error removing multiple keywords: {e}")
            return [], keywords
            
    def list_keywords_file(self) -> List[str]:
        """
        Get list of all keywords from file watchlist.
        
        Returns:
            List of keywords from file
        """
        return sorted(list(self.load_watchlist()))
    
    def clear_keywords(self) -> bool:
        """Clear all keywords from watchlist AND database (Railway-compatible)"""
        logger.info("🔄 Clearing ALL keywords from all systems")
        
        try:
            cleared_count = 0
            
            # Clear from database first
            database_url = os.getenv('DATABASE_URL')
            if database_url:
                conn = psycopg2.connect(database_url)
                cursor = conn.cursor()
                
                # Clear from all keyword tables that exist
                tables_to_clear = [
                    ('keyword_attribution', 'UPDATE keyword_attribution SET is_active = FALSE, updated_at = NOW(), deactivated_reason = %s'),
                    ('keywords', 'DELETE FROM keywords'),
                    ('user_keywords', 'DELETE FROM user_keywords')
                ]
                
                for table_name, clear_query in tables_to_clear:
                    try:
                        # Check if table exists
                        cursor.execute("""
                            SELECT EXISTS (
                                SELECT FROM information_schema.tables 
                                WHERE table_name = %s
                            )
                        """, (table_name,))
                        
                        result = cursor.fetchone()
                        if result and result[0]:
                            # Clear this table
                            if 'UPDATE' in clear_query:
                                cursor.execute(clear_query, ('bulk_clear_all',))
                            else:
                                cursor.execute(clear_query)
                            
                            affected = cursor.rowcount
                            if affected > 0:
                                cleared_count += affected
                                logger.info(f"✅ Cleared {affected} entries from {table_name}")
                    except Exception as e:
                        logger.warning(f"Could not clear {table_name}: {e}")
                        continue
                
                conn.commit()
                cursor.close()
                conn.close()
                
                logger.info(f"✅ Cleared {cleared_count} total database entries")
            
            # Clear from file as well
            file_success = self.save_watchlist([])
            if file_success:
                logger.info("✅ Cleared all keywords from file")
            
            return file_success
            
        except Exception as e:
            logger.error(f"❌ Error clearing all keywords: {e}")
            # Fallback to file-only clearing
            try:
                return self.save_watchlist([])
            except Exception as fallback_error:
                logger.error(f"❌ Fallback clear also failed: {fallback_error}")
                return False
        
    def get_watchlist_stats(self) -> dict:
        """
        Get statistics about the current watchlist.
        
        Returns:
            Dictionary with watchlist statistics
        """
        try:
            keywords = self.load_watchlist()
            
            if not keywords:
                return {
                    'total_keywords': 0,
                    'file_exists': os.path.exists(self.watchlist_file),
                    'file_size': 0
                }
                
            file_size = os.path.getsize(self.watchlist_file) if os.path.exists(self.watchlist_file) else 0
            
            return {
                'total_keywords': len(keywords),
                'file_exists': os.path.exists(self.watchlist_file),
                'file_size': file_size,
                'average_keyword_length': sum(len(k) for k in keywords) / len(keywords) if keywords else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting watchlist stats: {e}")
            return {'error': str(e)}
