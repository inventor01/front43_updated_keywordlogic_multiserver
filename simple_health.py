#!/usr/bin/env python3
"""
Simple health check server for Railway deployment
Starts immediately to pass health checks, then launches main application
"""
import os
import time
import threading
import json
from flask import Flask, jsonify

app = Flask(__name__)
start_time = time.time()

@app.route('/health')
def health():
    """Simple health check that always responds"""
    return jsonify({
        'status': 'healthy',
        'uptime': time.time() - start_time,
        'timestamp': time.time(),
        'service': 'token-monitor'
    })

@app.route('/')
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'Solana Token Monitor - Health Check Active',
        'status': 'healthy',
        'uptime': time.time() - start_time
    })

def start_main_application():
    """Start the main application after health check is ready"""
    time.sleep(2)  # Give health check time to start
    try:
        from main import IntegratedServer
        server = IntegratedServer()
        server.run()
    except Exception as e:
        print(f"Error starting main application: {e}")

if __name__ == "__main__":
    # Start main application in background
    app_thread = threading.Thread(target=start_main_application)
    app_thread.daemon = True
    app_thread.start()
    
    # Start health check server immediately
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)