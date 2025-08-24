# Production Deployment Guide

Panduan lengkap untuk deploy aplikasi Mindframe ke production dengan cloud services.

## 🚀 Overview

Aplikasi ini saat ini menggunakan beberapa local dependencies yang perlu diganti dengan cloud services untuk production deployment:

### Local Dependencies yang Perlu Diganti:

1. **MongoDB Local** → **MongoDB Atlas (Cloud)**
2. **Redis Local** → **Redis Cloud/AWS ElastiCache**
3. **Local File Storage** → **AWS S3/Google Cloud Storage**
4. **Local SMTP** → **SendGrid/AWS SES**
5. **Hardcoded Local Paths** → **Environment Variables**

## 📋 Pre-requisites

- [ ] MongoDB Atlas account
- [ ] Redis Cloud account atau AWS/GCP account
- [ ] Cloud storage account (AWS S3/Google Cloud Storage)
- [ ] Email service account (SendGrid/AWS SES)
- [ ] Production domain dan SSL certificate

## 🔧 Step-by-Step Migration

### 1. MongoDB Migration ke Atlas

#### Setup MongoDB Atlas:
1. Buat cluster di [MongoDB Atlas](https://cloud.mongodb.com/)
2. Setup database user dan password
3. Whitelist IP addresses untuk production server
4. Dapatkan connection string

#### Update Configuration:
```bash
# Ganti di .env production
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/mindframe?retryWrites=true&w=majority
```

#### Files yang Perlu Diupdate:
- `backend/src/services/database_service.py` (line 44)
- `backend/src/services/product_report_service.py` (line 39)
- `backend/app.py` (line 116)

### 2. Redis Migration ke Cloud

#### Pilihan Cloud Redis:
- **Redis Cloud**: Managed Redis service
- **AWS ElastiCache**: Redis di AWS
- **Google Cloud Memorystore**: Redis di GCP
- **Azure Cache for Redis**: Redis di Azure

#### Update Configuration:
```bash
# Redis Cloud example
REDIS_URL=redis://username:password@redis-host:port/db

# AWS ElastiCache example
REDIS_URL=redis://elasticache-endpoint:6379/0
```

#### Files yang Perlu Diupdate:
- `backend/src/services/redis_service.py` (line 29)
- `backend/job_queue/config.py` (line 6)
- `backend/app.py` (line 120)

### 3. File Storage Migration

#### Setup Cloud Storage:

**Option A: AWS S3**
```bash
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1
```

**Option B: Google Cloud Storage**
```bash
STORAGE_TYPE=gcs
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_STORAGE_BUCKET=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

#### Files yang Perlu Diupdate:
- `backend/src/services/storage_service.py` (line 35)
- `backend/app.py` (line 124)

### 4. Email Service Migration

#### Setup Production SMTP:

**Option A: SendGrid**
```bash
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_USE_TLS=True
```

**Option B: AWS SES**
```bash
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-ses-username
SMTP_PASSWORD=your-ses-password
SMTP_USE_TLS=True
```

### 5. Remove Hardcoded Paths

#### Files dengan Hardcoded Paths:

1. **Template Renderer Service**:
   - `backend/src/services/template_renderer_service.py` (line 139)
   - `backend/src/services/mongo_personal_values_service.py` (line 28, 393)
   - `backend/src/api/personal_values_api.py` (line 22)

2. **Test Files**:
   - `backend/tests/test_personal_values_template.py` (line 15, 62)
   - `backend/tests/test_template_renderer_service.py` (line 38)

#### Solution:
```python
# Ganti hardcoded paths dengan environment variables
import os

# Before:
self.interpretation_data_path = "/Users/crisbawana/Documents/..."

# After:
self.interpretation_data_path = os.getenv(
    'INTERPRETATION_DATA_PATH', 
    './ai/interpretation-data/interpretation-personal-values.json'
)
```

### 6. CORS Configuration

#### Update Production Domains:
```bash
# Development
CORS_ORIGINS=http://localhost:3000

# Production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,https://app.yourdomain.com
```

### 7. Google Drive Integration

#### Secure Credentials Management:
```bash
# Instead of local file path
GOOGLE_CREDENTIALS_FILE=./google-service-account-key.json

# Use environment variable with JSON content
GOOGLE_SERVICE_ACCOUNT_CREDENTIALS_JSON='{"type": "service_account", ...}'
```

## 🐳 Docker Deployment

### Dockerfile Example:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Expose port
EXPOSE 5000

# Start application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Docker Compose for Production:
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - MONGODB_URI=${MONGODB_URI}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - worker
  
  worker:
    build: .
    command: python -m rq worker --url ${REDIS_URL}
    environment:
      - MONGODB_URI=${MONGODB_URI}
      - REDIS_URL=${REDIS_URL}
```

## ☁️ Cloud Platform Deployment

### AWS Deployment:
1. **Elastic Beanstalk** untuk aplikasi Flask
2. **RDS** atau **DocumentDB** untuk database
3. **ElastiCache** untuk Redis
4. **S3** untuk file storage
5. **SES** untuk email

### Google Cloud Deployment:
1. **App Engine** atau **Cloud Run** untuk aplikasi
2. **Cloud Firestore** atau **MongoDB Atlas**
3. **Memorystore** untuk Redis
4. **Cloud Storage** untuk files
5. **SendGrid** untuk email

### Azure Deployment:
1. **App Service** untuk aplikasi Flask
2. **Cosmos DB** untuk database
3. **Azure Cache for Redis**
4. **Blob Storage** untuk files
5. **SendGrid** untuk email

## 🔒 Security Considerations

### Environment Variables:
- Gunakan secret management services (AWS Secrets Manager, Azure Key Vault, etc.)
- Jangan commit credentials ke repository
- Rotate keys secara berkala

### Network Security:
- Setup VPC/Virtual Networks
- Configure security groups/firewall rules
- Use SSL/TLS untuk semua connections

### Application Security:
- Enable rate limiting
- Setup monitoring dan logging
- Regular security updates

## 📊 Monitoring & Logging

### Recommended Tools:
- **Application Monitoring**: New Relic, Datadog, atau Sentry
- **Log Management**: ELK Stack, Splunk, atau cloud logging services
- **Uptime Monitoring**: Pingdom, UptimeRobot

### Health Checks:
```python
# Ensure health checks work with cloud services
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'database': check_mongodb_connection(),
        'redis': check_redis_connection(),
        'storage': check_storage_connection()
    }
```

## 🚀 Deployment Checklist

### Pre-deployment:
- [ ] Setup cloud services (MongoDB Atlas, Redis Cloud, etc.)
- [ ] Configure environment variables
- [ ] Update CORS origins
- [ ] Setup SSL certificates
- [ ] Configure monitoring

### Deployment:
- [ ] Deploy application
- [ ] Run database migrations
- [ ] Start worker processes
- [ ] Verify health checks
- [ ] Test critical functionality

### Post-deployment:
- [ ] Monitor application performance
- [ ] Check logs for errors
- [ ] Verify all integrations working
- [ ] Setup backup procedures
- [ ] Document production procedures

## 🔧 Troubleshooting

### Common Issues:

1. **Connection Timeouts**:
   - Check firewall rules
   - Verify network connectivity
   - Check service status

2. **Authentication Errors**:
   - Verify credentials
   - Check IP whitelisting
   - Validate connection strings

3. **File Upload Issues**:
   - Check storage permissions
   - Verify bucket configuration
   - Check file size limits

## 📞 Support

Untuk bantuan deployment:
1. Check logs untuk error messages
2. Verify environment variables
3. Test individual service connections
4. Consult cloud provider documentation

---

**Note**: Pastikan untuk test semua functionality di staging environment sebelum deploy ke production.