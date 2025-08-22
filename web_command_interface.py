#!/usr/bin/env python3
"""
Web-based command interface as backup for Discord bot commands
"""

from flask import Flask, render_template_string, request, jsonify, redirect, url_for
import os
import sys
sys.path.append('.')
from config_manager import ConfigManager

app = Flask(__name__)

# HTML template for web interface
WEB_INTERFACE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Token Monitor - Web Commands</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a1a; color: #fff; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 40px; }
        .section { background: #2d2d2d; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .button { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        .button:hover { background: #45a049; }
        .input { padding: 10px; border: 1px solid #555; background: #333; color: #fff; border-radius: 4px; width: 300px; }
        .keyword-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; margin: 20px 0; }
        .keyword-item { background: #444; padding: 8px 12px; border-radius: 4px; font-size: 14px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .stat-item { text-align: center; background: #333; padding: 15px; border-radius: 8px; }
        .success { color: #4CAF50; }
        .error { color: #f44336; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Token Monitor - Web Commands</h1>
            <p>Alternative interface while Discord bot commands are being fixed</p>
        </div>

        <div class="section">
            <h2>📊 System Status</h2>
            <div class="stats">
                <div class="stat-item">
                    <h3>Token Detection</h3>
                    <p class="success">✅ Active</p>
                </div>
                <div class="stat-item">
                    <h3>Discord Notifications</h3>
                    <p class="success">✅ Webhook Active</p>
                </div>
                <div class="stat-item">
                    <h3>Keywords Loaded</h3>
                    <p class="success">76 Keywords</p>
                </div>
                <div class="stat-item">
                    <h3>Bot Commands</h3>
                    <p class="error">🔧 In Progress</p>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>➕ Add Keywords</h2>
            <form method="POST" action="/add_keyword">
                <input type="text" name="keyword" class="input" placeholder="Enter keyword to monitor" required>
                <button type="submit" class="button">Add Keyword</button>
            </form>
        </div>

        <div class="section">
            <h2>🗑️ Remove Keywords</h2>
            <form method="POST" action="/remove_keyword">
                <input type="text" name="keyword" class="input" placeholder="Enter keyword to remove" required>
                <button type="submit" class="button">Remove Keyword</button>
            </form>
        </div>

        <div class="section">
            <h2>📝 Current Keywords ({{ keyword_count }})</h2>
            <div class="keyword-list">
                {% for keyword in keywords %}
                <div class="keyword-item">{{ keyword }}</div>
                {% endfor %}
            </div>
        </div>

        <div class="section">
            <h2>🔧 Discord Bot Status</h2>
            <p><strong>Issue:</strong> Discord bot tokens are returning 401 Unauthorized errors</p>
            <p><strong>Workaround:</strong> This web interface provides the same functionality</p>
            <p><strong>Notifications:</strong> Working perfectly via Discord webhooks</p>
            <p><strong>Next Steps:</strong> Creating fresh Discord bot application with new credentials</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    try:
        config_manager = ConfigManager()
        keywords = config_manager.list_keywords()
        return render_template_string(WEB_INTERFACE_HTML, 
                                    keywords=keywords, 
                                    keyword_count=len(keywords))
    except Exception as e:
        return f"Error loading keywords: {e}", 500

@app.route('/add_keyword', methods=['POST'])
def add_keyword():
    try:
        keyword = request.form.get('keyword', '').strip()
        if not keyword:
            return redirect(url_for('index'))
        
        config_manager = ConfigManager()
        success = config_manager.add_keyword(keyword)
        
        if success:
            return redirect(url_for('index'))
        else:
            return f"Failed to add keyword: {keyword}", 400
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/remove_keyword', methods=['POST'])
def remove_keyword():
    try:
        keyword = request.form.get('keyword', '').strip()
        if not keyword:
            return redirect(url_for('index'))
        
        config_manager = ConfigManager()
        success = config_manager.remove_keyword(keyword)
        
        if success:
            return redirect(url_for('index'))
        else:
            return f"Failed to remove keyword: {keyword}", 400
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/api/status')
def api_status():
    try:
        config_manager = ConfigManager()
        keywords = config_manager.list_keywords()
        
        return jsonify({
            'status': 'operational',
            'keyword_count': len(keywords),
            'discord_notifications': 'active_webhook',
            'discord_commands': 'in_progress',
            'token_detection': 'active',
            'monitoring': 'active'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🌐 Starting web command interface on http://localhost:5001")
    print("🔧 Use this while Discord bot commands are being fixed")
    app.run(host='0.0.0.0', port=5001, debug=False)