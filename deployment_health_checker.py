#!/usr/bin/env python3
"""
Railway Deployment Health Checker
Diagnoses why token detection has stopped
"""

import psycopg2
import requests
import os
import time
from datetime import datetime, timedelta

class DeploymentHealthChecker:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            self.database_url = 'postgresql://postgres:TAmpBPYHVAnWDQaLeftFUmpDIBReQHqi@crossover.proxy.rlwy.net:40211/railway'
    
    def check_detection_pipeline(self):
        """Check the entire token detection pipeline"""
        print("🔍 COMPREHENSIVE PIPELINE HEALTH CHECK")
        print("=" * 50)
        
        issues = []
        
        # 1. Database connectivity and recent activity
        db_issues = self.check_database_health()
        issues.extend(db_issues)
        
        # 2. External API connectivity
        api_issues = self.check_api_health()
        issues.extend(api_issues)
        
        # 3. Detection timeline analysis
        timeline_issues = self.check_detection_timeline()
        issues.extend(timeline_issues)
        
        # 4. System configuration
        config_issues = self.check_system_configuration()
        issues.extend(config_issues)
        
        return issues
    
    def check_database_health(self):
        """Check database connectivity and recent activity"""
        issues = []
        
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            print("\n📊 DATABASE HEALTH:")
            
            # Check recent detection activity
            cursor.execute("""
                SELECT COUNT(*), MAX(created_at) as latest
                FROM detected_tokens 
                WHERE created_at > NOW() - INTERVAL '6 hours'
            """)
            
            detected_count, latest_detected = cursor.fetchone()
            
            if detected_count == 0:
                issues.append("NO_RECENT_DETECTIONS - No tokens detected in 6 hours")
                print(f"   ❌ No detections in 6 hours")
            else:
                print(f"   ✅ Recent detections: {detected_count} (latest: {latest_detected})")
            
            # Check fallback processing
            cursor.execute("""
                SELECT COUNT(*), MAX(created_at) as latest
                FROM fallback_processing_coins 
                WHERE created_at > NOW() - INTERVAL '2 hours'
            """)
            
            fallback_count, latest_fallback = cursor.fetchone()
            print(f"   📦 Fallback processing: {fallback_count} tokens (latest: {latest_fallback})")
            
            # Check for database triggers (our routing protection)
            cursor.execute("""
                SELECT trigger_name 
                FROM information_schema.triggers 
                WHERE event_object_table = 'detected_tokens'
                AND trigger_name = 'prevent_unnamed_in_detected'
            """)
            
            trigger_exists = cursor.fetchone()
            if trigger_exists:
                print(f"   ✅ Routing protection trigger: Active")
            else:
                issues.append("MISSING_ROUTING_TRIGGER - Database routing protection not active")
                print(f"   ⚠️ Routing protection trigger: Missing")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            issues.append(f"DATABASE_ERROR - {e}")
            print(f"   ❌ Database error: {e}")
        
        return issues
    
    def check_api_health(self):
        """Check external API connectivity"""
        issues = []
        
        print("\n🌐 EXTERNAL API HEALTH:")
        
        # Test DexScreener API
        try:
            response = requests.get(
                'https://api.dexscreener.com/latest/dex/tokens/So11111111111111111111111111111111111111112',
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"   ✅ DexScreener API: OK")
            else:
                issues.append(f"DEXSCREENER_ERROR - Status {response.status_code}")
                print(f"   ❌ DexScreener API: Status {response.status_code}")
                
        except Exception as e:
            issues.append(f"DEXSCREENER_TIMEOUT - {e}")
            print(f"   ❌ DexScreener API: {e}")
        
        # Test Alchemy connectivity (basic check)
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
                    print(f"   ✅ Alchemy API: OK")
                else:
                    issues.append(f"ALCHEMY_ERROR - Status {response.status_code}")
                    print(f"   ❌ Alchemy API: Status {response.status_code}")
                    
            except Exception as e:
                issues.append(f"ALCHEMY_TIMEOUT - {e}")
                print(f"   ❌ Alchemy API: {e}")
        else:
            issues.append("ALCHEMY_KEY_MISSING - No API key in environment")
            print(f"   ⚠️ Alchemy API: No key in environment")
        
        return issues
    
    def check_detection_timeline(self):
        """Analyze detection timeline for patterns"""
        issues = []
        
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            
            print("\n⏰ DETECTION TIMELINE ANALYSIS:")
            
            # Get last 24 hours of detection activity by hour
            cursor.execute("""
                SELECT 
                    DATE_TRUNC('hour', created_at) as hour,
                    COUNT(*) as detections
                FROM detected_tokens 
                WHERE created_at > NOW() - INTERVAL '24 hours'
                GROUP BY DATE_TRUNC('hour', created_at)
                ORDER BY hour DESC
                LIMIT 8
            """)
            
            hourly_stats = cursor.fetchall()
            
            if not hourly_stats:
                issues.append("NO_DETECTIONS_24H - No detections in past 24 hours")
                print(f"   ❌ No detections in past 24 hours")
            else:
                print(f"   📈 Hourly detection pattern (last 8 hours):")
                for hour, count in hourly_stats:
                    print(f"      {hour.strftime('%Y-%m-%d %H:00')}: {count} tokens")
                
                # Check if there's been a recent drop-off
                recent_hours = [count for _, count in hourly_stats[:3]]
                if all(count == 0 for count in recent_hours):
                    issues.append("DETECTION_STOPPED - No detections in last 3 hours")
                    print(f"   ⚠️ Detection appears to have stopped in last 3 hours")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            issues.append(f"TIMELINE_CHECK_ERROR - {e}")
            print(f"   ❌ Timeline check error: {e}")
        
        return issues
    
    def check_system_configuration(self):
        """Check system configuration and environment"""
        issues = []
        
        print("\n⚙️ SYSTEM CONFIGURATION:")
        
        # Check essential environment variables
        required_vars = ['DATABASE_URL', 'DISCORD_BOT_TOKEN']
        optional_vars = ['ALCHEMY_API_KEY', 'BROWSERCAT_API_KEY']
        
        for var in required_vars:
            if os.getenv(var):
                print(f"   ✅ {var}: Set")
            else:
                issues.append(f"MISSING_ENV_VAR - {var} not set")
                print(f"   ❌ {var}: Missing")
        
        for var in optional_vars:
            if os.getenv(var):
                print(f"   ✅ {var}: Set")
            else:
                print(f"   ⚠️ {var}: Not set (optional)")
        
        return issues
    
    def suggest_fixes(self, issues):
        """Suggest fixes for identified issues"""
        print("\n🔧 SUGGESTED FIXES:")
        print("=" * 30)
        
        if not issues:
            print("✅ No issues detected - system appears healthy")
            return
        
        fix_suggestions = {
            "NO_RECENT_DETECTIONS": "Check if the token scanning service is running on Railway",
            "MISSING_ROUTING_TRIGGER": "Re-run the emergency routing fix to restore database protection",
            "DATABASE_ERROR": "Check Railway database connectivity and permissions",
            "DEXSCREENER_ERROR": "DexScreener API may be down - monitor status",
            "ALCHEMY_ERROR": "Check Alchemy API key and quota limits",
            "ALCHEMY_KEY_MISSING": "Add ALCHEMY_API_KEY to Railway environment variables",
            "DETECTION_STOPPED": "Restart the Railway deployment or check service logs",
            "NO_DETECTIONS_24H": "System may be completely down - immediate restart needed"
        }
        
        for issue in issues:
            issue_type = issue.split(' - ')[0]
            if issue_type in fix_suggestions:
                print(f"❌ {issue}")
                print(f"   💡 {fix_suggestions[issue_type]}")
            else:
                print(f"❌ {issue}")
                print(f"   💡 Manual investigation required")

if __name__ == "__main__":
    checker = DeploymentHealthChecker()
    issues = checker.check_detection_pipeline()
    checker.suggest_fixes(issues)
    
    if issues:
        print(f"\n🚨 HEALTH CHECK SUMMARY: {len(issues)} issues found")
        print("System requires attention to restore token detection")
    else:
        print(f"\n✅ HEALTH CHECK SUMMARY: System appears healthy")
        print("Token detection should be working normally")