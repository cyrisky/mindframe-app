#!/usr/bin/env python3
"""
Centralized Exception Classes for Mindframe Backend

This module defines custom exception classes and error handling utilities
for consistent error management across the application.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
import traceback
from datetime import datetime


class ErrorCode(Enum):
    """Standardized error codes for the application"""
    
    # Authentication & Authorization
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Validation Errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    INVALID_VALUE = "INVALID_VALUE"
    
    # Resource Errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    RESOURCE_LOCKED = "RESOURCE_LOCKED"
    
    # Database Errors
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_TIMEOUT = "DATABASE_TIMEOUT"
    DUPLICATE_KEY_ERROR = "DUPLICATE_KEY_ERROR"
    
    # External Service Errors
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    EXTERNAL_SERVICE_TIMEOUT = "EXTERNAL_SERVICE_TIMEOUT"
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"
    
    # File & Storage Errors
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    STORAGE_ERROR = "STORAGE_ERROR"
    
    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Business Logic Errors
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    INVALID_STATE = "INVALID_STATE"
    
    # System Errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"


class BaseAPIException(Exception):
    """Base exception class for all API exceptions"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.field = field
        self.user_message = user_message or message
        self.timestamp = datetime.utcnow().isoformat() + 'Z'
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response"""
        result = {
            'success': False,
            'error': self.error_code.value,
            'message': self.user_message,
            'timestamp': self.timestamp
        }
        
        if self.field:
            result['field'] = self.field
            
        if self.details:
            result['details'] = self.details
            
        return result


class ValidationError(BaseAPIException):
    """Exception for validation errors"""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=422,
            details=details,
            field=field,
            user_message=user_message
        )


class AuthenticationError(BaseAPIException):
    """Exception for authentication errors"""
    
    def __init__(
        self,
        message: str = "Authentication required",
        error_code: ErrorCode = ErrorCode.AUTHENTICATION_REQUIRED,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401,
            details=details,
            user_message="Please log in to access this resource"
        )


class AuthorizationError(BaseAPIException):
    """Exception for authorization errors"""
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            status_code=403,
            details=details,
            user_message="You don't have permission to access this resource"
        )


class ResourceNotFoundError(BaseAPIException):
    """Exception for resource not found errors"""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if resource_id:
            message = f"{resource_type} with ID '{resource_id}' not found"
            user_message = f"The requested {resource_type.lower()} could not be found"
        else:
            message = f"{resource_type} not found"
            user_message = f"The requested {resource_type.lower()} could not be found"
            
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=404,
            details=details or {'resource_type': resource_type, 'resource_id': resource_id},
            user_message=user_message
        )


class ResourceConflictError(BaseAPIException):
    """Exception for resource conflict errors"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_CONFLICT,
            status_code=409,
            details=details,
            user_message=user_message or "A conflict occurred with the requested resource"
        )


class DatabaseError(BaseAPIException):
    """Exception for database errors"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.DATABASE_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        if original_error:
            details = details or {}
            details['original_error'] = str(original_error)
            
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            details=details,
            user_message="A database error occurred. Please try again later."
        )


class ExternalServiceError(BaseAPIException):
    """Exception for external service errors"""
    
    def __init__(
        self,
        service_name: str,
        message: str,
        error_code: ErrorCode = ErrorCode.EXTERNAL_SERVICE_ERROR,
        status_code: int = 502,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details['service_name'] = service_name
        
        super().__init__(
            message=f"{service_name}: {message}",
            error_code=error_code,
            status_code=status_code,
            details=details,
            user_message=f"An error occurred with {service_name}. Please try again later."
        )


class RateLimitError(BaseAPIException):
    """Exception for rate limiting errors"""
    
    def __init__(
        self,
        limit: int,
        window: str,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Rate limit exceeded: {limit} requests per {window}"
        
        details = details or {}
        details.update({
            'limit': limit,
            'window': window,
            'retry_after': retry_after
        })
        
        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details=details,
            user_message="Too many requests. Please wait before trying again."
        )


class BusinessRuleError(BaseAPIException):
    """Exception for business rule violations"""
    
    def __init__(
        self,
        rule: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        details = details or {}
        details['rule'] = rule
        
        super().__init__(
            message=f"Business rule violation ({rule}): {message}",
            error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
            status_code=422,
            details=details,
            user_message=user_message or message
        )


class FileError(BaseAPIException):
    """Exception for file-related errors"""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        filename: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None
    ):
        details = details or {}
        if filename:
            details['filename'] = filename
            
        status_code = 400 if error_code in [
            ErrorCode.FILE_TOO_LARGE,
            ErrorCode.INVALID_FILE_TYPE
        ] else 404 if error_code == ErrorCode.FILE_NOT_FOUND else 500
        
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details,
            user_message=user_message or message
        )


class ConfigurationError(BaseAPIException):
    """Exception for configuration errors"""
    
    def __init__(
        self,
        setting: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details['setting'] = setting
        
        super().__init__(
            message=f"Configuration error ({setting}): {message}",
            error_code=ErrorCode.CONFIGURATION_ERROR,
            status_code=500,
            details=details,
            user_message="A configuration error occurred. Please contact support."
        )


class MultipleValidationErrors(BaseAPIException):
    """Exception for multiple validation errors"""
    
    def __init__(self, errors: List[Dict[str, Any]]):
        self.errors = errors
        
        # Create a summary message
        error_count = len(errors)
        message = f"Validation failed with {error_count} error{'s' if error_count != 1 else ''}"
        
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=422,
            details={'errors': errors},
            user_message="Please correct the validation errors and try again"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Override to include individual errors"""
        result = super().to_dict()
        result['errors'] = self.errors
        return result


class ErrorContext:
    """Context manager for capturing and enriching errors"""
    
    def __init__(
        self,
        operation: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ):
        self.operation = operation
        self.user_id = user_id
        self.request_id = request_id
        self.additional_context = additional_context or {}
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and issubclass(exc_type, BaseAPIException):
            # Enrich the exception with context
            exc_val.details = exc_val.details or {}
            exc_val.details.update({
                'operation': self.operation,
                'user_id': self.user_id,
                'request_id': self.request_id,
                **self.additional_context
            })
        return False  # Don't suppress the exception


def create_error_response(
    error: Exception,
    include_traceback: bool = False,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a standardized error response from any exception"""
    
    if isinstance(error, BaseAPIException):
        response = error.to_dict()
    else:
        # Handle unexpected exceptions
        response = {
            'success': False,
            'error': ErrorCode.INTERNAL_ERROR.value,
            'message': 'An unexpected error occurred',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        if include_traceback:
            response['details'] = {
                'original_error': str(error),
                'error_type': type(error).__name__,
                'traceback': traceback.format_exc()
            }
    
    if request_id:
        response['request_id'] = request_id
        
    return response


def get_http_status_code(error: Exception) -> int:
    """Get the appropriate HTTP status code for an exception"""
    
    if isinstance(error, BaseAPIException):
        return error.status_code
    
    # Default status codes for common exceptions
    if isinstance(error, (ValueError, TypeError)):
        return 400
    elif isinstance(error, PermissionError):
        return 403
    elif isinstance(error, FileNotFoundError):
        return 404
    elif isinstance(error, TimeoutError):
        return 408
    else:
        return 500