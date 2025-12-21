from flask import Flask, request, jsonify, render_template, session, render_template_string
from flask_cors import CORS
import requests
import base64
import json
import logging
from datetime import datetime, timedelta
import os

# Import configuration
from config import DEFAULT_ML_MODEL, LOGIN_URL, CLIENT_ID, CLIENT_SECRET, API_VERSION

# Get the directory of this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')

app = Flask(__name__, 
            template_folder=os.path.join(FRONTEND_DIR, 'templates'),
            static_folder=os.path.join(FRONTEND_DIR, 'static'),
            static_url_path='/static')
app.secret_key = os.urandom(24)
# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/auth-info', methods=['GET'])
def get_auth_info():
    """Get authentication configuration (OAuth 2.0 with PKCE)"""
    if not LOGIN_URL or not CLIENT_ID:
        return jsonify({'error': 'Salesforce config missing on server. Please configure .env file.'}), 500
    
    return jsonify({
        'loginUrl': LOGIN_URL,
        'clientId': CLIENT_ID,
    })

@app.route('/auth/callback')
def auth_callback():
    """OAuth callback handler - receives authorization code from Salesforce"""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Error</title>
            <meta http-equiv="refresh" content="3;url=/">
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .error { color: #d32f2f; background: #ffebee; padding: 20px; border-radius: 8px; }
            </style>
        </head>
        <body>
            <div class="error">
                <h2>Authentication Error</h2>
                <p>{{error}}</p>
                <p>Redirecting to home page...</p>
            </div>
        </body>
        </html>
        """, error=error), 400
    
    if not code:
        return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Error</title>
            <meta http-equiv="refresh" content="3;url=/">
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .error { color: #d32f2f; background: #ffebee; padding: 20px; border-radius: 8px; }
            </style>
        </head>
        <body>
            <div class="error">
                <h2>Authentication Error</h2>
                <p>No authorization code provided.</p>
                <p>Redirecting to home page...</p>
            </div>
        </body>
        </html>
        """), 400

    # Render a page that grabs code_verifier from sessionStorage and POSTs it to /auth/exchange
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Completing Authentication...</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .container {
                background: white;
                padding: 40px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 400px;
            }
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            h2 { color: #333; margin-bottom: 10px; }
            p { color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Completing Authentication...</h2>
            <div class="spinner"></div>
            <p>Please wait while we complete your authentication.</p>
        </div>
        <script>
            (function() {
                const code = '{{code}}';
                const codeVerifier = sessionStorage.getItem('pkce_code_verifier');
                
                if (!codeVerifier) {
                    alert('Authentication error: Code verifier not found. Please try again.');
                    window.location = '/';
                    return;
                }
                
                fetch('/auth/exchange', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ code: code, code_verifier: codeVerifier })
                }).then(response => {
                    if (response.ok) {
                        // Clear the code verifier
                        sessionStorage.removeItem('pkce_code_verifier');
                        window.location = '/';
                    } else {
                        response.text().then(text => {
                            alert('Authentication failed: ' + text);
                            window.location = '/';
                        });
                    }
                }).catch(error => {
                    console.error('Error:', error);
                    alert('Authentication error. Please try again.');
                    window.location = '/';
                });
            })();
        </script>
    </body>
    </html>
    """, code=code)

@app.route('/auth/exchange', methods=['POST'])
def auth_exchange():
    """Exchange authorization code for access token (OAuth 2.0 with PKCE)"""
    data = request.get_json()
    code = data.get('code')
    code_verifier = data.get('code_verifier')
    if not code or not code_verifier:
        return jsonify({'error': 'Missing code or code_verifier'}), 400

    redirect_uri = f"{request.url_root.rstrip('/')}/auth/callback"
    token_url = f"https://{LOGIN_URL}/services/oauth2/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "code_verifier": code_verifier
    }

    logger.info(f"Exchanging code for token: {token_url}")
    logger.debug(f"Redirect URI: {redirect_uri}")
    
    resp = requests.post(token_url, data=payload, timeout=30)
    logger.info(f"Token exchange response status: {resp.status_code}")
    
    if resp.status_code != 200:
        logger.error(f"Token exchange failed: {resp.text}")
        return jsonify({
            'error': f'Error exchanging code for token: {resp.text}'
        }), 400

    token_data = resp.json()
    access_token = token_data.get("access_token")
    instance_url = token_data.get("instance_url")
    
    if not access_token or not instance_url:
        return jsonify({
            'error': 'Invalid token response from Salesforce'
        }), 400
    
    # Store in session (runtime only, no database)
    session['access_token'] = access_token
    session['instance_url'] = instance_url
    session['authenticated'] = True
    session['auth_time'] = datetime.now().isoformat()
    
    logger.info("Token stored in session successfully")
    
    return '', 204

@app.route('/api/auth-status', methods=['GET'])
def auth_status():
    """Check authentication status"""
    try:
        is_authenticated = session.get('authenticated', False)
        has_token = bool(session.get('access_token'))
        
        return jsonify({
            'serverTime': datetime.now().isoformat(),
            'status': 'running',
            'authenticated': is_authenticated and has_token,
            'instance_url': session.get('instance_url', '') if is_authenticated else '',
            'message': 'Access token found' if (is_authenticated and has_token) else 'Access token not found. Please authenticate first.'
        })
    except Exception as e:
        return jsonify({
            'serverTime': datetime.now().isoformat(),
            'status': 'error',
            'authenticated': False,
            'error': 'Failed to check authentication status',
            'details': str(e)
        }), 500

@app.route('/api/generate-schema', methods=['POST'])
def generate_schema():
    """Generate schema from uploaded document"""
    try:
        if not session.get('authenticated'):
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Read file and convert to base64
        file_data = file.read()
        base64_data = base64.b64encode(file_data).decode('utf-8')
        
        # Determine file type
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        mime_types = {
            'pdf': 'application/pdf',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'tiff': 'image/tiff',
            'bmp': 'image/bmp'
        }
        mime_type = mime_types.get(file_ext, 'application/octet-stream')
        
        # Generate a basic schema based on document type
        # This is a simple schema generator - in production, you might want more sophisticated logic
        schema = {
            "version": "1.0",
            "fields": [
                {
                    "name": "document_type",
                    "type": "string",
                    "description": "Type of document"
                },
                {
                    "name": "text_content",
                    "type": "text",
                    "description": "Full text content extracted from the document"
                },
                {
                    "name": "key_information",
                    "type": "object",
                    "description": "Key information extracted from the document",
                    "properties": {}
                }
            ]
        }
        
        # Store file info in session for later use
        session['uploaded_file'] = {
            'filename': file.filename,
            'base64_data': base64_data,
            'mime_type': mime_type,
            'size': len(file_data)
        }
        session['generated_schema'] = schema
        
        return jsonify({
            'success': True,
            'schema': schema,
            'filename': file.filename,
            'mime_type': mime_type
        })
        
    except Exception as e:
        logger.error(f"Error generating schema: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error generating schema: {str(e)}'
        }), 500

@app.route('/api/process-document', methods=['POST'])
def process_document():
    """Process document using Document AI endpoint"""
    try:
        if not session.get('authenticated'):
            return jsonify({
                'success': False,
                'error': 'Authentication required'
            }), 401
        
        data = request.get_json()
        schema = data.get('schema')
        ml_model = data.get('mlModel', DEFAULT_ML_MODEL)
        
        if not schema:
            return jsonify({
                'success': False,
                'error': 'Schema is required'
            }), 400
        
        # Get file from session
        file_info = session.get('uploaded_file')
        if not file_info:
            return jsonify({
                'success': False,
                'error': 'No file found. Please upload a file first.'
            }), 400
        
        access_token = session.get('access_token')
        instance_url = session.get('instance_url')
        
        if not access_token or not instance_url:
            return jsonify({
                'success': False,
                'error': 'Authentication required. Please authenticate with Salesforce first.'
            }), 401
        
        # Prepare Document AI request
        url = f"{instance_url}/services/data/{API_VERSION}/ssot/document-processing/actions/extract-data"
        
        payload = {
            "mlModel": ml_model,
            "schemaConfig": json.dumps(schema) if isinstance(schema, dict) else schema,
            "files": [
                {
                    "mimeType": file_info['mime_type'],
                    "data": file_info['base64_data']
                }
            ]
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        logger.info(f"Calling Document AI endpoint: {url}")
        logger.debug(f"Payload keys: {list(payload.keys())}")
        
        response = requests.post(url, headers=headers, json=payload, timeout=160)
        
        logger.info(f"Document AI response status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            try:
                json_response = response.json()
                logger.debug(f"Response structure: {list(json_response.keys()) if isinstance(json_response, dict) else 'list'}")
                
                if 'data' in json_response and len(json_response['data']) > 0:
                    result_data = json_response['data'][0]
                    
                    if 'error' in result_data:
                        return jsonify({
                            'success': False,
                            'error': result_data['error']
                        }), 500
                    
                    if 'data' in result_data:
                        # Parse the nested JSON string
                        extracted_data_str = result_data['data']
                        # Replace HTML entities
                        extracted_data_str = extracted_data_str.replace('&quot;', '"').replace('&#92;', '\\')
                        extracted_data = json.loads(extracted_data_str)
                        
                        return jsonify({
                            'success': True,
                            'data': extracted_data
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'error': 'No extracted data in response'
                        }), 500
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Unexpected response format'
                    }), 500
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error parsing response: {str(e)}',
                    'raw_response': response.text[:500]
                }), 500
        else:
            error_text = response.text
            try:
                error_json = response.json()
                error_text = error_json.get('message', error_json.get('error', error_text))
            except:
                pass
            
            return jsonify({
                'success': False,
                'error': f'Document AI request failed: {error_text}',
                'status_code': response.status_code
            }), response.status_code
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Network error: {str(e)}'
        }), 500
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error processing document: {str(e)}'
        }), 500

@app.route('/api/clear-token', methods=['POST'])
def clear_token():
    """Clear the access token to force re-authentication"""
    try:
        session.clear()
        return jsonify({
            'success': True,
            'message': 'Token cleared successfully. Please authenticate again.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to clear token',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    # Use port 5001 to avoid conflict with macOS AirPlay on port 5000
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=port, host='0.0.0.0')

