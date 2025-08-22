#!/usr/bin/env python3
"""
Dual Table Token Processor
Handles token detection with separate pending and resolved token tables.
"""

import psycopg2
import os
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DualTableTokenProcessor:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not found")
    
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url)
    
    def insert_pending_token(self, contract_address, placeholder_name, keyword=None, 
                           matched_keywords=None, blockchain_age_seconds=None):
        """Insert token into pending_tokens table for incomplete tokens"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Generate placeholder name if not provided
            if not placeholder_name:
                # Create unique identifier from contract address
                address_suffix = contract_address[:6] if contract_address else "UNKNOWN"
                placeholder_name = f"Unnamed Token {address_suffix}"
            
            # Prepare matched keywords array
            keywords_array = matched_keywords if matched_keywords else []
            
            cursor.execute('''
                INSERT INTO pending_tokens 
                (contract_address, token_name, keyword, matched_keywords, 
                 blockchain_age_seconds, retry_count)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (contract_address) 
                DO UPDATE SET 
                    token_name = EXCLUDED.token_name,
                    keyword = EXCLUDED.keyword,
                    matched_keywords = EXCLUDED.matched_keywords,
                    blockchain_age_seconds = EXCLUDED.blockchain_age_seconds,
                    retry_count = pending_tokens.retry_count + 1,
                    last_retry_at = CURRENT_TIMESTAMP
                RETURNING id
            ''', (
                contract_address, 
                placeholder_name, 
                keyword, 
                keywords_array,
                blockchain_age_seconds,
                0
            ))
            
            result = cursor.fetchone()
            if result:
                token_id = result[0]
                conn.commit()
                
                logger.info(f"⚡ PENDING TOKEN STORED: {placeholder_name} ({contract_address[:10]}...)")
                logger.info(f"🔄 QUEUED: {placeholder_name} for background name resolution")
                
                cursor.close()
                conn.close()
                
                return token_id
            else:
                conn.rollback()
                cursor.close()
                conn.close()
                return None
            
        except Exception as e:
            logger.error(f"❌ Failed to insert pending token: {e}")
            return None
    
    def insert_resolved_token(self, contract_address, token_name, symbol=None, 
                            keyword=None, matched_keywords=None, blockchain_age_seconds=None,
                            social_links=None):
        """Insert token directly into detected_tokens table for resolved tokens"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Prepare data
            keywords_array = matched_keywords if matched_keywords else []
            
            cursor.execute('''
                INSERT INTO detected_tokens 
                (contract_address, token_name, symbol, matched_keywords, blockchain_age_seconds, platform)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (contract_address) 
                DO UPDATE SET 
                    token_name = EXCLUDED.token_name,
                    symbol = EXCLUDED.symbol,
                    matched_keywords = EXCLUDED.matched_keywords,
                    blockchain_age_seconds = EXCLUDED.blockchain_age_seconds,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            ''', (
                contract_address,
                token_name,
                symbol,
                keywords_array,
                blockchain_age_seconds,
                'LetsBonk'
            ))
            
            result = cursor.fetchone()
            if result:
                token_id = result[0]
                conn.commit()
                
                logger.info(f"✅ RESOLVED TOKEN STORED: {token_name} ({contract_address[:10]}...)")
                
                cursor.close()
                conn.close()
                
                return token_id
            else:
                conn.rollback()
                cursor.close()
                conn.close()
                return None
            
        except Exception as e:
            logger.error(f"❌ Failed to insert resolved token: {e}")
            return None
    
    def migrate_pending_to_resolved(self, contract_address, token_name, symbol=None, social_links=None):
        """Migrate token from pending_tokens to detected_tokens once name is resolved"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get pending token data
            cursor.execute('''
                SELECT contract_address, matched_keywords, blockchain_age_seconds, detected_at
                FROM pending_tokens 
                WHERE contract_address = %s AND name_status = 'pending'
            ''', (contract_address,))
            
            pending_data = cursor.fetchone()
            if not pending_data:
                logger.warning(f"⚠️ No pending token found for {contract_address[:10]}...")
                return False
            
            contract_addr, matched_keywords, blockchain_age, detected_at = pending_data
            
            # Insert into detected_tokens
            social_links_json = social_links if social_links else {}
            
            cursor.execute('''
                INSERT INTO detected_tokens 
                (address, name, symbol, matched_keywords, name_status, status, platform, detection_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (address) 
                DO UPDATE SET 
                    name = EXCLUDED.name,
                    symbol = EXCLUDED.symbol,
                    name_status = 'resolved',
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                contract_addr,
                token_name,
                symbol,
                matched_keywords,
                'resolved',
                'detected',
                'LetsBonk',
                detected_at
            ))
            
            # Remove from pending_tokens
            cursor.execute('''
                DELETE FROM pending_tokens
                WHERE contract_address = %s
            ''', (contract_address,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ MIGRATED: {token_name} from pending_tokens to detected_tokens")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to migrate token: {e}")
            return False
    
    def insert_detected_token(self, contract_address, token_name, symbol=None, 
                            platform='letsbonk.fun', social_links=None, 
                            matched_keywords=None, blockchain_age_seconds=None):
        """Insert token directly into detected_tokens table"""
        return self.insert_resolved_token(
            contract_address=contract_address,
            token_name=token_name,
            symbol=symbol,
            matched_keywords=matched_keywords,
            blockchain_age_seconds=blockchain_age_seconds,
            social_links=social_links
        )
    
    def get_pending_tokens(self, limit=50):
        """Get pending tokens for background processing"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT contract_address, placeholder_name, matched_keywords, 
                       retry_count, detected_at, blockchain_age_seconds
                FROM pending_tokens 
                WHERE name_status = 'pending'
                ORDER BY detected_at ASC
                LIMIT %s
            ''', (limit,))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to get pending tokens: {e}")
            return []
    
    def update_retry_count(self, contract_address):
        """Update retry count for pending token"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE pending_tokens 
                SET retry_count = retry_count + 1,
                    last_attempt = CURRENT_TIMESTAMP
                WHERE contract_address = %s
            ''', (contract_address,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to update retry count: {e}")
    
    def create_tables_if_needed(self):
        """Create dual table structure if not exists"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Create pending_tokens table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pending_tokens (
                    id SERIAL PRIMARY KEY,
                    contract_address VARCHAR(255) UNIQUE NOT NULL,
                    placeholder_name VARCHAR(255) NOT NULL,
                    keyword VARCHAR(255),
                    matched_keywords TEXT[],
                    blockchain_age_seconds INTEGER,
                    name_status VARCHAR(50) DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create detected_tokens table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detected_tokens (
                    id SERIAL PRIMARY KEY,
                    address VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    symbol VARCHAR(50),
                    matched_keywords TEXT[],
                    name_status VARCHAR(50) DEFAULT 'resolved',
                    status VARCHAR(50) DEFAULT 'detected',
                    platform VARCHAR(100) DEFAULT 'LetsBonk',
                    detection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("✅ Dual table structure verified/created")
            
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            
            conn.commit()
            
            logger.info(f"🎯 MIGRATION COMPLETE: {token_name} moved from pending to resolved")
            logger.info(f"✅ FINAL STATE: {token_name} ({contract_address[:10]}...)")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to migrate token: {e}")
            return False
    
    def get_pending_tokens(self, limit=50):
        """Get tokens that need name resolution"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT contract_address, placeholder_name, matched_keywords, 
                       retry_count, detected_at, blockchain_age_seconds
                FROM pending_tokens 
                WHERE name_status = 'pending' 
                AND retry_count < 10
                ORDER BY detected_at ASC
                LIMIT %s
            ''', (limit,))
            
            pending_tokens = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return pending_tokens
            
        except Exception as e:
            logger.error(f"❌ Failed to get pending tokens: {e}")
            return []
    
    def get_resolved_tokens(self, limit=50):
        """Get recently resolved tokens"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT address, name, symbol, matched_keywords, 
                       detection_timestamp
                FROM detected_tokens 
                WHERE name_status = 'resolved'
                ORDER BY detection_timestamp DESC
                LIMIT %s
            ''', (limit,))
            
            resolved_tokens = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return resolved_tokens
            
        except Exception as e:
            logger.error(f"❌ Failed to get resolved tokens: {e}")
            return []
    
    def update_retry_count(self, contract_address):
        """Update retry count for a pending token"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE pending_tokens 
                SET retry_count = retry_count + 1,
                    last_attempt = CURRENT_TIMESTAMP
                WHERE contract_address = %s
            ''', (contract_address,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to update retry count: {e}")
    
    def get_system_stats(self):
        """Get dual table system statistics"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Count pending tokens
            cursor.execute('SELECT COUNT(*) FROM pending_tokens WHERE name_status = %s', ('pending',))
            pending_count = cursor.fetchone()[0]
            
            # Count resolved tokens (last 24 hours)
            cursor.execute('''
                SELECT COUNT(*) FROM detected_tokens 
                WHERE name_status = %s 
                AND detection_timestamp > NOW() - INTERVAL '24 hours'
            ''', ('resolved',))
            resolved_count = cursor.fetchone()[0]
            
            # Count total resolved tokens
            cursor.execute('SELECT COUNT(*) FROM detected_tokens WHERE name_status = %s', ('resolved',))
            total_resolved = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {
                'pending_tokens': pending_count,
                'resolved_today': resolved_count,
                'total_resolved': total_resolved
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get system stats: {e}")
            return {'pending_tokens': 0, 'resolved_today': 0, 'total_resolved': 0}

if __name__ == "__main__":
    # Test the dual table system
    processor = DualTableTokenProcessor()
    
    # Test inserting a pending token
    test_address = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
    pending_id = processor.insert_pending_token(
        test_address, 
        "Unnamed Token TEST", 
        keyword="test",
        matched_keywords=["test", "demo"],
        blockchain_age_seconds=15.5
    )
    
    if pending_id:
        print(f"✅ Test pending token inserted with ID: {pending_id}")
        
        # Get system stats
        stats = processor.get_system_stats()
        print(f"📊 System Stats: {stats}")
        
        # Get pending tokens
        pending = processor.get_pending_tokens(5)
        print(f"⏳ Pending tokens: {len(pending)}")
    else:
        print("❌ Failed to insert test pending token")