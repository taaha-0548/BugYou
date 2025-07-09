#!/usr/bin/env python3
"""
Migration Script: Shared to Independent Sequences
This script migrates from the old shared sequence system to independent sequences per table.
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

def migrate_to_independent_sequences():
    """
    Migrate from shared sequences to independent sequences.
    This will:
    1. Backup existing data
    2. Recreate tables with independent sequences
    3. Restore data with new sequential IDs starting from 1 for each table
    """
    
    print("🔄 Starting migration to independent sequences...")
    print("⚠️  This will modify your database structure!")
    
    # Confirm with user
    confirm = input("\nDo you want to continue? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("Migration cancelled.")
        return False
    
    tables = [
        'python_basic', 'python_intermediate', 'python_advanced',
        'javascript_basic', 'javascript_intermediate', 'javascript_advanced',
        'java_basic', 'java_intermediate', 'java_advanced',
        'cpp_basic', 'cpp_intermediate', 'cpp_advanced'
    ]
    
    try:
        conn = get_direct_connection()
        cursor = conn.cursor()
        
        # Step 1: Backup all data
        print("\n📦 Step 1: Backing up existing data...")
        backup_data = {}
        
        for table in tables:
            print(f"   - Backing up {table}...")
            cursor.execute(f"""
                SELECT * FROM {table} ORDER BY challenge_id
            """)
            backup_data[table] = cursor.fetchall()
            print(f"     ✅ Backed up {len(backup_data[table])} records")
        
        # Step 2: Get table structure
        print("\n🏗️  Step 2: Getting table structure...")
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'python_basic' 
            ORDER BY ordinal_position
        """)
        columns_info = cursor.fetchall()
        
        # Step 3: Drop and recreate tables with independent sequences
        print("\n🔨 Step 3: Recreating tables with independent sequences...")
        
        # Read the new schema from database_setup.sql
        schema_file = os.path.join(os.path.dirname(__file__), 'database_setup.sql')
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Execute the new schema (this will drop and recreate all tables)
        print("   - Executing new schema...")
        cursor.execute(schema_sql)
        
        # Step 4: Restore data with new sequential IDs
        print("\n📝 Step 4: Restoring data with sequential IDs...")
        
        for table in tables:
            if backup_data[table]:
                print(f"   - Restoring {table}...")
                
                # Get column names excluding challenge_id (auto-generated)
                cursor.execute(f"""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = '{table}' AND column_name != 'challenge_id'
                    ORDER BY ordinal_position
                """)
                columns = [row[0] for row in cursor.fetchall()]
                
                # Prepare INSERT statement
                placeholders = ', '.join(['%s'] * len(columns))
                columns_str = ', '.join(columns)
                insert_sql = f"""
                    INSERT INTO {table} ({columns_str}) VALUES ({placeholders})
                """
                
                # Insert data (excluding the old challenge_id)
                for row in backup_data[table]:
                    # Skip the first column (challenge_id) and insert the rest
                    data_to_insert = row[1:]  # Skip challenge_id
                    cursor.execute(insert_sql, data_to_insert)
                
                print(f"     ✅ Restored {len(backup_data[table])} records with new sequential IDs")
        
        # Step 5: Reset sequences
        print("\n🔄 Step 5: Resetting sequences...")
        
        for table in tables:
            cursor.execute(f"""
                SELECT COUNT(*) FROM {table}
            """)
            count = cursor.fetchone()[0]
            
            if count > 0:
                # Get sequence name and reset it
                cursor.execute(f"""
                    SELECT pg_get_serial_sequence('{table}', 'challenge_id')
                """)
                sequence_name = cursor.fetchone()[0]
                
                if sequence_name:
                    cursor.execute(f"""
                        SELECT setval('{sequence_name}', {count}, true)
                    """)
                    print(f"   ✅ Reset sequence for {table} to {count}")
        
        # Commit all changes
        conn.commit()
        
        print("\n🎉 Migration completed successfully!")
        print("\n📊 Summary:")
        
        # Verify the results
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
                print(f"   - {table}: {count} records, IDs {min_id}-{max_id}")
            else:
                print(f"   - {table}: empty")
        
        print("\n✅ Each table now has independent sequential IDs starting from 1!")
        
        return True
        
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

def check_current_system():
    """Check if the current system uses shared or independent sequences"""
    print("🔍 Analyzing current sequence system...")
    
    tables = [
        'python_basic', 'python_intermediate', 'python_advanced',
        'javascript_basic', 'javascript_intermediate', 'javascript_advanced',
        'java_basic', 'java_intermediate', 'java_advanced',
        'cpp_basic', 'cpp_intermediate', 'cpp_advanced'
    ]
    
    try:
        conn = get_direct_connection()
        cursor = conn.cursor()
        
        # Get sequence information for each table
        sequence_info = {}
        all_ids = []
        
        for table in tables:
            cursor.execute(f"""
                SELECT COUNT(*) FROM {table}
            """)
            count = cursor.fetchone()[0]
            
            if count > 0:
                cursor.execute(f"""
                    SELECT challenge_id FROM {table} ORDER BY challenge_id
                """)
                ids = [row[0] for row in cursor.fetchall()]
                sequence_info[table] = ids
                all_ids.extend(ids)
                
                min_id, max_id = min(ids), max(ids)
                expected_ids = list(range(1, len(ids) + 1))
                is_sequential = ids == expected_ids
                
                print(f"   - {table}: {count} records, IDs {min_id}-{max_id} {'✅' if is_sequential else '❌'}")
        
        # Check if IDs overlap between tables (indicating shared sequences)
        all_ids_set = set(all_ids)
        has_overlaps = len(all_ids) != len(all_ids_set)
        
        print(f"\n📊 Analysis Results:")
        print(f"   - Total unique IDs across all tables: {len(all_ids_set)}")
        print(f"   - Total IDs (including duplicates): {len(all_ids)}")
        print(f"   - ID overlaps between tables: {'Yes' if has_overlaps else 'No'}")
        
        if has_overlaps:
            print("\n⚠️  Current system appears to use SHARED sequences")
            print("   Each table does NOT have independent sequential IDs starting from 1")
            print("   Migration is RECOMMENDED")
        else:
            # Check if each table starts from 1
            all_start_from_1 = True
            for table, ids in sequence_info.items():
                if ids and ids[0] != 1:
                    all_start_from_1 = False
                    break
            
            if all_start_from_1:
                print("\n✅ Current system uses INDEPENDENT sequences")
                print("   Each table has its own sequential IDs starting from 1")
                print("   No migration needed")
            else:
                print("\n⚠️  Current system has MIXED sequence behavior")
                print("   Some tables may not start from 1")
                print("   Migration is RECOMMENDED")
        
        return not has_overlaps and all_start_from_1
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def main():
    """Main function"""
    print("🐛 BugYou Sequence Migration Tool")
    print("=" * 50)
    
    # Test database connection
    try:
        conn = get_direct_connection()
        conn.close()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Please check your database configuration")
        return
    
    # Check current system
    is_independent = check_current_system()
    
    if is_independent:
        print("\n🎉 Your database already uses independent sequences!")
        print("No migration is needed.")
        return
    
    print("\n" + "=" * 50)
    print("MIGRATION OPTIONS:")
    print("1. Migrate to independent sequences (RECOMMENDED)")
    print("2. Exit without changes")
    
    choice = input("\nEnter your choice (1-2): ").strip()
    
    if choice == '1':
        if migrate_to_independent_sequences():
            print("\n🎉 Migration completed successfully!")
            print("Your database now uses independent sequences for each table.")
        else:
            print("\n❌ Migration failed. Please check the error messages above.")
    elif choice == '2':
        print("👋 No changes made. Goodbye!")
    else:
        print("Invalid choice.")

if __name__ == '__main__':
    main() 