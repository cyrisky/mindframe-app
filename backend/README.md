# Mindframe Backend

A comprehensive Flask-based API for psychological reporting applications with advanced features including authentication, template management, PDF generation, and assessment tools.

## 🚀 Features

- **🔐 User Authentication & Authorization** - JWT-based auth with role-based access control
- **📝 Template Management** - Dynamic HTML template system with Jinja2
- **📊 Report Generation** - Psychological report creation and management
- **📄 PDF Generation** - Advanced PDF creation with WeasyPrint
- **💾 File Storage** - Local and cloud storage support
- **📧 Email Service** - Template-based email notifications
- **⚡ Caching** - Redis-based caching and session management
- **🔍 Health Monitoring** - Comprehensive health checks and monitoring
- **🧠 Assessment APIs** - Personality and personal values assessments
- **🛡️ Security Features** - Rate limiting, CORS, input validation

## 📁 Project Structure

```
backend/
├── src/                    # Main application source code
│   ├── api/               # API routes and endpoints
│   ├── models/            # Data models and schemas
│   └── services/          # Business logic services
├── config/                # Configuration files
├── job_queue/             # Background job processing
├── templates/             # HTML templates
├── storage/               # File storage (PDFs, uploads)
├── docs/                  # Documentation files
├── dev/                   # Development and testing files
├── app.py                 # Main Flask application
└── requirements.txt       # Python dependencies
```

## 🛠️ Prerequisites

- **Python 3.8+**
- **MongoDB 4.4+**
- **Redis 6.0+**
- **WeasyPrint dependencies** (for PDF generation)

## 📦 Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd mindframe-app/backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install WeasyPrint Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-dev python3-pip python3-cffi python3-brotli libffi-dev libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0
```

**macOS:**
```bash
brew install pango
```

**Windows:**
```bash
# Install GTK+ for Windows from https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer
```

### 5. Setup Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key environment variables:

```env
# Core Application
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key
BASE_URL=http://localhost:5001
API_BASE_URL=http://localhost:5001

# Database
MONGO_URI=mongodb://localhost:27017/mindframe
REDIS_URL=redis://localhost:6379

# Authentication & Security
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000
PASSWORD_HASH_ROUNDS=12

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# CORS
CORS_ORIGINS=http://localhost:3000

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_DEFAULT=100 per hour
```

### 6. Setup Services

**Start MongoDB:**
```bash
# Ubuntu/Debian
sudo systemctl start mongod

# macOS
brew services start mongodb-community

# Windows
net start MongoDB
```

**Start Redis:**
```bash
# Ubuntu/Debian
sudo systemctl start redis

# macOS
brew services start redis

# Windows
redis-server
```

### 7. Initialize Database
```bash
python -c "from src.services.database_service import DatabaseService; DatabaseService().init_database()"
```

### 8. Create Required Directories
```bash
mkdir -p storage/pdfs storage/uploads storage/templates
```

### 9. Create Admin User (Optional)
```bash
python -c "
from src.services.auth_service import AuthService;
auth = AuthService();
auth.register_user('admin@example.com', 'SecurePass123!', 'Admin', 'User', role='admin')
"
```

## 🚀 Running the Application

### Development Mode
```bash
# Start the Flask development server
python app.py

# Or with Flask CLI
flask run --host=0.0.0.0 --port=5001
```

### Production Mode
```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 app:app

# With additional options
gunicorn -w 4 -b 0.0.0.0:5001 --timeout 120 --keep-alive 2 app:app
```

The API will be available at `http://localhost:5001`

## 📚 API Documentation

### 🏥 Health Check (`/health`)
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system health

### 🔐 Authentication (`/api/auth`)
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh JWT token
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password` - Reset password
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile

### 📝 Templates (`/api/templates`)
- `GET /api/templates` - List templates
- `POST /api/templates` - Create template
- `GET /api/templates/{id}` - Get template
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template
- `POST /api/templates/{id}/render` - Render template

### 📊 Reports (`/api/reports`)
- `GET /api/reports` - List reports
- `POST /api/reports` - Create report
- `GET /api/reports/{id}` - Get report
- `PUT /api/reports/{id}` - Update report
- `DELETE /api/reports/{id}` - Delete report
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

## 🔧 Services

For detailed service documentation, see [Services README](src/services/README.md).

### Core Services
- **🔐 AuthService** - Authentication and authorization
- **📝 TemplateService** - HTML template management
- **📊 ReportService** - Report lifecycle management
- **📄 PDFService** - PDF generation with WeasyPrint
- **💾 DatabaseService** - MongoDB operations
- **⚡ RedisService** - Caching and session storage
- **📁 StorageService** - File storage management
- **📧 EmailService** - Email communications

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_auth_service.py

# Run with verbose output
pytest -v
```

## 🔧 Development

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

## 🐳 Docker Deployment

### Single Backend Container

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
EXPOSE 5001
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "app:app"]
```

### Full Stack with Docker Compose

**Prerequisites**: Set up external MongoDB (MongoDB Atlas, self-hosted, or cloud provider) and update `MONGO_CONNECTION_STRING` in `.env.docker`.

Untuk deployment lengkap dengan frontend, backend, database, dan reverse proxy:

```bash
# Di root directory project
docker-compose up --build -d
```

Ini akan menjalankan:
- **Frontend (React)** di port 80
- **Backend (Flask)** di port 5001  
- **External MongoDB** via connection string
- **Redis** di port 6379
- **Nginx Proxy** di port 8080 (menggabungkan frontend + backend)

**Lihat:** [DOCKER_DEPLOYMENT.md](../DOCKER_DEPLOYMENT.md) untuk panduan lengkap Docker Compose.

## 🛡️ Security Features

### Authentication & Authorization
- JWT-based authentication with access and refresh tokens
- Password hashing with bcrypt
- Role-based access control (Admin, Psychologist, User, Moderator)
- Session management with timeout and revocation
- Account lockout protection
- API key management

### Input Validation & Protection
- Pydantic models for request/response validation
- Input sanitization to prevent XSS attacks
- File upload restrictions
- Template injection protection
- Rate limiting on endpoints

### Network Security
- CORS configuration
- HTTPS enforcement in production
- Security headers (HSTS, CSP, X-Frame-Options)
- Request size limits

## 📊 Monitoring

### Health Checks
- Basic: `GET /health`
- Detailed: `GET /health/detailed`

### Logging
Logs are written to stdout and optionally to files. Configure log level via environment variables.

### Metrics
Service health and performance metrics available through health check endpoints.

## 🔍 Troubleshooting

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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run code quality checks
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the documentation in `docs/`
3. Create an issue in the repository

---

**Note:** This README provides a comprehensive overview of the Mindframe Backend. For detailed service documentation, API specifications, and advanced configuration options, please refer to the documentation in the `docs/` folder.