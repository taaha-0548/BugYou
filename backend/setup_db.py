#!/usr/bin/env python3
"""
Setup script to create BugYou database schema
"""

import psycopg2
from database_config import DATABASE_CONFIG

def setup_database():
    """Execute the database_setup.sql file in the postgres database"""
    try:
        # Connect to database
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        print("🔌 Connected to PostgreSQL database")
        
        # Read and execute SQL file
        print("📜 Reading database_setup.sql...")
        with open('database_setup.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print("🚀 Executing SQL setup...")
        cursor.execute(sql_content)
        conn.commit()
        
        print("✅ Database schema created successfully!")
        print("📊 Tables and sample data have been set up")
        
        cursor.close()
        conn.close()
        
        return True
        
    except FileNotFoundError:
        print("❌ database_setup.sql file not found!")
        return False
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🏗️  Setting up BugYou database schema...")
    print("=" * 50)
    
    success = setup_database()
    
    if success:
        print("\n🎉 Setup complete!")
        print("💡 You can now run: python run_server.py")
    else:
        print("\n💥 Setup failed!")
        print("💡 Check the error messages above") 