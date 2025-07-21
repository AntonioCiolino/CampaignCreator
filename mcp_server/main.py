from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import requests
from dotenv import load_dotenv
import sys
import socket

load_dotenv()

# Configuration for the main Campaign Crafter API
CAMPAIGN_CRAFTER_API_URL = "http://localhost:8000/api/v1"
BACKEND_TOKEN = None

def authenticate_with_backend():
    """Authenticates with the main API and stores the token."""
    global BACKEND_TOKEN
    username = os.environ.get("CAMPAIGN_CRAFTER_USERNAME")
    password = os.environ.get("CAMPAIGN_CRAFTER_PASSWORD")

    if not username or not password:
        print("CAMPAIGN_CRAFTER_USERNAME and CAMPAIGN_CRAFTER_PASSWORD environment variables are not set. Cannot authenticate with the backend.", file=sys.stderr)
        return

    try:
        response = requests.post(
            f"{CAMPAIGN_CRAFTER_API_URL}/auth/token",
            data={"username": username, "password": password, "grant_type": "password"}
        )
        response.raise_for_status()
        BACKEND_TOKEN = response.json()["access_token"]
        print("Successfully authenticated with the backend.", file=sys.stderr)
    except requests.exceptions.RequestException as e:
        print(f"Failed to authenticate with the backend: {e}", file=sys.stderr)

class MCPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "name": "campaign_crafter",
                "version": "1.0.0",
                "protocol": "mcp",
            }).encode('utf-8'))
        elif self.path == '/mcp':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            base_url = f"http://{get_local_ip()}:{self.server.server_port}"
            self.wfile.write(json.dumps({
                "name": "Campaign Crafter",
                "version": "1.0.0",
                "protocol": "mcp",
                "auth_schemes": [
                    {
                        "type": "oauth2",
                        "url": f"{base_url}/.well-known/oauth-authorization-server"
                    }
                ],
                "methods": [
                    "create_campaign",
                    "get_campaign",
                    "update_campaign",
                    "delete_campaign",
                    "create_character",
                    "get_character",
                    "update_character",
                    "delete_character",
                    "link_character_to_campaign",
                    "unlink_character_from_campaign",
                    "create_campaign_section",
                    "list_campaign_sections",
                    "update_campaign_section",
                    "delete_campaign_section",
                    "generate_toc",
                    "generate_titles",
                ]
            }).encode('utf-8'))
        elif self.path.startswith('/.well-known/oauth-authorization-server'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            base_url = f"http://{get_local_ip()}:{self.server.server_port}"
            self.wfile.write(json.dumps({
                "issuer": base_url,
                "authorization_endpoint": f"{base_url}/authorize",
                "token_endpoint": f"{base_url}/token",
                "registration_endpoint": f"{base_url}/register",
                "response_types_supported": ["code"],
                "grant_types_supported": ["authorization_code", "password"],
                "token_endpoint_auth_methods_supported": ["none", "client_secret_post"]
            }).encode('utf-8'))
        elif self.path.startswith('/authorize'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f'''
            <!DOCTYPE html>
            <html>
            <head><title>Login</title></head>
            <body>
                <h1>Authorize Campaign Crafter</h1>
                <form method="post" action="/authorize">
                    <input type="hidden" name="client_id" value="{self.path.split('client_id=')[1].split('&')[0]}">
                    <input type="hidden" name="redirect_uri" value="{self.path.split('redirect_uri=')[1].split('&')[0]}">
                    <input type="hidden" name="response_type" value="{self.path.split('response_type=')[1].split('&')[0]}">
                    <input type="hidden" name="state" value="{self.path.split('state=')[1].split('&')[0]}">
                    <div>
                        <label for="username">Username:</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div>
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <br>
                    <input type="submit" value="Authorize">
                </form>
            </body>
            </html>
            '''.encode('utf-8'))
        elif self.path.startswith('/callback'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            code = self.path.split('code=')[1].split('&')[0]
            self.wfile.write(f"Received authorization code: {code}. Now, exchange this for a token at /token.".encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/mcp/rpc':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                if not data or "jsonrpc" not in data or "method" not in data:
                    raise ValueError("Invalid JSON-RPC request")

                jsonrpc = data["jsonrpc"]
                method = data["method"]
                params = data.get("params", {})
                request_id = data.get("id")

                if jsonrpc != "2.0":
                    raise ValueError("Invalid JSON-RPC version")

                # Dispatch to the correct function based on the method
                if method in [
                    "create_campaign",
                    "get_campaign",
                    "update_campaign",
                    "delete_campaign",
                    "create_character",
                    "get_character",
                    "update_character",
                    "delete_character",
                    "link_character_to_campaign",
                    "unlink_character_from_campaign",
                    "create_campaign_section",
                    "list_campaign_sections",
                    "update_campaign_section",
                    "delete_campaign_section",
                    "generate_toc",
                    "generate_titles",
                ]:
                    path = f"/{method.replace('_', '/')}"
                    http_method = "POST" if "create" in method or "generate" in method or "link" in method else "GET"
                    if "update" in method:
                        http_method = "PUT"
                    if "delete" in method or "unlink" in method:
                        http_method = "DELETE"

                    response_data, status_code = self.forward_request(http_method, path, json=params)
                else:
                    response_data = {"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method '{method}' not found"}, "id": request_id}
                    status_code = 200

                if status_code >= 400:
                    response_data = {"jsonrpc": "2.0", "error": {"code": -32602, "message": response_data}, "id": request_id}

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))

            except (ValueError, json.JSONDecodeError) as e:
                response_data = {"jsonrpc": "2.0", "error": {"code": -32700, "message": f"Parse error: {e}"}, "id": None}
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            except Exception as e:
                response_data = {"jsonrpc": "2.0", "error": {"code": -32603, "message": f"Internal error: {e}"}, "id": None}
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
        elif self.path == '/register':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            client_info = json.loads(post_data)
            if not client_info or 'client_name' not in client_info or 'redirect_uris' not in client_info:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "invalid_client_metadata"}).encode('utf-8'))
                return

            client_id = secrets.token_urlsafe(16)
            clients[client_id] = {
                "client_name": client_info["client_name"],
                "redirect_uris": client_info["redirect_uris"],
                "client_id_issued_at": datetime.now(timezone.utc).timestamp()
            }

            self.send_response(201)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "client_id": client_id,
                "client_name": client_info["client_name"],
                "redirect_uris": client_info["redirect_uris"],
                "grant_types": ["authorization_code"],
                "response_types": ["code"],
                "token_endpoint_auth_method": "none"
            }).encode('utf-8'))
        elif self.path == '/authorize':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            from urllib.parse import parse_qs
            form_data = parse_qs(post_data.decode('utf-8'))

            session_id = form_data.get('session_id', [None])[0]
            session_data = auth_codes.get(f"session_{session_id}")

            if not session_data:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"Invalid session")
                return

            username = form_data.get('username', [None])[0]
            password = form_data.get('password', [None])[0]

            # Authenticate with backend
            try:
                auth_response = requests.post(
                    f"{CAMPAIGN_CRAFTER_API_URL}/auth/token",
                    data={"username": username, "password": password, "grant_type": "password"}
                )
                auth_response.raise_for_status()
                backend_token = auth_response.json().get('access_token')
            except requests.exceptions.HTTPError:
                self.send_response(401)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"Invalid credentials")
                return
            except requests.exceptions.RequestException:
                self.send_response(500)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"Error connecting to authentication service")
                return

            # Generate auth code
            auth_code = secrets.token_urlsafe(16)
            auth_codes[auth_code] = {
                'client_id': session_data['client_id'],
                'user_id': username,
                'backend_token': backend_token
            }

            # Clean up session
            del auth_codes[f"session_{session_id}"]

            # Redirect back to Claude
            params = {'code': auth_code, 'state': session_data['state']}
            redirect_url = f"{session_data['redirect_uri']}?{urlencode(params)}"

            self.send_response(302)
            self.send_header('Location', redirect_url)
            self.end_headers()
        elif self.path == '/token':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            from urllib.parse import parse_qs
            form_data = parse_qs(post_data.decode('utf-8'))
            grant_type = form_data.get('grant_type', [None])[0]

            if grant_type == 'password':
                # Forward username/password to the main API's token endpoint
                try:
                    response = requests.post(
                        f"{CAMPAIGN_CRAFTER_API_URL}/auth/token",
                        data=form_data
                    )
                    response.raise_for_status()
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response.json()).encode('utf-8'))
                except requests.exceptions.HTTPError as e:
                    self.send_response(e.response.status_code)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(e.response.json()).encode('utf-8'))
                except requests.exceptions.RequestException as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

            elif grant_type == 'authorization_code':
                code = form_data.get('code', [None])[0]
                client_id = form_data.get('client_id', [None])[0]

                if not code or not client_id:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "invalid_request"}).encode('utf-8'))
                    return

                if client_id not in clients:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "unauthorized_client"}).encode('utf-8'))
                    return

                auth_code_data = auth_codes.pop(code, None)

                if not auth_code_data or auth_code_data['client_id'] != client_id:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "invalid_grant"}).encode('utf-8'))
                    return

                # Return the backend token we stored earlier
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "access_token": auth_code_data['backend_token'],
                    "token_type": "bearer",
                    "user_id": auth_code_data['user_id']
                }).encode('utf-8'))

            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "unsupported_grant_type"}).encode('utf-8'))
        else:
            self.send_error(404)

    def forward_request(self, method, path, **kwargs):
        """
        Forwards a request to the main Campaign Crafter API.
        """
        if not BACKEND_TOKEN:
            return {"error": "Backend not authenticated"}, 503

        headers = {
            'Authorization': f"Bearer {BACKEND_TOKEN}",
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        url = f"{CAMPAIGN_CRAFTER_API_URL}{path}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                **kwargs
            )
            response.raise_for_status()
            # For DELETE requests, a 204 No Content might not have a JSON body
            if response.status_code == 204:
                return {}, 204
            return response.json(), response.status_code
        except requests.exceptions.HTTPError as e:
            return e.response.json(), e.response.status_code
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}, 500

def run(server_class=HTTPServer, handler_class=MCPRequestHandler, port=5001):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting httpd on port {port}...", file=sys.stderr)
    httpd.serve_forever()

if __name__ == '__main__':
    authenticate_with_backend()
    port = int(os.environ.get("PORT", 5001))
    run(port=port)
