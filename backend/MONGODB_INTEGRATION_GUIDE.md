# MongoDB Personal Values Integration Guide

## Overview

Panduan ini menjelaskan cara mengintegrasikan payload MongoDB dengan sistem generasi PDF Personal Values. Sistem ini mengkonversi data `personalValues` dari MongoDB menjadi laporan PDF yang terformat dengan interpretasi yang sesuai.

## Struktur Payload MongoDB

### Format Input
```json
{
  "_id": "...",
  "createdDate": "2024-01-15T10:30:00Z",
  "orderNumber": "ORD-12345",
  "code": "ABC123",
  "status": "completed",
  "name": "Jhon Doe",
  "email": "jhon@example.com",
  "phoneNumber": "+62812345678",
  "productName": "Personal Values Assessment",
  "package": "premium",
  "testResult": {
    "personalValues": {
      "formName": "Tes Tujuan Hidup dan Personal Value",
      "formId": "npVJq1",
      "result": {
        "value": "universalism",
        "score": {
          "universalism": 28,
          "security": 27,
          "self_direction": 23,
          "benevolence": 22,
          "achievement": 21,
          "hedonism": 20,
          "power": 19,
          "stimulation": 18,
          "tradition": 17,
          "conformity": 16
        }
      }
    }
  }
}
```

### Field Requirements

#### Required Fields
- `testResult.personalValues.result.score`: Object dengan skor untuk setiap nilai personal
- `name`: Nama klien
- `email`: Email klien

#### Optional Fields
- `phoneNumber`: Nomor telepon klien
- `orderNumber`: Nomor order
- `createdDate`: Tanggal test (ISO format)
- `testResult.personalValues.formName`: Nama form
- `testResult.personalValues.formId`: ID form
- `testResult.personalValues.result.value`: Top value

## Key Mapping

Sistem melakukan mapping dari key MongoDB ke key interpretasi:

| MongoDB Key | Interpretation Key | Indonesian Title |
|-------------|-------------------|------------------|
| universalism | universalism | Universalisme (Universalism) |
| security | security | Keamanan (Security) |
| self_direction | selfDirection | Kemandirian (Self-Direction) |
| benevolence | benevolence | Kebajikan (Benevolence) |
| hedonism | hedonism | Hedonisme (Hedonism) |
| achievement | achievement | Pencapaian (Achievement) |
| power | power | Kekuasaan (Power) |
| Stimulation | stimulation | Stimulasi (Stimulation) |
| tradition | tradition | Tradisi (Tradition) |
| conformity | conformity | Konformitas (Conformity) |

## Implementasi

### 1. Service Class

```python
from src.services.mongo_personal_values_service import MongoPersonalValuesService

# Initialize service
service = MongoPersonalValuesService(
    template_dir="/path/to/templates"
)

# Validate payload
validation = service.validate_mongo_payload(mongo_payload)
if not validation['valid']:
    print(f"Validation errors: {validation['errors']}")
    return

# Generate PDF
result = service.process_mongo_payload_to_pdf(
    mongo_payload,
    "output_report.pdf",
    save_intermediate_files=True  # Optional: save debug files
)

if result['success']:
    print(f"PDF generated: {result['output_path']}")
    print(f"Client: {result['client_name']}")
    print(f"Top values: {result['top_values']}")
else:
    print(f"Error: {result['error']}")
```

### 2. API Endpoints

#### Generate PDF
```bash
POST /api/personal-values/generate-pdf
Content-Type: application/json

{
  "mongoData": { ... },  // Full MongoDB document
  "options": {
    "saveIntermediateFiles": false,
    "customOutputName": "custom_name.pdf"
  }
}
```

#### Validate Payload
```bash
POST /api/personal-values/validate
Content-Type: application/json

{
  "mongoData": { ... }  // Full MongoDB document
}
```

#### Preview Data
```bash
POST /api/personal-values/preview
Content-Type: application/json

{
  "mongoData": { ... }  // Full MongoDB document
}
```

#### Health Check
```bash
GET /api/personal-values/health
```

### 3. Start API Server

```bash
cd /path/to/backend
python src/api/personal_values_api.py
```

Server akan berjalan di `http://localhost:5000`

## Output

### PDF Report
Sistem menghasilkan PDF report yang berisi:
- Informasi klien (nama, email, tanggal test)
- Top 3 nilai personal berdasarkan skor tertinggi
- Deskripsi setiap nilai
- Manifestasi dalam kehidupan sehari-hari
- Kekuatan dan tantangan
- Badge ranking untuk setiap nilai

### Intermediate Files (Optional)
Jika `save_intermediate_files=True`:
- `*_mapped_data.json`: Data yang sudah dimapping
- `*_template_data.json`: Data untuk template
- `*.html`: HTML yang dirender

## Testing

### 1. Direct Service Test
```bash
python test_direct_service.py
```

### 2. Full Integration Test
```bash
python test_simple_integration.py
```

### 3. API Test
```bash
# Start server first
python src/api/personal_values_api.py

# In another terminal
python test_api_integration.py
```

## Error Handling

### Common Errors

1. **Missing personalValues**
   ```json
   {
     "error": "personalValues not found in testResult",
     "code": "VALIDATION_FAILED"
   }
   ```

2. **Missing scores**
   ```json
   {
     "error": "scores not found in personalValues.result",
     "code": "VALIDATION_FAILED"
   }
   ```

3. **Invalid key mapping**
   ```json
   {
     "error": "Key 'invalid_key' not found in interpretation data",
     "code": "PDF_GENERATION_FAILED"
   }
   ```

### Validation Response
```json
{
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": []
  },
  "additionalInfo": {
    "clientInfo": {
      "name": "Jhon Doe",
      "email": "jhon@example.com"
    },
    "formInfo": {
      "formId": "npVJq1",
      "formName": "Tes Tujuan Hidup dan Personal Value"
    },
    "topValues": [
      {"key": "universalism", "score": 28, "rank": 1},
      {"key": "security", "score": 27, "rank": 2},
      {"key": "self_direction", "score": 23, "rank": 3}
    ],
    "totalScores": 10
  }
}
```

## Dependencies

### Python Packages
```bash
pip install jinja2 weasyprint requests flask flask-cors
```

### System Requirements
- Python 3.7+
- WeasyPrint dependencies (untuk PDF generation)
- Template HTML file: `personal_values_report_template.html`
- Interpretation data: `interpretation-personal-values.json`

## File Structure

```
backend/
├── src/
│   ├── services/
│   │   └── mongo_personal_values_service.py
│   └── api/
│       └── personal_values_api.py
├── templates/
│   └── personal_values_report_template.html
├── test_direct_service.py
├── test_simple_integration.py
├── test_api_integration.py
└── MONGODB_INTEGRATION_GUIDE.md
```

## Example Usage

### Python Script
```python
import json
from src.services.mongo_personal_values_service import MongoPersonalValuesService

# Load MongoDB data
with open('mongoData-example.json', 'r') as f:
    mongo_data = json.load(f)

# Initialize service
service = MongoPersonalValuesService()

# Generate PDF
result = service.process_mongo_payload_to_pdf(
    mongo_data,
    'personal_values_report.pdf'
)

print(f"Success: {result['success']}")
print(f"Client: {result['client_name']}")
print(f"Top values: {result['top_values']}")
```

### cURL Example
```bash
curl -X POST http://localhost:5000/api/personal-values/generate-pdf \
  -H "Content-Type: application/json" \
  -d @mongoData-example.json \
  --output report.pdf
```

## Next Steps

1. **Integration dengan Main App**: Integrasikan service ini dengan aplikasi utama
2. **Database Integration**: Hubungkan langsung dengan MongoDB database
3. **Authentication**: Tambahkan autentikasi untuk API endpoints
4. **Caching**: Implementasi caching untuk performa yang lebih baik
5. **Monitoring**: Tambahkan logging dan monitoring

## Support

Untuk pertanyaan atau masalah:
1. Jalankan health check: `GET /api/personal-values/health`
2. Validasi payload: `POST /api/personal-values/validate`
3. Preview data: `POST /api/personal-values/preview`
4. Check logs untuk error details