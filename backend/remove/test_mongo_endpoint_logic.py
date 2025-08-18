#!/usr/bin/env python3
"""
Test MongoDB Endpoint Logic
Test logic endpoint mongo-to-pdf tanpa Flask server
"""

import os
import sys
import json
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_mongo_endpoint_logic():
    """
    Test logic endpoint mongo-to-pdf tanpa Flask
    """
    print("🧪 Testing MongoDB Endpoint Logic")
    print("=" * 50)
    
    try:
        # Import service
        from services.mongo_personality_service import MongoPersonalityService
        
        print("1. Initializing MongoPersonalityService...")
        service = MongoPersonalityService()
        print("   ✅ Service initialized")
        
        # Test payload (format MongoDB asli)
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
        
        print("\n2. Testing payload structure...")
        print(f"   📋 Client: {mongo_payload['name']}")
        print(f"   📧 Email: {mongo_payload['email']}")
        print(f"   📝 Form: {mongo_payload['testResult']['kepribadian']['formName']}")
        print(f"   📊 Scores: {mongo_payload['testResult']['kepribadian']['score']}")
        
        print("\n3. Converting MongoDB format to service format...")
        
        # Extract personality data
        personality_data = mongo_payload['testResult']['kepribadian']
        scores = personality_data['score']
        ranks = personality_data['rank']
        
        # Convert to service format (sama seperti di API endpoint)
        service_payload = {
            'name': mongo_payload['name'],
            'email': mongo_payload['email'],
            'personality': {
                'openness': scores['open'],
                'conscientiousness': scores['conscientious'], 
                'extraversion': scores['extraversion'],
                'agreeableness': scores['agreeable'],
                'neuroticism': scores['neurotic']
            },
            'aspects': {
                'openness': f"Tingkat keterbukaan {ranks['open']}",
                'conscientiousness': f"Tingkat kehati-hatian {ranks['conscientious']}",
                'extraversion': f"Tingkat ekstraversi {ranks['extraversion']}", 
                'agreeableness': f"Tingkat keramahan {ranks['agreeable']}",
                'neuroticism': f"Tingkat neurotisisme {ranks['neurotic']}"
            },
            'recommendations': {
                'openness': f"Rekomendasi untuk keterbukaan level {ranks['open']}",
                'conscientiousness': f"Rekomendasi untuk kehati-hatian level {ranks['conscientious']}",
                'extraversion': f"Rekomendasi untuk ekstraversi level {ranks['extraversion']}",
                'agreeableness': f"Rekomendasi untuk keramahan level {ranks['agreeable']}", 
                'neuroticism': f"Rekomendasi untuk neurotisisme level {ranks['neurotic']}"
            }
        }
        
        print("   ✅ Payload converted to service format")
        print(f"   📊 Service payload keys: {list(service_payload.keys())}")
        
        print("\n4. Validating service payload...")
        is_valid = service.validate_payload(service_payload)
        if is_valid:
            print("   ✅ Payload validation successful")
        else:
            print("   ❌ Payload validation failed")
            return False
        
        print("\n5. Generating PDF from MongoDB payload...")
        pdf_bytes = service.process_mongo_payload_to_pdf(service_payload)
        
        if pdf_bytes:
            print("   ✅ PDF generation successful")
            print(f"   📊 PDF size: {len(pdf_bytes):,} bytes")
            
            # Save PDF to root folder (sesuai request)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"mongo_endpoint_test_{timestamp}.pdf"
            
            # Save to root folder (parent directory)
            root_path = os.path.dirname(os.path.dirname(__file__))
            pdf_path = os.path.join(root_path, pdf_filename)
            
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)
            
            print(f"   💾 PDF saved to root folder: {pdf_filename}")
            print(f"   📁 Full path: {pdf_path}")
            
            if len(pdf_bytes) > 1000:
                print("   ✅ PDF appears to be valid (size > 1KB)")
            else:
                print("   ⚠️  PDF might be too small")
                
        else:
            print("   ❌ PDF generation failed")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 MongoDB Endpoint Logic Test Completed!")
        print("\n💡 Test Results:")
        print("   ✅ MongoDB payload format conversion working")
        print("   ✅ Service payload validation successful")
        print("   ✅ PDF generation from MongoDB data successful")
        print(f"   📄 Generated file in root: {pdf_filename}")
        print("\n🚀 Endpoint logic ready for API integration!")
        print("\n📋 API Endpoint Details:")
        print("   🔗 Endpoint: POST /api/personality/mongo-to-pdf")
        print("   📝 Input: MongoDB format payload (your exact JSON)")
        print("   📄 Output: PDF file download")
        print("   💾 PDF saved to: root folder")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        print("   💡 Make sure all dependencies are installed")
        return False
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_mongo_endpoint_logic()
    if success:
        print("\n✅ Endpoint logic test completed successfully")
        print("\n🎯 Ready for API deployment and Postman testing!")
        print("\n📋 Next Steps:")
        print("   1. Start Flask server: python src/api/personality_api.py")
        print("   2. Test with Postman: POST http://localhost:5001/api/personality/mongo-to-pdf")
        print("   3. Use your exact MongoDB payload as JSON body")
        print("   4. Expect PDF download and file saved to root folder")
    else:
        print("\n❌ Endpoint logic test failed")
        sys.exit(1)