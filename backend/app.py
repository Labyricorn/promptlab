"""
PromptLab Backend Application
Main Flask application with CORS configuration
"""

from flask import Flask, send_from_directory
from flask_cors import CORS
import os

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure CORS for local development
    CORS(app, origins=["http://localhost:5000", "http://127.0.0.1:5000"])
    
    # Basic health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'service': 'PromptLab Backend'}
    
    # Serve frontend files
    @app.route('/')
    def serve_frontend():
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
        return send_from_directory(frontend_dir, 'index.html')
    
    @app.route('/<path:filename>')
    def serve_static(filename):
        frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')
        return send_from_directory(frontend_dir, filename)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=5000)