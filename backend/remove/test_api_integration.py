#!/usr/bin/env python3
"""
Test script untuk API Personal Values integration
"""

import requests
import json
import os
from datetime import datetime

def test_api_endpoints():
    """
    Test semua API endpoints Personal Values
    """
    
    # Base URL API
    base_url = "http://localhost:5000/api/personal-values"
    
    # Load MongoDB example data
    mongo_data_path = "/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/ai/interpretation-data/mongoData-example.json"
    
    print("Loading MongoDB example data...")
    with open(mongo_data_path, 'r', encoding='utf-8') as file:
        mongo_data = json.load(file)
    
    print(f"✓ MongoDB data loaded: {mongo_data.get('name', 'Unknown')}")
    
    # Test 1: Health Check
    print("\n=== Test 1: Health Check ===")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✓ Service Status: {health_data['status']}")
            print(f"✓ Checks: {health_data['checks']}")
        else:
            print(f"✗ Health check failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API server. Make sure the server is running.")
        print("To start the server, run: python src/api/personal_values_api.py")
        return False
    
    # Test 2: Validate Payload
    print("\n=== Test 2: Validate Payload ===")
    try:
        payload = {"mongoData": mongo_data}
        response = requests.post(f"{base_url}/validate", json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            validation_data = response.json()
            validation = validation_data["validation"]
            additional_info = validation_data["additionalInfo"]
            
            print(f"✓ Validation Valid: {validation['valid']}")
            print(f"✓ Errors: {validation['errors']}")
            print(f"✓ Warnings: {validation['warnings']}")
            
            if additional_info:
                print(f"✓ Client: {additional_info['clientInfo']['name']}")
                print(f"✓ Form: {additional_info['formInfo']['formName']}")
                print(f"✓ Top Values: {additional_info['topValues']}")
        else:
            print(f"✗ Validation failed: {response.text}")
            
    except Exception as e:
        print(f"✗ Validation test error: {e}")
    
    # Test 3: Preview Data
    print("\n=== Test 3: Preview Data ===")
    try:
        payload = {"mongoData": mongo_data}
        response = requests.post(f"{base_url}/preview", json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            preview_data = response.json()
            template_data = preview_data["templateData"]
            
            print(f"✓ Top N: {template_data['top_n']}")
            print(f"✓ Client Name: {template_data['client_info']['name']}")
            print(f"✓ Top Values Count: {len(template_data['top_values'])}")
            
            for i, value in enumerate(template_data['top_values'], 1):
                print(f"  {i}. {value['title']} (Score: {value['score']})")
                
        else:
            print(f"✗ Preview failed: {response.text}")
            
    except Exception as e:
        print(f"✗ Preview test error: {e}")
    
    # Test 4: Generate PDF
    print("\n=== Test 4: Generate PDF ===")
    try:
        payload = {
            "mongoData": mongo_data,
            "options": {
                "saveIntermediateFiles": True,
                "customOutputName": "api_test_report.pdf"
            }
        }
        
        response = requests.post(f"{base_url}/generate-pdf", json=payload)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Save PDF file
            output_path = "api_generated_report.pdf"
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(output_path)
            print(f"✓ PDF generated successfully: {output_path}")
            print(f"✓ File size: {file_size} bytes")
            
            # Check if file is valid PDF
            with open(output_path, 'rb') as f:
                header = f.read(4)
                if header == b'%PDF':
                    print("✓ Valid PDF file format")
                else:
                    print("✗ Invalid PDF file format")
                    
        else:
            print(f"✗ PDF generation failed: {response.text}")
            
    except Exception as e:
        print(f"✗ PDF generation test error: {e}")
    
    # Test 5: Error Handling - Invalid Payload
    print("\n=== Test 5: Error Handling ===")
    try:
        # Test dengan payload kosong
        response = requests.post(f"{base_url}/validate", json={})
        print(f"Empty payload - Status Code: {response.status_code}")
        
        if response.status_code == 400:
            error_data = response.json()
            print(f"✓ Expected error: {error_data['error']}")
        
        # Test dengan payload invalid
        invalid_payload = {"mongoData": {"invalid": "data"}}
        response = requests.post(f"{base_url}/validate", json=invalid_payload)
        print(f"Invalid payload - Status Code: {response.status_code}")
        
        if response.status_code == 400:
            error_data = response.json()
            print(f"✓ Expected validation error: {error_data['code']}")
            
    except Exception as e:
        print(f"✗ Error handling test error: {e}")
    
    print("\n=== API Integration Test Complete ===")
    return True

def test_direct_service():
    """
    Test service secara langsung tanpa API
    """
    print("\n=== Direct Service Test ===")
    
    try:
        # Import service
        import sys
        sys.path.append('/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/backend')
        
        from src.services.mongo_personal_values_service import MongoPersonalValuesService
        
        # Initialize service
        service = MongoPersonalValuesService(
            template_dir="/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/backend/templates"
        )
        
        # Load MongoDB data
        mongo_data_path = "/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/ai/interpretation-data/mongoData-example.json"
        
        with open(mongo_data_path, 'r', encoding='utf-8') as file:
            mongo_data = json.load(file)
        
        # Test validation
        validation = service.validate_mongo_payload(mongo_data)
        print(f"✓ Direct validation: {validation['valid']}")
        
        if validation["valid"]:
            # Test PDF generation
            result = service.process_mongo_payload_to_pdf(
                mongo_data,
                "direct_service_test.pdf",
                save_intermediate_files=True
            )
            
            print(f"✓ Direct PDF generation: {result['success']}")
            if result["success"]:
                print(f"✓ Client: {result['client_name']}")
                print(f"✓ Top values: {result['top_values']}")
            
        return True
        
    except Exception as e:
        print(f"✗ Direct service test error: {e}")
        return False

def main():
    """
    Main test function
    """
    print("Personal Values API Integration Test")
    print("====================================")
    
    # Test direct service first
    direct_success = test_direct_service()
    
    if direct_success:
        print("\n" + "="*50)
        print("Starting API tests...")
        print("Note: Make sure API server is running on localhost:5000")
        print("To start: python src/api/personal_values_api.py")
        print("="*50)
        
        # Test API endpoints
        api_success = test_api_endpoints()
        
        if api_success:
            print("\n✓ All tests completed successfully!")
        else:
            print("\n✗ Some API tests failed")
    else:
        print("\n✗ Direct service test failed")

if __name__ == '__main__':
    main()