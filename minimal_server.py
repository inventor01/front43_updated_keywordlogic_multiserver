#!/usr/bin/env python3
"""
Minimal server that starts immediately for Railway health checks
"""
import os
import time
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

start_time = time.time()

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'uptime': time.time() - start_time,
                'timestamp': time.time()
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'message': 'Solana Token Monitor Active',
                'status': 'healthy',
                'uptime': time.time() - start_time
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    
    print(f"Starting minimal server on port {port}")
    print(f"Health check available at: http://0.0.0.0:{port}/health")
    
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped")
        server.server_close()