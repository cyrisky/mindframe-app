#!/usr/bin/env python3
"""
Rate Limiting Middleware

This module provides rate limiting functionality using Flask-Limiter with Redis backend.
It includes configurable rate limits, IP whitelisting, and comprehensive error handling.
"""

import logging
import os
from functools import wraps
from typing import Dict, List, Optional, Callable, Any

from flask import Flask, request, current_app, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded

from src.utils.exceptions import RateLimitError
from src.utils.error_handler import create_error_response
from config.rate_limiting import get_rate_limiting_config





class EnhancedRateLimiter:
    """Enhanced rate limiter with advanced features"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.limiter: Optional[Limiter] = None
        self.logger = logging.getLogger(__name__)
        self.config = get_rate_limiting_config()
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask) -> None:
        """Initialize the rate limiter with Flask app"""
        self.app = app
        
        # Check if rate limiting is enabled
        if not self.config.ENABLED:
            self.logger.info("Rate limiting is disabled")
            return
        
        # Configure Flask-Limiter
        self.limiter = Limiter(
            key_func=self._get_rate_limit_key,
            app=app,
            storage_uri=self.config.REDIS_URL,
            strategy=self.config.STRATEGY,
            default_limits=self.config.GLOBAL_DEFAULT_LIMITS,
            application_limits=self.config.APPLICATION_LIMITS,
            headers_enabled=self.config.ENABLE_HEADERS,
            header_name_mapping=self.config.HEADER_MAPPING,
            swallow_errors=False  # We want to handle errors ourselves
        )
        
        # Register request filters
        self._register_request_filters()
        
        # Register error handlers
        self._register_error_handlers()
        
        # Add request hooks for logging
        self._register_request_hooks()
        
        self.logger.info(
            "Rate limiter initialized",
            extra={
                'component': 'rate_limiter',
                'redis_url': self.config.REDIS_URL,
                'strategy': self.config.STRATEGY,
                'enabled': self.config.ENABLED,
                'default_limits': self.config.GLOBAL_DEFAULT_LIMITS
            }
        )
    
    def _get_rate_limit_key(self) -> str:
        """Generate rate limit key based on user context"""
        # Try to get authenticated user ID first
        user_id = getattr(g, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        return get_remote_address()
    
    def _register_request_filters(self) -> None:
        """Register request filters to bypass rate limiting"""
        
        @self.limiter.request_filter
        def whitelist_ips():
            """Skip rate limiting for whitelisted IPs"""
            remote_addr = request.remote_addr
            if self.config.is_ip_whitelisted(remote_addr):
                return True
            
            return False
        
        @self.limiter.request_filter
        def internal_requests():
            """Skip rate limiting for internal requests"""
            return request.headers.get('X-Internal-Request') == 'true'
        
        @self.limiter.request_filter
        def admin_bypass():
            """Skip rate limiting for admin users"""
            user_role = getattr(g, 'user_role', None)
            return user_role and self.config.is_role_exempt(user_role)
    
    def _register_error_handlers(self) -> None:
        """Register custom error handlers for rate limit violations"""
        
        @self.app.errorhandler(RateLimitExceeded)
        def handle_rate_limit_exceeded(error):
            """Handle rate limit exceeded errors"""
            
            # Log the violation
            if self.config.LOG_VIOLATIONS:
                self.logger.log(
                    getattr(logging, self.config.LOG_LEVEL),
                    "Rate limit exceeded",
                    extra={
                        'component': 'rate_limiter',
                        'limit': str(error.limit),
                        'key': self._get_rate_limit_key(),
                        'endpoint': request.endpoint,
                        'method': request.method,
                        'path': request.path,
                        'user_agent': request.headers.get('User-Agent'),
                        'remote_addr': request.remote_addr,
                        'retry_after': error.retry_after
                    }
                )
            
            # Create standardized error response
            rate_limit_error = RateLimitError(
                f"Rate limit exceeded: {error.limit}",
                limit=str(error.limit),
                retry_after=error.retry_after
            )
            
            return create_error_response(rate_limit_error), 429
    
    def _register_request_hooks(self) -> None:
        """Register request hooks for monitoring"""
        
        @self.app.before_request
        def log_rate_limit_info():
            """Log rate limit information for monitoring"""
            # Store rate limit info in g for potential use in responses
            g.rate_limit_key = self._get_rate_limit_key()
    
    def limit(self, limit_string: str, **kwargs) -> Callable:
        """Decorator to apply rate limits to routes"""
        if not self.config.ENABLED:
            # Return a no-op decorator if rate limiting is disabled
            def no_op_decorator(func):
                return func
            return no_op_decorator
        
        return self.limiter.limit(limit_string, **kwargs)
    
    def shared_limit(self, limit_string: str, scope: str, **kwargs) -> Callable:
        """Create a shared rate limit across multiple routes"""
        if not self.config.ENABLED:
            def no_op_decorator(func):
                return func
            return no_op_decorator
        
        return self.limiter.shared_limit(limit_string, scope=scope, **kwargs)
    
    def exempt(self, route_or_blueprint, **kwargs) -> None:
        """Exempt a route or blueprint from rate limiting"""
        if self.limiter:
            self.limiter.exempt(route_or_blueprint, **kwargs)
    
    def get_current_limits(self, key: Optional[str] = None) -> Dict[str, Any]:
        """Get current rate limit status for a key"""
        if not self.limiter or not self.config.ENABLED:
            return {}
        
        if key is None:
            key = self._get_rate_limit_key()
        
        try:
            # This would require accessing internal limiter state
            # Implementation depends on Flask-Limiter version
            return {
                'key': key,
                'enabled': True,
                'strategy': self.config.STRATEGY
            }
        except Exception as e:
            self.logger.error(f"Error getting rate limit status: {e}")
            return {}


# Predefined rate limit decorators for common use cases
class RateLimitDecorators:
    """Predefined rate limit decorators for common scenarios"""
    
    def __init__(self, limiter: EnhancedRateLimiter):
        self.limiter = limiter
    
    @property
    def api_standard(self) -> Callable:
        """Standard API rate limit"""
        config = get_rate_limiting_config()
        limit = config.get_endpoint_limit('api', 'standard') or '100/hour'
        return self.limiter.limit(limit)
    
    @property
    def api_strict(self) -> Callable:
        """Strict API rate limit"""
        config = get_rate_limiting_config()
        limit = config.get_endpoint_limit('api', 'strict') or '50/hour'
        return self.limiter.limit(limit)
    
    @property
    def auth_endpoints(self) -> Callable:
        """Authentication endpoints"""
        config = get_rate_limiting_config()
        limit = config.get_endpoint_limit('auth', 'login') or '10/minute'
        return self.limiter.limit(limit)
    
    @property
    def upload_endpoints(self) -> Callable:
        """File upload endpoints"""
        config = get_rate_limiting_config()
        limit = config.get_endpoint_limit('files', 'upload') or '5/minute'
        return self.limiter.limit(limit)
    
    @property
    def heavy_computation(self) -> Callable:
        """Heavy computation endpoints"""
        config = get_rate_limiting_config()
        limit = config.get_endpoint_limit('computation', 'report_generation') or '20/hour'
        return self.limiter.limit(limit)
    
    @property
    def public_endpoints(self) -> Callable:
        """Public endpoints"""
        config = get_rate_limiting_config()
        limit = config.get_endpoint_limit('api', 'public') or '1000/hour'
        return self.limiter.limit(limit)
    
    def custom_limit(self, limit_string: str, **kwargs) -> Callable:
        """Custom rate limit with additional options"""
        return self.limiter.limit(limit_string, **kwargs)
    
    def user_based_limit(self, limit_string: str) -> Callable:
        """Rate limit based on authenticated user"""
        return self.limiter.limit(
            limit_string,
            key_func=lambda: getattr(g, 'user_id', get_remote_address())
        )
    
    def conditional_limit(self, limit_string: str, condition: Callable[[], bool]) -> Callable:
        """Apply rate limit only when condition is met"""
        return self.limiter.limit(
            limit_string,
            exempt_when=lambda: not condition()
        )


def setup_rate_limiting(app: Flask) -> tuple[EnhancedRateLimiter, RateLimitDecorators]:
    """Setup rate limiting for the Flask application"""
    
    # Initialize rate limiter
    rate_limiter = EnhancedRateLimiter(app)
    
    # Create decorator helpers
    decorators = RateLimitDecorators(rate_limiter)
    
    # Store in app context for access in other modules
    app.extensions = getattr(app, 'extensions', {})
    app.extensions['rate_limiter'] = rate_limiter
    app.extensions['rate_limit_decorators'] = decorators
    
    return rate_limiter, decorators


def get_rate_limiter(app: Optional[Flask] = None) -> Optional[EnhancedRateLimiter]:
    """Get the rate limiter instance from app context"""
    if app is None:
        from flask import current_app
        app = current_app
    
    return app.extensions.get('rate_limiter')


def get_rate_limit_decorators(app: Optional[Flask] = None) -> Optional[RateLimitDecorators]:
    """Get the rate limit decorators from app context"""
    if app is None:
        from flask import current_app
        app = current_app
    
    return app.extensions.get('rate_limit_decorators')


# Utility functions for manual rate limit checking
def check_rate_limit(key: str, limit: str) -> bool:
    """Manually check if a rate limit would be exceeded"""
    try:
        limiter = get_rate_limiter()
        if not limiter or not limiter.config.ENABLED:
            return True
        
        # This would require implementing manual limit checking
        # For now, return True (allowed)
        return True
    except Exception:
        return True


def get_rate_limit_status(key: Optional[str] = None) -> Dict[str, Any]:
    """Get current rate limit status"""
    try:
        limiter = get_rate_limiter()
        if not limiter:
            return {'enabled': False}
        
        return limiter.get_current_limits(key)
    except Exception:
        return {'enabled': False, 'error': True}