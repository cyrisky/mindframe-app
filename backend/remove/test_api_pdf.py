#!/usr/bin/env python3
"""
Test API PDF Generation - Direct Test
Testing personality PDF generation without running Flask server
"""

import os
import sys
import json
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_api_pdf_generation():
    """
    Test PDF generation functionality that would be used by API
    """
    print("🧠 Testing API PDF Generation Pipeline")
    print("=" * 50)
    
    try:
        # Import the service
        from services.mongo_personality_service import MongoPersonalityService
        
        print("1. Initializing MongoPersonalityService...")
        service = MongoPersonalityService()
        print("   ✅ Service initialized successfully")
        
        # Sample MongoDB payload (same as what API would receive)
        sample_payload = {
            "client": {
                "name": "Sarah Johnson",
                "email": "sarah.johnson@example.com"
            },
            "test_date": "2024-08-14",
            "form": "Tes Kepribadian Big Five - Comprehensive",
            "keterbukaan": {
                "skor": 85,
                "aspek": [
                    "Sangat terbuka terhadap pengalaman baru",
                    "Memiliki imajinasi yang kuat",
                    "Menyukai tantangan intelektual"
                ],
                "rekomendasi": [
                    {"title": "Eksplorasi Kreatif", "description": "Coba hobi baru seperti melukis atau menulis"},
                    {"title": "Pembelajaran Berkelanjutan", "description": "Ikuti kursus online atau workshop"}
                ]
            },
            "kehati_hatian": {
                "skor": 72,
                "aspek": [
                    "Cukup terorganisir dalam kehidupan sehari-hari",
                    "Mampu menyelesaikan tugas dengan baik",
                    "Kadang perlu reminder untuk deadline"
                ],
                "rekomendasi": [
                    {"title": "Manajemen Waktu", "description": "Gunakan aplikasi calendar dan to-do list"},
                    {"title": "Rutinitas Harian", "description": "Buat jadwal harian yang konsisten"}
                ]
            },
            "ekstraversi": {
                "skor": 68,
                "aspek": [
                    "Cukup nyaman dalam situasi sosial",
                    "Menikmati interaksi dengan orang lain",
                    "Kadang butuh waktu sendiri untuk recharge"
                ],
                "rekomendasi": [
                    {"title": "Networking", "description": "Ikuti acara networking atau komunitas"},
                    {"title": "Public Speaking", "description": "Latih kemampuan berbicara di depan umum"}
                ]
            },
            "keramahan": {
                "skor": 78,
                "aspek": [
                    "Mudah berempati dengan orang lain",
                    "Suka membantu dan bekerja sama",
                    "Kadang terlalu mengalah"
                ],
                "rekomendasi": [
                    {"title": "Assertiveness Training", "description": "Belajar menyampaikan pendapat dengan tegas"},
                    {"title": "Boundary Setting", "description": "Tetapkan batasan yang sehat dalam hubungan"}
                ]
            },
            "neurotisisme": {
                "skor": 45,
                "aspek": [
                    "Cukup stabil secara emosional",
                    "Mampu mengelola stress dengan baik",
                    "Kadang khawatir berlebihan"
                ],
                "rekomendasi": [
                    {"title": "Mindfulness", "description": "Praktik meditasi dan mindfulness"},
                    {"title": "Stress Management", "description": "Pelajari teknik relaksasi dan breathing"}
                ]
            }
        }
        
        print("\n2. Testing payload validation...")
        validation_result = service.validate_mongo_payload(sample_payload)
        if validation_result['validation']['valid']:
            print("   ✅ Payload validation successful")
        else:
            print(f"   ❌ Payload validation failed: {validation_result['validation']['errors']}")
            return False
        
        print("\n3. Testing PDF generation (API method)...")
        # This is the method that API endpoint calls
        pdf_bytes = service.process_mongo_payload_to_pdf(sample_payload)
        
        if pdf_bytes:
            print(f"   ✅ PDF generation successful")
            print(f"   📊 PDF size: {len(pdf_bytes):,} bytes")
            
            # Save PDF file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"api_test_personality_{timestamp}.pdf"
            
            with open(pdf_filename, 'wb') as f:
                f.write(pdf_bytes)
            
            print(f"   💾 PDF saved as: {pdf_filename}")
            print(f"   📄 File size: {os.path.getsize(pdf_filename):,} bytes")
            
        else:
            print("   ❌ PDF generation failed - no bytes returned")
            return False
        
        print("\n" + "=" * 50)
        print("🎉 API PDF Generation Test Passed!")
        print("\n💡 Generated file:")
        print(f"   📄 {pdf_filename}")
        print("\n🚀 API endpoint ready for PDF generation!")
        print("\n✅ Pipeline benar - API langsung generate PDF!")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        print("   💡 This might be due to missing pymongo dependency")
        return False
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_api_pdf_generation()
    if success:
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed")
        sys.exit(1)