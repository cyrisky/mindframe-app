#!/usr/bin/env python3
"""
Structured Logging Demonstration

This script demonstrates the enhanced structured logging capabilities
implemented in the Mindframe backend application.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.utils.logging_utils import LoggingUtils
from src.services.report_service import ReportService
from src.services.database_service import DatabaseService
import time
import json

def demonstrate_basic_logging():
    """Demonstrate basic structured logging"""
    print("\n=== Basic Structured Logging ===")
    
    # Get a logger for this demo
    logger = LoggingUtils.get_logger('demo.basic')
    
    # Basic log messages
    logger.info("Application started")
    logger.debug("Debug information", extra={'debug_level': 'verbose'})
    logger.warning("This is a warning message", extra={'warning_type': 'configuration'})
    
    # Log with structured context
    logger.info("User action performed", extra={
        'user_id': 'user_12345',
        'action': 'login',
        'ip_address': '192.168.1.100',
        'user_agent': 'Mozilla/5.0 (Demo Browser)',
        'success': True,
        'duration_ms': 250
    })
    
    # Log with sensitive data (will be automatically redacted)
    logger.info("Authentication attempt", extra={
        'username': 'john.doe@example.com',
        'password': 'secret123',  # Will be redacted
        'api_key': 'sk_test_123456',  # Will be redacted
        'session_token': 'sess_abcdef',  # Will be redacted
        'result': 'success'
    })

def demonstrate_contextual_logging():
    """Demonstrate contextual logging with automatic context"""
    print("\n=== Contextual Logging ===")
    
    # Create a contextual logger with automatic context
    context_logger = LoggingUtils.get_contextual_logger('demo.contextual', {
        'request_id': 'req_abc123',
        'user_id': 'user_456',
        'operation': 'report_generation',
        'client_name': 'Demo Client'
    })
    
    # All log messages will automatically include the context
    context_logger.info("Starting operation")
    context_logger.debug("Processing step 1")
    context_logger.debug("Processing step 2")
    context_logger.info("Operation completed successfully", extra={
        'duration_ms': 1500,
        'items_processed': 42
    })

def demonstrate_performance_logging():
    """Demonstrate performance logging"""
    print("\n=== Performance Logging ===")
    
    logger = LoggingUtils.get_logger('demo.performance')
    
    # Manual performance logging
    start_time = time.time()
    
    # Simulate some work
    time.sleep(0.1)
    
    execution_time = time.time() - start_time
    logger.info("Operation completed", extra={
        'operation': 'data_processing',
        'execution_time_ms': round(execution_time * 1000, 2),
        'records_processed': 1000,
        'throughput_per_second': round(1000 / execution_time, 2)
    })
    
    # Using the performance decorator
    @LoggingUtils.log_performance(logger, level='INFO', threshold_seconds=0.05)
    def expensive_operation():
        """Simulate an expensive operation"""
        time.sleep(0.1)
        return "Operation result"
    
    result = expensive_operation()
    logger.info("Decorated function result", extra={'result': result})

def demonstrate_error_logging():
    """Demonstrate error logging with context"""
    print("\n=== Error Logging ===")
    
    logger = LoggingUtils.get_logger('demo.errors')
    
    try:
        # Simulate an error
        raise ValueError("This is a demonstration error")
    except ValueError as e:
        logger.error("Demonstration error occurred", extra={
            'error_type': type(e).__name__,
            'error_message': str(e),
            'operation': 'demo_operation',
            'user_id': 'demo_user',
            'recovery_possible': True
        }, exc_info=True)
    
    # Log a warning about a recoverable issue
    logger.warning("Recoverable issue detected", extra={
        'issue_type': 'configuration_missing',
        'default_used': True,
        'config_key': 'DEMO_SETTING',
        'default_value': 'demo_default'
    })

def demonstrate_service_logging():
    """Demonstrate service-level structured logging"""
    print("\n=== Service-Level Logging ===")
    
    # Initialize services (this will generate structured logs)
    db_service = DatabaseService()
    report_service = ReportService()
    
    # Note: These will fail without actual database connection,
    # but will demonstrate the logging structure
    print("Attempting database initialization (will fail without MongoDB)...")
    db_result = db_service.initialize()
    
    print("Attempting report service initialization...")
    report_result = report_service.initialize(db_service=db_service)
    
    # Demonstrate report creation logging (will fail without database)
    if report_result:
        sample_report_data = {
            'report_type': 'personality_assessment',
            'client_information': {
                'name': 'Demo Client',
                'email': 'demo@example.com',
                'age': 25
            },
            'test_results': []
        }
        
        print("Attempting report creation (will fail without database)...")
        create_result = report_service.create_report(sample_report_data, user_id='demo_user')

def demonstrate_json_logging():
    """Demonstrate JSON logging output"""
    print("\n=== JSON Logging Output ===")
    
    # Create a logger with JSON formatter
    json_logger = LoggingUtils.create_json_formatter(
        include_caller_info=True,
        include_process_info=True,
        include_thread_info=False
    )
    
    # Note: This would typically be configured at the application level
    logger = LoggingUtils.get_logger('demo.json')
    
    # Add some sample structured data
    logger.info("JSON formatted log entry", extra={
        'event_type': 'user_action',
        'user_id': 'user_789',
        'action_details': {
            'action': 'file_upload',
            'file_name': 'report.pdf',
            'file_size_bytes': 1024000,
            'upload_duration_ms': 2500
        },
        'metadata': {
            'client_version': '1.0.0',
            'api_version': 'v1',
            'feature_flags': ['new_ui', 'enhanced_logging']
        }
    })

def main():
    """Main demonstration function"""
    print("Mindframe Backend - Structured Logging Demonstration")
    print("=" * 60)
    
    # Set up logging configuration for demo
    os.environ.setdefault('LOG_LEVEL', 'DEBUG')
    os.environ.setdefault('LOG_FORMAT', 'structured')
    
    try:
        demonstrate_basic_logging()
        demonstrate_contextual_logging()
        demonstrate_performance_logging()
        demonstrate_error_logging()
        demonstrate_service_logging()
        demonstrate_json_logging()
        
        print("\n=== Demo Complete ===")
        print("Check the console output above to see the structured logging in action.")
        print("In production, these logs would be written to files and/or sent to log aggregation systems.")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()