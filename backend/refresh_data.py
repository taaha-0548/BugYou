"""
Refresh database with comprehensive sample data
"""

import psycopg2
from database_config import DATABASE_CONFIG

def refresh_database():
    """Clear existing data and insert new comprehensive data, resetting IDs to start from 1 in each table."""
    try:
        # Connect to Neon DB
        print("🔌 Connecting to Neon DB...")
        conn = psycopg2.connect(**DATABASE_CONFIG)
        conn.autocommit = True
        
        # Truncate tables and reset identity
        print("🗑️  Truncating tables and resetting identity...")
        with conn.cursor() as cursor:
            tables = [
                'python_basic', 'python_intermediate', 'python_advanced',
                'javascript_basic', 'javascript_intermediate', 'javascript_advanced',
                'java_basic', 'java_intermediate', 'java_advanced',
                'cpp_basic', 'cpp_intermediate', 'cpp_advanced'
            ]
            for table in tables:
                cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
                print(f"   ✅ Truncated {table} and reset identity")
        
        # Insert new comprehensive data
        print("\n📝 Inserting comprehensive sample data...")
        with open('sample_data.sql', 'r') as f:
            sample_data = f.read()
            
        with conn.cursor() as cursor:
            cursor.execute(sample_data)
            
        print("✅ Comprehensive data inserted successfully!")
        
        # Verify the data was inserted
        print("\n📊 Verifying data insertion...")
        total_challenges = 0
        with conn.cursor() as cursor:
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_challenges += count
                print(f"   📈 Records in {table}: {count}")
        
        print(f"\n🎉 Database refresh completed! Total challenges: {total_challenges}")
        
    except Exception as e:
        print(f"❌ Error refreshing database: {str(e)}")
        raise e
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    refresh_database() 