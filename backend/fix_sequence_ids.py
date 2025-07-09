#!/usr/bin/env python3
"""
Fix Sequential IDs Script
This script fixes the challenge ID sequences to ensure each table has independent IDs starting from 1.
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

def fix_sequence_ids():
    """Fix sequence IDs for all challenge tables"""
    print("🔧 Starting sequence ID fix...")
    
    # List of all challenge tables
    tables = [
        'python_basic', 'python_intermediate', 'python_advanced',
        'javascript_basic', 'javascript_intermediate', 'javascript_advanced',
        'java_basic', 'java_intermediate', 'java_advanced',
        'cpp_basic', 'cpp_intermediate', 'cpp_advanced'
    ]
    
    try:
        conn = get_direct_connection()
        cursor = conn.cursor()
        
        print("📊 Analyzing current sequence states...")
        
        for table in tables:
            print(f"\n🔍 Processing table: {table}")
            
            # Check if table exists and has data
            cursor.execute(f"""
                SELECT COUNT(*) FROM {table}
            """)
            count = cursor.fetchone()[0]
            print(f"   - Current records: {count}")
            
            if count == 0:
                print(f"   - Table is empty, skipping sequence reset")
                continue
            
            # Get current sequence name
            cursor.execute(f"""
                SELECT pg_get_serial_sequence('{table}', 'challenge_id')
            """)
            sequence_name = cursor.fetchone()[0]
            
            if sequence_name:
                print(f"   - Sequence name: {sequence_name}")
                
                # Get current max ID in table
                cursor.execute(f"""
                    SELECT COALESCE(MAX(challenge_id), 0) FROM {table}
                """)
                max_id = cursor.fetchone()[0]
                print(f"   - Current max ID: {max_id}")
                
                # Check if IDs are sequential starting from 1
                cursor.execute(f"""
                    SELECT challenge_id FROM {table} ORDER BY challenge_id
                """)
                ids = [row[0] for row in cursor.fetchall()]
                expected_ids = list(range(1, len(ids) + 1))
                
                if ids == expected_ids:
                    print(f"   ✅ IDs are already sequential (1 to {len(ids)})")
                    # Just reset the sequence to continue from the next number
                    cursor.execute(f"""
                        SELECT setval('{sequence_name}', {max_id}, true)
                    """)
                else:
                    print(f"   ⚠️ IDs are not sequential: {ids}")
                    print(f"   🔄 Reassigning IDs to be sequential starting from 1...")
                    
                    # Create a mapping of old IDs to new IDs
                    old_to_new = {}
                    for i, old_id in enumerate(sorted(ids)):
                        old_to_new[old_id] = i + 1
                    
                    # Update IDs to be sequential
                    # First, temporarily set all IDs to negative values to avoid conflicts
                    for old_id, new_id in old_to_new.items():
                        if old_id != new_id:
                            cursor.execute(f"""
                                UPDATE {table} SET challenge_id = -{new_id} WHERE challenge_id = {old_id}
                            """)
                    
                    # Then update to positive sequential values
                    cursor.execute(f"""
                        UPDATE {table} SET challenge_id = -challenge_id WHERE challenge_id < 0
                    """)
                    
                    # Reset the sequence
                    cursor.execute(f"""
                        SELECT setval('{sequence_name}', {len(ids)}, true)
                    """)
                    
                    print(f"   ✅ Successfully reassigned IDs to 1-{len(ids)}")
            else:
                print(f"   ❌ No sequence found for table {table}")
        
        # Commit all changes
        conn.commit()
        print("\n🎉 Successfully fixed all sequence IDs!")
        print("📋 Summary:")
        print("   - Each table now has independent sequential IDs starting from 1")
        print("   - Sequences are properly reset to continue from the next available ID")
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.rollback()
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
    
    return True

def verify_sequences():
    """Verify that sequences are working correctly"""
    print("\n🔍 Verifying sequence states...")
    
    tables = [
        'python_basic', 'python_intermediate', 'python_advanced',
        'javascript_basic', 'javascript_intermediate', 'javascript_advanced',
        'java_basic', 'java_intermediate', 'java_advanced',
        'cpp_basic', 'cpp_intermediate', 'cpp_advanced'
    ]
    
    try:
        conn = get_direct_connection()
        cursor = conn.cursor()
        
        all_good = True
        
        for table in tables:
            cursor.execute(f"""
                SELECT COUNT(*) FROM {table}
            """)
            count = cursor.fetchone()[0]
            
            if count > 0:
                # Check if IDs are sequential starting from 1
                cursor.execute(f"""
                    SELECT challenge_id FROM {table} ORDER BY challenge_id
                """)
                ids = [row[0] for row in cursor.fetchall()]
                expected_ids = list(range(1, len(ids) + 1))
                
                if ids == expected_ids:
                    print(f"   ✅ {table}: IDs 1-{len(ids)} (sequential)")
                else:
                    print(f"   ❌ {table}: IDs {ids} (not sequential)")
                    all_good = False
            else:
                print(f"   📭 {table}: empty")
        
        if all_good:
            print("\n🎉 All sequences are properly configured!")
        else:
            print("\n⚠️ Some sequences still need fixing")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """Main function"""
    print("🐛 BugYou Sequential ID Fix Tool")
    print("=" * 50)
    
    # Test database connection
    try:
        conn = get_direct_connection()
        conn.close()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Please check your database configuration")
        return False
    
    # Ask user what they want to do
    while True:
        print("\nWhat would you like to do?")
        print("1. Fix sequence IDs (recommended for existing databases)")
        print("2. Verify current sequence states")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            if fix_sequence_ids():
                print("\n✅ Sequence fix completed successfully!")
                verify_sequences()
            else:
                print("\n❌ Sequence fix failed. Please check the error messages above.")
        elif choice == '2':
            verify_sequences()
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == '__main__':
    main() 