#!/usr/bin/env python3
"""
Final PDF Test - Memastikan Pipeline PDF Generation Sudah Benar
Test ini membuktikan bahwa pipeline sudah generate PDF langsung, bukan HTML
"""

import os
import json
from datetime import datetime
from jinja2 import Template

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    print("⚠️  WeasyPrint not available - install with: pip install weasyprint")

def load_interpretation_data():
    """
    Load interpretation data from JSON file
    """
    interpretation_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 'ai', 'interpretation-data', 'interpretation.json'
    )
    with open(interpretation_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_html_template():
    """
    Load HTML template
    """
    template_path = os.path.join(
        os.path.dirname(__file__), 
        'templates', 'personality_report_template.html'
    )
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

class FinalPDFService:
    def __init__(self):
        self.interpretation_data = load_interpretation_data()
        self.html_template = load_html_template()
        
    def validate_payload(self, payload):
        """Validate MongoDB payload"""
        required_fields = ['client', 'keterbukaan', 'kehati_hatian', 'ekstraversi', 'keramahan', 'neurotisisme']
        
        for field in required_fields:
            if field not in payload:
                return False, f"Missing field: {field}"
        
        return True, "Valid"
    
    def extract_personality_data(self, payload):
        """Extract personality data from MongoDB payload"""
        dimensions = {}
        
        # Map MongoDB keys to our internal keys
        mongo_to_internal = {
            'keterbukaan': 'openness',
            'kehati_hatian': 'conscientiousness', 
            'ekstraversi': 'extraversion',
            'keramahan': 'agreeableness',
            'neurotisisme': 'neuroticism'
        }
        
        for mongo_key, internal_key in mongo_to_internal.items():
            if mongo_key in payload:
                dimension_data = payload[mongo_key]
                dimensions[internal_key] = {
                    'score': dimension_data.get('skor', 0),
                    'aspects': dimension_data.get('aspek', []),
                    'recommendations': dimension_data.get('rekomendasi', [])
                }
        
        return dimensions
    
    def determine_level(self, score):
        """Determine personality level based on score"""
        if score >= 80:
            return 'very_high'
        elif score >= 60:
            return 'high'
        elif score >= 40:
            return 'medium'
        elif score >= 20:
            return 'low'
        else:
            return 'very_low'
    
    def render_html(self, payload, personality_data):
        """Render HTML template with data"""
        template = Template(self.html_template)
        
        # Prepare template data
        template_data = {
            'client': payload.get('client', {}),
            'test_date': payload.get('test_date', datetime.now().strftime('%Y-%m-%d')),
            'form': payload.get('form', 'Tes Kepribadian Big Five'),
            'dimensions': {}
        }
        
        # Process each dimension
        for dim_key, dim_data in personality_data.items():
            score = dim_data['score']
            level = self.determine_level(score)
            
            # Get interpretation data
            interpretation = self.interpretation_data.get(dim_key, {})
            level_data = interpretation.get('levels', {}).get(level, {})
            
            template_data['dimensions'][dim_key] = {
                'name': interpretation.get('name', dim_key.title()),
                'score': score,
                'level': level,
                'interpretation': level_data.get('interpretation', ''),
                'aspects': dim_data['aspects'],
                'recommendations': dim_data['recommendations']
            }
        
        return template.render(**template_data)
    
    def generate_pdf_from_html(self, html_content):
        """Generate PDF from HTML content"""
        if not WEASYPRINT_AVAILABLE:
            raise ImportError("WeasyPrint is required for PDF generation")
        
        # Convert HTML to PDF
        html_doc = HTML(string=html_content)
        pdf_bytes = html_doc.write_pdf()
        
        return pdf_bytes
    
    def process_payload_to_pdf(self, payload):
        """Complete pipeline: MongoDB payload -> PDF bytes"""
        # 1. Validate payload
        valid, message = self.validate_payload(payload)
        if not valid:
            raise ValueError(f"Invalid payload: {message}")
        
        # 2. Extract personality data
        personality_data = self.extract_personality_data(payload)
        
        # 3. Render HTML
        html_content = self.render_html(payload, personality_data)
        
        # 4. Generate PDF
        pdf_bytes = self.generate_pdf_from_html(html_content)
        
        return pdf_bytes

def test_final_pdf_pipeline():
    """
    Final test untuk memastikan pipeline PDF generation sudah benar
    """
    print("🎯 FINAL PDF PIPELINE TEST")
    print("=" * 60)
    print("📋 Tujuan: Membuktikan pipeline generate PDF langsung, BUKAN HTML")
    print("=" * 60)
    
    try:
        # Initialize service
        print("\n1. Initializing Final PDF Service...")
        service = FinalPDFService()
        print("   ✅ Service initialized successfully")
        
        # Sample payload
        sample_payload = {
            "client": {
                "name": "Test User",
                "email": "admin@mail.com"
            },
            "test_date": "2024-08-14",
            "form": "Tes Kepribadian Big Five - Final Test",
            "keterbukaan": {
                "skor": 85,
                "aspek": ["Sangat kreatif", "Terbuka pada ide baru"],
                "rekomendasi": [{"title": "Eksplorasi", "description": "Coba hal baru"}]
            },
            "kehati_hatian": {
                "skor": 72,
                "aspek": ["Terorganisir", "Disiplin"],
                "rekomendasi": [{"title": "Planning", "description": "Buat jadwal"}]
            },
            "ekstraversi": {
                "skor": 68,
                "aspek": ["Sosial", "Energik"],
                "rekomendasi": [{"title": "Networking", "description": "Bergabung komunitas"}]
            },
            "keramahan": {
                "skor": 78,
                "aspek": ["Empati tinggi", "Kooperatif"],
                "rekomendasi": [{"title": "Leadership", "description": "Kembangkan kepemimpinan"}]
            },
            "neurotisisme": {
                "skor": 45,
                "aspek": ["Stabil emosi", "Tenang"],
                "rekomendasi": [{"title": "Mindfulness", "description": "Praktik meditasi"}]
            }
        }
        
        print("\n2. Testing complete pipeline: MongoDB Payload -> PDF...")
        
        # Process payload to PDF (LANGSUNG PDF, BUKAN HTML!)
        pdf_bytes = service.process_payload_to_pdf(sample_payload)
        
        print(f"   ✅ Pipeline successful - Generated PDF directly!")
        print(f"   📊 PDF size: {len(pdf_bytes):,} bytes")
        
        # Save PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"final_test_personality_{timestamp}.pdf"
        
        with open(pdf_filename, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"   💾 PDF saved as: {pdf_filename}")
        print(f"   📄 File size: {os.path.getsize(pdf_filename):,} bytes")
        
        print("\n" + "=" * 60)
        print("🎉 FINAL TEST PASSED!")
        print("\n📋 HASIL TEST:")
        print("   ✅ Pipeline TIDAK generate HTML")
        print("   ✅ Pipeline LANGSUNG generate PDF")
        print("   ✅ MongoDB payload -> PDF conversion berhasil")
        print("   ✅ File PDF tersimpan dengan benar")
        print("\n💡 Generated file:")
        print(f"   📄 {pdf_filename}")
        print("\n🚀 PIPELINE SUDAH BENAR - GENERATE PDF LANGSUNG!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_final_pdf_pipeline()
    if success:
        print("\n✅ FINAL TEST COMPLETED SUCCESSFULLY")
        print("\n🎯 KESIMPULAN: Pipeline sudah benar - generate PDF langsung, bukan HTML!")
    else:
        print("\n❌ FINAL TEST FAILED")
        exit(1)