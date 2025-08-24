"""Main Flask application for the Mindframe backend"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
from src.services.product_report_service import ProductReportService
from src.services.google_drive_service import GoogleDriveService

# Import route blueprints
from src.api.routes import (
    health_bp,
    pdf_bp,
    auth_bp,
    template_bp,
    report_bp,
    interpretation_bp,
    admin_bp,
    job_bp
)

# Import route initialization functions
from src.api.routes.auth_routes import init_auth_routes
from src.api.routes.template_routes import init_template_routes
from src.api.routes.report_routes import init_report_routes
from src.api.routes.interpretation_routes import init_interpretation_routes
from src.api.routes.admin_routes import init_admin_routes

# Import utilities
from src.utils.config_utils import ConfigUtils
from src.utils.logging_utils import LoggingUtils
from src.utils.security_middleware import setup_security_middleware
from src.utils.error_handler import setup_error_handling
from src.utils.rate_limiter import setup_rate_limiting


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
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Enable CORS
    cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    CORS(app, origins=cors_origins, supports_credentials=True)
    
    # Setup security middleware
    setup_security_middleware(app)
    
    # Setup rate limiting
    rate_limiter, rate_limit_decorators = setup_rate_limiting(app)
    
    # Initialize services
    services = initialize_services(app)
    
    # Register blueprints
    register_blueprints(app, services)
    
    # Setup centralized error handling
    setup_error_handling(app)
    
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
        'MONGODB_URI': os.getenv('MONGODB_URI'),
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
        'JWT_TOKEN_LOCATION': ['headers'],
        'PASSWORD_SALT_ROUNDS': int(os.getenv('PASSWORD_SALT_ROUNDS', 12)),
        
        # Security middleware configuration
        'SECURITY_CSP_ENABLED': os.getenv('SECURITY_CSP_ENABLED', 'true').lower() == 'true',
        'SECURITY_HSTS_ENABLED': os.getenv('SECURITY_HSTS_ENABLED', 'true').lower() == 'true',
        'SECURITY_HSTS_MAX_AGE': int(os.getenv('SECURITY_HSTS_MAX_AGE', 31536000)),
        'SECURITY_X_FRAME_OPTIONS': os.getenv('SECURITY_X_FRAME_OPTIONS', 'DENY'),
        'SECURITY_X_CONTENT_TYPE_OPTIONS': os.getenv('SECURITY_X_CONTENT_TYPE_OPTIONS', 'nosniff'),
        'SECURITY_REFERRER_POLICY': os.getenv('SECURITY_REFERRER_POLICY', 'strict-origin-when-cross-origin'),
        'SECURITY_FORCE_HTTPS': os.getenv('SECURITY_FORCE_HTTPS', 'false').lower() == 'true',
        'SECURITY_ALLOWED_HOSTS': os.getenv('SECURITY_ALLOWED_HOSTS', '').split(',') if os.getenv('SECURITY_ALLOWED_HOSTS') else [],
        
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
        
        # Google Drive configuration
        'GOOGLE_CREDENTIALS_FILE': os.getenv('GOOGLE_CREDENTIALS_FILE'),
        'GOOGLE_DRIVE_FOLDER_ID': os.getenv('GOOGLE_DRIVE_FOLDER_ID'),
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
    from src.utils.logging_utils import LogConfig, LoggingUtils
    
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = os.getenv('LOG_FORMAT', 'structured')
    log_file = os.getenv('LOG_FILE', 'dev/logs/mindframe.log')
    json_output = os.getenv('LOG_JSON', 'false').lower() == 'true'
    
    config = LogConfig(
        level=log_level,
        format_type=log_format,
        log_file=log_file,
        max_file_size_mb=int(os.getenv('LOG_MAX_SIZE_MB', '50')),
        backup_count=int(os.getenv('LOG_BACKUP_COUNT', '10')),
        console_output=True,
        json_output=json_output,
        include_caller_info=True,
        include_process_info=True,
        include_thread_info=False
    )
    LoggingUtils.setup_logging(config)
    
    # Setup request logging
    LoggingUtils.setup_request_logging(app)
    
    # Set Flask app logger
    app.logger = LoggingUtils.get_logger('mindframe.app')
    
    # Log application startup
    app.logger.info("Logging system initialized", extra={
        'log_level': log_level,
        'log_format': log_format,
        'log_file': log_file,
        'json_output': json_output
    })


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
            local_storage_path = app.config.get('STORAGE_PATH', './storage')
            gcs_credentials_path = app.config.get('GOOGLE_CREDENTIALS_FILE')
            gcs_bucket_name = app.config.get('GOOGLE_DRIVE_FOLDER_ID')
            
            if not services['storage'].initialize(
                local_storage_path=local_storage_path,
                gcs_credentials_path=gcs_credentials_path,
                gcs_bucket_name=gcs_bucket_name
            ):
                app.logger.warning("Failed to initialize storage service - running without storage")
                services['storage'] = None
        except Exception as e:
            app.logger.warning(f"Storage service initialization failed: {e} - running without storage")
            services['storage'] = None
        
        # Initialize email service
        services['email'] = EmailService()
        try:
            from src.services.email_service import EmailConfig
            email_config = EmailConfig(
                smtp_server=app.config.get('SMTP_SERVER', 'localhost'),
                smtp_port=app.config.get('SMTP_PORT', 587),
                username=app.config.get('SMTP_USERNAME'),
                password=app.config.get('SMTP_PASSWORD'),
                use_tls=app.config.get('SMTP_USE_TLS', True),
                from_email=app.config.get('EMAIL_FROM', 'noreply@mindframe.com')
            )
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
            if not services['pdf'].initialize(
                db_service=services['database'],
                storage_service=None,  # No longer using local storage
                email_service=services['email'],
                google_drive_service=services.get('google_drive'),
                max_workers=4
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
        
        # Initialize Google Drive service
        try:
            credentials_file = app.config.get('GOOGLE_CREDENTIALS_FILE')
            folder_id = app.config.get('GOOGLE_DRIVE_FOLDER_ID')
            
            if credentials_file and os.path.exists(credentials_file):
                services['google_drive'] = GoogleDriveService(
                    credentials_path=credentials_file,
                    folder_id=folder_id
                )
                app.logger.info("Google Drive service initialized successfully")
            else:
                app.logger.warning(f"Google Drive credentials file not found: {credentials_file} - running without Google Drive")
                services['google_drive'] = None
        except Exception as e:
            app.logger.warning(f"Google Drive service initialization failed: {e} - running without Google Drive")
            services['google_drive'] = None
        
        # Initialize product report service
        services['product_report'] = ProductReportService()
        try:
            if not services['product_report'].initialize(
                services['database'],
                services['pdf'],
                services.get('google_drive')  # Optional Google Drive service
            ):
                app.logger.warning("Product report service initialization failed - running without product reports")
                services['product_report'] = None
        except Exception as e:
            app.logger.warning(f"Product report service initialization failed: {e} - running without product reports")
            services['product_report'] = None
        
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
        init_report_routes(services['auth'], services['report'], services.get('product_report'))
    if services.get('auth'):
        init_interpretation_routes(services['auth'], services.get('database'))
    if services.get('auth'):
        init_admin_routes(services['auth'], services.get('database'))
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(pdf_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(template_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(interpretation_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(job_bp, url_prefix='/api/v1/jobs')
    
    app.logger.info("All blueprints registered successfully")


# Error handling is now managed by the centralized error handler
# See src/utils/error_handler.py for implementation details


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
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    app.logger.info(f"Starting Mindframe application on port {port}")
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )