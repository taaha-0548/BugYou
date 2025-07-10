"""
BugYou Database Setup Script
This script initializes the database schema in Neon DB
"""

import os
import psycopg2
from database_config import DATABASE_CONFIG

def setup_database():
    """Set up the database schema"""
    try:
        # Read the SQL setup script
        with open('database_setup.sql', 'r') as f:
            setup_script = f.read()
            
        # Connect to Neon DB
        print("🔌 Connecting to Neon DB...")
        conn = psycopg2.connect(**DATABASE_CONFIG)
        conn.autocommit = True
        
        # Create tables
        print("📦 Creating database tables...")
        with conn.cursor() as cursor:
            cursor.execute(setup_script)
            
        print("✅ Database setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error setting up database: {str(e)}")
        raise e
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    setup_database() 