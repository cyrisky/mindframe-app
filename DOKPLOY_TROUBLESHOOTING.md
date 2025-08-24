# 🔧 Dokploy Troubleshooting Guide

Panduan mengatasi masalah umum saat deploy dengan Dokploy.

## ❌ Problem: Dokploy tidak mendeteksi docker-compose.yml

### ✅ Solusi yang Sudah Diterapkan

1. **File docker-compose.yml sudah valid** ✓
   ```bash
   # Test validasi berhasil
   docker compose config
   ```

2. **Network configuration sudah benar** ✓
   ```yaml
   networks:
     dokploy-network:
       external: true
     mindframe-network:
       driver: bridge
   ```

3. **Traefik labels sudah lengkap** ✓
   ```yaml
   labels:
     - "traefik.enable=true"
     - "traefik.http.routers.frontend-app.rule=Host(`your-domain.com`)"
     - "traefik.http.routers.frontend-app.entrypoints=web"
     - "traefik.http.services.frontend-app.loadbalancer.server.port=80"
     - "traefik.docker.network=dokploy-network"
   ```

4. **Port configuration menggunakan expose** ✓
   ```yaml
   expose:
     - "80"    # Frontend
     - "5001"  # Backend
     - "6379"  # Redis
   ```

### 🔍 Langkah Troubleshooting Tambahan

#### 1. **Verifikasi Lokasi File**
```bash
# Pastikan file ada di root repository
ls -la docker-compose.yml

# File harus di root, bukan di subfolder
pwd  # Harus di /path/to/mindframe-app/
```

#### 2. **Check Git Repository**
```bash
# Pastikan file sudah di-commit
git status
git add docker-compose.yml
git commit -m "Add Dokploy-compatible docker-compose.yml"
git push origin main
```

#### 3. **Verifikasi Dokploy Network**
```bash
# Di server Dokploy, check network exists
docker network ls | grep dokploy

# Jika tidak ada, create network
docker network create dokploy-network
```

#### 4. **Check Dokploy Version**
```bash
# Check versi Dokploy
dokploy --version

# Untuk v0.7.0+, gunakan UI domain management
# Untuk versi lama, gunakan Traefik labels manual
```

#### 5. **Restart Dokploy Services**
```bash
# Restart Dokploy
sudo systemctl restart dokploy

# Check status
sudo systemctl status dokploy

# Check logs
sudo journalctl -u dokploy -f
```

#### 6. **Validate Docker Compose Syntax**
```bash
# Test di local
docker compose config

# Test specific services
docker compose config --services
```

### 🎯 Checklist Deployment

- [ ] File `docker-compose.yml` ada di root repository
- [ ] File sudah di-commit dan push ke Git
- [ ] Repository accessible oleh Dokploy
- [ ] Network `dokploy-network` exists di server
- [ ] Dokploy service running
- [ ] Environment variables configured
- [ ] Domain DNS records configured

### 🔄 Alternative Deployment Methods

#### Method 1: Manual File Upload
1. Login ke Dokploy dashboard
2. Create new Docker Compose application
3. Upload `docker-compose.yml` manually
4. Configure environment variables
5. Deploy

#### Method 2: Git Repository Clone
1. Ensure repository is public atau add SSH key
2. Use repository URL di Dokploy
3. Specify branch (main/master)
4. Auto-deploy on push (optional)

#### Method 3: Local Build & Push
```bash
# Build images locally
docker compose build

# Tag dan push ke registry
docker tag mindframe-frontend your-registry/mindframe-frontend
docker tag mindframe-backend your-registry/mindframe-backend
docker push your-registry/mindframe-frontend
docker push your-registry/mindframe-backend

# Update docker-compose.yml dengan registry images
```

### 📋 Environment Variables Checklist

```bash
# Required variables untuk Dokploy
SECRET_KEY=your-production-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
MONGO_CONNECTION_STRING=mongodb://...
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
REACT_APP_API_URL=https://api.your-domain.com
```

### 🌐 Domain Configuration Steps

#### For Dokploy v0.7.0+
1. **Dokploy Dashboard**:
   - Go to Application → Domains
   - Add `your-domain.com` for frontend
   - Add `api.your-domain.com` for backend
   - Enable SSL (automatic)

2. **DNS Configuration**:
   ```
   your-domain.com        A    [DOKPLOY_SERVER_IP]
   api.your-domain.com    A    [DOKPLOY_SERVER_IP]
   ```

#### For Dokploy < v0.7.0
1. **Manual Traefik Labels** (already configured)
2. **DNS Configuration** (same as above)
3. **SSL Configuration** via Traefik

### 🚨 Common Issues & Solutions

#### Issue: "Network dokploy-network not found"
```bash
# Solution: Create network
docker network create dokploy-network
sudo systemctl restart dokploy
```

#### Issue: "Port already in use"
```bash
# Solution: Use expose instead of ports
# Already configured in our docker-compose.yml
expose:
  - "80"
# Instead of:
# ports:
#   - "80:80"
```

#### Issue: "Traefik not routing correctly"
```bash
# Check Traefik dashboard
http://your-dokploy-server:8080

# Verify labels
docker inspect mindframe-frontend | grep traefik
```

#### Issue: "SSL certificate not working"
```bash
# Check Let's Encrypt logs
docker logs traefik | grep acme

# Verify domain DNS
nslookup your-domain.com
```

### 📞 Getting Help

1. **Dokploy Discord**: https://discord.com/invite/2tBnJ3jDJc
2. **Dokploy Documentation**: https://docs.dokploy.com/
3. **GitHub Issues**: https://github.com/Dokploy/dokploy/issues

### 📝 Debug Commands

```bash
# Check Dokploy status
sudo systemctl status dokploy

# Check Docker status
docker ps
docker network ls

# Check application logs
docker logs mindframe-frontend
docker logs mindframe-backend
docker logs mindframe-redis

# Check Traefik routing
curl -H "Host: your-domain.com" http://localhost
curl -H "Host: api.your-domain.com" http://localhost

# Test internal connectivity
docker exec mindframe-backend curl http://localhost:5001/health
docker exec mindframe-frontend curl http://localhost:80
```

### 🎯 Next Steps

Jika masalah masih berlanjut:

1. **Collect Information**:
   - Dokploy version
   - Docker version
   - Server OS
   - Error logs

2. **Try Alternative**:
   - Manual deployment
   - Different Git repository
   - Local registry

3. **Contact Support**:
   - Dokploy Discord dengan informasi lengkap
   - Include logs dan konfigurasi
   - Mention specific error messages