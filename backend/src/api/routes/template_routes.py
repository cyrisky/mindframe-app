"""Template routes for the mindframe application"""

from flask import Blueprint, request, jsonify, current_app, g
from functools import wraps
import logging
from typing import Dict, Any, Optional
from pydantic import ValidationError

from ...services.auth_service import AuthService
from ...utils.decorators import require_auth, require_roles
from ...services.template_service import TemplateService

from ...utils.logging_utils import LoggingUtils
from ...utils.error_handler import raise_validation_error, raise_authentication_error, raise_not_found
from ...utils.input_validation import (
    validate_json, validate_query_params,
    ValidationError as InputValidationError
)
from ...models.request_models import (
    TemplateCreateRequest, TemplateUpdateRequest, PaginationParams,
    SortParams, FilterParams, TemplateListParams, TemplateRenderRequest,
    TemplatePreviewRequest, TemplateValidationRequest, TemplateDuplicateRequest
)

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


def handle_validation_error(error: Exception) -> tuple:
    """Handle validation errors consistently"""
    if isinstance(error, ValidationError):
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': error.errors()
        }), 400
    elif isinstance(error, InputValidationError):
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': str(error)
        }), 400
    else:
        logger.error(f"Unexpected validation error: {str(error)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('', methods=['GET'])
@require_auth()
@validate_query_params(TemplateListParams)
def list_templates() -> tuple:
    """List templates with optional filtering
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        # Get validated query parameters
        params = request.validated_params
        
        # Build filters
        filters = {}
        if params.category:
            filters['category'] = params.category.value
        if params.search:
            filters['search'] = params.search
        
        # Get templates
        result = template_service.list_templates(
            page=params.page,
            limit=params.limit,
            filters=filters,
            sort_by=params.sort_by,
            sort_order=params.sort_order
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
    
    except (ValidationError, InputValidationError) as e:
        return handle_validation_error(e)
    except Exception as e:
        logger.error(f"List templates error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('', methods=['POST'])
@require_auth()
@validate_json()
@validate_json(pydantic_model=TemplateCreateRequest)
def create_template() -> tuple:
    """Create a new template
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        validated_data = request.validated_data
        
        # Create template
        template_data = {
            'name': validated_data['name'],
            'description': validated_data['description'],
            'content': validated_data['content'],
            'category': validated_data['category'],
            'variables': validated_data['variables'],
            'tags': validated_data['tags'],
            'is_public': validated_data['is_public'],
            'created_by': str(user['_id'])
        }
        
        result = template_service.create_template(template_data)
        
        if result['success']:
            logger.info(f"Template created: {validated_data['name']} by {user['email']}")
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
    
    except (ValidationError, InputValidationError) as e:
        return handle_validation_error(e)
    except Exception as e:
        logger.error(f"Create template error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('/<template_id>', methods=['GET'])
@require_auth()
def get_template(template_id: str) -> tuple:
    """Get a specific template
    
    Args:
        template_id: Template ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        
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
@require_auth()
@validate_json()  # 50KB limit for templates
@validate_json(pydantic_model=TemplateUpdateRequest)
def update_template(template_id: str) -> tuple:
    """Update a template
    
    Args:
        template_id: Template ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        validated_data = request.validated_data
        
        # Build update data from validated fields
        update_data = {}
        if validated_data.get('name') is not None:
            update_data['name'] = validated_data['name']
        if validated_data.get('description') is not None:
            update_data['description'] = validated_data['description']
        if validated_data.get('content') is not None:
            update_data['content'] = validated_data['content']
        if validated_data.get('category') is not None:
            update_data['category'] = validated_data['category']
        if validated_data.get('variables') is not None:
            update_data['variables'] = validated_data['variables']
        if validated_data.get('tags') is not None:
            update_data['tags'] = validated_data['tags']
        if validated_data.get('is_public') is not None:
            update_data['is_public'] = validated_data['is_public']
        
        if not update_data:
            return jsonify({
                'success': False,
                'error': 'No valid fields to update'
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
    
    except (ValidationError, InputValidationError) as e:
        return handle_validation_error(e)
    except Exception as e:
        logger.error(f"Update template error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('/<template_id>', methods=['DELETE'])
@require_auth()
def delete_template(template_id: str) -> tuple:
    """Delete a template
    
    Args:
        template_id: Template ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        
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
@require_auth()
@validate_json()
@validate_json(pydantic_model=TemplateRenderRequest)
def render_template(template_id: str) -> tuple:
    """Render a template with provided data
    
    Args:
        template_id: Template ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        validated_data = request.validated_data
        
        # Render template
        result = template_service.render_template(template_id, validated_data.variables, str(user['_id']))
        
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
    
    except (ValidationError, InputValidationError) as e:
        return handle_validation_error(e)
    except Exception as e:
        logger.error(f"Render template error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('/<template_id>/preview', methods=['POST'])
@require_auth()
@validate_json(pydantic_model=TemplatePreviewRequest)
def preview_template(template_id: str) -> tuple:
    """Preview a template with sample data
    
    Args:
        template_id: Template ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        validated_data = request.validated_data
        
        # Get custom sample data if provided
        sample_data = validated_data.sample_data
        
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
    
    except (ValidationError, InputValidationError) as e:
        logger.warning(f"Preview template validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Validation error: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Preview template error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('/<template_id>/variables', methods=['GET'])
@require_auth()
def get_template_variables(template_id: str) -> tuple:
    """Get template variable definitions
    
    Args:
        template_id: Template ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        
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
@require_auth()
@validate_json()
@validate_json(pydantic_model=TemplateValidationRequest)
def validate_template_data(template_id: str) -> tuple:
    """Validate data against template requirements
    
    Args:
        template_id: Template ID
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        validated_data = request.validated_data
        
        # Get template data to validate
        template_data = validated_data.data
        
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
    
    except (ValidationError, InputValidationError) as e:
        logger.warning(f"Validate template data validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Validation error: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Validate template data error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@template_bp.route('/categories', methods=['GET'])
@require_auth()
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
@require_auth()
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
@require_auth()
@validate_json()
@validate_json(pydantic_model=TemplateDuplicateRequest)
def duplicate_template(template_id: str) -> tuple:
    """Duplicate a template
    
    Args:
        template_id: Template ID to duplicate
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        validated_data = request.validated_data
        
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
            'name': validated_data.name,
            'description': validated_data.description or f"Copy of {original_template['name']}",
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
    
    except (ValidationError, InputValidationError) as e:
        return handle_validation_error(e)
    except Exception as e:
        logger.error(f"Duplicate template error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500