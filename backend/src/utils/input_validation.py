"""Comprehensive input validation framework for API endpoints"""

import functools
import logging
from typing import Dict, Any, List, Optional, Callable, Union, Type
from flask import request, jsonify
from pydantic import BaseModel, ValidationError
from werkzeug.datastructures import FileStorage

from .validation_utils import ValidationUtils
from .logging_utils import LoggingUtils

logger = LoggingUtils.get_logger(__name__)


class ValidationConfig:
    """Configuration for validation rules"""
    
    def __init__(self):
        self.max_content_length = 16 * 1024 * 1024  # 16MB
        self.allowed_file_types = {
            'image': ['jpg', 'jpeg', 'png', 'gif', 'webp'],
            'document': ['pdf', 'doc', 'docx', 'txt'],
            'data': ['json', 'csv', 'xlsx']
        }
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_string_length = 10000
        self.max_array_length = 1000
        self.max_nested_depth = 10


class ValidationError(Exception):
    """Custom validation error"""
    
    def __init__(self, message: str, field: str = None, code: str = None):
        self.message = message
        self.field = field
        self.code = code or 'VALIDATION_ERROR'
        super().__init__(self.message)


class InputValidator:
    """Main input validation class"""
    
    def __init__(self, config: ValidationConfig = None):
        self.config = config or ValidationConfig()
    
    def validate_request_size(self, request_obj) -> None:
        """Validate request content length"""
        if hasattr(request_obj, 'content_length') and request_obj.content_length:
            if request_obj.content_length > self.config.max_content_length:
                raise ValidationError(
                    f"Request too large. Maximum size: {self.config.max_content_length} bytes",
                    code='REQUEST_TOO_LARGE'
                )
    
    def validate_content_type(self, request_obj, allowed_types: List[str]) -> None:
        """Validate request content type"""
        content_type = request_obj.content_type
        if content_type and content_type.split(';')[0] not in allowed_types:
            raise ValidationError(
                f"Invalid content type. Allowed: {', '.join(allowed_types)}",
                code='INVALID_CONTENT_TYPE'
            )
    
    def validate_json_structure(self, data: Any, max_depth: int = None) -> None:
        """Validate JSON structure depth and complexity"""
        max_depth = max_depth or self.config.max_nested_depth
        
        def check_depth(obj, current_depth=0):
            if current_depth > max_depth:
                raise ValidationError(
                    f"JSON structure too deep. Maximum depth: {max_depth}",
                    code='JSON_TOO_DEEP'
                )
            
            if isinstance(obj, dict):
                if len(obj) > self.config.max_array_length:
                    raise ValidationError(
                        f"Object has too many keys. Maximum: {self.config.max_array_length}",
                        code='OBJECT_TOO_LARGE'
                    )
                for value in obj.values():
                    check_depth(value, current_depth + 1)
            elif isinstance(obj, list):
                if len(obj) > self.config.max_array_length:
                    raise ValidationError(
                        f"Array too long. Maximum length: {self.config.max_array_length}",
                        code='ARRAY_TOO_LONG'
                    )
                for item in obj:
                    check_depth(item, current_depth + 1)
            elif isinstance(obj, str):
                if len(obj) > self.config.max_string_length:
                    raise ValidationError(
                        f"String too long. Maximum length: {self.config.max_string_length}",
                        code='STRING_TOO_LONG'
                    )
        
        check_depth(data)
    
    def validate_file_upload(self, file: FileStorage, file_type: str = None) -> None:
        """Validate uploaded file"""
        if not file or not file.filename:
            raise ValidationError("No file provided", code='NO_FILE')
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if size > self.config.max_file_size:
            raise ValidationError(
                f"File too large. Maximum size: {self.config.max_file_size} bytes",
                code='FILE_TOO_LARGE'
            )
        
        # Check file extension
        if file_type and file_type in self.config.allowed_file_types:
            allowed_extensions = self.config.allowed_file_types[file_type]
            file_extension = file.filename.rsplit('.', 1)[-1].lower()
            
            if file_extension not in allowed_extensions:
                raise ValidationError(
                    f"Invalid file type. Allowed: {', '.join(allowed_extensions)}",
                    code='INVALID_FILE_TYPE'
                )
    
    def sanitize_input(self, data: Any) -> Any:
        """Sanitize input data"""
        if isinstance(data, str):
            return ValidationUtils.sanitize_string(data)
        elif isinstance(data, dict):
            return {key: self.sanitize_input(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        else:
            return data


# Global validator instance
validator = InputValidator()


def validate_json(required_fields: List[str] = None,
                 optional_fields: List[str] = None,
                 pydantic_model: Type[BaseModel] = None,
                 sanitize: bool = True,
                 max_depth: int = None) -> Callable:
    """Decorator for JSON request validation
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names
        pydantic_model: Pydantic model for validation
        sanitize: Whether to sanitize input data
        max_depth: Maximum JSON nesting depth
    
    Returns:
        Decorated function
    """
    def json_validation_decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                # Validate content type
                validator.validate_content_type(request, ['application/json'])
                
                # Validate request size
                validator.validate_request_size(request)
                
                # Get JSON data
                if not request.is_json:
                    return jsonify({
                        'success': False,
                        'error': 'Content-Type must be application/json',
                        'code': 'INVALID_CONTENT_TYPE'
                    }), 400
                
                data = request.get_json()
                if data is None:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid JSON data',
                        'code': 'INVALID_JSON'
                    }), 400
                
                # Validate JSON structure
                validator.validate_json_structure(data, max_depth)
                
                # Sanitize input if requested
                if sanitize:
                    data = validator.sanitize_input(data)
                
                # Validate using Pydantic model
                if pydantic_model:
                    try:
                        validated_data = pydantic_model(**data)
                        request.validated_data = validated_data.dict()
                    except ValidationError as e:
                        return jsonify({
                            'success': False,
                            'error': 'Validation failed',
                            'details': e.errors(),
                            'code': 'PYDANTIC_VALIDATION_ERROR'
                        }), 400
                else:
                    # Manual field validation
                    if required_fields:
                        validation_errors = ValidationUtils.validate_required_fields(data, required_fields)
                        if validation_errors:
                            return jsonify({
                                'success': False,
                                'error': 'Missing required fields',
                                'details': validation_errors,
                                'code': 'MISSING_REQUIRED_FIELDS'
                            }), 400
                    
                    # Store validated data
                    request.validated_data = data
                
                return func(*args, **kwargs)
                
            except ValidationError as e:
                logger.warning(f"Validation error in {func.__name__}: {e.message}")
                return jsonify({
                    'success': False,
                    'error': e.message,
                    'field': e.field,
                    'code': e.code
                }), 400
            except Exception as e:
                logger.error(f"Unexpected validation error in {func.__name__}: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Internal validation error',
                    'code': 'INTERNAL_VALIDATION_ERROR'
                }), 500
        
        return wrapper
    return json_validation_decorator


def validate_query_params(pydantic_model: Type[BaseModel] = None,
                         required_params: List[str] = None,
                         optional_params: List[str] = None,
                         param_types: Dict[str, type] = None) -> Callable:
    """Decorator for query parameter validation
    
    Args:
        pydantic_model: Pydantic model class for validation (preferred)
        required_params: List of required parameter names (legacy)
        optional_params: List of optional parameter names (legacy)
        param_types: Dictionary mapping parameter names to expected types (legacy)
    
    Returns:
        Decorated function
    """
    # Handle case where first argument is a Pydantic model class
    if (pydantic_model is not None and 
        hasattr(pydantic_model, '__bases__') and 
        BaseModel in pydantic_model.__bases__):
        model_class = pydantic_model
    elif (required_params is None and optional_params is None and param_types is None and
          pydantic_model is not None and 
          hasattr(pydantic_model, '__bases__') and 
          BaseModel in pydantic_model.__bases__):
        model_class = pydantic_model
    else:
        model_class = None
    
    def query_validation_decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                params = request.args.to_dict()
                
                # Handle Pydantic model validation
                if model_class:
                    try:
                        # Convert string values to appropriate types for Pydantic
                        converted_params = {}
                        for key, value in params.items():
                            # Try to convert common types
                            if value.lower() in ('true', 'false'):
                                converted_params[key] = value.lower() == 'true'
                            elif value.isdigit():
                                converted_params[key] = int(value)
                            else:
                                try:
                                    converted_params[key] = float(value)
                                except ValueError:
                                    converted_params[key] = value
                        
                        # Validate with Pydantic model
                        validated_params = model_class(**converted_params)
                        request.validated_params = validated_params
                        
                    except ValidationError as e:
                        error_details = []
                        for error in e.errors():
                            field = '.'.join(str(loc) for loc in error['loc'])
                            message = error['msg']
                            error_details.append(f"{field}: {message}")
                        
                        return jsonify({
                            'success': False,
                            'error': 'Parameter validation error',
                            'details': error_details,
                            'code': 'PARAM_VALIDATION_ERROR'
                        }), 400
                        
                else:
                    # Legacy validation logic
                    # Validate required parameters
                    if required_params:
                        missing_params = [param for param in required_params if param not in params]
                        if missing_params:
                            return jsonify({
                                'success': False,
                                'error': f'Missing required parameters: {", ".join(missing_params)}',
                                'code': 'MISSING_REQUIRED_PARAMS'
                            }), 400
                    
                    # Type validation
                    if param_types:
                        for param_name, expected_type in param_types.items():
                            if param_name in params:
                                try:
                                    if expected_type == bool:
                                        params[param_name] = params[param_name].lower() in ('true', '1', 'yes')
                                    elif expected_type == int:
                                        params[param_name] = int(params[param_name])
                                    elif expected_type == float:
                                        params[param_name] = float(params[param_name])
                                    # str is default, no conversion needed
                                except (ValueError, TypeError):
                                    return jsonify({
                                        'success': False,
                                        'error': f'Invalid type for parameter {param_name}. Expected {expected_type.__name__}',
                                        'code': 'INVALID_PARAM_TYPE'
                                    }), 400
                    
                    # Store validated parameters
                    request.validated_params = params
                
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Query parameter validation error in {func.__name__}: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Parameter validation error',
                    'code': 'PARAM_VALIDATION_ERROR'
                }), 500
        
        return wrapper
    
    # Handle direct call with Pydantic model as first argument
    if (pydantic_model is not None and 
        hasattr(pydantic_model, '__bases__') and 
        BaseModel in pydantic_model.__bases__):
        return query_validation_decorator
    else:
        return query_validation_decorator


def validate_file_upload(file_param: str = 'file',
                        file_type: str = None,
                        required: bool = True) -> Callable:
    """Decorator for file upload validation
    
    Args:
        file_param: Name of the file parameter
        file_type: Expected file type category
        required: Whether file is required
    
    Returns:
        Decorated function
    """
    def file_validation_decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                # Check if file exists in request
                if file_param not in request.files:
                    if required:
                        return jsonify({
                            'success': False,
                            'error': f'No file found with parameter name: {file_param}',
                            'code': 'NO_FILE_PARAM'
                        }), 400
                    else:
                        request.validated_file = None
                        return func(*args, **kwargs)
                
                file = request.files[file_param]
                
                # Validate file
                validator.validate_file_upload(file, file_type)
                
                # Store validated file
                request.validated_file = file
                
                return func(*args, **kwargs)
                
            except ValidationError as e:
                logger.warning(f"File validation error in {func.__name__}: {e.message}")
                return jsonify({
                    'success': False,
                    'error': e.message,
                    'code': e.code
                }), 400
            except Exception as e:
                logger.error(f"Unexpected file validation error in {func.__name__}: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'File validation error',
                    'code': 'FILE_VALIDATION_ERROR'
                }), 500
        
        return wrapper
    return file_validation_decorator


def validate_path_params(**param_validators) -> Callable:
    """Decorator for path parameter validation
    
    Args:
        **param_validators: Keyword arguments mapping parameter names to validation functions
    
    Returns:
        Decorated function
    
    Example:
        @validate_path_params(user_id=ValidationUtils.validate_uuid, age=lambda x: 0 <= int(x) <= 150)
        def get_user(user_id, age):
            pass
    """
    def path_validation_decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                # Validate path parameters
                for param_name, validator_func in param_validators.items():
                    if param_name in kwargs:
                        param_value = kwargs[param_name]
                        
                        # Apply validation function
                        if not validator_func(param_value):
                            return jsonify({
                                'success': False,
                                'error': f'Invalid value for path parameter: {param_name}',
                                'code': 'INVALID_PATH_PARAM'
                            }), 400
                
                return func(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Path parameter validation error in {func.__name__}: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Path parameter validation error',
                    'code': 'PATH_PARAM_VALIDATION_ERROR'
                }), 500
        
        return wrapper
    return email_validation_decorator


# Convenience decorators for common validation patterns
def require_json_fields(*required_fields) -> Callable:
    """Simple decorator to require specific JSON fields"""
    return validate_json(required_fields=list(required_fields))


def validate_email_field(field_name: str = 'email') -> Callable:
    """Decorator to validate email field in JSON request"""
    def email_validation_decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            data = request.get_json() or {}
            
            if field_name in data:
                if not ValidationUtils.validate_email(data[field_name]):
                    return jsonify({
                        'success': False,
                        'error': f'Invalid email format in field: {field_name}',
                        'code': 'INVALID_EMAIL'
                    }), 400
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_uuid_param(param_name: str) -> Callable:
    """Decorator to validate UUID path parameter"""
    return validate_path_params(**{param_name: ValidationUtils.validate_uuid})


# Export commonly used validators
__all__ = [
    'ValidationConfig',
    'ValidationError',
    'InputValidator',
    'validator',
    'validate_json',
    'validate_query_params',
    'validate_file_upload',
    'validate_path_params',
    'require_json_fields',
    'validate_email_field',
    'validate_uuid_param'
]