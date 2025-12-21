import os
from dotenv import load_dotenv

# Load .env file from the same directory as this config file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(env_path)

LOGIN_URL = os.environ.get("LOGIN_URL", "login.salesforce.com")
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
API_VERSION = os.environ.get("API_VERSION", "v60.0")

DEFAULT_ML_MODEL = "llmgateway__VertexAIGemini20Flash001"

