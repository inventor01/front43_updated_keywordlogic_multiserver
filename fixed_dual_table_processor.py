#!/usr/bin/env python3
"""
Fixed Dual Table Token Processor with Fallback Support
Handles token detection with separate pending, detected, and fallback token tables.
"""

import psycopg2
import os
import logging
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FixedDualTableProcessor:
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
    
    def insert_detected_token(self, address, name, symbol=None, matched_keywords=None, name_status='resolved'):
        """Insert token into detected_tokens table (alias for insert_resolved_token)"""
        # CRITICAL VALIDATION: Prevent unnamed tokens from being inserted into detected_tokens
        if name and name.startswith('Unnamed Token'):
            logger.error(f"🚫 CRITICAL BLOCK: Cannot insert unnamed token '{name}' into detected_tokens")
            logger.error(f"🔄 ROUTING VIOLATION: This token MUST use insert_fallback_token() instead")
            logger.error(f"📍 TOKEN ADDRESS: {address}")
            # Force failure to prevent insertion
            raise ValueError(f"Routing violation: Unnamed token '{name}' cannot go to detected_tokens")
            
        return self.insert_resolved_token(address, name, symbol, matched_keywords=matched_keywords)
    
    def insert_resolved_token(self, contract_address, token_name, symbol=None, 
                            keyword=None, matched_keywords=None, blockchain_age_seconds=None):
        """Insert token directly into detected_tokens table for resolved tokens"""
        
        # CRITICAL VALIDATION: Prevent unnamed tokens from entering detected_tokens
        if token_name and token_name.startswith('Unnamed Token'):
            logger.error(f"🚫 CRITICAL ERROR: Attempted to insert unnamed token '{token_name}' into detected_tokens")
            logger.error(f"🔄 ROUTING VIOLATION: This token should go to fallback_processing_coins")
            logger.error(f"📍 CONTRACT ADDRESS: {contract_address}")
            # Force failure to prevent insertion
            raise ValueError(f"Routing violation: Unnamed token '{token_name}' cannot go to detected_tokens")
            
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Prepare data
            keywords_array = matched_keywords if matched_keywords else []
            
            cursor.execute('''
                INSERT INTO detected_tokens 
                (address, name, symbol, matched_keywords, platform, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (address) 
                DO UPDATE SET 
                    name = EXCLUDED.name,
                    symbol = EXCLUDED.symbol,
                    matched_keywords = EXCLUDED.matched_keywords,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            ''', (
                contract_address,  # address
                token_name,        # name
                symbol,
                keywords_array,
                'LetsBonk',
                'detected'
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
    
    def insert_fallback_token(self, contract_address, token_name=None, symbol=None, 
                            keyword=None, matched_keywords=None, blockchain_age_seconds=None,
                            processing_status='pending', error_message=None):
        """Insert token into fallback_processing_coins table for tokens that need special handling"""
        try:
            # Validate contract address format (Solana addresses are 32-44 characters, base58)
            if not contract_address or len(contract_address) < 32:
                logger.error(f"❌ Invalid contract address format: {contract_address}")
                return None
            
            # Skip test addresses that start with TEST_ or FALLBACK_
            if contract_address.startswith(('TEST_', 'FALLBACK_', 'ERROR_', 'MONITOR_')):
                logger.warning(f"⚠️ Skipping test address: {contract_address}")
                return None
            
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Generate fallback name if not provided
            if not token_name:
                address_suffix = contract_address[:6] if contract_address else "UNKNOWN"
                token_name = f"Fallback Token {address_suffix}"
            
            # Prepare matched keywords array
            keywords_array = matched_keywords if matched_keywords else []
            
            cursor.execute('''
                INSERT INTO fallback_processing_coins 
                (contract_address, token_name, symbol, blockchain_age_seconds, 
                 matched_keywords, keyword, processing_status, error_message, retry_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (contract_address) 
                DO UPDATE SET 
                    token_name = EXCLUDED.token_name,
                    symbol = EXCLUDED.symbol,
                    blockchain_age_seconds = EXCLUDED.blockchain_age_seconds,
                    matched_keywords = EXCLUDED.matched_keywords,
                    keyword = EXCLUDED.keyword,
                    processing_status = EXCLUDED.processing_status,
                    error_message = EXCLUDED.error_message,
                    retry_count = COALESCE(fallback_processing_coins.retry_count, 0) + 1,
                    last_retry_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            ''', (
                contract_address,
                token_name,
                symbol,
                blockchain_age_seconds,
                keywords_array,
                keyword,
                processing_status,
                error_message,
                1  # Start with retry count 1 - first attempt
            ))
            
            result = cursor.fetchone()
            if result:
                token_id = result[0]
                conn.commit()
                
                logger.info(f"🔄 FALLBACK TOKEN STORED: {token_name} ({contract_address[:10]}...)")
                logger.info(f"📝 STATUS: {processing_status}")
                
                cursor.close()
                conn.close()
                
                return token_id
            else:
                conn.rollback()
                cursor.close()
                conn.close()
                return None
            
        except Exception as e:
            logger.error(f"❌ Failed to insert fallback token: {e}")
            return None
    
    def migrate_pending_to_resolved(self, contract_address, token_name, symbol=None, 
                                  matched_keywords=None):
        """Migrate token from pending_tokens to detected_tokens"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # First insert into detected_tokens
            token_id = self.insert_resolved_token(
                contract_address, token_name, symbol, 
                matched_keywords=matched_keywords
            )
            
            if token_id:
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
            else:
                conn.rollback()
                cursor.close()
                conn.close()
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to migrate token: {e}")
            return False
    
    def migrate_fallback_to_detected(self, contract_address, token_name, symbol=None, matched_keywords=None):
        """Migrate token from fallback_processing_coins to detected_tokens"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Insert into detected_tokens
            token_id = self.insert_resolved_token(
                contract_address, token_name, symbol, 
                matched_keywords=matched_keywords
            )
            
            if token_id:
                # Delete from fallback_processing_coins after successful migration
                cursor.execute('''
                    DELETE FROM fallback_processing_coins 
                    WHERE contract_address = %s
                ''', (contract_address,))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                logger.info(f"✅ MIGRATED: {token_name} from fallback_processing_coins to detected_tokens")
                logger.info(f"🧹 CLEANED: Removed fallback entry for {contract_address[:10]}...")
                return True
            else:
                conn.rollback()
                cursor.close()
                conn.close()
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to migrate fallback token: {e}")
            return False
    
    def update_fallback_retry_count(self, contract_address):
        """Update retry count for fallback token"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE fallback_processing_coins 
                SET retry_count = COALESCE(retry_count, 0) + 1,
                    last_retry_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE contract_address = %s
            ''', (contract_address,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.debug(f"🔄 Updated retry count for {contract_address[:10]}...")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update retry count: {e}")
            return False
    
    def get_fallback_tokens(self, limit=50):
        """Get fallback tokens that need name resolution"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT contract_address, token_name, symbol, matched_keywords, 
                       blockchain_age_seconds, created_at, processing_status, retry_count
                FROM fallback_processing_coins 
                WHERE processing_status = 'name_pending' 
                AND retry_count < 5
                ORDER BY created_at ASC
                LIMIT %s
            ''', (limit,))
            
            tokens = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return tokens
            
        except Exception as e:
            logger.error(f"❌ Failed to get fallback tokens: {e}")
            return []
    
    def get_pending_tokens(self, limit=50):
        """Get pending tokens for background processing"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT contract_address, token_name, matched_keywords, 
                       retry_count, detected_at, blockchain_age_seconds
                FROM pending_tokens 
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
    
    def get_fallback_tokens(self, limit=50):
        """Get fallback tokens for special processing"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT contract_address, token_name, matched_keywords, 
                       retry_count, detected_at, blockchain_age_seconds, processing_status
                FROM fallback_processing_coins 
                WHERE processing_status IN ('pending', 'api_failed', 'network_error', 'name_pending')
                AND migrated_to_detected IS NOT TRUE
                ORDER BY detected_at ASC
                LIMIT %s
            ''', (limit,))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to get fallback tokens: {e}")
            return []
    
    def update_retry_count(self, contract_address, table='pending_tokens'):
        """Update retry count for pending or fallback token"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            if table == 'fallback_processing_coins':
                cursor.execute('''
                    UPDATE fallback_processing_coins 
                    SET retry_count = retry_count + 1,
                        last_retry_at = CURRENT_TIMESTAMP
                    WHERE contract_address = %s
                ''', (contract_address,))
            else:
                cursor.execute('''
                    UPDATE pending_tokens 
                    SET retry_count = retry_count + 1,
                        last_retry_at = CURRENT_TIMESTAMP
                    WHERE contract_address = %s
                ''', (contract_address,))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to update retry count: {e}")
    
    def create_tables_if_needed(self):
        """Create all required tables if they don't exist"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Create pending_tokens table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pending_tokens (
                    id SERIAL PRIMARY KEY,
                    contract_address VARCHAR(255) UNIQUE NOT NULL,
                    token_name VARCHAR(255),
                    symbol VARCHAR(50),
                    keyword VARCHAR(255),
                    matched_keywords TEXT[],
                    blockchain_age_seconds DOUBLE PRECISION,
                    retry_count INTEGER DEFAULT 0,
                    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    last_retry_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Ensure detected_tokens has proper structure (using existing schema)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detected_tokens (
                    id SERIAL PRIMARY KEY,
                    address VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255),
                    symbol VARCHAR(50),
                    matched_keywords TEXT[],
                    platform VARCHAR(100) DEFAULT 'LetsBonk',
                    status VARCHAR(50) DEFAULT 'detected',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    market_cap BIGINT,
                    migrated_to_raydium BOOLEAN DEFAULT FALSE,
                    migration_timestamp TIMESTAMP WITH TIME ZONE,
                    notification_sent BOOLEAN DEFAULT FALSE,
                    created_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    detection_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    name_status VARCHAR(50) DEFAULT 'resolved',
                    social_links TEXT[]
                )
            ''')
            
            # Create fallback_processing_coins table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fallback_processing_coins (
                    id SERIAL PRIMARY KEY,
                    contract_address VARCHAR(255) UNIQUE NOT NULL,
                    token_name VARCHAR(255),
                    symbol VARCHAR(50),
                    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    processing_status VARCHAR(50) DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    last_retry_at TIMESTAMP WITH TIME ZONE,
                    blockchain_age_seconds DOUBLE PRECISION,
                    matched_keywords TEXT[],
                    keyword VARCHAR(255),
                    platform VARCHAR(100) DEFAULT 'LetsBonk',
                    error_message TEXT,
                    success_timestamp TIMESTAMP WITH TIME ZONE,
                    migrated_to_detected BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_pending_tokens_contract ON pending_tokens(contract_address)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_detected_tokens_address ON detected_tokens(address)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_fallback_processing_contract ON fallback_processing_coins(contract_address)')
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("✅ All tables structure verified/created")
            
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
    
    def get_system_stats(self):
        """Get system statistics for all tables"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Count pending tokens
            cursor.execute('SELECT COUNT(*) FROM pending_tokens')
            pending_count = cursor.fetchone()[0] if cursor.fetchone() else 0
            
            # Count detected tokens
            cursor.execute('SELECT COUNT(*) FROM detected_tokens')
            detected_count = cursor.fetchone()[0] if cursor.fetchone() else 0
            
            # Count fallback tokens
            cursor.execute('SELECT COUNT(*) FROM fallback_processing_coins')
            fallback_count = cursor.fetchone()[0] if cursor.fetchone() else 0
            
            cursor.close()
            conn.close()
            
            return {
                'pending_tokens': pending_count,
                'detected_tokens': detected_count,
                'fallback_tokens': fallback_count,
                'total_tokens': pending_count + detected_count + fallback_count
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get system stats: {e}")
            return {'pending_tokens': 0, 'detected_tokens': 0, 'fallback_tokens': 0, 'total_tokens': 0}

    def update_retry_count(self, contract_address, table='pending_tokens'):
        """Update retry count for pending or fallback token"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            if table == 'fallback_processing_coins':
                cursor.execute('''
                    UPDATE fallback_processing_coins 
                    SET retry_count = retry_count + 1,
                        last_retry_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE contract_address = %s
                ''', (contract_address,))
            else:
                cursor.execute('''
                    UPDATE pending_tokens 
                    SET retry_count = retry_count + 1,
                        last_retry_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE contract_address = %s
                ''', (contract_address,))
            
            affected_rows = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            if affected_rows > 0:
                logger.info(f"📈 Retry count updated for {contract_address[:10]}... in {table}")
                return True
            else:
                logger.warning(f"⚠️ No rows updated for {contract_address[:10]}... in {table}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Failed to update retry count: {e}")
            return False

# Global instance for easy import
dual_processor = FixedDualTableProcessor()

if __name__ == "__main__":
    # Test the system
    processor = FixedDualTableProcessor()
    processor.create_tables_if_needed()
    
    # Test inserting a fallback token
    from datetime import datetime
    test_address = "TEST_FALLBACK_" + str(datetime.now().timestamp())
    fallback_id = processor.insert_fallback_token(
        test_address, 
        "Test Fallback Token",
        processing_status='pending',
        error_message='API timeout during name resolution'
    )
    
    if fallback_id:
        print(f"✅ Successfully tested fallback token insertion: ID {fallback_id}")
    else:
        print("❌ Failed to test fallback token insertion")
    
    # Show stats
    stats = processor.get_system_stats()
    print(f"📊 System Stats: {stats}")