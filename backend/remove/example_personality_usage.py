#!/usr/bin/env python3
"""
Contoh penggunaan MongoDB Personality Service
Demonstrasi cara menggunakan template hasil tes kepribadian
"""

import json
import sys
import os
from datetime import datetime

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.mongo_personality_service import MongoPersonalityService

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

def demonstrate_service_usage():
    """
    Demonstrate complete personality service usage
    """
    print("🧠 MongoDB Personality Service - Usage Example")
    print("=" * 60)
    
    # Initialize service
    print("\n1. Initializing service...")
    try:
        service = MongoPersonalityService()
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
    
    # Generate HTML
    print("\n6. Generating HTML report...")
    try:
        html_content = service.render_html_template(interpreted_data)
        print("   ✅ HTML generation successful")
        print(f"   📄 HTML length: {len(html_content):,} characters")
        
        # Save HTML for inspection
        html_filename = f"personality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"   💾 HTML saved as: {html_filename}")
        
    except Exception as e:
        print(f"   ❌ HTML generation failed: {e}")
        return
    
    # Generate PDF (optional - requires WeasyPrint)
    print("\n7. Generating PDF report...")
    try:
        pdf_content = service.generate_pdf_report(sample_data)
        print("   ✅ PDF generation successful")
        print(f"   📄 PDF size: {len(pdf_content):,} bytes")
        
        # Save PDF
        pdf_filename = f"personality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        with open(pdf_filename, 'wb') as f:
            f.write(pdf_content)
        print(f"   💾 PDF saved as: {pdf_filename}")
        
    except Exception as e:
        print(f"   ⚠️  PDF generation skipped: {e}")
        print("   💡 Install WeasyPrint for PDF generation: pip install weasyprint")
    
    print("\n" + "=" * 60)
    print("🎉 Demonstration completed successfully!")
    print("\n📋 Generated Files:")
    print(f"   • HTML Report: {html_filename if 'html_filename' in locals() else 'Not generated'}")
    print(f"   • PDF Report: {pdf_filename if 'pdf_filename' in locals() else 'Not generated'}")
    
    return interpreted_data

def show_detailed_analysis(interpreted_data):
    """
    Show detailed personality analysis
    """
    print("\n" + "=" * 60)
    print("🔍 DETAILED PERSONALITY ANALYSIS")
    print("=" * 60)
    
    print(f"\n👤 Client: {interpreted_data['client_name']}")
    print(f"📧 Email: {interpreted_data['client_email']}")
    print(f"📅 Test Date: {interpreted_data['test_date']}")
    print(f"📝 Form: {interpreted_data['form_name']}")
    
    print("\n🧠 PERSONALITY DIMENSIONS:")
    print("-" * 40)
    
    for i, dim in enumerate(interpreted_data['dimensions'], 1):
        print(f"\n{i}. {dim['title']}")
        print(f"   Score: {dim['score']} | Level: {dim['level_label']} | Rank: {dim['rank']}")
        print(f"   Interpretation: {dim['interpretation'][:100]}...")
        
        # Show aspects
        aspects = dim['aspects']
        print(f"   Strengths: {len(aspects.get('kekuatan', []))} items")
        print(f"   Areas for growth: {len(aspects.get('kelemahan', []))} items")
        print(f"   Recommendations: {len(dim['recommendations'])} items")
        
        # Show first recommendation
        if dim['recommendations']:
            first_rec = dim['recommendations'][0]
            print(f"   💡 Key recommendation: {first_rec['title']}")
    
    print("\n" + "=" * 60)

def api_usage_example():
    """
    Show example of API usage
    """
    print("\n" + "=" * 60)
    print("🌐 API USAGE EXAMPLES")
    print("=" * 60)
    
    sample_data = load_sample_data()
    
    print("\n1. Validate Payload:")
    print("POST /api/personality/validate")
    print(json.dumps({"payload": sample_data}, indent=2, ensure_ascii=False)[:200] + "...")
    
    print("\n2. Generate PDF:")
    print("POST /api/personality/generate-pdf")
    print("Content-Type: application/json")
    print("{\"payload\": { /* MongoDB document */ }}")
    
    print("\n3. Preview Data:")
    print("POST /api/personality/preview")
    print("Returns: Extracted and interpreted personality data")
    
    print("\n4. Get Dimensions Info:")
    print("GET /api/personality/dimensions")
    print("Returns: Available personality dimensions and their descriptions")
    
    print("\n💡 Integration Tips:")
    print("   • Always validate payload before processing")
    print("   • Use preview endpoint for debugging")
    print("   • Handle errors gracefully in production")
    print("   • Cache interpretation data for better performance")

if __name__ == "__main__":
    try:
        # Run main demonstration
        interpreted_data = demonstrate_service_usage()
        
        if interpreted_data:
            # Show detailed analysis
            show_detailed_analysis(interpreted_data)
            
            # Show API usage examples
            api_usage_example()
            
            print("\n🚀 Ready for production integration!")
            print("\n📚 For more details, see: PERSONALITY_INTEGRATION_GUIDE.md")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demonstration interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()