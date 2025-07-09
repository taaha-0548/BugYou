#!/usr/bin/env python3

from database_config import DatabaseManager

def fix_to_simple_format():
    """Fix all test inputs to simple [10, 20] format"""
    print("🔧 Fixing all inputs to simple format...\n")
    
    db = DatabaseManager()
    
    # Fix C++ inputs to simple format
    print("📌 Fixing C++ inputs...")
    cpp_query = """
        UPDATE cpp_basic 
        SET test_case_1_input = '[1, 2, 3, 4, 5]',
            test_case_2_input = '[10, 20]',
            test_case_3_input = '[]',
            test_case_4_input = '[7, 8, 9, 10, 11, 12]',
            test_case_5_input = '[100]'
        WHERE challenge_id = 1
    """
    
    try:
        result = db.execute_query(cpp_query, fetch_all=False)
        print(f"  ✅ Updated C++ inputs, affected rows: {result}")
    except Exception as e:
        print(f"  ❌ Error updating C++ inputs: {e}")
    
    # Fix Java inputs to simple format  
    print("📌 Fixing Java inputs...")
    java_query = """
        UPDATE java_basic 
        SET test_case_1_input = '[1, 2, 3, 4, 5]',
            test_case_2_input = '[10, 5, 8, 2]',
            test_case_3_input = '[7, 7, 7]',
            test_case_4_input = '[15, 12, 18, 9]',
            test_case_5_input = '[100]'
        WHERE challenge_id = 1
    """
    
    try:
        result = db.execute_query(java_query, fetch_all=False)
        print(f"  ✅ Updated Java inputs, affected rows: {result}")
    except Exception as e:
        print(f"  ❌ Error updating Java inputs: {e}")
    
    print("\n🎉 All inputs fixed to simple [10, 20] format!")

if __name__ == "__main__":
    fix_to_simple_format() 