# Docker Deployment Guide

Panduan lengkap untuk menjalankan aplikasi Mindframe menggunakan Docker Compose yang menggabungkan frontend dan backend dalam satu konfigurasi.

## 🐳 Arsitektur Docker

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │   Frontend      │    │   Backend API   │
│   (Port 8080)   │────│   (React)       │────│   (Flask)       │
│                 │    │   (Port 80)     │    │   (Port 5001)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                └────────┬───────────────┘
                                         │
                        ┌─────────────────┐    ┌─────────────────┐
                        │   MongoDB       │    │   Redis Cache   │
                        │   (Port 27017)  │    │   (Port 6379)   │
                        └─────────────────┘    └─────────────────┘
```

## 📋 Prerequisites

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Git** (untuk clone repository)

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd mindframe-app
```

### 2. Setup Environment Variables
```bash
# Copy environment template
cp .env.docker .env

# Edit environment variables
nano .env  # atau editor lainnya
```

**Penting:** Update variabel berikut di file `.env`:
```env
SECRET_KEY=your-production-secret-key-change-this
JWT_SECRET_KEY=your-jwt-secret-key-change-this
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MONGO_CONNECTION_STRING=mongodb://username:password@your-mongodb-host:27017/mindframe?authSource=admin
```

### 3. Build dan Jalankan
```bash
# Build dan start semua services
docker-compose up --build

# Atau jalankan di background
docker-compose up --build -d
```

### 4. Akses Aplikasi
- **Frontend (React):** http://localhost:80
- **Backend API:** http://localhost:5001
- **Nginx Proxy:** http://localhost:8080 (menggabungkan frontend + backend)
- **MongoDB:** External (configured via connection string)
- **Redis:** localhost:6379

## 🔧 Services Detail

### Frontend (React)
- **Container:** `mindframe-frontend`
- **Port:** 80
- **Build:** Multi-stage dengan Nginx
- **Features:** 
  - Optimized production build
  - Nginx dengan gzip compression
  - React Router support
  - Security headers
  - Static asset caching

### Backend (Flask)
- **Container:** `mindframe-backend`
- **Port:** 5001
- **Features:**
  - WeasyPrint untuk PDF generation
  - Gunicorn WSGI server
  - Health checks
  - Volume mounting untuk storage

### Database (External MongoDB)
- **Setup:** Requires external MongoDB instance
- **Connection:** Via connection string in environment variables
- **Supported:** MongoDB Atlas, self-hosted MongoDB, or other cloud providers
- **Features:**
  - Connection via MONGO_CONNECTION_STRING
  - Support for authentication
  - Cloud-ready configuration

### Cache (Redis)
- **Container:** `mindframe-redis`
- **Port:** 6379
- **Features:**
  - Session storage
  - Rate limiting
  - Caching

### Reverse Proxy (Nginx)
- **Container:** `mindframe-nginx`
- **Port:** 8080
- **Features:**
  - Load balancing
  - Rate limiting
  - CORS handling
  - Static asset optimization

## 📝 Management Commands

### Prerequisites
Before starting, ensure you have:
1. **External MongoDB**: Set up MongoDB Atlas, self-hosted MongoDB, or cloud provider
2. **Connection String**: Update `MONGO_CONNECTION_STRING` in `.env`

### Development
```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Rebuild specific service
docker-compose build backend
docker-compose build frontend

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down
```

### Production
```bash
# Start production environment
docker-compose -f docker-compose.yml up -d

# Update and restart
docker-compose pull
docker-compose up --build -d

# Backup database (adjust connection string)
mongodump --uri="$MONGO_CONNECTION_STRING" --out ./backup
```

### Maintenance
```bash
# Check service status
docker-compose ps

# Check service health
docker-compose exec backend curl http://localhost:5001/health
docker-compose exec frontend curl http://localhost:80/health

# Access service shell
docker-compose exec backend bash
# Connect to external MongoDB
mongosh "$MONGO_CONNECTION_STRING"

# View resource usage
docker stats

# Clean up
docker-compose down --volumes --rmi all
docker system prune -a
```

## 🔒 Security Configuration

### Environment Variables
Pastikan variabel berikut diset dengan nilai yang aman:

```env
# Generate strong keys
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# External MongoDB connection
MONGO_CONNECTION_STRING=mongodb://username:password@your-mongodb-host:27017/mindframe?authSource=admin
```

### Network Security
- Semua services terisolasi dalam `mindframe-network`
- Rate limiting pada API endpoints
- CORS configuration
- Security headers

### Data Persistence
- MongoDB data: External MongoDB instance
- Redis data: `redis_data` volume
- Application storage: `./backend/storage` bind mount

## 🔍 Monitoring & Debugging

### Health Checks
```bash
# Check all services
curl http://localhost:8080/health
curl http://localhost:5001/health
curl http://localhost:80/health

# Detailed backend health
curl http://localhost:5001/health/detailed
```

### Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs mongodb
docker-compose logs redis

# Follow logs
docker-compose logs -f --tail=100 backend
```

### Performance Monitoring
```bash
# Resource usage
docker stats

# Container inspection
docker inspect mindframe-backend
docker inspect mindframe-frontend
```

## 🚨 Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check port usage
   lsof -i :80
   lsof -i :5001
   lsof -i :27017
   
   # Change ports in docker-compose.yml if needed
   ```

2. **Build failures**
   ```bash
   # Clean build
   docker-compose build --no-cache
   
   # Check Dockerfile syntax
   docker build -t test ./backend
   docker build -t test ./frontend
   ```

3. **Database connection issues**
   ```bash
   # Test external MongoDB connection
   mongosh "$MONGO_CONNECTION_STRING" --eval "db.adminCommand('ping')"
   
   # Test connection from backend
   docker-compose exec backend python -c "from src.services.database_service import DatabaseService; print(DatabaseService().health_check())"
   ```

4. **Frontend build issues**
   ```bash
   # Check Node.js version
   docker-compose exec frontend node --version
   
   # Rebuild with verbose output
   docker-compose build --progress=plain frontend
   ```

### Performance Optimization

1. **Increase worker processes**
   ```yaml
   # In docker-compose.yml, backend service
   command: ["gunicorn", "-w", "8", "-b", "0.0.0.0:5001", "app:app"]
   ```

2. **Add resource limits**
   ```yaml
   # In docker-compose.yml
   deploy:
     resources:
       limits:
         cpus: '2.0'
         memory: 2G
       reservations:
         cpus: '1.0'
         memory: 1G
   ```

3. **Enable caching**
   ```bash
   # Use BuildKit for faster builds
   export DOCKER_BUILDKIT=1
   export COMPOSE_DOCKER_CLI_BUILD=1
   ```

## 🔄 CI/CD Integration

### GitHub Actions Example
```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to server
        run: |
          docker-compose pull
          docker-compose up --build -d
          docker-compose exec backend python -c "print('Health check passed')"
```

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Configuration Guide](https://nginx.org/en/docs/)
- [MongoDB Docker Guide](https://hub.docker.com/_/mongo)
- [Redis Docker Guide](https://hub.docker.com/_/redis)

---

**Note:** Untuk production deployment, pertimbangkan menggunakan orchestration tools seperti Docker Swarm atau Kubernetes untuk high availability dan scalability.