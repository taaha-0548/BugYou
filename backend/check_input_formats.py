from database_config import get_db_connection

def check_input_formats():
    print("🔍 Checking test case input formats in database...\n")
    
    # Check each language table
    tables = [
        ('python_basic', 'Python Basic'),
        ('javascript_basic', 'JavaScript Basic'), 
        ('java_basic', 'Java Basic'),
        ('cpp_basic', 'C++ Basic')
    ]
    
    for table_name, display_name in tables:
        print(f"📌 {display_name}:")
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = f"""
                SELECT challenge_id, title, test_case_1_input, test_case_2_input, test_case_3_input 
                FROM {table_name} 
                ORDER BY challenge_id
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            if rows:
                for row in rows:
                    challenge_id, title, input1, input2, input3 = row
                    print(f"  Challenge {challenge_id}: {title}")
                    print(f"    Test 1: {input1}")
                    print(f"    Test 2: {input2}")
                    print(f"    Test 3: {input3}")
                    print()
            else:
                print("    No data found")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
        
        print("-" * 50)

if __name__ == "__main__":
    check_input_formats() 