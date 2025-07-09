#!/usr/bin/env python3
"""
Script to clear all data from challenge tables and reset sequences
"""

import psycopg2
from database_config import DATABASE_CONFIG

def clear_and_reset_data():
    """Clear all data from challenge tables and reset sequences"""
    try:
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        # List of all challenge tables
        tables = [
            'python_basic', 'python_intermediate', 'python_advanced',
            'javascript_basic', 'javascript_intermediate', 'javascript_advanced', 
            'java_basic', 'java_intermediate', 'java_advanced',
            'cpp_basic', 'cpp_intermediate', 'cpp_advanced'
        ]
        
        print("🗑️ Clearing all challenge data...")
        for table in tables:
            try:
                # Delete all data from table
                cursor.execute(f"DELETE FROM {table}")
                print(f"   ✅ Cleared {table}")
            except Exception as e:
                print(f"   ⚠️ Error clearing {table}: {e}")
        
        print("🔄 Resetting sequences...")
        for table in tables:
            try:
                # Reset the sequence to start from 1
                cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'challenge_id'), 1, false)")
                print(f"   ✅ Reset sequence for {table}")
            except Exception as e:
                print(f"   ⚠️ Error resetting sequence for {table}: {e}")
        
        # Commit all changes
        conn.commit()
        print("✅ All data cleared and sequences reset!")
        
        # Verify the reset
        print("\n📊 Verification:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count} records")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    clear_and_reset_data() 