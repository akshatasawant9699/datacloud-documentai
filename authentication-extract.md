# Authentication Functionality Extract

This document contains the complete authentication functionality from the test-suite-idp project that can be ported to another project. The authentication flow uses Salesforce OAuth 2.0 with implicit grant flow.

## Overview

The authentication system consists of:
1. **Frontend**: Authentication button and callback handling
2. **Backend**: API endpoints for auth info and token storage
3. **Token Management**: Local file storage for access tokens
4. **OAuth Flow**: Salesforce OAuth 2.0 with implicit grant

## Environment Variables Required

```bash
# Salesforce Connected App Configuration
LOGIN_URL=your-salesforce-instance.salesforce.com
CLIENT_ID=your-connected-app-client-id
INSTANCE_URL=https://your-salesforce-instance.salesforce.com
API_VERSION=v60.0  # or your preferred API version
```

## Backend Components

### 1. Authentication API Endpoints (Express.js)

```javascript
// Authentication status check
app.get('/api/status', (req, res) => {
  try {
    const apiClient = new APIClient();
    const hasAccessToken = apiClient.isAuthenticated();
    
    res.json({
      serverTime: new Date().toISOString(),
      status: 'running',
      authenticated: hasAccessToken,
      message: hasAccessToken ? 'Access token found' : 'Access token not found. Please authenticate first.'
    });
  } catch (error) {
    res.status(500).json({
      serverTime: new Date().toISOString(),
      status: 'error',
      authenticated: false,
      error: 'Failed to check authentication status',
      details: error instanceof Error ? error.message : String(error)
    });
  }
});

// Get authentication configuration
app.get('/api/auth-info', (req, res) => {
  if (!process.env.LOGIN_URL || !process.env.CLIENT_ID) {
    return res.status(500).json({ error: 'Salesforce config missing on server' });
  }
  res.json({
    loginUrl: process.env.LOGIN_URL,
    clientId: process.env.CLIENT_ID,
  });
});

// OAuth callback page
app.get('/auth/callback', (req, res) => {
  res.sendFile(path.join(process.cwd(), 'public', 'callback.html'));
});

// Save access token
app.post('/api/save-token', async (req, res) => {
  try {
    const { accessToken } = req.body;
    
    if (!accessToken) {
      return res.status(400).json({ 
        success: false, 
        error: 'Access token is required' 
      });
    }
    
    // Save the access token to the secret file
    const tokenPath = path.join(process.cwd(), 'access-token.secret');
    await fs.writeFile(tokenPath, accessToken, 'utf-8');
    
    console.log('Access token saved successfully');
    
    res.json({
      success: true,
      message: 'Access token saved successfully'
    });
  } catch (error) {
    console.error('Error saving access token:', error);
    res.status(500).json({ 
      success: false,
      error: 'Failed to save access token',
      details: error instanceof Error ? error.message : String(error)
    });
  }
});
```

### 2. API Client for Token Management

```javascript
import axios, { AxiosResponse } from 'axios';
import fs from 'fs';
import path from 'path';

export class APIClient {
    private BASE_URL: string;

    constructor() {
        this.BASE_URL = `${process.env.INSTANCE_URL}/services/data/${process.env.API_VERSION}/ssot/document-processing`;
    }

    private loadAccessToken(): string {
        const tokenPath = path.join(process.cwd(), 'access-token.secret');
        if (!fs.existsSync(tokenPath)) {
            throw new Error('Access token not found. Please authenticate with Salesforce first.');
        }
        return fs.readFileSync(tokenPath, 'utf-8').trim();
    }

    public isAuthenticated(): boolean {
        try {
            const accessToken = this.loadAccessToken();
            return accessToken !== null && accessToken.trim() !== '';
        } catch (error) {
            return false;
        }
    }

    // Use this method to get the token for API calls
    public getAccessToken(): string {
        return this.loadAccessToken();
    }
}
```

## Frontend Components

### 1. Authentication Button (HTML)

```html
<div class="auth-section">
    <button id="auth-button" class="btn btn-compact">🔐 Authenticate</button>
</div>
```

### 2. Authentication Function (JavaScript)

```javascript
async function authenticateWithSalesforce() {
    try {
        const response = await fetch('/api/auth-info');
        const data = await response.json();
        
        if (!data.loginUrl || !data.clientId) {
            showNotification('Salesforce configuration missing on server', 'error');
            return;
        }
        
        const redirectUri = encodeURIComponent(`${window.location.origin}/auth/callback`);
        const authUrl = `https://${data.loginUrl}/services/oauth2/authorize?response_type=token&client_id=${data.clientId}&redirect_uri=${redirectUri}&scope=api%20cdp_query_api%20cdp_profile_api`;
        
        // Redirect to the auth URL
        window.location.href = authUrl;
        
    } catch (error) {
        showNotification('Failed to initiate authentication: ' + error.message, 'error');
    }
}

// Add event listener
document.getElementById('auth-button').addEventListener('click', authenticateWithSalesforce);
```

### 3. OAuth Callback Page (HTML)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Authentication Callback</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f0f2f5;
        }
        .container {
            text-align: center;
            padding: 40px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            max-width: 800px;
        }
        h1 { color: #333; }
        p { color: #555; word-break: break-all; max-width: 600px; }
        pre {
            background-color: #eee;
            padding: 10px;
            border-radius: 4px;
            text-align: left;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-all;
        }
        .countdown {
            font-size: 1.2em;
            color: #007bff;
            margin: 20px 0;
        }
        .redirect-link {
            margin-top: 20px;
        }
        .redirect-link a {
            color: #007bff;
            text-decoration: none;
            font-weight: bold;
        }
        .redirect-link a:hover {
            text-decoration: underline;
        }
        .status {
            margin: 10px 0;
            padding: 10px;
            border-radius: 4px;
        }
        .status.success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Authentication Successful</h1>
        <div id="status" class="status"></div>
        <p>Your access token has been saved and is displayed below:</p>
        <pre id="token-display"></pre>
        <div class="countdown" id="countdown">This page will close automatically in <span id="timer">5</span> seconds...</div>
        <div class="redirect-link">
            <a href="/" id="home-link">Click here to go to Home Page</a>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', async () => {
            const hash = window.location.hash.substring(1);
            const params = new URLSearchParams(hash);
            const accessToken = params.get('access_token');
            const statusDiv = document.getElementById('status');
            const tokenDisplay = document.getElementById('token-display');
            const countdown = document.getElementById('countdown');
            const timer = document.getElementById('timer');

            if (accessToken) {
                // Display the access token
                tokenDisplay.textContent = accessToken;
                console.log('Access Token:', accessToken);

                // Save access token via API
                try {
                    const response = await fetch('/api/save-token', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ accessToken })
                    });

                    if (response.ok) {
                        statusDiv.textContent = '✅ Access token saved successfully!';
                        statusDiv.className = 'status success';
                    } else {
                        throw new Error('Failed to save token');
                    }
                } catch (error) {
                    console.error('Error saving token:', error);
                    statusDiv.textContent = '❌ Error saving access token to file';
                    statusDiv.className = 'status error';
                }

                // Countdown timer and redirect
                let secondsLeft = 3;
                const countdownInterval = setInterval(() => {
                    secondsLeft--;
                    timer.textContent = secondsLeft;
                    
                    if (secondsLeft <= 0) {
                        clearInterval(countdownInterval);
                        window.location.href = '/';
                    }
                }, 1000);

            } else {
                tokenDisplay.textContent = 'Error: Could not retrieve access token.';
                statusDiv.textContent = '❌ Could not find access token in URL fragment';
                statusDiv.className = 'status error';
                countdown.style.display = 'none';
                console.error('Could not find access token in URL fragment');
            }
        });
    </script>
</body>
</html>
```

## Authentication Flow

1. **User clicks "Authenticate" button**
   - Frontend calls `/api/auth-info` to get Salesforce configuration
   - Constructs OAuth URL with client_id, redirect_uri, and scopes
   - Redirects user to Salesforce login page

2. **User logs into Salesforce**
   - User enters credentials on Salesforce login page
   - Salesforce redirects back to callback URL with access token in URL fragment

3. **Callback page processes token**
   - Extracts access token from URL fragment
   - Sends token to `/api/save-token` endpoint
   - Backend saves token to `access-token.secret` file
   - Shows success message and auto-redirects after 3 seconds

4. **Token is available for API calls**
   - `APIClient.isAuthenticated()` checks if token exists
   - `APIClient.getAccessToken()` retrieves token for API calls
   - Token is used in Authorization header: `Bearer ${accessToken}`

## Usage in Your Project

### For Node.js/Express Projects:

1. **Copy the backend endpoints** to your server
2. **Add the APIClient class** for token management
3. **Set up environment variables** for Salesforce configuration
4. **Add the callback HTML page** to your public directory
5. **Implement the authentication button** in your frontend

### For Python/Flask Projects:

```python
# Flask equivalent of the authentication endpoints
from flask import Flask, request, jsonify, send_file
import os
import json

app = Flask(__name__)

@app.route('/api/status')
def check_auth_status():
    try:
        token_path = os.path.join(os.getcwd(), 'access-token.secret')
        has_token = os.path.exists(token_path) and os.path.getsize(token_path) > 0
        
        return jsonify({
            'serverTime': datetime.now().isoformat(),
            'status': 'running',
            'authenticated': has_token,
            'message': 'Access token found' if has_token else 'Access token not found. Please authenticate first.'
        })
    except Exception as e:
        return jsonify({
            'serverTime': datetime.now().isoformat(),
            'status': 'error',
            'authenticated': False,
            'error': 'Failed to check authentication status',
            'details': str(e)
        }), 500

@app.route('/api/auth-info')
def get_auth_info():
    login_url = os.getenv('LOGIN_URL')
    client_id = os.getenv('CLIENT_ID')
    
    if not login_url or not client_id:
        return jsonify({'error': 'Salesforce config missing on server'}), 500
    
    return jsonify({
        'loginUrl': login_url,
        'clientId': client_id,
    })

@app.route('/auth/callback')
def auth_callback():
    return send_file('public/callback.html')

@app.route('/api/save-token', methods=['POST'])
def save_token():
    try:
        data = request.get_json()
        access_token = data.get('accessToken')
        
        if not access_token:
            return jsonify({
                'success': False,
                'error': 'Access token is required'
            }), 400
        
        # Save the access token to the secret file
        token_path = os.path.join(os.getcwd(), 'access-token.secret')
        with open(token_path, 'w') as f:
            f.write(access_token)
        
        print('Access token saved successfully')
        
        return jsonify({
            'success': True,
            'message': 'Access token saved successfully'
        })
    except Exception as e:
        print(f'Error saving access token: {e}')
        return jsonify({
            'success': False,
            'error': 'Failed to save access token',
            'details': str(e)
        }), 500

# API Client equivalent for Python
class APIClient:
    def __init__(self):
        self.base_url = f"{os.getenv('INSTANCE_URL')}/services/data/{os.getenv('API_VERSION')}/ssot/document-processing"
    
    def load_access_token(self):
        token_path = os.path.join(os.getcwd(), 'access-token.secret')
        if not os.path.exists(token_path):
            raise Exception('Access token not found. Please authenticate with Salesforce first.')
        
        with open(token_path, 'r') as f:
            return f.read().strip()
    
    def is_authenticated(self):
        try:
            access_token = self.load_access_token()
            return access_token is not None and access_token.strip() != ''
        except Exception:
            return False
    
    def get_access_token(self):
        return self.load_access_token()
```

## Security Notes

1. **Token Storage**: Access tokens are stored in a local file (`access-token.secret`). In production, consider using more secure storage methods.

2. **Token Expiration**: Salesforce access tokens expire. Implement token refresh logic or re-authentication prompts.

3. **HTTPS**: Always use HTTPS in production for secure token transmission.

4. **Callback URL**: Ensure your callback URL is properly configured in your Salesforce Connected App.

## Dependencies

### Node.js Dependencies:
```json
{
  "express": "^4.21.2",
  "cors": "^2.8.5",
  "fs-extra": "^11.1.1",
  "dotenv": "^16.5.0"
}
```

### Python Dependencies:
```txt
Flask==2.3.3
python-dotenv==1.0.0
requests==2.31.0
```

This authentication system provides a complete OAuth 2.0 flow for Salesforce integration that can be easily ported to any web application. 