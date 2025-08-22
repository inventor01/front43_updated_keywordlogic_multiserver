#!/usr/bin/env python3
"""
Fix Database Schema Mismatch - Critical Production Fix
Resolves 'column name_status does not exist' error

The error occurs because the code tries to insert 'name_status' column
which doesn't exist in the detected_tokens table.
"""

import psycopg2
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_schema():
    """Fix the database schema mismatch by updating table structure"""
    try:
        # Connect to Railway PostgreSQL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL not found in environment")
            return False
            
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        logger.info("🔧 Analyzing detected_tokens table structure...")
        
        # Check current columns
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'detected_tokens' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        column_names = [col[0] for col in columns]
        
        logger.info(f"📋 Current columns: {column_names}")
        
        # Add missing name_status column if it doesn't exist
        if 'name_status' not in column_names:
            logger.info("➕ Adding missing name_status column...")
            cursor.execute("""
                ALTER TABLE detected_tokens 
                ADD COLUMN IF NOT EXISTS name_status VARCHAR(50) DEFAULT 'resolved'
            """)
            logger.info("✅ Added name_status column")
        
        # Ensure we have proper indexes
        logger.info("🔗 Creating/updating indexes...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_detected_tokens_address 
            ON detected_tokens(address)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_detected_tokens_contract 
            ON detected_tokens(contract_address)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_detected_tokens_status 
            ON detected_tokens(status)
        """)
        
        # Update any NULL values in required columns
        logger.info("🔄 Updating NULL values...")
        cursor.execute("""
            UPDATE detected_tokens 
            SET status = 'detected' 
            WHERE status IS NULL
        """)
        cursor.execute("""
            UPDATE detected_tokens 
            SET platform = 'LetsBonk' 
            WHERE platform IS NULL
        """)
        cursor.execute("""
            UPDATE detected_tokens 
            SET name_status = 'resolved' 
            WHERE name_status IS NULL
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Database schema fixed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to fix database schema: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Starting database schema fix...")
    success = fix_database_schema()
    if success:
        logger.info("🎉 Database schema fix completed successfully")
    else:
        logger.error("💥 Database schema fix failed")