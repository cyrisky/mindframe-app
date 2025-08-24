#!/usr/bin/env python3
"""
Simple Server Runner
This script runs the server with proper environment setup
"""

import os
import sys
import subprocess

def main():
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("🚀 Starting Mindframe API Server")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python executable: {sys.executable}")
    
    # Add src to Python path
    src_path = os.path.join(script_dir, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
        print(f"📦 Added to Python path: {src_path}")
    
    # Set environment variable for Google credentials
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        cred_file = os.path.join(script_dir, 'google-service-account-key.json')
        if os.path.exists(cred_file):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = cred_file
            print(f"🔑 Set GOOGLE_APPLICATION_CREDENTIALS: {cred_file}")
    
    # Test imports before starting server
    print("🧪 Testing imports...")
    
    try:
        import google.oauth2.service_account
        import googleapiclient.discovery
        print("✅ Google API imports successful")
    except ImportError as e:
        print(f"❌ Google API import failed: {e}")
        print("💡 Try: pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2")
        return
    
    try:
        from src.services.google_drive_service import GoogleDriveService
        print("✅ GoogleDriveService import successful")
    except ImportError as e:
        print(f"❌ GoogleDriveService import failed: {e}")
        print(f"📁 Current directory: {os.getcwd()}")
        print(f"📁 Src path: {src_path}")
        print(f"📁 Src exists: {os.path.exists(src_path)}")
        if os.path.exists(src_path):
            print(f"📁 Src contents: {os.listdir(src_path)}")
        return
    
    print("✅ All imports successful!")
    print("🔥 Starting server...")
    print("")
    
    # Import and run the server
    try:
        from app import app
        
        # Get port from environment or use default
        port = int(os.getenv('PORT', 5001))
        debug = os.getenv('FLASK_ENV') == 'development'
        
        print(f"🌐 Starting server on http://localhost:{port}")
        print(f"🔧 Debug mode: {debug}")
        print("📡 Server is listening...")
        print("")
        
        # Start the Flask application
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug,
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return

if __name__ == '__main__':
    main()