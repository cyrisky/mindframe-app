#!/usr/bin/env python3
"""
Test PDF generation for personality service
"""

import os
import sys
import json
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def load_sample_data():
    """
    Load sample MongoDB personality data
    """
    return {
        "clientName": "Sarah Johnson",
        "clientEmail": "sarah.johnson@example.com",
        "testDate": "2024-01-20T10:30:00Z",
        "formName": "Tes Kepribadian Big Five - Comprehensive",
        "kepribadian": {
            "keterbukaan": 45,
            "kehati_hatian": 32,
            "ekstraversi": 28,
            "keramahan": 41,
            "neurotisisme": 35
        },
        "ranking": {
            "keterbukaan": 85,
            "kehati_hatian": 60,
            "ekstraversi": 40,
            "keramahan": 80,
            "neurotisisme": 65
        }
    }

def test_pdf_generation():
    """
    Test PDF generation functionality
    """
    print("🧠 Testing PDF Generation for Personality Service")
    print("=" * 60)
    
    # Test 1: Import service
    print("\n1. Importing MongoPersonalityService...")
    try:
        from services.mongo_personality_service import MongoPersonalityService
        service = MongoPersonalityService()
        print("   ✅ Service imported and initialized successfully")
    except Exception as e:
        print(f"   ❌ Service import failed: {e}")
        return False
    
    # Test 2: Load sample data
    print("\n2. Loading sample data...")
    sample_data = load_sample_data()
    print(f"   📋 Client: {sample_data['clientName']}")
    print(f"   📧 Email: {sample_data['clientEmail']}")
    print(f"   📝 Form: {sample_data['formName']}")
    
    # Test 3: Validate payload
    print("\n3. Validating payload...")
    try:
        validation_result = service.validate_mongo_payload(sample_data)
        if validation_result['validation']['valid']:
            print("   ✅ Payload validation successful")
        else:
            print(f"   ❌ Payload validation failed: {validation_result['validation']['errors']}")
            return False
    except Exception as e:
        print(f"   ❌ Validation error: {e}")
        return False
    
    # Test 4: Generate PDF using new method
    print("\n4. Generating PDF using generate_pdf_report...")
    try:
        pdf_bytes = service.generate_pdf_report(sample_data)
        print("   ✅ PDF generation successful")
        print(f"   📊 PDF size: {len(pdf_bytes):,} bytes")
        
        # Save PDF to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_filename = f"personality_test_{timestamp}.pdf"
        
        with open(pdf_filename, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"   💾 PDF saved as: {pdf_filename}")
        
        # Check file size
        file_size = os.path.getsize(pdf_filename)
        print(f"   📄 File size on disk: {file_size:,} bytes")
        
    except Exception as e:
        print(f"   ❌ PDF generation failed: {e}")
        return False
    
    # Test 5: Generate PDF using process method
    print("\n5. Generating PDF using process_mongo_payload_to_pdf...")
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"personality_process_{timestamp}.pdf"
        
        result = service.process_mongo_payload_to_pdf(
            sample_data,
            output_path,
            save_intermediate_files=True
        )
        
        if result['success']:
            print("   ✅ PDF processing successful")
            print(f"   📄 Output path: {result['output_path']}")
            print(f"   👤 Client: {result['client_name']}")
            print(f"   📅 Test date: {result['test_date']}")
            print(f"   📊 Dimensions: {result['dimensions_processed']}")
            
            # Check file exists and size
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"   📄 File size: {file_size:,} bytes")
            else:
                print("   ❌ PDF file not found")
                return False
                
        else:
            print(f"   ❌ PDF processing failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"   ❌ PDF processing error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All PDF generation tests passed!")
    print("\n💡 Generated files:")
    print(f"   📄 {pdf_filename}")
    print(f"   📄 {output_path}")
    print(f"   📄 {output_path.replace('.pdf', '.html')} (intermediate HTML)")
    print("\n🚀 PDF generation is working correctly!")
    
    return True

if __name__ == '__main__':
    success = test_pdf_generation()
    if success:
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed")
        sys.exit(1)