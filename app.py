# /app.py
import os
import threading
import signal
import sys
from flask import Flask, jsonify

import config
from logger import get_logger
from dashboard import dashboard
from tastytrade_client import client

# Initialize logger
logger = get_logger(__name__)

# Lock for client initialization
client_init_lock = threading.Lock()
client_initialized = False

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {sig}, shutting down...")
    # Perform any cleanup needed
    if hasattr(client, 'authenticated') and client.authenticated:
        try:
            client.tasty.logout()
            logger.info("Successfully logged out of Tastytrade API")
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')
    
    # Configure the app
    app.secret_key = config.FLASK_SECRET_KEY
    app.config['DEBUG'] = config.DEBUG
    
    # Register blueprints
    app.register_blueprint(dashboard)
    
    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        logger.warning(f"404 error: {str(e)}")
        return jsonify({"error": "Not Found", "message": "The requested resource was not found"}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"500 error: {str(e)}")
        return jsonify({"error": "Server Error", "message": "An internal server error occurred"}), 500
    
    # Before request handler to ensure client is initialized - MODIFIED TO SKIP AUTHENTICATION
    @app.before_request
    def ensure_client():
        global client_initialized
        if not client_initialized:
            with client_init_lock:
                if not client_initialized:
                    logger.info("Initializing Tastytrade client in DEMO MODE")
                    try:
                        # Try to authenticate but don't require success
                        client.authenticate()
                    except Exception as e:
                        logger.error(f"Authentication failed: {str(e)}")
                    finally:
                        # Mark as initialized regardless of authentication result
                        client_initialized = True
                        logger.info("Client initialized in demo mode - some features may be limited")
    
    return app

# Create the app
app = create_app()

if __name__ == '__main__':
    # Run the app
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
