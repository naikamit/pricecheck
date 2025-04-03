# /config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Tastytrade API configuration
TASTYTRADE_LOGIN = os.environ.get('TASTYTRADE_LOGIN')
TASTYTRADE_PASSWORD = os.environ.get('TASTYTRADE_PASSWORD')
API_BASE_URL = os.environ.get('API_BASE_URL', 'api.tastytrade.com')
ACCOUNT_NUMBER = os.environ.get('ACCOUNT_NUMBER')

# Flask configuration
FLASK_SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', os.urandom(24).hex())
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')

# Server configuration
PORT = int(os.environ.get('PORT', 8000))

# Logging configuration
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Validate required configuration
def validate_config():
    missing_vars = []
    
    if not TASTYTRADE_LOGIN:
        missing_vars.append('TASTYTRADE_LOGIN')
    if not TASTYTRADE_PASSWORD:
        missing_vars.append('TASTYTRADE_PASSWORD')
    if not ACCOUNT_NUMBER:
        missing_vars.append('ACCOUNT_NUMBER')
    
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Call validation (will raise exception if config is invalid)
validate_config()
