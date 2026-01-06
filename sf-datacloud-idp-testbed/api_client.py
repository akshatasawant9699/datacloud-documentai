import os
import json
from typing import Optional
from config import TOKEN_FILE

class APIClient:
    def __init__(self):
        self.token_file = TOKEN_FILE
    
    def load_token_data(self):
        if not os.path.exists(self.token_file):
            raise Exception('Token file not found. Please authenticate.')
        with open(self.token_file, 'r') as f:
            return json.load(f)
    
    def get_access_token(self):
        return self.load_token_data().get('access_token')
    
    def get_instance_url(self):
        return self.load_token_data().get('instance_url')
    
    def is_authenticated(self):
        try:
            data = self.load_token_data()
            return bool(data.get('access_token')) and bool(data.get('instance_url'))
        except Exception:
            return False
    
    def save_access_token(self, access_token: str) -> None:
        """Save access token to local storage"""
        with open(self.token_file, 'w') as f:
            f.write(access_token.strip()) 