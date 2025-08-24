# Services Directory

This directory contains the business logic layer of the Mindframe application. Services handle complex operations, external integrations, and coordinate between different components of the system.

## Overview

The services layer follows a modular architecture where each service is responsible for a specific domain of functionality. All services implement a common initialization pattern and provide health check capabilities for monitoring.

## Core Services

### 🔐 AuthService (`auth_service.py`)
**Purpose**: Authentication and authorization management

**Key Features**:
- User authentication (login/logout)
- JWT token generation and validation
- Password hashing and verification
- Session management
- Account lockout protection
- API key management
- Role-based access control
- Password reset functionality

**Dependencies**: Redis, Database Service

**Usage Example**:
```python
from services import AuthService

auth_service = AuthService()
auth_service.initialize(config, redis_client, db_service)

# Login user
result = auth_service.login_user(email, password, ip_address)
if result['success']:
    access_token = result['access_token']
```

### 🗄️ DatabaseService (`database_service.py`)
**Purpose**: MongoDB database operations and connection management

**Key Features**:
- MongoDB connection management
- CRUD operations abstraction
- Index management
- Connection pooling
- Health monitoring
- Backup and restore utilities
- Aggregation pipeline support

**Usage Example**:
```python
from services import DatabaseService

db_service = DatabaseService()
db_service.initialize(connection_string, database_name)

# Insert document
doc_id = db_service.insert_one('users', user_data)

# Find documents
users = db_service.find_many('users', {'status': 'active'})
```

### 📧 EmailService (`email_service.py`)
**Purpose**: Email notifications and communication

**Key Features**:
- SMTP email sending
- HTML and text email templates
- Attachment support
- Template rendering with variables
- Email queue management
- Delivery status tracking
- Multiple email providers support

**Usage Example**:
```python
from services import EmailService

email_service = EmailService()
email_service.initialize(email_config)

# Send email
email_service.send_email(
    to=['user@example.com'],
    subject='Welcome!',
    template='welcome',
    variables={'name': 'John'}
)
```

### 📄 PDFService (`pdf_service.py`)
**Purpose**: PDF generation and document management

**Key Features**:
- HTML to PDF conversion
- Template-based PDF generation
- Psychological report generation
- Asynchronous PDF processing
- Document storage and retrieval
- Generation statistics
- Cleanup utilities

**Dependencies**: Template Service, Storage Service, Email Service

**Usage Example**:
```python
from services import PDFService

pdf_service = PDFService()
pdf_service.initialize(db_service, storage_service)

# Generate PDF from template
result = pdf_service.generate_pdf_from_template(
    template_name='report_template',
    variables={'client_name': 'John Doe'},
    user_id='user123'
)
```

### 📊 ReportService (`report_service.py`)
**Purpose**: Psychological report management and operations

**Key Features**:
- Report creation and management
- Test result integration
- Report status tracking
- PDF generation coordination
- Access control and sharing
- Report statistics and analytics
- Data validation and integrity

**Dependencies**: PDF Service, Template Service, Auth Service

**Usage Example**:
```python
from services import ReportService

report_service = ReportService()
report_service.initialize(db_service, pdf_service, template_service)

# Create psychological report
report = report_service.create_report({
    'client_information': client_data,
    'report_type': 'comprehensive',
    'test_results': test_data
}, user_id='psychologist123')
```

### 🎨 TemplateService (`template_service.py`)
**Purpose**: HTML template management and rendering

**Key Features**:
- Template CRUD operations
- Jinja2 template rendering
- Variable validation
- Template caching
- Preview generation
- Category management
- Usage statistics

**Dependencies**: Storage Service

**Usage Example**:
```python
from services import TemplateService

template_service = TemplateService()
template_service.initialize(db_service, storage_service)

# Render template
result = template_service.render_template(
    template_name='psychological_report',
    variables={'client_name': 'John', 'date': '2024-01-15'}
)
```

## Supporting Services

### 🔄 RedisService (`redis_service.py`)
**Purpose**: Caching and session storage

**Key Features**:
- Redis connection management
- Caching operations
- Session storage
- Rate limiting support
- Pub/Sub messaging

### 💾 StorageService (`storage_service.py`)
**Purpose**: File storage and management

**Key Features**:
- File upload/download
- Cloud storage integration
- File metadata management
- Access control
- Cleanup utilities

### 🧠 Personality Services
- `mongo_personality_service.py`: Personality assessment data management
- `mongo_personal_values_service.py`: Personal values assessment management

### 🎨 TemplateRendererService (`template_renderer_service.py`)
**Purpose**: Advanced template rendering with layout engines

## Service Architecture

### Initialization Pattern
All services follow a consistent initialization pattern:

```python
class ServiceName:
    def __init__(self):
        self._initialized = False
        # Initialize instance variables
    
    def initialize(self, dependencies) -> bool:
        """Initialize service with dependencies"""
        try:
            # Setup dependencies
            # Configure service
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize {self.__class__.__name__}: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health status"""
        return {
            'service': self.__class__.__name__,
            'status': 'healthy' if self._initialized else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat()
        }
```

### Dependency Injection
Services use dependency injection for loose coupling:

```python
# Service initialization with dependencies
auth_service.initialize(
    config=auth_config,
    redis_client=redis_service,
    db_service=database_service
)

pdf_service.initialize(
    db_service=database_service,
    storage_service=storage_service,
    email_service=email_service
)
```

### Error Handling
All services implement consistent error handling:

```python
try:
    result = service.operation(params)
    return {
        'success': True,
        'data': result
    }
except SpecificException as e:
    logger.error(f"Specific error: {e}")
    return {
        'success': False,
        'error': 'specific_error',
        'message': str(e)
    }
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return {
        'success': False,
        'error': 'internal_error',
        'message': 'An unexpected error occurred'
    }
```

## Configuration

### Environment Variables
Services use environment variables for configuration:

```bash
# Database
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=mindframe_app

# Redis
REDIS_URL=redis://localhost:6379

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
```

### Service Configuration Classes
Many services use configuration dataclasses:

```python
@dataclass
class AuthConfig:
    jwt_secret_key: str
    jwt_algorithm: str = 'HS256'
    access_token_expires: int = 3600
    refresh_token_expires: int = 604800
    # ... other config options
```

## Testing

### Unit Testing
Each service should have comprehensive unit tests:

```python
import pytest
from unittest.mock import Mock, patch
from services.auth_service import AuthService

class TestAuthService:
    def setup_method(self):
        self.auth_service = AuthService()
        self.mock_db = Mock()
        self.mock_redis = Mock()
    
    def test_login_success(self):
        # Test successful login
        pass
    
    def test_login_invalid_credentials(self):
        # Test login with invalid credentials
        pass
```

### Integration Testing
Test service interactions:

```python
def test_pdf_generation_with_template():
    # Test PDF service with template service
    template_service.create_template(template_data)
    result = pdf_service.generate_pdf_from_template(
        template_name='test_template',
        variables={'name': 'Test'}
    )
    assert result['success'] is True
```

## Monitoring and Logging

### Health Checks
All services provide health check endpoints:

```python
# Check individual service health
health = auth_service.health_check()
print(health['status'])  # 'healthy' or 'unhealthy'

# Check all services
for service in [auth_service, db_service, email_service]:
    health = service.health_check()
    print(f"{health['service']}: {health['status']}")
```

### Logging
Services use structured logging:

```python
import logging

logger = logging.getLogger(__name__)

# Log with context
logger.info("User login successful", extra={
    'user_id': user_id,
    'ip_address': ip_address,
    'user_agent': user_agent
})

logger.error("Database connection failed", extra={
    'connection_string': masked_connection_string,
    'error_code': error.code
})
```

## Performance Optimization

### Caching
- Use Redis for frequently accessed data
- Implement template caching in TemplateService
- Cache user sessions and permissions

### Async Operations
- PDF generation uses thread pools
- Email sending can be queued
- Database operations can be batched

### Connection Pooling
- MongoDB connection pooling in DatabaseService
- Redis connection pooling
- SMTP connection reuse

## Security Best Practices

### Authentication
- Use strong JWT secrets
- Implement token rotation
- Rate limit authentication attempts
- Log security events

### Data Protection
- Hash passwords with bcrypt
- Encrypt sensitive data at rest
- Use HTTPS for all communications
- Validate all inputs

### Access Control
- Implement role-based permissions
- Validate user access for all operations
- Log access attempts
- Use principle of least privilege

## Migration and Deployment

### Database Migrations
```python
# Run database migrations
db_service.create_index('users', [('email', 1)], unique=True)
db_service.create_index('reports', [('user_id', 1), ('created_at', -1)])
```

### Service Deployment
1. Initialize services in correct order
2. Run health checks before serving traffic
3. Implement graceful shutdown
4. Monitor service metrics

## Troubleshooting

### Common Issues

**Service Initialization Failures**:
- Check environment variables
- Verify external service connectivity
- Review dependency versions

**Database Connection Issues**:
- Verify MongoDB connection string
- Check network connectivity
- Review authentication credentials

**Email Delivery Problems**:
- Verify SMTP configuration
- Check email provider settings
- Review firewall rules

**PDF Generation Errors**:
- Check template syntax
- Verify required variables
- Review file permissions

### Debug Mode
Enable debug logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Service-specific debug info
result = service.operation(params)
logger.debug(f"Operation result: {result}")
```

## Contributing

### Adding New Services
1. Follow the initialization pattern
2. Implement health checks
3. Add comprehensive error handling
4. Write unit and integration tests
5. Update this README
6. Add configuration documentation

### Code Standards
- Use type hints for all methods
- Follow PEP 8 style guidelines
- Add docstrings for all public methods
- Implement proper logging
- Handle exceptions gracefully

### Testing Requirements
- Minimum 80% code coverage
- Unit tests for all public methods
- Integration tests for service interactions
- Mock external dependencies
- Test error conditions

For more detailed information about specific services, refer to the individual service files and the main authentication documentation in `../AUTH_README.md`.