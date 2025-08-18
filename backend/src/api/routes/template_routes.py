"""Template routes for the mindframe application"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import logging
from typing import Dict, Any, Optional

from ...services.auth_service import AuthService
from ...utils.decorators import require_auth, require_roles
from ...services.template_service import TemplateService
from ...utils.validation_utils import ValidationUtils
from ...utils.logging_utils import LoggingUtils

# Create blueprint
template_bp = Blueprint('template', __name__, url_prefix='/api/templates')
logger = LoggingUtils.get_logger(__name__)

# Initialize services
auth_service = None
template_service = None


def init_template_routes(auth_svc: AuthService, template_svc: TemplateService) -> None:
    """Initialize template routes with services
    
    Args:
        auth_svc: Authentication service instance
        template_svc: Template service instance
    """
    global auth_service, template_service
    auth_service = auth_svc
    template_service = template_svc


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


@template_bp.route('', methods=['GET'])
@require_auth
def list_templates() -> tuple:
    """List templates with optional filtering
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        category = request.args.get('category')
        search = request.args.get('search')
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 20
        
        # Build filters
        filters = {}
        if category:
            filters['category'] = category
        if search:
            filters['search'] = search
        
        # Get templates
        result = template_service.list_templates(
            page=page,
            limit=limit,
            filters=filters
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'templates': result['templates'],
                'pagination': result['pagination']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        logger.error(f"List templates error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('', methods=['POST'])
@require_auth
@require_json
def create_template() -> tuple:
    """Create a new template
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'content', 'category']
        validation_errors = ValidationUtils.validate_required_fields(data, required_fields)
        
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        # Validate template name
        if not ValidationUtils.validate_string_length(data['name'], min_length=1, max_length=100):
            return jsonify({
                'success': False,
                'error': 'Template name must be between 1 and 100 characters'
            }), 400
        
        # Create template
        template_data = {
            'name': data['name'],
            'description': data.get('description', ''),
            'content': data['content'],
            'category': data['category'],
            'variables': data.get('variables', []),
            'tags': data.get('tags', []),
            'is_public': data.get('is_public', False),
            'created_by': str(user['_id'])
        }
        
        result = template_service.create_template(template_data)
        
        if result['success']:
            logger.info(f"Template created: {data['name']} by {user['email']}")
            return jsonify({
                'success': True,
                'message': 'Template created successfully',
                'template_id': result['template_id']
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        logger.error(f"Create template error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('/<template_id>', methods=['GET'])
@require_auth
def get_template(template_id: str) -> tuple:
    """Get a specific template
    
    Args:
        template_id: Template ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        
        # Get template
        result = template_service.get_template(template_id, str(user['_id']))
        
        if result['success']:
            return jsonify({
                'success': True,
                'template': result['template']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404 if 'not found' in result['error'].lower() else 400
    
    except Exception as e:
        logger.error(f"Get template error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('/<template_id>', methods=['PUT'])
@require_auth
@require_json
def update_template(template_id: str) -> tuple:
    """Update a template
    
    Args:
        template_id: Template ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        data = request.get_json()
        
        # Validate updatable fields
        allowed_fields = ['name', 'description', 'content', 'category', 'variables', 'tags', 'is_public']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return jsonify({
                'success': False,
                'error': 'No valid fields to update'
            }), 400
        
        # Validate template name if provided
        if 'name' in update_data and not ValidationUtils.validate_string_length(update_data['name'], min_length=1, max_length=100):
            return jsonify({
                'success': False,
                'error': 'Template name must be between 1 and 100 characters'
            }), 400
        
        # Update template
        result = template_service.update_template(template_id, update_data, str(user['_id']))
        
        if result['success']:
            logger.info(f"Template updated: {template_id} by {user['email']}")
            return jsonify({
                'success': True,
                'message': 'Template updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404 if 'not found' in result['error'].lower() else 400
    
    except Exception as e:
        logger.error(f"Update template error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('/<template_id>', methods=['DELETE'])
@require_auth
def delete_template(template_id: str) -> tuple:
    """Delete a template
    
    Args:
        template_id: Template ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        
        # Delete template
        result = template_service.delete_template(template_id, str(user['_id']))
        
        if result['success']:
            logger.info(f"Template deleted: {template_id} by {user['email']}")
            return jsonify({
                'success': True,
                'message': 'Template deleted successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404 if 'not found' in result['error'].lower() else 400
    
    except Exception as e:
        logger.error(f"Delete template error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('/<template_id>/render', methods=['POST'])
@require_auth
@require_json
def render_template(template_id: str) -> tuple:
    """Render a template with provided data
    
    Args:
        template_id: Template ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        data = request.get_json()
        
        # Get template variables
        variables = data.get('variables', {})
        
        # Render template
        result = template_service.render_template(template_id, variables, str(user['_id']))
        
        if result['success']:
            return jsonify({
                'success': True,
                'rendered_content': result['rendered_content']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404 if 'not found' in result['error'].lower() else 400
    
    except Exception as e:
        logger.error(f"Render template error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('/<template_id>/preview', methods=['POST'])
@require_auth
@require_json
def preview_template(template_id: str) -> tuple:
    """Preview a template with sample data
    
    Args:
        template_id: Template ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        data = request.get_json()
        
        # Get custom sample data if provided
        sample_data = data.get('sample_data')
        
        # Preview template
        result = template_service.preview_template(template_id, str(user['_id']), sample_data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'preview_content': result['preview_content'],
                'sample_data': result['sample_data']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404 if 'not found' in result['error'].lower() else 400
    
    except Exception as e:
        logger.error(f"Preview template error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('/<template_id>/variables', methods=['GET'])
@require_auth
def get_template_variables(template_id: str) -> tuple:
    """Get template variable definitions
    
    Args:
        template_id: Template ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        
        # Get template variables
        result = template_service.get_template_variables(template_id, str(user['_id']))
        
        if result['success']:
            return jsonify({
                'success': True,
                'variables': result['variables']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404 if 'not found' in result['error'].lower() else 400
    
    except Exception as e:
        logger.error(f"Get template variables error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('/<template_id>/validate', methods=['POST'])
@require_auth
@require_json
def validate_template_data(template_id: str) -> tuple:
    """Validate data against template requirements
    
    Args:
        template_id: Template ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        data = request.get_json()
        
        # Get template data to validate
        template_data = data.get('data', {})
        
        # Validate template data
        result = template_service.validate_template_data(template_id, template_data, str(user['_id']))
        
        if result['success']:
            return jsonify({
                'success': True,
                'is_valid': result['is_valid'],
                'errors': result.get('errors', [])
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404 if 'not found' in result['error'].lower() else 400
    
    except Exception as e:
        logger.error(f"Validate template data error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('/categories', methods=['GET'])
@require_auth
def get_template_categories() -> tuple:
    """Get available template categories
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        # Get template categories
        result = template_service.get_template_categories()
        
        if result['success']:
            return jsonify({
                'success': True,
                'categories': result['categories']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        logger.error(f"Get template categories error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('/stats', methods=['GET'])
@require_auth
@require_roles(['admin', 'manager'])
def get_template_stats() -> tuple:
    """Get template usage statistics
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        # Get template statistics
        result = template_service.get_template_stats()
        
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
        logger.error(f"Get template stats error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('/<template_id>/duplicate', methods=['POST'])
@require_auth
@require_json
def duplicate_template(template_id: str) -> tuple:
    """Duplicate a template
    
    Args:
        template_id: Template ID to duplicate
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        data = request.get_json()
        
        # Get new template name
        new_name = data.get('name')
        if not new_name:
            return jsonify({
                'success': False,
                'error': 'New template name is required'
            }), 400
        
        # Validate template name
        if not ValidationUtils.validate_string_length(new_name, min_length=1, max_length=100):
            return jsonify({
                'success': False,
                'error': 'Template name must be between 1 and 100 characters'
            }), 400
        
        # Get original template
        template_result = template_service.get_template(template_id, str(user['_id']))
        
        if not template_result['success']:
            return jsonify({
                'success': False,
                'error': template_result['error']
            }), 404 if 'not found' in template_result['error'].lower() else 400
        
        # Create duplicate template
        original_template = template_result['template']
        duplicate_data = {
            'name': new_name,
            'description': f"Copy of {original_template['name']}",
            'content': original_template['content'],
            'category': original_template['category'],
            'variables': original_template.get('variables', []),
            'tags': original_template.get('tags', []),
            'is_public': False,  # Duplicates are private by default
            'created_by': str(user['_id'])
        }
        
        result = template_service.create_template(duplicate_data)
        
        if result['success']:
            logger.info(f"Template duplicated: {template_id} -> {result['template_id']} by {user['email']}")
            return jsonify({
                'success': True,
                'message': 'Template duplicated successfully',
                'template_id': result['template_id']
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        logger.error(f"Duplicate template error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500