#!/usr/bin/env python3
"""
Contoh penggunaan MongoDB Personality Service (Direct Import)
Demonstrasi cara menggunakan template hasil tes kepribadian tanpa dependency pymongo
"""

import json
import sys
import os
from datetime import datetime

# Direct import to avoid __init__.py pymongo dependency
sys.path.append(os.path.dirname(__file__))

# Import required modules directly
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

class DirectPersonalityService:
    """
    Direct personality service without external dependencies
    """
    
    def __init__(self):
        self.interpretation_data = load_interpretation_data()
        
        # Setup Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
    
    def validate_payload(self, payload):
        """
        Validate MongoDB payload structure
        """
        required_fields = ['clientName', 'clientEmail', 'kepribadian']
        
        for field in required_fields:
            if field not in payload:
                return False, f"Missing required field: {field}"
        
        # Check personality data
        personality = payload['kepribadian']
        required_scores = ['open', 'conscientious', 'extraversion', 'agreeable', 'neurotic']
        
        for score in required_scores:
            if score not in personality:
                return False, f"Missing personality score: {score}"
        
        return True, "Payload is valid"
    
    def extract_personality_data(self, payload):
        """
        Extract personality data from MongoDB payload
        """
        personality = payload['kepribadian']
        
        return {
            'client_name': payload['clientName'],
            'client_email': payload['clientEmail'],
            'phone_number': payload.get('phoneNumber', ''),
            'order_number': payload.get('orderNumber', ''),
            'created_date': payload.get('createdDate', ''),
            'form_name': payload.get('formName', 'Tes Kepribadian'),
            'form_id': payload.get('formId', ''),
            'scores': {
                'open': personality['open'],
                'conscientious': personality['conscientious'],
                'extraversion': personality['extraversion'],
                'agreeable': personality['agreeable'],
                'neurotic': personality['neurotic']
            },
            'ranks': personality.get('rank', {})
        }
    
    def determine_level(self, score, dimension_key):
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
        dimensions = []
        dimension_names = {
            'openness': 'Keterbukaan (Openness)',
            'conscientiousness': 'Kehati-hatian (Conscientiousness)', 
            'extraversion': 'Ekstraversi (Extraversion)',
            'agreeableness': 'Keramahan (Agreeableness)',
            'neuroticism': 'Neurotisisme (Neuroticism)'
        }
        
        # Map MongoDB keys to interpretation keys
        mongo_to_interpretation = {
            'open': 'openness',
            'conscientious': 'conscientiousness',
            'extraversion': 'extraversion',
            'agreeable': 'agreeableness',
            'neurotic': 'neuroticism'
        }
        
        scores = extracted_data['scores']
        ranks = extracted_data.get('ranks', {})
        
        for mongo_key, interpretation_key in mongo_to_interpretation.items():
            if mongo_key in scores:
                score = scores[mongo_key]
                level = self.determine_level(score, interpretation_key)
                rank = ranks.get(mongo_key, '')
                
                # Get interpretation data
                interpretation_info = self.interpretation_data['results']['dimensions'][interpretation_key][level]
                
                dimension_data = {
                    'key': interpretation_key,
                    'title': dimension_names[interpretation_key],
                    'score': score,
                    'rank': rank,
                    'level': level,
                    'level_label': level.title(),
                    'interpretation': interpretation_info['interpretation'],
                    'aspects': interpretation_info['aspekKehidupan'],
                    'recommendations': interpretation_info['rekomendasi']
                }
                
                dimensions.append(dimension_data)
        
        return {
            'client_name': extracted_data['client_name'],
            'client_email': extracted_data['client_email'],
            'phone_number': extracted_data['phone_number'],
            'order_number': extracted_data['order_number'],
            'test_date': self._format_date(extracted_data['created_date']),
            'form_name': extracted_data['form_name'],
            'form_id': extracted_data['form_id'],
            'dimensions': dimensions,
            'overview': self._generate_overview(dimensions),
            'current_year': datetime.now().year
        }
    
    def _format_date(self, date_str):
        """
        Format date string for display
        """
        if not date_str:
            return datetime.now().strftime('%d %B %Y')
        
        try:
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%d %B %Y')
        except:
            return datetime.now().strftime('%d %B %Y')
    
    def _generate_overview(self, dimensions):
        """
        Generate personality overview
        """
        high_dims = [d['title'] for d in dimensions if d['level'] == 'tinggi']
        low_dims = [d['title'] for d in dimensions if d['level'] == 'rendah']
        
        overview = "Berdasarkan hasil tes kepribadian Big Five, "
        
        if high_dims:
            overview += f"Anda menunjukkan tingkat tinggi pada {', '.join(high_dims)}. "
        
        if low_dims:
            overview += f"Sementara pada {', '.join(low_dims)} menunjukkan tingkat yang lebih rendah. "
        
        overview += "Profil kepribadian ini memberikan wawasan tentang cara Anda berinteraksi dengan dunia, mengambil keputusan, dan membangun hubungan dengan orang lain."
        
        return overview
    
    def render_html_template(self, interpreted_data):
        """
        Render HTML template with interpreted data
        """
        template = self.jinja_env.get_template('personality_report_template.html')
        return template.render(**interpreted_data)

def load_sample_data():
    """
    Load sample MongoDB personality data
    """
    return {
        "clientName": "Sarah Johnson",
        "clientEmail": "sarah.johnson@email.com",
        "phoneNumber": "+62812345678",
        "orderNumber": "ORD-PERS-2024-001",
        "createdDate": "2024-01-20T14:30:00Z",
        "formName": "Tes Kepribadian Big Five - Comprehensive",
        "formId": "personality-big5-comprehensive",
        "kepribadian": {
            "open": 45,          # Tinggi - Creative and open to new experiences
            "conscientious": 32, # Sedang - Moderately organized and disciplined
            "extraversion": 28,  # Rendah - More introverted and reserved
            "agreeable": 41,     # Tinggi - Cooperative and trusting
            "neurotic": 35,      # Sedang - Moderate emotional stability
            "rank": {
                "open": "tinggi",
                "conscientious": "sedang",
                "extraversion": "rendah",
                "agreeable": "tinggi",
                "neurotic": "sedang"
            }
        }
    }

def demonstrate_personality_template():
    """
    Demonstrate personality template usage
    """
    print("🧠 Personality Test Results Template - Demo")
    print("=" * 60)
    
    # Initialize service
    print("\n1. Initializing service...")
    try:
        service = DirectPersonalityService()
        print("   ✅ Service initialized successfully")
    except Exception as e:
        print(f"   ❌ Service initialization failed: {e}")
        return
    
    # Load sample data
    print("\n2. Loading sample data...")
    sample_data = load_sample_data()
    print(f"   📋 Client: {sample_data['clientName']}")
    print(f"   📧 Email: {sample_data['clientEmail']}")
    print(f"   📝 Form: {sample_data['formName']}")
    
    # Validate payload
    print("\n3. Validating payload...")
    is_valid, message = service.validate_payload(sample_data)
    if is_valid:
        print("   ✅ Payload validation successful")
    else:
        print(f"   ❌ Payload validation failed: {message}")
        return
    
    # Extract data
    print("\n4. Extracting personality data...")
    try:
        extracted_data = service.extract_personality_data(sample_data)
        print("   ✅ Data extraction successful")
        print(f"   📊 Scores extracted: {list(extracted_data['scores'].keys())}")
    except Exception as e:
        print(f"   ❌ Data extraction failed: {e}")
        return
    
    # Map to interpretation format
    print("\n5. Mapping to interpretation format...")
    try:
        interpreted_data = service.map_to_interpretation_format(extracted_data)
        print("   ✅ Interpretation mapping successful")
        print(f"   🎯 Dimensions processed: {len(interpreted_data['dimensions'])}")
        
        # Show dimension summary
        print("\n   📈 Personality Profile Summary:")
        for dim in interpreted_data['dimensions']:
            print(f"      • {dim['title']}: {dim['score']} ({dim['level_label']})")
            
    except Exception as e:
        print(f"   ❌ Interpretation mapping failed: {e}")
        return
    
    # Generate PDF directly
    print("\n6. Generating PDF report...")
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
        
        # Render HTML template
        html_content = service.render_html_template(interpreted_data)
        
        # Generate PDF
        font_config = FontConfiguration()
        html_doc = HTML(string=html_content)
        
        pdf_filename = f"personality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        html_doc.write_pdf(pdf_filename, font_config=font_config)
        
        print("   ✅ PDF generation successful")
        print(f"   📄 PDF saved as: {pdf_filename}")
        
        # Get file size
        file_size = os.path.getsize(pdf_filename)
        print(f"   📊 PDF size: {file_size:,} bytes")
        
    except ImportError:
        print("   ❌ WeasyPrint not installed. Install with: pip install weasyprint")
        return
    except Exception as e:
        print(f"   ❌ PDF generation failed: {e}")
        return
    
    print("\n" + "=" * 60)
    print("🎉 PDF generation completed successfully!")
    print(f"\n📄 Generated PDF Report: {pdf_filename}")
    print("\n💡 PDF is ready for use and distribution.")
    
    return interpreted_data, pdf_filename

def show_template_features(interpreted_data):
    """
    Show template features and structure
    """
    print("\n" + "=" * 60)
    print("📋 TEMPLATE FEATURES & STRUCTURE")
    print("=" * 60)
    
    print("\n🎨 Template Components:")
    print("   • Header with client information")
    print("   • Professional styling with CSS")
    print("   • Overview section with personality summary")
    print("   • Detailed dimension analysis (Big Five)")
    print("   • Life aspects for each dimension")
    print("   • Personalized recommendations")
    print("   • Footer with generation info")
    
    print("\n📊 Data Structure:")
    print(f"   • Client: {interpreted_data['client_name']}")
    print(f"   • Test Date: {interpreted_data['test_date']}")
    print(f"   • Form: {interpreted_data['form_name']}")
    print(f"   • Dimensions: {len(interpreted_data['dimensions'])}")
    
    print("\n🧠 Personality Dimensions:")
    for i, dim in enumerate(interpreted_data['dimensions'], 1):
        print(f"   {i}. {dim['title']}")
        print(f"      Score: {dim['score']} | Level: {dim['level_label']}")
        print(f"      Aspects: {len(dim['aspects'])} categories")
        print(f"      Recommendations: {len(dim['recommendations'])} items")
    
    print("\n🎯 Template Benefits:")
    print("   ✅ Professional appearance")
    print("   ✅ Comprehensive personality analysis")
    print("   ✅ Actionable recommendations")
    print("   ✅ Easy to customize")
    print("   ✅ PDF-ready format")
    print("   ✅ Mobile-responsive design")

if __name__ == "__main__":
    try:
        # Run demonstration
        result = demonstrate_personality_template()
        
        if result:
            interpreted_data, pdf_filename = result
            
            # Show template features
            show_template_features(interpreted_data)
            
            print("\n" + "=" * 60)
            print("🚀 TEMPLATE READY FOR USE!")
            print("=" * 60)
            print("\n📚 Integration Guide: PERSONALITY_INTEGRATION_GUIDE.md")
            print(f"📄 Sample Report: {pdf_filename}")
            print("\n💡 Next Steps:")
            print("   1. Review the generated PDF report")
            print("   2. Customize the template as needed")
            print("   3. Integrate with your application")
            print("   4. Test with real MongoDB data")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demonstration interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()