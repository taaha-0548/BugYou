#!/usr/bin/env python3
"""
Script to fix database inputs to use simple [1,2,3] format
instead of language-specific formats like new int[]{1,2,3} or std::vector<int>{1,2,3}
"""

import re
from database_config import DatabaseManager

def extract_array_values(input_str):
    """Extract array values from various formats and return as [1,2,3] format"""
    if not input_str:
        return input_str
    
    # Handle Java format: new int[]{1, 2, 3, 4, 5}
    java_match = re.search(r'new\s+\w+\[]\s*\{([^}]+)\}', input_str)
    if java_match:
        values = java_match.group(1).strip()
        return f"[{values}]"
    
    # Handle C++ format: std::vector<int>{1, 2, 3, 4, 5}
    cpp_match = re.search(r'std::vector<[^>]+>\s*\{([^}]+)\}', input_str)
    if cpp_match:
        values = cpp_match.group(1).strip()
        return f"[{values}]"
    
    # Handle already correct format [1, 2, 3]
    if input_str.strip().startswith('[') and input_str.strip().endswith(']'):
        return input_str.strip()
    
    # Handle bare values like "1, 2, 3"
    if re.match(r'^\s*\d+(\s*,\s*\d+)*\s*$', input_str):
        return f"[{input_str.strip()}]"
    
    # Return as-is for other formats
    return input_str

def fix_table_inputs(db, table_name):
    """Fix inputs for a specific table"""
    print(f"Fixing inputs for table: {table_name}")
    
    # Get all rows
    rows = db.execute_query(f"SELECT challenge_id, test_case_1_input, test_case_1_expected, test_case_2_input, test_case_2_expected FROM {table_name}")
    
    if not rows:
        print(f"  No data found in {table_name}")
        return
    
    updates = 0
    for row in rows:
        # Access by dictionary keys since the database returns Row objects
        challenge_id = row['challenge_id']
        tc1_input = row['test_case_1_input']
        tc1_expected = row['test_case_1_expected']
        tc2_input = row['test_case_2_input']
        tc2_expected = row['test_case_2_expected']
        
        # Fix inputs
        new_tc1_input = extract_array_values(tc1_input)
        new_tc2_input = extract_array_values(tc2_input)
        
        # Check if we need to update
        if new_tc1_input != tc1_input or new_tc2_input != tc2_input:
            print(f"  Challenge {challenge_id}:")
            if new_tc1_input != tc1_input:
                print(f"    TC1: '{tc1_input}' -> '{new_tc1_input}'")
            if new_tc2_input != tc2_input:
                print(f"    TC2: '{tc2_input}' -> '{new_tc2_input}'")
            
            # Update the database
            update_query = f"""
                UPDATE {table_name} 
                SET test_case_1_input = %s, test_case_2_input = %s
                WHERE challenge_id = %s
            """
            db.execute_query(update_query, (new_tc1_input, new_tc2_input, challenge_id), fetch_all=False)
            updates += 1
    
    print(f"  Updated {updates} rows in {table_name}")

def main():
    """Main function to fix all database inputs"""
    print("🔧 Fixing database inputs to use simple [1,2,3] format...")
    
    db = DatabaseManager()
    
    # Tables to fix
    tables = ['python_basic', 'javascript_basic', 'java_basic', 'cpp_basic']
    
    for table in tables:
        try:
            fix_table_inputs(db, table)
        except Exception as e:
            print(f"❌ Error fixing {table}: {e}")
    
    print("✅ Database input format fix completed!")

if __name__ == "__main__":
    main() 