from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import requests

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.utils import create_response

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """Handle OAuth callback - Exchange code for token"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            code = data.get('code')
            login_url = data.get('login_url')
            client_id = data.get('client_id')
            client_secret = data.get('client_secret')
            
            if not code:
                response = create_response(400, {
                    'success': False,
                    'error': 'Authorization code is required'
                })
                self.send_response(response['statusCode'])
                for key, value in response['headers'].items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(response['body'].encode('utf-8'))
                return
            
            if not login_url or not client_id or not client_secret:
                response = create_response(400, {
                    'success': False,
                    'error': 'Login URL, Client ID, and Client Secret are required'
                })
                self.send_response(response['statusCode'])
                for key, value in response['headers'].items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(response['body'].encode('utf-8'))
                return
            
            # Exchange code for token
            # Construct the redirect URI relative to the request host
            # Note: In Vercel, we need to match what the frontend sent.
            # The frontend used window.location.origin + '/auth/callback'
            # We can try to reconstruct it or rely on the frontend to send it (it doesn't).
            # But wait! 'redirect_uri' in the token exchange MUST match the one in the auth request.
            # The auth request used: `${window.location.protocol}//${window.location.host}/auth/callback`
            
            # We need to construct the exact same string here.
            # In Vercel serverless, 'Host' header gives the domain.
            # Protocol is usually https.
            host = self.headers.get('Host')
            # Check for X-Forwarded-Proto
            proto = self.headers.get('X-Forwarded-Proto', 'https')
            
            redirect_uri = f"{proto}://{host}/auth/callback"
            
            # Special case for localhost testing if not behind proxy
            if 'localhost' in host and proto == 'https':
                 # Localhost often uses http
                 pass
            
            # Actually, to be safe, we should probably update the frontend to SEND the redirect_uri it used.
            # But since I can't easily change the frontend deployment without redeploying, 
            # and 'app_local.py' worked with f"{request.scheme}://{request.host}/auth/callback",
            # I will try to replicate that.
            
            token_url = f"https://{login_url}/services/oauth2/token"
            
            payload = {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri
            }
            
            # Make request
            api_response = requests.post(token_url, data=payload, timeout=30)
            
            if api_response.status_code == 200:
                token_data = api_response.json()
                response = create_response(200, {
                    'success': True,
                    'access_token': token_data.get('access_token'),
                    'instance_url': token_data.get('instance_url'),
                    'token_type': token_data.get('token_type', 'Bearer')
                })
            else:
                error_text = api_response.text
                try:
                    error_json = api_response.json()
                    error_text = error_json.get('error_description', error_json.get('error', error_text))
                except:
                    pass
                
                response = create_response(400, {
                    'success': False,
                    'error': f'Token exchange failed: {error_text}',
                    'debug_redirect_uri': redirect_uri # Return this to help debug if mismatch
                })
            
            self.send_response(response['statusCode'])
            for key, value in response['headers'].items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response['body'].encode('utf-8'))
            
        except Exception as e:
            response = create_response(500, {
                'success': False,
                'error': f'Server error: {str(e)}'
            })
            self.send_response(response['statusCode'])
            for key, value in response['headers'].items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response['body'].encode('utf-8'))
