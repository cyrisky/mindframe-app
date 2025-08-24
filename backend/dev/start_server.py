#!/usr/bin/env python3
"""
Server Starter Script
This script ensures the server runs with the correct Python environment
and all dependencies are properly loaded.
"""

import os
import sys
import subprocess
from pathlib import Path

def print_status(message):
    print(f"✅ {message}")

def print_warning(message):
    print(f"⚠️  {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def check_environment():
    """Check if we're in the right environment"""
    print("🚀 Starting Mindframe API Server")
    print("=" * 40)
    print()
    
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        print_error("Please run this script from the backend directory")
        sys.exit(1)
    
    print_info(f"Current directory: {os.getcwd()}")
    print_info(f"Python executable: {sys.executable}")
    print_info(f"Python version: {sys.version.split()[0]}")
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_status(f"Running in virtual environment: {sys.prefix}")
    else:
        print_warning("Running in system Python (not in virtual environment)")
        print_info("Consider using a virtual environment for better isolation")

def test_imports():
    """Test required imports"""
    print_info("Testing Google API imports...")
    
    try:
        import google.oauth2.service_account
        import googleapiclient.discovery
        import googleapiclient.http
        import googleapiclient.errors
        print_status("Google API imports successful")
    except ImportError as e:
        print_error(f"Google API import error: {e}")
        print_info("Please install requirements: pip install -r requirements.txt")
        return False
    
    print_info("Testing GoogleDriveService import...")
    
    # Add src to path if not already there
    src_path = os.path.join(os.path.dirname(__file__), 'src')
    if src_path not in sys.path:
        sys.path.append(src_path)
    
    try:
        from src.services.google_drive_service import GoogleDriveService
        print_status("GoogleDriveService import successful")
    except ImportError as e:
        print_error(f"GoogleDriveService import error: {e}")
        return False
    
    return True

def check_files():
    """Check for required files"""
    # Check for credentials file
    if os.path.exists('google-service-account-key.json'):
        print_status("Google service account key file found")
    else:
        print_warning("Google service account key file not found")
        print_info("Google Drive features will be disabled")
    
    # Check .env file
    if os.path.exists('.env'):
        print_status(".env file found")
    else:
        print_warning(".env file not found")
        if os.path.exists('.env.example'):
            print_info("You can copy .env.example to .env: cp .env.example .env")

def start_server():
    """Start the server"""
    print()
    print_info("Starting server...")
    print_info("Server will be available at: http://localhost:5001")
    print_info("Press Ctrl+C to stop the server")
    print()
    print_status("🔥 Server starting...")
    print()
    
    # Import and run the server
    try:
        # Import the server module
        import app
        
        # The server should start automatically when imported
        # If it doesn't, we can call app.run() here
        
    except KeyboardInterrupt:
        print("\n")
        print_info("Server stopped by user")
    except Exception as e:
        print_error(f"Server error: {e}")
        sys.exit(1)

def main():
    """Main function"""
    try:
        # Check environment
        check_environment()
        
        # Test imports
        if not test_imports():
            print_error("Import tests failed. Please fix the issues above.")
            sys.exit(1)
        
        # Check files
        check_files()
        
        # Start server
        start_server()
        
    except KeyboardInterrupt:
        print("\n")
        print_info("Startup interrupted by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"Startup error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()