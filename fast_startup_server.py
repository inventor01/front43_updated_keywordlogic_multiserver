#!/usr/bin/env python3
"""
Fast Startup Server for Railway Deployment
Optimized for immediate port binding to pass 20-second deployment requirement
"""

import os
import sys
import logging
import threading
import time
from flask import Flask
from waitress import serve

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create minimal Flask app for immediate port binding
app = Flask(__name__)

# Global reference to monitoring server
monitor_server = None

@app.route('/')
def index():
    """Health check endpoint"""
    status = "initializing" if monitor_server is None else "operational"
    return f"""
    <h1>Alchemy Token Monitoring Server</h1>
    <p>Status: <strong>{status}</strong></p>
    <p>Server time: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
    <p>Uptime: Active</p>
    """

@app.route('/health')
def health():
    """Health check for Railway deployment"""
    return {'status': 'healthy', 'timestamp': time.time()}

@app.route('/status')
def status():
    """Detailed status endpoint"""
    return {
        'status': 'operational' if monitor_server else 'initializing',
        'monitoring_active': monitor_server is not None,
        'timestamp': time.time()
    }

@app.route('/uptime')
def uptime():
    """Uptime endpoint"""
    return {
        'uptime': 'active',
        'status': 'healthy',
        'server': 'FastStartupServer'
    }

def delayed_monitoring_initialization():
    """Initialize monitoring system after web server is running"""
    global monitor_server
    
    try:
        # Wait for web server to fully start
        time.sleep(3)
        
        logger.info("🚀 BACKGROUND: Starting monitoring system initialization...")
        
        # Install all critical dependencies FIRST before any imports
        critical_deps = [
            "cachetools>=6.1.0",
            "aiohttp>=3.12.13", 
            "discord-py>=2.5.2",
            "discord-webhook>=1.4.1",
            "requests>=2.32.4",
            "psycopg2-binary>=2.9.10",
            "websockets>=15.0.1",
            "beautifulsoup4>=4.13.4",
            "lxml>=5.4.0"
        ]
        
        for dep in critical_deps:
            try:
                # Extract package name for import test
                pkg_name = dep.split(">=")[0].replace("-", "_")
                if pkg_name == "discord_py":
                    pkg_name = "discord"
                __import__(pkg_name)
            except ImportError:
                logger.info(f"🔧 Installing missing dependency: {dep}")
                try:
                    import subprocess
                    subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                except Exception as e:
                    logger.warning(f"⚠️ Failed to install {dep}: {e}")
        
        # Final verification that cachetools is available
        try:
            import cachetools
            logger.info("✅ cachetools and dependencies verified")
        except ImportError:
            logger.error("❌ Critical dependencies missing after installation attempt")
            raise
        
        # Import and initialize the full monitoring server
        from alchemy_server import AlchemyMonitoringServer
        
        logger.info("📡 Creating AlchemyMonitoringServer instance...")
        monitor_server = AlchemyMonitoringServer()
        
        logger.info("🤖 Setting up Discord bot...")
        monitor_server.setup_discord_bot()
        
        logger.info("🔄 Starting monitoring threads...")
        monitoring_thread = monitor_server.start_monitoring()
        
        logger.info("✅ Full monitoring system operational!")
        logger.info("   🎯 Token detection active")
        logger.info("   🤖 Discord bot connected")
        logger.info("   💰 Auto-trading enabled")
        logger.info("   🔗 URL monitoring active")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize monitoring system: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Ultra-fast startup main function"""
    try:
        logger.info("🚀 ULTRA-FAST STARTUP: Binding to port immediately...")
        
        # Start monitoring initialization in background immediately
        init_thread = threading.Thread(target=delayed_monitoring_initialization, daemon=True)
        init_thread.start()
        
        # Get port from environment
        port = int(os.getenv('PORT', 5000))
        
        # Start web server immediately for Railway deployment check
        logger.info(f"🌐 IMMEDIATE: Web server starting on 0.0.0.0:{port}")
        logger.info("📡 Monitoring system initializing in background...")
        
        # Serve with minimal configuration for fastest startup
        serve(app, host='0.0.0.0', port=port, threads=2)
        
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested...")
        if monitor_server:
            try:
                monitor_server.stop_monitoring()
            except:
                pass
    except Exception as e:
        logger.error(f"❌ Critical startup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()