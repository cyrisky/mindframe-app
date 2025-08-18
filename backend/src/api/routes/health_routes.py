"""Health check routes"""

import os
from datetime import datetime
from flask import Blueprint, jsonify, current_app
from ...services.database_service import DatabaseService
from ...services.redis_service import RedisService


health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint
    
    Returns:
        JSON response with health status
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'mindframe-api',
        'version': '1.0.0'
    })


@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check with service dependencies
    
    Returns:
        JSON response with detailed health status
    """
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'mindframe-api',
        'version': '1.0.0',
        'checks': {}
    }
    
    overall_healthy = True
    
    # Check database connection
    try:
        db_service = current_app.db
        db_status = db_service.health_check()
        health_status['checks']['database'] = {
            'status': 'healthy' if db_status else 'unhealthy',
            'message': 'MongoDB connection successful' if db_status else 'MongoDB connection failed'
        }
        if not db_status:
            overall_healthy = False
    except Exception as e:
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database check failed: {str(e)}'
        }
        overall_healthy = False
    
    # Check Redis connection
    try:
        redis_service = current_app.redis
        redis_status = redis_service.health_check()
        health_status['checks']['redis'] = {
            'status': 'healthy' if redis_status else 'unhealthy',
            'message': 'Redis connection successful' if redis_status else 'Redis connection failed'
        }
        if not redis_status:
            overall_healthy = False
    except Exception as e:
        health_status['checks']['redis'] = {
            'status': 'unhealthy',
            'message': f'Redis check failed: {str(e)}'
        }
        overall_healthy = False
    
    # Check file system access
    try:
        pdf_output_dir = current_app.config['PDF_OUTPUT_DIR']
        upload_folder = current_app.config['UPLOAD_FOLDER']
        
        # Check if directories exist and are writable
        pdf_dir_ok = os.path.exists(pdf_output_dir) and os.access(pdf_output_dir, os.W_OK)
        upload_dir_ok = os.path.exists(upload_folder) and os.access(upload_folder, os.W_OK)
        
        if pdf_dir_ok and upload_dir_ok:
            health_status['checks']['filesystem'] = {
                'status': 'healthy',
                'message': 'File system access successful'
            }
        else:
            health_status['checks']['filesystem'] = {
                'status': 'unhealthy',
                'message': 'File system access issues detected'
            }
            overall_healthy = False
            
    except Exception as e:
        health_status['checks']['filesystem'] = {
            'status': 'unhealthy',
            'message': f'File system check failed: {str(e)}'
        }
        overall_healthy = False
    
    # Check WeasyPrint functionality
    try:
        from ...core.pdf_generator import PDFGenerator
        
        # Simple test to ensure WeasyPrint is working
        generator = PDFGenerator()
        test_html = "<html><body><h1>Test</h1></body></html>"
        pdf_bytes = generator.generate_from_html(test_html)
        
        if pdf_bytes and len(pdf_bytes) > 0:
            health_status['checks']['weasyprint'] = {
                'status': 'healthy',
                'message': 'WeasyPrint PDF generation successful'
            }
        else:
            health_status['checks']['weasyprint'] = {
                'status': 'unhealthy',
                'message': 'WeasyPrint PDF generation failed'
            }
            overall_healthy = False
            
    except Exception as e:
        health_status['checks']['weasyprint'] = {
            'status': 'unhealthy',
            'message': f'WeasyPrint check failed: {str(e)}'
        }
        overall_healthy = False
    
    # Check Google Drive integration (if configured)
    google_creds_path = current_app.config.get('GOOGLE_DRIVE_CREDENTIALS_PATH')
    if google_creds_path:
        try:
            from ...services.google_drive_service import GoogleDriveService
            
            drive_service = GoogleDriveService(google_creds_path)
            drive_status = drive_service.health_check()
            
            health_status['checks']['google_drive'] = {
                'status': 'healthy' if drive_status else 'unhealthy',
                'message': 'Google Drive connection successful' if drive_status else 'Google Drive connection failed'
            }
            
            if not drive_status:
                overall_healthy = False
                
        except Exception as e:
            health_status['checks']['google_drive'] = {
                'status': 'unhealthy',
                'message': f'Google Drive check failed: {str(e)}'
            }
            overall_healthy = False
    else:
        health_status['checks']['google_drive'] = {
            'status': 'not_configured',
            'message': 'Google Drive integration not configured'
        }
    
    # Update overall status
    health_status['status'] = 'healthy' if overall_healthy else 'unhealthy'
    
    # Return appropriate HTTP status code
    status_code = 200 if overall_healthy else 503
    
    return jsonify(health_status), status_code


@health_bp.route('/health/ready', methods=['GET'])
def readiness_check():
    """Readiness check for Kubernetes/container orchestration
    
    Returns:
        JSON response indicating if service is ready to accept traffic
    """
    try:
        # Check critical dependencies
        db_service = current_app.db
        redis_service = current_app.redis
        
        db_ready = db_service.health_check()
        redis_ready = redis_service.health_check()
        
        ready = db_ready and redis_ready
        
        response = {
            'ready': ready,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'database': db_ready,
                'redis': redis_ready
            }
        }
        
        status_code = 200 if ready else 503
        return jsonify(response), status_code
        
    except Exception as e:
        return jsonify({
            'ready': False,
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503


@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """Liveness check for Kubernetes/container orchestration
    
    Returns:
        JSON response indicating if service is alive
    """
    return jsonify({
        'alive': True,
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'mindframe-api'
    })


@health_bp.route('/version', methods=['GET'])
def version_info():
    """Get version and build information
    
    Returns:
        JSON response with version details
    """
    return jsonify({
        'service': 'mindframe-api',
        'version': '1.0.0',
        'build_date': '2024-01-01',
        'git_commit': os.getenv('GIT_COMMIT', 'unknown'),
        'environment': current_app.config.get('ENV', 'development'),
        'python_version': os.sys.version,
        'dependencies': {
            'flask': '2.3.0',
            'weasyprint': '61.0',
            'pymongo': '4.0.0',
            'redis': '4.5.0'
        }
    })