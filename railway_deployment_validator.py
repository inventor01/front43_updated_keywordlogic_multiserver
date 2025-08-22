#!/usr/bin/env python3
"""
Railway Deployment Validator
Checks if the correct routing code is actually deployed on Railway
"""

import psycopg2
import os

class RailwayDeploymentValidator:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            self.database_url = 'postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway'
    
    def validate_routing_enforcement(self):
        """Check if routing validation is actually working"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            print("🔍 RAILWAY DEPLOYMENT VALIDATION")
            print("=" * 50)
            
            # Check total routing violations
            cursor.execute("""
                SELECT COUNT(*) 
                FROM detected_tokens 
                WHERE name LIKE 'Unnamed Token%'
            """)
            
            total_violations = cursor.fetchone()[0]
            
            # Check recent violations (evidence of ongoing problem)
            cursor.execute("""
                SELECT COUNT(*) 
                FROM detected_tokens 
                WHERE name LIKE 'Unnamed Token%'
                AND created_at > NOW() - INTERVAL '1 hour'
            """)
            
            recent_violations = cursor.fetchone()[0]
            
            print(f"📊 ROUTING VIOLATIONS:")
            print(f"   Total unnamed in detected_tokens: {total_violations}")
            print(f"   New violations (1h): {recent_violations}")
            
            if recent_violations > 0:
                print(f"\n❌ DEPLOYMENT ISSUE CONFIRMED:")
                print(f"   Routing validation NOT working on Railway")
                print(f"   {recent_violations} new violations in last hour")
                
                # Show recent violations
                cursor.execute("""
                    SELECT address, name, created_at 
                    FROM detected_tokens 
                    WHERE name LIKE 'Unnamed Token%'
                    AND created_at > NOW() - INTERVAL '1 hour'
                    ORDER BY created_at DESC
                    LIMIT 3
                """)
                
                violations = cursor.fetchall()
                print(f"\n📋 RECENT VIOLATIONS:")
                for addr, name, created in violations:
                    print(f"   {name} ({addr[:12]}...) at {created}")
                
                return False
            else:
                print(f"\n✅ ROUTING APPEARS TO BE WORKING")
                print(f"   No new violations in past hour")
                return True
                
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"Validation error: {e}")
            return False
    
    def force_cleanup_violations(self):
        """Remove current routing violations"""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            # Move unnamed tokens from detected_tokens to fallback_processing_coins
            cursor.execute("""
                INSERT INTO fallback_processing_coins 
                (contract_address, token_name, processing_status, created_at)
                SELECT address, name, 'name_pending', created_at 
                FROM detected_tokens 
                WHERE name LIKE 'Unnamed Token%'
                ON CONFLICT (contract_address) DO NOTHING
            """)
            
            moved = cursor.rowcount
            
            # Remove from detected_tokens
            cursor.execute("""
                DELETE FROM detected_tokens 
                WHERE name LIKE 'Unnamed Token%'
            """)
            
            deleted = cursor.rowcount
            conn.commit()
            
            print(f"🧹 CLEANUP COMPLETED:")
            print(f"   Moved {moved} tokens to fallback_processing_coins")
            print(f"   Removed {deleted} violations from detected_tokens")
            
            cursor.close()
            conn.close()
            
            return deleted
            
        except Exception as e:
            print(f"Cleanup error: {e}")
            return 0

if __name__ == "__main__":
    validator = RailwayDeploymentValidator()
    
    # Check current status
    is_working = validator.validate_routing_enforcement()
    
    if not is_working:
        print(f"\n🔧 ATTEMPTING CLEANUP...")
        cleaned = validator.force_cleanup_violations()
        
        if cleaned > 0:
            print(f"\n✅ Cleaned {cleaned} routing violations")
            print(f"💡 ISSUE: Railway deployment lacks proper routing validation")
            print(f"📋 SOLUTION: Need to redeploy with Front34 routing fixes")
        else:
            print(f"\n⚠️ No violations to clean - issue may be elsewhere")
    else:
        print(f"\n✅ Routing validation appears to be working correctly")