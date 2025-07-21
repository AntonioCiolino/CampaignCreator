#!/usr/bin/env python3
"""
Minimal OAuth connector for testing Claude connectivity
Run with: python minimal_connector.py
"""

from flask import Flask, request, jsonify, redirect
import secrets
import os
from datetime import datetime

app = Flask(__name__)

# Simple in-memory storage
clients = {}
auth_codes = {}
access_tokens = {}

def log(message):
    """Simple logging"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

@app.before_request
def log_request():
    log(f"🌐 {request.method} {request.path} from {request.remote_addr}")

# 1. OAuth Discovery Endpoint (Claude starts here)
@app.route('/.well-known/oauth-authorization-server', methods=['GET'])
def oauth_discovery():
    log("📋 OAuth discovery requested")
    
    base_url = f"http://127.0.0.1:{os.environ.get('PORT', 5000)}"
    
    return jsonify({
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "registration_endpoint": f"{base_url}/register",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "token_endpoint_auth_methods_supported": ["none"]
    })

# 2. Client Registration (Claude registers itself)
@app.route('/register', methods=['POST'])
def register_client():
    log("📝 Client registration requested")
    
    data = request.get_json() or {}
    client_id = secrets.token_urlsafe(16)
    
    clients[client_id] = {
        "name": data.get("client_name", "Claude"),
        "redirect_uris": data.get("redirect_uris", [])
    }
    
    log(f"✅ Registered client: {client_id}")
    
    return jsonify({
        "client_id": client_id,
        "client_name": data.get("client_name", "Claude"),
        "redirect_uris": data.get("redirect_uris", [])
    }), 201

# 3. Authorization Endpoint (User login)
@app.route('/authorize', methods=['GET', 'POST'])
def authorize():
    if request.method == 'GET':
        log("🔐 Authorization page requested")
        
        client_id = request.args.get('client_id')
        redirect_uri = request.args.get('redirect_uri')
        state = request.args.get('state')
        
        log(f"   Client: {client_id}")
        log(f"   Redirect: {redirect_uri}")
        
        # Simple auto-approval for testing
        auth_code = secrets.token_urlsafe(16)
        auth_codes[auth_code] = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'user_id': 'test_user'
        }
        
        log(f"🎫 Generated auth code: {auth_code}")
        
        # Auto-redirect back to Claude
        redirect_url = f"{redirect_uri}?code={auth_code}&state={state}"
        log(f"↩️  Redirecting to: {redirect_url}")
        
        return redirect(redirect_url)

# 4. Token Exchange
@app.route('/token', methods=['POST'])
def token():
    log("🔑 Token exchange requested")
    
    code = request.form.get('code')
    client_id = request.form.get('client_id')
    
    log(f"   Code: {code}")
    log(f"   Client: {client_id}")
    
    # Validate auth code
    auth_data = auth_codes.pop(code, None)
    if not auth_data or auth_data['client_id'] != client_id:
        log("❌ Invalid auth code")
        return jsonify({"error": "invalid_grant"}), 400
    
    # Generate access token
    access_token = secrets.token_urlsafe(32)
    access_tokens[access_token] = {
        'user_id': auth_data['user_id'],
        'client_id': client_id
    }
    
    log(f"✅ Generated access token: {access_token[:8]}...")
    
    return jsonify({
        "access_token": access_token,
        "token_type": "bearer"
    })

# 5. Test API Endpoint (Protected resource)
@app.route('/api/hello', methods=['GET'])
def api_hello():
    log("👋 API hello endpoint called")
    
    # Check for access token
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        log("❌ No bearer token")
        return jsonify({"error": "unauthorized"}), 401
    
    token = auth_header[7:]  # Remove "Bearer "
    token_data = access_tokens.get(token)
    
    if not token_data:
        log("❌ Invalid token")
        return jsonify({"error": "invalid_token"}), 401
    
    log(f"✅ Valid request from user: {token_data['user_id']}")
    
    return jsonify({
        "message": "Hello from your OAuth connector!",
        "user": token_data['user_id'],
        "timestamp": datetime.now().isoformat()
    })

# Health check
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "clients": len(clients),
        "active_tokens": len(access_tokens)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    print("🚀 Starting minimal OAuth connector")
    print(f"📍 OAuth URL: http://127.0.0.1:{port}/.well-known/oauth-authorization-server")
    print(f"🔍 Health check: http://127.0.0.1:{port}/health")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=port, debug=True)