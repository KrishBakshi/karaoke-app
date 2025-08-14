#!/usr/bin/env python3
"""
Simple HTTP server to serve audio devices JSON for frontend integration
"""

import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# Add current directory to path to import get_devices_json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from get_devices_json import get_audio_devices

class DevicesHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Enable CORS
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        if self.path == '/api/devices':
            try:
                devices = get_audio_devices()
                self.wfile.write(json.dumps(devices, indent=2).encode())
            except Exception as e:
                error_response = {'error': str(e)}
                self.wfile.write(json.dumps(error_response, indent=2).encode())
        else:
            # Return 404 for unknown paths
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {'error': 'Not found'}
            self.wfile.write(json.dumps(error_response, indent=2).encode())
    
    def do_OPTIONS(self):
        # Handle CORS preflight request
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def main():
    PORT = 8766
    print(f"🎤 Audio Devices Server starting on port {PORT}")
    print(f"🌐 Access devices at: http://localhost:{PORT}/api/devices")
    
    try:
        server = HTTPServer(('localhost', PORT), DevicesHandler)
        print(f"✅ Server started successfully!")
        print(f"🎵 Press Ctrl+C to stop the server")
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == '__main__':
    main()
