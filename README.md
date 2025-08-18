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

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- MongoDB
- Redis

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Environment Variables
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

## License

MIT License - see LICENSE file for details.