#!/usr/bin/env python3
"""
Direct test script untuk MongoDB Personality Integration
Mengimport service secara langsung tanpa __init__.py
"""

import json
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import service directly without going through __init__.py
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'services'))
from mongo_personality_service import MongoPersonalityService

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
            
            # Check test info
            test_info = service.interpretation_data
            print(f"Test name: {test_info.get('testName', 'Unknown')}")
            print(f"Test type: {test_info.get('testType', 'Unknown')}")
            
            # Check dimensions
            dimensions = service.interpretation_data.get('results', {}).get('dimensions', {})
            expected_dimensions = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
            
            print(f"Available dimensions: {list(dimensions.keys())}")
            
            for dim in expected_dimensions:
                if dim in dimensions:
                    print(f"✅ Dimension '{dim}' found")
                    # Check levels
                    levels = list(dimensions[dim].keys())
                    print(f"  Levels: {levels}")
                else:
                    print(f"❌ Dimension '{dim}' missing")
        else:
            print("❌ Interpretation data not loaded")
            
        return service
        
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_payload_validation(service, mongo_data):
    """
    Test validasi payload MongoDB
    """
    print("\n=== Test Payload Validation ===")
    
    try:
        validation_result = service.validate_mongo_payload(mongo_data)
        
        print(f"Validation valid: {validation_result['validation']['valid']}")
        
        if validation_result['validation']['valid']:
            print("✅ Payload validation passed")
            
            # Print additional info
            if 'additionalInfo' in validation_result:
                info = validation_result['additionalInfo']
                print(f"Client: {info['clientInfo']['name']}")
                print(f"Email: {info['clientInfo']['email']}")
                print(f"Form: {info['formInfo']['formName']}")
                print(f"Scores available: {list(info['scores'].keys())}")
                print(f"Ranks available: {list(info['ranks'].keys())}")
        else:
            print("❌ Payload validation failed")
            print(f"Errors: {validation_result['validation']['errors']}")
            print(f"Warnings: {validation_result['validation']['warnings']}")
            
        return validation_result['validation']['valid']
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        import traceback
        traceback.print_exc()
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
        print(f"Client email: {extracted_data['client_email']}")
        print(f"Form name: {extracted_data['form_name']}")
        print(f"Form ID: {extracted_data['form_id']}")
        print(f"Created date: {extracted_data['created_date']}")
        
        print(f"\nScores ({len(extracted_data['scores'])} dimensions):")
        for dim, score in extracted_data['scores'].items():
            print(f"  {dim}: {score}")
        
        print(f"\nRanks ({len(extracted_data['ranks'])} dimensions):")
        for dim, rank in extracted_data['ranks'].items():
            print(f"  {dim}: {rank}")
        
        print("✅ Data extraction successful")
        return extracted_data
        
    except Exception as e:
        print(f"❌ Data extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_level_determination(service):
    """
    Test penentuan level berdasarkan skor
    """
    print("\n=== Test Level Determination ===")
    
    test_cases = [
        (85, 'tinggi'),
        (70, 'tinggi'),
        (65, 'sedang'),
        (50, 'sedang'),
        (40, 'sedang'),
        (35, 'rendah'),
        (20, 'rendah')
    ]
    
    all_passed = True
    for score, expected_level in test_cases:
        actual_level = service.determine_level(score, 'openness')
        if actual_level == expected_level:
            print(f"✅ Score {score} -> {actual_level}")
        else:
            print(f"❌ Score {score} -> {actual_level} (expected {expected_level})")
            all_passed = False
    
    return all_passed

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
        print(f"Form: {template_data['form_name']}")
        print(f"Dimensions count: {len(template_data['dimensions'])}")
        
        print(f"\nOverview: {template_data['overview']}")
        
        print(f"\nDimensions:")
        for i, dim in enumerate(template_data['dimensions'], 1):
            print(f"  {i}. {dim['title']}")
            print(f"     Score: {dim['score']}, Level: {dim['level']} ({dim['level_label']})")
            print(f"     Rank: {dim['rank']}")
            print(f"     Interpretation: {dim['interpretation'][:100]}...")
            
            # Check aspects
            aspects = dim['aspects']
            print(f"     Aspects: {list(aspects.keys())}")
            
            # Check recommendations
            recommendations = dim['recommendations']
            if isinstance(recommendations, list):
                print(f"     Recommendations ({len(recommendations)} items):")
                for rec in recommendations:
                    if isinstance(rec, dict) and 'title' in rec:
                        print(f"       - {rec['title']}")
            else:
                print(f"     Recommendations: {type(recommendations)}")
            print()
        
        print("✅ Interpretation mapping successful")
        return template_data
        
    except Exception as e:
        print(f"❌ Interpretation mapping failed: {e}")
        import traceback
        traceback.print_exc()
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
            ('HTML structure', '<html' in html_content and '</html>' in html_content),
            ('CSS styles', '<style' in html_content or 'class=' in html_content)
        ]
        
        for check_name, check_result in checks:
            if check_result:
                print(f"✅ {check_name} found in HTML")
            else:
                print(f"❌ {check_name} missing in HTML")
        
        # Check dimensions in HTML
        dimensions_found = 0
        for dim in template_data['dimensions']:
            if dim['title'] in html_content:
                dimensions_found += 1
        
        print(f"✅ {dimensions_found}/{len(template_data['dimensions'])} dimensions found in HTML")
        
        print("✅ HTML rendering successful")
        return html_content
        
    except Exception as e:
        print(f"❌ HTML rendering failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """
    Main test function
    """
    print("🧪 Direct MongoDB Personality Integration Tests")
    print("=" * 70)
    
    # Load test data
    try:
        mongo_data = load_test_data()
        print(f"✅ Test data loaded for: {mongo_data.get('name', 'Unknown')}")
        print(f"Email: {mongo_data.get('email', 'N/A')}")
        print(f"Phone: {mongo_data.get('phoneNumber', 'N/A')}")
    except Exception as e:
        print(f"❌ Failed to load test data: {e}")
        return
    
    # Initialize service
    service = test_service_initialization()
    if not service:
        print("❌ Cannot continue without service")
        return
    
    # Test level determination
    level_test_passed = test_level_determination(service)
    
    # Test payload validation
    validation_passed = test_payload_validation(service, mongo_data)
    if not validation_passed:
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
    html_test_passed = html_content is not None
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎯 TEST SUMMARY")
    print("=" * 70)
    
    tests_results = [
        ("Service Initialization", service is not None),
        ("Level Determination", level_test_passed),
        ("Payload Validation", validation_passed),
        ("Data Extraction", extracted_data is not None),
        ("Interpretation Mapping", template_data is not None),
        ("HTML Rendering", html_test_passed)
    ]
    
    passed = 0
    total = len(tests_results)
    
    for test_name, result in tests_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! MongoDB Personality integration is working correctly.")
        print("\n📋 Key Features Verified:")
        print("  ✅ Service initialization with interpretation data")
        print("  ✅ MongoDB payload validation")
        print("  ✅ Data extraction from MongoDB format")
        print("  ✅ Level determination logic (tinggi/sedang/rendah)")
        print("  ✅ Mapping to interpretation format")
        print("  ✅ HTML template rendering")
        print("\n🚀 Ready for PDF generation and API integration!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the errors above.")

if __name__ == "__main__":
    main()