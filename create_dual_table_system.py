#!/usr/bin/env python3
"""
Dual Table System Migration for Token Name Resolution
Creates pending_tokens table and updates system for two-table architecture.
"""

import psycopg2
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_dual_table_system():
    """Create the dual table system for token name resolution"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not found")
        return False
        
    try:
        # Connect to Railway PostgreSQL
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        logger.info("📡 Connected to Railway PostgreSQL database")
        
        # Create pending_tokens table for incomplete tokens
        logger.info("🛠️ Creating pending_tokens table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_tokens (
            id SERIAL PRIMARY KEY,
            contract_address TEXT UNIQUE NOT NULL,
            placeholder_name TEXT,
            detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            keyword TEXT,
            name_status TEXT DEFAULT 'pending',
            retry_count INTEGER DEFAULT 0,
            first_attempt TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            last_attempt TIMESTAMP WITH TIME ZONE,
            platform VARCHAR(100) DEFAULT 'LetsBonk',
            blockchain_age_seconds FLOAT,
            matched_keywords TEXT[]
        );
        ''')
        
        # Ensure detected_tokens table exists with proper structure
        logger.info("🛠️ Ensuring detected_tokens table has proper structure...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS detected_tokens (
            id SERIAL PRIMARY KEY,
            address VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(500),
            symbol VARCHAR(100),
            platform VARCHAR(100) DEFAULT 'LetsBonk',
            status VARCHAR(50) DEFAULT 'detected',
            name_status VARCHAR(50) DEFAULT 'resolved',
            matched_keywords TEXT[],
            social_links JSONB,
            detection_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            blockchain_age_seconds FLOAT,
            keyword TEXT
        );
        ''')
        
        # Create comprehensive performance indexes for pending_tokens
        logger.info("🔧 Creating performance indexes for pending_tokens...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pending_tokens_address ON pending_tokens(contract_address);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pending_tokens_status ON pending_tokens(name_status);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pending_tokens_detected_at ON pending_tokens(detected_at);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pending_tokens_retry_count ON pending_tokens(retry_count);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pending_tokens_last_attempt ON pending_tokens(last_attempt);')
        
        # Update detected_tokens indexes if needed
        logger.info("🔧 Updating detected_tokens indexes...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_detected_tokens_address ON detected_tokens(address);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_detected_tokens_timestamp ON detected_tokens(detection_timestamp);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_detected_tokens_name_status ON detected_tokens(name_status);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_detected_tokens_platform ON detected_tokens(platform);')
        
        # Commit all changes
        conn.commit()
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name AND table_schema = 'public') as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public' 
            AND table_name IN ('pending_tokens', 'detected_tokens')
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        logger.info("✅ Dual table system setup completed successfully!")
        logger.info("📋 Table structure:")
        for table_name, column_count in tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            record_count = cursor.fetchone()[0]
            logger.info(f"   ✅ {table_name}: {column_count} columns, {record_count} records")
        
        # Check pending_tokens specific structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'pending_tokens' AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        pending_columns = cursor.fetchall()
        
        logger.info("🔍 pending_tokens table structure:")
        for col_name, data_type, nullable, default in pending_columns:
            logger.info(f"   • {col_name}: {data_type} (nullable: {nullable})")
            
        logger.info("🚀 Dual table system ready for:")
        logger.info("   • Incomplete tokens → pending_tokens")
        logger.info("   • Resolved tokens → detected_tokens")
        logger.info("   • Background name resolution")
        logger.info("   • Token migration between tables")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Dual table system setup failed: {e}")
        return False

if __name__ == "__main__":
    success = create_dual_table_system()
    if success:
        print("🎉 Dual table system is ready for token name resolution!")
    else:
        print("❌ Dual table system setup failed. Check logs for details.")