"""
Insert sample data into the database
"""

import psycopg2
from database_config import DATABASE_CONFIG

def insert_sample_data():
    """Insert sample data into the database"""
    try:
        # Read the sample data SQL file
        with open('sample_data.sql', 'r') as f:
            sample_data = f.read()
            
        # Connect to Neon DB
        print("🔌 Connecting to Neon DB...")
        conn = psycopg2.connect(**DATABASE_CONFIG)
        conn.autocommit = True
        
        # Insert sample data
        print("📝 Inserting sample data...")
        with conn.cursor() as cursor:
            cursor.execute(sample_data)
            
        print("✅ Sample data inserted successfully!")
        
        # Verify the data was inserted
        print("\n📊 Verifying data insertion...")
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM python_basic")
            count = cursor.fetchone()[0]
            print(f"📈 Records in python_basic: {count}")
            
            cursor.execute("SELECT COUNT(*) FROM javascript_basic")
            count = cursor.fetchone()[0]
            print(f"📈 Records in javascript_basic: {count}")
            
            cursor.execute("SELECT COUNT(*) FROM java_basic")
            count = cursor.fetchone()[0]
            print(f"📈 Records in java_basic: {count}")
            
            cursor.execute("SELECT COUNT(*) FROM cpp_basic")
            count = cursor.fetchone()[0]
            print(f"📈 Records in cpp_basic: {count}")
        
    except Exception as e:
        print(f"❌ Error inserting sample data: {str(e)}")
        raise e
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    insert_sample_data() 