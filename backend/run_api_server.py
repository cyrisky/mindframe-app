#!/usr/bin/env python3
"""
Run API Server for MongoDB to PDF Testing
Simple Flask server runner untuk testing dengan Postman
"""

import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def run_api_server():
    """
    Run Flask API server untuk testing
    """
    print("🚀 Starting API Server for MongoDB to PDF Testing")
    print("=" * 60)
    
    try:
        # Try to import Flask
        try:
            import flask
            print("✅ Flask is available")
        except ImportError:
            print("❌ Flask not installed. Installing Flask...")
            os.system("pip install flask")
            print("✅ Flask installed")
        
        # Import the API app
        from api.personality_api import app
        
        print("\n📋 API Server Information:")
        print(f"   🌐 Host: localhost")
        print(f"   🔌 Port: 5001")
        print(f"   📡 Endpoint: POST /api/personality/mongo-to-pdf")
        print(f"   📄 Content-Type: application/json")
        
        print("\n📝 MongoDB Payload (ready for Postman):")
        payload = {
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
        
        import json
        print(json.dumps(payload, indent=2))
        
        print("\n🎯 Postman Testing Steps:")
        print("   1. Open Postman")
        print("   2. Create new POST request")
        print("   3. URL: http://localhost:5001/api/personality/mongo-to-pdf")
        print("   4. Headers: Content-Type = application/json")
        print("   5. Body: Raw JSON (copy payload above)")
        print("   6. Send request")
        print("   7. Expected: PDF file download + saved to root folder")
        
        print("\n🔥 Starting Flask server...")
        print("   Press Ctrl+C to stop the server")
        print("=" * 60)
        
        # Start the Flask app
        app.run(host='localhost', port=5001, debug=True)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 Alternative: Manual Flask Server")
        print("   Run: python src/api/personality_api.py")
        return False
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    run_api_server()