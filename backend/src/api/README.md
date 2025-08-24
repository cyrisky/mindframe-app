# API Directory

This directory contains the REST API layer of the Mindframe application, providing HTTP endpoints for client applications to interact with the system's functionality.

## Overview

The API is built using Flask and follows a modular blueprint architecture. It provides endpoints for authentication, PDF generation, psychological reports, templates, and assessment tools.

## Architecture

### Application Structure
```
api/
├── app.py                      # Flask application factory
├── __init__.py                 # API module exports
├── personality_api.py          # Personality assessment API
├── personal_values_api.py      # Personal values assessment API
└── routes/                     # Modular route blueprints
    ├── __init__.py            # Route exports
    ├── auth_routes.py         # Authentication endpoints
    ├── health_routes.py       # Health check endpoints
    ├── pdf_routes.py          # PDF generation endpoints
    ├── report_routes.py       # Psychological report endpoints
    └── template_routes.py     # Template management endpoints
```

### Flask Application Factory
The `app.py` file contains the Flask application factory pattern:

```python
from api.app import create_app

# Create application instance
app = create_app('development')

# Run application
if __name__ == '__main__':
    app.run(debug=True)
```

## API Endpoints

### 🔐 Authentication API (`/api/auth`)
**Blueprint**: `auth_routes.py`

| Method | Endpoint                    | Description               | Auth Required |
| ------ | --------------------------- | ------------------------- | ------------- |
| POST   | `/api/auth/register`        | User registration         | No            |
| POST   | `/api/auth/login`           | User login                | No            |
| POST   | `/api/auth/logout`          | User logout               | Yes           |
| POST   | `/api/auth/refresh`         | Refresh JWT token         | Yes           |
| GET    | `/api/auth/profile`         | Get user profile          | Yes           |
| PUT    | `/api/auth/profile`         | Update user profile       | Yes           |
| POST   | `/api/auth/change-password` | Change password           | Yes           |
| POST   | `/api/auth/forgot-password` | Request password reset    | No            |
| POST   | `/api/auth/reset-password`  | Reset password with token | No            |
| POST   | `/api/auth/verify-email`    | Verify email address      | No            |
| GET    | `/api/auth/sessions`        | List user sessions        | Yes           |
| DELETE | `/api/auth/sessions/<id>`   | Revoke session            | Yes           |

**Example Usage**:
```bash
# Register new user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'

# Login user
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

### 🏥 Health Check API (`/health`)
**Blueprint**: `health_routes.py`

| Method | Endpoint           | Description                       | Auth Required |
| ------ | ------------------ | --------------------------------- | ------------- |
| GET    | `/health`          | Basic health check                | No            |
| GET    | `/health/detailed` | Detailed health with dependencies | No            |

**Example Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "mindframe-api",
  "version": "1.0.0",
  "checks": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "storage": {"status": "healthy"}
  }
}
```

### 📄 PDF Generation API (`/api/pdf`)
**Blueprint**: `pdf_routes.py`

| Method | Endpoint                          | Description                   | Auth Required |
| ------ | --------------------------------- | ----------------------------- | ------------- |
| POST   | `/api/pdf/generate`               | Generate PDF from HTML        | No*           |
| POST   | `/api/pdf/generate-from-template` | Generate PDF from template    | No*           |
| GET    | `/api/pdf/documents`              | List PDF documents            | Yes           |
| GET    | `/api/pdf/documents/<id>`         | Get PDF document              | Yes           |
| DELETE | `/api/pdf/documents/<id>`         | Delete PDF document           | Yes           |
| GET    | `/api/pdf/download/<id>`          | Download PDF file             | Yes           |
| GET    | `/api/pdf/status/<task_id>`       | Check async generation status | No            |

*Rate limited and may require API key

**Example Usage**:
```bash
# Generate PDF from HTML
curl -X POST http://localhost:5000/api/pdf/generate \
  -H "Content-Type: application/json" \
  -d '{
    "html_content": "<html><body><h1>Hello World</h1></body></html>",
    "options": {
      "page_size": "A4",
      "orientation": "portrait"
    }
  }'

# Generate PDF from template
curl -X POST http://localhost:5000/api/pdf/generate-from-template \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "psychological_report",
    "variables": {
      "client_name": "John Doe",
      "date": "2024-01-15"
    }
  }'
```

### 📊 Reports API (`/api/reports`)
**Blueprint**: `report_routes.py`

| Method | Endpoint                         | Description                | Auth Required |
| ------ | -------------------------------- | -------------------------- | ------------- |
| GET    | `/api/reports`                   | List psychological reports | Yes           |
| POST   | `/api/reports`                   | Create new report          | Yes           |
| GET    | `/api/reports/<id>`              | Get specific report        | Yes           |
| PUT    | `/api/reports/<id>`              | Update report              | Yes           |
| DELETE | `/api/reports/<id>`              | Delete report              | Yes           |
| POST   | `/api/reports/<id>/generate-pdf` | Generate PDF for report    | Yes           |
| POST   | `/api/reports/<id>/test-results` | Add test results           | Yes           |
| PUT    | `/api/reports/<id>/status`       | Update report status       | Yes           |
| POST   | `/api/reports/<id>/viewers`      | Add authorized viewer      | Yes           |
| GET    | `/api/reports/statistics`        | Get report statistics      | Yes           |

**Example Usage**:
```bash
# Create psychological report
curl -X POST http://localhost:5000/api/reports \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt_token>" \
  -d '{
    "client_information": {
      "name": "John Doe",
      "age": 30,
      "gender": "male"
    },
    "report_type": "comprehensive",
    "assessment_date": "2024-01-15"
  }'
```

### 🎨 Templates API (`/api/templates`)
**Blueprint**: `template_routes.py`

| Method | Endpoint                        | Description               | Auth Required |
| ------ | ------------------------------- | ------------------------- | ------------- |
| GET    | `/api/templates`                | List templates            | Yes           |
| POST   | `/api/templates`                | Create new template       | Yes           |
| GET    | `/api/templates/<id>`           | Get specific template     | Yes           |
| PUT    | `/api/templates/<id>`           | Update template           | Yes           |
| DELETE | `/api/templates/<id>`           | Delete template           | Yes           |
| POST   | `/api/templates/<id>/render`    | Render template with data | Yes           |
| POST   | `/api/templates/<id>/preview`   | Preview template          | Yes           |
| GET    | `/api/templates/<id>/variables` | Get template variables    | Yes           |
| GET    | `/api/templates/categories`     | List template categories  | Yes           |

**Example Usage**:
```bash
# Create template
curl -X POST http://localhost:5000/api/templates \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt_token>" \
  -d '{
    "name": "Assessment Report",
    "category": "psychological",
    "html_content": "<html><body><h1>{{title}}</h1></body></html>",
    "variables": [
      {"name": "title", "type": "string", "required": true}
    ]
  }'
```

### 🧠 Personality Assessment API (`/api/personality`)
**Standalone API**: `personality_api.py`

| Method | Endpoint                         | Description                     | Auth Required |
| ------ | -------------------------------- | ------------------------------- | ------------- |
| GET    | `/api/personality/health`        | Health check                    | No            |
| POST   | `/api/personality/validate`      | Validate MongoDB payload        | No            |
| POST   | `/api/personality/preview`       | Preview assessment data         | No            |
| POST   | `/api/personality/generate-pdf`  | Generate personality PDF        | No            |
| POST   | `/api/personality/generate-html` | Generate personality HTML       | No            |
| POST   | `/api/personality/mongo-to-pdf`  | Convert MongoDB data to PDF     | No            |
| GET    | `/api/personality/dimensions`    | Get personality dimensions info | No            |

**Example Usage**:
```bash
# Generate personality assessment PDF
curl -X POST http://localhost:5001/api/personality/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "mongoData": {
      "user_id": "123",
      "assessment_results": {...}
    },
    "options": {
      "customOutputName": "personality_report.pdf"
    }
  }'
```

### 💎 Personal Values API (`/api/personal-values`)
**Standalone API**: `personal_values_api.py`

| Method | Endpoint                            | Description              | Auth Required |
| ------ | ----------------------------------- | ------------------------ | ------------- |
| GET    | `/api/personal-values/health`       | Health check             | No            |
| POST   | `/api/personal-values/validate`     | Validate MongoDB payload | No            |
| POST   | `/api/personal-values/preview`      | Preview values data      | No            |
| POST   | `/api/personal-values/generate-pdf` | Generate values PDF      | No            |

**Example Usage**:
```bash
# Generate personal values PDF
curl -X POST http://localhost:5000/api/personal-values/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "mongoData": {
      "user_id": "123",
      "values_assessment": {...}
    }
  }'
```

## Authentication & Authorization

### JWT Token Authentication
Most endpoints require JWT authentication:

```bash
# Include JWT token in Authorization header
curl -H "Authorization: Bearer <jwt_token>" \
     http://localhost:5000/api/protected-endpoint
```

### API Key Authentication
Some endpoints support API key authentication:

```bash
# Include API key in header
curl -H "X-API-Key: <api_key>" \
     http://localhost:5000/api/pdf/generate
```

### Role-Based Access Control
Endpoints may require specific roles:

- **Admin**: Full system access
- **Psychologist**: Report creation and management
- **User**: Basic access to own data
- **Moderator**: Content moderation capabilities

## Request/Response Format

### Standard Request Format
```json
{
  "data": {
    // Request payload
  },
  "options": {
    // Optional parameters
  }
}
```

### Standard Response Format
```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Operation completed successfully",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response Format
```json
{
  "success": false,
  "error": "error_code",
  "message": "Human readable error message",
  "details": {
    // Additional error details
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Rate Limiting

API endpoints implement rate limiting to prevent abuse:

- **Authentication endpoints**: 5 requests per minute
- **PDF generation**: 10 requests per minute
- **General endpoints**: 100 requests per minute
- **Health checks**: No limit

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
```

## Error Handling

### HTTP Status Codes
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Common Error Codes
```json
{
  "INVALID_REQUEST": "Request data is invalid",
  "AUTHENTICATION_REQUIRED": "Authentication token required",
  "INSUFFICIENT_PERMISSIONS": "User lacks required permissions",
  "RESOURCE_NOT_FOUND": "Requested resource not found",
  "VALIDATION_ERROR": "Input validation failed",
  "RATE_LIMIT_EXCEEDED": "Too many requests",
  "INTERNAL_ERROR": "Internal server error occurred"
}
```

## CORS Configuration

CORS is configured to allow requests from:
- `http://localhost:3000` (React development server)
- `http://localhost:3001` (Alternative frontend port)
- Production domains (configured via environment variables)

## Environment Configuration

### Required Environment Variables
```bash
# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key

# Database
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=mindframe_app

# Redis
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES=3600

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Storage
STORAGE_TYPE=local
STORAGE_PATH=/path/to/storage

# API Configuration
API_RATE_LIMIT_ENABLED=true
API_KEY_REQUIRED=false
```

## Development Setup

### Running the API Server
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=True

# Run main API server
python -m api.app

# Run personality API (separate server)
python -m api.personality_api

# Run personal values API (separate server)
python -m api.personal_values_api
```

### API Testing
```bash
# Test health endpoint
curl http://localhost:5000/health

# Test with authentication
curl -H "Authorization: Bearer <token>" \
     http://localhost:5000/api/reports

# Test PDF generation
curl -X POST http://localhost:5000/api/pdf/generate \
  -H "Content-Type: application/json" \
  -d '{"html_content": "<h1>Test</h1>"}'
```

## API Documentation

### Interactive Documentation
The API provides interactive documentation via:
- Swagger UI: `http://localhost:5000/docs`
- ReDoc: `http://localhost:5000/redoc`
- OpenAPI Spec: `http://localhost:5000/openapi.json`

### Postman Collection
A Postman collection is available at `docs/api/mindframe-api.postman_collection.json`

## Security Best Practices

### Input Validation
- All inputs are validated using Pydantic models
- SQL injection prevention through parameterized queries
- XSS prevention through output encoding
- File upload restrictions and scanning

### Authentication Security
- JWT tokens with short expiration times
- Refresh token rotation
- Account lockout after failed attempts
- Password strength requirements
- Rate limiting on authentication endpoints

### API Security
- HTTPS enforcement in production
- CORS configuration
- Request size limits
- API versioning for backward compatibility
- Security headers (HSTS, CSP, etc.)

## Monitoring & Logging

### Request Logging
All API requests are logged with:
- Request method and URL
- User ID (if authenticated)
- IP address and user agent
- Response status and duration
- Error details (if applicable)

### Health Monitoring
```bash
# Check API health
curl http://localhost:5000/health/detailed

# Monitor specific services
curl http://localhost:5000/health/database
curl http://localhost:5000/health/redis
```

### Metrics Collection
- Request count and duration
- Error rates by endpoint
- Authentication success/failure rates
- PDF generation statistics
- Database query performance

## Performance Optimization

### Caching Strategy
- Redis caching for frequently accessed data
- Template caching for PDF generation
- User session caching
- API response caching for static data

### Async Operations
- PDF generation uses background tasks
- Email sending is queued
- Large file uploads are chunked
- Database operations are optimized

### Load Balancing
- Multiple API server instances
- Database connection pooling
- Redis connection pooling
- CDN for static assets

## Testing

### Unit Tests
```bash
# Run API unit tests
pytest tests/api/

# Run with coverage
pytest --cov=api tests/api/
```

### Integration Tests
```bash
# Run integration tests
pytest tests/integration/

# Test specific endpoints
pytest tests/integration/test_auth_api.py
```

### Load Testing
```bash
# Install artillery
npm install -g artillery

# Run load tests
artillery run tests/load/api-load-test.yml
```

## Deployment

### Production Configuration
```bash
# Production environment variables
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=<strong-production-secret>

# Database (production)
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/

# Redis (production)
REDIS_URL=redis://production-redis:6379

# Security
HTTPS_ONLY=true
SECURE_COOKIES=true
```

### Docker Deployment
```dockerfile
# Dockerfile for API
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "api.app:create_app()"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mindframe-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mindframe-api
  template:
    metadata:
      labels:
        app: mindframe-api
    spec:
      containers:
      - name: api
        image: mindframe/api:latest
        ports:
        - containerPort: 5000
        env:
        - name: MONGODB_URI
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: uri
```

## Troubleshooting

### Common Issues

**API Server Won't Start**:
- Check environment variables
- Verify database connectivity
- Review application logs
- Ensure port availability

**Authentication Failures**:
- Verify JWT secret configuration
- Check token expiration
- Review user permissions
- Validate request headers

**PDF Generation Errors**:
- Check template syntax
- Verify required variables
- Review file permissions
- Monitor memory usage

**Database Connection Issues**:
- Verify MongoDB URI
- Check network connectivity
- Review authentication credentials
- Monitor connection pool

### Debug Mode
```bash
# Enable debug logging
export FLASK_DEBUG=True
export LOG_LEVEL=DEBUG

# Run with verbose output
python -m api.app --debug
```

### Log Analysis
```bash
# View API logs
tail -f logs/api.log

# Filter error logs
grep "ERROR" logs/api.log

# Monitor specific endpoint
grep "/api/pdf/generate" logs/api.log
```

## Contributing

### Adding New Endpoints
1. Create or update blueprint in `routes/`
2. Implement endpoint with proper validation
3. Add authentication/authorization decorators
4. Write unit and integration tests
5. Update API documentation
6. Add to this README

### Code Standards
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Add docstrings for all endpoints
- Implement proper error handling
- Add request/response validation

### API Versioning
- Use URL versioning: `/api/v1/endpoint`
- Maintain backward compatibility
- Document breaking changes
- Provide migration guides

For more detailed information about specific components, refer to:
- Authentication: `../AUTH_README.md`
- Services: `../services/README.md`
- Models: `../models/README.md`