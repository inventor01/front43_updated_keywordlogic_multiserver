#!/usr/bin/env python3
"""
Railway Database Setup Script
Creates the necessary tables for the Discord bot keyword monitoring system.
"""

import psycopg2
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_database_tables():
    """Create all necessary tables for the Discord bot system"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable not found")
        return False
        
    try:
        # Connect to Railway PostgreSQL
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        logger.info("📡 Connected to Railway PostgreSQL database")
        
        # Create all necessary tables for the complete system
        
        # 1. Keywords table (Discord bot keyword management)
        logger.info("🛠️ Creating keywords table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS keywords (
            id SERIAL PRIMARY KEY,
            keyword VARCHAR(255) NOT NULL,
            user_id VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        
        # 2. Detected tokens table (stores all found tokens before they hit exchanges)
        logger.info("🛠️ Creating detected_tokens table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS detected_tokens (
            id SERIAL PRIMARY KEY,
            address VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(500),
            symbol VARCHAR(100),
            platform VARCHAR(100) DEFAULT 'pump.fun',
            status VARCHAR(50) DEFAULT 'detected',
            name_status VARCHAR(50) DEFAULT 'resolved',
            matched_keywords TEXT[],
            social_links JSONB,
            detection_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        
        # 3. Notified tokens table (prevents duplicate notifications)
        logger.info("🛠️ Creating notified_tokens table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS notified_tokens (
            id SERIAL PRIMARY KEY,
            token_address VARCHAR(255) NOT NULL,
            token_name VARCHAR(500),
            notification_type VARCHAR(100) DEFAULT 'discord',
            notified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            user_id VARCHAR(255) DEFAULT 'system',
            UNIQUE(token_address, notification_type, user_id)
        );
        ''')
        
        # 4. Keyword attribution table (tracks keyword performance)
        logger.info("🛠️ Creating keyword_attribution table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS keyword_attribution (
            id SERIAL PRIMARY KEY,
            keyword VARCHAR(255) NOT NULL,
            user_id VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            deactivated_reason VARCHAR(255),
            total_matches INTEGER DEFAULT 0,
            successful_notifications INTEGER DEFAULT 0
        );
        ''')
        
        # 5. Connected wallets table (for trading integration)
        logger.info("🛠️ Creating connected_wallets table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS connected_wallets (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            wallet_address VARCHAR(255) NOT NULL,
            encrypted_private_key TEXT,
            connected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP WITH TIME ZONE,
            is_active BOOLEAN DEFAULT TRUE,
            UNIQUE(user_id, wallet_address)
        );
        ''')
        
        # 6. Link sniper configs table (for URL-based monitoring)
        logger.info("🛠️ Creating link_sniper_configs table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS link_sniper_configs (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            target_link TEXT NOT NULL,
            enabled BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            last_checked TIMESTAMP WITH TIME ZONE,
            check_interval_minutes INTEGER DEFAULT 5,
            max_market_cap BIGINT DEFAULT 1000000
        );
        ''')
        
        # Create comprehensive performance indexes
        logger.info("🔧 Creating performance indexes...")
        
        # Keywords table indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords_user_id ON keywords(user_id);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords_created_at ON keywords(created_at);')
        
        # Detected tokens indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_detected_tokens_address ON detected_tokens(address);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_detected_tokens_timestamp ON detected_tokens(detection_timestamp);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_detected_tokens_platform ON detected_tokens(platform);')
        
        # Notified tokens indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notified_tokens_address ON notified_tokens(token_address);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notified_tokens_user ON notified_tokens(user_id);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notified_tokens_timestamp ON notified_tokens(notified_at);')
        
        # Keyword attribution indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keyword_attribution_user ON keyword_attribution(user_id);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keyword_attribution_keyword ON keyword_attribution(keyword);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keyword_attribution_active ON keyword_attribution(is_active);')
        
        # Connected wallets indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_connected_wallets_user ON connected_wallets(user_id);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_connected_wallets_address ON connected_wallets(wallet_address);')
        
        # Link sniper configs indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_link_sniper_user ON link_sniper_configs(user_id);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_link_sniper_enabled ON link_sniper_configs(enabled);')
        
        # Commit all changes
        conn.commit()
        
        # Verify all tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        all_tables = cursor.fetchall()
        
        logger.info("✅ Database setup completed successfully!")
        logger.info("📋 Created tables:")
        for (table_name,) in all_tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            count = cursor.fetchone()[0]
            logger.info(f"   ✅ {table_name} ({count} records)")
            
        logger.info("🚀 Complete system database ready for:")
        logger.info("   • Discord bot keyword management")
        logger.info("   • Token detection and storage")
        logger.info("   • Notification deduplication")
        logger.info("   • Trading wallet integration")
        logger.info("   • URL monitoring capabilities")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False

if __name__ == "__main__":
    success = create_database_tables()
    if success:
        print("🎉 Railway database is ready for Discord bot deployment!")
    else:
        print("❌ Database setup failed. Check logs for details.")