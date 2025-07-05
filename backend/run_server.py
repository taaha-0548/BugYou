#!/usr/bin/env python3
"""
BugYou Server Startup Script
Run this script to start the Flask backend with database integration
"""

import sys
import os

# Check if required packages are installed
try:
    import flask
    import psycopg2
    from flask_cors import CORS
    import requests
except ImportError as e:
    print(f"❌ Missing required package: {e}")
    print("💡 Run: pip install -r requirements.txt")
    sys.exit(1)

# Check if database config exists
if not os.path.exists('database_config.py'):
    print("❌ database_config.py not found!")
    print("💡 Make sure all database files are in the current directory")
    sys.exit(1)

# Test database connection
try:
    from database_config import test_connection
    print("🔌 Testing database connection...")
    if test_connection():
        print("✅ Database connection successful!")
    else:
        print("❌ Database connection failed!")
        print("💡 Make sure PostgreSQL is running and database is set up")
        print("📖 Check DATABASE_SETUP.md for setup instructions")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
except Exception as e:
    print(f"❌ Database test error: {e}")
    print("💡 Check your database configuration")
    sys.exit(1)

# Start the Flask server
if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 Starting BugYou Flask Server")
    print("="*50)
    print("📍 Frontend: http://localhost:5000")
    print("🔗 API Health: http://localhost:5000/api/health")
    print("🗄️  Database: Integrated with PostgreSQL")
    print("⚡ Code Execution: Piston API")
    print("="*50)
    print("💡 Press Ctrl+C to stop the server")
    print()
    
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Thanks for using BugYou!")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1) 