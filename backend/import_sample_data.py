#!/usr/bin/env python3
"""
Script to import sequential sample data into BugYou database
"""

import psycopg2
from database_config import DATABASE_CONFIG

def import_sequential_data():
    """Import sample data from sequential_sample_data.sql"""
    try:
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        # First, create a default user for the created_by foreign key
        print("👤 Creating default user...")
        cursor.execute("INSERT INTO users (user_id, username) VALUES (1, 'admin') ON CONFLICT (user_id) DO NOTHING")
        conn.commit()
        
        print("📄 Reading sequential sample data file...")
        with open('sequential_sample_data.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print("💾 Importing sequential sample data...")
        cursor.execute(sql_content)
        conn.commit()
        
        print("✅ Sequential sample data imported successfully!")
        
        # Verify the import for each table with challenge IDs
        tables_info = [
            ('python_basic', 'Python Basic'),
            ('javascript_basic', 'JavaScript Basic'), 
            ('java_basic', 'Java Basic'),
            ('cpp_basic', 'C++ Basic')
        ]
        
        print("\n📊 Challenge Distribution:")
        for table, name in tables_info:
            cursor.execute(f"SELECT challenge_id, title FROM {table} ORDER BY challenge_id")
            challenges = cursor.fetchall()
            if challenges:
                ids = [str(c[0]) for c in challenges]
                print(f"   {name}: IDs {', '.join(ids)} ({len(challenges)} challenges)")
                for challenge in challenges:
                    print(f"     - ID {challenge[0]}: {challenge[1]}")
            else:
                print(f"   {name}: No challenges")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error importing sequential sample data: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    import_sequential_data() 