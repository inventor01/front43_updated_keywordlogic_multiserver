#!/usr/bin/env python3
"""
Database migration to update notified_tokens table with proper unique constraint
"""

import psycopg2
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_notified_tokens_table():
    """Update notified_tokens table with proper constraints"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not found")
        return False
        
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        logger.info("📡 Connected to Railway PostgreSQL database")
        
        # Check if notified_tokens table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'notified_tokens'
            )
        """)
        
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            logger.info("🛠️ Creating notified_tokens table...")
            cursor.execute('''
            CREATE TABLE notified_tokens (
                id SERIAL PRIMARY KEY,
                token_address VARCHAR(255) NOT NULL,
                token_name VARCHAR(500),
                notification_type VARCHAR(100) DEFAULT 'discord',
                notified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                user_id VARCHAR(255) DEFAULT 'system',
                UNIQUE(token_address, notification_type, user_id)
            );
            ''')
        else:
            logger.info("🔧 Updating notified_tokens table structure...")
            
            # Add user_id column if it doesn't exist
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'notified_tokens' AND column_name = 'user_id'
            """)
            
            if not cursor.fetchone():
                logger.info("➕ Adding user_id column...")
                cursor.execute('''
                    ALTER TABLE notified_tokens 
                    ADD COLUMN user_id VARCHAR(255) DEFAULT 'system'
                ''')
            
            # Check if unique constraint exists
            cursor.execute("""
                SELECT constraint_name 
                FROM information_schema.table_constraints 
                WHERE table_name = 'notified_tokens' 
                AND constraint_type = 'UNIQUE'
            """)
            
            existing_constraints = cursor.fetchall()
            
            # Drop existing unique constraints and create the correct one
            for constraint in existing_constraints:
                logger.info(f"🗑️ Dropping old constraint: {constraint[0]}")
                cursor.execute(f'ALTER TABLE notified_tokens DROP CONSTRAINT IF EXISTS {constraint[0]}')
            
            # Add the proper unique constraint
            logger.info("✅ Adding proper unique constraint...")
            cursor.execute('''
                ALTER TABLE notified_tokens 
                ADD CONSTRAINT unique_notification_per_user 
                UNIQUE(token_address, notification_type, user_id)
            ''')
        
        # Create indexes for performance
        logger.info("🔧 Creating performance indexes...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notified_tokens_address ON notified_tokens(token_address);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notified_tokens_user ON notified_tokens(user_id);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notified_tokens_timestamp ON notified_tokens(notified_at);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notified_tokens_type ON notified_tokens(notification_type);')
        
        conn.commit()
        
        # Verify table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'notified_tokens' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        logger.info("✅ Updated notified_tokens table structure:")
        for col in columns:
            logger.info(f"   📋 {col[0]} ({col[1]}) - Nullable: {col[2]} - Default: {col[3]}")
        
        cursor.close()
        conn.close()
        
        logger.info("🚀 Notified tokens table ready for duplicate prevention!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database update error: {e}")
        return False

if __name__ == "__main__":
    update_notified_tokens_table()