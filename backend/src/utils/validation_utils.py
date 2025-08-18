"""Validation utilities for the mindframe application"""

import re
import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union, Callable
from email_validator import validate_email, EmailNotValidError
from pydantic import BaseModel, ValidationError


class ValidationUtils:
    """Utility class for data validation operations"""
    
    # Common regex patterns
    PHONE_PATTERN = re.compile(r'^[\+]?[1-9]?[0-9]{7,15}$')
    PASSWORD_PATTERN = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,20}$')
    NAME_PATTERN = re.compile(r'^[a-zA-Z\s\-\']{2,50}$')
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email address format
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if email is valid, False otherwise
        """
        try:
            validate_email(email)
            return True
        except EmailNotValidError:
            return False
    
    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Validate phone number format
        
        Args:
            phone: Phone number to validate
            
        Returns:
            bool: True if phone is valid, False otherwise
        """
        if not phone:
            return False
        # Remove spaces and dashes for validation
        clean_phone = re.sub(r'[\s\-]', '', phone)
        return bool(ValidationUtils.PHONE_PATTERN.match(clean_phone))
    
    @staticmethod
    def is_valid_password(password: str) -> bool:
        """Validate password strength
        
        Args:
            password: Password to validate
            
        Returns:
            bool: True if password meets requirements, False otherwise
        """
        if not password:
            return False
        return bool(ValidationUtils.PASSWORD_PATTERN.match(password))
    
    @staticmethod
    def is_valid_username(username: str) -> bool:
        """Validate username format
        
        Args:
            username: Username to validate
            
        Returns:
            bool: True if username is valid, False otherwise
        """
        if not username:
            return False
        return bool(ValidationUtils.USERNAME_PATTERN.match(username))
    
    @staticmethod
    def is_valid_name(name: str) -> bool:
        """Validate person name format
        
        Args:
            name: Name to validate
            
        Returns:
            bool: True if name is valid, False otherwise
        """
        if not name:
            return False
        return bool(ValidationUtils.NAME_PATTERN.match(name.strip()))
    
    @staticmethod
    def is_valid_uuid(uuid_string: str) -> bool:
        """Validate UUID format
        
        Args:
            uuid_string: UUID string to validate
            
        Returns:
            bool: True if UUID is valid, False otherwise
        """
        try:
            uuid.UUID(uuid_string)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_date(date_string: str, date_format: str = '%Y-%m-%d') -> bool:
        """Validate date string format
        
        Args:
            date_string: Date string to validate
            date_format: Expected date format
            
        Returns:
            bool: True if date is valid, False otherwise
        """
        try:
            datetime.strptime(date_string, date_format)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_age(age: int, min_age: int = 0, max_age: int = 150) -> bool:
        """Validate age range
        
        Args:
            age: Age to validate
            min_age: Minimum allowed age
            max_age: Maximum allowed age
            
        Returns:
            bool: True if age is valid, False otherwise
        """
        try:
            return min_age <= int(age) <= max_age
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate URL format
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if URL is valid, False otherwise
        """
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # domain...
            r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # host...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(url))
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Validate that required fields are present and not empty
        
        Args:
            data: Data dictionary to validate
            required_fields: List of required field names
            
        Returns:
            List[str]: List of missing or empty fields
        """
        missing_fields = []
        for field in required_fields:
            if field not in data or not data[field] or (isinstance(data[field], str) and not data[field].strip()):
                missing_fields.append(field)
        return missing_fields
    
    @staticmethod
    def validate_field_types(data: Dict[str, Any], field_types: Dict[str, type]) -> List[str]:
        """Validate field types
        
        Args:
            data: Data dictionary to validate
            field_types: Dictionary mapping field names to expected types
            
        Returns:
            List[str]: List of fields with incorrect types
        """
        invalid_fields = []
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                invalid_fields.append(field)
        return invalid_fields
    
    @staticmethod
    def validate_field_lengths(data: Dict[str, Any], field_lengths: Dict[str, Dict[str, int]]) -> List[str]:
        """Validate field string lengths
        
        Args:
            data: Data dictionary to validate
            field_lengths: Dictionary mapping field names to min/max length constraints
                          Format: {'field_name': {'min': 1, 'max': 100}}
            
        Returns:
            List[str]: List of fields with invalid lengths
        """
        invalid_fields = []
        for field, constraints in field_lengths.items():
            if field in data and isinstance(data[field], str):
                field_length = len(data[field])
                min_length = constraints.get('min', 0)
                max_length = constraints.get('max', float('inf'))
                
                if field_length < min_length or field_length > max_length:
                    invalid_fields.append(field)
        return invalid_fields
    
    @staticmethod
    def validate_pydantic_model(data: Dict[str, Any], model_class: type) -> tuple[bool, Optional[str]]:
        """Validate data against a Pydantic model
        
        Args:
            data: Data to validate
            model_class: Pydantic model class
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            model_class(**data)
            return True, None
        except ValidationError as e:
            return False, str(e)
    
    @staticmethod
    def validate_custom_rules(data: Dict[str, Any], validators: Dict[str, Callable]) -> List[str]:
        """Validate data using custom validation functions
        
        Args:
            data: Data dictionary to validate
            validators: Dictionary mapping field names to validation functions
                       Each function should return True if valid, False otherwise
            
        Returns:
            List[str]: List of fields that failed validation
        """
        invalid_fields = []
        for field, validator in validators.items():
            if field in data:
                try:
                    if not validator(data[field]):
                        invalid_fields.append(field)
                except Exception:
                    invalid_fields.append(field)
        return invalid_fields
    
    @staticmethod
    def sanitize_string(text: str, max_length: Optional[int] = None, allow_html: bool = False) -> str:
        """Sanitize string input
        
        Args:
            text: Text to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML tags
            
        Returns:
            str: Sanitized text
        """
        if not isinstance(text, str):
            return str(text)
        
        # Remove or escape HTML if not allowed
        if not allow_html:
            text = re.sub(r'<[^>]+>', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Truncate if necessary
        if max_length and len(text) > max_length:
            text = text[:max_length].strip()
        
        return text
    
    @staticmethod
    def validate_file_upload(file_data: Dict[str, Any], 
                           allowed_types: List[str] = None,
                           max_size_mb: int = 10) -> tuple[bool, Optional[str]]:
        """Validate file upload data
        
        Args:
            file_data: Dictionary containing file information
            allowed_types: List of allowed file extensions
            max_size_mb: Maximum file size in MB
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not file_data:
            return False, "No file data provided"
        
        filename = file_data.get('filename', '')
        file_size = file_data.get('size', 0)
        
        if not filename:
            return False, "Filename is required"
        
        # Check file extension
        if allowed_types:
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            if file_ext not in [ext.lower() for ext in allowed_types]:
                return False, f"File type '{file_ext}' not allowed. Allowed types: {', '.join(allowed_types)}"
        
        # Check file size
        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            return False, f"File size exceeds maximum allowed size of {max_size_mb}MB"
        
        return True, None
    
    @staticmethod
    def validate_json_schema(data: Any, schema: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate data against JSON schema
        
        Args:
            data: Data to validate
            schema: JSON schema dictionary
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            import jsonschema
            jsonschema.validate(data, schema)
            return True, None
        except ImportError:
            return False, "jsonschema library not available"
        except jsonschema.ValidationError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {str(e)}"


def validate_pdf_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate PDF generation request data
    
    Args:
        data: Request data dictionary
        
    Returns:
        dict: Validation result with 'valid' boolean and 'errors' list
    """
    errors = []
    
    if not data:
        errors.append("Request data is required")
        return {'valid': False, 'errors': errors}
    
    # Check required fields
    if 'html_content' not in data or not data['html_content']:
        errors.append("html_content is required")
    
    # Validate options if provided
    if 'options' in data and data['options']:
        options = data['options']
        if 'page_size' in options:
            valid_sizes = ['A4', 'A3', 'A5', 'Letter', 'Legal']
            if options['page_size'] not in valid_sizes:
                errors.append(f"Invalid page_size. Must be one of: {', '.join(valid_sizes)}")
        
        if 'orientation' in options:
            valid_orientations = ['portrait', 'landscape']
            if options['orientation'] not in valid_orientations:
                errors.append(f"Invalid orientation. Must be one of: {', '.join(valid_orientations)}")
    
    return {'valid': len(errors) == 0, 'errors': errors}


def validate_template_data(template_name: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate template data
    
    Args:
        template_name: Name of the template
        template_data: Template data dictionary
        
    Returns:
        dict: Validation result with 'valid' boolean and 'errors' list
    """
    errors = []
    
    if not template_name:
        errors.append("Template name is required")
    
    if not template_data:
        errors.append("Template data is required")
        return {'valid': False, 'errors': errors}
    
    # Basic validation - can be extended based on specific template requirements
    if not isinstance(template_data, dict):
        errors.append("Template data must be a dictionary")
    
    return {'valid': len(errors) == 0, 'errors': errors}