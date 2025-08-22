#!/usr/bin/env python3
"""
Check Railway deployment status and simulate log analysis
"""

import requests
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_deployment_health(url):
    """Check if the Railway deployment is responding"""
    
    logger.info(f"🔍 CHECKING RAILWAY DEPLOYMENT: {url}")
    logger.info("=" * 60)
    
    endpoints_to_test = [
        '/',
        '/status', 
        '/fallback_tokens',
        '/health'
    ]
    
    results = {}
    
    for endpoint in endpoints_to_test:
        full_url = f"https://{url}{endpoint}"
        logger.info(f"🌐 Testing: {endpoint}")
        
        try:
            response = requests.get(full_url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    results[endpoint] = {
                        'status': 'SUCCESS',
                        'response_time': response.elapsed.total_seconds(),
                        'data': data
                    }
                    logger.info(f"✅ {endpoint}: SUCCESS ({response.elapsed.total_seconds():.2f}s)")
                    
                    # Log key information
                    if endpoint == '/':
                        if 'features' in data:
                            logger.info(f"   Features: {len(data['features'])} active")
                        if 'statistics' in data:
                            stats = data['statistics']
                            logger.info(f"   Database: {stats.get('total_tokens', 0)} total tokens")
                            
                    elif endpoint == '/status':
                        logger.info(f"   Running: {data.get('running', False)}")
                        logger.info(f"   Resolver: {data.get('resolver_active', False)}")
                        logger.info(f"   Monitor: {data.get('monitor_active', False)}")
                        
                    elif endpoint == '/fallback_tokens':
                        count = data.get('count', 0)
                        logger.info(f"   Fallback tokens: {count}")
                        if count > 0:
                            logger.info("   Recent fallback tokens found:")
                            for token in data.get('tokens', [])[:3]:
                                logger.info(f"     • {token.get('address', '')[:15]}... - {token.get('status', 'unknown')}")
                
                except json.JSONDecodeError:
                    results[endpoint] = {
                        'status': 'SUCCESS_TEXT',
                        'response_time': response.elapsed.total_seconds(),
                        'content': response.text[:200]
                    }
                    logger.info(f"✅ {endpoint}: SUCCESS (text response)")
                    
            else:
                results[endpoint] = {
                    'status': 'ERROR',
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds()
                }
                logger.warning(f"⚠️ {endpoint}: HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            results[endpoint] = {'status': 'TIMEOUT'}
            logger.error(f"❌ {endpoint}: TIMEOUT (>10s)")
            
        except requests.exceptions.ConnectionError:
            results[endpoint] = {'status': 'CONNECTION_ERROR'}
            logger.error(f"❌ {endpoint}: CONNECTION ERROR")
            
        except Exception as e:
            results[endpoint] = {'status': 'EXCEPTION', 'error': str(e)}
            logger.error(f"❌ {endpoint}: {e}")
    
    # Summary
    logger.info("=" * 60)
    logger.info("📊 DEPLOYMENT HEALTH SUMMARY:")
    
    working_endpoints = sum(1 for r in results.values() if r.get('status') in ['SUCCESS', 'SUCCESS_TEXT'])
    total_endpoints = len(results)
    
    logger.info(f"   Working endpoints: {working_endpoints}/{total_endpoints}")
    
    if working_endpoints == total_endpoints:
        logger.info("🎉 DEPLOYMENT STATUS: HEALTHY")
    elif working_endpoints > 0:
        logger.info("⚠️ DEPLOYMENT STATUS: PARTIAL")
    else:
        logger.info("❌ DEPLOYMENT STATUS: DOWN")
    
    return results

def analyze_potential_issues():
    """Analyze potential deployment issues"""
    
    logger.info("=" * 60)
    logger.info("🔍 POTENTIAL DEPLOYMENT ISSUES TO CHECK:")
    logger.info("")
    
    common_issues = [
        {
            'issue': 'Environment Variables Missing',
            'symptoms': 'HTTP 500 errors, database connection failures',
            'solution': 'Check DATABASE_URL, ALCHEMY_API_KEY, DISCORD_TOKEN in Railway dashboard'
        },
        {
            'issue': 'Database Connection Failure', 
            'symptoms': 'App starts but crashes when accessing endpoints',
            'solution': 'Verify PostgreSQL service is running and DATABASE_URL is correct'
        },
        {
            'issue': 'Memory/Resource Limits',
            'symptoms': 'App restarts frequently, timeouts',
            'solution': 'Check Railway metrics for memory usage and upgrade plan if needed'
        },
        {
            'issue': 'Build/Deploy Errors',
            'symptoms': 'Deployment fails, old version still running',
            'solution': 'Check Railway build logs for Python dependency issues'
        },
        {
            'issue': 'Port Binding Issues',
            'symptoms': 'App builds but never becomes accessible',
            'solution': 'Ensure app binds to 0.0.0.0:$PORT, not localhost'
        }
    ]
    
    for i, issue in enumerate(common_issues, 1):
        logger.info(f"{i}. {issue['issue']}")
        logger.info(f"   Symptoms: {issue['symptoms']}")
        logger.info(f"   Solution: {issue['solution']}")
        logger.info("")

def log_check_instructions():
    """Provide instructions for checking Railway logs"""
    
    logger.info("=" * 60)
    logger.info("📋 HOW TO CHECK RAILWAY LOGS:")
    logger.info("")
    logger.info("1. Go to railway.app and sign in")
    logger.info("2. Open your project dashboard")
    logger.info("3. Click on your service (believable-inspiration-production)")
    logger.info("4. Click 'Deployments' tab")
    logger.info("5. Click on the latest deployment")
    logger.info("6. Click 'View Logs' to see real-time logs")
    logger.info("")
    logger.info("🔍 KEY LOG PATTERNS TO LOOK FOR:")
    logger.info("   ✅ 'All tables structure verified/created'")
    logger.info("   ✅ 'Alchemy connection successful'")
    logger.info("   ✅ 'Flask app is running'")
    logger.info("   ❌ 'Database connection failed'")
    logger.info("   ❌ 'ModuleNotFoundError'")
    logger.info("   ❌ 'Environment variable not found'")

if __name__ == "__main__":
    deployment_url = "believable-inspiration-production-a68b.up.railway.app"
    
    logger.info(f"🚀 RAILWAY DEPLOYMENT ANALYSIS")
    logger.info(f"📅 Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    # Test deployment health
    results = check_deployment_health(deployment_url)
    
    # Analyze potential issues
    analyze_potential_issues()
    
    # Provide log checking instructions
    log_check_instructions()
    
    logger.info("=" * 60)
    logger.info("💡 NEXT STEPS:")
    logger.info("1. Check Railway logs using instructions above")
    logger.info("2. Verify environment variables are set")
    logger.info("3. Check database connection status")
    logger.info("4. Monitor resource usage in Railway dashboard")