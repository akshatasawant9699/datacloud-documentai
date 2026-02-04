#!/usr/bin/env python3
"""
Document AI End-to-End Demo Script
Demonstrates document extraction with confidence scores using Salesforce Document AI API

SETUP:
1. Copy .env.example to .env
2. Fill in your Salesforce credentials in .env
3. Run: python document_ai_demo.py
"""

import requests
import json
import base64
import os
import sys
import webbrowser
import http.server
import socketserver
import urllib.parse
from threading import Thread
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Salesforce Credentials from environment
CLIENT_ID = os.environ.get('CLIENT_ID', '')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET', '')
USERNAME = os.environ.get('SF_USERNAME', '')
PASSWORD = os.environ.get('SF_PASSWORD', '')
SECURITY_TOKEN = os.environ.get('SF_SECURITY_TOKEN', '')
INSTANCE_URL = os.environ.get('INSTANCE_URL', '')
LOGIN_URL = 'https://login.salesforce.com/services/oauth2/token'
AUTH_URL = 'https://login.salesforce.com/services/oauth2/authorize'
REDIRECT_URI = 'http://localhost:8888/callback'

# API Configuration
API_VERSION = os.environ.get('API_VERSION', 'v65.0')
ML_MODEL = 'llmgateway__VertexAIGemini20Flash001'

# Dynamic Schema - works for any document type
UNIVERSAL_SCHEMA = {
    "type": "object",
    "properties": {
        "document_type": {
            "type": "string",
            "description": "Identify the document type: Sales Order, Invoice, Purchase Order, Healthcare Form, etc."
        },
        "document_number": {
            "type": "string",
            "description": "Primary document identifier (invoice number, order number, form ID, etc.)"
        },
        "document_date": {
            "type": "string",
            "description": "Date on the document"
        },
        "customer_name": {
            "type": "string",
            "description": "Customer or recipient name"
        },
        "customer_address": {
            "type": "string",
            "description": "Customer address"
        },
        "vendor_name": {
            "type": "string",
            "description": "Vendor, seller, or issuer name"
        },
        "vendor_address": {
            "type": "string",
            "description": "Vendor address"
        },
        "total_amount": {
            "type": "number",
            "description": "Total amount if applicable"
        },
        "currency": {
            "type": "string",
            "description": "Currency code (USD, EUR, INR, etc.)"
        },
        "line_items": {
            "type": "array",
            "description": "Line items/products/services if present",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Item description"},
                    "quantity": {"type": "number", "description": "Quantity"},
                    "unit_price": {"type": "number", "description": "Unit price"},
                    "line_total": {"type": "number", "description": "Line total"}
                }
            }
        },
        "additional_info": {
            "type": "object",
            "description": "Any other relevant information from the document"
        }
    }
}


class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    """Handler for OAuth callback"""
    auth_code = None
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/callback':
            params = urllib.parse.parse_qs(parsed.query)
            if 'code' in params:
                OAuthCallbackHandler.auth_code = params['code'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'''
                    <html><body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h2 style="color: green;">Authentication Successful!</h2>
                    <p>You can close this window and return to the terminal.</p>
                    </body></html>
                ''')
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'Error: No authorization code received')
        return
    
    def log_message(self, format, *args):
        pass  # Suppress logging


def get_access_token_oauth():
    """Get access token using OAuth Authorization Code flow (browser-based)"""
    print("\n🔐 Starting OAuth Authorization Flow...")
    print("   A browser window will open for you to log in.")
    
    # Build authorization URL
    auth_params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'full api'
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(auth_params)}"
    
    # Start local server to receive callback
    server = socketserver.TCPServer(("", 8888), OAuthCallbackHandler)
    server_thread = Thread(target=server.handle_request)
    server_thread.start()
    
    # Open browser
    webbrowser.open(auth_url)
    print("   Waiting for authorization...")
    
    # Wait for callback
    server_thread.join(timeout=120)
    server.server_close()
    
    if not OAuthCallbackHandler.auth_code:
        print("❌ Authorization timed out or failed")
        return None, None
    
    # Exchange code for token
    token_payload = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'code': OAuthCallbackHandler.auth_code
    }
    
    response = requests.post(LOGIN_URL, data=token_payload)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Authentication successful!")
        return data['access_token'], data.get('instance_url', INSTANCE_URL)
    else:
        print(f"❌ Token exchange failed: {response.text}")
        return None, None


def get_access_token_password():
    """Authenticate using username/password flow"""
    if not USERNAME or not PASSWORD:
        return None, None
        
    print("\n🔐 Authenticating with Salesforce (Password Flow)...")
    
    # Password + security token
    full_password = PASSWORD + SECURITY_TOKEN
    
    payload = {
        'grant_type': 'password',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'username': USERNAME,
        'password': full_password
    }
    
    response = requests.post(LOGIN_URL, data=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Authentication successful!")
        return data['access_token'], data.get('instance_url', INSTANCE_URL)
    else:
        error_data = response.json() if response.text else {}
        if error_data.get('error') == 'invalid_grant':
            print("❌ Authentication failed - Invalid credentials or security token needed")
        else:
            print(f"❌ Authentication failed: {response.text}")
        return None, None


def get_access_token():
    """Get access token - tries password first, falls back to OAuth"""
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Missing CLIENT_ID or CLIENT_SECRET in environment variables")
        print("   Please copy .env.example to .env and fill in your credentials")
        return None, None
    
    # First try password flow
    token, instance = get_access_token_password()
    
    if token:
        return token, instance
    
    # Fall back to OAuth flow
    print("\n⚠️ Password authentication failed or not configured. Trying OAuth flow...")
    return get_access_token_oauth()


def extract_document(access_token, instance_url, file_path, schema_config=None):
    """
    Extract data from a document using Document AI
    Works with any document type - schema is dynamic
    """
    print(f"\n📄 Processing document: {file_path}")
    
    # Read and encode file
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    with open(file_path, 'rb') as f:
        file_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Determine MIME type
    ext = os.path.splitext(file_path)[1].lower()
    mime_types = {
        '.pdf': 'application/pdf',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.tiff': 'image/tiff',
        '.tif': 'image/tiff',
        '.bmp': 'image/bmp'
    }
    mime_type = mime_types.get(ext, 'application/pdf')
    
    # Use provided schema or default universal schema
    schema = schema_config if schema_config else UNIVERSAL_SCHEMA
    
    # Build request
    request_body = {
        "mlModel": ML_MODEL,
        "schemaConfig": json.dumps(schema),
        "files": [{
            "mimeType": mime_type,
            "data": file_data
        }]
    }
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    url = f"{instance_url}/services/data/{API_VERSION}/ssot/document-processing/actions/extract-data?htmlEncode=false&extractDataWithConfidenceScore=true"
    
    print("🚀 Sending to Document AI API...")
    response = requests.post(url, headers=headers, json=request_body, timeout=120)
    
    if response.status_code in [200, 201]:
        result = response.json()
        return result
    else:
        print(f"❌ API Error: {response.status_code}")
        print(f"Response: {response.text}")
        return None


def display_results_with_confidence(result):
    """Display extracted data with confidence scores"""
    print("\n" + "="*80)
    print("📊 EXTRACTION RESULTS WITH CONFIDENCE SCORES")
    print("="*80)
    
    if not result or 'data' not in result:
        print("No data extracted")
        return
    
    for idx, item in enumerate(result.get('data', [])):
        if 'data' in item:
            try:
                # Parse the extracted data
                extracted = json.loads(item['data'].replace('&quot;', '"'))
                
                print(f"\n📋 Document {idx + 1}:")
                print("-" * 60)
                
                for field_name, field_data in extracted.items():
                    if isinstance(field_data, dict):
                        field_type = field_data.get('type', 'unknown')
                        value = field_data.get('value')
                        confidence = field_data.get('confidence_score')
                        
                        # Format confidence indicator
                        if confidence is not None:
                            conf_percent = confidence * 100
                            if conf_percent >= 90:
                                conf_indicator = f"🟢 {conf_percent:.0f}%"
                            elif conf_percent >= 70:
                                conf_indicator = f"🟡 {conf_percent:.0f}%"
                            else:
                                conf_indicator = f"🔴 {conf_percent:.0f}%"
                        else:
                            conf_indicator = "⚪ N/A"
                        
                        # Format value display
                        if field_type == 'array' and isinstance(value, list):
                            print(f"\n  {field_name.replace('_', ' ').title()}:")
                            print(f"    Confidence: {conf_indicator}")
                            for i, line_item in enumerate(value):
                                print(f"    Item {i+1}:")
                                if isinstance(line_item, dict) and 'value' in line_item:
                                    for k, v in line_item.get('value', {}).items():
                                        if isinstance(v, dict):
                                            print(f"      - {k}: {v.get('value', 'N/A')}")
                        elif value is not None and str(value) != 'null':
                            print(f"  {field_name.replace('_', ' ').title()}: {value}")
                            print(f"    └─ Confidence: {conf_indicator}")
                
            except json.JSONDecodeError as e:
                print(f"  Raw data: {item['data']}")
    
    print("\n" + "="*80)
    print("📈 CONFIDENCE SCORE LEGEND:")
    print("  🟢 High (90%+)    - Reliable extraction")
    print("  🟡 Medium (70-89%) - May need review")
    print("  🔴 Low (<70%)     - Requires verification")
    print("="*80)


def interactive_mode(access_token, instance_url):
    """Interactive mode for custom document extraction"""
    print("\n🔄 INTERACTIVE MODE")
    print("-" * 40)
    
    while True:
        file_path = input("\nEnter document path (or 'quit' to exit): ").strip()
        
        if file_path.lower() in ['quit', 'exit', 'q']:
            break
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            continue
        
        # Use universal schema for any document
        result = extract_document(access_token, instance_url, file_path)
        if result:
            display_results_with_confidence(result)


def main():
    """Main demo function"""
    print("\n" + "="*80)
    print("🚀 DOCUMENT AI END-TO-END DEMO")
    print("   Extract data from ANY document with confidence scores")
    print("="*80)
    
    # Authenticate
    access_token, instance_url = get_access_token()
    
    if not access_token:
        print("❌ Failed to authenticate. Please check credentials in .env file.")
        return
    
    # Interactive mode
    interactive_mode(access_token, instance_url)
    print("\nGoodbye! 👋")


if __name__ == '__main__':
    main()
