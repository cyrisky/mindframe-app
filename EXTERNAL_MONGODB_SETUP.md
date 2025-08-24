# 🗄️ External MongoDB Setup Guide

Panduan untuk mengatur MongoDB eksternal untuk aplikasi Mindframe.

## 📋 Pilihan MongoDB Eksternal

### 1. MongoDB Atlas (Cloud - Recommended)

**Keuntungan:**
- Fully managed service
- Automatic backups
- Built-in security
- Global clusters
- Free tier tersedia

**Setup Steps:**

1. **Buat Account MongoDB Atlas**
   - Kunjungi [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Daftar akun gratis

2. **Buat Cluster**
   - Pilih "Build a Database"
   - Pilih "Shared" untuk free tier
   - Pilih region terdekat
   - Buat cluster

3. **Setup Database User**
   ```
   Username: mindframe_user
   Password: [generate strong password]
   Database Admin privileges
   ```

4. **Whitelist IP Address**
   - Tambahkan IP address server Anda
   - Untuk development: `0.0.0.0/0` (tidak disarankan untuk production)

5. **Get Connection String**
   ```
   mongodb+srv://mindframe_user:<password>@cluster0.xxxxx.mongodb.net/mindframe?retryWrites=true&w=majority
   ```

### 2. Self-Hosted MongoDB

**Setup untuk Ubuntu/Debian:**

```bash
# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Create database and user
mongosh
```

**MongoDB Shell Commands:**
```javascript
// Switch to admin database
use admin

// Create admin user
db.createUser({
  user: "admin",
  pwd: "your-admin-password",
  roles: ["userAdminAnyDatabase", "dbAdminAnyDatabase", "readWriteAnyDatabase"]
})

// Switch to mindframe database
use mindframe

// Create application user
db.createUser({
  user: "mindframe_user",
  pwd: "your-app-password",
  roles: ["readWrite"]
})

// Create required collections and indexes
db.createCollection("users")
db.createCollection("templates")
db.createCollection("reports")
db.createCollection("pdf_documents")
db.createCollection("sessions")
db.createCollection("assessment_results")
db.createCollection("job_queue")

// Create indexes
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "created_at": 1 })
db.templates.createIndex({ "name": 1 })
db.templates.createIndex({ "created_at": 1 })
db.reports.createIndex({ "user_id": 1 })
db.reports.createIndex({ "created_at": 1 })
db.pdf_documents.createIndex({ "report_id": 1 })
db.pdf_documents.createIndex({ "created_at": 1 })
db.sessions.createIndex({ "session_id": 1 }, { unique: true })
db.sessions.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 })
db.assessment_results.createIndex({ "user_id": 1 })
db.assessment_results.createIndex({ "assessment_type": 1 })
db.assessment_results.createIndex({ "created_at": 1 })
db.job_queue.createIndex({ "status": 1 })
db.job_queue.createIndex({ "created_at": 1 })
db.job_queue.createIndex({ "scheduled_at": 1 })
```

**Connection String:**
```
mongodb://mindframe_user:your-app-password@your-server-ip:27017/mindframe?authSource=mindframe
```

### 3. Cloud Providers

#### AWS DocumentDB
```
mongodb://username:password@docdb-cluster.cluster-xxxxx.us-east-1.docdb.amazonaws.com:27017/mindframe?ssl=true&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false
```

#### Google Cloud MongoDB
```
mongodb://username:password@mongodb-instance-ip:27017/mindframe?authSource=admin
```

#### Azure Cosmos DB (MongoDB API)
```
mongodb://account-name:password@account-name.mongo.cosmos.azure.com:10255/mindframe?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@account-name@
```

## 🔧 Konfigurasi Aplikasi

### 1. Update Environment Variables

Edit file `.env.docker`:
```bash
# Database Configuration (External MongoDB)
MONGO_CONNECTION_STRING=mongodb://username:password@your-mongodb-host:27017/mindframe?authSource=admin
```

### 2. Test Connection

```bash
# Test connection dengan mongosh
mongosh "$MONGO_CONNECTION_STRING" --eval "db.adminCommand('ping')"

# Test dari aplikasi
docker-compose exec backend python -c "from src.services.database_service import DatabaseService; print(DatabaseService().health_check())"
```

## 🔒 Security Best Practices

### 1. Connection Security
- **Gunakan SSL/TLS** untuk koneksi
- **Whitelist IP** yang diperlukan saja
- **Strong passwords** untuk database users
- **Separate users** untuk aplikasi dan admin

### 2. Network Security
```bash
# Untuk production, gunakan private networks
# Contoh connection string dengan SSL:
mongodb://user:pass@host:27017/db?ssl=true&authSource=admin
```

### 3. Backup Strategy
```bash
# Regular backup
mongodump --uri="$MONGO_CONNECTION_STRING" --out=./backup/$(date +%Y%m%d)

# Automated backup script
#!/bin/bash
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR
mongodump --uri="$MONGO_CONNECTION_STRING" --out=$BACKUP_DIR
echo "Backup completed: $BACKUP_DIR"
```

## 🚀 Migration dari Local MongoDB

Jika Anda memiliki data di MongoDB lokal:

```bash
# Export dari local MongoDB
mongodump --host localhost:27017 --db mindframe --out ./local_backup

# Import ke external MongoDB
mongorestore --uri="$MONGO_CONNECTION_STRING" ./local_backup/mindframe
```

## 📊 Monitoring & Maintenance

### 1. Health Checks
```bash
# Check database status
mongosh "$MONGO_CONNECTION_STRING" --eval "db.adminCommand('ping')"

# Check collections
mongosh "$MONGO_CONNECTION_STRING" --eval "db.adminCommand('listCollections')"
```

### 2. Performance Monitoring
```bash
# Check database stats
mongosh "$MONGO_CONNECTION_STRING" --eval "db.stats()"

# Check slow queries
mongosh "$MONGO_CONNECTION_STRING" --eval "db.adminCommand('currentOp')"
```

## 🆘 Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Check network connectivity
   - Verify IP whitelist
   - Check firewall settings

2. **Authentication Failed**
   - Verify username/password
   - Check authSource parameter
   - Ensure user has proper permissions

3. **SSL/TLS Issues**
   - Add `ssl=true` to connection string
   - For self-signed certificates: `ssl=true&tlsAllowInvalidCertificates=true`

### Debug Commands
```bash
# Test basic connectivity
telnet your-mongodb-host 27017

# Test with mongosh
mongosh "mongodb://your-host:27017" --eval "db.adminCommand('hello')"

# Check from application
docker-compose logs backend | grep -i mongo
```

## 📞 Support

Untuk bantuan lebih lanjut:
- MongoDB Atlas: [Support Portal](https://support.mongodb.com/)
- Community: [MongoDB Community Forums](https://community.mongodb.com/)
- Documentation: [MongoDB Manual](https://docs.mongodb.com/)