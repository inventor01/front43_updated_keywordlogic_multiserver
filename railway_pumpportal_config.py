#!/usr/bin/env python3
"""
Railway Configuration for PumpPortal Integration
Setup script for deploying PumpPortal-based token detection
"""

import os
import psycopg2
import json

def setup_pumpportal_database():
    """Setup database for PumpPortal integration"""
    
    railway_db = 'postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway'
    
    print("🔧 SETTING UP PUMPPORTAL DATABASE INTEGRATION")
    print("=" * 55)
    
    try:
        conn = psycopg2.connect(railway_db)
        cursor = conn.cursor()
        
        # 1. Add data_source column to track token source
        print("📊 Adding data source tracking...")
        
        try:
            cursor.execute("""
                ALTER TABLE detected_tokens 
                ADD COLUMN IF NOT EXISTS data_source VARCHAR(50) DEFAULT 'alchemy'
            """)
            print("   ✅ Added data_source to detected_tokens")
        except Exception as e:
            print(f"   ⚠️ detected_tokens column: {e}")
        
        try:
            cursor.execute("""
                ALTER TABLE fallback_processing_coins 
                ADD COLUMN IF NOT EXISTS data_source VARCHAR(50) DEFAULT 'alchemy'
            """)
            print("   ✅ Added data_source to fallback_processing_coins")
        except Exception as e:
            print(f"   ⚠️ fallback_processing_coins column: {e}")
        
        # 2. Create PumpPortal monitoring table
        print("📡 Setting up PumpPortal monitoring...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pumpportal_status (
                id SERIAL PRIMARY KEY,
                connection_status VARCHAR(20),
                last_heartbeat TIMESTAMP,
                tokens_processed INTEGER DEFAULT 0,
                last_token_address VARCHAR(100),
                last_token_name VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ Created pumpportal_status table")
        
        # 3. Insert initial status record
        cursor.execute("""
            INSERT INTO pumpportal_status (connection_status, last_heartbeat, tokens_processed)
            VALUES ('initializing', CURRENT_TIMESTAMP, 0)
            ON CONFLICT DO NOTHING
        """)
        
        # 4. Create data source index for performance
        print("⚡ Optimizing for multiple data sources...")
        
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_detected_tokens_data_source 
                ON detected_tokens(data_source, created_at DESC)
            """)
            print("   ✅ Created data_source index on detected_tokens")
        except Exception as e:
            print(f"   ⚠️ Index creation: {e}")
        
        # 5. Update routing trigger to handle PumpPortal data
        print("🔧 Updating routing protection for PumpPortal...")
        
        cursor.execute("""
            CREATE OR REPLACE FUNCTION prevent_unnamed_tokens()
            RETURNS TRIGGER AS $$
            BEGIN
                -- Allow PumpPortal tokens with better validation
                IF NEW.data_source = 'pumpportal' THEN
                    -- PumpPortal tokens can have different naming patterns
                    IF NEW.name LIKE 'Unnamed Token%' OR NEW.name = 'Unknown' THEN
                        RAISE EXCEPTION 'ROUTING VIOLATION: Invalid token name from PumpPortal: %', NEW.name;
                    END IF;
                ELSE
                    -- Standard validation for other sources
                    IF NEW.name LIKE 'Unnamed Token%' THEN
                        RAISE EXCEPTION 'ROUTING VIOLATION: Unnamed tokens must go to fallback_processing_coins';
                    END IF;
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        print("   ✅ Updated routing trigger for PumpPortal compatibility")
        
        conn.commit()
        
        # 6. Verify setup
        print("✅ Verifying PumpPortal database setup...")
        
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'detected_tokens' AND column_name = 'data_source'
        """)
        
        if cursor.fetchone():
            print("   ✅ Data source tracking: Active")
        else:
            print("   ❌ Data source tracking: Failed")
        
        cursor.execute("""
            SELECT COUNT(*) FROM pumpportal_status
        """)
        
        status_count = cursor.fetchone()[0]
        print(f"   ✅ PumpPortal status table: {status_count} records")
        
        cursor.close()
        conn.close()
        
        print(f"\n🎯 PUMPPORTAL DATABASE SETUP COMPLETE")
        print(f"✅ Ready for PumpPortal token detection")
        print(f"🔄 Can now track tokens from multiple sources")
        print(f"📊 Enhanced routing validation for PumpPortal data")
        
        return True
        
    except Exception as e:
        print(f"❌ Database setup error: {e}")
        return False

def create_pumpportal_environment():
    """Create environment configuration for PumpPortal"""
    
    print(f"\n⚙️ PUMPPORTAL ENVIRONMENT CONFIGURATION")
    print(f"=" * 45)
    
    env_vars = {
        'PUMPPORTAL_ENABLED': 'true',
        'PUMPPORTAL_WEBSOCKET_URL': 'wss://pumpportal.fun/api/data',
        'TOKEN_DETECTION_SOURCE': 'pumpportal',
        'FALLBACK_TO_DEXSCREENER': 'true',
        'PUMPPORTAL_RECONNECT_DELAY': '5',
        'PUMPPORTAL_HEARTBEAT_TIMEOUT': '120'
    }
    
    print(f"Required environment variables:")
    for key, value in env_vars.items():
        print(f"   {key}={value}")
    
    # Create .env.pumpportal file
    try:
        with open('.env.pumpportal', 'w') as f:
            f.write("# PumpPortal Integration Environment Variables\n")
            f.write("# Alternative to rate-limited Alchemy API\n\n")
            
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
            
            f.write("\n# Existing environment variables still needed:\n")
            f.write("# DATABASE_URL=your_railway_database_url\n")
            f.write("# DISCORD_BOT_TOKEN=your_discord_token\n")
        
        print(f"✅ Created .env.pumpportal configuration file")
        
    except Exception as e:
        print(f"❌ Environment file creation error: {e}")

def main():
    """Main setup function"""
    print("🚀 PumpPortal Integration Setup")
    print("Replacing rate-limited Alchemy API with PumpPortal")
    print()
    
    # Setup database
    db_success = setup_pumpportal_database()
    
    # Create environment configuration
    create_pumpportal_environment()
    
    if db_success:
        print(f"\n🎯 SETUP SUMMARY:")
        print(f"✅ Database configured for PumpPortal")
        print(f"✅ Environment variables defined")
        print(f"✅ Routing protection updated")
        print(f"\n🚀 DEPLOYMENT READY:")
        print(f"   1. Use Procfile.pumpportal for Railway deployment")
        print(f"   2. Set environment variables from .env.pumpportal")
        print(f"   3. Deploy pumpportal_server.py as main application")
        print(f"   4. Monitor pumpportal_status table for health")
    else:
        print(f"\n❌ Setup incomplete - resolve database issues first")

if __name__ == "__main__":
    main()