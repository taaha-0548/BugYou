#!/usr/bin/env python3
"""
Script to check and fix ALL test case inputs in ALL tables
"""

import re
from database_config import DatabaseManager

def clean_input_format(input_str):
    """Clean input to simple [1,2,3] format"""
    if not input_str:
        return input_str
    
    # Handle Java format: new int[]{1, 2, 3, 4, 5}
    java_match = re.search(r'new\s+\w+\[\]\s*\{([^}]+)\}', input_str)
    if java_match:
        values = java_match.group(1).strip()
        return f"[{values}]"
    
    # Handle C++ format: std::vector<int>{1, 2, 3, 4, 5}
    cpp_match = re.search(r'std::vector<[^>]+>\s*\{([^}]+)\}', input_str)
    if cpp_match:
        values = cpp_match.group(1).strip()
        return f"[{values}]"
    
    # Already in correct format or simple value
    return input_str

def main():
    db = DatabaseManager()
    
    tables = ['python_basic', 'javascript_basic', 'java_basic', 'cpp_basic']
    
    for table in tables:
        print(f"\n=== Checking {table} ===")
        
        # Get all rows
        try:
            rows = db.execute_query(f"SELECT challenge_id, test_case_1_input, test_case_2_input FROM {table} ORDER BY challenge_id")
            
            if not rows:
                print(f"  No data found in {table}")
                continue
            
            for row in rows:
                challenge_id = row['challenge_id']
                tc1_input = row['test_case_1_input'] 
                tc2_input = row['test_case_2_input']
                
                print(f"  Before - ID {challenge_id}:")
                print(f"    tc1: '{tc1_input}'")
                print(f"    tc2: '{tc2_input}'")
                
                # Clean the inputs
                new_tc1 = clean_input_format(tc1_input)
                new_tc2 = clean_input_format(tc2_input)
                
                # Update if changed
                if new_tc1 != tc1_input or new_tc2 != tc2_input:
                    print(f"  After - ID {challenge_id}:")
                    print(f"    tc1: '{new_tc1}'")
                    print(f"    tc2: '{new_tc2}'")
                    
                    # Update the database
                    update_query = f"""
                        UPDATE {table} 
                        SET test_case_1_input = %s, test_case_2_input = %s
                        WHERE challenge_id = %s
                    """
                    db.execute_query(update_query, (new_tc1, new_tc2, challenge_id), fetch_all=False)
                    print(f"  ✅ Updated challenge {challenge_id} in {table}")
                else:
                    print(f"  ✅ No changes needed for challenge {challenge_id}")
                    
        except Exception as e:
            print(f"  ❌ Error processing {table}: {e}")
    
    print("\n🎉 All test case inputs have been checked and fixed!")

if __name__ == "__main__":
    main() 