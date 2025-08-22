#!/usr/bin/env python3
"""
Front 36 - Railway Health Service
Minimal service for Railway health checks with port conflict resolution
Optimized deployment for Solana Token Scanner Discord Bot
"""

import os
import time
import logging
from flask import Flask, jsonify
from waitress import serve

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'service': 'Railway Token Scanner Health Check'
    })

@app.route('/')
def home():
    return jsonify({
        'status': 'Front 36 Railway Deployment Active',
        'system': 'Solana Token Scanner + Discord Bot',
        'features': [
            'PumpPortal WebSocket monitoring',
            'Multi-platform token detection (Pump.fun + LetsBonk)', 
            'Discord bot with 35+ commands',
            'Mobile-optimized contract address copying',
            'Railway deployment ready'
        ],
        'deployment_guide': '/status'
    })

@app.route('/status')
def status():
    return jsonify({
        'running': True,
        'database_available': bool(os.getenv('DATABASE_URL')),
        'discord_token_available': bool(os.getenv('DISCORD_TOKEN')),
        'main_services': {
            'token_monitoring': 'Use pumpportal_server.py',
            'discord_bot': 'Use complete_discord_bot_with_commands.py',
            'mobile_copy_fix': 'Implemented - single backticks in description'
        },
        'railway_deployment': {
            'entry_point': 'python3 railway_health_only.py',
            'health_check': '/health',
            'status_check': '/status'
        },
        'timestamp': time.time()
    })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    logger.info(f"🚀 Railway Health Service starting on port {port}")
    serve(app, host='0.0.0.0', port=port)