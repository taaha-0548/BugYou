#!/usr/bin/env python3
"""
Fix newline characters in database
Replace literal '\n' strings with actual line breaks in problem statements and other text fields
"""

import psycopg2
from database_config import DATABASE_CONFIG, CHALLENGE_TABLES

def fix_newlines_in_table(table_name):
    """Fix newline characters in a specific table"""
    conn = psycopg2.connect(**DATABASE_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Get all records from the table
        cursor.execute(f"SELECT challenge_id, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3 FROM {table_name}")
        records = cursor.fetchall()
        
        print(f"Processing {len(records)} records in {table_name}...")
        
        for record in records:
            challenge_id, problem_statement, buggy_code, reference_solution, solution_explanation, hint_1, hint_2, hint_3 = record
            
            # Fix newlines in each field
            if problem_statement:
                problem_statement = problem_statement.replace('\\n', '\n')
            if buggy_code:
                buggy_code = buggy_code.replace('\\n', '\n')
            if reference_solution:
                reference_solution = reference_solution.replace('\\n', '\n')
            if solution_explanation:
                solution_explanation = solution_explanation.replace('\\n', '\n')
            if hint_1:
                hint_1 = hint_1.replace('\\n', '\n')
            if hint_2:
                hint_2 = hint_2.replace('\\n', '\n')
            if hint_3:
                hint_3 = hint_3.replace('\\n', '\n')
            
            # Update the record
            cursor.execute(f"""
                UPDATE {table_name} 
                SET problem_statement = %s, buggy_code = %s, reference_solution = %s, 
                    solution_explanation = %s, hint_1 = %s, hint_2 = %s, hint_3 = %s
                WHERE challenge_id = %s
            """, (problem_statement, buggy_code, reference_solution, solution_explanation, 
                  hint_1, hint_2, hint_3, challenge_id))
        
        conn.commit()
        print(f"✅ Fixed newlines in {table_name}")
        
    except Exception as e:
        print(f"❌ Error processing {table_name}: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def main():
    """Fix newlines in all challenge tables"""
    print("🔧 Fixing newline characters in database...")
    
    for language, difficulties in CHALLENGE_TABLES.items():
        for difficulty, table_name in difficulties.items():
            print(f"\nProcessing {language} {difficulty}...")
            fix_newlines_in_table(table_name)
    
    print("\n✅ All newline fixes completed!")

if __name__ == "__main__":
    main() 