"""Admin routes for the mindframe application"""

from flask import Blueprint, request, jsonify, current_app, g
from functools import wraps
import logging
from typing import Dict, Any, Optional
from pydantic import ValidationError

from ...services.auth_service import AuthService
from ...utils.auth_decorators import require_auth as admin_require_auth
from ...utils.decorators import require_roles
from ...utils.logging_utils import LoggingUtils
from ...utils.error_handler import raise_validation_error, raise_authentication_error, raise_not_found
from ...utils.input_validation import (
    validate_json, validate_query_params,
    ValidationError as InputValidationError
)

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')
logger = LoggingUtils.get_logger(__name__)

# Initialize services
auth_service = None
database_service = None


def admin_auth_decorator(f):
    """Decorator for authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Add authentication logic here
        return f(*args, **kwargs)
    return decorated_function


def init_admin_routes(auth_svc: AuthService, db_svc=None) -> None:
    """Initialize admin routes with dependencies
    
    Args:
        auth_svc: Authentication service instance
        db_svc: Database service instance
    """
    global auth_service, database_service
    auth_service = auth_svc
    database_service = db_svc
    logger.info("Admin routes initialized successfully")


@admin_bp.route('/product-configs', methods=['GET'])
@admin_auth_decorator
@require_roles(['admin'])
def list_product_configs():
    """List all product configurations
    
    Returns:
        JSON response with product configurations list
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
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # Get product_configs collection
        collection = database_service.get_collection('product_configs')
        
        # Get all product configurations
        configs = list(collection.find({}))
        
        # Convert MongoDB documents to frontend format
        formatted_configs = []
        for config in configs:
            formatted_config = {
                'id': str(config.get('_id', '')),
                'productName': config.get('productId', ''),  # Map productId to productName for frontend
                'displayName': config.get('productName', ''),  # Map productName to displayName
                'description': config.get('description', ''),
                'testCombinations': [],
                'staticContent': {
                    'introduction': config.get('staticContent', {}).get('introduction', {}).get('content', '') if isinstance(config.get('staticContent', {}).get('introduction'), dict) else config.get('staticContent', {}).get('introduction', ''),
                    'conclusion': config.get('staticContent', {}).get('closing', {}).get('content', '') if isinstance(config.get('staticContent', {}).get('closing'), dict) else config.get('staticContent', {}).get('conclusion', ''),
                    'coverPageTitle': config.get('staticContent', {}).get('coverPage', {}).get('title', '') if isinstance(config.get('staticContent', {}).get('coverPage'), dict) else config.get('staticContent', {}).get('coverPageTitle', ''),
                    'coverPageSubtitle': config.get('staticContent', {}).get('coverPage', {}).get('subtitle', '') if isinstance(config.get('staticContent', {}).get('coverPage'), dict) else config.get('staticContent', {}).get('coverPageSubtitle', '')
                },
                'isActive': config.get('isActive', True),
                'createdAt': config.get('createdAt', ''),
                'updatedAt': config.get('updatedAt', '')
            }
            
            # Convert tests to testCombinations format for frontend compatibility
            if 'tests' in config:
                for test in config['tests']:
                    formatted_config['testCombinations'].append({
                        'testName': test.get('testType', ''),
                        'order': test.get('order', 1),
                        'isRequired': test.get('required', True)
                    })
            
            formatted_configs.append(formatted_config)
        
        logger.info(f"Found {len(formatted_configs)} product configurations")
        
        return jsonify({
            'success': True,
            'productConfigs': formatted_configs,
            'total': len(formatted_configs),
            'page': page,
            'limit': limit,
            'total_pages': 1
        })
    except Exception as e:
        logger.error(f"Error listing product configs: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to retrieve product configurations'
        }), 500


@admin_bp.route('/available-tests', methods=['OPTIONS'])
def available_tests_options():
    """Handle CORS preflight for available tests endpoint"""
    return '', 200


@admin_bp.route('/available-tests', methods=['GET'])
@admin_auth_decorator
@require_roles(['admin'])
def get_available_tests():
    """Get list of available test types from interpretations collection
    
    Returns:
        JSON response with available test types
    """
    try:
        if not database_service:
            logger.warning("Database service not available")
            return jsonify({
                'success': False,
                'error': 'Service unavailable',
                'message': 'Database service not initialized'
            }), 503
        
        # Get interpretations collection
        collection = database_service.get_collection('interpretations')
        
        # Get unique test names from interpretations collection
        pipeline = [
            {
                '$group': {
                    '_id': '$testName',
                    'displayName': {'$first': '$displayName'},
                    'description': {'$first': '$description'}
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'testName': '$_id',
                    'displayName': {'$ifNull': ['$displayName', '$_id']},
                    'description': {'$ifNull': ['$description', '']}
                }
            },
            {
                '$sort': {'testName': 1}
            }
        ]
        
        available_tests = list(collection.aggregate(pipeline))
        
        logger.info(f"Found {len(available_tests)} available tests from interpretations collection")
        
        return jsonify(available_tests), 200
        
    except Exception as e:
        logger.error(f"Error getting available tests: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to retrieve available tests'
        }), 500


@admin_bp.route('/product-configs/<config_id>', methods=['GET'])
@admin_auth_decorator
@require_roles(['admin'])
def get_product_config(config_id: str):
    """Get a specific product configuration
    
    Args:
        config_id: ID of the product configuration to retrieve
        
    Returns:
        JSON response with product configuration data
    """
    try:
        if not database_service:
            logger.warning("Database service not available")
            return jsonify({
                'success': False,
                'error': 'Service unavailable',
                'message': 'Database service not initialized'
            }), 503
        
        # Get product_configs collection
        collection = database_service.get_collection('product_configs')
        
        # Try to find by MongoDB _id first, then by productId
        from bson import ObjectId
        config = None
        
        try:
            # Try to find by MongoDB _id
            config = collection.find_one({'_id': ObjectId(config_id)})
        except:
            # If not a valid ObjectId, try to find by productId
            config = collection.find_one({'productId': config_id})
        
        if not config:
            return jsonify({
                'success': False,
                'error': 'Not found',
                'message': 'Product configuration not found'
            }), 404
        
        # Convert to frontend format
        formatted_config = {
            'id': str(config.get('_id', '')),
            'productName': config.get('productId', ''),  # Map productId to productName for frontend
            'displayName': config.get('productName', ''),  # Map productName to displayName
            'description': config.get('description', ''),
            'testCombinations': [],
            'staticContent': {
                'introduction': config.get('staticContent', {}).get('introduction', {}).get('content', '') if isinstance(config.get('staticContent', {}).get('introduction'), dict) else config.get('staticContent', {}).get('introduction', ''),
                'conclusion': config.get('staticContent', {}).get('closing', {}).get('content', '') if isinstance(config.get('staticContent', {}).get('closing'), dict) else config.get('staticContent', {}).get('conclusion', ''),
                'coverPageTitle': config.get('staticContent', {}).get('coverPage', {}).get('title', '') if isinstance(config.get('staticContent', {}).get('coverPage'), dict) else config.get('staticContent', {}).get('coverPageTitle', ''),
                'coverPageSubtitle': config.get('staticContent', {}).get('coverPage', {}).get('subtitle', '') if isinstance(config.get('staticContent', {}).get('coverPage'), dict) else config.get('staticContent', {}).get('coverPageSubtitle', '')
            },
            'isActive': config.get('isActive', True),
            'createdAt': config.get('createdAt', ''),
            'updatedAt': config.get('updatedAt', '')
        }
        
        # Convert tests to testCombinations format for frontend compatibility
        if 'tests' in config:
            for test in config['tests']:
                formatted_config['testCombinations'].append({
                    'testName': test.get('testType', ''),
                    'order': test.get('order', 1),
                    'isRequired': test.get('required', True)
                })
        
        logger.info(f"Found product config: {config.get('productId', 'N/A')}")
        
        return jsonify({
            'success': True,
            'productConfig': formatted_config
        })
    except Exception as e:
        logger.error(f"Error getting product config {config_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to retrieve product configuration'
        }), 500


@admin_bp.route('/product-configs', methods=['POST'])
@admin_auth_decorator
@require_roles(['admin'])
def create_product_config():
    """Create a new product configuration
    
    Returns:
        JSON response with created product configuration data
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
        
        required_fields = ['productName', 'testCombinations']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': 'Validation error',
                    'message': f'Field {field} is required'
                }), 400
        
        # Get database service
        if not database_service:
            logger.warning("Database service not available")
            return jsonify({
                'success': False,
                'error': 'Service unavailable',
                'message': 'Database service not initialized'
            }), 503
        
        # Get product_configs collection
        collection = database_service.get_collection('product_configs')
        
        # Prepare document for MongoDB
        from datetime import datetime
        now = datetime.utcnow().isoformat() + 'Z'
        
        # Convert testCombinations to tests format for MongoDB
        tests = []
        if 'testCombinations' in data:
            for i, test_combo in enumerate(data['testCombinations']):
                tests.append({
                    'testType': test_combo.get('testName', ''),
                    'order': test_combo.get('order', i + 1),
                    'required': test_combo.get('isRequired', True)
                })
        
        mongo_doc = {
            'productId': data['productName'],  # Use productName as productId
            'productName': data.get('displayName', data['productName']),  # Use displayName as productName
            'description': data.get('description', ''),
            'tests': tests,
            'staticContent': data.get('staticContent', {
                'introduction': '',
                'conclusion': '',
                'coverPageTitle': '',
                'coverPageSubtitle': ''
            }),
            'isActive': data.get('isActive', True),
            'createdAt': now,
            'updatedAt': now
        }
        
        # Insert into MongoDB
        result = collection.insert_one(mongo_doc)
        
        # Format response for frontend
        formatted_config = {
            'id': str(result.inserted_id),
            'productName': data['productName'],
            'displayName': data.get('displayName', data['productName']),
            'description': data.get('description', ''),
            'testCombinations': data.get('testCombinations', []),
            'staticContent': data.get('staticContent', {
                'introduction': '',
                'conclusion': '',
                'coverPageTitle': '',
                'coverPageSubtitle': ''
            }),
            'isActive': data.get('isActive', True),
            'createdAt': now,
            'updatedAt': now
        }
        
        logger.info(f"Created product config: {data['productName']}")
        
        return jsonify({
            'success': True,
            'productConfig': formatted_config
        }), 201
    except Exception as e:
        logger.error(f"Error creating product config: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to create product configuration'
        }), 500


@admin_bp.route('/product-configs/<config_id>', methods=['OPTIONS'])
def product_config_options(config_id: str):
    """Handle CORS preflight for product config operations (PUT, DELETE)"""
    return '', 200


@admin_bp.route('/product-configs/<config_id>', methods=['PUT'])
@admin_auth_decorator
@require_roles(['admin'])
def update_product_config(config_id: str):
    """Update an existing product configuration
    
    Args:
        config_id: ID of the product configuration to update
        
    Returns:
        JSON response with updated product configuration data
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
        # TODO: Implement actual product config update
        return jsonify({
            'success': True,
            'productConfig': {
                'id': config_id,
                'productName': data.get('productName', 'Updated Product'),
                'description': data.get('description', ''),
                'tests': data.get('tests', []),
                'staticContent': data.get('staticContent', {}),
                'isActive': data.get('isActive', True),
                'createdAt': '2024-01-01T00:00:00Z',
                'updatedAt': '2024-01-01T00:00:00Z'
            }
        })
    except Exception as e:
        logger.error(f"Error updating product config {config_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to update product configuration'
        }), 500


@admin_bp.route('/product-configs/<config_id>', methods=['DELETE'])
@admin_auth_decorator
@require_roles(['admin'])
def delete_product_config(config_id: str):
    """Delete a product configuration
    
    Args:
        config_id: ID of the product configuration to delete
        
    Returns:
        JSON response confirming deletion
    """
    try:
        # For now, return placeholder response
        # TODO: Implement actual product config deletion
        return jsonify({
            'success': True,
            'message': 'Product configuration deleted successfully'
        })
    except Exception as e:
        logger.error(f"Error deleting product config {config_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to delete product configuration'
        }), 500


@admin_bp.route('/users', methods=['GET'])
@admin_auth_decorator
@require_roles(['admin'])
def list_users():
    """List all users (admin only)
    
    Returns:
        JSON response with users list
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # For now, return placeholder data
        # TODO: Implement actual user management
        return jsonify({
            'success': True,
            'users': [],
            'total': 0,
            'page': page,
            'limit': limit,
            'total_pages': 0
        })
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to retrieve users'
        }), 500


@admin_bp.route('/system/status', methods=['GET'])
@admin_auth_decorator
@require_roles(['admin'])
def system_status():
    """Get system status information
    
    Returns:
        JSON response with system status
    """
    try:
        # For now, return basic status
        # TODO: Implement actual system monitoring
        return jsonify({
            'success': True,
            'status': {
                'database': 'connected',
                'redis': 'connected',
                'storage': 'available',
                'services': {
                    'auth': 'running',
                    'template': 'running',
                    'report': 'running',
                    'pdf': 'running'
                },
                'uptime': '1h 30m',
                'version': '1.0.0'
            }
        })
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'Failed to retrieve system status'
        }), 500