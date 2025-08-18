# Template System for Mindframe App

## Overview

Sistem template yang telah dibuat untuk aplikasi Mindframe menggunakan **Jinja2** sebagai template engine dan **WeasyPrint** untuk menghasilkan PDF. Sistem ini dirancang khusus untuk menghasilkan laporan psikologi yang profesional dan terstruktur.

## Komponen Utama

### 1. Template Renderer Service
**File**: `src/services/template_renderer_service.py`

Service utama yang menangani:
- Loading data interpretasi dari file JSON
- Rendering template HTML dengan Jinja2
- Konversi HTML ke PDF menggunakan WeasyPrint
- Validasi template dan data

### 2. Template HTML
**File**: `templates/personal_values_report_template.html`

Template untuk laporan Personal Values yang mencakup:
- Header dengan informasi klien
- Nilai-nilai utama dengan ranking
- Deskripsi, manifestasi, dan tantangan untuk setiap nilai
- Summary dan rekomendasi
- Styling CSS yang profesional

### 3. Test Suite
**Files**: 
- `tests/test_template_renderer_service.py`
- `tests/test_personal_values_template.py`

## Cara Penggunaan

### Basic Usage

```python
from services.template_renderer_service import TemplateRendererService

# Initialize service
renderer = TemplateRendererService()

# Generate Personal Values report
client_info = {
    'name': 'John Doe',
    'age': '28',
    'test_date': '13 Agustus 2024'
}

pdf_bytes = renderer.generate_personal_values_report(
    interpretation_data_path='/path/to/interpretation-personal-values.json',
    client_info=client_info,
    output_path='report.pdf'
)
```

### Advanced Usage

```python
# Load and prepare data manually
interpretation_data = renderer.load_interpretation_data('data.json')
template_data = renderer.prepare_personal_values_data(interpretation_data, client_info)

# Render HTML
html_content = renderer.render_template('personal_values_report_template.html', template_data)

# Generate PDF with custom CSS
custom_css = "body { font-family: 'Times New Roman'; }"
pdf_bytes = renderer.generate_pdf(html_content, 'custom_report.pdf', custom_css)
```

## Template Variables

Template Personal Values menggunakan variabel berikut:

### Client Information
- `client_name`: Nama klien
- `client_age`: Usia klien
- `test_date`: Tanggal tes
- `report_date`: Tanggal laporan dibuat

### Test Information
- `test_name`: Nama tes
- `test_type`: Jenis tes
- `top_n`: Jumlah nilai teratas

### Values Data
- `top_values`: Array nilai-nilai utama dengan struktur:
  ```python
  {
      'key': 'achievement',
      'title': 'Pencapaian',
      'description': 'Deskripsi nilai...',
      'manifestation': 'Cara manifestasi...',
      'strengthChallenges': {
          'strength': 'Kekuatan...',
          'challenge': 'Tantangan...'
      }
  }
  ```

## Struktur Data Interpretasi

File JSON interpretasi harus memiliki struktur:

```json
{
    "testName": "Personal Values Test",
    "testType": "top-n-dimension",
    "results": {
        "topN": 3,
        "dimensions": {
            "achievement": {
                "title": "Pencapaian",
                "description": "...",
                "manifestation": "...",
                "strengthChallenges": {
                    "strength": "...",
                    "challenge": "..."
                }
            }
        }
    }
}
```

## Testing

Jalankan test suite:

```bash
# Test template renderer service
python tests/test_template_renderer_service.py

# Test personal values template
python tests/test_personal_values_template.py

# Run all tests with pytest
pytest tests/ -v
```

## Dependencies

- **Jinja2**: Template engine
- **WeasyPrint**: HTML to PDF conversion
- **Pytest**: Testing framework

## File Output

Sistem menghasilkan file PDF dengan:
- Ukuran rata-rata: 170-180 KB
- Format: A4
- Styling: Professional dengan color scheme biru-abu
- Font: Arial/sans-serif

## Generated Files

Contoh file yang dihasilkan:
- `personal_values_report.pdf` (183 KB)
- `personal_values_service_test.pdf` (174 KB)
- `test_complete_personal_values_report.pdf` (174 KB)

## Future Enhancements

1. **Multi-template Support**: Template untuk jenis tes lain
2. **Custom Styling**: CSS themes yang dapat dikonfigurasi
3. **Internationalization**: Support multi-bahasa
4. **Chart Integration**: Integrasi dengan chart libraries
5. **Email Integration**: Kirim laporan via email
6. **Batch Processing**: Generate multiple reports sekaligus

## Notes

- Template menggunakan sintaks Jinja2 (`{% %}` dan `{{ }}`)
- CSS styling sudah dioptimasi untuk print media
- Error handling sudah diimplementasi untuk skenario umum
- Service dapat di-extend untuk template jenis lain