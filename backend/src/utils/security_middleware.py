"""Security middleware for Flask application"""

from flask import Flask, request, g
from typing import Dict, Any, Optional, List
import os
from datetime import datetime


class SecurityMiddleware:
    """Security middleware for adding security headers and protections"""
    
    def __init__(self, app: Optional[Flask] = None, config: Optional[Dict[str, Any]] = None):
        """Initialize security middleware
        
        Args:
            app: Flask application instance
            config: Security configuration dictionary
        """
        self.app = app
        self.config = config or {}
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask) -> None:
        """Initialize security middleware with Flask app
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Load configuration from app config or environment
        self._load_config()
        
        # Register security headers middleware
        app.after_request(self._add_security_headers)
        
        # Register request security checks
        app.before_request(self._security_checks)
    
    def _load_config(self) -> None:
        """Load security configuration from app config and environment"""
        default_config = {
            # Content Security Policy
            'CSP_ENABLED': True,
            'CSP_POLICY': {
                'default-src': ["'self'"],
                'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
                'style-src': ["'self'", "'unsafe-inline'"],
                'img-src': ["'self'", "data:", "https:"],
                'font-src': ["'self'", "https:"],
                'connect-src': ["'self'"],
                'frame-ancestors': ["'none'"],
                'base-uri': ["'self'"],
                'form-action': ["'self'"]
            },
            
            # HTTP Strict Transport Security
            'HSTS_ENABLED': True,
            'HSTS_MAX_AGE': 31536000,  # 1 year
            'HSTS_INCLUDE_SUBDOMAINS': True,
            'HSTS_PRELOAD': True,
            
            # X-Frame-Options
            'X_FRAME_OPTIONS': 'DENY',
            
            # X-Content-Type-Options
            'X_CONTENT_TYPE_OPTIONS': 'nosniff',
            
            # X-XSS-Protection
            'X_XSS_PROTECTION': '1; mode=block',
            
            # Referrer Policy
            'REFERRER_POLICY': 'strict-origin-when-cross-origin',
            
            # Permissions Policy
            'PERMISSIONS_POLICY_ENABLED': True,
            'PERMISSIONS_POLICY': {
                'geolocation': [],
                'microphone': [],
                'camera': [],
                'payment': [],
                'usb': [],
                'magnetometer': [],
                'gyroscope': [],
                'speaker': []
            },
            
            # Security checks
            'FORCE_HTTPS': os.getenv('FORCE_HTTPS', 'false').lower() == 'true',
            'ALLOWED_HOSTS': os.getenv('ALLOWED_HOSTS', '').split(',') if os.getenv('ALLOWED_HOSTS') else [],
            'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
            
            # Rate limiting headers
            'RATE_LIMIT_HEADERS': True
        }
        
        # Update with app config
        for key, value in default_config.items():
            self.config[key] = self.app.config.get(f'SECURITY_{key}', 
                                                  os.getenv(f'SECURITY_{key}', value))
    
    def _add_security_headers(self, response):
        """Add security headers to response
        
        Args:
            response: Flask response object
            
        Returns:
            Flask response object with security headers
        """
        # Content Security Policy
        if self.config.get('CSP_ENABLED'):
            csp_policy = self._build_csp_policy()
            response.headers['Content-Security-Policy'] = csp_policy
        
        # HTTP Strict Transport Security (only for HTTPS)
        if self.config.get('HSTS_ENABLED') and request.is_secure:
            hsts_value = f"max-age={self.config['HSTS_MAX_AGE']}"
            if self.config.get('HSTS_INCLUDE_SUBDOMAINS'):
                hsts_value += "; includeSubDomains"
            if self.config.get('HSTS_PRELOAD'):
                hsts_value += "; preload"
            response.headers['Strict-Transport-Security'] = hsts_value
        
        # X-Frame-Options
        if self.config.get('X_FRAME_OPTIONS'):
            response.headers['X-Frame-Options'] = self.config['X_FRAME_OPTIONS']
        
        # X-Content-Type-Options
        if self.config.get('X_CONTENT_TYPE_OPTIONS'):
            response.headers['X-Content-Type-Options'] = self.config['X_CONTENT_TYPE_OPTIONS']
        
        # X-XSS-Protection
        if self.config.get('X_XSS_PROTECTION'):
            response.headers['X-XSS-Protection'] = self.config['X_XSS_PROTECTION']
        
        # Referrer Policy
        if self.config.get('REFERRER_POLICY'):
            response.headers['Referrer-Policy'] = self.config['REFERRER_POLICY']
        
        # Permissions Policy
        if self.config.get('PERMISSIONS_POLICY_ENABLED'):
            permissions_policy = self._build_permissions_policy()
            if permissions_policy:
                response.headers['Permissions-Policy'] = permissions_policy
        
        # Remove server header for security
        response.headers.pop('Server', None)
        
        # Add custom security headers
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
        
        return response
    
    def _security_checks(self) -> None:
        """Perform security checks before processing request"""
        # Force HTTPS in production
        if self.config.get('FORCE_HTTPS') and not request.is_secure:
            if request.headers.get('X-Forwarded-Proto') != 'https':
                from flask import abort
                abort(426)  # Upgrade Required
        
        # Check allowed hosts
        allowed_hosts = self.config.get('ALLOWED_HOSTS')
        if allowed_hosts and request.host not in allowed_hosts:
            from flask import abort
            abort(400)  # Bad Request
        
        # Check content length
        max_length = self.config.get('MAX_CONTENT_LENGTH')
        if max_length and request.content_length and request.content_length > max_length:
            from flask import abort
            abort(413)  # Payload Too Large
        
        # Add request ID for tracking
        if not hasattr(g, 'request_id'):
            import uuid
            g.request_id = str(uuid.uuid4())
    
    def _build_csp_policy(self) -> str:
        """Build Content Security Policy string
        
        Returns:
            str: CSP policy string
        """
        csp_policy = self.config.get('CSP_POLICY', {})
        policy_parts = []
        
        for directive, sources in csp_policy.items():
            if sources:
                sources_str = ' '.join(sources)
                policy_parts.append(f"{directive} {sources_str}")
            else:
                policy_parts.append(f"{directive} 'none'")
        
        return '; '.join(policy_parts)
    
    def _build_permissions_policy(self) -> str:
        """Build Permissions Policy string
        
        Returns:
            str: Permissions Policy string
        """
        permissions_policy = self.config.get('PERMISSIONS_POLICY', {})
        policy_parts = []
        
        for feature, allowlist in permissions_policy.items():
            if allowlist:
                allowlist_str = ' '.join(f'"{origin}"' for origin in allowlist)
                policy_parts.append(f"{feature}=({allowlist_str})")
            else:
                policy_parts.append(f"{feature}=()")
        
        return ', '.join(policy_parts)
    
    def update_csp_policy(self, directive: str, sources: List[str]) -> None:
        """Update CSP policy directive
        
        Args:
            directive: CSP directive name
            sources: List of allowed sources
        """
        if 'CSP_POLICY' not in self.config:
            self.config['CSP_POLICY'] = {}
        
        self.config['CSP_POLICY'][directive] = sources
    
    def add_csp_source(self, directive: str, source: str) -> None:
        """Add source to CSP directive
        
        Args:
            directive: CSP directive name
            source: Source to add
        """
        if 'CSP_POLICY' not in self.config:
            self.config['CSP_POLICY'] = {}
        
        if directive not in self.config['CSP_POLICY']:
            self.config['CSP_POLICY'][directive] = []
        
        if source not in self.config['CSP_POLICY'][directive]:
            self.config['CSP_POLICY'][directive].append(source)
    
    def get_security_report(self) -> Dict[str, Any]:
        """Get security configuration report
        
        Returns:
            Dict: Security configuration report
        """
        return {
            'csp_enabled': self.config.get('CSP_ENABLED'),
            'hsts_enabled': self.config.get('HSTS_ENABLED'),
            'force_https': self.config.get('FORCE_HTTPS'),
            'allowed_hosts': self.config.get('ALLOWED_HOSTS'),
            'max_content_length': self.config.get('MAX_CONTENT_LENGTH'),
            'security_headers': {
                'x_frame_options': self.config.get('X_FRAME_OPTIONS'),
                'x_content_type_options': self.config.get('X_CONTENT_TYPE_OPTIONS'),
                'x_xss_protection': self.config.get('X_XSS_PROTECTION'),
                'referrer_policy': self.config.get('REFERRER_POLICY')
            }
        }


# Convenience function for easy setup
def setup_security_middleware(app: Flask, config: Optional[Dict[str, Any]] = None) -> SecurityMiddleware:
    """Setup security middleware for Flask app
    
    Args:
        app: Flask application instance
        config: Optional security configuration
        
    Returns:
        SecurityMiddleware: Configured security middleware instance
    """
    return SecurityMiddleware(app, config)