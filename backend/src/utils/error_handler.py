#!/usr/bin/env python3
"""
Centralized Error Handler for Mindframe Backend

This module provides Flask error handlers and utilities for consistent
error handling and response formatting across the application.
"""

from flask import Flask, request, jsonify, g
from werkzeug.exceptions import HTTPException
from pymongo.errors import (
    ConnectionFailure, 
    ServerSelectionTimeoutError,
    DuplicateKeyError,
    OperationFailure
)
from bson.errors import InvalidId
from typing import Tuple, Dict, Any, Optional
import logging
import uuid
from datetime import datetime

from .exceptions import (
    BaseAPIException,
    ErrorCode,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    DatabaseError,
    ExternalServiceError,
    RateLimitError,
    create_error_response,
    get_http_status_code
)
from .logging_utils import LoggingUtils


class ErrorHandler:
    """Centralized error handler for Flask applications"""
    
    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.logger = LoggingUtils.get_logger('error_handler')
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize error handling for Flask app"""
        self.app = app
        
        # Register error handlers
        self._register_error_handlers(app)
        
        # Add before_request handler to generate request IDs
        app.before_request(self._before_request)
        
        # Add after_request handler for error logging
        app.after_request(self._after_request)
    
    def _before_request(self):
        """Generate request ID for tracking"""
        g.request_id = str(uuid.uuid4())
        g.request_start_time = datetime.utcnow()
    
    def _after_request(self, response):
        """Log request completion"""
        # Only log errors (4xx, 5xx status codes)
        if response.status_code >= 400:
            duration = None
            if hasattr(g, 'request_start_time'):
                duration = (datetime.utcnow() - g.request_start_time).total_seconds() * 1000
            
            self.logger.warning("Request completed with error", extra={
                'request_id': getattr(g, 'request_id', 'unknown'),
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': round(duration, 2) if duration else None,
                'user_agent': request.headers.get('User-Agent'),
                'ip_address': request.remote_addr
            })
        
        return response
    
    def _register_error_handlers(self, app: Flask):
        """Register all error handlers with the Flask app"""
        
        # Custom API exceptions
        app.register_error_handler(BaseAPIException, self._handle_api_exception)
        
        # HTTP exceptions
        app.register_error_handler(400, self._handle_bad_request)
        app.register_error_handler(401, self._handle_unauthorized)
        app.register_error_handler(403, self._handle_forbidden)
        app.register_error_handler(404, self._handle_not_found)
        app.register_error_handler(405, self._handle_method_not_allowed)
        app.register_error_handler(409, self._handle_conflict)
        app.register_error_handler(422, self._handle_unprocessable_entity)
        app.register_error_handler(429, self._handle_rate_limit_exceeded)
        app.register_error_handler(500, self._handle_internal_error)
        app.register_error_handler(502, self._handle_bad_gateway)
        app.register_error_handler(503, self._handle_service_unavailable)
        
        # Generic HTTP exception handler
        app.register_error_handler(HTTPException, self._handle_http_exception)
        
        # Database exceptions
        app.register_error_handler(ConnectionFailure, self._handle_database_connection_error)
        app.register_error_handler(ServerSelectionTimeoutError, self._handle_database_timeout)
        app.register_error_handler(DuplicateKeyError, self._handle_duplicate_key_error)
        app.register_error_handler(OperationFailure, self._handle_database_operation_error)
        app.register_error_handler(InvalidId, self._handle_invalid_object_id)
        
        # Generic exception handler (catch-all)
        app.register_error_handler(Exception, self._handle_generic_exception)
    
    def _handle_api_exception(self, error: BaseAPIException) -> Tuple[Dict[str, Any], int]:
        """Handle custom API exceptions"""
        request_id = getattr(g, 'request_id', None)
        
        # Log the error with context
        self.logger.error("API exception occurred", extra={
            'request_id': request_id,
            'error_code': error.error_code.value,
            'error_message': error.message,
            'status_code': error.status_code,
            'method': request.method,
            'path': request.path,
            'user_id': getattr(g, 'user_id', None),
            'error_details': error.details
        })
        
        response = error.to_dict()
        if request_id:
            response['request_id'] = request_id
            
        return jsonify(response), error.status_code
    
    def _handle_bad_request(self, error) -> Tuple[Dict[str, Any], int]:
        """Handle 400 Bad Request errors"""
        return self._create_error_response(
            ErrorCode.INVALID_REQUEST,
            "The request was invalid or malformed",
            400,
            {'original_error': str(error)}
        )
    
    def _handle_unauthorized(self, error) -> Tuple[Dict[str, Any], int]:
        """Handle 401 Unauthorized errors"""
        return self._create_error_response(
            ErrorCode.AUTHENTICATION_REQUIRED,
            "Authentication is required to access this resource",
            401
        )
    
    def _handle_forbidden(self, error) -> Tuple[Dict[str, Any], int]:
        """Handle 403 Forbidden errors"""
        return self._create_error_response(
            ErrorCode.INSUFFICIENT_PERMISSIONS,
            "You don't have permission to access this resource",
            403
        )
    
    def _handle_not_found(self, error) -> Tuple[Dict[str, Any], int]:
        """Handle 404 Not Found errors"""
        return self._create_error_response(
            ErrorCode.RESOURCE_NOT_FOUND,
            "The requested resource was not found",
            404,
            {
                'path': request.path,
                'method': request.method,
                'available_endpoints': self._get_available_endpoints()
            }
        )
    
    def _handle_method_not_allowed(self, error) -> Tuple[Dict[str, Any], int]:
        """Handle 405 Method Not Allowed errors"""
        allowed_methods = getattr(error, 'valid_methods', [])
        return self._create_error_response(
            ErrorCode.INVALID_REQUEST,
            f"Method {request.method} not allowed for this endpoint",
            405,
            {
                'method': request.method,
                'path': request.path,
                'allowed_methods': list(allowed_methods) if allowed_methods else []
            }
        )
    
    def _handle_conflict(self, error) -> Tuple[Dict[str, Any], int]:
        """Handle 409 Conflict errors"""
        return self._create_error_response(
            ErrorCode.RESOURCE_CONFLICT,
            "A conflict occurred with the requested resource",
            409
        )
    
    def _handle_unprocessable_entity(self, error) -> Tuple[Dict[str, Any], int]:
        """Handle 422 Unprocessable Entity errors"""
        return self._create_error_response(
            ErrorCode.VALIDATION_ERROR,
            "The request data failed validation",
            422
        )
    
    def _handle_rate_limit_exceeded(self, error) -> Tuple[Dict[str, Any], int]:
        """Handle 429 Rate Limit Exceeded errors"""
        retry_after = getattr(error, 'retry_after', None)
        details = {'retry_after': retry_after} if retry_after else {}
        
        return self._create_error_response(
            ErrorCode.RATE_LIMIT_EXCEEDED,
            "Rate limit exceeded. Please try again later.",
            429,
            details
        )
    
    def _handle_internal_error(self, error) -> Tuple[Dict[str, Any], int]:
        """Handle 500 Internal Server Error"""
        return self._create_error_response(
            ErrorCode.INTERNAL_ERROR,
            "An internal server error occurred",
            500
        )
    
    def _handle_bad_gateway(self, error) -> Tuple[Dict[str, Any], int]:
        """Handle 502 Bad Gateway errors"""
        return self._create_error_response(
            ErrorCode.EXTERNAL_SERVICE_ERROR,
            "An external service is currently unavailable",
            502
        )
    
    def _handle_service_unavailable(self, error) -> Tuple[Dict[str, Any], int]:
        """Handle 503 Service Unavailable errors"""
        return self._create_error_response(
            ErrorCode.SERVICE_UNAVAILABLE,
            "The service is temporarily unavailable",
            503
        )
    
    def _handle_http_exception(self, error: HTTPException) -> Tuple[Dict[str, Any], int]:
        """Handle generic HTTP exceptions"""
        # Map common HTTP status codes to error codes
        error_code_map = {
            400: ErrorCode.INVALID_REQUEST,
            401: ErrorCode.AUTHENTICATION_REQUIRED,
            403: ErrorCode.INSUFFICIENT_PERMISSIONS,
            404: ErrorCode.RESOURCE_NOT_FOUND,
            409: ErrorCode.RESOURCE_CONFLICT,
            422: ErrorCode.VALIDATION_ERROR,
            429: ErrorCode.RATE_LIMIT_EXCEEDED,
            500: ErrorCode.INTERNAL_ERROR,
            502: ErrorCode.EXTERNAL_SERVICE_ERROR,
            503: ErrorCode.SERVICE_UNAVAILABLE
        }
        
        error_code = error_code_map.get(error.code, ErrorCode.INTERNAL_ERROR)
        message = error.description or "An error occurred"
        
        return self._create_error_response(
            error_code,
            message,
            error.code,
            {'http_exception': error.name}
        )
    
    def _handle_database_connection_error(self, error: ConnectionFailure) -> Tuple[Dict[str, Any], int]:
        """Handle database connection errors"""
        self.logger.error("Database connection failed", extra={
            'error': str(error),
            'error_type': 'ConnectionFailure',
            'request_id': getattr(g, 'request_id', None)
        })
        
        return self._create_error_response(
            ErrorCode.DATABASE_CONNECTION_ERROR,
            "Database connection failed",
            503,
            {'database_error': str(error)}
        )
    
    def _handle_database_timeout(self, error: ServerSelectionTimeoutError) -> Tuple[Dict[str, Any], int]:
        """Handle database timeout errors"""
        self.logger.error("Database timeout", extra={
            'error': str(error),
            'error_type': 'ServerSelectionTimeoutError',
            'request_id': getattr(g, 'request_id', None)
        })
        
        return self._create_error_response(
            ErrorCode.DATABASE_TIMEOUT,
            "Database operation timed out",
            503,
            {'timeout_error': str(error)}
        )
    
    def _handle_duplicate_key_error(self, error: DuplicateKeyError) -> Tuple[Dict[str, Any], int]:
        """Handle duplicate key errors"""
        # Extract field information from the error if possible
        error_details = {'duplicate_key_error': str(error)}
        
        return self._create_error_response(
            ErrorCode.DUPLICATE_KEY_ERROR,
            "A resource with this identifier already exists",
            409,
            error_details
        )
    
    def _handle_database_operation_error(self, error: OperationFailure) -> Tuple[Dict[str, Any], int]:
        """Handle database operation errors"""
        self.logger.error("Database operation failed", extra={
            'error': str(error),
            'error_type': 'OperationFailure',
            'request_id': getattr(g, 'request_id', None)
        })
        
        return self._create_error_response(
            ErrorCode.DATABASE_ERROR,
            "Database operation failed",
            500,
            {'operation_error': str(error)}
        )
    
    def _handle_invalid_object_id(self, error: InvalidId) -> Tuple[Dict[str, Any], int]:
        """Handle invalid MongoDB ObjectId errors"""
        return self._create_error_response(
            ErrorCode.INVALID_FORMAT,
            "Invalid ID format provided",
            400,
            {'invalid_id': str(error)}
        )
    
    def _handle_generic_exception(self, error: Exception) -> Tuple[Dict[str, Any], int]:
        """Handle any unhandled exceptions"""
        request_id = getattr(g, 'request_id', None)
        
        # Log the full exception with traceback
        self.logger.error("Unhandled exception occurred", extra={
            'request_id': request_id,
            'error': str(error),
            'error_type': type(error).__name__,
            'method': request.method,
            'path': request.path,
            'user_id': getattr(g, 'user_id', None)
        }, exc_info=True)
        
        # Don't expose internal error details in production
        include_details = self.app.config.get('DEBUG', False)
        
        response = create_error_response(
            error,
            include_traceback=include_details,
            request_id=request_id
        )
        
        status_code = get_http_status_code(error)
        
        return jsonify(response), status_code
    
    def _create_error_response(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int,
        details: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], int]:
        """Create a standardized error response"""
        request_id = getattr(g, 'request_id', None)
        
        # Log the error
        self.logger.error(f"HTTP {status_code} error", extra={
            'request_id': request_id,
            'error_code': error_code.value,
            'status_code': status_code,
            'method': request.method,
            'path': request.path,
            'user_id': getattr(g, 'user_id', None),
            'error_details': details
        })
        
        response = {
            'success': False,
            'error': error_code.value,
            'message': message,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        if request_id:
            response['request_id'] = request_id
            
        if details:
            response['details'] = details
            
        return jsonify(response), status_code
    
    def _get_available_endpoints(self) -> list:
        """Get list of available endpoints for 404 responses"""
        if not self.app:
            return []
            
        endpoints = []
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint != 'static':  # Exclude static file endpoints
                methods = [m for m in rule.methods if m not in ['HEAD', 'OPTIONS']]
                if methods:
                    endpoints.append({
                        'path': str(rule),
                        'methods': methods
                    })
        
        return endpoints[:10]  # Limit to first 10 endpoints


def setup_error_handling(app: Flask) -> ErrorHandler:
    """Setup centralized error handling for a Flask app"""
    error_handler = ErrorHandler(app)
    
    # Add error handler to app context for access in other modules
    app.error_handler = error_handler
    
    return error_handler


# Utility functions for raising common exceptions
def raise_validation_error(
    message: str,
    field: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Raise a validation error"""
    raise ValidationError(message, field=field, details=details)


def raise_not_found(resource_type: str, resource_id: Optional[str] = None):
    """Raise a resource not found error"""
    raise ResourceNotFoundError(resource_type, resource_id)


def raise_authentication_error(message: str = "Authentication required"):
    """Raise an authentication error"""
    raise AuthenticationError(message)


def raise_authorization_error(message: str = "Insufficient permissions"):
    """Raise an authorization error"""
    raise AuthorizationError(message)


def raise_database_error(message: str, original_error: Optional[Exception] = None):
    """Raise a database error"""
    raise DatabaseError(message, original_error=original_error)