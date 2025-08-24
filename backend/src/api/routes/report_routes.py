"""Report routes for the mindframe application"""

from flask import Blueprint, request, jsonify, current_app, send_file, g
from functools import wraps
import logging
from typing import Dict, Any, Optional
import io
from pydantic import ValidationError

from ...services.auth_service import AuthService
from ...utils.decorators import require_auth, require_roles
from ...services.report_service import ReportService
from ...services.product_report_service import ProductReportService
from ...utils.input_validation import validate_json, ValidationError as InputValidationError
from ...models.request_models import ReportCreateRequest, ReportUpdateRequest, ReportStatusUpdateRequest, TestResultRequest, AuthorizedViewerRequest, ReportDuplicateRequest, BatchGenerateReportsRequest
from ...utils.logging_utils import LoggingUtils
from ...utils.error_handler import raise_validation_error, raise_authentication_error, raise_not_found

# Create blueprint
report_bp = Blueprint('report', __name__, url_prefix='/api/reports')
logger = LoggingUtils.get_logger(__name__)

# Initialize services
auth_service = None
report_service = None
product_report_service = None


def init_report_routes(auth_svc: AuthService, report_svc: ReportService, product_report_svc: ProductReportService = None) -> None:
    """Initialize report routes with services
    
    Args:
        auth_svc: Authentication service instance
        report_svc: Report service instance
        product_report_svc: Product report service instance
    """
    global auth_service, report_service, product_report_service
    auth_service = auth_svc
    report_service = report_svc
    product_report_service = product_report_svc


# Note: require_json decorator has been replaced with @validate_json
# All endpoints now use the new validation framework


@report_bp.route('', methods=['GET'])
@require_auth()
def list_reports() -> tuple:
    """List reports with optional filtering
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        
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
            }), 500
    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/recent', methods=['GET'])
@require_auth()
def get_recent_reports() -> tuple:
    """Get recent reports for the authenticated user
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        
        # Get query parameters
        limit = int(request.args.get('limit', 5))
        
        # Validate limit parameter
        if limit < 1 or limit > 50:
            limit = 5
        
        # Get recent reports
        result = report_service.list_reports(
            user_id=str(user['_id']),
            page=1,
            limit=limit,
            filters={'sort_by': 'created_at', 'sort_order': 'desc'}
        )
        
        if result['success']:
            return jsonify(result['reports']), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500
    except Exception as e:
        logger.error(f"Error getting recent reports: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('', methods=['POST'])
@require_auth()
@validate_json()
@validate_json(pydantic_model=ReportCreateRequest)
def create_report() -> tuple:
    """Create a new report
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        
        # Access validated data
        title = request.validated_data['title']
        description = request.validated_data['description']
        template_id = request.validated_data['template_id']
        data = request.validated_data['data']
        tags = request.validated_data['tags']
        is_public = request.validated_data['is_public']
        
        # Create report
        report_data = {
            'template_id': template_id,
            'title': title,
            'description': description,
            'data': data,
            'tags': tags,
            'is_public': is_public,
            'created_by': str(user['_id'])
        }
        
        result = report_service.create_report(report_data)
        
        if result['success']:
            logger.info(f"Report created: {title} by {user['email']}")
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
    
    except ValidationError as e:
        logger.warning(f"Validation error in create report: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': e.errors()
        }), 400
    
    except InputValidationError as e:
        logger.warning(f"Input validation error in create report: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Create report error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/<report_id>', methods=['GET'])
@require_auth()
def get_report(report_id: str) -> tuple:
    """Get a specific report
    
    Args:
        report_id: Report ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        
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
@require_auth()
@validate_json(pydantic_model=ReportUpdateRequest)
def update_report(report_id: str) -> tuple:
    """Update a report
    
    Args:
        report_id: Report ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        
        # Access validated data and build update dictionary
        update_data = {}
        
        if request.validated_data.get('title') is not None:
            update_data['title'] = request.validated_data['title']
        if request.validated_data.get('description') is not None:
            update_data['description'] = request.validated_data['description']
        if request.validated_data.get('data') is not None:
            update_data['data'] = request.validated_data['data']
        if request.validated_data.get('tags') is not None:
            update_data['tags'] = request.validated_data['tags']
        if request.validated_data.get('is_public') is not None:
            update_data['is_public'] = request.validated_data['is_public']
        
        if not update_data:
            return jsonify({
                'success': False,
                'error': 'No valid fields to update'
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
    
    except ValidationError as e:
        logger.warning(f"Validation error in update report: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': e.errors()
        }), 400
    
    except InputValidationError as e:
        logger.warning(f"Input validation error in update report: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Update report error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/<report_id>', methods=['DELETE'])
@require_auth()
def delete_report(report_id: str) -> tuple:
    """Delete a report
    
    Args:
        report_id: Report ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        
        # Get report
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
@require_auth()
def generate_report_pdf(report_id: str) -> tuple:
    """Generate PDF for a report
    
    Args:
        report_id: Report ID
        
    Returns:
        tuple: PDF file response or JSON error
    """
    try:
        user = g.current_user
        
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
@require_auth()
@validate_json()
@validate_json(pydantic_model=ReportStatusUpdateRequest)
def update_report_status(report_id: str) -> tuple:
    """Update report status
    
    Args:
        report_id: Report ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        data = request.validated_data
        
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
    
    except ValidationError as e:
        logger.warning(f"Validation error in update report status: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': e.errors()
        }), 400
    
    except InputValidationError as e:
        logger.warning(f"Input validation error in update report status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Update report status error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/<report_id>/test-results', methods=['POST'])
@require_auth()
@validate_json()
@validate_json(pydantic_model=TestResultRequest)
def add_test_result(report_id: str) -> tuple:
    """Add test result to a report
    
    Args:
        report_id: Report ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        data = request.validated_data
        
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
    
    except ValidationError as e:
        logger.warning(f"Validation error in add test result: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': e.errors()
        }), 400
    
    except InputValidationError as e:
        logger.warning(f"Input validation error in add test result: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Add test result error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/<report_id>/viewers', methods=['POST'])
@require_auth()
@validate_json()
@validate_json(pydantic_model=AuthorizedViewerRequest)
def add_authorized_viewer(report_id: str) -> tuple:
    """Add authorized viewer to a report
    
    Args:
        report_id: Report ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        data = request.validated_data
        
        # Add authorized viewer
        result = report_service.add_authorized_viewer(
            report_id,
            data.user_id,
            str(user['_id']),
            data.permissions
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
    
    except ValidationError as e:
        logger.warning(f"Validation error in add authorized viewer: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': e.errors()
        }), 400
    
    except InputValidationError as e:
        logger.warning(f"Input validation error in add authorized viewer: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Add authorized viewer error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/<report_id>/viewers/<viewer_id>', methods=['DELETE'])
@require_auth()
def remove_authorized_viewer(report_id: str, viewer_id: str) -> tuple:
    """Remove authorized viewer from a report
    
    Args:
        report_id: Report ID
        viewer_id: Viewer user ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        
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
@require_auth()
@require_roles(['admin', 'manager'])
def get_report_stats() -> tuple:
    """Get report statistics
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        
        # Get the reportdate range from query parameters
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
@require_auth()
@validate_json()
@validate_json(pydantic_model=ReportDuplicateRequest)
def duplicate_report(report_id: str) -> tuple:
    """Duplicate a report
    
    Args:
        report_id: Report ID to duplicate
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        data = request.validated_data
        
        # Get new report title from validated data
        new_title = data.title
        
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
    
    except ValidationError as e:
        logger.warning(f"Validation error in duplicate report: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': str(e)
        }), 400
    
    except InputValidationError as e:
        logger.warning(f"Input validation error in duplicate report: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Duplicate report error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/batch/generate', methods=['POST'])
@require_auth()
@validate_json()
@validate_json(pydantic_model=BatchGenerateReportsRequest)
def batch_generate_reports() -> tuple:
    """Generate multiple reports in batch
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        data = request.validated_data
        
        # Get validated reports list
        reports_data = data.reports
        
        # Process batch generation
        results = []
        for report_item in reports_data:
            # Convert Pydantic model to dict and add user info
            report_dict = report_item.dict()
            report_dict['created_by'] = str(user['_id'])
            
            result = report_service.create_report(report_dict)
            results.append({
                'title': report_item.title,
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
    
    except ValidationError as e:
        logger.warning(f"Validation error in batch generate reports: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': str(e)
        }), 400
    
    except InputValidationError as e:
        logger.warning(f"Input validation error in batch generate reports: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    
    except Exception as e:
        logger.error(f"Batch generate reports error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@report_bp.route('/generate-product-report', methods=['POST'])
def generate_product_report() -> tuple:
    """Generate combined PDF report for a product
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body is required'
            }), 400
        
        # Validate required parameters
        code = data.get('code')
        product_id = data.get('productId')
        
        if not code:
            return jsonify({
                'success': False,
                'error': 'Parameter "code" is required'
            }), 400
        
        if not product_id:
            return jsonify({
                'success': False,
                'error': 'Parameter "productId" is required'
            }), 400
        
        # Check if product report service is available
        if not product_report_service:
            return jsonify({
                'success': False,
                'error': 'Product report service not available'
            }), 503
        
        logger.info(f"Generating product report for code: {code}, productId: {product_id}")
        
        # Generate the product report
        result = product_report_service.generate_product_report(code, product_id)
        
        if result['success']:
            response_data = {
                'success': True,
                'message': 'Product report generated successfully',
                'filename': result['filename']
            }
            
            # Add Google Drive info if available
            if 'google_drive' in result:
                response_data['google_drive'] = result['google_drive']
            
            return jsonify(response_data), 200
        else:
            # Determine appropriate HTTP status code based on error type
            status_code = 500  # Default to internal server error
            if result.get('error_type') == 'product_not_found':
                status_code = 404
            elif result.get('error_type') == 'test_data_not_found':
                status_code = 404
            elif result.get('error_type') == 'missing_required_tests':
                status_code = 400
            elif result.get('error_type') == 'service_not_initialized':
                status_code = 503
            elif result.get('error_type') == 'service_unavailable':
                status_code = 503
            
            return jsonify({
                'success': False,
                'error': result['error'],
                'error_type': result.get('error_type', 'unknown')
            }), status_code
            
    except Exception as e:
        logger.error(f"Error in generate_product_report endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500