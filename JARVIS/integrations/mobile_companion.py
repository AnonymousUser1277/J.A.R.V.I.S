"""
Mobile Companion App Backend
- Control JARVIS from phone
- View logs remotely
- Emergency shutdown
- Real-time status updates via WebSocket
"""

import logging
import threading
import time
import json
import hashlib
import secrets
from typing import Dict, Optional
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from pathlib import Path
from config.settings import DATA_DIR, LOG_DIR

logger = logging.getLogger(__name__)

class MobileCompanion:
    """
    Mobile companion backend server
    
    Features:
    - REST API for control
    - WebSocket for real-time updates
    - Authentication with tokens
    - Emergency shutdown
    """
    
    def __init__(self, gui_handler, port: int = 5555):
        self.gui_handler = gui_handler
        self.port = port
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = secrets.token_hex(32)
        
        # Enable CORS for mobile access
        CORS(self.app, resources={r"/*": {"origins": "*"}})
        
        # WebSocket support
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            async_mode='threading'
        )
        
        # Authentication
        self.auth_dir = DATA_DIR / "mobile_auth"
        self.auth_dir.mkdir(exist_ok=True)
        self.auth_file = self.auth_dir / "tokens.json"
        self.tokens = self._load_tokens()
        
        # Connected clients
        self.connected_clients = []
        
        # Setup routes
        self._setup_routes()
        self._setup_websocket()
        
        # Start server in background
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True,
            name="Mobile-Companion"
        )
        self.server_thread.start()
        
        # Start status broadcaster
        self.broadcasting = True
        self.broadcast_thread = threading.Thread(
            target=self._broadcast_status_loop,
            daemon=True,
            name="Mobile-Broadcast"
        )
        self.broadcast_thread.start()
        self.file_lock = threading.Lock()
        logger.info(f"✅ Mobile Companion started on port {self.port}")
        logger.info(f"📱 Connect from: http://<your-ip>:{self.port}")

    def _load_tokens(self) -> Dict:
        """Load authentication tokens"""
        if self.auth_file.exists():
            try:
                with open(self.auth_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_tokens(self):
        """Save authentication tokens"""
        with self.file_lock:
            with open(self.auth_file, 'w') as f:
                json.dump(self.tokens, f, indent=2)
    
    def _generate_token(self) -> str:
        """Generate new authentication token"""
        token = secrets.token_urlsafe(32)
        self.tokens[token] = {
            'created': datetime.now().isoformat(),
            'expires': (datetime.now() + timedelta(days=30)).isoformat()
        }
        self._save_tokens()
        return token
    
    def _verify_token(self, token: str) -> bool:
        """Verify authentication token"""
        if token not in self.tokens:
            return False
        
        expires = datetime.fromisoformat(self.tokens[token]['expires'])
        return datetime.now() < expires
    
    def _require_auth(self, f):
        """Decorator for routes requiring authentication"""
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if not self._verify_token(token):
                return jsonify({'error': 'Unauthorized'}), 401
            return f(*args, **kwargs)
        decorated.__name__ = f.__name__
        return decorated
    
    def _setup_routes(self):
        """Setup REST API routes"""
        
        @self.app.route('/api/auth/pair', methods=['POST'])
        def pair():
            """Pair new device"""
            data = request.json
            device_name = data.get('device_name', 'Unknown Device')
            
            # Generate QR code data
            token = self._generate_token()
            
            return jsonify({
                'success': True,
                'token': token,
                'device_name': device_name,
                'server_url': f'http://{self._get_local_ip()}:{self.port}'
            })
        
        @self.app.route('/api/status', methods=['GET'])
        @self._require_auth
        def get_status():
            """Get JARVIS status"""
            try:
                context = self.gui_handler.context_manager.get_context_string()
                
                return jsonify({
                    'status': 'running',
                    'context': context,
                    'cpu': self.gui_handler.context_manager.cpu_percent,
                    'ram': self.gui_handler.context_manager.ram_percent,
                    'battery': self.gui_handler.context_manager.battery_percent,
                    'network': self.gui_handler.context_manager.network_connected,
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"Status error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/command', methods=['POST'])
        @self._require_auth
        def execute_command():
            """Execute command"""
            try:
                data = request.json
                command = data.get('command', '')
                
                if not command:
                    return jsonify({'error': 'No command provided'}), 400
                
                # Queue command for execution
                from ai.instructions import generate_instructions
                
                def execute():
                    generate_instructions(
                        command,
                        self.gui_handler.client,
                        self.gui_handler
                    )
                
                threading.Thread(target=execute, daemon=True).start()
                
                return jsonify({
                    'success': True,
                    'message': f'Executing: {command}'
                })
            
            except Exception as e:
                logger.error(f"Command error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/logs', methods=['GET'])
        @self._require_auth
        def get_logs():
            """Get recent logs"""
            try:
                today_log = datetime.now().strftime("%Y-%m-%d") + ".log"
                log_file = LOG_DIR / today_log
                
                if not log_file.exists():
                    return jsonify({'logs': []})
                
                # Read last 100 lines
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    recent_lines = lines[-100:]
                
                return jsonify({
                    'logs': recent_lines,
                    'file': str(log_file)
                })
            
            except Exception as e:
                logger.error(f"Logs error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/shutdown', methods=['POST'])
        @self._require_auth
        def emergency_shutdown():
            """Emergency shutdown"""
            try:
                data = request.json
                confirm = data.get('confirm', False)
                
                if not confirm:
                    return jsonify({'error': 'Confirmation required'}), 400
                
                logger.warning("🚨 EMERGENCY SHUTDOWN from mobile app")
                
                def shutdown():
                    time.sleep(1)
                    self.gui_handler.cleanup()
                    self.gui_handler.root.after(0, self.gui_handler.root.quit)
                
                threading.Thread(target=shutdown, daemon=True).start()
                
                return jsonify({
                    'success': True,
                    'message': 'JARVIS is shutting down...'
                })
            
            except Exception as e:
                logger.error(f"Shutdown error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/cache/stats', methods=['GET'])
        @self._require_auth
        def cache_stats():
            """Get cache statistics"""
            try:
                from ai.redis_cache import cache
                stats = cache.get_stats()
                return jsonify(stats)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _setup_websocket(self):
        """Setup WebSocket events"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Client connected"""
            logger.info(f"📱 Mobile client connected: {request.sid}")
            self.connected_clients.append(request.sid)
            emit('connected', {'message': 'Connected to JARVIS'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Client disconnected"""
            logger.info(f"📱 Mobile client disconnected: {request.sid}")
            if request.sid in self.connected_clients:
                self.connected_clients.remove(request.sid)
        
        @self.socketio.on('ping')
        def handle_ping():
            """Ping/pong for keep-alive"""
            emit('pong', {'timestamp': time.time()})
    
    def _broadcast_status_loop(self):
        """Broadcast status updates to connected clients"""
        while self.broadcasting:
            try:
                if self.connected_clients:
                    status = {
                        'context': self.gui_handler.context_manager.get_context_string(),
                        'cpu': self.gui_handler.context_manager.cpu_percent,
                        'ram': self.gui_handler.context_manager.ram_percent,
                        'battery': self.gui_handler.context_manager.battery_percent,
                        'timestamp': time.time()
                    }
                    
                    self.socketio.emit('status_update', status)
                
                time.sleep(2)
            
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                time.sleep(5)
    
    def _run_server(self):
        """Run Flask server"""
        try:
            self.socketio.run(
                self.app,
                host='0.0.0.0',
                port=self.port,
                debug=False,
                use_reloader=False,
                allow_unsafe_werkzeug=True
            )
        except Exception as e:
            logger.error(f"Server error: {e}")
    
    def _get_local_ip(self) -> str:
        """Get local IP address"""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return 'localhost'
    
    def shutdown(self):
        """Shutdown mobile companion"""
        logger.info("🛑 Shutting down mobile companion...")
        self.broadcasting = False
        # Flask/SocketIO shutdown is handled by daemon threads


# Global instance
_mobile_companion = None

def start_mobile_companion(gui_handler, port: int = 5555):
    """Start mobile companion"""
    global _mobile_companion
    if _mobile_companion is None:
        _mobile_companion = MobileCompanion(gui_handler, port)
    return _mobile_companion

def get_mobile_companion() -> Optional[MobileCompanion]:
    """Get mobile companion instance"""
    return _mobile_companion
