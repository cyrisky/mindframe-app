#!/usr/bin/env python3
"""
Test script untuk memverifikasi bahwa template variables sudah ter-replace dengan benar
setelah implementasi Jinja2 yang proper
"""

import requests
import json
from datetime import datetime

def test_template_variables():
    """
    Test apakah template variables seperti client_name, client_email, 
    dan dimension.recommendations sudah ter-replace dengan benar
    """
    
    print("🧪 Testing Template Variable Replacement")
    print("=" * 50)
    
    # Sample MongoDB payload
    test_payload = {
        "_id": {"$oid": "688a41c682760799c056b7fa"},
        "name": "Cris Bawana",
        "email": "cris.bawana@example.com",
        "testResult": {
            "kepribadian": {
                "formName": "Tes Kepribadian Big Five",
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
    
    print(f"📋 Testing with client: {test_payload['name']}")
    print(f"📧 Email: {test_payload['email']}")
    
    try:
        # Send request to API
        print("\n📡 Sending request to API...")
        response = requests.post(
            'http://localhost:5001/api/personality/mongo-to-pdf',
            json=test_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API request successful!")
            
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            print(f"📄 Content-Type: {content_type}")
            
            if 'application/pdf' in content_type:
                print("✅ Response is PDF format")
                
                # Save PDF for manual inspection
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_filename = f"template_test_{timestamp}.pdf"
                
                with open(pdf_filename, 'wb') as f:
                    f.write(response.content)
                
                print(f"💾 PDF saved as: {pdf_filename}")
                print(f"📏 PDF size: {len(response.content):,} bytes")
                
                print("\n🔍 Manual Verification Required:")
                print("   Please open the generated PDF and check:")
                print(f"   ✓ Client name should show: '{test_payload['name']}'")
                print(f"   ✓ Client email should show: '{test_payload['email']}'")
                print("   ✓ Dimensions should have proper recommendations")
                print("   ✓ No template variables like {{ client_name }} should remain")
                print("   ✓ Jinja2 loops and conditions should be processed")
                
                return True
            else:
                print(f"❌ Unexpected content type: {content_type}")
                return False
        else:
            print(f"❌ API request failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Error response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        print("   Make sure the server is running on http://localhost:5001")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Template Variable Replacement Test")
    print("This test verifies that Jinja2 template rendering works correctly")
    print("and that variables like {{ client_name }} are properly replaced.\n")
    
    success = test_template_variables()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("Please manually verify the generated PDF to confirm")
        print("that all template variables have been replaced correctly.")
    else:
        print("\n💥 Test failed!")
        print("Check the error messages above for details.")