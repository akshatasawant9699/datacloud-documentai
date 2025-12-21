from http.server import BaseHTTPRequestHandler
import json
import requests
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.utils import create_response, API_VERSION, DEFAULT_ML_MODEL

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_POST(self):
        """Handle document processing requests"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            access_token = data.get('access_token')
            instance_url = data.get('instance_url')
            schema = data.get('schema')
            ml_model = data.get('mlModel', DEFAULT_ML_MODEL)
            api_version = data.get('api_version', API_VERSION)
            
            # AUTO-FIX: v60.0 is too old for Document AI. Force upgrade to v65.0.
            if api_version == 'v60.0':
                api_version = 'v65.0'
                
            file_data = data.get('file')
            idp_config_name = data.get('idpConfigurationIdOrName')
            
            if not access_token or not instance_url:
                response = create_response(401, {
                    'success': False,
                    'error': 'Authentication required. Please authenticate with Salesforce first.'
                })
                self.send_response(response['statusCode'])
                for key, value in response['headers'].items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(response['body'].encode('utf-8'))
                return
            
            # Schema is required ONLY if not using IDP Config
            if not idp_config_name and not schema:
                response = create_response(400, {
                    'success': False,
                    'error': 'Schema is required when not using a pre-configured IDP'
                })
                self.send_response(response['statusCode'])
                for key, value in response['headers'].items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(response['body'].encode('utf-8'))
                return
            
            if not file_data:
                response = create_response(400, {
                    'success': False,
                    'error': 'File data is required'
                })
                self.send_response(response['statusCode'])
                for key, value in response['headers'].items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(response['body'].encode('utf-8'))
                return
            
            # Prepare Document AI request
            url = f"{instance_url}/services/data/{api_version}/ssot/document-processing/actions/extract-data"
            
            # Check if idpConfigurationIdOrName is provided
            idp_config = idp_config_name
            
            # schemaConfig must be a JSON string (escaped), not an object
            schema_config_str = json.dumps(schema) if isinstance(schema, dict) else schema
            if not schema_config_str:
                 schema_config_str = "{}"
            
            if idp_config:
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
            api_response = requests.post(url, headers=headers, json=payload, timeout=160)
            
            if api_response.status_code in [200, 201]:
                try:
                    json_response = api_response.json()
                    
                    if 'data' in json_response and len(json_response['data']) > 0:
                        result_data = json_response['data'][0]
                        
                        # Check for error (ignore if None)
                        if result_data.get('error'):
                            response = create_response(500, {
                                'success': False,
                                'error': result_data['error']
                            })
                        # Check for data
                        elif 'data' in result_data and result_data['data']:
                            # Parse the nested JSON string
                            extracted_data_str = result_data['data']
                            # Replace HTML entities
                            extracted_data_str = extracted_data_str.replace('&quot;', '"').replace('&#92;', '\\')
                            try:
                                extracted_data = json.loads(extracted_data_str)
                                response = create_response(200, {
                                    'success': True,
                                    'data': extracted_data
                                })
                            except Exception as e:
                                response = create_response(500, {
                                    'success': False,
                                    'error': f'Failed to parse extracted data: {str(e)}'
                                })
                        else:
                            response = create_response(500, {
                                'success': False,
                                'error': 'No extracted data in response'
                            })
                    else:
                        response = create_response(500, {
                            'success': False,
                            'error': 'Unexpected response format'
                        })
                        
                except json.JSONDecodeError as e:
                    response = create_response(500, {
                        'success': False,
                        'error': f'Error parsing response: {str(e)}',
                        'raw_response': api_response.text[:500]
                    })
            else:
                error_text = api_response.text
                try:
                    error_json = api_response.json()
                    error_text = error_json.get('message', error_json.get('error', error_text))
                except:
                    pass
                
                response = create_response(api_response.status_code, {
                    'success': False,
                    'error': f'Document AI request failed: {error_text}',
                    'status_code': api_response.status_code
                })
            
            self.send_response(response['statusCode'])
            for key, value in response['headers'].items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response['body'].encode('utf-8'))
            
        except requests.exceptions.RequestException as e:
            response = create_response(500, {
                'success': False,
                'error': f'Network error: {str(e)}'
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

