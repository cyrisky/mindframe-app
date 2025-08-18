#!/usr/bin/env python3
"""
Simple test untuk Personal Values service integration tanpa dependencies eksternal
"""

import json
import os
import sys
from datetime import datetime

# Add backend to path
sys.path.append('/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/backend')

def test_service_integration():
    """
    Test service integration dengan MongoDB payload
    """
    print("Personal Values Service Integration Test")
    print("=======================================")
    
    try:
        # Import service
        from src.services.mongo_personal_values_service import MongoPersonalValuesService
        
        print("✓ Service imported successfully")
        
        # Initialize service
        service = MongoPersonalValuesService(
            template_dir="/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/backend/templates"
        )
        
        print("✓ Service initialized successfully")
        
        # Load MongoDB example data
        mongo_data_path = "/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/ai/interpretation-data/mongoData-example.json"
        
        with open(mongo_data_path, 'r', encoding='utf-8') as file:
            mongo_data = json.load(file)
        
        print(f"✓ MongoDB data loaded: {mongo_data.get('name', 'Unknown')}")
        
        # Test 1: Validation
        print("\n=== Test 1: Payload Validation ===")
        validation = service.validate_mongo_payload(mongo_data)
        print(f"Valid: {validation['valid']}")
        print(f"Errors: {validation['errors']}")
        print(f"Warnings: {validation['warnings']}")
        
        if not validation['valid']:
            print("✗ Validation failed, stopping tests")
            return False
        
        print("✓ Validation passed")
        
        # Test 2: Data Extraction
        print("\n=== Test 2: Data Extraction ===")
        extracted_data = service.extract_personal_values_from_mongo(mongo_data)
        
        print(f"Form ID: {extracted_data['formId']}")
        print(f"Form Name: {extracted_data['formName']}")
        print(f"Client Name: {extracted_data['clientInfo']['name']}")
        print(f"Scores count: {len(extracted_data['scores'])}")
        
        # Show top 3 scores
        top_values = service.get_top_n_values(extracted_data['scores'], 3)
        print("Top 3 values:")
        for i, (key, score) in enumerate(top_values, 1):
            print(f"  {i}. {key}: {score}")
        
        print("✓ Data extraction successful")
        
        # Test 3: Mapping to Interpretation
        print("\n=== Test 3: Mapping to Interpretation ===")
        mapped_data = service.map_to_interpretation_format(extracted_data)
        
        dimensions = mapped_data['results']['dimensions']
        print(f"Mapped dimensions count: {len(dimensions)}")
        
        for key, dimension in dimensions.items():
            print(f"  {dimension['rank']}. {dimension['title']} (Score: {dimension['score']})")
        
        print("✓ Mapping to interpretation successful")
        
        # Test 4: Template Data Generation
        print("\n=== Test 4: Template Data Generation ===")
        template_data = service.generate_template_data(mapped_data)
        
        print(f"Top N: {template_data['top_n']}")
        print(f"Client Name: {template_data['client_info']['name']}")
        print(f"Test Date: {template_data['client_info']['test_date']}")
        print(f"Top Values count: {len(template_data['top_values'])}")
        
        print("✓ Template data generation successful")
        
        # Test 5: HTML Rendering
        print("\n=== Test 5: HTML Rendering ===")
        try:
            html_content = service.render_html_template(template_data)
            html_length = len(html_content)
            print(f"HTML content length: {html_length} characters")
            
            # Check if HTML contains expected content
            if template_data['client_info']['name'] in html_content:
                print("✓ Client name found in HTML")
            else:
                print("✗ Client name not found in HTML")
            
            # Check for top values
            found_values = 0
            for value in template_data['top_values']:
                if value['title'] in html_content:
                    found_values += 1
            
            print(f"✓ Found {found_values}/{len(template_data['top_values'])} values in HTML")
            
            print("✓ HTML rendering successful")
            
        except Exception as e:
            print(f"✗ HTML rendering failed: {e}")
            return False
        
        # Test 6: PDF Generation
        print("\n=== Test 6: PDF Generation ===")
        try:
            pdf_output = "integration_test_report.pdf"
            success = service.generate_pdf(html_content, pdf_output)
            
            if success and os.path.exists(pdf_output):
                file_size = os.path.getsize(pdf_output)
                print(f"✓ PDF generated: {pdf_output} ({file_size} bytes)")
                
                # Verify PDF header
                with open(pdf_output, 'rb') as f:
                    header = f.read(4)
                    if header == b'%PDF':
                        print("✓ Valid PDF format")
                    else:
                        print("✗ Invalid PDF format")
                        
            else:
                print("✗ PDF generation failed")
                return False
                
        except Exception as e:
            print(f"✗ PDF generation failed: {e}")
            return False
        
        # Test 7: Full Pipeline
        print("\n=== Test 7: Full Pipeline ===")
        try:
            pipeline_output = "pipeline_test_report.pdf"
            result = service.process_mongo_payload_to_pdf(
                mongo_data,
                pipeline_output,
                save_intermediate_files=True
            )
            
            if result['success']:
                print(f"✓ Full pipeline successful")
                print(f"✓ Client: {result['client_name']}")
                print(f"✓ Output: {result['output_path']}")
                print(f"✓ Form: {result['form_info']['formName']}")
                
                # Show top values
                print("✓ Top Values:")
                for value in result['top_values']:
                    print(f"  {value['rank']}. {value['title']} (Score: {value['score']})")
                    
            else:
                print(f"✗ Full pipeline failed: {result['error']}")
                return False
                
        except Exception as e:
            print(f"✗ Full pipeline failed: {e}")
            return False
        
        print("\n=== All Tests Passed! ===")
        print("\nGenerated files:")
        print(f"- {pdf_output}")
        print(f"- {pipeline_output}")
        print(f"- pipeline_test_report_mapped_data.json")
        print(f"- pipeline_test_report_template_data.json")
        print(f"- pipeline_test_report.html")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("Make sure all required modules are installed")
        return False
        
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_key_mapping():
    """
    Test key mapping dari MongoDB ke interpretasi
    """
    print("\n=== Key Mapping Test ===")
    
    try:
        from src.services.mongo_personal_values_service import MongoPersonalValuesService
        
        service = MongoPersonalValuesService()
        
        # Load data
        mongo_data_path = "/Users/crisbawana/Documents/2_Areas/Satu Persen/Code/mindframe-app/ai/interpretation-data/mongoData-example.json"
        
        with open(mongo_data_path, 'r', encoding='utf-8') as file:
            mongo_data = json.load(file)
        
        # Extract scores
        extracted_data = service.extract_personal_values_from_mongo(mongo_data)
        scores = extracted_data['scores']
        
        print(f"MongoDB keys found: {list(scores.keys())}")
        
        # Check mapping
        interpretation_dimensions = service.interpretation_data['results']['dimensions']
        print(f"Interpretation keys available: {list(interpretation_dimensions.keys())}")
        
        print("\nKey mapping check:")
        for mongo_key in scores.keys():
            interpretation_key = service.key_mapping.get(mongo_key)
            if interpretation_key:
                if interpretation_key in interpretation_dimensions:
                    print(f"✓ {mongo_key} → {interpretation_key} (Found)")
                else:
                    print(f"✗ {mongo_key} → {interpretation_key} (Not found in interpretation)")
            else:
                print(f"✗ {mongo_key} → No mapping")
        
        return True
        
    except Exception as e:
        print(f"✗ Key mapping test failed: {e}")
        return False

def main():
    """
    Main test function
    """
    # Test key mapping first
    mapping_success = test_key_mapping()
    
    if mapping_success:
        # Test full integration
        integration_success = test_service_integration()
        
        if integration_success:
            print("\n🎉 All integration tests passed!")
            print("\nNext steps:")
            print("1. Start API server: python src/api/personal_values_api.py")
            print("2. Test API endpoints with the generated test script")
            print("3. Integrate with your main application")
        else:
            print("\n❌ Integration tests failed")
    else:
        print("\n❌ Key mapping test failed")

if __name__ == '__main__':
    main()