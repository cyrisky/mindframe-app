#!/usr/bin/env python3
"""
Rate Limiting Demo

This module demonstrates how to use the rate limiting middleware
with various decorators and configurations.
"""

from flask import Blueprint, jsonify, request, g
from src.utils.rate_limiter import get_rate_limit_decorators, get_rate_limiter
from src.utils.exceptions import ValidationError

# Create demo blueprint
rate_limit_demo_bp = Blueprint('rate_limit_demo', __name__, url_prefix='/api/demo/rate-limit')


def init_rate_limit_demo_routes(app):
    """Initialize rate limiting demo routes"""
    
    # Get rate limit decorators
    decorators = get_rate_limit_decorators(app)
    rate_limiter = get_rate_limiter(app)
    
    if not decorators or not rate_limiter:
        app.logger.warning("Rate limiting not available for demo routes")
        return
    
    @rate_limit_demo_bp.route('/standard', methods=['GET'])
    @decorators.api_standard  # 100 requests per hour
    def standard_endpoint():
        """Standard API endpoint with 100 req/hour limit"""
        return jsonify({
            'success': True,
            'message': 'Standard rate limited endpoint',
            'limit': '100 requests per hour',
            'key': g.get('rate_limit_key', 'unknown')
        })
    
    @rate_limit_demo_bp.route('/strict', methods=['GET'])
    @decorators.api_strict  # 50 requests per hour
    def strict_endpoint():
        """Strict API endpoint with 50 req/hour limit"""
        return jsonify({
            'success': True,
            'message': 'Strict rate limited endpoint',
            'limit': '50 requests per hour',
            'key': g.get('rate_limit_key', 'unknown')
        })
    
    @rate_limit_demo_bp.route('/auth-simulation', methods=['POST'])
    @decorators.auth_endpoints  # 10 requests per minute
    def auth_simulation():
        """Simulated authentication endpoint with 10 req/min limit"""
        return jsonify({
            'success': True,
            'message': 'Authentication simulation',
            'limit': '10 requests per minute',
            'key': g.get('rate_limit_key', 'unknown')
        })
    
    @rate_limit_demo_bp.route('/upload-simulation', methods=['POST'])
    @decorators.upload_endpoints  # 5 requests per minute
    def upload_simulation():
        """Simulated file upload endpoint with 5 req/min limit"""
        return jsonify({
            'success': True,
            'message': 'Upload simulation',
            'limit': '5 requests per minute',
            'key': g.get('rate_limit_key', 'unknown')
        })
    
    @rate_limit_demo_bp.route('/heavy-computation', methods=['POST'])
    @decorators.heavy_computation  # 20 requests per hour
    def heavy_computation_simulation():
        """Simulated heavy computation endpoint with 20 req/hour limit"""
        return jsonify({
            'success': True,
            'message': 'Heavy computation simulation',
            'limit': '20 requests per hour',
            'key': g.get('rate_limit_key', 'unknown')
        })
    
    @rate_limit_demo_bp.route('/public', methods=['GET'])
    @decorators.public_endpoints  # 1000 requests per hour
    def public_endpoint():
        """Public endpoint with 1000 req/hour limit"""
        return jsonify({
            'success': True,
            'message': 'Public endpoint',
            'limit': '1000 requests per hour',
            'key': g.get('rate_limit_key', 'unknown')
        })
    
    @rate_limit_demo_bp.route('/custom-limit', methods=['GET'])
    @decorators.custom_limit('30/hour;5/minute')  # Multiple limits
    def custom_limit_endpoint():
        """Custom rate limit with multiple constraints"""
        return jsonify({
            'success': True,
            'message': 'Custom rate limited endpoint',
            'limit': '30 per hour AND 5 per minute',
            'key': g.get('rate_limit_key', 'unknown')
        })
    
    @rate_limit_demo_bp.route('/user-based', methods=['GET'])
    @decorators.user_based_limit('100/hour')  # Per authenticated user
    def user_based_endpoint():
        """User-based rate limiting (requires authentication)"""
        # Simulate user authentication
        g.user_id = request.headers.get('X-User-ID', 'anonymous')
        
        return jsonify({
            'success': True,
            'message': 'User-based rate limited endpoint',
            'limit': '100 requests per hour per user',
            'user_id': g.user_id,
            'key': g.get('rate_limit_key', 'unknown')
        })
    
    @rate_limit_demo_bp.route('/conditional', methods=['GET'])
    @decorators.conditional_limit(
        '10/minute',
        condition=lambda: request.headers.get('X-Premium-User') != 'true'
    )
    def conditional_endpoint():
        """Conditional rate limiting (only for non-premium users)"""
        is_premium = request.headers.get('X-Premium-User') == 'true'
        
        return jsonify({
            'success': True,
            'message': 'Conditional rate limited endpoint',
            'limit': 'None (premium user)' if is_premium else '10 requests per minute',
            'is_premium': is_premium,
            'key': g.get('rate_limit_key', 'unknown')
        })
    
    @rate_limit_demo_bp.route('/shared-limit-a', methods=['GET'])
    @rate_limiter.shared_limit('50/hour', scope='shared_demo')
    def shared_limit_a():
        """Endpoint A sharing rate limit with endpoint B"""
        return jsonify({
            'success': True,
            'message': 'Shared rate limit endpoint A',
            'limit': '50 requests per hour (shared with endpoint B)',
            'endpoint': 'A',
            'key': g.get('rate_limit_key', 'unknown')
        })
    
    @rate_limit_demo_bp.route('/shared-limit-b', methods=['GET'])
    @rate_limiter.shared_limit('50/hour', scope='shared_demo')
    def shared_limit_b():
        """Endpoint B sharing rate limit with endpoint A"""
        return jsonify({
            'success': True,
            'message': 'Shared rate limit endpoint B',
            'limit': '50 requests per hour (shared with endpoint A)',
            'endpoint': 'B',
            'key': g.get('rate_limit_key', 'unknown')
        })
    
    @rate_limit_demo_bp.route('/no-limit', methods=['GET'])
    def no_limit_endpoint():
        """Endpoint with no specific rate limit (uses global defaults)"""
        return jsonify({
            'success': True,
            'message': 'No specific rate limit (uses global defaults)',
            'limit': 'Global defaults: 500/hour, 50/minute',
            'key': g.get('rate_limit_key', 'unknown')
        })
    
    @rate_limit_demo_bp.route('/status', methods=['GET'])
    def rate_limit_status():
        """Get current rate limit status"""
        from src.utils.rate_limiter import get_rate_limit_status
        
        status = get_rate_limit_status()
        
        return jsonify({
            'success': True,
            'message': 'Rate limit status',
            'status': status,
            'key': g.get('rate_limit_key', 'unknown')
        })
    
    @rate_limit_demo_bp.route('/test-violation', methods=['GET'])
    @rate_limiter.limit('1/minute')  # Very restrictive for testing
    def test_violation():
        """Endpoint to test rate limit violations (1 req/min)"""
        return jsonify({
            'success': True,
            'message': 'Rate limit violation test endpoint',
            'limit': '1 request per minute (for testing violations)',
            'key': g.get('rate_limit_key', 'unknown'),
            'warning': 'Call this endpoint multiple times to test rate limiting'
        })
    
    # Register the blueprint
    app.register_blueprint(rate_limit_demo_bp)
    
    app.logger.info("Rate limiting demo routes initialized")


# Usage examples for different scenarios
class RateLimitingExamples:
    """Examples of different rate limiting patterns"""
    
    @staticmethod
    def api_endpoint_pattern():
        """Standard API endpoint pattern"""
        """
        @api_bp.route('/users', methods=['GET'])
        @decorators.api_standard  # 100 requests per hour
        def get_users():
            # Implementation
            pass
        """
        pass
    
    @staticmethod
    def authentication_pattern():
        """Authentication endpoint pattern"""
        """
        @auth_bp.route('/login', methods=['POST'])
        @decorators.auth_endpoints  # 10 requests per minute
        def login():
            # Implementation
            pass
        
        @auth_bp.route('/register', methods=['POST'])
        @decorators.auth_endpoints  # 10 requests per minute
        def register():
            # Implementation
            pass
        """
        pass
    
    @staticmethod
    def file_upload_pattern():
        """File upload endpoint pattern"""
        """
        @upload_bp.route('/files', methods=['POST'])
        @decorators.upload_endpoints  # 5 requests per minute
        def upload_file():
            # Implementation
            pass
        """
        pass
    
    @staticmethod
    def heavy_computation_pattern():
        """Heavy computation endpoint pattern"""
        """
        @report_bp.route('/generate', methods=['POST'])
        @decorators.heavy_computation  # 20 requests per hour
        def generate_report():
            # Implementation
            pass
        """
        pass
    
    @staticmethod
    def custom_limit_pattern():
        """Custom rate limit pattern"""
        """
        @api_bp.route('/special', methods=['POST'])
        @decorators.custom_limit('15/hour;3/minute')  # Multiple constraints
        def special_endpoint():
            # Implementation
            pass
        """
        pass
    
    @staticmethod
    def user_based_pattern():
        """User-based rate limiting pattern"""
        """
        @api_bp.route('/user-data', methods=['GET'])
        @decorators.user_based_limit('200/hour')  # Per authenticated user
        def get_user_data():
            # Implementation (requires authentication middleware)
            pass
        """
        pass
    
    @staticmethod
    def conditional_pattern():
        """Conditional rate limiting pattern"""
        """
        @api_bp.route('/premium-feature', methods=['GET'])
        @decorators.conditional_limit(
            '10/hour',
            condition=lambda: not is_premium_user()
        )
        def premium_feature():
            # Implementation
            pass
        """
        pass
    
    @staticmethod
    def shared_limit_pattern():
        """Shared rate limit pattern"""
        """
        @api_bp.route('/resource-a', methods=['GET'])
        @rate_limiter.shared_limit('100/hour', scope='resource_access')
        def get_resource_a():
            # Implementation
            pass
        
        @api_bp.route('/resource-b', methods=['GET'])
        @rate_limiter.shared_limit('100/hour', scope='resource_access')
        def get_resource_b():
            # Implementation (shares limit with resource-a)
            pass
        """
        pass
    
    @staticmethod
    def blueprint_exemption_pattern():
        """Blueprint exemption pattern"""
        """
        # Exempt entire admin blueprint from rate limiting
        rate_limiter.exempt(admin_bp)
        
        # Or exempt specific routes
        @admin_bp.route('/health', methods=['GET'])
        def health_check():
            # This endpoint is exempt from rate limiting
            pass
        """
        pass


if __name__ == '__main__':
    print("Rate Limiting Demo")
    print("==================")
    print("")
    print("This module demonstrates various rate limiting patterns:")
    print("")
    print("1. Standard API limits (100/hour)")
    print("2. Strict API limits (50/hour)")
    print("3. Authentication limits (10/minute)")
    print("4. Upload limits (5/minute)")
    print("5. Heavy computation limits (20/hour)")
    print("6. Public endpoint limits (1000/hour)")
    print("7. Custom limits with multiple constraints")
    print("8. User-based limits (per authenticated user)")
    print("9. Conditional limits (based on user type)")
    print("10. Shared limits (across multiple endpoints)")
    print("11. Global default limits (500/hour, 50/minute)")
    print("12. Rate limit violation testing")
    print("")
    print("Test endpoints:")
    print("- GET  /api/demo/rate-limit/standard")
    print("- GET  /api/demo/rate-limit/strict")
    print("- POST /api/demo/rate-limit/auth-simulation")
    print("- POST /api/demo/rate-limit/upload-simulation")
    print("- POST /api/demo/rate-limit/heavy-computation")
    print("- GET  /api/demo/rate-limit/public")
    print("- GET  /api/demo/rate-limit/custom-limit")
    print("- GET  /api/demo/rate-limit/user-based")
    print("- GET  /api/demo/rate-limit/conditional")
    print("- GET  /api/demo/rate-limit/shared-limit-a")
    print("- GET  /api/demo/rate-limit/shared-limit-b")
    print("- GET  /api/demo/rate-limit/no-limit")
    print("- GET  /api/demo/rate-limit/status")
    print("- GET  /api/demo/rate-limit/test-violation")