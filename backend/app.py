"""Main Flask application for the Mindframe backend"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import datetime

# Import services
from src.services import (
    DatabaseService,
    RedisService,
    StorageService,
    EmailService,
    AuthService,
    PDFService,
    TemplateService,
    ReportService
)

# Import route blueprints
from src.api.routes import (
    health_bp,
    pdf_bp,
    auth_bp,
    template_bp,
    report_bp
)

# Import route initialization functions
from src.api.routes.auth_routes import init_auth_routes
from src.api.routes.template_routes import init_template_routes
from src.api.routes.report_routes import init_report_routes

# Import utilities
from src.utils.config_utils import ConfigUtils
from src.utils.logging_utils import LoggingUtils


def create_app(config_name: str = None) -> Flask:
    """Create and configure Flask application
    
    Args:
        config_name: Configuration environment name
        
    Returns:
        Flask: Configured Flask application
    """
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    load_config(app, config_name)
    
    # Setup logging
    setup_logging(app)
    
    # Enable CORS
    CORS(app, origins=['*'], supports_credentials=True)
    
    # Initialize services
    services = initialize_services(app)
    
    # Register blueprints
    register_blueprints(app, services)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Add health check endpoint
    register_health_endpoints(app, services)
    
    app.logger.info(f"Mindframe application created successfully in {config_name} mode")
    return app


def load_config(app: Flask, config_name: str) -> None:
    """Load application configuration
    
    Args:
        app: Flask application
        config_name: Configuration environment name
    """
    # Default configuration
    app.config.update({
        'SECRET_KEY': os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
        'DEBUG': config_name == 'development',
        'TESTING': config_name == 'testing',
        
        # Database configuration
        'MONGODB_URI': os.getenv('MONGODB_URI', 'mongodb://localhost:27017/mindframe'),
        'MONGODB_DB': os.getenv('MONGODB_DB', 'mindframe'),
        
        # Redis configuration
        'REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
        
        # Storage configuration
        'STORAGE_TYPE': os.getenv('STORAGE_TYPE', 'local'),
        'STORAGE_PATH': os.getenv('STORAGE_PATH', './storage'),
        'AWS_S3_BUCKET': os.getenv('AWS_S3_BUCKET'),
        'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
        'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
        'AWS_REGION': os.getenv('AWS_REGION', 'us-east-1'),
        
        # Email configuration
        'SMTP_SERVER': os.getenv('SMTP_SERVER', 'localhost'),
        'SMTP_PORT': int(os.getenv('SMTP_PORT', 587)),
        'SMTP_USERNAME': os.getenv('SMTP_USERNAME'),
        'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD'),
        'SMTP_USE_TLS': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
        'EMAIL_FROM': os.getenv('EMAIL_FROM', 'noreply@mindframe.app'),
        
        # Security configuration
        'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY', app.config['SECRET_KEY']),
        'JWT_ACCESS_TOKEN_EXPIRES': int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)),
        'JWT_REFRESH_TOKEN_EXPIRES': int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 86400)),
        'PASSWORD_SALT_ROUNDS': int(os.getenv('PASSWORD_SALT_ROUNDS', 12)),
        
        # PDF configuration
        'PDF_TEMP_DIR': os.getenv('PDF_TEMP_DIR', './temp/pdf'),
        'PDF_MAX_SIZE': int(os.getenv('PDF_MAX_SIZE', 50 * 1024 * 1024)),  # 50MB
        
        # Template configuration
        'TEMPLATE_DIRS': os.getenv('TEMPLATE_DIRS', './templates').split(','),
        'TEMPLATE_CACHE_TTL': int(os.getenv('TEMPLATE_CACHE_TTL', 3600)),
        
        # CORS configuration
        'CORS_ORIGINS': os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(','),
        
        # Rate limiting
        'RATE_LIMIT_ENABLED': os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true',
        'RATE_LIMIT_DEFAULT': os.getenv('RATE_LIMIT_DEFAULT', '100 per hour'),
        
        # File upload limits
        'MAX_CONTENT_LENGTH': int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)),  # 16MB
    })
    
    # Environment-specific overrides
    if config_name == 'production':
        app.config.update({
            'DEBUG': False,
            'TESTING': False,
        })
    elif config_name == 'testing':
        app.config.update({
            'TESTING': True,
            'MONGODB_DB': 'mindframe_test',
            'REDIS_URL': 'redis://localhost:6379/1',
        })


def setup_logging(app: Flask) -> None:
    """Setup application logging
    
    Args:
        app: Flask application
    """
    from src.utils.logging_utils import LogConfig
    
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = os.getenv('LOG_FORMAT', 'detailed')
    log_file = os.getenv('LOG_FILE')
    
    config = LogConfig(
        level=log_level,
        format_type=log_format,
        log_file=log_file,
        console_output=True,
        include_caller_info=True
    )
    LoggingUtils.setup_logging(config)
    
    # Set Flask app logger
    app.logger = LoggingUtils.get_logger('mindframe.app')


def initialize_services(app: Flask) -> dict:
    """Initialize all application services
    
    Args:
        app: Flask application
        
    Returns:
        dict: Dictionary of initialized services
    """
    services = {}
    
    try:
        # Initialize database service
        services['database'] = DatabaseService()
        try:
            if not services['database'].initialize(
                connection_string=app.config['MONGODB_URI'],
                database_name=app.config['MONGODB_DB']
            ):
                app.logger.warning("Failed to initialize database service - running without database")
                services['database'] = None
        except Exception as e:
            app.logger.warning(f"Database connection failed: {e} - running without database")
            services['database'] = None
        
        # Initialize Redis service
        services['redis'] = RedisService()
        try:
            if not services['redis'].initialize(app.config['REDIS_URL']):
                app.logger.warning("Failed to initialize Redis service - running without Redis")
                services['redis'] = None
        except Exception as e:
            app.logger.warning(f"Redis connection failed: {e} - running without Redis")
            services['redis'] = None
        
        # Initialize storage service
        services['storage'] = StorageService()
        try:
            storage_config = {
                'type': app.config.get('STORAGE_TYPE', 'local'),
                'local_path': app.config.get('STORAGE_PATH', 'tmp/storage'),
                'aws_bucket': app.config.get('AWS_S3_BUCKET'),
                'aws_access_key': app.config.get('AWS_ACCESS_KEY_ID'),
                'aws_secret_key': app.config.get('AWS_SECRET_ACCESS_KEY'),
                'aws_region': app.config.get('AWS_REGION')
            }
            if not services['storage'].initialize(storage_config):
                app.logger.warning("Failed to initialize storage service - running without storage")
                services['storage'] = None
        except Exception as e:
            app.logger.warning(f"Storage service initialization failed: {e} - running without storage")
            services['storage'] = None
        
        # Initialize email service
        services['email'] = EmailService()
        try:
            email_config = {
                'smtp_server': app.config.get('SMTP_SERVER', 'localhost'),
                'smtp_port': app.config.get('SMTP_PORT', 587),
                'username': app.config.get('SMTP_USERNAME'),
                'password': app.config.get('SMTP_PASSWORD'),
                'use_tls': app.config.get('SMTP_USE_TLS', True),
                'from_email': app.config.get('EMAIL_FROM', 'noreply@mindframe.com')
            }
            if not services['email'].initialize(email_config):
                app.logger.warning("Email service initialization failed - running without email")
                services['email'] = None
        except Exception as e:
            app.logger.warning(f"Email service initialization failed: {e} - running without email")
            services['email'] = None
        
        # Initialize authentication service
        services['auth'] = AuthService()
        try:
            auth_config = {
                'jwt_secret': app.config.get('JWT_SECRET_KEY', app.config['SECRET_KEY']),
                'access_token_expires': app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600),
                'refresh_token_expires': app.config.get('JWT_REFRESH_TOKEN_EXPIRES', 86400),
                'password_salt_rounds': app.config.get('PASSWORD_SALT_ROUNDS', 12)
            }
            # Create AuthConfig object
            from src.services.auth_service import AuthConfig
            auth_config_obj = AuthConfig(
                jwt_secret_key=auth_config['jwt_secret'],
                access_token_expires=auth_config['access_token_expires'],
                refresh_token_expires=auth_config['refresh_token_expires']
            )
            
            if not services['auth'].initialize(
                auth_config_obj,
                services['redis'],
                services['database']
            ):
                app.logger.warning("Authentication service initialization failed - running without auth")
                services['auth'] = None
        except Exception as e:
            app.logger.warning(f"Authentication service initialization failed: {e} - running without auth")
            services['auth'] = None
        
        # Initialize PDF service
        services['pdf'] = PDFService()
        try:
            pdf_config = {
                'temp_dir': app.config.get('PDF_TEMP_DIR', 'tmp/pdfs'),
                'max_size': app.config.get('PDF_MAX_SIZE', 50 * 1024 * 1024)  # 50MB
            }
            if not services['pdf'].initialize(
                services['storage'],
                pdf_config
            ):
                app.logger.warning("PDF service initialization failed - running without PDF generation")
                services['pdf'] = None
        except Exception as e:
            app.logger.warning(f"PDF service initialization failed: {e} - running without PDF generation")
            services['pdf'] = None
        
        # Initialize template service
        services['template'] = TemplateService()
        try:
            if not services['template'].initialize(
                services['database'],
                services['storage'],
                app.config.get('TEMPLATE_DIRS', ['templates'])
            ):
                app.logger.warning("Template service initialization failed - running without templates")
                services['template'] = None
        except Exception as e:
            app.logger.warning(f"Template service initialization failed: {e} - running without templates")
            services['template'] = None
        
        # Initialize report service
        services['report'] = ReportService()
        try:
            if not services['report'].initialize(
                services['database'],
                services['pdf'],
                services['template'],
                services['storage']
            ):
                app.logger.warning("Report service initialization failed - running without reports")
                services['report'] = None
        except Exception as e:
            app.logger.warning(f"Report service initialization failed: {e} - running without reports")
            services['report'] = None
        
        app.logger.info("Service initialization completed")
        return services
        
    except Exception as e:
        app.logger.error(f"Service initialization failed: {e}")
        raise


def register_blueprints(app: Flask, services: dict) -> None:
    """Register Flask blueprints
    
    Args:
        app: Flask application
        services: Dictionary of initialized services
    """
    # Initialize route dependencies (only if services are available)
    if services.get('auth'):
        init_auth_routes(services['auth'])
    if services.get('auth') and services.get('template'):
        init_template_routes(services['auth'], services['template'])
    if services.get('auth') and services.get('report'):
        init_report_routes(services['auth'], services['report'])
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(pdf_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(template_bp)
    app.register_blueprint(report_bp)
    
    app.logger.info("All blueprints registered successfully")


def register_error_handlers(app: Flask) -> None:
    """Register error handlers
    
    Args:
        app: Flask application
    """
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 'Bad request',
            'message': str(error.description) if hasattr(error, 'description') else 'Invalid request'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'success': False,
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'success': False,
            'error': 'Forbidden',
            'message': 'Insufficient permissions'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Not found',
            'message': 'Resource not found'
        }), 404
    
    @app.errorhandler(413)
    def payload_too_large(error):
        return jsonify({
            'success': False,
            'error': 'Payload too large',
            'message': 'Request entity too large'
        }), 413
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'success': False,
            'error': 'Rate limit exceeded',
            'message': 'Too many requests'
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {error}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500


def register_health_endpoints(app: Flask, services: dict) -> None:
    """Register health check endpoints
    
    Args:
        app: Flask application
        services: Dictionary of initialized services
    """
    @app.route('/health')
    def health_check():
        """Basic health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        })
    
    @app.route('/health/detailed')
    def detailed_health_check():
        """Detailed health check with service status"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'services': {}
        }
        
        overall_healthy = True
        
        # Check each service
        for service_name, service in services.items():
            try:
                if hasattr(service, 'health_check'):
                    service_health = service.health_check()
                    health_status['services'][service_name] = service_health
                    if not service_health.get('healthy', False):
                        overall_healthy = False
                else:
                    health_status['services'][service_name] = {
                        'healthy': True,
                        'message': 'No health check available'
                    }
            except Exception as e:
                health_status['services'][service_name] = {
                    'healthy': False,
                    'error': str(e)
                }
                overall_healthy = False
        
        if not overall_healthy:
            health_status['status'] = 'unhealthy'
        
        status_code = 200 if overall_healthy else 503
        return jsonify(health_status), status_code


# Create application instance
app = create_app()

if __name__ == '__main__':
    # Development server
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    app.logger.info(f"Starting Mindframe application on port {port}")
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )