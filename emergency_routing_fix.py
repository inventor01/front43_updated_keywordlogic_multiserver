#!/usr/bin/env python3
"""
Emergency Routing Fix for Railway
Applies aggressive routing validation directly in the database
"""

import psycopg2
import os

def apply_emergency_routing_fix():
    """Apply database-level routing validation"""
    
    database_url = 'postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway'
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("🚨 APPLYING EMERGENCY ROUTING FIX")
        print("=" * 40)
        
        # Step 1: Create database trigger to prevent unnamed tokens in detected_tokens
        cursor.execute("""
            CREATE OR REPLACE FUNCTION prevent_unnamed_tokens()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.name LIKE 'Unnamed Token%' THEN
                    RAISE EXCEPTION 'ROUTING VIOLATION: Unnamed tokens must go to fallback_processing_coins, not detected_tokens';
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Drop trigger if exists and recreate
        cursor.execute("""
            DROP TRIGGER IF EXISTS prevent_unnamed_in_detected ON detected_tokens;
        """)
        
        cursor.execute("""
            CREATE TRIGGER prevent_unnamed_in_detected
                BEFORE INSERT OR UPDATE ON detected_tokens
                FOR EACH ROW
                EXECUTE FUNCTION prevent_unnamed_tokens();
        """)
        
        print("✅ Database trigger created to block unnamed tokens")
        
        # Step 2: Move existing violations
        cursor.execute("""
            INSERT INTO fallback_processing_coins 
            (contract_address, token_name, processing_status, created_at, retry_count)
            SELECT address, name, 'name_pending', created_at, 0
            FROM detected_tokens 
            WHERE name LIKE 'Unnamed Token%'
            ON CONFLICT (contract_address) DO NOTHING
        """)
        
        moved = cursor.rowcount
        
        # Step 3: Remove violations from detected_tokens
        cursor.execute("""
            DELETE FROM detected_tokens 
            WHERE name LIKE 'Unnamed Token%'
        """)
        
        deleted = cursor.rowcount
        
        conn.commit()
        
        print(f"📦 Moved {moved} tokens to fallback_processing_coins")
        print(f"🗑️ Removed {deleted} violations from detected_tokens")
        print(f"🛡️ Database-level protection now active")
        
        # Step 4: Test the trigger
        try:
            cursor.execute("""
                INSERT INTO detected_tokens (address, name, symbol, platform, status)
                VALUES ('TEST_TRIGGER_123', 'Unnamed Token TEST', 'TEST', 'test', 'detected')
            """)
            conn.commit()
            print(f"❌ TRIGGER FAILED - Test insertion succeeded")
        except Exception as trigger_error:
            print(f"✅ TRIGGER WORKING - Test insertion blocked: {trigger_error}")
            conn.rollback()
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Emergency fix failed: {e}")
        return False

if __name__ == "__main__":
    success = apply_emergency_routing_fix()
    
    if success:
        print(f"\n🎯 EMERGENCY FIX APPLIED SUCCESSFULLY")
        print(f"💡 This provides database-level protection against routing violations")
        print(f"🔄 Railway deployment should now respect proper token routing")
    else:
        print(f"\n❌ EMERGENCY FIX FAILED")
        print(f"🔧 Manual intervention required")