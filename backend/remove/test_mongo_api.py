#!/usr/bin/env python3
"""
Test MongoDB API Endpoint
Test endpoint /api/personality/mongo-to-pdf dengan payload MongoDB format asli
"""

import os
import sys
import json
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_mongo_api_endpoint():
    """
    Test endpoint mongo-to-pdf dengan payload format MongoDB
    """
    print("🧪 Testing MongoDB API Endpoint")
    print("=" * 50)
    
    try:
        # Import the API app
        from api.personality_api import app
        
        print("1. Initializing Flask test client...")
        app.config['TESTING'] = True
        client = app.test_client()
        print("   ✅ Test client initialized")
        
        # Test payload (format MongoDB asli)
        test_payload = {
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
        print(f"   📋 Client: {test_payload['name']}")
        print(f"   📧 Email: {test_payload['email']}")
        print(f"   📝 Form: {test_payload['testResult']['kepribadian']['formName']}")
        print(f"   📊 Scores: {test_payload['testResult']['kepribadian']['score']}")
        
        print("\n3. Sending POST request to /api/personality/mongo-to-pdf...")
        response = client.post(
            '/api/personality/mongo-to-pdf',
            json=test_payload,
            content_type='application/json'
        )
        
        print(f"   📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ API request successful!")
            
            # Check if response is PDF
            content_type = response.headers.get('Content-Type', '')
            print(f"   📄 Content-Type: {content_type}")
            
            if 'application/pdf' in content_type:
                print("   ✅ Response is PDF format")
                
                # Save PDF to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_filename = f"mongo_api_test_{timestamp}.pdf"
                
                with open(pdf_filename, 'wb') as f:
                    f.write(response.data)
                
                file_size = len(response.data)
                print(f"   💾 PDF saved as: {pdf_filename}")
                print(f"   📊 File size: {file_size:,} bytes")
                
                if file_size > 1000:  # Basic check for valid PDF
                    print("   ✅ PDF appears to be valid (size > 1KB)")
                else:
                    print("   ⚠️  PDF might be too small")
                    
            else:
                print(f"   ❌ Unexpected content type: {content_type}")
                print(f"   📄 Response data: {response.data[:200]}...")
                
        else:
            print(f"   ❌ API request failed with status {response.status_code}")
            try:
                error_data = response.get_json()
                print(f"   📄 Error response: {error_data}")
            except:
                print(f"   📄 Raw response: {response.data[:200]}...")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 MongoDB API Test Completed!")
        print("\n💡 Test Results:")
        print("   ✅ Endpoint /api/personality/mongo-to-pdf working")
        print("   ✅ MongoDB payload format accepted")
        print("   ✅ PDF generation successful")
        print(f"   📄 Generated file: {pdf_filename}")
        print("\n🚀 API ready for Postman testing!")
        print("\n📋 Postman Instructions:")
        print("   1. Method: POST")
        print("   2. URL: http://localhost:5001/api/personality/mongo-to-pdf")
        print("   3. Headers: Content-Type: application/json")
        print("   4. Body: Raw JSON (use the payload from your request)")
        print("   5. Expected: PDF file download")
        
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
    success = test_mongo_api_endpoint()
    if success:
        print("\n✅ Test completed successfully")
        print("\n🎯 Ready for Postman testing!")
    else:
        print("\n❌ Test failed")
        sys.exit(1)