#!/usr/bin/env python3
"""
Create a minimal GitHub-ready repository with only the critical files Railway needs
This bypasses the 2.59GB push issue by creating a clean, focused deployment package
"""

import os
import shutil
import subprocess

# Critical files Railway needs (confirmed missing from error logs)
CRITICAL_FILES = [
    'alchemy_letsbonk_scraper.py',
    'new_token_only_monitor.py', 
    'enhanced_letsbonk_scraper.py',
    'automated_link_extractor.py',
    'speed_optimized_monitor.py',
    'undo_manager.py',
    'token_recovery_system.py',
    'age_validation_fix.py',
    'enhanced_extraction_integration.py',
    'system_monitoring_integration.py',
    'keyword_attribution.py',
    'uptime_manager.py',
    'trading_engine.py'
]

# Core deployment files (already on GitHub)
DEPLOYMENT_FILES = [
    'alchemy_server.py',
    'fast_startup_server.py',
    'config_manager.py',
    'discord_notifier.py',
    'auto_keyword_sync.py',
    'auto_sell_monitor.py',
    'auto_sniper.py',
    'config.py',
    'token_link_validator.py',
    'market_data_api.py',
    'webhook_discord_notifier.py',
    'requirements.txt',
    'railway.toml',
    'Procfile',
    '.env.example'
]

def create_clean_repo():
    """Create a clean repository with only essential files"""
    
    # Create clean directory
    clean_dir = 'railway_deployment_clean'
    if os.path.exists(clean_dir):
        shutil.rmtree(clean_dir)
    os.makedirs(clean_dir)
    
    print(f"📁 Created clean directory: {clean_dir}")
    
    # Copy critical missing files
    missing_count = 0
    for file in CRITICAL_FILES:
        if os.path.exists(file):
            shutil.copy2(file, clean_dir)
            print(f"✅ Copied critical file: {file}")
        else:
            print(f"❌ Missing critical file: {file}")
            missing_count += 1
    
    # Copy deployment files
    for file in DEPLOYMENT_FILES:
        if os.path.exists(file):
            shutil.copy2(file, clean_dir)
            print(f"✅ Copied deployment file: {file}")
    
    print(f"\n📊 Summary:")
    print(f"   • Critical files: {len(CRITICAL_FILES) - missing_count}/{len(CRITICAL_FILES)}")
    print(f"   • Deployment files: {len([f for f in DEPLOYMENT_FILES if os.path.exists(f)])}")
    print(f"   • Total files ready: {len(os.listdir(clean_dir))}")
    
    if missing_count == 0:
        print(f"\n🎯 All critical files present! Ready for deployment.")
        print(f"📦 Package location: {clean_dir}/")
        print(f"\n🚀 Next steps:")
        print(f"   1. Upload contents of '{clean_dir}/' to GitHub manually")
        print(f"   2. Railway will auto-deploy within 2-3 minutes")
        print(f"   3. Import errors will be resolved")
    else:
        print(f"\n⚠️  Missing {missing_count} critical files - deployment will still fail")
    
    return clean_dir

if __name__ == "__main__":
    create_clean_repo()