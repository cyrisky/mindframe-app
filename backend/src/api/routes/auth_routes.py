"""Authentication routes for the mindframe application"""

from flask import Blueprint, request, jsonify, current_app, g
from functools import wraps
import logging
from typing import Dict, Any, Optional
from pydantic import ValidationError

from ...services.auth_service import AuthService
from ...utils.logging_utils import LoggingUtils
from ...utils.auth_decorators import require_auth
from ...utils.input_validation import (
    validate_json, ValidationError as InputValidationError
)
from ...utils.exceptions import (
    ValidationError as APIValidationError,
    AuthenticationError,
    ResourceNotFoundError
)
from ...utils.error_handler import (
    raise_validation_error,
    raise_authentication_error,
    raise_not_found
)
from ...utils.rate_limiter import get_rate_limit_decorators
from ...models.request_models import (
    UserRegistrationRequest, UserLoginRequest, PasswordResetRequest,
    PasswordResetConfirmRequest, ChangePasswordRequest, RefreshTokenRequest,
    EmailVerificationRequest, ForgotPasswordRequest, UserProfileUpdateRequest
)

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
    
    # Apply rate limiting to auth endpoints
    # _apply_rate_limiting_to_auth_routes()  # Temporarily disabled to fix endpoint conflicts


def _apply_rate_limiting_to_auth_routes() -> None:
    """Apply rate limiting decorators to authentication routes"""
    try:
        from flask import current_app
        decorators = get_rate_limit_decorators(current_app)
        
        if not decorators:
            logger.warning("Rate limiting decorators not available for auth routes")
            return
        
        # Apply auth endpoint rate limiting (10 requests per minute)
        auth_endpoints = [
            'auth.register',
            'auth.login', 
            'auth.forgot_password',
            'auth.reset_password',
            'auth.verify_email',
            'auth.resend_verification'
        ]
        
        # Apply rate limiting to auth endpoints
        for endpoint in auth_endpoints:
            try:
                # Get the view function
                view_func = current_app.view_functions.get(endpoint)
                if view_func:
                    # Apply the auth endpoints rate limiter
                    limited_func = decorators.auth_endpoints(view_func)
                    current_app.view_functions[endpoint] = limited_func
                    logger.debug(f"Applied auth rate limiting to {endpoint}")
            except Exception as e:
                logger.warning(f"Failed to apply rate limiting to {endpoint}: {e}")
        
        # Apply stricter rate limiting to sensitive endpoints
        sensitive_endpoints = [
            'auth.change_password',
            'auth.delete_account'
        ]
        
        for endpoint in sensitive_endpoints:
            try:
                view_func = current_app.view_functions.get(endpoint)
                if view_func:
                    # Apply stricter rate limiting (5 requests per minute)
                    limited_func = decorators.custom_limit('5/minute')(view_func)
                    current_app.view_functions[endpoint] = limited_func
                    logger.debug(f"Applied strict rate limiting to {endpoint}")
            except Exception as e:
                logger.warning(f"Failed to apply strict rate limiting to {endpoint}: {e}")
        
        # Apply standard API rate limiting to other endpoints
        standard_endpoints = [
            'auth.refresh_token',
            'auth.profile',
            'auth.update_profile',
            'auth.logout'
        ]
        
        for endpoint in standard_endpoints:
            try:
                view_func = current_app.view_functions.get(endpoint)
                if view_func:
                    # Apply standard API rate limiting
                    limited_func = decorators.api_standard(view_func)
                    current_app.view_functions[endpoint] = limited_func
                    logger.debug(f"Applied standard rate limiting to {endpoint}")
            except Exception as e:
                logger.warning(f"Failed to apply standard rate limiting to {endpoint}: {e}")
        
        logger.info("Rate limiting applied to auth routes successfully")
        
    except Exception as e:
        logger.error(f"Failed to apply rate limiting to auth routes: {e}")
        # Don't fail the initialization if rate limiting setup fails
        pass


def handle_validation_error(error: Exception) -> None:
    """Handle validation errors using centralized error handling"""
    if isinstance(error, ValidationError):
        # Convert Pydantic validation error to our API validation error
        details = {}
        for err in error.errors():
            field = '.'.join(str(loc) for loc in err['loc'])
            details[field] = err['msg']
        raise_validation_error(
            "Request validation failed",
            details=details
        )
    elif isinstance(error, InputValidationError):
        raise_validation_error(
            error.message,
            field=getattr(error, 'field', None),
            details=getattr(error, 'details', None)
        )
    else:
        # Re-raise other exceptions to be handled by the centralized handler
        raise error


@auth_bp.route('/register', methods=['POST'])
@validate_json(pydantic_model=UserRegistrationRequest)
def register() -> tuple:
    """Register a new user
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        # Get validated data from request (it's a dict after validation)
        validated_data: dict = request.validated_data
        
        # Register user
        result = auth_service.register_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            role=validated_data.get('role', 'user')
        )
        
        if result['success']:
            logger.info(f"User registered successfully: {validated_data['email']}")
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
    
    except (ValidationError, InputValidationError) as e:
        return handle_validation_error(e)
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/login', methods=['POST'])
@validate_json(pydantic_model=UserLoginRequest)
def login() -> tuple:
    """User login
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        # Get validated data from request
        validated_data: UserLoginRequest = request.validated_data
        
        # Attempt login
        result = auth_service.login_user(
            email=validated_data['email'],
            password=validated_data['password'],
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        if result['success']:
            logger.info(f"User logged in successfully: {validated_data['email']}")
            return jsonify({
                'user': result['user'],
                'token': result['access_token'],
                'refreshToken': result['refresh_token'],
                'expiresIn': 3600
            }), 200
        else:
            logger.warning(f"Login failed for {validated_data['email']}: {result['error']}")
            return jsonify({
                'success': False,
                'error': result['error']
            }), 401
    
    except (ValidationError, InputValidationError) as e:
        return handle_validation_error(e)
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@validate_json(pydantic_model=RefreshTokenRequest)
def refresh_token() -> tuple:
    """Refresh access token
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        # Get validated data from request
        validated_data: RefreshTokenRequest = request.validated_data
        
        # Refresh token
        result = auth_service.refresh_access_token(validated_data['refresh_token'])
        
        if result['success']:
            return jsonify({
                'user': result.get('user'),
                'token': result['access_token'],
                'expiresIn': 3600
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 401
    
    except (ValidationError, InputValidationError) as e:
        return handle_validation_error(e)
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
@require_auth()
def get_profile() -> tuple:
    """Get user profile
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user_id = g.current_user  # This is the user ID string from JWT
        
        # Fetch full user data from database using auth service
        user = auth_service.db_service.get_user(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'role': user.get('roles', ['user'])[0] if user.get('roles') else 'user',
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
@require_auth()
@validate_json(pydantic_model=UserProfileUpdateRequest)
def update_profile() -> tuple:
    """Update user profile
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        validated_data: UserProfileUpdateRequest = request.validated_data
        
        # Convert to dict for service call
        update_data = validated_data
        
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
    
    except (ValidationError, InputValidationError) as e:
        return handle_validation_error(e)
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/change-password', methods=['POST'])
@require_auth()
@validate_json(pydantic_model=ChangePasswordRequest)
def change_password() -> tuple:
    """Change user password
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        validated_data: ChangePasswordRequest = request.validated_data
        
        # Change password
        result = auth_service.change_password(
            str(user['_id']),
            validated_data['current_password'],
            validated_data['new_password']
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
    
    except (ValidationError, InputValidationError) as e:
        return handle_validation_error(e)
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/forgot-password', methods=['POST'])
@validate_json(pydantic_model=ForgotPasswordRequest)
def forgot_password() -> tuple:
    """Request password reset
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        validated_data: ForgotPasswordRequest = request.validated_data
        
        # Request password reset
        result = auth_service.request_password_reset(validated_data['email'])
        
        # Always return success to prevent email enumeration
        logger.info(f"Password reset requested for: {validated_data['email']}")
        return jsonify({
            'success': True,
            'message': 'If the email exists, a password reset link has been sent'
        }), 200
    
    except (ValidationError, InputValidationError) as e:
        return handle_validation_error(e)
    except Exception as e:
        logger.error(f"Forgot password error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/reset-password', methods=['POST'])
@validate_json(pydantic_model=PasswordResetConfirmRequest)
def reset_password() -> tuple:
    """Reset password with token
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        validated_data: PasswordResetConfirmRequest = request.validated_data
        
        # Reset password
        result = auth_service.reset_password(validated_data['token'], validated_data['new_password'])
        
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
    
    except (ValidationError, InputValidationError) as e:
        return handle_validation_error(e)
    except Exception as e:
        logger.error(f"Reset password error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/verify-email', methods=['POST'])
@validate_json(pydantic_model=EmailVerificationRequest)
def verify_email() -> tuple:
    """Verify email address
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        validated_data: EmailVerificationRequest = request.validated_data
        
        # Verify email
        result = auth_service.verify_email(validated_data['token'])
        
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
    
    except (ValidationError, InputValidationError) as e:
        return handle_validation_error(e)
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@auth_bp.route('/sessions', methods=['GET'])
@require_auth()
def get_sessions() -> tuple:
    """Get user sessions
    
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        
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
@require_auth()
def revoke_session(session_id: str) -> tuple:
    """Revoke a specific session
    
    Args:
        session_id: Session ID to revoke
        
    Returns:
        tuple: JSON response and status code
    """
    try:
        user = g.current_user
        
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