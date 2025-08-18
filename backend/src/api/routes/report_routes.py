"""Report routes for the mindframe application"""

from flask import Blueprint, request, jsonify, current_app, send_file
from functools import wraps
import logging
from typing import Dict, Any, Optional
import io

from ...services.auth_service import AuthService
from ...utils.decorators import require_auth, require_roles
from ...services.report_service import ReportService
from ...utils.validation_utils import ValidationUtils
from ...utils.logging_utils import LoggingUtils

# Create blueprint
report_bp = Blueprint('report', __name__, url_prefix='/api/reports')
logger = LoggingUtils.get_logger(__name__)

# Initialize services
auth_service = None
report_service = None


def init_report_routes(auth_svc: AuthService, report_svc: ReportService) -> None:
    """Initialize report routes with services
    
    Args:
        auth_svc: Authentication service instance
        report_svc: Report service instance
    """
    global auth_service, report_service
    auth_service = auth_svc
    report_service = report_svc


def require_json(f):
    """Decorator to require JSON content type"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        return f(*args, **kwargs)
    return decorated_function


@report_bp.route('', methods=['GET'])
@require_auth
def list_reports() -> tuple:
    """List reports with optional filtering
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        
        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        status = request.args.get('status')
        patient_id = request.args.get('patient_id')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20
        
        # Build filters
        filters = {}
        if status:
            filters['status'] = status
        if patient_id:
            filters['patient_id'] = patient_id
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        
        # Get reports
        result = report_service.list_reports(
            user_id=str(user['_id']),
            page=page,
            limit=limit,
            filters=filters
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'reports': result['reports'],
                'pagination': result['pagination']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        logger.error(f"List reports error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('', methods=['POST'])
@require_auth
@require_json
def create_report() -> tuple:
    """Create a new report
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['patient_id', 'template_id', 'title']
        validation_errors = ValidationUtils.validate_required_fields(data, required_fields)
        
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        # Validate report title
        if not ValidationUtils.validate_string_length(data['title'], min_length=1, max_length=200):
            return jsonify({
                'success': False,
                'error': 'Report title must be between 1 and 200 characters'
            }), 400
        
        # Create report
        report_data = {
            'patient_id': data['patient_id'],
            'template_id': data['template_id'],
            'title': data['title'],
            'description': data.get('description', ''),
            'data': data.get('data', {}),
            'settings': data.get('settings', {}),
            'created_by': str(user['_id'])
        }
        
        result = report_service.create_report(report_data)
        
        if result['success']:
            logger.info(f"Report created: {data['title']} by {user['email']}")
            return jsonify({
                'success': True,
                'message': 'Report created successfully',
                'report_id': result['report_id']
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        logger.error(f"Create report error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/<report_id>', methods=['GET'])
@require_auth
def get_report(report_id: str) -> tuple:
    """Get a specific report
    
    Args:
        report_id: Report ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        
        # Get report
        result = report_service.get_report(report_id, str(user['_id']))
        
        if result['success']:
            return jsonify({
                'success': True,
                'report': result['report']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404 if 'not found' in result['error'].lower() else 400
    
    except Exception as e:
        logger.error(f"Get report error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/<report_id>', methods=['PUT'])
@require_auth
@require_json
def update_report(report_id: str) -> tuple:
    """Update a report
    
    Args:
        report_id: Report ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        data = request.get_json()
        
        # Validate updatable fields
        allowed_fields = ['title', 'description', 'data', 'settings']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return jsonify({
                'success': False,
                'error': 'No valid fields to update'
            }), 400
        
        # Validate report title if provided
        if 'title' in update_data and not ValidationUtils.validate_string_length(update_data['title'], min_length=1, max_length=200):
            return jsonify({
                'success': False,
                'error': 'Report title must be between 1 and 200 characters'
            }), 400
        
        # Update report
        result = report_service.update_report(report_id, update_data, str(user['_id']))
        
        if result['success']:
            logger.info(f"Report updated: {report_id} by {user['email']}")
            return jsonify({
                'success': True,
                'message': 'Report updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404 if 'not found' in result['error'].lower() else 400
    
    except Exception as e:
        logger.error(f"Update report error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/<report_id>', methods=['DELETE'])
@require_auth
def delete_report(report_id: str) -> tuple:
    """Delete a report
    
    Args:
        report_id: Report ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        
        # Delete report
        result = report_service.delete_report(report_id, str(user['_id']))
        
        if result['success']:
            logger.info(f"Report deleted: {report_id} by {user['email']}")
            return jsonify({
                'success': True,
                'message': 'Report deleted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404 if 'not found' in result['error'].lower() else 400
    
    except Exception as e:
        logger.error(f"Delete report error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/<report_id>/pdf', methods=['GET'])
@require_auth
def generate_report_pdf(report_id: str) -> tuple:
    """Generate PDF for a report
    
    Args:
        report_id: Report ID
        
    Returns:
        tuple: PDF file response or JSON error
    """
    try:
        user = request.current_user
        
        # Generate PDF
        result = report_service.generate_report_pdf(report_id, str(user['_id']))
        
        if result['success']:
            # Return PDF file
            pdf_buffer = io.BytesIO(result['pdf_data'])
            pdf_buffer.seek(0)
            
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f"report_{report_id}.pdf"
            )
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404 if 'not found' in result['error'].lower() else 400
    
    except Exception as e:
        logger.error(f"Generate report PDF error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/<report_id>/status', methods=['PUT'])
@require_auth
@require_json
def update_report_status(report_id: str) -> tuple:
    """Update report status
    
    Args:
        report_id: Report ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        data = request.get_json()
        
        # Validate required fields
        if 'status' not in data:
            return jsonify({
                'success': False,
                'error': 'Status is required'
            }), 400
        
        # Validate status value
        valid_statuses = ['draft', 'in_review', 'approved', 'published', 'archived']
        if data['status'] not in valid_statuses:
            return jsonify({
                'success': False,
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400
        
        # Update report status
        result = report_service.update_report_status(
            report_id,
            data['status'],
            str(user['_id']),
            data.get('notes', '')
        )
        
        if result['success']:
            logger.info(f"Report status updated: {report_id} -> {data['status']} by {user['email']}")
            return jsonify({
                'success': True,
                'message': 'Report status updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404 if 'not found' in result['error'].lower() else 400
    
    except Exception as e:
        logger.error(f"Update report status error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/<report_id>/test-results', methods=['POST'])
@require_auth
@require_json
def add_test_result(report_id: str) -> tuple:
    """Add test result to a report
    
    Args:
        report_id: Report ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['test_name', 'test_type', 'results']
        validation_errors = ValidationUtils.validate_required_fields(data, required_fields)
        
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        # Add test result
        test_result = {
            'test_name': data['test_name'],
            'test_type': data['test_type'],
            'results': data['results'],
            'notes': data.get('notes', ''),
            'administered_by': str(user['_id']),
            'administered_date': data.get('administered_date')
        }
        
        result = report_service.add_test_result(report_id, test_result, str(user['_id']))
        
        if result['success']:
            logger.info(f"Test result added to report: {report_id} by {user['email']}")
            return jsonify({
                'success': True,
                'message': 'Test result added successfully'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404 if 'not found' in result['error'].lower() else 400
    
    except Exception as e:
        logger.error(f"Add test result error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/<report_id>/viewers', methods=['POST'])
@require_auth
@require_json
def add_authorized_viewer(report_id: str) -> tuple:
    """Add authorized viewer to a report
    
    Args:
        report_id: Report ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        data = request.get_json()
        
        # Validate required fields
        if 'user_id' not in data:
            return jsonify({
                'success': False,
                'error': 'User ID is required'
            }), 400
        
        # Add authorized viewer
        result = report_service.add_authorized_viewer(
            report_id,
            data['user_id'],
            str(user['_id']),
            data.get('permissions', ['view'])
        )
        
        if result['success']:
            logger.info(f"Authorized viewer added to report: {report_id} by {user['email']}")
            return jsonify({
                'success': True,
                'message': 'Authorized viewer added successfully'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404 if 'not found' in result['error'].lower() else 400
    
    except Exception as e:
        logger.error(f"Add authorized viewer error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/<report_id>/viewers/<viewer_id>', methods=['DELETE'])
@require_auth
def remove_authorized_viewer(report_id: str, viewer_id: str) -> tuple:
    """Remove authorized viewer from a report
    
    Args:
        report_id: Report ID
        viewer_id: Viewer user ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        
        # Remove authorized viewer
        result = report_service.remove_authorized_viewer(report_id, viewer_id, str(user['_id']))
        
        if result['success']:
            logger.info(f"Authorized viewer removed from report: {report_id} by {user['email']}")
            return jsonify({
                'success': True,
                'message': 'Authorized viewer removed successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404 if 'not found' in result['error'].lower() else 400
    
    except Exception as e:
        logger.error(f"Remove authorized viewer error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/stats', methods=['GET'])
@require_auth
@require_roles(['admin', 'manager'])
def get_report_stats() -> tuple:
    """Get report statistics
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        
        # Get date range from query parameters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Get report statistics
        result = report_service.get_report_stats(date_from, date_to)
        
        if result['success']:
            return jsonify({
                'success': True,
                'stats': result['stats']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        logger.error(f"Get report stats error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/<report_id>/duplicate', methods=['POST'])
@require_auth
@require_json
def duplicate_report(report_id: str) -> tuple:
    """Duplicate a report
    
    Args:
        report_id: Report ID to duplicate
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        data = request.get_json()
        
        # Get new report title
        new_title = data.get('title')
        if not new_title:
            return jsonify({
                'success': False,
                'error': 'New report title is required'
            }), 400
        
        # Validate report title
        if not ValidationUtils.validate_string_length(new_title, min_length=1, max_length=200):
            return jsonify({
                'success': False,
                'error': 'Report title must be between 1 and 200 characters'
            }), 400
        
        # Get original report
        report_result = report_service.get_report(report_id, str(user['_id']))
        
        if not report_result['success']:
            return jsonify({
                'success': False,
                'error': report_result['error']
            }), 404 if 'not found' in report_result['error'].lower() else 400
        
        # Create duplicate report
        original_report = report_result['report']
        duplicate_data = {
            'patient_id': original_report['patient_id'],
            'template_id': original_report['template_id'],
            'title': new_title,
            'description': f"Copy of {original_report['title']}",
            'data': original_report.get('data', {}),
            'settings': original_report.get('settings', {}),
            'created_by': str(user['_id'])
        }
        
        result = report_service.create_report(duplicate_data)
        
        if result['success']:
            logger.info(f"Report duplicated: {report_id} -> {result['report_id']} by {user['email']}")
            return jsonify({
                'success': True,
                'message': 'Report duplicated successfully',
                'report_id': result['report_id']
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        logger.error(f"Duplicate report error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/batch/generate', methods=['POST'])
@require_auth
@require_json
def batch_generate_reports() -> tuple:
    """Generate multiple reports in batch
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        data = request.get_json()
        
        # Validate required fields
        if 'reports' not in data or not isinstance(data['reports'], list):
            return jsonify({
                'success': False,
                'error': 'Reports list is required'
            }), 400
        
        if len(data['reports']) > 50:  # Limit batch size
            return jsonify({
                'success': False,
                'error': 'Batch size cannot exceed 50 reports'
            }), 400
        
        # Validate each report data
        for i, report_data in enumerate(data['reports']):
            required_fields = ['patient_id', 'template_id', 'title']
            validation_errors = ValidationUtils.validate_required_fields(report_data, required_fields)
            
            if validation_errors:
                return jsonify({
                    'success': False,
                    'error': f'Validation failed for report {i + 1}',
                    'details': validation_errors
                }), 400
        
        # Process batch generation
        results = []
        for report_data in data['reports']:
            report_data['created_by'] = str(user['_id'])
            result = report_service.create_report(report_data)
            results.append({
                'title': report_data['title'],
                'success': result['success'],
                'report_id': result.get('report_id'),
                'error': result.get('error')
            })
        
        # Count successes and failures
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        logger.info(f"Batch report generation: {successful} successful, {failed} failed by {user['email']}")
        
        return jsonify({
            'success': True,
            'message': f'Batch generation completed: {successful} successful, {failed} failed',
            'results': results,
            'summary': {
                'total': len(results),
                'successful': successful,
                'failed': failed
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Batch generate reports error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500