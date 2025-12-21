"""
Local Flask server for testing - proxies to API endpoints
Run this locally: python backend/app_local.py
"""
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import requests
import base64
import json
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add api directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api'))
from utils import authenticate_with_salesforce, create_response, API_VERSION, DEFAULT_ML_MODEL

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

app = Flask(__name__, 
            template_folder=os.path.join(FRONTEND_DIR, 'templates'),
            static_folder=os.path.join(FRONTEND_DIR, 'static'),
            static_url_path='/static')
app.secret_key = os.urandom(24)
CORS(app, resources={r"/*": {"origins": "*"}})

# Error handlers to ensure JSON responses
@app.errorhandler(404)
def not_found(error):
    from flask import request
    try:
        if request.path.startswith('/api/'):
            response = jsonify({'success': False, 'error': 'API endpoint not found'})
            response.status_code = 404
            return response
    except:
        pass
    return error

@app.errorhandler(500)
def internal_error(error):
    from flask import request
    try:
        if request.path.startswith('/api/'):
            response = jsonify({'success': False, 'error': 'Internal server error'})
            response.status_code = 500
            return response
    except:
        pass
    return error

@app.route('/')
def index():
    # Serve index.html from root
    index_path = os.path.join(BASE_DIR, 'index.html')
    if os.path.exists(index_path):
        return open(index_path).read()
    return render_template('index.html')

@app.route('/auth/callback')
def oauth_callback():
    """OAuth callback handler - renders page that exchanges code for token"""
    code = request.args.get('code')
    error = request.args.get('error')
    state = request.args.get('state')
    
    if error:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Error</title>
            <meta http-equiv="refresh" content="3;url=/">
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .error {{ color: #d32f2f; background: #ffebee; padding: 20px; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h2>Authentication Error</h2>
                <p>{error}</p>
                <p>Redirecting to home page...</p>
            </div>
        </body>
        </html>
        """, 400
    
    if not code:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Error</title>
            <meta http-equiv="refresh" content="3;url=/">
        </head>
        <body>
            <div class="error">
                <h2>Authentication Error</h2>
                <p>No authorization code provided.</p>
                <p>Redirecting to home page...</p>
            </div>
        </body>
        </html>
        """, 400
    
    # Render page that will exchange code for token via JavaScript
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Completing Authentication...</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 400px;
            }}
            .spinner {{
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }}
            .error-message {{
                color: #d32f2f;
                background: #ffebee;
                padding: 15px;
                border-radius: 6px;
                margin-top: 20px;
                display: none;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Completing Authentication...</h2>
            <div id="loader">
                <div class="spinner"></div>
                <p>Please wait while we complete your authentication.</p>
            </div>
            <div id="error" class="error-message"></div>
            <button id="retryBtn" onclick="window.location='/'" style="display:none; margin-top:20px; padding:10px 20px; background:#667eea; color:white; border:none; border-radius:6px; cursor:pointer;">Return to Home</button>
        </div>
        <script>
            (function() {{
                const code = '{code}';
                const state = '{state}';
                
                // Prevent duplicate execution
                if (window.authProcessing) return;
                window.authProcessing = true;
                
                function showError(msg) {{
                    document.getElementById('loader').style.display = 'none';
                    const errorDiv = document.getElementById('error');
                    errorDiv.textContent = msg;
                    errorDiv.style.display = 'block';
                    document.getElementById('retryBtn').style.display = 'inline-block';
                }}

                // Get config from sessionStorage (stored before redirect)
                const savedConfig = sessionStorage.getItem('sf_config_temp');
                if (!savedConfig) {{
                    showError('Configuration not found. Please configure the app first.');
                    return;
                }}
                
                let config;
                try {{
                    config = JSON.parse(savedConfig);
                }} catch (e) {{
                    showError('Invalid configuration data.');
                    return;
                }}
                
                fetch('/api/oauth/callback', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        code: code,
                        state: state,
                        login_url: config.LOGIN_URL,
                        client_id: config.CLIENT_ID,
                        client_secret: config.CLIENT_SECRET
                    }})
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        // Store tokens in localStorage
                        localStorage.setItem('sf_access_token', data.access_token);
                        localStorage.setItem('sf_instance_url', data.instance_url);
                        // Clear temp config
                        sessionStorage.removeItem('sf_config_temp');
                        sessionStorage.removeItem('oauth_state');
                        // Redirect to home
                        window.location.replace('/');
                    }} else {{
                        showError('Authentication failed: ' + (data.error || 'Unknown error'));
                        sessionStorage.removeItem('sf_config_temp');
                    }}
                }})
                .catch(error => {{
                    console.error('Error:', error);
                    showError('Authentication error. Please check console for details.');
                    sessionStorage.removeItem('sf_config_temp');
                }});
            }})();
        </script>
    </body>
    </html>
    """

@app.route('/api/oauth/callback', methods=['POST', 'OPTIONS'])
def api_oauth_callback():
    """Exchange OAuth authorization code for access token"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        if data is None:
            return jsonify({
                'success': False,
                'error': 'Invalid JSON in request body'
            }), 400
        
        code = data.get('code')
        login_url = data.get('login_url')
        client_id = data.get('client_id')
        client_secret = data.get('client_secret')
        
        if not code:
            return jsonify({
                'success': False,
                'error': 'Authorization code is required'
            }), 400
        
        if not login_url or not client_id or not client_secret:
            return jsonify({
                'success': False,
                'error': 'Login URL, Client ID, and Client Secret are required'
            }), 400
        
        # Exchange code for token
        # Use the exact same redirect URI that was used in the authorization request
        redirect_uri = f"{request.scheme}://{request.host}/auth/callback"
        token_url = f"https://{login_url}/services/oauth2/token"
        
        logger.info(f"Token exchange - Redirect URI: {redirect_uri}")
        
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri
        }
        
        response = requests.post(token_url, data=payload, timeout=30)
        
        if response.status_code == 200:
            token_data = response.json()
            return jsonify({
                'success': True,
                'access_token': token_data.get('access_token'),
                'instance_url': token_data.get('instance_url'),
                'token_type': token_data.get('token_type', 'Bearer')
            })
        else:
            error_text = response.text
            try:
                error_json = response.json()
                error_text = error_json.get('error_description', error_json.get('error', error_text))
            except:
                pass
            
            return jsonify({
                'success': False,
                'error': f'Token exchange failed: {error_text}'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/auth', methods=['POST', 'OPTIONS'])
def api_auth():
    """Handle authentication (kept for backward compatibility)"""
    if request.method == 'OPTIONS':
        return '', 200
    
    # Redirect to OAuth flow - Username/Password flow is deprecated in favor of OAuth redirect
    return jsonify({
        'success': False,
        'error': 'Please use OAuth login flow. Click "Login to Salesforce" button to be redirected to Salesforce login page.'
    }), 400

@app.route('/api/test-connection', methods=['POST', 'OPTIONS'])
def api_test_connection():
    """Test connection to Salesforce Document AI API with auto-discovery"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        access_token = data.get('access_token')
        instance_url = data.get('instance_url')
        current_version = data.get('api_version', 'v65.0')
        
        if not access_token or not instance_url:
            return jsonify({
                'success': False,
                'error': 'Access token and instance URL are required'
            }), 400
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Testing connection. Instance: {instance_url}, Version: {current_version}")
        
        # Versions to probe
        versions_to_try = ['v65.0', 'v64.0', 'v63.0', 'v62.0', 'v61.0', 'v60.0']
        # Move current version to top if it's not in the list
        if current_version not in versions_to_try:
            versions_to_try.insert(0, current_version)
        else:
            # Move it to top
            versions_to_try.remove(current_version)
            versions_to_try.insert(0, current_version)
            
        working_version = None
        working_endpoint = None
        idp_enabled = False
        
        results = []
        
        for version in versions_to_try:
            logger.info(f"Probing version {version}...")
            
            # 1. Check basic API access
            api_url = f"{instance_url}/services/data/{version}"
            resp = requests.get(api_url, headers=headers, timeout=5)
            
            if resp.status_code != 200:
                results.append(f"{version}: API not accessible ({resp.status_code})")
                continue
                
            # 2. Check Document AI Configurations endpoint
            # This confirms the IDP feature is enabled
            configs_url = f"{instance_url}/services/data/{version}/ssot/document-processing/configurations"
            resp_conf = requests.get(configs_url, headers=headers, timeout=5)
            
            if resp_conf.status_code == 200:
                logger.info(f"Found working IDP endpoint at {version}")
                working_version = version
                working_endpoint = configs_url
                idp_enabled = True
                
                # Get available configs
                configs = resp_conf.json()
                
                return jsonify({
                    'success': True,
                    'message': f'Document AI is enabled and accessible on {version}',
                    'api_version': version,
                    'configurations': configs,
                    'auto_updated': version != current_version
                })
            
            elif resp_conf.status_code == 404:
                 # 3. Try the Extract Data endpoint directly (POST with empty body just to check existence, or OPTIONS)
                 # Note: A GET on a POST-only endpoint usually returns 405 Method Not Allowed, which proves existence!
                 # If it returns 404, it doesn't exist.
                 extract_url = f"{instance_url}/services/data/{version}/ssot/document-processing/actions/extract-data"
                 resp_extract = requests.post(extract_url, headers=headers, json={}, timeout=5)
                 
                 # 400 Bad Request means it exists but payload was empty (GOOD)
                 # 405 Method Not Allowed means it exists (GOOD)
                 # 404 Not Found means it doesn't exist (BAD)
                 if resp_extract.status_code in [400, 405]:
                     logger.info(f"Found working Extract Data endpoint at {version} (Status: {resp_extract.status_code})")
                     working_version = version
                     return jsonify({
                        'success': True,
                        'message': f'Document AI Extract endpoint found on {version}',
                        'api_version': version,
                        'warning': 'Could not list configurations, but extraction endpoint exists.',
                        'auto_updated': version != current_version
                    })
                 
                 results.append(f"{version}: IDP endpoints not found (404)")
            else:
                results.append(f"{version}: Error {resp_conf.status_code}")
                
        # If we get here, no version worked
        return jsonify({
            'success': False,
            'error': 'Could not find working Document AI endpoint on any supported version.',
            'details': results,
            'suggestion': 'Ensure "Intelligent Document Processing" is enabled in Data Cloud Setup.'
        }), 404
            
    except Exception as e:
        logger.exception("Test connection error:")
        return jsonify({
            'success': False,
            'error': f'Test failed: {str(e)}'
        }), 500

@app.route('/api/generate-schema', methods=['POST', 'OPTIONS'])
def api_generate_schema():
    """Generate schema from uploaded document"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        if data is None:
            return jsonify({
                'success': False,
                'error': 'Invalid JSON in request body'
            }), 400
        filename = data.get('filename', 'document.pdf')
        mime_type = data.get('mime_type', 'application/pdf')
        base64_data = data.get('base64_data')
        
        if not base64_data:
            return jsonify({
                'success': False,
                'error': 'File data is required'
            }), 400
        
        # Import schema generator
        # Add api directory to path if not already there
        api_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api')
        if api_path not in sys.path:
            sys.path.append(api_path)
            
        # Use importlib to import the module since it contains a hyphen
        import importlib.util
        spec = importlib.util.spec_from_file_location("generate_schema", os.path.join(api_path, "generate-schema.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        schema = module.generate_schema_from_document(filename, mime_type)
        
        return jsonify({
            'success': True,
            'schema': schema,
            'filename': filename,
            'mime_type': mime_type
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/process-document', methods=['POST', 'OPTIONS'])
def api_process_document():
    """Process document using Document AI endpoint"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        if data is None:
            return jsonify({
                'success': False,
                'error': 'Invalid JSON in request body'
            }), 400
        access_token = data.get('access_token')
        instance_url = data.get('instance_url')
        schema = data.get('schema')
        ml_model = data.get('mlModel', DEFAULT_ML_MODEL)
        api_version = data.get('api_version', API_VERSION)
        
        # AUTO-FIX: v60.0 is too old for Document AI. Force upgrade to v65.0.
        if api_version == 'v60.0':
            api_version = 'v65.0'
            logger.info("Auto-upgraded API version from v60.0 to v65.0")
            
        file_data = data.get('file')
        idp_config_name = data.get('idpConfigurationIdOrName')
        
        if not access_token or not instance_url:
            return jsonify({
                'success': False,
                'error': 'Authentication required. Please authenticate with Salesforce first.'
            }), 401
        
        # Schema is required ONLY if not using IDP Config
        if not idp_config_name and not schema:
            return jsonify({
                'success': False,
                'error': 'Schema is required when not using a pre-configured IDP'
            }), 400
        
        if not file_data:
            return jsonify({
                'success': False,
                'error': 'File data is required'
            }), 400
        
        # Prepare Document AI request
        # URL without query params as shown in Postman
        url = f"{instance_url}/services/data/{api_version}/ssot/document-processing/actions/extract-data"
        
        logger.info(f"=== Document AI Request ===")
        logger.info(f"URL: {url}")
        logger.info(f"Instance URL: {instance_url}")
        logger.info(f"API Version: {api_version}")
        
        # Check if idpConfigurationIdOrName is provided (pre-configured Document AI)
        idp_config = idp_config_name
        
        # schemaConfig must be a JSON string (escaped), not an object
        schema_config_str = json.dumps(schema) if isinstance(schema, dict) else schema
        
        if idp_config:
            # Use pre-configured Document AI configuration
            logger.info(f"Using IDP Configuration: {idp_config}")
            payload = {
                "idpConfigurationIdOrName": idp_config,
                "files": [
                    {
                        "mimeType": file_data.get('mime_type', 'application/pdf'),
                        "data": file_data.get('base64_data')
                    }
                ]
            }
        else:
            # Use dynamic schema with ML model (as shown in Postman)
            logger.info(f"Using ML Model: {ml_model}")
            # Ensure schema_config_str is not None
            if not schema_config_str:
                 schema_config_str = "{}" 
            
            logger.info(f"Schema Config: {str(schema_config_str)[:200]}...")
            
            payload = {
                "mlModel": ml_model,
                "schemaConfig": schema_config_str,
                "files": [
                    {
                        "mimeType": file_data.get('mime_type', 'application/pdf'),
                        "data": file_data.get('base64_data')[:50] + "..." if file_data.get('base64_data') else None
                    }
                ]
            }
            # Log payload keys only (not full base64)
            logger.info(f"Payload keys: {list(payload.keys())}")
            
            # Rebuild actual payload for the request
            payload = {
                "mlModel": ml_model,
                "schemaConfig": schema_config_str,
                "files": [
                    {
                        "mimeType": file_data.get('mime_type', 'application/pdf'),
                        "data": file_data.get('base64_data')
                    }
                ]
            }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        # Make request to Document AI API
        response = requests.post(url, headers=headers, json=payload, timeout=160)
        
        logger.info(f"API Response Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            try:
                json_response = response.json()
                logger.info(f"API Response Content (Keys): {list(json_response.keys())}")
                
                if 'data' in json_response and len(json_response['data']) > 0:
                    result_data = json_response['data'][0]
                    logger.info(f"Result Data Keys: {list(result_data.keys())}")
                    
                    # Check for error (ignore if None)
                    if result_data.get('error'):
                        logger.error(f"API returned error in data: {result_data['error']}")
                        return jsonify({
                            'success': False,
                            'error': result_data['error']
                        }), 500
                    
                    # Check for data
                    if 'data' in result_data and result_data['data']:
                        # Parse the nested JSON string
                        extracted_data_str = result_data['data']
                        # Replace HTML entities
                        extracted_data_str = extracted_data_str.replace('&quot;', '"').replace('&#92;', '\\')
                        try:
                            extracted_data = json.loads(extracted_data_str)
                            return jsonify({
                                'success': True,
                                'data': extracted_data
                            })
                        except Exception as e:
                            logger.error(f"Failed to parse inner JSON: {str(e)}")
                            logger.error(f"Inner JSON content: {extracted_data_str[:500]}")
                            return jsonify({
                                'success': False,
                                'error': f'Failed to parse extracted data: {str(e)}'
                            }), 500
                    else:
                        logger.error(f"Unexpected result data keys: {list(result_data.keys())}")
                        return jsonify({
                            'success': False,
                            'error': 'No extracted data in response (missing "data" field)',
                            'raw_response': str(result_data)[:500]
                        }), 500
                else:
                    logger.error(f"Unexpected response format (no data list): {str(json_response)[:500]}")
                    return jsonify({
                        'success': False,
                        'error': 'Unexpected response format (no data list)',
                        'raw_response': str(json_response)[:500]
                    }), 500
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON Decode Error: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': f'Error parsing response: {str(e)}',
                    'raw_response': response.text[:500]
                }), 500
            except Exception as e:
                logger.exception("Error processing success response:")
                return jsonify({
                    'success': False,
                    'error': f'Processing error: {str(e)}'
                }), 500
        else:
            logger.error(f"API Error Response: {response.text}")
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
            
    except json.JSONDecodeError as e:
        return jsonify({
            'success': False,
            'error': f'Invalid JSON in request: {str(e)}'
        }), 400
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Network error: {str(e)}'
        }), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, port=port, host='0.0.0.0')

