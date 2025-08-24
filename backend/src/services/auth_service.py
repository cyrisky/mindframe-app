"""Authentication service for user management and security"""

import os
import jwt
import bcrypt
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from functools import wraps
from flask import request, jsonify, current_app, g
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
import redis
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AuthConfig:
    """Authentication configuration"""
    jwt_secret_key: str
    jwt_algorithm: str = 'HS256'
    access_token_expires: int = 3600  # 1 hour
    refresh_token_expires: int = 604800  # 7 days
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration: int = 1800  # 30 minutes
    session_timeout: int = 3600  # 1 hour
    require_email_verification: bool = True
    password_reset_expires: int = 3600  # 1 hour


class AuthService:
    """Service for authentication and authorization"""
    
    def __init__(self):
        self.config = None
        self.redis_client = None
        self.db_service = None
        self._initialized = False
    
    def initialize(self, config: AuthConfig = None, 
                   redis_client=None, db_service=None) -> bool:
        """Initialize authentication service"""
        try:
            # Use provided config or load from environment
            if config:
                self.config = config
            else:
                self.config = AuthConfig(
                    jwt_secret_key=os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32)),
                    jwt_algorithm=os.getenv('JWT_ALGORITHM', 'HS256'),
                    access_token_expires=int(os.getenv('ACCESS_TOKEN_EXPIRES', '3600')),
                    refresh_token_expires=int(os.getenv('REFRESH_TOKEN_EXPIRES', '604800')),
                    password_min_length=int(os.getenv('PASSWORD_MIN_LENGTH', '8')),
                    max_login_attempts=int(os.getenv('MAX_LOGIN_ATTEMPTS', '5')),
                    lockout_duration=int(os.getenv('LOCKOUT_DURATION', '1800')),
                    session_timeout=int(os.getenv('SESSION_TIMEOUT', '3600')),
                    require_email_verification=os.getenv('REQUIRE_EMAIL_VERIFICATION', 'true').lower() == 'true',
                    password_reset_expires=int(os.getenv('PASSWORD_RESET_EXPIRES', '3600'))
                )
            
            self.redis_client = redis_client
            self.db_service = db_service
            
            self._initialized = True
            logger.info("Authentication service initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize authentication service: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Perform authentication service health check"""
        try:
            health_info = {
                "status": "healthy",
                "jwt_configured": bool(self.config and self.config.jwt_secret_key),
                "redis_available": False,
                "database_available": False,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Check Redis connection
            if self.redis_client:
                try:
                    self.redis_client.ping()
                    health_info["redis_available"] = True
                except Exception as e:
                    health_info["redis_error"] = str(e)
            
            # Check database connection
            if self.db_service:
                try:
                    db_health = self.db_service.health_check()
                    health_info["database_available"] = db_health.get("status") == "healthy"
                except Exception as e:
                    health_info["database_error"] = str(e)
            
            return health_info
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Auth health check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Password utilities
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False
    
    def validate_password_strength(self, password: str) -> tuple[bool, list[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
        
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    # JWT token utilities
    def generate_access_token(self, user_id: str, email: str, 
                             roles: List[str] = None) -> str:
        """Generate JWT access token using Flask-JWT-Extended"""
        additional_claims = {
            'email': str(email),
            'roles': roles or [],
            'type': 'access'
        }
        
        return create_access_token(
            identity=str(user_id),
            additional_claims=additional_claims,
            expires_delta=timedelta(seconds=self.config.access_token_expires)
        )
    
    def generate_refresh_token(self, user_id: str) -> str:
        """Generate JWT refresh token using Flask-JWT-Extended"""
        additional_claims = {
            'type': 'refresh'
        }
        
        return create_refresh_token(
            identity=str(user_id),
            additional_claims=additional_claims,
            expires_delta=timedelta(seconds=self.config.refresh_token_expires)
        )
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token using Flask-JWT-Extended"""
        try:
            payload = decode_token(token)
            
            # Check if token is blacklisted
            if self.redis_client and self.is_token_blacklisted(token):
                return None
            
            return payload
            
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            return None
    
    def blacklist_token(self, token: str) -> bool:
        """Add token to blacklist"""
        if not self.redis_client:
            return False
        
        try:
            # Decode token to get expiration
            payload = jwt.decode(
                token, 
                self.config.jwt_secret_key, 
                algorithms=[self.config.jwt_algorithm],
                options={"verify_exp": False}
            )
            
            exp = payload.get('exp')
            if exp:
                # Calculate TTL until token expires
                exp_datetime = datetime.fromtimestamp(exp)
                ttl = int((exp_datetime - datetime.utcnow()).total_seconds())
                
                if ttl > 0:
                    self.redis_client.setex(f"blacklist:{token}", ttl, "1")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error blacklisting token: {e}")
            return False
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.exists(f"blacklist:{token}")
        except Exception as e:
            logger.error(f"Error checking token blacklist: {e}")
            return False
    
    # Login attempt tracking
    def record_login_attempt(self, email: str, success: bool, ip_address: str = None) -> bool:
        """Record login attempt"""
        if not self.redis_client:
            return False
        
        try:
            key = f"login_attempts:{email}"
            
            if success:
                # Clear failed attempts on successful login
                self.redis_client.delete(key)
                
                # Record successful login
                if ip_address:
                    self.redis_client.setex(
                        f"last_login:{email}", 
                        86400,  # 24 hours
                        f"{datetime.utcnow().isoformat()}|{ip_address}"
                    )
            else:
                # Increment failed attempts
                attempts = self.redis_client.incr(key)
                self.redis_client.expire(key, self.config.lockout_duration)
                
                # Lock account if max attempts reached
                if attempts >= self.config.max_login_attempts:
                    self.lock_account(email)
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording login attempt: {e}")
            return False
    
    def get_failed_login_attempts(self, email: str) -> int:
        """Get number of failed login attempts"""
        if not self.redis_client:
            return 0
        
        try:
            attempts = self.redis_client.get(f"login_attempts:{email}")
            return int(attempts) if attempts else 0
        except Exception as e:
            logger.error(f"Error getting failed login attempts: {e}")
            return 0
    
    def lock_account(self, email: str) -> bool:
        """Lock user account"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.setex(
                f"account_locked:{email}", 
                self.config.lockout_duration, 
                datetime.utcnow().isoformat()
            )
            logger.warning(f"Account locked: {email}")
            return True
        except Exception as e:
            logger.error(f"Error locking account: {e}")
            return False
    
    def is_account_locked(self, email: str) -> bool:
        """Check if account is locked"""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.exists(f"account_locked:{email}")
        except Exception as e:
            logger.error(f"Error checking account lock: {e}")
            return False
    
    def unlock_account(self, email: str) -> bool:
        """Unlock user account"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(f"account_locked:{email}")
            self.redis_client.delete(f"login_attempts:{email}")
            logger.info(f"Account unlocked: {email}")
            return True
        except Exception as e:
            logger.error(f"Error unlocking account: {e}")
            return False
    
    # Session management
    def create_session(self, user_id: str, session_data: Dict[str, Any]) -> str:
        """Create user session"""
        if not self.redis_client:
            return None
        
        try:
            session_id = secrets.token_urlsafe(32)
            session_key = f"session:{session_id}"
            
            session_info = {
                'user_id': user_id,
                'created_at': datetime.utcnow().isoformat(),
                'last_activity': datetime.utcnow().isoformat(),
                **session_data
            }
            
            self.redis_client.hmset(session_key, session_info)
            self.redis_client.expire(session_key, self.config.session_timeout)
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        if not self.redis_client:
            return None
        
        try:
            session_key = f"session:{session_id}"
            session_data = self.redis_client.hgetall(session_key)
            
            if session_data:
                # Update last activity
                self.redis_client.hset(session_key, 'last_activity', datetime.utcnow().isoformat())
                self.redis_client.expire(session_key, self.config.session_timeout)
                
                # Convert bytes to strings
                return {k.decode() if isinstance(k, bytes) else k: 
                       v.decode() if isinstance(v, bytes) else v 
                       for k, v in session_data.items()}
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session data"""
        if not self.redis_client:
            return False
        
        try:
            session_key = f"session:{session_id}"
            
            if self.redis_client.exists(session_key):
                data['last_activity'] = datetime.utcnow().isoformat()
                self.redis_client.hmset(session_key, data)
                self.redis_client.expire(session_key, self.config.session_timeout)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        if not self.redis_client:
            return False
        
        try:
            session_key = f"session:{session_id}"
            return bool(self.redis_client.delete(session_key))
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
    
    def extend_session(self, session_id: str) -> bool:
        """Extend session timeout"""
        if not self.redis_client:
            return False
        
        try:
            session_key = f"session:{session_id}"
            if self.redis_client.exists(session_key):
                self.redis_client.expire(session_key, self.config.session_timeout)
                return True
            return False
        except Exception as e:
            logger.error(f"Error extending session: {e}")
            return False
    
    # Password reset
    def generate_password_reset_token(self, user_id: str, email: str) -> str:
        """Generate password reset token"""
        if not self.redis_client:
            return None
        
        try:
            token = secrets.token_urlsafe(32)
            reset_key = f"password_reset:{token}"
            
            reset_data = {
                'user_id': user_id,
                'email': email,
                'created_at': datetime.utcnow().isoformat()
            }
            
            self.redis_client.hmset(reset_key, reset_data)
            self.redis_client.expire(reset_key, self.config.password_reset_expires)
            
            return token
            
        except Exception as e:
            logger.error(f"Error generating password reset token: {e}")
            return None
    
    def verify_password_reset_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify password reset token"""
        if not self.redis_client:
            return None
        
        try:
            reset_key = f"password_reset:{token}"
            reset_data = self.redis_client.hgetall(reset_key)
            
            if reset_data:
                # Convert bytes to strings
                return {k.decode() if isinstance(k, bytes) else k: 
                       v.decode() if isinstance(v, bytes) else v 
                       for k, v in reset_data.items()}
            
            return None
            
        except Exception as e:
            logger.error(f"Error verifying password reset token: {e}")
            return None
    
    def invalidate_password_reset_token(self, token: str) -> bool:
        """Invalidate password reset token"""
        if not self.redis_client:
            return False
        
        try:
            reset_key = f"password_reset:{token}"
            return bool(self.redis_client.delete(reset_key))
        except Exception as e:
            logger.error(f"Error invalidating password reset token: {e}")
            return False
    
    # API key management
    def generate_api_key(self, user_id: str, name: str = None) -> str:
        """Generate API key for user"""
        api_key = f"mk_{secrets.token_urlsafe(32)}"
        
        if self.redis_client:
            try:
                api_key_data = {
                    'user_id': user_id,
                    'name': name or 'Default API Key',
                    'created_at': datetime.utcnow().isoformat(),
                    'last_used': None,
                    'usage_count': 0
                }
                
                self.redis_client.hmset(f"api_key:{api_key}", api_key_data)
                # API keys don't expire by default
                
            except Exception as e:
                logger.error(f"Error storing API key: {e}")
        
        return api_key
    
    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify API key and return user info"""
        if not self.redis_client or not api_key.startswith('mk_'):
            return None
        
        try:
            api_key_data = self.redis_client.hgetall(f"api_key:{api_key}")
            
            if api_key_data:
                # Update usage statistics
                self.redis_client.hset(f"api_key:{api_key}", 'last_used', datetime.utcnow().isoformat())
                self.redis_client.hincrby(f"api_key:{api_key}", 'usage_count', 1)
                
                # Convert bytes to strings
                return {k.decode() if isinstance(k, bytes) else k: 
                       v.decode() if isinstance(v, bytes) else v 
                       for k, v in api_key_data.items()}
            
            return None
            
        except Exception as e:
            logger.error(f"Error verifying API key: {e}")
            return None
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke API key"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(f"api_key:{api_key}"))
        except Exception as e:
            logger.error(f"Error revoking API key: {e}")
            return False
    
    # User authentication
    def register_user(self, email: str, password: str, first_name: str = None, 
                      last_name: str = None, role: str = 'user') -> Dict[str, Any]:
        """Register a new user"""
        try:
            # Check if user already exists
            existing_user = self.db_service.find_one('users', {'email': email})
            if existing_user:
                return {
                    'success': False,
                    'error': 'User with this email already exists'
                }
            
            # Validate password strength
            is_valid, errors = self.validate_password_strength(password)
            if not is_valid:
                return {
                    'success': False,
                    'error': f"Password validation failed: {', '.join(errors)}"
                }
            
            # Hash password
            password_hash = self.hash_password(password)
            
            # Create user document
            from ..models.user_model import User, UserPreferences, UserQuota
            
            # Generate username from email if not provided
            username = email.split('@')[0]
            counter = 1
            original_username = username
            while self.db_service.find_one('users', {'username': username}):
                username = f"{original_username}{counter}"
                counter += 1
            
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                salt='',  # bcrypt handles salt internally
                first_name=first_name,
                last_name=last_name,
                roles=[role] if role else ['user'],
                preferences=UserPreferences(),
                quota=UserQuota()
            )
            
            # Convert to dict and insert into database
            user_dict = user.to_dict()
            user_id = self.db_service.insert_one('users', user_dict)
            
            logger.info(f"User registered successfully: {email}")
            return {
                'success': True,
                'user_id': str(user_id),
                'message': 'User registered successfully'
            }
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return {
                'success': False,
                'error': 'Registration failed'
            }

    def login_user(self, email: str, password: str, ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """Login user with email and password"""
        try:
            # Check if account is locked
            if self.is_account_locked(email):
                return {
                    'success': False,
                    'error': 'Account is temporarily locked due to too many failed login attempts'
                }
            
            # Get user from database
            user_data = self.db_service.find_one('users', {'email': email})
            if not user_data:
                self.record_login_attempt(email, False, ip_address)
                return {
                    'success': False,
                    'error': 'Invalid email or password'
                }
            
            # Verify password
            if not self.verify_password(password, user_data['password_hash']):
                self.record_login_attempt(email, False, ip_address)
                return {
                    'success': False,
                    'error': 'Invalid email or password'
                }
            
            # Check if user is active
            if not user_data.get('is_active', True):
                return {
                    'success': False,
                    'error': 'Account is deactivated'
                }
            
            # Record successful login
            self.record_login_attempt(email, True, ip_address)
            
            # Generate tokens
            access_token = self.generate_access_token(
                user_data['_id'], 
                user_data['email'],
                user_data.get('roles', [])
            )
            refresh_token = self.generate_refresh_token(user_data['_id'])
            
            # Create session
            session_id = self.create_session(user_data['_id'], {
                'ip_address': ip_address,
                'user_agent': user_agent,
                'login_time': datetime.utcnow().isoformat()
            })
            
            return {
                'success': True,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'session_id': session_id,
                'user': {
                    'id': str(user_data['_id']),
                    'email': user_data['email'],
                    'first_name': user_data.get('first_name'),
                    'last_name': user_data.get('last_name'),
                    'roles': user_data.get('roles', [])
                }
            }
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {
                'success': False,
                'error': 'Login failed'
            }
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = self.verify_token(refresh_token)
            if not payload:
                return {
                    'success': False,
                    'error': 'Invalid or expired refresh token'
                }
            
            # Check if it's actually a refresh token
            if payload.get('type') != 'refresh':
                return {
                    'success': False,
                    'error': 'Invalid token type'
                }
            
            user_id = payload.get('sub')
            if not user_id:
                return {
                    'success': False,
                    'error': 'Invalid token payload'
                }
            
            # Get user data from database
            if self.db_service:
                user_data = self.db_service.get_user(user_id)
                if not user_data:
                    return {
                        'success': False,
                        'error': 'User not found'
                    }
                
                # Generate new access token
                new_access_token = self.generate_access_token(
                    user_id=user_id,
                    email=user_data.get('email', ''),
                    roles=user_data.get('roles', [])
                )
                
                return {
                    'success': True,
                    'access_token': new_access_token,
                    'user': {
                        'id': user_id,
                        'email': user_data.get('email'),
                        'first_name': user_data.get('first_name'),
                        'last_name': user_data.get('last_name'),
                        'roles': user_data.get('roles', [])
                    }
                }
            else:
                # Fallback if no db_service (generate token with minimal data)
                new_access_token = self.generate_access_token(
                    user_id=user_id,
                    email='',  # Will need to be populated from token or DB
                    roles=[]
                )
                
                return {
                    'success': True,
                    'access_token': new_access_token,
                    'user': {
                        'id': user_id
                    }
                }
                
        except Exception as e:
            logger.error(f"Refresh token error: {e}")
            return {
                'success': False,
                'error': 'Token refresh failed'
            }
    
    # Decorators for route protection
    def require_auth(self, f):
        """Decorator to require authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = None
            
            # Check for token in Authorization header
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            
            # Check for API key
            api_key = request.headers.get('X-API-Key')
            if api_key:
                api_key_data = self.verify_api_key(api_key)
                if api_key_data:
                    g.current_user = {'user_id': api_key_data['user_id'], 'auth_type': 'api_key'}
                    return f(*args, **kwargs)
            
            if not token:
                return jsonify({'error': 'Authentication required'}), 401
            
            payload = self.verify_token(token)
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            g.current_user = payload
            return f(*args, **kwargs)
        
        return decorated_function
    
    def require_roles(self, roles: List[str]):
        """Decorator to require specific roles"""
        def roles_decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not hasattr(g, 'current_user') or not g.current_user:
                    return jsonify({'error': 'Authentication required'}), 401
                
                user_roles = g.current_user.get('roles', [])
                if not any(role in user_roles for role in roles):
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                return f(*args, **kwargs)
            return decorated_function
        return roles_decorator
    
    def require_permission(self, permission: str):
        """Decorator to require specific permission"""
        def permission_decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not hasattr(g, 'current_user') or not g.current_user:
                    return jsonify({'error': 'Authentication required'}), 401
                
                # This would need to be implemented based on your permission system
                # For now, just check if user has admin role
                user_roles = g.current_user.get('roles', [])
                if 'admin' not in user_roles:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                return f(*args, **kwargs)
            return decorated_function
        return permission_decorator


# Global auth service instance
auth_service = AuthService()