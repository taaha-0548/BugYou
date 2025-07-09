from database_config import DatabaseManager

def fix_input_formats():
    """Fix input formats for C++ and Java challenges"""
    print("🔧 Fixing input formats for C++ and Java challenges...\n")
    
    db = DatabaseManager()
    
    # C++ input format fixes - convert {} to vector initialization
    print("📌 Fixing C++ input formats...")
    cpp_fixes = [
        # C++ Basic Challenge 1: Count Elements
        {
            'table': 'cpp_basic',
            'challenge_id': 1,
            'test_case_1_input': 'std::vector<int>{1, 2, 3, 4, 5}',
            'test_case_2_input': 'std::vector<int>{10, 20}',
            'test_case_3_input': 'std::vector<int>{}',
            'test_case_4_input': 'std::vector<int>{7, 8, 9, 10, 11, 12}',
            'test_case_5_input': 'std::vector<int>{100}',
        }
    ]
    
    # Java input format fixes - convert {} to proper array syntax
    print("📌 Fixing Java input formats...")
    java_fixes = [
        # Java Basic Challenge 1: Find Minimum
        {
            'table': 'java_basic',
            'challenge_id': 1,
            'test_case_1_input': 'new int[]{1, 2, 3, 4, 5}',
            'test_case_2_input': 'new int[]{10, 5, 8, 2}',
            'test_case_3_input': 'new int[]{7, 7, 7}',
            'test_case_4_input': 'new int[]{15, 12, 18, 9}',
            'test_case_5_input': 'new int[]{100}',
        }
    ]
    
    # Apply C++ fixes
    for fix in cpp_fixes:
        table = fix.pop('table')
        challenge_id = fix.pop('challenge_id')
        
        # Build SET clause dynamically
        set_clauses = []
        params = []
        for column, value in fix.items():
            set_clauses.append(f"{column} = %s")
            params.append(value)
        
        params.append(challenge_id)  # For WHERE clause
        
        query = f"""
            UPDATE {table} 
            SET {', '.join(set_clauses)}
            WHERE challenge_id = %s
        """
        
        print(f"  Updating {table} challenge {challenge_id}...")
        try:
            result = db.execute_query(query, params, fetch_all=False)
            print(f"    ✅ Updated {result} rows")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Apply Java fixes
    for fix in java_fixes:
        table = fix.pop('table')
        challenge_id = fix.pop('challenge_id')
        
        # Build SET clause dynamically
        set_clauses = []
        params = []
        for column, value in fix.items():
            set_clauses.append(f"{column} = %s")
            params.append(value)
        
        params.append(challenge_id)  # For WHERE clause
        
        query = f"""
            UPDATE {table} 
            SET {', '.join(set_clauses)}
            WHERE challenge_id = %s
        """
        
        print(f"  Updating {table} challenge {challenge_id}...")
        try:
            result = db.execute_query(query, params, fetch_all=False)
            print(f"    ✅ Updated {result} rows")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    print("\n🎉 Input format fixes completed!")

if __name__ == "__main__":
    fix_input_formats() 