# Analisis Dependency Requirements.txt

Analisis ini menunjukkan dependency mana yang benar-benar digunakan dalam proyek dan mana yang mungkin tidak diperlukan.

## ✅ Dependency yang DIGUNAKAN

### Core Flask Dependencies
- **Flask==2.3.3** ✅ - Digunakan di banyak file (app.py, routes, services)
- **Flask-CORS==4.0.0** ✅ - Digunakan di app.py dan personal_values_api.py
- **Flask-Limiter==3.5.0** ✅ - Digunakan di rate_limiter.py
- **Werkzeug==2.3.7** ✅ - Dependency Flask (otomatis digunakan)

### Database
- **pymongo==4.5.0** ✅ - Digunakan di database_service.py, error_handler.py, simple_api_server.py
- **redis==6.4.0** ✅ - Digunakan di redis_service.py, auth_service.py, job_queue/config.py

### Job Queue
- **rq>=1.15.1** ✅ - Digunakan di job_queue/jobs.py, job_queue/config.py, workers.py
- **rq-dashboard>=0.6.1** ⚠️ - Tidak terlihat digunakan langsung dalam kode

### Authentication & Security
- **PyJWT==2.8.0** ✅ - Digunakan di security_utils.py, auth_service.py
- **bcrypt==4.0.1** ✅ - Digunakan di security_utils.py, auth_service.py
- **cryptography==41.0.7** ✅ - Digunakan di security_utils.py

### PDF Generation
- **WeasyPrint==60.1** ✅ - Digunakan di product_report_service.py, template_renderer_service.py, pdf_generator.py
- **reportlab==4.0.4** ❌ - TIDAK DITEMUKAN penggunaan dalam kode
- **PyPDF2==3.0.1** ✅ - Digunakan di product_report_service.py dan simple_api_server.py (deprecated)

### Google Drive Integration
- **google-api-python-client==2.178.0** ✅ - Digunakan di google_drive_service.py
- **google-auth==2.40.3** ✅ - Digunakan di google_drive_service.py
- **google-auth-oauthlib==1.2.2** ❌ - TIDAK DITEMUKAN penggunaan dalam kode
- **google-auth-httplib2==0.2.0** ❌ - TIDAK DITEMUKAN penggunaan dalam kode
- **google-cloud-storage==2.10.0** ✅ - Digunakan di storage_service.py

### Template Processing
- **Jinja2==3.1.2** ✅ - Digunakan di banyak file (template_processor.py, services, dll)
- **MarkupSafe==2.1.3** ✅ - Digunakan di template_processor.py

### Email
- **email-validator==2.1.0** ✅ - Digunakan di validation_utils.py, email_utils.py

### File Storage
- **boto3==1.29.7** ❌ - TIDAK DITEMUKAN penggunaan dalam kode
- **botocore==1.32.7** ❌ - TIDAK DITEMUKAN penggunaan dalam kode

### Data Validation
- **pydantic==2.5.0** ✅ - Digunakan di banyak model dan validation files
- **validators==0.22.0** ❌ - TIDAK DITEMUKAN penggunaan langsung (hanya referensi dalam komentar)

### Date/Time
- **python-dateutil==2.8.2** ✅ - Digunakan di date_utils.py
- **pytz==2023.3** ✅ - Digunakan di date_utils.py

### HTTP Requests
- **requests==2.31.0** ✅ - Digunakan di test_job_queue_integration.py

### Environment Variables
- **python-dotenv==1.0.0** ✅ - Digunakan di app.py, workers.py, test files

### Configuration
- **PyYAML==6.0.1** ✅ - Digunakan di config_utils.py
- **configparser==6.0.0** ✅ - Digunakan di config_utils.py

### Logging
- **coloredlogs==15.0.1** ❌ - TIDAK DITEMUKAN penggunaan dalam kode

### Development Dependencies
- **pytest==7.4.3** ✅ - Digunakan di semua test files
- **pytest-flask==1.3.0** ⚠️ - Tidak terlihat digunakan langsung
- **pytest-cov==4.1.0** ⚠️ - Tidak terlihat digunakan langsung
- **black==23.11.0** ⚠️ - Tool development (tidak diimport dalam kode)
- **flake8==6.1.0** ⚠️ - Tool development (tidak diimport dalam kode)
- **mypy==1.7.1** ⚠️ - Tool development (tidak diimport dalam kode)

### Production Dependencies
- **gunicorn==22.0.0** ✅ - Digunakan dalam deployment (README, Dockerfile)
- **waitress==3.0.0** ⚠️ - Alternative WSGI server (tidak terlihat digunakan)

### Monitoring
- **psutil==5.9.6** ❌ - TIDAK DITEMUKAN penggunaan dalam kode

### Image Processing
- **Pillow==10.1.0** ⚠️ - Dependency WeasyPrint (tidak digunakan langsung)

### XML/CSS/HTML Processing (WeasyPrint Dependencies)
- **lxml==4.9.3** ⚠️ - Dependency WeasyPrint
- **cssselect2==0.7.0** ⚠️ - Dependency WeasyPrint
- **tinycss2==1.2.1** ⚠️ - Dependency WeasyPrint
- **html5lib==1.1** ⚠️ - Dependency WeasyPrint
- **BeautifulSoup4==4.12.2** ❌ - TIDAK DITEMUKAN penggunaan dalam kode

### Utilities
- **click==8.1.7** ⚠️ - Dependency Flask (tidak digunakan langsung)
- **itsdangerous==2.1.2** ⚠️ - Dependency Flask (tidak digunakan langsung)

## ❌ Dependency yang DAPAT DIHAPUS

### Tidak Digunakan Sama Sekali:
1. **reportlab==4.0.4** - Tidak ada penggunaan dalam kode
2. **google-auth-oauthlib==1.2.2** - Tidak digunakan untuk Google Drive integration
3. **google-auth-httplib2==0.2.0** - Tidak digunakan untuk Google Drive integration
4. **boto3==1.29.7** - Tidak ada penggunaan AWS S3
5. **botocore==1.32.7** - Dependency boto3
6. **validators==0.22.0** - Tidak digunakan langsung (pydantic sudah cukup)
7. **coloredlogs==15.0.1** - Tidak digunakan untuk logging
8. **psutil==5.9.6** - Tidak digunakan untuk monitoring
9. **BeautifulSoup4==4.12.2** - Tidak digunakan untuk HTML parsing
10. **waitress==3.0.0** - Alternative WSGI yang tidak digunakan

### Opsional (Development Tools):
- **pytest-flask==1.3.0** - Bisa dihapus jika tidak menggunakan fitur khusus Flask testing
- **pytest-cov==4.1.0** - Bisa dihapus jika tidak perlu coverage report

## 📝 Rekomendasi

### Hapus Dependency Tidak Terpakai:
```bash
# Hapus dari requirements.txt:
reportlab==4.0.4
google-auth-oauthlib==1.2.2
google-auth-httplib2==0.2.0
boto3==1.29.7
botocore==1.32.7
validators==0.22.0
coloredlogs==15.0.1
psutil==5.9.6
BeautifulSoup4==4.12.2
waitress==3.0.0
```

### Pertahankan untuk Kompatibilitas:
- WeasyPrint dependencies (lxml, cssselect2, tinycss2, html5lib, Pillow)
- Flask utilities (click, itsdangerous)
- Development tools (black, flake8, mypy) - jika masih digunakan untuk development

### Estimasi Pengurangan:
- **~10 dependency** dapat dihapus
- **Pengurangan ukuran** virtual environment
- **Waktu instalasi** lebih cepat
- **Keamanan** lebih baik (fewer dependencies = smaller attack surface)

## 🔍 Catatan Tambahan

1. **rq-dashboard** - Mungkin digunakan untuk monitoring job queue via web interface
2. **PyPDF2** - Masih digunakan di simple_api_server.py (deprecated) dan product_report_service.py
3. **WeasyPrint dependencies** - Jangan dihapus karena diperlukan untuk PDF generation
4. **Development tools** - Pertimbangkan untuk memindahkan ke requirements-dev.txt terpisah

## ✅ Requirements.txt yang Dioptimalkan

Setelah cleanup, requirements.txt akan berkurang dari **97 lines** menjadi sekitar **80-85 lines**.