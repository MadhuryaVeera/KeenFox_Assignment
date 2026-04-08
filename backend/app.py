"""Main Flask Application"""
from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import logging

from models.database import db
from app.routes import bp as api_bp
from utils.logger_config import setup_logger

# Load environment variables
from pathlib import Path
backend_env_path = Path(__file__).parent / '.env'
root_env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=backend_env_path)
load_dotenv(dotenv_path=root_env_path)

# Setup logger
logger = setup_logger()


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 
        'sqlite:///keenfox.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False

    env_name = os.getenv('FLASK_ENV', 'development').lower()
    configured_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    configured_origins = [origin.strip() for origin in configured_origins if origin.strip()]

    # In development allow localhost loopback ports to avoid CORS failures while switching ports.
    if env_name == 'development':
        cors_origins = [
            r"http://localhost:[0-9]+",
            r"http://127\.0\.0\.1:[0-9]+"
        ]
    else:
        cors_origins = configured_origins
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins
        }
    })
    
    # Create tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables initialized")
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Root route
    @app.route('/')
    def root():
        return jsonify({
            'name': 'KeenFox Intelligence Engine',
            'version': '1.0.0',
            'status': 'active',
            'endpoints': {
                'health': '/api/health',
                'analyze': 'POST /api/analyze',
                'brands': 'GET /api/brands',
                'reports': 'GET /api/reports',
                'stats': 'GET /api/stats'
            }
        }), 200
    
    # Error handlers
    @app.errorhandler(Exception)
    def handle_error(error):
        logger.error(f"Unhandled error: {error}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': str(error),
            'status': 'error'
        }), 500
    
    logger.info("Flask app created successfully")
    return app


if __name__ == '__main__':
    app = create_app()
    logger.info("Starting KeenFox Intelligence Engine...")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.getenv('FLASK_ENV') == 'development'
    )
