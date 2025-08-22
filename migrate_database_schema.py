#!/usr/bin/env python3
"""
Database Schema Migration for Hybrid Token Processing
Adds name_status column to support pending name resolution
"""

import os
import psycopg2
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_database_schema():
    """Add name_status column to detected_tokens table"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not found")
        return False
        
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        logger.info("📡 Connected to Railway PostgreSQL database")
        
        # Check if name_status column exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'detected_tokens' AND column_name = 'name_status'
        """)
        
        if cursor.fetchone():
            logger.info("✅ name_status column already exists")
        else:
            logger.info("🔧 Adding name_status column to detected_tokens table...")
            
            # Add name_status column
            cursor.execute("""
                ALTER TABLE detected_tokens 
                ADD COLUMN name_status VARCHAR(50) DEFAULT 'resolved'
            """)
            
            # Update existing records to have resolved status  
            cursor.execute("""
                UPDATE detected_tokens 
                SET name_status = 'resolved' 
                WHERE name_status IS NULL
            """)
            
            logger.info("✅ name_status column added successfully")
        
        # Create updated_at column if it doesn't exist
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'detected_tokens' AND column_name = 'updated_at'
        """)
        
        if not cursor.fetchone():
            logger.info("🔧 Adding updated_at column...")
            cursor.execute("""
                ALTER TABLE detected_tokens 
                ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            """)
            logger.info("✅ updated_at column added successfully")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("🎉 Database schema migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        return False

def main():
    """Run the database migration"""
    logger.info("🚀 HYBRID TOKEN PROCESSING - Database Schema Migration")
    logger.info("=" * 60)
    
    success = migrate_database_schema()
    
    if success:
        logger.info("✅ Migration complete - database ready for hybrid processing")
    else:
        logger.error("❌ Migration failed - manual intervention required")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())