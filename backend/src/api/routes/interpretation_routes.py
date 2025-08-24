"""Interpretation routes for the mindframe application"""

from flask import Blueprint, request, jsonify, current_app, g
from functools import wraps
import logging
from typing import Dict, Any, Optional
from pydantic import ValidationError
from bson import ObjectId

from ...services.auth_service import AuthService
from ...utils.auth_decorators import require_auth
from ...utils.decorators import require_roles
from ...utils.logging_utils import LoggingUtils
from ...utils.error_handler import raise_validation_error, raise_authentication_error, raise_not_found
from ...utils.input_validation import (
    validate_json, validate_query_params,
    ValidationError as InputValidationError
)

# Create blueprint
interpretation_bp = Blueprint('interpretation', __name__, url_prefix='/api/interpretations')
logger = LoggingUtils.get_logger(__name__)

# Initialize services
auth_service = None
database_service = None


def init_interpretation_routes(auth_svc: AuthService, db_svc=None) -> None:
    """Initialize interpretation routes with dependencies
    
    Args:
        auth_svc: Authentication service instance
        db_svc: Database service instance
    """
    global auth_service, database_service
    auth_service = auth_svc
    database_service = db_svc
    logger.info("Interpretation routes initialized successfully")


def interpretation_auth_decorator(f):
    """Decorator for authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Add authentication logic here
        return f(*args, **kwargs)
    return decorated_function


@interpretation_bp.route('', methods=['GET'])
@interpretation_auth_decorator
def list_interpretations():
    """List all interpretations
    
    Returns:
        JSON response with interpretations list
    """
    try:
        if not database_service:
            logger.warning("Database service not available")
            return jsonify({
                'success': False,
                'error': 'Service unavailable',
                'message': 'Database service not initialized'
            }), 503
        
        # Get query parameters
        test_name = request.args.get('testName')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        skip = (page - 1) * limit
        
        # Build filter
        filter_dict = {}
        if test_name:
            filter_dict['testName'] = test_name
        
        # Get interpretations from database
        interpretations = database_service.find_many(
            'interpretations',
            filter_dict=filter_dict,
            limit=limit,
            skip=skip
        )
        
        # Convert ObjectId to string for JSON serialization
        for interpretation in interpretations:
            if '_id' in interpretation:
                interpretation['_id'] = str(interpretation['_id'])
        
        # Get total count
        total = database_service.count_documents('interpretations', filter_dict)
        total_pages = (total + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'interpretations': interpretations,
            'total': total,
            'page': page,
            'limit': limit,
            'total_pages': total_pages
        })
    except Exception as e:
        logger.error(f"Error listing interpretations: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to retrieve interpretations'
        }), 500


@interpretation_bp.route('/<interpretation_id>', methods=['GET'])
@interpretation_auth_decorator
def get_interpretation(interpretation_id: str):
    """Get a specific interpretation
    
    Args:
        interpretation_id: ID of the interpretation to retrieve
        
    Returns:
        JSON response with interpretation data
    """
    try:
        if not database_service:
            logger.warning("Database service not available")
            return jsonify({
                'success': False,
                'error': 'Service unavailable',
                'message': 'Database service not initialized'
            }), 503
        
        # Convert string ID to ObjectId for MongoDB query
        try:
            object_id = ObjectId(interpretation_id)
        except Exception:
            return jsonify({
                'success': False,
                'error': 'Invalid ID format',
                'message': f'Invalid interpretation ID format: {interpretation_id}'
            }), 400
        
        # Get interpretation from database
        interpretation = database_service.find_one(
            'interpretations',
            {'_id': object_id}
        )
        
        if not interpretation:
            return jsonify({
                'success': False,
                'error': 'Not found',
                'message': f'Interpretation with ID {interpretation_id} not found'
            }), 404
        
        # Convert ObjectId to string for JSON serialization
        if '_id' in interpretation:
            interpretation['_id'] = str(interpretation['_id'])
        
        return jsonify({
            'success': True,
            'interpretation': interpretation
        })
    except Exception as e:
        logger.error(f"Error getting interpretation {interpretation_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to retrieve interpretation'
        }), 500


@interpretation_bp.route('', methods=['POST'])
@interpretation_auth_decorator
@require_roles(['admin', 'editor'])
def create_interpretation():
    """Create a new interpretation
    
    Returns:
        JSON response with created interpretation data
    """
    try:
        if not database_service:
            logger.warning("Database service not available")
            return jsonify({
                'success': False,
                'error': 'Service unavailable',
                'message': 'Database service not initialized'
            }), 503
        
        data = request.get_json()
        
        # Basic validation
        if not data:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'message': 'Request body is required'
            }), 400
        
        # Validate required fields
        if 'testName' not in data:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'message': 'testName is required'
            }), 400
        
        # Check for dimensions/results in different possible locations
        if 'results' in data and 'dimensions' in data['results']:
            # Move dimensions to root level for consistency
            data['dimensions'] = data['results']['dimensions']
        
        if 'dimensions' not in data and 'results' not in data:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'message': 'Either dimensions or results is required'
            }), 400
        
        # Add timestamps and default values
        from datetime import datetime
        data['createdAt'] = datetime.utcnow()
        data['updatedAt'] = datetime.utcnow()
        
        # Set default isActive to True if not provided
        if 'isActive' not in data:
            data['isActive'] = True
        
        # Insert interpretation into database
        result = database_service.insert_one('interpretations', data)
        
        if not result:
            return jsonify({
                'success': False,
                'error': 'Database error',
                'message': 'Failed to create interpretation'
            }), 500
        
        # Get the created interpretation
        created_interpretation = database_service.find_one(
            'interpretations',
            {'_id': result}
        )
        
        if created_interpretation and '_id' in created_interpretation:
            created_interpretation['_id'] = str(created_interpretation['_id'])
        
        return jsonify({
            'success': True,
            'interpretation': created_interpretation,
            'message': 'Interpretation created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating interpretation: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to create interpretation'
        }), 500


@interpretation_bp.route('/<interpretation_id>', methods=['PUT'])
@interpretation_auth_decorator
@require_roles(['admin', 'editor'])
def update_interpretation(interpretation_id: str):
    """Update an existing interpretation
    
    Args:
        interpretation_id: ID of the interpretation to update
        
    Returns:
        JSON response with updated interpretation data
    """
    try:
        data = request.get_json()
        
        # Basic validation
        if not data:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'message': 'Request body is required'
            }), 400
        
        # For now, return placeholder response
        # TODO: Implement actual interpretation update
        return jsonify({
            'success': True,
            'interpretation': {
                'id': interpretation_id,
                'title': data.get('title', 'Updated Interpretation'),
                'content': data.get('content', ''),
                'type': data.get('type', 'personality'),
                'created_at': '2024-01-01T00:00:00Z',
                'updated_at': '2024-01-01T00:00:00Z'
            }
        })
    except Exception as e:
        logger.error(f"Error updating interpretation {interpretation_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to update interpretation'
        }), 500


@interpretation_bp.route('/<interpretation_id>', methods=['DELETE'])
@interpretation_auth_decorator
@require_roles(['admin'])
def delete_interpretation(interpretation_id: str):
    """Delete an interpretation
    
    Args:
        interpretation_id: ID of the interpretation to delete
        
    Returns:
        JSON response confirming deletion
    """
    try:
        # For now, return placeholder response
        # TODO: Implement actual interpretation deletion
        return jsonify({
            'success': True,
            'message': 'Interpretation deleted successfully'
        })
    except Exception as e:
        logger.error(f"Error deleting interpretation {interpretation_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to delete interpretation'
        }), 500


@interpretation_bp.route('/<interpretation_id>/duplicate', methods=['OPTIONS'])
def duplicate_interpretation_options(interpretation_id: str):
    """Handle CORS preflight request for duplicate endpoint"""
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'POST,OPTIONS')
    return response

@interpretation_bp.route('/<interpretation_id>/duplicate', methods=['POST'])
@interpretation_auth_decorator
@require_roles(['admin', 'editor'])
def duplicate_interpretation(interpretation_id: str):
    """Duplicate an interpretation
    
    Args:
        interpretation_id: ID of the interpretation to duplicate
        
    Returns:
        JSON response with duplicated interpretation data
    """
    try:
        if not database_service:
            logger.warning("Database service not available")
            return jsonify({
                'success': False,
                'error': 'Service unavailable',
                'message': 'Database service not initialized'
            }), 503
        
        data = request.get_json()
        
        if not data or 'testName' not in data:
            return jsonify({
                'success': False,
                'error': 'Validation error',
                'message': 'testName is required'
            }), 400
        
        # Convert string ID to ObjectId for MongoDB query
        try:
            object_id = ObjectId(interpretation_id)
        except Exception:
            return jsonify({
                'success': False,
                'error': 'Invalid ID format',
                'message': f'Invalid interpretation ID format: {interpretation_id}'
            }), 400
        
        # Find original interpretation
        original = database_service.find_one(
            'interpretations',
            {'_id': object_id}
        )
        
        if not original:
            return jsonify({
                'success': False,
                'error': 'Not found',
                'message': f'Interpretation with ID {interpretation_id} not found'
            }), 404
        
        # Create duplicate data
        duplicate_data = original.copy()
        if '_id' in duplicate_data:
            del duplicate_data['_id']  # Remove original ID
        
        # Use the provided test name
        duplicate_data['testName'] = data['testName']
        
        # Update timestamps if they exist
        from datetime import datetime
        duplicate_data['createdAt'] = datetime.utcnow()
        duplicate_data['updatedAt'] = datetime.utcnow()
        
        # Insert duplicate
        result = database_service.insert_one('interpretations', duplicate_data)
        
        if not result:
            return jsonify({
                'success': False,
                'error': 'Database error',
                'message': 'Failed to create duplicate interpretation'
            }), 500
        
        # Get the created duplicate
        created_duplicate = database_service.find_one(
            'interpretations',
            {'_id': result}
        )
        
        if created_duplicate and '_id' in created_duplicate:
            created_duplicate['_id'] = str(created_duplicate['_id'])
        
        return jsonify({
            'success': True,
            'interpretation': created_duplicate,
            'message': 'Interpretation duplicated successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error duplicating interpretation {interpretation_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to duplicate interpretation'
        }), 500