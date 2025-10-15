"""
METIS Lab Portal - Main Application Entry Point
Run this file to start the Flask application
"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Get configuration from environment variables for deployment
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(
        host='0.0.0.0',  # Allow external connections
        port=port,
        debug=debug
    )