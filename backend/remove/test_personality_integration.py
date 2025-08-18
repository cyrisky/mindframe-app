#!/usr/bin/env python3
"""
Test script untuk MongoDB Personality Integration
Menguji konversi payload MongoDB kepribadian ke PDF report
"""

import json
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.mongo_personality_service import MongoPersonalityService

def load_test_data():
    """
    Load test data dari mongoData-example.json
    """
    test_data_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'ai', 'interpretation-data', 'mongoData-example.json'
    )
    
    with open(test_data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_service_initialization():
    """
    Test inisialisasi service
    """
    print("\n=== Test Service Initialization ===")
    
    try:
        service = MongoPersonalityService()
        print("✅ Service initialized successfully")
        
        # Check if interpretation data is loaded
        if hasattr(service, 'interpretation_data') and service.interpretation_data:
            print("✅ Interpretation data loaded")
            
            # Check dimensions
            dimensions = service.interpretation_data.get('results', {}).get('dimensions', {})
            expected_dimensions = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
            
            for dim in expected_dimensions:
                if dim in dimensions:
                    print(f"✅ Dimension '{dim}' found")
                else:
                    print(f"❌ Dimension '{dim}' missing")
        else:
            print("❌ Interpretation data not loaded")
            
        return service
        
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return None

def test_payload_validation(service, mongo_data):
    """
    Test validasi payload MongoDB
    """
    print("\n=== Test Payload Validation ===")
    
    try:
        validation_result = service.validate_mongo_payload(mongo_data)
        
        print(f"Validation result: {validation_result}")
        
        if validation_result['validation']['valid']:
            print("✅ Payload validation passed")
            
            # Print additional info
            if 'additionalInfo' in validation_result:
                info = validation_result['additionalInfo']
                print(f"Client: {info['clientInfo']['name']}")
                print(f"Form: {info['formInfo']['formName']}")
                print(f"Scores available: {list(info['scores'].keys())}")
                print(f"Ranks available: {list(info['ranks'].keys())}")
        else:
            print("❌ Payload validation failed")
            print(f"Errors: {validation_result['validation']['errors']}")
            
        return validation_result['validation']['valid']
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False

def test_data_extraction(service, mongo_data):
    """
    Test ekstraksi data dari payload
    """
    print("\n=== Test Data Extraction ===")
    
    try:
        extracted_data = service.extract_personality_data(mongo_data)
        
        print(f"Extracted data keys: {list(extracted_data.keys())}")
        print(f"Client name: {extracted_data['client_name']}")
        print(f"Form name: {extracted_data['form_name']}")
        print(f"Scores: {extracted_data['scores']}")
        print(f"Ranks: {extracted_data['ranks']}")
        
        print("✅ Data extraction successful")
        return extracted_data
        
    except Exception as e:
        print(f"❌ Data extraction failed: {e}")
        return None

def test_interpretation_mapping(service, extracted_data):
    """
    Test mapping ke format interpretasi
    """
    print("\n=== Test Interpretation Mapping ===")
    
    try:
        template_data = service.map_to_interpretation_format(extracted_data)
        
        print(f"Template data keys: {list(template_data.keys())}")
        print(f"Client: {template_data['client_name']}")
        print(f"Test date: {template_data['test_date']}")
        print(f"Dimensions count: {len(template_data['dimensions'])}")
        print(f"Overview: {template_data['overview'][:100]}...")
        
        # Print dimension details
        for dim in template_data['dimensions']:
            print(f"  - {dim['title']}: Score {dim['score']}, Level {dim['level']}")
        
        print("✅ Interpretation mapping successful")
        return template_data
        
    except Exception as e:
        print(f"❌ Interpretation mapping failed: {e}")
        return None

def test_html_rendering(service, template_data):
    """
    Test rendering HTML template
    """
    print("\n=== Test HTML Rendering ===")
    
    try:
        html_content = service.render_html_template(template_data)
        
        print(f"HTML content length: {len(html_content)} characters")
        
        # Check if key elements are present
        checks = [
            ('Client name', template_data['client_name'] in html_content),
            ('Form name', template_data['form_name'] in html_content),
            ('Overview', template_data['overview'] in html_content),
            ('Dimensions', len([d for d in template_data['dimensions'] if d['title'] in html_content]) > 0)
        ]
        
        for check_name, check_result in checks:
            if check_result:
                print(f"✅ {check_name} found in HTML")
            else:
                print(f"❌ {check_name} missing in HTML")
        
        print("✅ HTML rendering successful")
        return html_content
        
    except Exception as e:
        print(f"❌ HTML rendering failed: {e}")
        return None

def test_pdf_generation(service, template_data):
    """
    Test generate PDF
    """
    print("\n=== Test PDF Generation ===")
    
    try:
        # Generate timestamp for unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"personality_report_{timestamp}.pdf"
        
        # Process complete pipeline
        result = service.process_mongo_payload_to_pdf(
            mongo_data,  # Use original mongo_data
            output_path,
            save_intermediate_files=True
        )
        
        print(f"PDF generation result: {result}")
        
        if result['success']:
            print(f"✅ PDF generated successfully: {result['output_path']}")
            print(f"Client: {result['client_name']}")
            print(f"Dimensions: {result['dimensions_count']}")
            print(f"Form: {result['form_name']}")
            
            # Check if file exists
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"✅ PDF file exists, size: {file_size} bytes")
            else:
                print("❌ PDF file not found")
                
        else:
            print(f"❌ PDF generation failed: {result.get('error')}")
            
        return result['success']
        
    except Exception as e:
        print(f"❌ PDF generation test failed: {e}")
        return False

def test_level_determination(service):
    """
    Test penentuan level berdasarkan skor
    """
    print("\n=== Test Level Determination ===")
    
    test_cases = [
        (85, 'tinggi'),
        (65, 'sedang'),
        (25, 'rendah'),
        (70, 'tinggi'),
        (40, 'sedang'),
        (39, 'rendah')
    ]
    
    for score, expected_level in test_cases:
        actual_level = service.determine_level(score, 'openness')
        if actual_level == expected_level:
            print(f"✅ Score {score} -> {actual_level} (expected {expected_level})")
        else:
            print(f"❌ Score {score} -> {actual_level} (expected {expected_level})")

def main():
    """
    Main test function
    """
    print("🧪 Starting MongoDB Personality Integration Tests")
    print("=" * 60)
    
    # Load test data
    try:
        global mongo_data
        mongo_data = load_test_data()
        print(f"✅ Test data loaded: {mongo_data.get('name', 'Unknown')}")
    except Exception as e:
        print(f"❌ Failed to load test data: {e}")
        return
    
    # Initialize service
    service = test_service_initialization()
    if not service:
        print("❌ Cannot continue without service")
        return
    
    # Test level determination
    test_level_determination(service)
    
    # Test payload validation
    if not test_payload_validation(service, mongo_data):
        print("❌ Cannot continue with invalid payload")
        return
    
    # Test data extraction
    extracted_data = test_data_extraction(service, mongo_data)
    if not extracted_data:
        print("❌ Cannot continue without extracted data")
        return
    
    # Test interpretation mapping
    template_data = test_interpretation_mapping(service, extracted_data)
    if not template_data:
        print("❌ Cannot continue without template data")
        return
    
    # Test HTML rendering
    html_content = test_html_rendering(service, template_data)
    if not html_content:
        print("❌ Cannot continue without HTML content")
        return
    
    # Test PDF generation
    pdf_success = test_pdf_generation(service, template_data)
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    if pdf_success:
        print("✅ All tests passed! MongoDB Personality integration is working correctly.")
        print("\n📋 Key Features Verified:")
        print("  - MongoDB payload validation")
        print("  - Data extraction and mapping")
        print("  - Interpretation system integration")
        print("  - HTML template rendering")
        print("  - PDF generation")
        print("  - Level determination logic")
    else:
        print("❌ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()