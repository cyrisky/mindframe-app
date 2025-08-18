# Mindframe Backend

A Flask-based backend API for the Mindframe psychological reporting application. This backend provides comprehensive services for user authentication, template management, report generation, and PDF creation using WeasyPrint.

## Features

- **User Authentication**: JWT-based authentication with role-based access control
- **Template Management**: Create, edit, and manage HTML templates for reports
- **Report Generation**: Generate psychological reports from templates and data
- **PDF Generation**: High-quality PDF generation using WeasyPrint
- **File Storage**: Support for local and AWS S3 storage
- **Email Services**: Email notifications and verification
- **Caching**: Redis-based caching for improved performance
- **Health Monitoring**: Comprehensive health check endpoints

## Architecture

```
backend/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── src/
    ├── api/              # API routes and endpoints
    │   └── routes/       # Route blueprints
    ├── core/             # Core PDF generation components
    ├── models/           # Data models
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

### 7. Create required directories

```bash
mkdir -p storage temp/pdf logs templates
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Default |
|----------|-------------|----------|
| `FLASK_ENV` | Environment (development/production) | development |
| `SECRET_KEY` | Flask secret key | - |
| `MONGODB_URI` | MongoDB connection string | mongodb://localhost:27017/mindframe |
| `REDIS_URL` | Redis connection string | redis://localhost:6379/0 |
| `STORAGE_TYPE` | Storage type (local/s3) | local |
| `JWT_SECRET_KEY` | JWT signing key | - |
| `SMTP_SERVER` | Email server | localhost |

### Database Setup

The application will automatically create necessary collections and indexes on first run.

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

### Health Check
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed service health status

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh JWT token
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Get user profile
- `PUT /api/auth/profile` - Update user profile

### Templates
- `GET /api/templates` - List templates
- `POST /api/templates` - Create template
- `GET /api/templates/{id}` - Get template
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template
- `POST /api/templates/{id}/render` - Render template

### Reports
- `GET /api/reports` - List reports
- `POST /api/reports` - Create report
- `GET /api/reports/{id}` - Get report
- `PUT /api/reports/{id}` - Update report
- `DELETE /api/reports/{id}` - Delete report
- `GET /api/reports/{id}/pdf` - Generate PDF

### PDF Generation
- `POST /api/pdf/generate` - Generate PDF from HTML
- `POST /api/pdf/from-template` - Generate PDF from template

## Services

### AuthService
Handles user authentication, JWT tokens, and authorization.

### TemplateService
Manages HTML templates with Jinja2 processing.

### ReportService
Handles psychological report creation and management.

### PDFService
Generates PDFs using WeasyPrint with custom styling.

### DatabaseService
MongoDB operations and connection management.

### RedisService
Caching and session management.

### StorageService
File storage (local filesystem or AWS S3).

### EmailService
Email notifications and verification.

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

- JWT-based authentication
- Password hashing with bcrypt
- Input validation and sanitization
- CORS configuration
- Rate limiting
- File upload restrictions
- SQL injection prevention (NoSQL)

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