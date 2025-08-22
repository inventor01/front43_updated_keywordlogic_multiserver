#!/usr/bin/env python3
"""
Start both web server and Discord bot for Railway deployment
This ensures both services run simultaneously on Railway
"""

import subprocess
import threading
import time
import os
import sys

def start_web_server():
    """Start the web server"""
    print("🌐 Starting web server...")
    subprocess.run([sys.executable, "fast_startup_server.py"])

def start_discord_bot():
    """Start the Discord bot"""
    print("🤖 Starting Discord bot...")
    time.sleep(2)  # Small delay to let web server start first
    subprocess.run([sys.executable, "working_discord_bot.py"])

if __name__ == "__main__":
    print("🚀 RAILWAY DEPLOYMENT: Starting both services")
    
    # Start web server in background thread
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    
    # Start Discord bot in main thread (keeps process alive)
    start_discord_bot()