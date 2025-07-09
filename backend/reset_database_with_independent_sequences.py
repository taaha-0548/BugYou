#!/usr/bin/env python3
"""
Reset Database with Independent Sequences
This script resets the database with the new schema that has independent sequences per table.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(__file__))

from database_config import DatabaseManager, DATABASE_CONFIG, test_connection
import psycopg2

def get_direct_connection():
    """Get a direct database connection for DDL operations"""
    return psycopg2.connect(**DATABASE_CONFIG)

def reset_database():
    """Reset database with new independent sequence schema"""
    print("🔄 Resetting database with independent sequences...")
    print("⚠️  This will DELETE ALL existing data!")
    
    # Confirm with user
    confirm = input("\nDo you want to continue? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("Operation cancelled.")
        return False
    
    try:
        # Use direct connection for DDL operations
        conn = get_direct_connection()
        cursor = conn.cursor()
        
        # Step 1: Execute new schema
        print("\n🏗️  Step 1: Creating new database schema...")
        schema_file = os.path.join(os.path.dirname(__file__), 'database_setup.sql')
        
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        cursor.execute(schema_sql)
        print("   ✅ Schema created successfully")
        
        # Step 2: Load sample data
        print("\n📝 Step 2: Loading sample data...")
        sample_data_file = os.path.join(os.path.dirname(__file__), 'sample_data.sql')
        
        with open(sample_data_file, 'r') as f:
            sample_data_sql = f.read()
        
        cursor.execute(sample_data_sql)
        print("   ✅ Sample data loaded successfully")
        
        # Step 3: Verify sequences
        print("\n🔍 Step 3: Verifying sequences...")
        
        tables = [
            'python_basic', 'python_intermediate', 'python_advanced',
            'javascript_basic', 'javascript_intermediate', 'javascript_advanced',
            'java_basic', 'java_intermediate', 'java_advanced',
            'cpp_basic', 'cpp_intermediate', 'cpp_advanced'
        ]
        
        for table in tables:
            cursor.execute(f"""
                SELECT COUNT(*) FROM {table}
            """)
            count = cursor.fetchone()[0]
            
            if count > 0:
                cursor.execute(f"""
                    SELECT MIN(challenge_id), MAX(challenge_id) FROM {table}
                """)
                min_id, max_id = cursor.fetchone()
                
                # Check if IDs are sequential
                cursor.execute(f"""
                    SELECT challenge_id FROM {table} ORDER BY challenge_id
                """)
                ids = [row[0] for row in cursor.fetchall()]
                expected_ids = list(range(1, len(ids) + 1))
                is_sequential = ids == expected_ids
                
                status = "✅" if is_sequential else "❌"
                print(f"   {status} {table}: {count} records, IDs {min_id}-{max_id}")
            else:
                print(f"   📭 {table}: empty")
        
        # Commit all changes
        conn.commit()
        
        print("\n🎉 Database reset completed successfully!")
        print("\n📊 Summary:")
        print("   - Database schema updated with independent sequences")
        print("   - Each table now has its own sequential IDs starting from 1")
        print("   - Sample data loaded successfully")
        print("   - All sequences properly configured")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.rollback()
        return False
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        print("Please make sure database_setup.sql and sample_data.sql exist in the backend directory")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """Main function"""
    print("🐛 BugYou Database Reset Tool")
    print("=" * 50)
    print("This tool will reset your database with the new independent sequence schema.")
    print("\nFeatures:")
    print("✅ Each table gets its own sequential IDs starting from 1")
    print("✅ No more shared sequences across tables")
    print("✅ Clean, organized ID structure")
    print("✅ Sample data included")
    
    # Test database connection
    try:
        if test_connection():
            print("\n✅ Database connection successful")
        else:
            raise Exception("Connection test failed")
    except Exception as e:
        print(f"\n❌ Database connection failed: {e}")
        print("Please check your database configuration")
        return
    
    # Perform reset
    if reset_database():
        print("\n🎉 Your database is now ready with independent sequences!")
        print("You can start the server and begin using the platform.")
    else:
        print("\n❌ Database reset failed. Please check the error messages above.")

if __name__ == '__main__':
    main() 