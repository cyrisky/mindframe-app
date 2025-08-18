"""Flask application factory"""

import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

from .routes.pdf_routes import pdf_bp
from .routes.health_routes import health_bp
from ..services.database_service import DatabaseService
from ..services.redis_service import RedisService
from ..utils.logging_utils import LoggingUtils, LogConfig


def setup_logging(app: Flask) -> None:
    """Setup application logging
    
    Args:
        app: Flask application
    """
    config = LogConfig(
        level=app.config.get('LOG_LEVEL', 'INFO'),
        format_type='detailed',
        console_output=True,
        include_caller_info=True
    )
    LoggingUtils.setup_logging(config)


def create_app(config_name: str = None) -> Flask:
    """Create and configure Flask application
    
    Args:
        config_name: Configuration name (development, production, testing)
        
    Returns:
        Configured Flask application
    """
    # Load environment variables
    load_dotenv()
    
    # Create Flask app
    app = Flask(__name__)
    
    # Configure app
    configure_app(app, config_name)
    
    # Setup CORS
    CORS(app, origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:3000",  # Vite dev server
        "https://mindframe-app.com"  # Production domain
    ])
    
    # Setup logging
    setup_logging(app)
    
    # Initialize services
    initialize_services(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app


def configure_app(app: Flask, config_name: str = None) -> None:
    """Configure Flask application
    
    Args:
        app: Flask application
        config_name: Configuration name
    """
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    
    # Base configuration
    app.config.update({
        'SECRET_KEY': os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
        'DEBUG': config_name == 'development',
        'TESTING': config_name == 'testing',
        
        # Database configuration
        'MONGODB_URI': os.getenv('MONGODB_URI', 'mongodb://localhost:27017/mindframe'),
        'MONGODB_DB_NAME': os.getenv('MONGODB_DB_NAME', 'mindframe'),
        
        # Redis configuration
        'REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        
        # Google Drive configuration
        'GOOGLE_DRIVE_CREDENTIALS_PATH': os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH'),
        'GOOGLE_DRIVE_FOLDER_ID': os.getenv('GOOGLE_DRIVE_FOLDER_ID'),
        
        # PDF generation configuration
        'PDF_TEMPLATE_DIR': os.getenv('PDF_TEMPLATE_DIR', 'shared/templates'),
        'PDF_OUTPUT_DIR': os.getenv('PDF_OUTPUT_DIR', 'tmp/pdfs'),
        'MAX_PDF_SIZE_MB': int(os.getenv('MAX_PDF_SIZE_MB', '50')),
        
        # File upload configuration
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max file size
        'UPLOAD_FOLDER': os.getenv('UPLOAD_FOLDER', 'tmp/uploads'),
        
        # Celery configuration
        'CELERY_BROKER_URL': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
        'CELERY_RESULT_BACKEND': os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
        
        # Security configuration
        'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY', app.config['SECRET_KEY']),
        'JWT_ACCESS_TOKEN_EXPIRES': int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600')),
        
        # API configuration
        'API_RATE_LIMIT': os.getenv('API_RATE_LIMIT', '100 per hour'),
        'API_VERSION': 'v1',
    })
    
    # Environment-specific configuration
    if config_name == 'development':
        app.config.update({
            'DEBUG': True,
            'TESTING': False,
        })
    elif config_name == 'testing':
        app.config.update({
            'DEBUG': False,
            'TESTING': True,
            'MONGODB_DB_NAME': 'mindframe_test',
            'REDIS_URL': 'redis://localhost:6379/15',  # Use different Redis DB for testing
        })
    elif config_name == 'production':
        app.config.update({
            'DEBUG': False,
            'TESTING': False,
        })
        
        # Ensure required production environment variables
        required_vars = [
            'SECRET_KEY',
            'MONGODB_URI',
            'REDIS_URL',
            'GOOGLE_DRIVE_CREDENTIALS_PATH'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")


def initialize_services(app: Flask) -> None:
    """Initialize application services
    
    Args:
        app: Flask application
    """
    # Initialize database service
    db_service = DatabaseService(
        uri=app.config['MONGODB_URI'],
        db_name=app.config['MONGODB_DB_NAME']
    )
    app.db = db_service
    
    # Initialize Redis service
    redis_service = RedisService(app.config['REDIS_URL'])
    app.redis = redis_service
    
    # Create necessary directories
    os.makedirs(app.config['PDF_OUTPUT_DIR'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints
    
    Args:
        app: Flask application
    """
    # Register API blueprints
    app.register_blueprint(health_bp, url_prefix='/api/v1')
    app.register_blueprint(pdf_bp, url_prefix='/api/v1')


def register_error_handlers(app: Flask) -> None:
    """Register error handlers
    
    Args:
        app: Flask application
    """
    from flask import jsonify
    from werkzeug.exceptions import HTTPException
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request was invalid',
            'status_code': 400
        }), 400
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {str(error)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({
            'error': error.name,
            'message': error.description,
            'status_code': error.code
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


if __name__ == '__main__':
    app = create_app()
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=app.config['DEBUG']
    )