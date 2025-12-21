import os
import json
import requests
from datetime import datetime

# Load environment variables
LOGIN_URL = os.environ.get("LOGIN_URL", "login.salesforce.com")
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
API_VERSION = os.environ.get("API_VERSION", "v60.0")
DEFAULT_ML_MODEL = os.environ.get("DEFAULT_ML_MODEL", "llmgateway__VertexAIGemini20Flash001")

def normalize_login_url(login_url):
    """Normalize login URL by removing protocol and trailing slashes"""
    if not login_url:
        return "login.salesforce.com"
    
    # Remove protocol
    if login_url.startswith("https://"):
        login_url = login_url[8:]
    elif login_url.startswith("http://"):
        login_url = login_url[7:]
    
    # Remove trailing slash
    login_url = login_url.rstrip('/')
    
    return login_url

def authenticate_with_salesforce(username, password, security_token=None, login_url=None, client_id=None, client_secret=None):
    """Authenticate with Salesforce using Username/Password OAuth flow"""
    try:
        # Use provided config or fall back to environment variables
        use_login_url = login_url or LOGIN_URL
        use_client_id = client_id or CLIENT_ID
        use_client_secret = client_secret or CLIENT_SECRET
        
        if not use_login_url or not use_client_id or not use_client_secret:
            return {
                "success": False,
                "error": "Missing required configuration: LOGIN_URL, CLIENT_ID, and CLIENT_SECRET are required"
            }
        
        login_url_normalized = normalize_login_url(use_login_url)
        token_url = f"https://{login_url_normalized}/services/oauth2/token"
        
        # Combine password and security token
        full_password = password
        if security_token:
            full_password = password + security_token
        
        payload = {
            "grant_type": "password",
            "client_id": use_client_id,
            "client_secret": use_client_secret,
            "username": username,
            "password": full_password
        }
        
        response = requests.post(token_url, data=payload, timeout=30)
        
        if response.status_code == 200:
            token_data = response.json()
            return {
                "success": True,
                "access_token": token_data.get("access_token"),
                "instance_url": token_data.get("instance_url"),
                "token_type": token_data.get("token_type", "Bearer")
            }
        else:
            error_text = response.text
            error_code = None
            try:
                error_json = response.json()
                error_code = error_json.get("error", "")
                error_description = error_json.get("error_description", error_json.get("error", error_text))
                
                # Provide more helpful error messages
                if error_code == "invalid_grant":
                    if "authentication failure" in error_description.lower():
                        error_text = "Authentication failure. This usually means:\n1. Username or password is incorrect\n2. Your IP is not whitelisted - you need to add a Security Token to your password\n3. The Connected App may not be configured correctly"
                    else:
                        error_text = f"Invalid grant: {error_description}"
                elif error_code == "invalid_client_id":
                    error_text = "Invalid Client ID. Please check your Connected App Client ID."
                elif error_code == "invalid_client":
                    error_text = "Invalid Client ID or Client Secret. Please check your Connected App credentials."
                else:
                    error_text = error_description
            except:
                pass
            
            return {
                "success": False,
                "error": f"Authentication failed: {error_text}",
                "status_code": response.status_code,
                "error_code": error_code
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Authentication error: {str(e)}"
        }

def create_response(status_code, body, headers=None):
    """Create a Vercel-compatible response"""
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(body) if isinstance(body, dict) else body
    }

