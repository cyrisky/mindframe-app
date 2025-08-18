#!/usr/bin/env python3
"""
Test API Ready - MongoDB to PDF
Test endpoint logic tanpa dependency pymongo
"""

import os
import sys
import json
from datetime import datetime

def test_api_ready():
    """
    Test API ready untuk MongoDB to PDF conversion
    """
    print("🧪 Testing API Ready - MongoDB to PDF")
    print("=" * 50)
    
    try:
        # Import weasyprint untuk PDF generation
        try:
            from weasyprint import HTML, CSS
            print("1. WeasyPrint imported successfully")
        except ImportError:
            print("   ❌ WeasyPrint not available")
            return False
        
        print("\n2. Loading interpretation data...")
        # Load interpretation data
        interpretation_path = os.path.join('..', 'ai', 'interpretation-data', 'interpretation.json')
        if not os.path.exists(interpretation_path):
            print(f"   ❌ Interpretation file not found: {interpretation_path}")
            return False
            
        with open(interpretation_path, 'r', encoding='utf-8') as f:
            interpretation_data = json.load(f)
        print("   ✅ Interpretation data loaded")
        
        print("\n3. Loading HTML template...")
        # Load HTML template
        template_path = os.path.join('templates', 'personality_report_template.html')
        if not os.path.exists(template_path):
            print(f"   ❌ Template file not found: {template_path}")
            return False
            
        with open(template_path, 'r', encoding='utf-8') as f:
            html_template = f.read()
        print("   ✅ HTML template loaded")
        
        print("\n4. Processing MongoDB payload...")
        # MongoDB payload (exact format dari user)
        mongo_payload = {
            "_id": {
                "$oid": "688a41c682760799c056b7fa"
            },
            "createdDate": "2025-07-30T16:01:10.316Z",
            "orderNumber": "2025730144807",
            "code": "jmCGjMOStFLa9nPz",
            "status": "ACCESS_GRANTED",
            "name": "Cris",
            "email": "cris@mail.com",
            "phoneNumber": "628112345678",
            "productName": "Tes Minat Bakat - Umum",
            "package": "Standard Bundle",
            "testResult": {
                "kepribadian": {
                    "formId": "3jxWyE",
                    "formName": "Tes Kepribadian",
                    "score": {
                        "open": 29,
                        "conscientious": 36,
                        "extraversion": 29,
                        "agreeable": 37,
                        "neurotic": 34
                    },
                    "rank": {
                        "open": "sedang",
                        "conscientious": "sedang",
                        "extraversion": "sedang",
                        "agreeable": "tinggi",
                        "neurotic": "sedang"
                    }
                }
            }
        }
        
        print(f"   📋 Client: {mongo_payload['name']}")
        print(f"   📧 Email: {mongo_payload['email']}")
        print(f"   📝 Form: {mongo_payload['testResult']['kepribadian']['formName']}")
        
        print("\n5. Converting to service format...")
        # Extract personality data
        personality_data = mongo_payload['testResult']['kepribadian']
        scores = personality_data['score']
        ranks = personality_data['rank']
        
        # Map to standard format
        personality_mapping = {
            'openness': scores['open'],
            'conscientiousness': scores['conscientious'],
            'extraversion': scores['extraversion'],
            'agreeableness': scores['agreeable'],
            'neuroticism': scores['neurotic']
        }
        
        print(f"   📊 Mapped scores: {personality_mapping}")
        
        print("\n6. Determining personality levels...")
        # Determine levels based on scores
        def get_level(score):
            if score <= 20:
                return 'rendah'
            elif score <= 35:
                return 'sedang'
            else:
                return 'tinggi'
        
        levels = {dim: get_level(score) for dim, score in personality_mapping.items()}
        print(f"   📈 Calculated levels: {levels}")
        
        print("\n7. Extracting interpretations...")
        # Extract interpretations
        interpretations = {}
        recommendations = {}
        
        for dimension, level in levels.items():
            if dimension in interpretation_data:
                dim_data = interpretation_data[dimension]
                if level in dim_data:
                    level_data = dim_data[level]
                    interpretations[dimension] = level_data.get('interpretation', f'Interpretasi {dimension} level {level}')
                    recommendations[dimension] = level_data.get('recommendation', f'Rekomendasi {dimension} level {level}')
                else:
                    interpretations[dimension] = f'Interpretasi {dimension} level {level}'
                    recommendations[dimension] = f'Rekomendasi {dimension} level {level}'
            else:
                interpretations[dimension] = f'Interpretasi {dimension} level {level}'
                recommendations[dimension] = f'Rekomendasi {dimension} level {level}'
        
        print("   ✅ Interpretations extracted")
        
        print("\n8. Rendering HTML...")
        # Prepare template data
        template_data = {
            'name': mongo_payload['name'],
            'email': mongo_payload['email'],
            'openness_score': personality_mapping['openness'],
            'conscientiousness_score': personality_mapping['conscientiousness'],
            'extraversion_score': personality_mapping['extraversion'],
            'agreeableness_score': personality_mapping['agreeableness'],
            'neuroticism_score': personality_mapping['neuroticism'],
            'openness_interpretation': interpretations['openness'],
            'conscientiousness_interpretation': interpretations['conscientiousness'],
            'extraversion_interpretation': interpretations['extraversion'],
            'agreeableness_interpretation': interpretations['agreeableness'],
            'neuroticism_interpretation': interpretations['neuroticism'],
            'openness_recommendation': recommendations['openness'],
            'conscientiousness_recommendation': recommendations['conscientiousness'],
            'extraversion_recommendation': recommendations['extraversion'],
            'agreeableness_recommendation': recommendations['agreeableness'],
            'neuroticism_recommendation': recommendations['neuroticism']
        }
        
        # Render HTML
        rendered_html = html_template
        for key, value in template_data.items():
            rendered_html = rendered_html.replace(f'{{{{{key}}}}}', str(value))
        
        print("   ✅ HTML rendered")
        
        print("\n9. Generating PDF...")
        # Generate PDF using WeasyPrint
        html_obj = HTML(string=rendered_html)
        pdf_bytes = html_obj.write_pdf()
        
        print(f"   ✅ PDF generated ({len(pdf_bytes):,} bytes)")
        
        print("\n10. Saving PDF to root folder...")
        # Save to root folder (sesuai request user)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_filename = f"api_ready_test_{timestamp}.pdf"
        
        # Save to root folder (parent directory dari backend)
        root_path = os.path.dirname(os.path.dirname(__file__))
        pdf_path = os.path.join(root_path, pdf_filename)
        
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"   💾 PDF saved to root: {pdf_filename}")
        print(f"   📁 Full path: {pdf_path}")
        
        print("\n" + "=" * 50)
        print("🎉 API Ready Test Completed Successfully!")
        print("\n💡 Test Results:")
        print("   ✅ MongoDB payload processing working")
        print("   ✅ Data conversion and mapping successful")
        print("   ✅ PDF generation pipeline functional")
        print(f"   📄 Test PDF generated: {pdf_filename}")
        print("   💾 PDF saved to root folder as requested")
        
        print("\n🚀 API Endpoint Ready for Testing!")
        print("\n📋 Postman Testing Instructions:")
        print("   1. Method: POST")
        print("   2. URL: http://localhost:5001/api/personality/mongo-to-pdf")
        print("   3. Headers: Content-Type: application/json")
        print("   4. Body: Raw JSON (your exact MongoDB payload)")
        print("   5. Expected: PDF file download + saved to root folder")
        
        print("\n📝 Your MongoDB Payload (ready to copy):")
        print(json.dumps(mongo_payload, indent=2))
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api_ready()
    if success:
        print("\n✅ API Ready Test completed successfully")
        print("\n🎯 Ready for Postman testing with your exact payload!")
    else:
        print("\n❌ API Ready Test failed")
        sys.exit(1)