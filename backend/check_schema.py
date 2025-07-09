#!/usr/bin/env python3
"""
Script to check database schema
"""

import psycopg2
from database_config import DATABASE_CONFIG

def check_schema():
    """Check the database schema"""
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        # Get column information
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'python_basic' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("Columns in python_basic table:")
        for i, (name, type_, nullable, default) in enumerate(columns, 1):
            default_str = f" DEFAULT {default}" if default else ""
            print(f"{i:2d}. {name:25} ({type_:<20}) {'NULL' if nullable == 'YES' else 'NOT NULL':<8}{default_str}")
        
        print(f"\nTotal columns: {len(columns)}")
        
        # Also check the columns used in sample_data.sql
        sample_columns = [
            'challenge_id', 'title', 'problem_statement', 'buggy_code', 
            'reference_solution', 'solution_explanation', 'hint_1', 'hint_2', 
            'hint_3', 'learning_objectives', 'max_score', 'test_case_1_input', 
            'test_case_1_expected', 'test_case_2_input', 'test_case_2_expected', 
            'test_case_3_input', 'test_case_3_expected'
        ]
        
        all_columns = [col[0] for col in columns]
        missing_columns = [col for col in all_columns if col not in sample_columns]
        print(f"\nColumns in table but NOT in sample_data.sql ({len(missing_columns)}):")
        for col in missing_columns:
            print(f"  - {col}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema() 