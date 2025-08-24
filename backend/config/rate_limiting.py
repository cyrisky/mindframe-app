#!/usr/bin/env python3
"""
Rate Limiting Configuration

This module contains configuration settings for rate limiting across the application.
Settings can be overridden via environment variables for different deployment environments.
"""

import os
from typing import Dict, List, Optional


class RateLimitingConfig:
    """Configuration class for rate limiting settings"""
    
    # Enable/disable rate limiting globally
    ENABLED = os.getenv('RATE_LIMITING_ENABLED', 'true').lower() == 'true'
    
    # Redis configuration for rate limiting storage
    REDIS_URL = os.getenv('RATE_LIMITING_REDIS_URL', os.getenv('REDIS_URL', 'redis://localhost:6379/1'))
    
    # Rate limiting strategy
    # Options: 'fixed-window', 'moving-window', 'sliding-window-counter'
    STRATEGY = os.getenv('RATE_LIMITING_STRATEGY', 'moving-window')
    
    # Application-wide meta limits (applied to all requests)
    APPLICATION_LIMITS = [
        os.getenv('RATE_LIMITING_APP_DAILY', '10000/day'),
        os.getenv('RATE_LIMITING_APP_HOURLY', '1000/hour')
    ]
    
    # Global default limits for all routes (if no specific limit is set)
    GLOBAL_DEFAULT_LIMITS = [
        os.getenv('RATE_LIMITING_GLOBAL_HOURLY', '500/hour'),
        os.getenv('RATE_LIMITING_GLOBAL_MINUTE', '50/minute')
    ]
    
    # Endpoint-specific rate limits
    ENDPOINT_LIMITS = {
        # Authentication endpoints (stricter limits)
        'auth': {
            'login': os.getenv('RATE_LIMITING_AUTH_LOGIN', '10/minute'),
            'register': os.getenv('RATE_LIMITING_AUTH_REGISTER', '5/minute'),
            'forgot_password': os.getenv('RATE_LIMITING_AUTH_FORGOT', '3/minute'),
            'reset_password': os.getenv('RATE_LIMITING_AUTH_RESET', '3/minute'),
            'verify_email': os.getenv('RATE_LIMITING_AUTH_VERIFY', '5/minute'),
            'resend_verification': os.getenv('RATE_LIMITING_AUTH_RESEND', '3/minute'),
            'change_password': os.getenv('RATE_LIMITING_AUTH_CHANGE_PWD', '5/minute'),
            'refresh_token': os.getenv('RATE_LIMITING_AUTH_REFRESH', '20/minute'),
        },
        
        # API endpoints (standard limits)
        'api': {
            'standard': os.getenv('RATE_LIMITING_API_STANDARD', '100/hour'),
            'strict': os.getenv('RATE_LIMITING_API_STRICT', '50/hour'),
            'public': os.getenv('RATE_LIMITING_API_PUBLIC', '1000/hour'),
        },
        
        # File operations (more restrictive)
        'files': {
            'upload': os.getenv('RATE_LIMITING_FILES_UPLOAD', '5/minute'),
            'download': os.getenv('RATE_LIMITING_FILES_DOWNLOAD', '20/minute'),
            'delete': os.getenv('RATE_LIMITING_FILES_DELETE', '10/minute'),
        },
        
        # Heavy computation endpoints
        'computation': {
            'report_generation': os.getenv('RATE_LIMITING_COMPUTE_REPORT', '20/hour'),
            'pdf_generation': os.getenv('RATE_LIMITING_COMPUTE_PDF', '30/hour'),
            'data_export': os.getenv('RATE_LIMITING_COMPUTE_EXPORT', '10/hour'),
        },
        
        # Template operations
        'templates': {
            'create': os.getenv('RATE_LIMITING_TEMPLATE_CREATE', '20/hour'),
            'update': os.getenv('RATE_LIMITING_TEMPLATE_UPDATE', '50/hour'),
            'delete': os.getenv('RATE_LIMITING_TEMPLATE_DELETE', '10/hour'),
            'list': os.getenv('RATE_LIMITING_TEMPLATE_LIST', '200/hour'),
        }
    }
    
    # Rate limit headers configuration
    ENABLE_HEADERS = os.getenv('RATE_LIMITING_HEADERS_ENABLED', 'true').lower() == 'true'
    HEADER_MAPPING = {
        'LIMIT': os.getenv('RATE_LIMITING_HEADER_LIMIT', 'X-RateLimit-Limit'),
        'RESET': os.getenv('RATE_LIMITING_HEADER_RESET', 'X-RateLimit-Reset'),
        'REMAINING': os.getenv('RATE_LIMITING_HEADER_REMAINING', 'X-RateLimit-Remaining'),
        'RETRY_AFTER': os.getenv('RATE_LIMITING_HEADER_RETRY', 'Retry-After')
    }
    
    # IP whitelist (bypass rate limiting)
    WHITELIST_IPS = [
        '127.0.0.1',
        '::1',
        'localhost'
    ]
    
    # Additional whitelisted IPs from environment
    additional_ips = os.getenv('RATE_LIMITING_WHITELIST_IPS', '')
    if additional_ips:
        WHITELIST_IPS.extend([ip.strip() for ip in additional_ips.split(',') if ip.strip()])
    
    # User role-based exemptions
    EXEMPT_ROLES = [
        'admin',
        'system'
    ]
    
    # Additional exempt roles from environment
    additional_roles = os.getenv('RATE_LIMITING_EXEMPT_ROLES', '')
    if additional_roles:
        EXEMPT_ROLES.extend([role.strip() for role in additional_roles.split(',') if role.strip()])
    
    # Logging configuration
    LOG_VIOLATIONS = os.getenv('RATE_LIMITING_LOG_VIOLATIONS', 'true').lower() == 'true'
    LOG_LEVEL = os.getenv('RATE_LIMITING_LOG_LEVEL', 'WARNING')
    
    # Error handling
    SWALLOW_ERRORS = os.getenv('RATE_LIMITING_SWALLOW_ERRORS', 'false').lower() == 'true'
    
    # Development/testing overrides
    if os.getenv('FLASK_ENV') == 'development':
        # More lenient limits for development
        ENDPOINT_LIMITS['auth']['login'] = '50/minute'
        ENDPOINT_LIMITS['auth']['register'] = '20/minute'
        ENDPOINT_LIMITS['api']['standard'] = '500/hour'
        
    elif os.getenv('FLASK_ENV') == 'testing':
        # Disable rate limiting for tests unless explicitly enabled
        ENABLED = os.getenv('RATE_LIMITING_ENABLED', 'false').lower() == 'true'
    
    elif os.getenv('FLASK_ENV') == 'production':
        # Stricter limits for production
        ENDPOINT_LIMITS['auth']['login'] = '5/minute'
        ENDPOINT_LIMITS['auth']['register'] = '3/minute'
        ENDPOINT_LIMITS['auth']['forgot_password'] = '2/minute'
        ENDPOINT_LIMITS['files']['upload'] = '3/minute'
    
    @classmethod
    def get_endpoint_limit(cls, category: str, endpoint: str) -> Optional[str]:
        """Get rate limit for a specific endpoint
        
        Args:
            category: Endpoint category (auth, api, files, etc.)
            endpoint: Specific endpoint name
            
        Returns:
            Rate limit string or None if not found
        """
        return cls.ENDPOINT_LIMITS.get(category, {}).get(endpoint)
    
    @classmethod
    def get_all_limits(cls) -> Dict[str, Dict[str, str]]:
        """Get all configured rate limits
        
        Returns:
            Dictionary of all rate limits organized by category
        """
        return cls.ENDPOINT_LIMITS.copy()
    
    @classmethod
    def is_ip_whitelisted(cls, ip: str) -> bool:
        """Check if an IP address is whitelisted
        
        Args:
            ip: IP address to check
            
        Returns:
            True if IP is whitelisted
        """
        return ip in cls.WHITELIST_IPS
    
    @classmethod
    def is_role_exempt(cls, role: str) -> bool:
        """Check if a user role is exempt from rate limiting
        
        Args:
            role: User role to check
            
        Returns:
            True if role is exempt
        """
        return role in cls.EXEMPT_ROLES
    
    @classmethod
    def get_config_summary(cls) -> Dict[str, any]:
        """Get a summary of current rate limiting configuration
        
        Returns:
            Dictionary containing configuration summary
        """
        return {
            'enabled': cls.ENABLED,
            'strategy': cls.STRATEGY,
            'redis_url': cls.REDIS_URL,
            'application_limits': cls.APPLICATION_LIMITS,
            'global_default_limits': cls.GLOBAL_DEFAULT_LIMITS,
            'headers_enabled': cls.ENABLE_HEADERS,
            'whitelist_ips_count': len(cls.WHITELIST_IPS),
            'exempt_roles_count': len(cls.EXEMPT_ROLES),
            'log_violations': cls.LOG_VIOLATIONS,
            'endpoint_categories': list(cls.ENDPOINT_LIMITS.keys()),
            'total_endpoint_limits': sum(len(endpoints) for endpoints in cls.ENDPOINT_LIMITS.values())
        }


# Environment-specific configurations
class DevelopmentRateLimitingConfig(RateLimitingConfig):
    """Development environment rate limiting configuration"""
    
    # More lenient limits for development
    GLOBAL_DEFAULT_LIMITS = ['1000/hour', '100/minute']
    
    # Relaxed auth limits
    ENDPOINT_LIMITS = RateLimitingConfig.ENDPOINT_LIMITS.copy()
    ENDPOINT_LIMITS['auth'].update({
        'login': '100/minute',
        'register': '50/minute',
        'forgot_password': '20/minute',
    })


class TestingRateLimitingConfig(RateLimitingConfig):
    """Testing environment rate limiting configuration"""
    
    # Disable by default for testing
    ENABLED = False
    
    # Very high limits if enabled
    GLOBAL_DEFAULT_LIMITS = ['10000/hour', '1000/minute']
    APPLICATION_LIMITS = ['100000/day', '10000/hour']


class ProductionRateLimitingConfig(RateLimitingConfig):
    """Production environment rate limiting configuration"""
    
    # Stricter limits for production
    GLOBAL_DEFAULT_LIMITS = ['200/hour', '20/minute']
    
    # Strict auth limits
    ENDPOINT_LIMITS = RateLimitingConfig.ENDPOINT_LIMITS.copy()
    ENDPOINT_LIMITS['auth'].update({
        'login': '5/minute',
        'register': '2/minute',
        'forgot_password': '1/minute',
        'reset_password': '1/minute',
    })
    
    # Strict file operation limits
    ENDPOINT_LIMITS['files'].update({
        'upload': '2/minute',
        'download': '10/minute',
    })


def get_rate_limiting_config():
    """Get the appropriate rate limiting configuration based on environment
    
    Returns:
        Rate limiting configuration class
    """
    env = os.getenv('FLASK_ENV', 'development').lower()
    
    if env == 'production':
        return ProductionRateLimitingConfig
    elif env == 'testing':
        return TestingRateLimitingConfig
    elif env == 'development':
        return DevelopmentRateLimitingConfig
    else:
        return RateLimitingConfig


if __name__ == '__main__':
    # Print configuration summary
    config = get_rate_limiting_config()
    summary = config.get_config_summary()
    
    print("Rate Limiting Configuration Summary")
    print("=" * 40)
    for key, value in summary.items():
        print(f"{key}: {value}")
    
    print("\nEndpoint Limits:")
    print("-" * 20)
    for category, endpoints in config.get_all_limits().items():
        print(f"\n{category.upper()}:")
        for endpoint, limit in endpoints.items():
            print(f"  {endpoint}: {limit}")