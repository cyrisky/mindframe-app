"""Authentication decorators module - separate from main decorators to avoid Flask conflicts"""

import functools
from typing import Callable, Optional, List
from flask import jsonify, g
from flask_jwt_extended import (
    verify_jwt_in_request, get_jwt_identity, get_jwt
)
from flask_jwt_extended.exceptions import (
    JWTExtendedException, NoAuthorizationError
)
import logging

logger = logging.getLogger(__name__)


def jwt_required_decorator(optional: bool = False, fresh: bool = False, refresh: bool = False, 
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
    def auth_decorator(func):
        def authenticated_func(*args, **kwargs):
            try:
                verify_jwt_in_request(
                    optional=optional,
                    fresh=fresh,
                    refresh=refresh,
                    locations=locations
                )
                current_user = get_jwt_identity()
                
                if not optional and not current_user:
                    logger.warning("Authentication required but no token provided")
                    return jsonify({
                        'success': False,
                        'error': 'Authentication required',
                        'code': 'AUTH_REQUIRED'
                    }), 401
                
                if fresh and not get_jwt().get('fresh', False):
                    logger.warning("Fresh token required but refresh token provided")
                    return jsonify({
                        'success': False,
                        'error': 'Fresh token required',
                        'code': 'FRESH_TOKEN_REQUIRED'
                    }), 401
                
                g.current_user = current_user
                g.current_user_id = current_user
                
                return func(*args, **kwargs)
                
            except NoAuthorizationError:
                if optional:
                    g.current_user = None
                    return func(*args, **kwargs)
                
                logger.warning("No authorization header found")
                return jsonify({
                    'success': False,
                    'error': 'Authorization header is expected',
                    'code': 'MISSING_AUTH_HEADER'
                }), 401
                
            except JWTExtendedException as e:
                logger.warning(f"JWT validation failed: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'code': 'INVALID_TOKEN'
                }), 401
                
            except Exception as e:
                logger.error(f"Unexpected error during authentication: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'An unexpected error occurred during authentication',
                    'code': 'AUTH_ERROR'
                }), 500
        
        # Copy function metadata to preserve original function identity
        authenticated_func.__name__ = func.__name__
        authenticated_func.__doc__ = func.__doc__
        authenticated_func.__module__ = func.__module__
        authenticated_func.__qualname__ = func.__qualname__
        
        return authenticated_func
    return auth_decorator


# Alias for backward compatibility
require_auth = jwt_required_decorator