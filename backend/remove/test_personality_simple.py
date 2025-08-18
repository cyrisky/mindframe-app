#!/usr/bin/env python3
"""
Simple test script untuk MongoDB Personality Integration
Tanpa dependency pymongo
"""

import json
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import service directly
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

def test_service_basic():
    """
    Test basic service functionality
    """
    print("\n=== Test Service Basic Functionality ===")
    
    try:
        # Load test data
        mongo_data = load_test_data()
        print(f"✅ Test data loaded for: {mongo_data.get('name', 'Unknown')}")
        
        # Initialize service
        service = MongoPersonalityService()
        print("✅ Service initialized")
        
        # Test validation
        validation = service.validate_mongo_payload(mongo_data)
        print(f"Validation result: {validation['validation']['valid']}")
        
        if validation['validation']['valid']:
            print("✅ Payload validation passed")
            
            # Test data extraction
            extracted = service.extract_personality_data(mongo_data)
            print(f"✅ Data extracted for: {extracted['client_name']}")
            print(f"Scores: {list(extracted['scores'].keys())}")
            
            # Test level determination
            for dim, score in extracted['scores'].items():
                level = service.determine_level(score, dim)
                print(f"  {dim}: {score} -> {level}")
            
            # Test mapping
            template_data = service.map_to_interpretation_format(extracted)
            print(f"✅ Template data mapped with {len(template_data['dimensions'])} dimensions")
            
            # Show dimensions
            for dim in template_data['dimensions']:
                print(f"  - {dim['title']}: Score {dim['score']}, Level {dim['level']}")
            
            print(f"Overview: {template_data['overview'][:100]}...")
            
            return True
        else:
            print(f"❌ Validation failed: {validation['validation']['errors']}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_level_logic():
    """
    Test level determination logic
    """
    print("\n=== Test Level Logic ===")
    
    service = MongoPersonalityService()
    
    test_cases = [
        (85, 'tinggi'),
        (70, 'tinggi'),
        (65, 'sedang'),
        (40, 'sedang'),
        (35, 'rendah'),
        (10, 'rendah')
    ]
    
    all_passed = True
    for score, expected in test_cases:
        actual = service.determine_level(score, 'test')
        if actual == expected:
            print(f"✅ Score {score} -> {actual}")
        else:
            print(f"❌ Score {score} -> {actual} (expected {expected})")
            all_passed = False
    
    return all_passed

def test_key_mapping():
    """
    Test key mapping between MongoDB and interpretation
    """
    print("\n=== Test Key Mapping ===")
    
    try:
        # Load test data
        mongo_data = load_test_data()
        service = MongoPersonalityService()
        
        # Get MongoDB keys
        kepribadian_data = mongo_data['testResult']['kepribadian']
        mongo_scores = kepribadian_data.get('score', {})
        
        # Expected dimensions
        expected_dims = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        
        print(f"MongoDB score keys: {list(mongo_scores.keys())}")
        print(f"Expected dimensions: {expected_dims}")
        
        # Check mapping
        all_mapped = True
        for dim in expected_dims:
            if dim in mongo_scores:
                print(f"✅ {dim}: {mongo_scores[dim]}")
            else:
                print(f"❌ {dim}: not found in MongoDB data")
                all_mapped = False
        
        return all_mapped
        
    except Exception as e:
        print(f"❌ Key mapping test failed: {e}")
        return False

def main():
    """
    Main test function
    """
    print("🧪 Simple MongoDB Personality Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Level Logic", test_level_logic),
        ("Key Mapping", test_key_mapping),
        ("Service Basic", test_service_basic)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} Test...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Personality service is ready.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the issues above.")

if __name__ == "__main__":
    main()