"""
chatbot/api.py

Zero-dependency HTTP server to expose the Ask Chipathon RAG chain to the MkDocs frontend.
"""

import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

# Ensure the parent directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chatbot.rag_chain import ask

class ChatRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path != '/chat':
            self.send_response(404)
            self.end_headers()
            return
            
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        # Add CORS headers
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            body = json.loads(post_data)
            query = body.get('query', '')
            
            result = ask(query)
            
            response_data = {
                "answer": result.get("answer", "No answer generated."),
                "citations": result.get("citations", []),
                "confidence": result.get("confidence", 0.0),
                "is_fallback": result.get("is_fallback", False)
            }
            
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            error_data = {
                "error": f"Error processing request: {str(e)}",
                "answer": f"Error processing request: {str(e)}",
                "citations": [],
                "confidence": 0.0,
                "is_fallback": True
            }
            self.wfile.write(json.dumps(error_data).encode('utf-8'))

def run_server(port=None):
    port = port or int(os.environ.get('PORT', 8001))
    server_address = ('', port)
    httpd = HTTPServer(server_address, ChatRequestHandler)
    print(f"Starting Chipathon API server on port {port}...")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
