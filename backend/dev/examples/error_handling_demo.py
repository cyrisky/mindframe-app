#!/usr/bin/env python3
"""
Centralized Error Handling Demonstration

This script demonstrates the usage of the centralized error handling system
with various types of exceptions and error scenarios.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from bson.errors import InvalidId

# Import our centralized error handling components
from src.utils.exceptions import (
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ResourceNotFoundError,
    DatabaseError,
    ExternalServiceError,
    RateLimitError,
    BusinessRuleError,
    FileError,
    ConfigurationError,
    ErrorCode
)
from src.utils.error_handler import (
    setup_error_handling,
    raise_validation_error,
    raise_not_found,
    raise_authentication_error,
    raise_authorization_error,
    raise_database_error
)
from src.utils.logging_utils import LoggingUtils


def create_demo_app():
    """Create a demo Flask app with error handling"""
    app = Flask(__name__)
    app.config['DEBUG'] = True
    
    # Setup logging
    LoggingUtils.setup_logging(
        log_level='DEBUG',
        log_format='structured',
        log_file='../logs/error_demo.log'
    )
    
    # Setup centralized error handling
    error_handler = setup_error_handling(app)
    
    return app, error_handler


def register_demo_routes(app):
    """Register demonstration routes for different error types"""
    
    @app.route('/demo/validation-error')
    def demo_validation_error():
        """Demonstrate validation error"""
        # Simulate validation failure
        raise_validation_error(
            "Invalid email format",
            field="email",
            details={
                "provided_value": "invalid-email",
                "expected_format": "user@domain.com",
                "validation_rules": ["must contain @", "must have valid domain"]
            }
        )
    
    @app.route('/demo/authentication-error')
    def demo_authentication_error():
        """Demonstrate authentication error"""
        raise_authentication_error("Invalid credentials provided")
    
    @app.route('/demo/authorization-error')
    def demo_authorization_error():
        """Demonstrate authorization error"""
        raise AuthorizationError(
            "Insufficient permissions to access admin resources",
            required_role="admin",
            user_role="user"
        )
    
    @app.route('/demo/not-found')
    def demo_not_found():
        """Demonstrate resource not found error"""
        raise_not_found("user", "12345")
    
    @app.route('/demo/database-error')
    def demo_database_error():
        """Demonstrate database error"""
        # Simulate a database connection error
        original_error = ConnectionFailure("Unable to connect to MongoDB")
        raise_database_error(
            "Failed to connect to user database",
            original_error=original_error
        )
    
    @app.route('/demo/duplicate-key')
    def demo_duplicate_key():
        """Demonstrate duplicate key error (handled automatically)"""
        # This will be caught by the centralized handler
        raise DuplicateKeyError("E11000 duplicate key error collection: users index: email_1")
    
    @app.route('/demo/invalid-object-id')
    def demo_invalid_object_id():
        """Demonstrate invalid MongoDB ObjectId"""
        # This will be caught by the centralized handler
        raise InvalidId("invalid-object-id")
    
    @app.route('/demo/external-service-error')
    def demo_external_service_error():
        """Demonstrate external service error"""
        raise ExternalServiceError(
            "Email service unavailable",
            service_name="SendGrid",
            error_code="503",
            retry_after=300
        )
    
    @app.route('/demo/rate-limit')
    def demo_rate_limit():
        """Demonstrate rate limiting error"""
        raise RateLimitError(
            "API rate limit exceeded",
            limit=100,
            window="1 hour",
            retry_after=3600
        )
    
    @app.route('/demo/business-rule')
    def demo_business_rule():
        """Demonstrate business rule violation"""
        raise BusinessRuleError(
            "Cannot delete user with active subscriptions",
            rule="active_subscription_check",
            details={
                "user_id": "12345",
                "active_subscriptions": 2,
                "action_required": "Cancel subscriptions before deletion"
            }
        )
    
    @app.route('/demo/file-error')
    def demo_file_error():
        """Demonstrate file operation error"""
        raise FileError(
            "Failed to upload profile image",
            file_path="/uploads/profile.jpg",
            operation="upload",
            details={
                "file_size": "5MB",
                "max_allowed": "2MB",
                "error_type": "size_exceeded"
            }
        )
    
    @app.route('/demo/configuration-error')
    def demo_configuration_error():
        """Demonstrate configuration error"""
        raise ConfigurationError(
            "Missing required environment variable",
            config_key="DATABASE_URL",
            details={
                "required_format": "mongodb://username:password@host:port/database",
                "current_value": None
            }
        )
    
    @app.route('/demo/multiple-validation-errors')
    def demo_multiple_validation_errors():
        """Demonstrate multiple validation errors"""
        from src.utils.exceptions import MultipleValidationErrors
        
        errors = [
            ValidationError("Email is required", field="email"),
            ValidationError("Password must be at least 8 characters", field="password"),
            ValidationError("Age must be between 18 and 120", field="age")
        ]
        
        raise MultipleValidationErrors(errors)
    
    @app.route('/demo/unhandled-exception')
    def demo_unhandled_exception():
        """Demonstrate unhandled exception (caught by generic handler)"""
        # This will be caught by the generic exception handler
        raise ValueError("This is an unhandled exception for demonstration")
    
    @app.route('/demo/success')
    def demo_success():
        """Demonstrate successful response"""
        return jsonify({
            'success': True,
            'message': 'Operation completed successfully',
            'data': {
                'user_id': '12345',
                'action': 'demo_success',
                'timestamp': '2024-01-20T10:30:00Z'
            }
        })
    
    @app.route('/demo')
    def demo_index():
        """List all available demo endpoints"""
        endpoints = [
            {'path': '/demo/validation-error', 'description': 'Validation error with field details'},
            {'path': '/demo/authentication-error', 'description': 'Authentication failure'},
            {'path': '/demo/authorization-error', 'description': 'Authorization/permission error'},
            {'path': '/demo/not-found', 'description': 'Resource not found'},
            {'path': '/demo/database-error', 'description': 'Database connection error'},
            {'path': '/demo/duplicate-key', 'description': 'MongoDB duplicate key error'},
            {'path': '/demo/invalid-object-id', 'description': 'Invalid MongoDB ObjectId'},
            {'path': '/demo/external-service-error', 'description': 'External service unavailable'},
            {'path': '/demo/rate-limit', 'description': 'Rate limit exceeded'},
            {'path': '/demo/business-rule', 'description': 'Business rule violation'},
            {'path': '/demo/file-error', 'description': 'File operation error'},
            {'path': '/demo/configuration-error', 'description': 'Configuration/environment error'},
            {'path': '/demo/multiple-validation-errors', 'description': 'Multiple validation errors'},
            {'path': '/demo/unhandled-exception', 'description': 'Unhandled exception (generic handler)'},
            {'path': '/demo/success', 'description': 'Successful operation'}
        ]
        
        return jsonify({
            'success': True,
            'message': 'Error Handling Demo Endpoints',
            'endpoints': endpoints,
            'usage': {
                'description': 'Visit any endpoint to see different error handling examples',
                'note': 'All errors include request IDs for tracking and structured logging'
            }
        })


def main():
    """Run the error handling demonstration"""
    print("🚀 Starting Error Handling Demonstration")
    print("==========================================")
    
    # Create demo app
    app, error_handler = create_demo_app()
    
    # Register demo routes
    register_demo_routes(app)
    
    print("\n📋 Available Demo Endpoints:")
    print("- http://localhost:5001/demo - List all endpoints")
    print("- http://localhost:5001/demo/validation-error - Validation error")
    print("- http://localhost:5001/demo/authentication-error - Auth error")
    print("- http://localhost:5001/demo/not-found - Resource not found")
    print("- http://localhost:5001/demo/database-error - Database error")
    print("- http://localhost:5001/demo/success - Successful response")
    print("\n🔍 Features Demonstrated:")
    print("- Standardized error responses with error codes")
    print("- Request ID tracking for debugging")
    print("- Structured logging with context")
    print("- Automatic error type detection")
    print("- Detailed error information for debugging")
    print("\n📝 Check ../logs/error_demo.log for structured logging output")
    print("\n🌐 Starting server on http://localhost:5001")
    print("Press Ctrl+C to stop")
    
    try:
        app.run(
            host='0.0.0.0',
            port=5001,
            debug=True,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Demo stopped")


if __name__ == '__main__':
    main()