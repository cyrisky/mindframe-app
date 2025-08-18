"""Authentication routes for the mindframe application"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import logging
from typing import Dict, Any, Optional

from ...services.auth_service import AuthService
from ...utils.validation_utils import ValidationUtils
from ...utils.logging_utils import LoggingUtils
from ...utils.decorators import require_auth, require_roles

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
logger = LoggingUtils.get_logger(__name__)

# Initialize services
auth_service = None


def init_auth_routes(auth_svc: AuthService) -> None:
    """Initialize auth routes with services
    
    Args:
        auth_svc: Authentication service instance
    """
    global auth_service
    auth_service = auth_svc


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


@auth_bp.route('/register', methods=['POST'])
@require_json
def register() -> tuple:
    """Register a new user
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'first_name', 'last_name']
        validation_errors = ValidationUtils.validate_required_fields(data, required_fields)
        
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Validation failed',
                'details': validation_errors
            }), 400
        
        # Validate email format
        if not ValidationUtils.validate_email(data['email']):
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        # Validate password strength
        password_errors = ValidationUtils.validate_password(data['password'])
        if password_errors:
            return jsonify({
                'success': False,
                'error': 'Password validation failed',
                'details': password_errors
            }), 400
        
        # Register user
        result = auth_service.register_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data.get('role', 'user')
        )
        
        if result['success']:
            logger.info(f"User registered successfully: {data['email']}")
            return jsonify({
                'success': True,
                'message': 'User registered successfully',
                'user_id': result['user_id']
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/login', methods=['POST'])
@require_json
def login() -> tuple:
    """User login
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password']
        validation_errors = ValidationUtils.validate_required_fields(data, required_fields)
        
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
        
        # Attempt login
        result = auth_service.login_user(
            email=data['email'],
            password=data['password'],
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        if result['success']:
            logger.info(f"User logged in successfully: {data['email']}")
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'access_token': result['access_token'],
                'refresh_token': result['refresh_token'],
                'user': result['user']
            }), 200
        else:
            logger.warning(f"Login failed for {data['email']}: {result['error']}")
            return jsonify({
                'success': False,
                'error': result['error']
            }), 401
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@require_json
def refresh_token() -> tuple:
    """Refresh access token
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        data = request.get_json()
        
        if 'refresh_token' not in data:
            return jsonify({
                'success': False,
                'error': 'Refresh token is required'
            }), 400
        
        # Refresh token
        result = auth_service.refresh_access_token(data['refresh_token'])
        
        if result['success']:
            return jsonify({
                'success': True,
                'access_token': result['access_token']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 401
    
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
def logout() -> tuple:
    """User logout
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        # Get token from request
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Invalid authorization header'
            }), 400
        
        token = auth_header.split(' ')[1]
        
        # Logout user
        result = auth_service.logout_user(token)
        
        if result['success']:
            logger.info(f"User logged out successfully")
            return jsonify({
                'success': True,
                'message': 'Logout successful'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile() -> tuple:
    """Get user profile
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        
        return jsonify({
            'success': True,
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'role': user['role'],
                'created_at': user['created_at'].isoformat(),
                'last_login': user.get('last_login', {}).get('timestamp', '').isoformat() if user.get('last_login', {}).get('timestamp') else None
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/profile', methods=['PUT'])
@require_auth
@require_json
def update_profile() -> tuple:
    """Update user profile
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        data = request.get_json()
        
        # Validate updatable fields
        allowed_fields = ['first_name', 'last_name']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return jsonify({
                'success': False,
                'error': 'No valid fields to update'
            }), 400
        
        # Update profile
        result = auth_service.update_user_profile(str(user['_id']), update_data)
        
        if result['success']:
            logger.info(f"Profile updated for user: {user['email']}")
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/change-password', methods=['POST'])
@require_auth
@require_json
def change_password() -> tuple:
    """Change user password
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['current_password', 'new_password']
        validation_errors = ValidationUtils.validate_required_fields(data, required_fields)
        
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Current password and new password are required'
            }), 400
        
        # Validate new password strength
        password_errors = ValidationUtils.validate_password(data['new_password'])
        if password_errors:
            return jsonify({
                'success': False,
                'error': 'New password validation failed',
                'details': password_errors
            }), 400
        
        # Change password
        result = auth_service.change_password(
            str(user['_id']),
            data['current_password'],
            data['new_password']
        )
        
        if result['success']:
            logger.info(f"Password changed for user: {user['email']}")
            return jsonify({
                'success': True,
                'message': 'Password changed successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/forgot-password', methods=['POST'])
@require_json
def forgot_password() -> tuple:
    """Request password reset
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        data = request.get_json()
        
        if 'email' not in data:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400
        
        # Validate email format
        if not ValidationUtils.validate_email(data['email']):
            return jsonify({
                'success': False,
                'error': 'Invalid email format'
            }), 400
        
        # Request password reset
        result = auth_service.request_password_reset(data['email'])
        
        # Always return success to prevent email enumeration
        logger.info(f"Password reset requested for: {data['email']}")
        return jsonify({
            'success': True,
            'message': 'If the email exists, a password reset link has been sent'
        }), 200
    
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/reset-password', methods=['POST'])
@require_json
def reset_password() -> tuple:
    """Reset password with token
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['token', 'new_password']
        validation_errors = ValidationUtils.validate_required_fields(data, required_fields)
        
        if validation_errors:
            return jsonify({
                'success': False,
                'error': 'Token and new password are required'
            }), 400
        
        # Validate new password strength
        password_errors = ValidationUtils.validate_password(data['new_password'])
        if password_errors:
            return jsonify({
                'success': False,
                'error': 'New password validation failed',
                'details': password_errors
            }), 400
        
        # Reset password
        result = auth_service.reset_password(data['token'], data['new_password'])
        
        if result['success']:
            logger.info("Password reset completed successfully")
            return jsonify({
                'success': True,
                'message': 'Password reset successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/verify-email', methods=['POST'])
@require_json
def verify_email() -> tuple:
    """Verify email address
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        data = request.get_json()
        
        if 'token' not in data:
            return jsonify({
                'success': False,
                'error': 'Verification token is required'
            }), 400
        
        # Verify email
        result = auth_service.verify_email(data['token'])
        
        if result['success']:
            logger.info("Email verified successfully")
            return jsonify({
                'success': True,
                'message': 'Email verified successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/sessions', methods=['GET'])
@require_auth
def get_sessions() -> tuple:
    """Get user sessions
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        
        # Get user sessions
        result = auth_service.get_user_sessions(str(user['_id']))
        
        if result['success']:
            return jsonify({
                'success': True,
                'sessions': result['sessions']
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        logger.error(f"Get sessions error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/sessions/<session_id>', methods=['DELETE'])
@require_auth
def revoke_session(session_id: str) -> tuple:
    """Revoke a specific session
    
    Args:
        session_id: Session ID to revoke
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = request.current_user
        
        # Revoke session
        result = auth_service.revoke_session(str(user['_id']), session_id)
        
        if result['success']:
            logger.info(f"Session revoked: {session_id}")
            return jsonify({
                'success': True,
                'message': 'Session revoked successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
    
    except Exception as e:
        logger.error(f"Revoke session error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500