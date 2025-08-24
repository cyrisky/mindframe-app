# 🚀 Production Migration Plan

## Priority 1: Critical Infrastructure

### 1. MongoDB Migration
- Setup MongoDB Atlas cluster
- Update connection strings in:
  - src/services/database_service.py
  - src/services/product_report_service.py
  - app.py
  - .env.example

### 2. Redis Migration
- Setup cloud Redis service
- Update Redis URLs in:
  - src/services/redis_service.py
  - job_queue/config.py
  - app.py
  - .env
  - .env.example

## Priority 2: Application Configuration

### 3. Storage Migration
- Setup cloud storage bucket
- Update storage configuration in:
  - src/services/storage_service.py
  - app.py
  - .env
  - .env.example

### 4. Remove Hardcoded Paths
- Replace hardcoded paths with environment variables:
  - tests/test_personal_values_template.py: Hardcoded path found: /Users/crisbawana/Documents/2_Areas/Satu
  - tests/test_template_renderer_service.py: Hardcoded path found: /Users/crisbawana/Documents/2_Areas/Satu
  - scripts/migrate_to_production.py: Hardcoded path found: /Users/[^\s\
  - src/api/personal_values_api.py: Hardcoded path found: /Users/crisbawana/Documents/2_Areas/Satu
  - src/services/template_renderer_service.py: Hardcoded path found: /Users/crisbawana/Documents/2_Areas/Satu
  - ... and 1 more files

## Priority 3: External Services

### 5. Email Service Setup
- Configure production SMTP service
- Update email configuration

### 6. CORS Configuration
- Update CORS origins for production domains

### 7. Google Credentials
- Secure Google service account credentials
- Use environment variables or secret manager

## Environment Setup

1. Copy `.env.production.example` to `.env`
2. Update all environment variables with production values
3. Test configuration with staging environment
4. Deploy to production
