#!/usr/bin/env python3
"""
Railway-specific server with comprehensive logging and port binding verification
"""
import os
import sys
import time
import json
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Get Railway configuration
PORT = int(os.environ.get('PORT', 5000))
HOST = '0.0.0.0'

print(f"[STARTUP] Railway server starting...")
print(f"[STARTUP] Port: {PORT}")
print(f"[STARTUP] Host: {HOST}")
print(f"[STARTUP] Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'unknown')}")

start_time = time.time()

class RailwayHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == '/health':
                response_data = {
                    'status': 'healthy',
                    'service': 'solana-token-monitor',
                    'uptime': time.time() - start_time,
                    'timestamp': time.time(),
                    'port': PORT,
                    'railway': True
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
                print(f"[HEALTH] Health check successful at {time.strftime('%H:%M:%S')}")
                
            elif self.path == '/':
                response_data = {
                    'message': 'Solana Token Monitor - Railway Deployment',
                    'status': 'active',
                    'uptime': time.time() - start_time,
                    'health_endpoint': '/health',
                    'railway': True
                }
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Not found'}).encode('utf-8'))
                
        except Exception as e:
            print(f"[ERROR] Handler error: {e}")
            self.send_response(500)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Custom logging
        print(f"[REQUEST] {format % args}")

def check_port_availability():
    """Check if port is available before binding"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        sock.close()
        print(f"[PORT] Port {PORT} is available")
        return True
    except Exception as e:
        print(f"[ERROR] Port {PORT} check failed: {e}")
        return False

def start_background_services():
    """Start main application after health check is stable"""
    print("[BACKGROUND] Waiting 10 seconds before starting main services...")
    time.sleep(10)
    
    try:
        print("[BACKGROUND] Starting main application...")
        # Import and start main application
        from main import IntegratedServer
        server = IntegratedServer()
        server.run()
    except Exception as e:
        print(f"[ERROR] Background service failed: {e}")
        # Continue running health check even if main app fails

if __name__ == "__main__":
    print(f"[INIT] Python version: {sys.version}")
    print(f"[INIT] Current directory: {os.getcwd()}")
    
    # Check port availability
    if not check_port_availability():
        print(f"[FATAL] Cannot bind to port {PORT}")
        sys.exit(1)
    
    # Create server
    try:
        server = HTTPServer((HOST, PORT), RailwayHandler)
        print(f"[SUCCESS] Server created successfully")
        
        # Start background services in separate thread
        bg_thread = threading.Thread(target=start_background_services, daemon=True)
        bg_thread.start()
        
        print(f"[READY] Server listening on {HOST}:{PORT}")
        print(f"[READY] Health check: http://{HOST}:{PORT}/health")
        print(f"[READY] Starting server loop...")
        
        # Start server
        server.serve_forever()
        
    except KeyboardInterrupt:
        print(f"[SHUTDOWN] Server stopped by user")
    except Exception as e:
        print(f"[FATAL] Server failed to start: {e}")
        sys.exit(1)
    finally:
        if 'server' in locals():
            server.server_close()
            print(f"[SHUTDOWN] Server closed")