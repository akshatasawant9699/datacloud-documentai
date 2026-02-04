import os
import json
from typing import Optional
from config import TOKEN_FILE

class APIClient:
    """
    API Client for managing Salesforce authentication tokens.
    Supports both local file storage and environment variables for serverless deployments.
    """
    
    def __init__(self):
        self.token_file = TOKEN_FILE
        self._cached_token_data = None
    
    def load_token_data(self):
        """Load token data from file or cache"""
        if self._cached_token_data:
            return self._cached_token_data
            
        if not os.path.exists(self.token_file):
            raise Exception('Token file not found. Please authenticate.')
        
        with open(self.token_file, 'r') as f:
            content = f.read().strip()
            # Handle both JSON format and plain token format
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                # If it's just a plain token, create a data structure
                data = {'access_token': content}
            
            self._cached_token_data = data
            return data
    
    def get_access_token(self):
        """Get the access token"""
        try:
            return self.load_token_data().get('access_token')
        except Exception:
            return None
    
    def get_instance_url(self):
        """Get the Salesforce instance URL"""
        try:
            return self.load_token_data().get('instance_url')
        except Exception:
            # Fallback to environment variable
            return os.environ.get('INSTANCE_URL')
    
    def is_authenticated(self):
        """Check if we have valid authentication"""
        try:
            data = self.load_token_data()
            return bool(data.get('access_token')) and bool(data.get('instance_url'))
        except Exception:
            return False
    
    def save_access_token(self, access_token: str, instance_url: str = None) -> None:
        """Save access token and instance URL to local storage"""
        data = {
            'access_token': access_token.strip() if access_token else None,
            'instance_url': instance_url
        }
        
        # Try to preserve existing instance_url if not provided
        if not instance_url:
            try:
                existing = self.load_token_data()
                data['instance_url'] = existing.get('instance_url')
            except Exception:
                pass
        
        with open(self.token_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Update cache
        self._cached_token_data = data
    
    def clear_token(self) -> None:
        """Clear the stored token"""
        self._cached_token_data = None
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
