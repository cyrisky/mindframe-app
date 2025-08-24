# Mindframe App - Psychological Test Report Generator

A monorepo application for generating psychological test reports using WeasyPrint as the core PDF generation engine.

## Project Structure

```
mindframe-app/
├── backend/                 # Backend API service
│   ├── src/
│   │   ├── core/           # Core PDF generation (WeasyPrint wrapper)
│   │   ├── api/            # Flask API endpoints
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   └── tests/              # Backend tests
├── frontend/               # Frontend application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   └── utils/          # Frontend utilities
│   └── public/             # Static assets
├── shared/                 # Shared resources
│   ├── templates/          # HTML/CSS templates for PDF generation
│   └── schemas/            # Shared data schemas
└── docs/                   # Documentation
```

## Features

### Completed Features (from WeasyPrint)
- ✅ **PDF Generation Core**: Robust HTML/CSS to PDF conversion
- ✅ **Advanced Layout Support**: Complex CSS layouts, grids, flexbox
- ✅ **Template Support**: HTML/CSS template processing with Jinja2
- ✅ **Font Support**: International fonts including Bahasa Indonesia
- ✅ **Image Integration**: Support for various image formats

### Architecture
- **Monorepo Structure**: Backend and frontend in single repository
- **WeasyPrint Foundation**: Core PDF generation capabilities
- **Flask API**: RESTful backend service
- **React Frontend**: Modern web interface
- **MongoDB Integration**: Data persistence
- **Redis Queue**: Asynchronous job processing

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git
- **External MongoDB** (MongoDB Atlas, self-hosted, or cloud provider)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mindframe-app
   ```

2. **Set up external MongoDB**
   - See `EXTERNAL_MONGODB_SETUP.md` for detailed setup guide
   - Get your MongoDB connection string

3. **Set up environment variables**
   ```bash
   cp .env.docker .env
   # Edit .env with your MongoDB connection string:
   # MONGO_CONNECTION_STRING=mongodb://username:password@your-host:27017/mindframe?authSource=admin
   ```

4. **Start the application**
   ```bash
   docker-compose up --build -d
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5001
   - Nginx Proxy: http://localhost:80

### Production Deployment with Dokploy

For production deployment using Dokploy:

1. **Prepare your repository**
   - Ensure your code is in a Git repository accessible to Dokploy
   - Configure your environment variables

2. **Deploy with Dokploy**
   ```bash
   # Use Dokploy's Docker Compose deployment feature
   # Configure domain and SSL in Dokploy dashboard
   ```

**Dokploy Features:**
- Automatic SSL certificates with Let's Encrypt
- Custom domain management
- Traefik reverse proxy integration
- Container orchestration and monitoring
- Centralized logging and metrics

For detailed Dokploy setup instructions, see `DOKPLOY_SETUP.md`.

### Alternative: Local Development Setup

#### Prerequisites
- Python 3.9+
- Node.js 16+
- MongoDB
- Redis

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

#### Environment Variables
Copy `.env.example` to `.env` and configure:
- Database connections
- Google Drive credentials
- Redis configuration
- API keys

## Development

### Backend Development
```bash
cd backend
source venv/bin/activate
flask run --debug
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Testing
```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test
```

## Core Components

### PDF Generation Engine
Built on WeasyPrint with enhanced template processing:
- Dynamic content binding
- Template versioning
- Multi-language support
- Custom styling capabilities

### Template System
- Jinja2 template engine
- Reusable components
- Brand customization
- Historical preservation

### Data Management
- MongoDB for application data
- Redis for job queuing
- Google Drive for file storage
- Structured logging

## 📚 Documentation

- **Backend**: See `backend/README.md` for detailed backend documentation
- **Frontend**: See `frontend/README.md` for frontend setup and development
- **Docker**: See `DOCKER_DEPLOYMENT.md` for complete Docker deployment guide
- **Dokploy**: See `DOKPLOY_SETUP.md` for production deployment with Dokploy
- **Dokploy Troubleshooting**: See `DOKPLOY_TROUBLESHOOTING.md` for troubleshooting Dokploy issues
- **External MongoDB**: See `EXTERNAL_MONGODB_SETUP.md` for MongoDB setup guide

## License

MIT License - see LICENSE file for details.