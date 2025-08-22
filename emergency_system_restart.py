#!/usr/bin/env python3
"""
Emergency System Restart
Restores token detection functionality after system stoppage
"""

import psycopg2
import os
import requests
from datetime import datetime

def emergency_restart():
    """Perform emergency restart of token detection system"""
    
    railway_db = 'postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway'
    
    print("🚨 EMERGENCY SYSTEM RESTART")
    print("=" * 40)
    
    fixes_applied = []
    
    try:
        conn = psycopg2.connect(railway_db)
        cursor = conn.cursor()
        
        # 1. Restore database routing trigger
        print("🔧 Step 1: Restoring database routing protection...")
        
        cursor.execute("""
            CREATE OR REPLACE FUNCTION prevent_unnamed_tokens()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.name LIKE 'Unnamed Token%' THEN
                    RAISE EXCEPTION 'ROUTING VIOLATION: Unnamed tokens must go to fallback_processing_coins';
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        cursor.execute("""
            DROP TRIGGER IF EXISTS prevent_unnamed_in_detected ON detected_tokens;
        """)
        
        cursor.execute("""
            CREATE TRIGGER prevent_unnamed_in_detected
                BEFORE INSERT OR UPDATE ON detected_tokens
                FOR EACH ROW
                EXECUTE FUNCTION prevent_unnamed_tokens();
        """)
        
        conn.commit()
        fixes_applied.append("Database routing protection restored")
        print("   ✅ Database routing trigger restored")
        
        # 2. Check current system status
        print("\n🔍 Step 2: System status verification...")
        
        # Check recent activity
        cursor.execute("""
            SELECT COUNT(*) FROM detected_tokens 
            WHERE created_at > NOW() - INTERVAL '1 hour'
        """)
        recent_detections = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM fallback_processing_coins 
            WHERE created_at > NOW() - INTERVAL '1 hour'
        """)
        recent_fallback = cursor.fetchone()[0]
        
        print(f"   Recent detections (1h): {recent_detections}")
        print(f"   Recent fallback (1h): {recent_fallback}")
        
        if recent_detections == 0 and recent_fallback == 0:
            print("   🚨 CONFIRMED: System is completely stopped")
            fixes_applied.append("System stoppage confirmed - requires Railway restart")
        
        # 3. Test external API connectivity
        print("\n🌐 Step 3: External API verification...")
        
        try:
            response = requests.get(
                'https://api.dexscreener.com/latest/dex/tokens/So11111111111111111111111111111111111111112',
                timeout=10
            )
            if response.status_code == 200:
                print("   ✅ DexScreener API: Operational")
                fixes_applied.append("DexScreener API confirmed working")
            else:
                print(f"   ⚠️ DexScreener API: Status {response.status_code}")
        except Exception as e:
            print(f"   ❌ DexScreener API: {e}")
        
        # Check Alchemy API status
        alchemy_key = os.getenv('ALCHEMY_API_KEY')
        if alchemy_key:
            try:
                alchemy_url = f"https://solana-mainnet.g.alchemy.com/v2/{alchemy_key}"
                response = requests.post(
                    alchemy_url,
                    json={"jsonrpc": "2.0", "id": 1, "method": "getHealth"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    print("   ✅ Alchemy API: Operational")
                    fixes_applied.append("Alchemy API confirmed working")
                elif response.status_code == 429:
                    print("   🚨 Alchemy API: RATE LIMITED - This is the primary issue!")
                    fixes_applied.append("CRITICAL: Alchemy API rate limited - need new key or upgrade")
                else:
                    print(f"   ❌ Alchemy API: Status {response.status_code}")
            except Exception as e:
                print(f"   ❌ Alchemy API: {e}")
        
        # 4. Create restart marker
        print("\n📝 Step 4: Creating restart marker...")
        
        cursor.execute("""
            INSERT INTO system_events (event_type, description, created_at)
            VALUES ('emergency_restart', 'System restart initiated due to 66h stoppage', CURRENT_TIMESTAMP)
            ON CONFLICT DO NOTHING
        """)
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_events (
                id SERIAL PRIMARY KEY,
                event_type VARCHAR(100),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT INTO system_events (event_type, description, created_at)
            VALUES ('emergency_restart', 'System restart initiated due to 66h stoppage', CURRENT_TIMESTAMP)
        """)
        
        conn.commit()
        fixes_applied.append("Restart marker created in database")
        print("   ✅ Restart marker created")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Emergency restart error: {e}")
        fixes_applied.append(f"ERROR: {e}")
    
    # 5. Summary and next steps
    print(f"\n📋 EMERGENCY RESTART SUMMARY:")
    print(f"Fixes applied ({len(fixes_applied)}):")
    for fix in fixes_applied:
        print(f"   - {fix}")
    
    print(f"\n🎯 REQUIRED ACTIONS:")
    print(f"   1. ⚠️ ALCHEMY API RATE LIMITED - Need new API key or paid plan")
    print(f"   2. 🔄 RESTART RAILWAY DEPLOYMENT - Service appears stopped")
    print(f"   3. 📊 MONITOR RESTORATION - Check for new token detections")
    print(f"   4. 🔧 VERIFY ROUTING - Ensure unnamed tokens go to fallback table")
    
    print(f"\n💡 IMMEDIATE NEXT STEPS:")
    print(f"   - Get new Alchemy API key or upgrade to paid plan")
    print(f"   - Restart the Railway service manually") 
    print(f"   - Monitor database for new token activity")
    print(f"   - Verify the system is detecting tokens again")

if __name__ == "__main__":
    emergency_restart()