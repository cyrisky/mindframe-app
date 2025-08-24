# Mindframe Backend API Documentation

## Overview

The Mindframe Backend API is a comprehensive Flask-based REST API that provides services for psychological reporting, user authentication, template management, and PDF generation. The API follows RESTful principles and uses JWT-based authentication.

**Base URL**: `http://localhost:5001` (development)
**API Version**: v1
**Authentication**: JWT Bearer Token

## Table of Contents

1. [Authentication](#authentication)
2. [Health Monitoring](#health-monitoring)
3. [User Management](#user-management)
4. [Template Management](#template-management)
5. [Report Management](#report-management)
6. [PDF Generation](#pdf-generation)
7. [Assessment APIs](#assessment-apis)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [Request/Response Examples](#request-response-examples)

---

## Authentication

The API uses JWT (JSON Web Token) based authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Authentication Endpoints

#### POST `/api/auth/register`
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user_id": "64f1a2b3c4d5e6f7g8h9i0j1",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Validation Rules:**
- Email must be valid format
- Password minimum 8 characters with uppercase, lowercase, digit, and special character
- Names can only contain letters, spaces, hyphens, and apostrophes
- Role must be one of: `admin`, `user`, `moderator`, `psychologist`

#### POST `/api/auth/login`
Authenticate user and receive access tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "remember_me": false
}
```

**Response:**
```json
{
  "message": "Login successful",
  "user": {
    "id": "64f1a2b3c4d5e6f7g8h9i0j1",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### POST `/api/auth/refresh`
Refresh access token using refresh token.

**Headers:**
```
Authorization: Bearer <refresh-token>
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "expires_in": 3600
}
```

#### POST `/api/auth/logout`
Logout user and invalidate tokens.

**Headers:**
```
Authorization: Bearer <access-token>
```

**Response:**
```json
{
  "message": "Logout successful"
}
```

#### GET `/api/auth/profile`
Get current user profile.

**Headers:**
```
Authorization: Bearer <access-token>
```

**Response:**
```json
{
  "user": {
    "id": "64f1a2b3c4d5e6f7g8h9i0j1",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "display_name": "John Doe",
    "role": "user",
    "created_at": "2024-01-15T10:30:00Z",
    "last_login": "2024-01-20T14:22:00Z"
  }
}
```

#### PUT `/api/auth/profile`
Update user profile.

**Headers:**
```
Authorization: Bearer <access-token>
```

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "display_name": "John Smith",
  "bio": "Psychologist specializing in personality assessments",
  "timezone": "America/New_York",
  "language": "en-US"
}
```

#### POST `/api/auth/change-password`
Change user password.

**Headers:**
```
Authorization: Bearer <access-token>
```

**Request Body:**
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewSecurePass456!"
}
```

#### POST `/api/auth/forgot-password`
Request password reset email.

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

#### POST `/api/auth/reset-password`
Reset password with token.

**Request Body:**
```json
{
  "token": "reset-token-from-email",
  "new_password": "NewSecurePass456!"
}
```

#### POST `/api/auth/verify-email`
Verify email address with token.

**Request Body:**
```json
{
  "token": "verification-token-from-email"
}
```

#### GET `/api/auth/sessions`
List active user sessions.

**Headers:**
```
Authorization: Bearer <access-token>
```

**Response:**
```json
{
  "sessions": [
    {
      "id": "session-id-1",
      "device": "Chrome on Windows",
      "ip_address": "192.168.1.100",
      "last_activity": "2024-01-20T14:22:00Z",
      "current": true
    }
  ]
}
```

#### DELETE `/api/auth/sessions/<session_id>`
Revoke specific session.

**Headers:**
```
Authorization: Bearer <access-token>
```

---

## Health Monitoring

### Health Check Endpoints

#### GET `/health`
Basic health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T14:22:00Z",
  "service": "mindframe-api",
  "version": "1.0.0"
}
```

#### GET `/health/detailed`
Detailed health check with service dependencies.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-20T14:22:00Z",
  "service": "mindframe-api",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "MongoDB connection successful"
    },
    "redis": {
      "status": "healthy",
      "message": "Redis connection successful"
    },
    "filesystem": {
      "status": "healthy",
      "message": "File system access successful"
    },
    "pdf_generation": {
      "status": "healthy",
      "message": "WeasyPrint PDF generation available"
    },
    "google_drive": {
      "status": "healthy",
      "message": "Google Drive integration configured"
    }
  }
}
```

#### GET `/health/readiness`
Readiness probe for container orchestration.

#### GET `/health/liveness`
Liveness probe for container orchestration.

#### GET `/health/version`
Get API version information.

---

## Template Management

### Template Endpoints

#### GET `/api/templates`
List templates with filtering and pagination.

**Headers:**
```
Authorization: Bearer <access-token>
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20, max: 100)
- `search` (string): Search query
- `category` (string): Filter by category (`personality`, `values`, `assessment`, `report`, `custom`)
- `sort_by` (string): Sort field (default: `created_at`)
- `sort_order` (string): Sort order (`asc`, `desc`)

**Response:**
```json
{
  "templates": [
    {
      "id": "64f1a2b3c4d5e6f7g8h9i0j1",
      "name": "Personality Assessment Report",
      "description": "Comprehensive personality assessment template",
      "category": "personality",
      "variables": [
        {
          "name": "patient_name",
          "type": "string",
          "required": true,
          "description": "Patient full name"
        }
      ],
      "tags": ["personality", "assessment"],
      "is_public": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-18T16:45:00Z",
      "created_by": "64f1a2b3c4d5e6f7g8h9i0j2"
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 20,
  "has_more": true
}
```

#### POST `/api/templates`
Create a new template.

**Headers:**
```
Authorization: Bearer <access-token>
```

**Request Body:**
```json
{
  "name": "New Assessment Template",
  "description": "Template for psychological assessments",
  "content": "<html><body><h1>{{patient_name}}</h1><p>{{assessment_results}}</p></body></html>",
  "category": "assessment",
  "variables": [
    {
      "name": "patient_name",
      "type": "string",
      "description": "Patient full name",
      "required": true
    },
    {
      "name": "assessment_results",
      "type": "object",
      "description": "Assessment results data",
      "required": true
    }
  ],
  "tags": ["assessment", "psychology"],
  "is_public": false
}
```

#### GET `/api/templates/<template_id>`
Get specific template details.

**Headers:**
```
Authorization: Bearer <access-token>
```

#### PUT `/api/templates/<template_id>`
Update existing template.

**Headers:**
```
Authorization: Bearer <access-token>
```

#### DELETE `/api/templates/<template_id>`
Delete template.

**Headers:**
```
Authorization: Bearer <access-token>
```

#### POST `/api/templates/<template_id>/render`
Render template with data.

**Headers:**
```
Authorization: Bearer <access-token>
```

**Request Body:**
```json
{
  "variables": {
    "patient_name": "John Doe",
    "assessment_results": {
      "score": 85,
      "category": "High Extraversion"
    }
  }
}
```

#### POST `/api/templates/<template_id>/preview`
Preview template rendering.

#### GET `/api/templates/<template_id>/variables`
Get template variable definitions.

#### POST `/api/templates/<template_id>/validate`
Validate data against template.

#### POST `/api/templates/<template_id>/duplicate`
Duplicate existing template.

#### GET `/api/templates/categories`
Get available template categories.

#### GET `/api/templates/statistics`
Get template usage statistics.

---

## Report Management

### Report Endpoints

#### GET `/api/reports`
List reports with filtering and pagination.

**Headers:**
```
Authorization: Bearer <access-token>
```

**Query Parameters:**
- `page` (int): Page number
- `limit` (int): Items per page
- `search` (string): Search query
- `status` (string): Filter by status
- `created_after` (datetime): Filter by creation date
- `created_before` (datetime): Filter by creation date

**Response:**
```json
{
  "reports": [
    {
      "id": "64f1a2b3c4d5e6f7g8h9i0j1",
      "title": "John Doe - Personality Assessment",
      "description": "Comprehensive personality evaluation",
      "template_id": "64f1a2b3c4d5e6f7g8h9i0j2",
      "status": "completed",
      "data": {
        "patient_name": "John Doe",
        "assessment_date": "2024-01-20"
      },
      "tags": ["personality", "assessment"],
      "is_public": false,
      "created_at": "2024-01-20T10:30:00Z",
      "updated_at": "2024-01-20T14:22:00Z",
      "created_by": "64f1a2b3c4d5e6f7g8h9i0j3"
    }
  ],
  "total": 15,
  "page": 1,
  "limit": 20,
  "has_more": false
}
```

#### POST `/api/reports`
Create a new report.

**Headers:**
```
Authorization: Bearer <access-token>
```

**Request Body:**
```json
{
  "title": "Patient Assessment Report",
  "description": "Psychological assessment for patient",
  "template_id": "64f1a2b3c4d5e6f7g8h9i0j2",
  "data": {
    "patient_name": "Jane Smith",
    "assessment_date": "2024-01-20",
    "results": {
      "extraversion": 75,
      "neuroticism": 45
    }
  },
  "tags": ["assessment", "personality"],
  "is_public": false
}
```

#### GET `/api/reports/<report_id>`
Get specific report details.

#### PUT `/api/reports/<report_id>`
Update existing report.

#### DELETE `/api/reports/<report_id>`
Delete report.

#### POST `/api/reports/<report_id>/generate-pdf`
Generate PDF from report.

**Response:**
```json
{
  "pdf_url": "/api/pdf/download/report-64f1a2b3c4d5e6f7g8h9i0j1.pdf",
  "file_size": 245760,
  "generated_at": "2024-01-20T14:22:00Z"
}
```

#### PUT `/api/reports/<report_id>/status`
Update report status.

**Request Body:**
```json
{
  "status": "completed",
  "notes": "Report finalized and reviewed"
}
```

#### POST `/api/reports/<report_id>/test-results`
Add test results to report.

#### GET `/api/reports/<report_id>/viewers`
Get authorized viewers for report.

#### POST `/api/reports/<report_id>/viewers`
Add authorized viewer to report.

#### DELETE `/api/reports/<report_id>/viewers/<user_id>`
Remove authorized viewer from report.

#### POST `/api/reports/<report_id>/duplicate`
Duplicate existing report.

#### POST `/api/reports/batch-generate`
Generate multiple reports in batch.

**Request Body:**
```json
{
  "reports": [
    {
      "patient_id": "patient-1",
      "template_id": "64f1a2b3c4d5e6f7g8h9i0j2",
      "title": "Patient 1 Assessment",
      "data": {
        "patient_name": "Patient One"
      }
    }
  ]
}
```

---

## PDF Generation

### PDF Endpoints

#### POST `/api/pdf/generate`
Generate PDF from HTML content.

**Headers:**
```
Authorization: Bearer <access-token>
```

**Request Body:**
```json
{
  "html_content": "<html><body><h1>Report Title</h1><p>Content here</p></body></html>",
  "css_content": "body { font-family: Arial, sans-serif; }",
  "options": {
    "page_size": "A4",
    "orientation": "portrait",
    "margin": "1in"
  }
}
```

**Response:**
```json
{
  "pdf_url": "/api/pdf/download/generated-64f1a2b3c4d5e6f7g8h9i0j1.pdf",
  "file_size": 245760,
  "generated_at": "2024-01-20T14:22:00Z"
}
```

#### POST `/api/pdf/generate-from-template`
Generate PDF from template.

**Request Body:**
```json
{
  "template_name": "personality-assessment",
  "data": {
    "patient_name": "John Doe",
    "assessment_results": {
      "extraversion": 75
    }
  },
  "options": {
    "page_size": "A4"
  }
}
```

#### POST `/api/pdf/generate-report`
Generate psychological report PDF.

**Request Body:**
```json
{
  "patient_info": {
    "name": "John Doe",
    "age": 35,
    "gender": "male"
  },
  "test_results": [
    {
      "test_name": "Big Five Personality",
      "scores": {
        "extraversion": 75,
        "neuroticism": 45
      }
    }
  ],
  "template_options": {
    "include_charts": true,
    "detailed_analysis": true
  }
}
```

#### GET `/api/pdf/download/<filename>`
Download generated PDF file.

#### GET `/api/pdf/list`
List available PDF files.

#### DELETE `/api/pdf/<filename>`
Delete PDF file.

#### GET `/api/pdf/templates`
List available PDF templates.

#### GET `/api/pdf/templates/<template_name>/preview`
Preview PDF template.

---

## Assessment APIs

### Personality Assessment

#### GET `/api/personality/health`
Health check for personality service.

#### POST `/api/personality/validate`
Validate personality assessment data.

#### POST `/api/personality/preview`
Preview personality report.

#### POST `/api/personality/generate-pdf`
Generate personality assessment PDF.

#### POST `/api/personality/generate-html`
Generate personality assessment HTML.

#### POST `/api/personality/mongo-to-pdf`
Convert MongoDB personality data to PDF.

#### GET `/api/personality/dimensions`
Get personality dimensions information.

### Personal Values Assessment

#### GET `/api/personal-values/health`
Health check for personal values service.

#### POST `/api/personal-values/validate`
Validate personal values assessment data.

#### POST `/api/personal-values/preview`
Preview personal values report.

#### POST `/api/personal-values/generate-pdf`
Generate personal values assessment PDF.

---

## Error Handling

### Standard Error Response Format

```json
{
  "error": "ValidationError",
  "message": "Invalid input data",
  "details": {
    "field": "email",
    "issue": "Invalid email format"
  },
  "status_code": 400,
  "timestamp": "2024-01-20T14:22:00Z"
}
```

### HTTP Status Codes

- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Common Error Types

- `ValidationError` - Input validation failed
- `AuthenticationError` - Authentication failed
- `AuthorizationError` - Insufficient permissions
- `ResourceNotFoundError` - Requested resource not found
- `ConflictError` - Resource already exists
- `RateLimitError` - Too many requests

---

## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Authentication endpoints**: 5 requests per minute
- **PDF generation**: 10 requests per minute
- **General API**: 100 requests per minute
- **File uploads**: 20 requests per hour

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642694400
```

---

## Request/Response Examples

### Complete Authentication Flow

1. **Register User**
```bash
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

2. **Login**
```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePass123!"
  }'
```

3. **Access Protected Endpoint**
```bash
curl -X GET http://localhost:5001/api/auth/profile \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

### Template and Report Workflow

1. **Create Template**
```bash
curl -X POST http://localhost:5001/api/templates \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Assessment Template",
    "content": "<h1>{{patient_name}}</h1><p>Score: {{score}}</p>",
    "category": "assessment",
    "variables": [
      {"name": "patient_name", "type": "string", "required": true},
      {"name": "score", "type": "number", "required": true}
    ]
  }'
```

2. **Create Report**
```bash
curl -X POST http://localhost:5001/api/reports \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Patient Assessment",
    "template_id": "<template-id>",
    "data": {
      "patient_name": "John Doe",
      "score": 85
    }
  }'
```

3. **Generate PDF**
```bash
curl -X POST http://localhost:5001/api/reports/<report-id>/generate-pdf \
  -H "Authorization: Bearer <token>"
```

### PDF Generation

```bash
curl -X POST http://localhost:5001/api/pdf/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "html_content": "<html><body><h1>Test Report</h1></body></html>",
    "options": {
      "page_size": "A4",
      "orientation": "portrait"
    }
  }'
```

---

## Security Considerations

1. **Authentication**: All protected endpoints require valid JWT tokens
2. **Authorization**: Role-based access control (RBAC) for sensitive operations
3. **Input Validation**: Comprehensive validation using Pydantic models
4. **Rate Limiting**: Prevents API abuse and DoS attacks
5. **CORS**: Configured for frontend integration
6. **Security Headers**: HSTS, CSP, and other security headers implemented
7. **Password Security**: Bcrypt hashing with salt
8. **Session Management**: Secure session handling with Redis

---

## Development and Testing

### Running the API

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Start services
brew services start mongodb-community
brew services start redis

# Run the API
PORT=5001 python3 app.py
```

### Testing Endpoints

```bash
# Health check
curl http://localhost:5001/health

# Detailed health check
curl http://localhost:5001/health/detailed

# Test authentication
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password"}'
```

### Running Tests

```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v

# All tests
python -m pytest tests/ -v
```

---

## Support and Contact

For API support and questions:
- Documentation: This file
- Health Status: `GET /health/detailed`
- Version Info: `GET /health/version`

**Note**: This API is currently in development. Features and endpoints may change.