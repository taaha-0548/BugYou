#!/usr/bin/env python3

from database_config import DatabaseManager
import traceback

def fix_cpp_inputs():
    """Fix C++ input formats"""
    print("🔧 Fixing C++ input formats...")
    
    db = DatabaseManager()
    
    # Update C++ inputs
    update_query = """
        UPDATE cpp_basic 
        SET test_case_1_input = %s,
            test_case_2_input = %s,
            test_case_3_input = %s,
            test_case_4_input = %s,
            test_case_5_input = %s
        WHERE challenge_id = 1
    """
    
    new_inputs = [
        'std::vector<int>{1, 2, 3, 4, 5}',
        'std::vector<int>{10, 20}', 
        'std::vector<int>{}',
        'std::vector<int>{7, 8, 9, 10, 11, 12}',
        'std::vector<int>{100}'
    ]
    
    try:
        result = db.execute_query(update_query, new_inputs, fetch_all=False)
        print(f"  ✅ Updated C++ inputs, affected rows: {result}")
        return True
    except Exception as e:
        print(f"  ❌ Error updating C++ inputs: {e}")
        traceback.print_exc()
        return False

def fix_java_inputs():
    """Fix Java input formats"""
    print("🔧 Fixing Java input formats...")
    
    db = DatabaseManager()
    
    # Update Java inputs
    update_query = """
        UPDATE java_basic 
        SET test_case_1_input = %s,
            test_case_2_input = %s,
            test_case_3_input = %s,
            test_case_4_input = %s,
            test_case_5_input = %s
        WHERE challenge_id = 1
    """
    
    new_inputs = [
        'new int[]{1, 2, 3, 4, 5}',
        'new int[]{10, 5, 8, 2}',
        'new int[]{7, 7, 7}',
        'new int[]{15, 12, 18, 9}',
        'new int[]{100}'
    ]
    
    try:
        result = db.execute_query(update_query, new_inputs, fetch_all=False)
        print(f"  ✅ Updated Java inputs, affected rows: {result}")
        return True
    except Exception as e:
        print(f"  ❌ Error updating Java inputs: {e}")
        traceback.print_exc()
        return False

def main():
    print("🚀 Starting input format fixes...\n")
    
    cpp_success = fix_cpp_inputs()
    java_success = fix_java_inputs()
    
    if cpp_success and java_success:
        print("\n🎉 All input format fixes completed successfully!")
    else:
        print("\n⚠️ Some fixes failed. Check the errors above.")

if __name__ == "__main__":
    main() 