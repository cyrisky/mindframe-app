#!/usr/bin/env python3
"""
Test PDF generation directly without pymongo dependencies
"""

import os
import sys
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

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

def load_sample_data():
    """
    Load sample MongoDB personality data
    """
    return {
        "clientName": "Sarah Johnson",
        "clientEmail": "sarah.johnson@example.com",
        "testDate": "2024-01-20T10:30:00Z",
        "formName": "Tes Kepribadian Big Five - Comprehensive",
        "kepribadian": {
            "keterbukaan": 45,
            "kehati_hatian": 32,
            "ekstraversi": 28,
            "keramahan": 41,
            "neurotisisme": 35
        },
        "ranking": {
            "keterbukaan": 85,
            "kehati_hatian": 60,
            "ekstraversi": 40,
            "keramahan": 80,
            "neurotisisme": 65
        }
    }

class DirectPDFService:
    """
    Direct PDF service without external dependencies
    """
    
    def __init__(self):
        self.interpretation_data = load_interpretation_data()
        
        # Setup Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
    
    def validate_payload(self, payload):
        """
        Validate MongoDB payload
        """
        required_fields = ['clientName', 'clientEmail', 'kepribadian']
        
        for field in required_fields:
            if field not in payload:
                return False, f"Missing required field: {field}"
        
        # Check personality dimensions
        kepribadian = payload.get('kepribadian', {})
        required_dimensions = ['keterbukaan', 'kehati_hatian', 'ekstraversi', 'keramahan', 'neurotisisme']
        
        for dim in required_dimensions:
            if dim not in kepribadian:
                return False, f"Missing personality dimension: {dim}"
            
            score = kepribadian[dim]
            if not isinstance(score, (int, float)) or score < 0 or score > 100:
                return False, f"Invalid score for {dim}: {score}"
        
        return True, "Valid payload"
    
    def extract_personality_data(self, payload):
        """
        Extract personality data from MongoDB payload
        """
        return {
            'client': {
                'name': payload.get('clientName', 'Unknown'),
                'email': payload.get('clientEmail', 'unknown@example.com')
            },
            'test_date': payload.get('testDate', datetime.now().isoformat()),
            'form_name': payload.get('formName', 'Tes Kepribadian'),
            'scores': payload.get('kepribadian', {}),
            'rankings': payload.get('ranking', {})
        }
    
    def determine_level(self, score):
        """
        Determine personality level based on score
        """
        if score >= 40:
            return 'tinggi'
        elif score >= 30:
            return 'sedang'
        else:
            return 'rendah'
    
    def map_to_interpretation_format(self, extracted_data):
        """
        Map extracted data to interpretation format
        """
        # MongoDB to interpretation key mapping
        mongo_to_interpretation = {
            'keterbukaan': 'openness',
            'kehati_hatian': 'conscientiousness', 
            'ekstraversi': 'extraversion',
            'keramahan': 'agreeableness',
            'neurotisisme': 'neuroticism'
        }
        
        mapped_data = {
            'client': extracted_data['client'],
            'test_date': extracted_data['test_date'],
            'form_name': extracted_data['form_name'],
            'dimensions': {}
        }
        
        # Process each personality dimension
        for mongo_key, interp_key in mongo_to_interpretation.items():
            if mongo_key in extracted_data['scores']:
                score = extracted_data['scores'][mongo_key]
                level = self.determine_level(score)
                ranking = extracted_data['rankings'].get(mongo_key, 0)
                
                # Get interpretation data
                dimension_data = self.interpretation_data['results']['dimensions'].get(interp_key, {})
                level_data = dimension_data.get(level, {})
                
                mapped_data['dimensions'][interp_key] = {
                    'score': score,
                    'level': level,
                    'ranking': ranking,
                    'interpretation': level_data.get('interpretation', ''),
                    'aspects': level_data.get('aspekKehidupan', {}),
                    'recommendations': level_data.get('rekomendasi', [])
                }
        
        return mapped_data
    
    def render_html_template(self, data):
        """
        Render HTML template with data
        """
        template = self.jinja_env.get_template('personality_report_template.html')
        return template.render(data=data)
    
    def generate_pdf_bytes(self, html_content):
        """
        Generate PDF bytes from HTML content
        """
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
            
            font_config = FontConfiguration()
            html_doc = HTML(string=html_content)
            pdf_bytes = html_doc.write_pdf(font_config=font_config)
            
            return pdf_bytes
            
        except ImportError:
            raise Exception("WeasyPrint not installed. Install with: pip install weasyprint")
    
    def generate_pdf_file(self, html_content, output_path):
        """
        Generate PDF file from HTML content
        """
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
            
            font_config = FontConfiguration()
            html_doc = HTML(string=html_content)
            html_doc.write_pdf(output_path, font_config=font_config)
            
            return True
            
        except ImportError:
            raise Exception("WeasyPrint not installed. Install with: pip install weasyprint")
        except Exception as e:
            raise Exception(f"PDF generation failed: {str(e)}")

def test_pdf_generation():
    """
    Test PDF generation functionality
    """
    print("🧠 Testing Direct PDF Generation for Personality Service")
    print("=" * 60)
    
    # Test 1: Initialize service
    print("\n1. Initializing DirectPDFService...")
    try:
        service = DirectPDFService()
        print("   ✅ Service initialized successfully")
    except Exception as e:
        print(f"   ❌ Service initialization failed: {e}")
        return False
    
    # Test 2: Load sample data
    print("\n2. Loading sample data...")
    sample_data = load_sample_data()
    print(f"   📋 Client: {sample_data['clientName']}")
    print(f"   📧 Email: {sample_data['clientEmail']}")
    print(f"   📝 Form: {sample_data['formName']}")
    
    # Test 3: Validate payload
    print("\n3. Validating payload...")
    try:
        is_valid, message = service.validate_payload(sample_data)
        if is_valid:
            print("   ✅ Payload validation successful")
        else:
            print(f"   ❌ Payload validation failed: {message}")
            return False
    except Exception as e:
        print(f"   ❌ Validation error: {e}")
        return False
    
    # Test 4: Extract data
    print("\n4. Extracting personality data...")
    try:
        extracted_data = service.extract_personality_data(sample_data)
        print("   ✅ Data extraction successful")
        print(f"   📊 Scores extracted: {list(extracted_data['scores'].keys())}")
    except Exception as e:
        print(f"   ❌ Data extraction failed: {e}")
        return False
    
    # Test 5: Map to interpretation format
    print("\n5. Mapping to interpretation format...")
    try:
        interpreted_data = service.map_to_interpretation_format(extracted_data)
        print("   ✅ Interpretation mapping successful")
        print(f"   📊 Dimensions mapped: {list(interpreted_data['dimensions'].keys())}")
    except Exception as e:
        print(f"   ❌ Interpretation mapping failed: {e}")
        return False
    
    # Test 6: Render HTML
    print("\n6. Rendering HTML template...")
    try:
        html_content = service.render_html_template(interpreted_data)
        print("   ✅ HTML rendering successful")
        print(f"   📄 HTML length: {len(html_content):,} characters")
    except Exception as e:
        print(f"   ❌ HTML rendering failed: {e}")
        return False
    
    # Test 7: Generate PDF bytes
    print("\n7. Generating PDF bytes...")
    try:
        pdf_bytes = service.generate_pdf_bytes(html_content)
        print("   ✅ PDF bytes generation successful")
        print(f"   📊 PDF size: {len(pdf_bytes):,} bytes")
        
        # Save PDF bytes to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f"personality_bytes_{timestamp}.pdf"
        
        with open(pdf_filename, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"   💾 PDF saved as: {pdf_filename}")
        
    except Exception as e:
        print(f"   ❌ PDF bytes generation failed: {e}")
        return False
    
    # Test 8: Generate PDF file directly
    print("\n8. Generating PDF file directly...")
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename_direct = f"personality_direct_{timestamp}.pdf"
        
        success = service.generate_pdf_file(html_content, pdf_filename_direct)
        
        if success:
            print("   ✅ Direct PDF file generation successful")
            print(f"   💾 PDF saved as: {pdf_filename_direct}")
            
            # Check file size
            if os.path.exists(pdf_filename_direct):
                file_size = os.path.getsize(pdf_filename_direct)
                print(f"   📄 File size: {file_size:,} bytes")
            else:
                print("   ❌ PDF file not found")
                return False
        else:
            print("   ❌ Direct PDF file generation failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Direct PDF file generation error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All PDF generation tests passed!")
    print("\n💡 Generated files:")
    print(f"   📄 {pdf_filename} (from bytes)")
    print(f"   📄 {pdf_filename_direct} (direct generation)")
    print("\n🚀 PDF generation is working correctly!")
    print("\n✅ Pipeline sudah benar - langsung generate PDF, bukan HTML!")
    
    return True

if __name__ == '__main__':
    success = test_pdf_generation()
    if success:
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed")
        sys.exit(1)