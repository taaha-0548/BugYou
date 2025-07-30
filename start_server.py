#!/usr/bin/env python3
"""
BugYou Server Startup Script
Run this from the project root to start the BugYou platform
"""

import os
import sys
import subprocess

def start_bugyou():
    """Start the BugYou platform"""
    
    print("🚀 Starting BugYou Debugging Platform...")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    
    if not os.path.exists(backend_dir):
        print("❌ Error: Backend directory not found!")
        print("Make sure you're running this from the project root.")
        return False
    
    # Check if requirements are installed
    try:
        import flask
        import psycopg2
        import requests
        print("✅ Dependencies found")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r backend/requirements.txt")
        return False
    
    # Change to backend directory and run the server
    os.chdir(backend_dir)
    
    print(f"📁 Changed to backend directory: {backend_dir}")
    print("🔌 Starting Flask server...")
    print("📍 Frontend will be available at: http://localhost:5000")
    print("🔗 API Health check: http://localhost:5000/api/health")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Run the Flask app
        subprocess.run([sys.executable, 'app.py'], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server error: {e}")
        return False
    except FileNotFoundError:
        print("❌ Error: app.py not found in backend directory!")
        return False
    
    return True

if __name__ == "__main__":
    start_bugyou() 