"""Decorators for API routes"""

import functools
import time
import logging
from collections import defaultdict
from threading import Lock
from flask import request, jsonify, current_app, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from bson import ObjectId
from flask_jwt_extended.exceptions import (
    NoAuthorizationError, 
    InvalidHeaderError, 
    JWTDecodeError,
    RevokedTokenError,
    WrongTokenError
)
from typing import Callable, Any, List, Optional

logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis)
_rate_limit_storage = defaultdict(list)
_rate_limit_lock = Lock()


def rate_limit(limit: str) -> Callable:
    """Rate limiting decorator with actual implementation
    
    Args:
        limit: Rate limit string (e.g., '10 per minute', '100 per hour')
        
    Returns:
        Decorator function
    """
    # Parse limit string
    parts = limit.split(' per ')
    if len(parts) != 2:
        raise ValueError(f"Invalid rate limit format: {limit}")
    
    max_requests = int(parts[0])
    time_unit = parts[1].lower()
    
    # Convert time unit to seconds
    time_mapping = {
        'second': 1,
        'minute': 60,
        'hour': 3600,
        'day': 86400
    }
    
    if time_unit not in time_mapping:
        raise ValueError(f"Unsupported time unit: {time_unit}")
    
    per_seconds = time_mapping[time_unit]
    
    def rate_limit_decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get client identifier (IP address)
            client_id = request.remote_addr or 'unknown'
            current_time = time.time()
            
            with _rate_limit_lock:
                # Clean old requests
                _rate_limit_storage[client_id] = [
                    req_time for req_time in _rate_limit_storage[client_id]
                    if current_time - req_time < per_seconds
                ]
                
                # Check rate limit
                if len(_rate_limit_storage[client_id]) >= max_requests:
                    logger.warning(f"Rate limit exceeded for {client_id}: {len(_rate_limit_storage[client_id])} requests")
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Maximum {max_requests} requests per {time_unit}',
                        'retry_after': per_seconds
                    }), 429
                
                # Add current request
                _rate_limit_storage[client_id].append(current_time)
            
            return func(*args, **kwargs)
        return wrapper
    return rate_limit_decorator


def require_api_key(func: Callable) -> Callable:
    """API key requirement decorator with actual validation
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            logger.warning(f"Missing API key for {request.endpoint} from {request.remote_addr}")
            return jsonify({
                'error': 'Missing API key',
                'message': 'API key required in X-API-Key header or api_key parameter'
            }), 401
        
        # Get valid API keys from config
        valid_api_keys = current_app.config.get('VALID_API_KEYS', [])
        
        if not valid_api_keys:
            logger.warning("No valid API keys configured")
            # In development, allow any API key if none configured
            if current_app.config.get('ENV') == 'development':
                return func(*args, **kwargs)
        
        if api_key not in valid_api_keys:
            logger.warning(f"Invalid API key attempted: {api_key[:8]}... from {request.remote_addr}")
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid'
            }), 401
        
        return func(*args, **kwargs)
    return wrapper


class AuthDecorator:
    """Class-based authentication decorator to avoid Flask endpoint conflicts"""
    
    def __init__(self, optional: bool = False, fresh: bool = False, refresh: bool = False, 
                 locations: Optional[List[str]] = None):
        self.optional = optional
        self.fresh = fresh
        self.refresh = refresh
        self.locations = locations
        # Add Flask-compatible attributes
        self.__name__ = 'auth_decorator_class'
        self.__module__ = __name__
    
    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request(
                    optional=self.optional,
                    fresh=self.fresh,
                    refresh=self.refresh,
                    locations=self.locations
                )
                current_user = get_jwt_identity()
                
                if not self.optional and not current_user:
                    logger.warning("Authentication required but no token provided")
                    return jsonify({
                        'error': 'Authentication required',
                        'message': 'Please provide a valid JWT token'
                    }), 401
                
                if self.fresh and not get_jwt().get('fresh', False):
                    logger.warning("Fresh token required but refresh token provided")
                    return jsonify({
                        'error': 'Fresh token required',
                        'message': 'Please login again to access this resource'
                    }), 401
                
                # Fetch full user object from database
                if current_user:
                    from ..services.database_service import db_service
                    try:
                        # Use get_user method to fetch full user object
                        user = db_service.get_user(current_user)
                        
                        if not user:
                            logger.warning(f"User not found for ID: {current_user}")
                            return jsonify({'error': 'User not found'}), 401
                        
                        # Store user object in Flask's g object for access in routes
                        g.current_user = user
                    except Exception as e:
                        logger.error(f"Error fetching user from database: {e}")
                        return jsonify({'error': 'Database error'}), 500
                else:
                    g.current_user = None
                
                return func(*args, **kwargs)
                
            except NoAuthorizationError:
                if self.optional:
                    g.current_user = None
                    return func(*args, **kwargs)
                logger.warning("No authorization header found")
                return jsonify({
                    'error': 'Authorization header missing',
                    'message': 'Please provide Authorization header with Bearer token'
                }), 401
                
            except InvalidHeaderError as e:
                logger.warning(f"Invalid authorization header: {e}")
                return jsonify({
                    'error': 'Invalid authorization header',
                    'message': 'Authorization header must be in format: Bearer <token>'
                }), 401
                
            except RevokedTokenError:
                logger.warning("Revoked token used")
                return jsonify({
                    'error': 'Token revoked',
                    'message': 'This token has been revoked'
                }), 401
                
            except WrongTokenError:
                logger.warning("Wrong token type used")
                return jsonify({
                    'error': 'Wrong token type',
                    'message': 'Invalid token type for this endpoint'
                }), 401
                
            except JWTDecodeError as e:
                logger.warning(f"JWT decode error: {e}")
                return jsonify({
                    'error': 'Invalid token',
                    'message': 'Token is malformed or expired'
                }), 401
                
            except Exception as e:
                logger.error(f"Unexpected authentication error: {e}")
                return jsonify({
                    'error': 'Authentication error',
                    'message': 'An unexpected error occurred during authentication'
                }), 500
         
        return wrapper


def require_auth(optional: bool = False, fresh: bool = False, refresh: bool = False, 
                locations: Optional[List[str]] = None) -> Callable:
    """JWT authentication requirement decorator
    
    Args:
        optional: Allow access without token
        fresh: Require fresh token (recently authenticated)
        refresh: Require refresh token
        locations: Where to look for JWT (headers, cookies, etc.)
        
    Returns:
        Decorator function
    """
    return AuthDecorator(optional=optional, fresh=fresh, refresh=refresh, locations=locations)


def require_roles(roles: List[str]) -> Callable:
    """Role requirement decorator with actual validation
    
    Args:
        roles: List of required roles
        
    Returns:
        Decorator function
    """
    def roles_decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                # First verify JWT
                verify_jwt_in_request()
                
                # Get user claims from JWT
                claims = get_jwt()
                user_roles = claims.get('roles', [])
                user_id = get_jwt_identity()
                
                # Check if user has any of the required roles
                if not any(role in user_roles for role in roles):
                    logger.warning(f"Insufficient permissions for user {user_id} on {request.endpoint}. Required: {roles}, Has: {user_roles}")
                    return jsonify({
                        'error': 'Insufficient permissions',
                        'message': f'This endpoint requires one of the following roles: {", ".join(roles)}'
                    }), 403
                
                return func(*args, **kwargs)
            except NoAuthorizationError:
                logger.warning(f"Missing authorization for role-protected {request.endpoint} from {request.remote_addr}")
                return jsonify({
                    'error': 'Missing authorization',
                    'message': 'Authorization token is required'
                }), 401
            except (InvalidHeaderError, JWTDecodeError, RevokedTokenError, WrongTokenError) as e:
                logger.warning(f"Invalid token for role-protected {request.endpoint}: {str(e)}")
                return jsonify({
                    'error': 'Invalid token',
                    'message': 'The authorization token is invalid or expired'
                }), 401
            except Exception as e:
                logger.error(f"Role authorization error for {request.endpoint}: {str(e)}")
                return jsonify({
                    'error': 'Authorization failed',
                    'message': 'An error occurred during role verification'
                }), 500
        return wrapper
    return roles_decorator


# Convenience decorators for common use cases
def require_fresh_auth(func: Callable) -> Callable:
    """Require fresh JWT token (recently authenticated)"""
    return require_auth(fresh=True)(func)


def require_refresh_token(func: Callable) -> Callable:
    """Require refresh token"""
    return require_auth(refresh=True)(func)


def optional_auth(func: Callable) -> Callable:
    """Optional authentication - allows both authenticated and anonymous access"""
    return require_auth(optional=True)(func)


def admin_required(func: Callable) -> Callable:
    """Require admin role"""
    return require_roles(['admin'])(func)


def user_required(func: Callable) -> Callable:
    """Require user role (basic authenticated user)"""
    return require_roles(['user', 'admin'])(func)


def moderator_required(func: Callable) -> Callable:
    """Require moderator role"""
    return require_roles(['moderator', 'admin'])(func)