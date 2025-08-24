# 🚀 Dokploy Setup Guide

Panduan untuk deploy aplikasi Mindframe menggunakan Dokploy.

## 📋 Prerequisites

1. **Dokploy Server** yang sudah terinstall dan berjalan
2. **External MongoDB** (MongoDB Atlas, self-hosted, atau cloud provider)
3. **Domain** yang sudah dikonfigurasi untuk aplikasi
4. **Git Repository** yang dapat diakses oleh Dokploy

## 🔧 Konfigurasi Docker Compose untuk Dokploy

File `docker-compose.yml` telah dikonfigurasi dengan:

### 1. **Network Configuration**
```yaml
networks:
  mindframe-network:
    driver: bridge
  dokploy-network:
    external: true
```

### 2. **Traefik Labels untuk Routing**

#### Frontend Service
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.frontend-app.rule=Host(`your-domain.com`)"
  - "traefik.http.routers.frontend-app.entrypoints=web"
  - "traefik.http.services.frontend-app.loadbalancer.server.port=80"
  - "traefik.docker.network=dokploy-network"
```

#### Backend Service
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.backend-app.rule=Host(`api.your-domain.com`)"
  - "traefik.http.routers.backend-app.entrypoints=web"
  - "traefik.http.services.backend-app.loadbalancer.server.port=5001"
  - "traefik.docker.network=dokploy-network"
```

### 3. **Port Configuration**
- Menggunakan `expose` instead of `ports` untuk keamanan
- Hanya Traefik yang dapat mengakses services
- Nginx reverse proxy di-disable (optional)

## 🛠️ Setup di Dokploy

### 1. **Create New Application**
1. Login ke Dokploy dashboard
2. Klik "Create Application"
3. Pilih "Docker Compose"
4. Masukkan Git repository URL

### 2. **Environment Variables**
Set environment variables berikut di Dokploy:

```bash
# Security
SECRET_KEY=your-production-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Database Configuration (External MongoDB)
MONGO_CONNECTION_STRING=mongodb://username:password@your-mongodb-host:27017/mindframe?authSource=admin

# Frontend Configuration
REACT_APP_API_URL=https://api.your-domain.com
```

### 3. **Domain Configuration**

#### Option A: Using Dokploy UI (v0.7.0+) - RECOMMENDED
**Sejak v0.7.0, Dokploy mendukung domain secara native!**

1. Go to your application in Dokploy dashboard
2. Navigate to "Domains" section
3. Add domains:
   - **Frontend**: `your-domain.com`
   - **Backend**: `api.your-domain.com`
4. Dokploy akan otomatis mengkonfigurasi Traefik routing
5. SSL certificates akan di-generate otomatis

#### Option B: Manual Configuration (untuk versi < v0.7.0)
Jika menggunakan versi Dokploy yang lebih lama, domains sudah dikonfigurasi dalam Traefik labels di `docker-compose.yml`:

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.frontend-app.rule=Host(`your-domain.com`)"
  - "traefik.http.routers.frontend-app.entrypoints=web"
  - "traefik.http.services.frontend-app.loadbalancer.server.port=80"
  - "traefik.docker.network=dokploy-network"
```

### 4. **DNS Configuration**
Buat A records di DNS provider:
```
your-domain.com        A    [DOKPLOY_SERVER_IP]
api.your-domain.com    A    [DOKPLOY_SERVER_IP]
```

## 🔒 SSL/HTTPS Configuration

Dokploy secara otomatis menangani SSL dengan Let's Encrypt:

1. **Automatic SSL**: Dokploy akan generate SSL certificate
2. **Custom SSL**: Upload certificate di Dokploy dashboard
3. **Redirect HTTP to HTTPS**: Enable di Dokploy settings

## 📝 Deployment Steps

### 1. **Prepare Repository**
```bash
# Commit changes
git add .
git commit -m "Configure for Dokploy deployment"
git push origin main
```

### 2. **Deploy via Dokploy**
1. Trigger deployment dari Dokploy dashboard
2. Monitor logs untuk memastikan deployment berhasil
3. Check health endpoints:
   - Frontend: `https://your-domain.com`
   - Backend: `https://api.your-domain.com/health`

### 3. **Verify Deployment**
```bash
# Test frontend
curl -I https://your-domain.com

# Test backend API
curl https://api.your-domain.com/health

# Test database connection
curl https://api.your-domain.com/api/health
```

## 🔧 Configuration Files Modified

### 1. **docker-compose.yml**
- Added `dokploy-network` to all services
- Added Traefik labels for routing
- Changed `ports` to `expose` for security
- Disabled nginx service (Traefik handles routing)

### 2. **Environment Variables**
- Updated to use external MongoDB
- Added production-ready configurations
- Configured CORS for domain access

## 📊 Monitoring & Logs

### 1. **Dokploy Dashboard**
- View application status
- Monitor resource usage
- Access container logs

### 2. **Health Checks**
```bash
# Backend health
curl https://api.your-domain.com/health

# Database health
curl https://api.your-domain.com/api/health
```

### 3. **Log Access**
```bash
# Via Dokploy dashboard
# Or via Docker commands on server:
docker logs mindframe-backend
docker logs mindframe-frontend
docker logs mindframe-redis
```

## 🚨 Troubleshooting

### 1. **Dokploy tidak detect docker-compose.yml**
- **Pastikan file ada di root repository** (bukan di subfolder)
- **Check file permissions** - file harus readable
- **Verify Git repository access** - Dokploy harus bisa clone repo
- **Pastikan format docker-compose.yml valid** - test dengan `docker-compose config`
- **Check Dokploy logs** untuk error messages
- **Restart Dokploy service** jika perlu: `sudo systemctl restart dokploy`
- **Verify network configuration** - pastikan `dokploy-network` exists

### 2. **Domain tidak accessible**
- Check DNS configuration
- Verify Traefik labels
- Check Dokploy network configuration
- Monitor Traefik logs

### 3. **SSL Certificate Issues**
- Check domain DNS propagation
- Verify Let's Encrypt rate limits
- Check Dokploy SSL settings

### 4. **Database Connection Issues**
- Verify MongoDB connection string
- Check network connectivity from Dokploy server
- Test MongoDB credentials

### 5. **Service Health Check Failures**
```bash
# Check service status
docker ps

# Check service logs
docker logs [container_name]

# Test internal connectivity
docker exec mindframe-backend curl http://localhost:5001/health
```

## 🔄 Updates & Maintenance

### 1. **Application Updates**
1. Push changes to Git repository
2. Trigger redeploy dari Dokploy dashboard
3. Monitor deployment logs
4. Verify application functionality

### 2. **Environment Variable Updates**
1. Update variables di Dokploy dashboard
2. Restart application
3. Verify configuration changes

### 3. **Backup Strategy**
```bash
# Database backup (external MongoDB)
mongodump --uri="$MONGO_CONNECTION_STRING" --out=./backup/$(date +%Y%m%d)

# Application data backup
# Backup storage volumes if needed
```

## 📞 Support

- **Dokploy Documentation**: https://docs.dokploy.com/
- **Dokploy Discord**: https://discord.com/invite/2tBnJ3jDJc
- **Troubleshooting**: Lihat `DOKPLOY_TROUBLESHOOTING.md` untuk solusi masalah umum
- **MongoDB Setup**: Lihat `EXTERNAL_MONGODB_SETUP.md`
- **Application Docs**: Lihat `DOCKER_DEPLOYMENT.md`

## 🎯 Production Checklist

- [ ] External MongoDB configured dan accessible
- [ ] Environment variables set dengan production values
- [ ] Domain DNS records configured
- [ ] SSL certificates working
- [ ] Health checks passing
- [ ] Backup strategy implemented
- [ ] Monitoring setup
- [ ] Security review completed