# Product Configuration Schema

## MongoDB Collection: `product_configs`

This collection stores product configurations that define which tests are included in each product and their order.

### Schema Structure

```json
{
  "_id": ObjectId,
  "productId": "minatBakatUmum",
  "productName": "Minat Bakat Umum",
  "description": "Comprehensive assessment combining personality, values, and aptitude tests",
  "tests": [
    {
      "testType": "minatBakatStudent",
      "order": 1,
      "required": true
    },
    {
      "testType": "kepribadian",
      "order": 2,
      "required": true
    },
    {
      "testType": "personal_values",
      "order": 3,
      "required": true
    }
  ],
  "staticContent": {
    "coverPage": {
      "title": "Laporan Minat Bakat Umum",
      "subtitle": "Analisis Komprehensif Kepribadian, Nilai, dan Minat Bakat",
      "logoUrl": "/assets/logo.png",
      "includeUserName": true,
      "includeDate": true
    },
    "introduction": {
      "title": "Pengantar",
      "content": "Laporan ini menyajikan analisis komprehensif dari tiga aspek penting dalam pengembangan diri: minat bakat, kepribadian, dan nilai-nilai personal. Kombinasi ketiga aspek ini memberikan gambaran holistik untuk membantu dalam pengambilan keputusan karir dan pengembangan personal."
    },
    "closing": {
      "title": "Kesimpulan",
      "content": "Hasil dari ketiga tes ini dapat digunakan sebagai panduan dalam memilih jalur karir yang sesuai dengan minat, bakat, kepribadian, dan nilai-nilai Anda. Disarankan untuk mendiskusikan hasil ini dengan konselor atau mentor untuk mendapatkan panduan yang lebih personal."
    }
  },
  "isActive": true,
  "createdAt": ISODate,
  "updatedAt": ISODate,
  "createdBy": "admin",
  "updatedBy": "admin"
}
```

### Field Descriptions

- **productId**: Unique identifier for the product (used in API calls)
- **productName**: Human-readable name for the product
- **description**: Brief description of what the product includes
- **tests**: Array of test configurations
  - **testType**: Must match existing template types (kepribadian, personal_values, minatBakatStudent, etc.)
  - **order**: Sequential order for PDF generation (1, 2, 3, ...)
  - **required**: Whether this test is mandatory for the product
- **staticContent**: Product-level content for PDF generation
  - **coverPage**: Cover page configuration
  - **introduction**: Introduction section content
  - **closing**: Closing section content
- **isActive**: Whether this product configuration is currently active
- **createdAt/updatedAt**: Timestamps for tracking changes
- **createdBy/updatedBy**: User tracking for admin purposes

### API Integration

The API endpoint will:
1. Receive: `{"code": "rb5YrWGWJXOHoj6r", "product": "minatBakatUmum"}`
2. Look up product configuration from `product_configs` collection
3. Retrieve test results from `workflow.psikotes_v2` collection using the code
4. Generate sequential PDF combining all tests in specified order
5. Include static content (cover, intro, closing) with user name

### Example Products

1. **minatBakatUmum**: minatBakatStudent + kepribadian + personal_values
2. **kepribadianLengkap**: kepribadian + personal_values + motivationBoost
3. **minatBakatSiswa**: minatBakatStudent + petaPerilaku