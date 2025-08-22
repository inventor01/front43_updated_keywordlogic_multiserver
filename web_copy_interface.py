#!/usr/bin/env python3
"""
Web Interface for Mobile Contract Address Copying
Provides a dedicated web page for easy mobile address copying
"""

from flask import Flask, render_template_string, jsonify, request
import psycopg2
import os
import logging

logger = logging.getLogger(__name__)

class WebCopyInterface:
    """Web interface for mobile-friendly contract address copying"""
    
    def __init__(self, app: Flask, database_url: str):
        self.app = app
        self.database_url = database_url
        self.setup_routes()
    
    def setup_routes(self):
        """Setup Flask routes for copy interface"""
        
        @self.app.route('/copy')
        def copy_interface():
            """Main copy interface page"""
            return render_template_string(COPY_INTERFACE_HTML)
        
        @self.app.route('/api/recent-tokens')
        def get_recent_tokens():
            """API endpoint for recent tokens"""
            try:
                conn = psycopg2.connect(self.database_url)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT token_name, token_address, symbol, platform, created_at
                    FROM detected_tokens 
                    WHERE token_name IS NOT NULL 
                    AND token_name != 'Unnamed Token'
                    ORDER BY created_at DESC 
                    LIMIT 20
                """)
                
                tokens = []
                for row in cursor.fetchall():
                    tokens.append({
                        'name': row[0],
                        'address': row[1],
                        'symbol': row[2],
                        'platform': row[3] or 'Unknown',
                        'created_at': row[4].isoformat() if row[4] else None
                    })
                
                cursor.close()
                conn.close()
                
                return jsonify({'tokens': tokens})
                
            except Exception as e:
                logger.error(f"Error fetching recent tokens: {e}")
                return jsonify({'error': 'Failed to fetch tokens'}), 500
        
        @self.app.route('/api/copy-address', methods=['POST'])
        def copy_address_api():
            """API endpoint to get address for copying"""
            data = request.get_json()
            address = data.get('address', '')
            
            return jsonify({
                'address': address,
                'formatted': f"```\n{address}\n```",
                'short': f"{address[:12]}...{address[-12:]}" if len(address) > 24 else address
            })

# HTML Template for mobile copy interface
COPY_INTERFACE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📱 Token Address Copier</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            min-height: 100vh;
            color: white;
        }
        
        .container {
            max-width: 500px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .token-card {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        .token-name {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .token-symbol {
            font-size: 14px;
            opacity: 0.8;
            margin-bottom: 10px;
        }
        
        .address-container {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 8px;
            padding: 10px;
            margin: 10px 0;
        }
        
        .address-text {
            font-family: 'Courier New', monospace;
            font-size: 12px;
            word-break: break-all;
            user-select: all;
            -webkit-user-select: all;
            -moz-user-select: all;
            -ms-user-select: all;
            cursor: text;
            line-height: 1.4;
        }
        
        .copy-btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 5px;
            font-size: 14px;
            cursor: pointer;
            width: 100%;
            margin-top: 10px;
            transition: background 0.3s;
        }
        
        .copy-btn:hover {
            background: #45a049;
        }
        
        .copy-btn:active {
            background: #3d8b40;
        }
        
        .platform-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .pump-fun { background: #1E90FF; }
        .letsbonk { background: #FF8C00; }
        .other { background: #808080; }
        
        .loading {
            text-align: center;
            padding: 20px;
        }
        
        .success-msg {
            background: #4CAF50;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            text-align: center;
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .success-msg.show {
            opacity: 1;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 Token Address Copier</h1>
            <p>Tap any address to select & copy</p>
        </div>
        
        <div id="loading" class="loading">Loading recent tokens...</div>
        <div id="tokens-container"></div>
    </div>

    <script>
        async function loadTokens() {
            try {
                const response = await fetch('/api/recent-tokens');
                const data = await response.json();
                
                const container = document.getElementById('tokens-container');
                const loading = document.getElementById('loading');
                
                loading.style.display = 'none';
                
                if (data.tokens && data.tokens.length > 0) {
                    data.tokens.forEach(token => {
                        const tokenCard = createTokenCard(token);
                        container.appendChild(tokenCard);
                    });
                } else {
                    container.innerHTML = '<p>No recent tokens found</p>';
                }
                
            } catch (error) {
                console.error('Error loading tokens:', error);
                document.getElementById('loading').textContent = 'Error loading tokens';
            }
        }
        
        function createTokenCard(token) {
            const card = document.createElement('div');
            card.className = 'token-card';
            
            const platformClass = token.platform === 'Pump.fun' ? 'pump-fun' : 
                                 token.platform === 'LetsBonk' ? 'letsbonk' : 'other';
            
            card.innerHTML = `
                <div class="platform-badge ${platformClass}">${token.platform || 'Unknown'}</div>
                <div class="token-name">${token.name}</div>
                <div class="token-symbol">${token.symbol}</div>
                <div class="address-container">
                    <div class="address-text" onclick="selectAddress(this)">${token.address}</div>
                    <button class="copy-btn" onclick="copyAddress('${token.address}', this)">
                        📋 Copy Address
                    </button>
                    <div class="success-msg" id="success-${token.address}">
                        ✅ Copied to clipboard!
                    </div>
                </div>
            `;
            
            return card;
        }
        
        function selectAddress(element) {
            // Select all text in the address element
            const range = document.createRange();
            range.selectNodeContents(element);
            const selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);
        }
        
        async function copyAddress(address, button) {
            try {
                await navigator.clipboard.writeText(address);
                
                // Show success message
                const successMsg = document.getElementById(`success-${address}`);
                successMsg.classList.add('show');
                
                // Change button text temporarily
                const originalText = button.textContent;
                button.textContent = '✅ Copied!';
                button.style.background = '#4CAF50';
                
                setTimeout(() => {
                    button.textContent = originalText;
                    button.style.background = '#4CAF50';
                    successMsg.classList.remove('show');
                }, 2000);
                
            } catch (error) {
                console.error('Copy failed:', error);
                
                // Fallback: select the text
                const addressElements = document.querySelectorAll('.address-text');
                addressElements.forEach(el => {
                    if (el.textContent === address) {
                        selectAddress(el);
                    }
                });
                
                button.textContent = '📋 Text Selected - Copy Manually';
                setTimeout(() => {
                    button.textContent = '📋 Copy Address';
                }, 3000);
            }
        }
        
        // Load tokens when page loads
        document.addEventListener('DOMContentLoaded', loadTokens);
        
        // Refresh every 30 seconds
        setInterval(loadTokens, 30000);
    </script>
</body>
</html>
"""