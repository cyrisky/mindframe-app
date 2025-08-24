# Mindframe Backend

A Flask-based backend API for the Mindframe psychological reporting application. This backend provides comprehensive services for user authentication, template management, report generation, and PDF creation using WeasyPrint.

## Features

- **🔐 User Authentication**: Comprehensive JWT-based authentication with role-based access control, password policies, and session management
- **📝 Template Management**: Create, edit, and manage HTML templates for reports with Jinja2 processing
- **📊 Report Generation**: Generate psychological reports from templates and data with full lifecycle management
- **📄 PDF Generation**: High-quality PDF generation using WeasyPrint with custom styling and layouts
- **💾 File Storage**: Support for local and AWS S3 storage with secure file management
- **📧 Email Services**: Email notifications, verification, and password reset functionality
- **⚡ Caching**: Redis-based caching for improved performance and session storage
- **🏥 Health Monitoring**: Comprehensive health check endpoints with dependency monitoring
- **🧠 Assessment APIs**: Specialized APIs for personality and personal values assessments
- **🔒 Security**: Advanced security features including rate limiting, account lockout, and API key management

## Architecture

```
backend/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── src/
    ├── api/              # API routes and endpoints
    │   ├── routes/       # Route blueprints (auth, health, pdf, reports, templates)
    │   ├── app.py        # Flask application factory
    │   ├── personality_api.py    # Personality assessment API
    │   └── personal_values_api.py # Personal values API
    ├── auth/             # Authentication system
    │   ├── models.py     # User and authentication models
    │   ├── service.py    # Authentication service
    │   ├── middleware.py # Auth middleware and decorators
    │   └── routes.py     # Authentication endpoints
    ├── core/             # Core PDF generation components
    ├── models/           # Data models (User, PDFDocument, Template, Report)
    ├── services/         # Business logic services
    └── utils/            # Utility functions
```

## Prerequisites

- Python 3.8+
- MongoDB 4.4+
- Redis 6.0+
- WeasyPrint dependencies (see installation notes)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd mindframe-app/backend
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install WeasyPrint dependencies

**macOS:**
```bash
brew install python3 python3-dev python3-pip python3-cffi python3-brotli libffi-dev pango gdk-pixbuf2
```

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-dev python3-pip python3-cffi python3-brotli libffi-dev libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0
```

**Windows:**
- Install GTK+ for Windows
- Follow WeasyPrint Windows installation guide

### 5. Setup environment variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 6. Setup MongoDB and Redis

Ensure MongoDB and Redis are running:

```bash
# MongoDB (default port 27017)
mongod

# Redis (default port 6379)
redis-server
```

### 7. Initialize the database

```bash
# Create authentication collections and indexes
python -c "from src.auth.service import AuthService; AuthService().initialize_database()"
```

### 8. Create required directories

```bash
mkdir -p storage temp/pdf logs templates
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

#### Core Application
| Variable | Description | Default |
|----------|-------------|----------|
| `FLASK_ENV` | Environment (development/production) | development |
| `SECRET_KEY` | Flask secret key | - |
| `MONGODB_URI` | MongoDB connection string | mongodb://localhost:27017/mindframe |
| `REDIS_URL` | Redis connection string | redis://localhost:6379/0 |
| `STORAGE_TYPE` | Storage type (local/s3) | local |

#### Authentication & Security
| Variable | Description | Default |
|----------|-------------|----------|
| `JWT_SECRET_KEY` | JWT signing key | - |
| `JWT_ALGORITHM` | JWT algorithm | HS256 |
| `JWT_ACCESS_TOKEN_EXPIRES` | Access token expiration (seconds) | 3600 |
| `JWT_REFRESH_TOKEN_EXPIRES` | Refresh token expiration (seconds) | 2592000 |
| `PASSWORD_MIN_LENGTH` | Minimum password length | 8 |
| `PASSWORD_REQUIRE_UPPERCASE` | Require uppercase letters | true |
| `PASSWORD_REQUIRE_LOWERCASE` | Require lowercase letters | true |
| `PASSWORD_REQUIRE_NUMBERS` | Require numbers | true |
| `PASSWORD_REQUIRE_SPECIAL` | Require special characters | true |
| `MAX_LOGIN_ATTEMPTS` | Max failed login attempts | 5 |
| `ACCOUNT_LOCKOUT_DURATION` | Account lockout duration (seconds) | 900 |
| `SESSION_TIMEOUT` | Session timeout (seconds) | 3600 |
| `API_RATE_LIMIT_ENABLED` | Enable API rate limiting | true |

#### Email Configuration
| Variable | Description | Default |
|----------|-------------|----------|
| `SMTP_SERVER` | Email server | localhost |
| `SMTP_PORT` | SMTP port | 587 |
| `SMTP_USERNAME` | SMTP username | - |
| `SMTP_PASSWORD` | SMTP password | - |
| `SMTP_USE_TLS` | Use TLS encryption | true |
| `EMAIL_FROM` | Default sender email | noreply@mindframe.app |
| `EMAIL_VERIFICATION_REQUIRED` | Require email verification | false |
| `PASSWORD_RESET_TOKEN_EXPIRES` | Reset token expiration (seconds) | 3600 |

### Database Setup

The application will automatically create necessary collections and indexes on first run.

#### Authentication Database Structure
The authentication system uses the following MongoDB collections:

- **`mindframe.auth`**: User accounts and authentication data
- **`mindframe.sessions`**: Active user sessions
- **`mindframe.login_attempts`**: Failed login attempt tracking
- **`mindframe.password_resets`**: Password reset tokens
- **`mindframe.api_keys`**: API key management
- **`mindframe.blacklisted_tokens`**: Revoked JWT tokens

#### Initial Admin User
Create an initial admin user:

```bash
python -c "
from src.auth.service import AuthService
auth = AuthService()
user = auth.register_user(
    email='admin@mindframe.app',
    password='SecureAdminPass123!',
    first_name='Admin',
    last_name='User',
    role='admin'
)
print(f'Admin user created: {user.id}')
"```

## Running the Application

### Development

```bash
python app.py
```

The API will be available at `http://localhost:5000`

### Production

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API Endpoints

For detailed API documentation, see [API README](src/api/README.md).

### 🏥 Health Check
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed service health status

### 🔐 Authentication (`/api/auth`)
- `POST /api/auth/register` - User registration with email verification
- `POST /api/auth/login` - User login with account lockout protection
- `POST /api/auth/refresh` - Refresh JWT token
- `POST /api/auth/logout` - User logout (blacklist token)
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile
- `POST /api/auth/change-password` - Change password with validation
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password` - Reset password with token
- `POST /api/auth/verify-email` - Verify email address
- `GET /api/auth/sessions` - List active sessions
- `DELETE /api/auth/sessions/{id}` - Revoke session

### 📝 Templates (`/api/templates`)
- `GET /api/templates` - List templates with filtering
- `POST /api/templates` - Create template with validation
- `GET /api/templates/{id}` - Get template details
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template
- `POST /api/templates/{id}/render` - Render template with data
- `POST /api/templates/{id}/preview` - Preview template
- `GET /api/templates/{id}/variables` - Get template variables
- `GET /api/templates/categories` - List template categories

### 📊 Reports (`/api/reports`)
- `GET /api/reports` - List reports with pagination
- `POST /api/reports` - Create psychological report
- `GET /api/reports/{id}` - Get report details
- `PUT /api/reports/{id}` - Update report
- `DELETE /api/reports/{id}` - Delete report
- `POST /api/reports/{id}/generate-pdf` - Generate PDF for report
- `POST /api/reports/{id}/test-results` - Add test results
- `PUT /api/reports/{id}/status` - Update report status
- `POST /api/reports/{id}/viewers` - Add authorized viewer
- `GET /api/reports/statistics` - Get report statistics

### 📄 PDF Generation (`/api/pdf`)
- `POST /api/pdf/generate` - Generate PDF from HTML (rate limited)
- `POST /api/pdf/generate-from-template` - Generate PDF from template
- `GET /api/pdf/documents` - List PDF documents
- `GET /api/pdf/documents/{id}` - Get PDF document
- `DELETE /api/pdf/documents/{id}` - Delete PDF document
- `GET /api/pdf/download/{id}` - Download PDF file
- `GET /api/pdf/status/{task_id}` - Check async generation status

### 🧠 Assessment APIs
- **Personality API** (`/api/personality`) - Personality assessment endpoints
- **Personal Values API** (`/api/personal-values`) - Personal values assessment endpoints

## Authentication Usage

### User Registration
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### User Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

### Using JWT Token
```bash
# Include JWT token in Authorization header
curl -H "Authorization: Bearer <jwt_token>" \
     http://localhost:5000/api/reports
```

### Password Reset Flow
```bash
# Request password reset
curl -X POST http://localhost:5000/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'

# Reset password with token
curl -X POST http://localhost:5000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "reset_token_from_email",
    "new_password": "NewSecurePass123!"
  }'
```

## Services

For detailed service documentation, see [Services README](src/services/README.md).

### 🔐 AuthService
Comprehensive authentication service with:
- User registration and login
- JWT token management (access/refresh)
- Password hashing and validation
- Account lockout protection
- Session management
- Password reset functionality
- API key management
- Role-based access control

### 📝 TemplateService
HTML template management with:
- Template CRUD operations
- Jinja2 template processing
- Variable extraction and validation
- Template rendering and preview
- Category management
- Template caching

### 📊 ReportService
Psychological report management with:
- Report lifecycle management
- PDF generation integration
- Test result management
- Authorized viewer management
- Report status tracking
- Statistics and analytics

### 📄 PDFService
Advanced PDF generation with:
- WeasyPrint integration
- Template-based generation
- Async PDF processing
- Custom styling and layouts
- Document management
- Generation statistics

### 💾 DatabaseService
MongoDB operations with:
- Connection management
- CRUD operations
- Index management
- Health monitoring
- Backup and restore
- Collection management

### ⚡ RedisService
Caching and session storage with:
- Session management
- Data caching
- Rate limiting support
- Health monitoring
- Connection pooling

### 📁 StorageService
File storage management with:
- Local filesystem support
- AWS S3 integration
- File upload/download
- Security and validation
- Metadata management

### 📧 EmailService
Email communication with:
- SMTP configuration
- Template-based emails
- Verification emails
- Password reset emails
- Notification system
- Attachment support

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_auth_service.py
```

## Development

### Code Style

```bash
# Format code
black src/

# Lint code
flake8 src/

# Type checking
mypy src/
```

### Adding New Features

1. Create models in `src/models/`
2. Implement business logic in `src/services/`
3. Add API routes in `src/api/routes/`
4. Update `app.py` to register new services/routes
5. Add tests in `tests/`

## Deployment

### Docker

```dockerfile
FROM python:3.9-slim

# Install WeasyPrint dependencies
RUN apt-get update && apt-get install -y \
    python3-dev python3-pip python3-cffi python3-brotli \
    libffi-dev libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Environment Setup

1. Set production environment variables
2. Configure MongoDB and Redis
3. Setup file storage (S3 recommended for production)
4. Configure email service
5. Setup SSL/TLS certificates
6. Configure reverse proxy (nginx)

## Monitoring

### Health Checks
- Basic: `GET /health`
- Detailed: `GET /health/detailed`

### Logging
Logs are written to stdout and optionally to files. Configure log level and format via environment variables.

### Metrics
Service health and performance metrics are available through health check endpoints.

## Security

### Authentication & Authorization
- **JWT-based authentication** with access and refresh tokens
- **Password hashing** with bcrypt and configurable strength
- **Role-based access control** (Admin, Psychologist, User, Moderator)
- **Session management** with timeout and revocation
- **Account lockout** protection against brute force attacks
- **Password policies** with complexity requirements
- **API key management** for service-to-service authentication

### Input Validation & Sanitization
- **Pydantic models** for request/response validation
- **Input sanitization** to prevent XSS attacks
- **File upload restrictions** with type and size validation
- **SQL injection prevention** (NoSQL injection for MongoDB)
- **Template injection protection** in Jinja2 templates

### Network Security
- **CORS configuration** for cross-origin requests
- **Rate limiting** on authentication and API endpoints
- **HTTPS enforcement** in production
- **Security headers** (HSTS, CSP, X-Frame-Options)
- **Request size limits** to prevent DoS attacks

### Data Protection
- **Encrypted password storage** with bcrypt
- **Secure token generation** for password resets
- **Token blacklisting** for logout and revocation
- **Sensitive data masking** in logs
- **Database connection encryption** (TLS/SSL)

### Monitoring & Auditing
- **Login attempt tracking** with IP and timestamp
- **Security event logging** for audit trails
- **Failed authentication monitoring** with alerting
- **Session activity tracking** for security analysis
- **API usage monitoring** for anomaly detection

## Troubleshooting

### Common Issues

1. **WeasyPrint installation fails**
   - Ensure system dependencies are installed
   - Check Python version compatibility
   - Verify GTK+ installation on Windows

2. **MongoDB connection errors**
   - Verify MongoDB is running
   - Check connection string format
   - Ensure database permissions

3. **Redis connection errors**
   - Verify Redis is running
   - Check Redis URL format
   - Ensure Redis is accessible

4. **PDF generation fails**
   - Check WeasyPrint dependencies
   - Verify template syntax
   - Check file permissions

### Debug Mode

Set `FLASK_ENV=development` for detailed error messages and auto-reload.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run code quality checks
5. Submit a pull request

## License

This project is licensed under the MIT License.