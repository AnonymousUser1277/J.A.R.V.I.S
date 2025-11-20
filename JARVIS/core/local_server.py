"""
A simple, local HTTP server to receive context data from browser extensions.
"""

import threading
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

logger = logging.getLogger(__name__)

class _RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            url = post_data.decode('utf-8')
            
            # Update the context manager
            if self.server.context_manager:
                self.server.context_manager.update_url(url)
            
            self.send_response(200)
            self.end_headers()
        except Exception as e:
            logger.error(f"Local server request error: {e}")
            self.send_response(500)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress the default logging to keep the console clean
        return

class LocalContextServer(HTTPServer):
    def __init__(self, server_address, RequestHandlerClass, context_manager):
        super().__init__(server_address, RequestHandlerClass)
        self.context_manager = context_manager

def start_local_server(context_manager, host='localhost', port=8989):
    """Starts the local context server in a background thread."""
    def run_server():
        try:
            server_address = (host, port)
            httpd = LocalContextServer(server_address, _RequestHandler, context_manager)
            logger.info(f"🚀 Local context server started at http://{host}:{port}")
            httpd.serve_forever()
        except Exception as e:
            logger.error(f"❌ Failed to start local context server: {e}")

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()