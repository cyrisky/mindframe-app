# Authentication System

This document provides a comprehensive overview of the authentication system implemented in the Mindframe application backend.

## Overview

The authentication system provides secure user registration, login, session management, and role-based access control using JWT tokens and MongoDB for data persistence.

## Architecture

The authentication system is distributed across several components:

- **Models** (`models/user_model.py`): User data structures and validation
- **Services** (`services/auth_service.py`): Business logic for authentication operations
- **API Routes** (`api/routes/auth_routes.py`): HTTP endpoints for authentication
- **Middleware** (`utils/decorators.py`): Route protection and authorization
- **Database**: MongoDB collection `mindframe.auth` for user storage

## Features

### Core Authentication
- ✅ User registration with email validation
- ✅ Secure password hashing using bcrypt
- ✅ JWT-based authentication (access + refresh tokens)
- ✅ User login/logout with session tracking
- ✅ Password strength validation
- ✅ Role-based access control

### Advanced Features
- ✅ Password reset via email
- ✅ Email verification
- ✅ Session management and revocation
- ✅ Rate limiting on authentication endpoints
- ✅ API key authentication
- ✅ Fresh token requirements for sensitive operations

## Database Schema

### MongoDB Collection: `mindframe.auth`

User documents are stored with the following structure:

```json
{
  "_id": "ObjectId",
  "email": "user@example.com",
  "password_hash": "$2b$12$...",
  "salt": "random_salt_string",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user",
  "is_verified": true,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "last_login": {
    "timestamp": "2024-01-01T00:00:00Z",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0..."
  },
  "preferences": {
    "theme": "light",
    "language": "en",
    "notifications": {
      "email": true,
      "push": false
    }
  },
  "quota": {
    "reports_generated": 5,
    "max_reports": 100,
    "storage_used": 1024,
    "max_storage": 1073741824
  }
}
```

## API Endpoints

All authentication endpoints are prefixed with `/api/auth`:

### Public Endpoints (No Authentication Required)

#### POST `/register`
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user" // optional, defaults to "user"
}
```

**Response (201):**
```json
{
  "success": true,
  "message": "User registered successfully",
  "user_id": "507f1f77bcf86cd799439011"
}
```

#### POST `/login`
Authenticate user and receive tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Login successful",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user"
  }
}
```

#### POST `/refresh`
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response (200):**
```json
{
  "success": true,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### POST `/forgot-password`
Request password reset email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "If the email exists, a password reset link has been sent"
}
```

#### POST `/reset-password`
Reset password using reset token.

**Request Body:**
```json
{
  "token": "reset_token_here",
  "new_password": "NewSecurePassword123!"
}
```

#### POST `/verify-email`
Verify email address using verification token.

**Request Body:**
```json
{
  "token": "verification_token_here"
}
```

### Protected Endpoints (Authentication Required)

#### POST `/logout`
Logout user and invalidate token.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

#### GET `/profile`
Get current user profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "success": true,
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user",
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-01T00:00:00Z"
  }
}
```

#### PUT `/profile`
Update user profile.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith"
}
```

#### POST `/change-password`
Change user password.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "current_password": "CurrentPassword123!",
  "new_password": "NewSecurePassword123!"
}
```

#### GET `/sessions`
Get user's active sessions.

**Headers:**
```
Authorization: Bearer <access_token>
```

#### DELETE `/sessions/<session_id>`
Revoke a specific session.

**Headers:**
```
Authorization: Bearer <access_token>
```

## Authentication Middleware

The system provides several decorators for route protection:

### Basic Authentication
```python
from utils.decorators import require_auth

@app.route('/protected')
@require_auth()
def protected_route():
    # Access current user via request.current_user
    return jsonify({'user_id': request.current_user['_id']})
```

### Role-Based Access Control
```python
from utils.decorators import require_roles, admin_required, user_required

@app.route('/admin-only')
@admin_required
def admin_only():
    return jsonify({'message': 'Admin access granted'})

@app.route('/user-or-admin')
@user_required
def user_or_admin():
    return jsonify({'message': 'User access granted'})

@app.route('/custom-roles')
@require_roles(['moderator', 'admin'])
def custom_roles():
    return jsonify({'message': 'Moderator or admin access'})
```

### Fresh Token Requirements
```python
from utils.decorators import require_fresh_auth

@app.route('/sensitive-operation')
@require_fresh_auth
def sensitive_operation():
    # Requires recently authenticated token
    return jsonify({'message': 'Sensitive operation allowed'})
```

### Optional Authentication
```python
from utils.decorators import optional_auth

@app.route('/public-or-private')
@optional_auth
def public_or_private():
    # Works with or without authentication
    user = getattr(request, 'current_user', None)
    if user:
        return jsonify({'message': f'Hello {user["first_name"]}'})
    return jsonify({'message': 'Hello anonymous user'})
```

### Rate Limiting
```python
from utils.decorators import rate_limit

@app.route('/limited')
@rate_limit('10 per minute')
def limited_endpoint():
    return jsonify({'message': 'Rate limited endpoint'})
```

### API Key Authentication
```python
from utils.decorators import require_api_key

@app.route('/api-endpoint')
@require_api_key
def api_endpoint():
    return jsonify({'message': 'API key validated'})
```

## Security Features

### Password Security
- **Hashing**: bcrypt with configurable rounds (default: 12)
- **Salt**: Unique salt per password
- **Strength Validation**: Minimum length, complexity requirements
- **Reset Tokens**: Secure, time-limited password reset tokens

### JWT Security
- **Access Tokens**: Short-lived (15 minutes default)
- **Refresh Tokens**: Longer-lived (7 days default)
- **Token Revocation**: Blacklist support for logout
- **Fresh Tokens**: Required for sensitive operations
- **Custom Claims**: Role and permission information

### Rate Limiting
- **IP-based**: Tracks requests per IP address
- **Configurable**: Support for per-second, per-minute, per-hour, per-day limits
- **Thread-safe**: Uses locks for concurrent access
- **Production Ready**: Designed for Redis backend (currently in-memory)

### Session Management
- **Session Tracking**: IP address, user agent, timestamp
- **Session Revocation**: Individual session termination
- **Multi-device Support**: Multiple concurrent sessions
- **Security Logging**: Failed login attempts, suspicious activity

## Configuration

### Environment Variables
```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ACCESS_TOKEN_EXPIRES=900  # 15 minutes
JWT_REFRESH_TOKEN_EXPIRES=604800  # 7 days

# Database Configuration
MONGO_URI=mongodb://localhost:27017/mindframe
MONGO_AUTH_COLLECTION=mindframe.auth

# Email Configuration (for password reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# API Keys (comma-separated)
VALID_API_KEYS=key1,key2,key3

# Security
BCRYPT_ROUNDS=12
RATE_LIMIT_STORAGE=redis  # or 'memory' for development
```

### Flask-JWT-Extended Setup
```python
from flask_jwt_extended import JWTManager

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 900)))
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 604800)))

jwt = JWTManager(app)
```

## Error Handling

The authentication system provides consistent error responses:

### Common Error Codes
- **400**: Bad Request (validation errors, missing fields)
- **401**: Unauthorized (invalid credentials, expired tokens)
- **403**: Forbidden (insufficient permissions)
- **422**: Unprocessable Entity (malformed JWT)
- **429**: Too Many Requests (rate limit exceeded)
- **500**: Internal Server Error

### Error Response Format
```json
{
  "success": false,
  "error": "Error type",
  "message": "Human-readable error message",
  "details": ["Additional error details"]  // optional
}
```

## Testing

### Example Test Cases
```python
import pytest
from your_app import app

def test_user_registration():
    with app.test_client() as client:
        response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'SecurePassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        })
        assert response.status_code == 201
        assert response.json['success'] is True

def test_user_login():
    with app.test_client() as client:
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'SecurePassword123!'
        })
        assert response.status_code == 200
        assert 'access_token' in response.json
```

## Monitoring and Logging

### Security Events Logged
- User registration attempts
- Login successes and failures
- Password change attempts
- Token refresh operations
- Rate limit violations
- Invalid API key attempts
- Session revocations

### Log Format
```
2024-01-01 12:00:00 [INFO] User registered successfully: user@example.com
2024-01-01 12:01:00 [WARNING] Login failed for user@example.com: Invalid password
2024-01-01 12:02:00 [WARNING] Rate limit exceeded for 192.168.1.1: 11 requests
```

## Best Practices

### For Developers
1. **Always use HTTPS** in production
2. **Validate input** on both client and server
3. **Use fresh tokens** for sensitive operations
4. **Implement proper error handling**
5. **Log security events** for monitoring
6. **Rotate JWT secrets** regularly
7. **Use environment variables** for configuration

### For Frontend Integration
1. **Store tokens securely** (httpOnly cookies recommended)
2. **Handle token expiration** gracefully
3. **Implement automatic token refresh**
4. **Clear tokens on logout**
5. **Validate user permissions** before showing UI elements

## Troubleshooting

### Common Issues

#### "Token has expired"
- **Cause**: Access token has exceeded its lifetime
- **Solution**: Use refresh token to get new access token

#### "Invalid authorization header"
- **Cause**: Malformed Authorization header
- **Solution**: Ensure format is `Bearer <token>`

#### "Rate limit exceeded"
- **Cause**: Too many requests from same IP
- **Solution**: Wait for rate limit window to reset

#### "User not found"
- **Cause**: User doesn't exist in database
- **Solution**: Check email spelling, ensure user is registered

### Debug Mode
Enable debug logging to troubleshoot authentication issues:

```python
import logging
logging.getLogger('auth_service').setLevel(logging.DEBUG)
```

## Migration Notes

When migrating from the simple API server:

1. **Update route decorators** to use new authentication middleware
2. **Replace manual token validation** with `@require_auth`
3. **Update error handling** to use consistent format
4. **Configure JWT settings** in environment variables
5. **Test all protected endpoints** with new authentication

## Contributing

When contributing to the authentication system:

1. **Follow security best practices**
2. **Add tests for new features**
3. **Update documentation**
4. **Consider backward compatibility**
5. **Review security implications**

---

**Last Updated**: January 2024  
**Version**: 1.0.0  
**Maintainer**: Mindframe Development Team