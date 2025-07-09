#!/usr/bin/env python3
"""
Script to verify current database state
"""

import psycopg2
from database_config import DATABASE_CONFIG

def verify_data():
    """Verify current database state"""
    try:
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        # Check tables and their data
        tables_info = [
            ('python_basic', 'Python Basic'),
            ('javascript_basic', 'JavaScript Basic'), 
            ('java_basic', 'Java Basic'),
            ('cpp_basic', 'C++ Basic')
        ]
        
        print("\n📊 Current Database State:")
        total_challenges = 0
        
        for table, name in tables_info:
            try:
                cursor.execute(f"SELECT challenge_id, title, LEFT(buggy_code, 50) FROM {table} ORDER BY challenge_id")
                challenges = cursor.fetchall()
                if challenges:
                    ids = [str(c[0]) for c in challenges]
                    print(f"\n{name}: IDs {', '.join(ids)} ({len(challenges)} challenges)")
                    for challenge in challenges:
                        code_preview = challenge[2].replace('\n', ' ')
                        print(f"     - ID {challenge[0]}: {challenge[1]}")
                        print(f"       Code: {code_preview}...")
                    total_challenges += len(challenges)
                else:
                    print(f"\n{name}: No challenges")
            except Exception as e:
                print(f"\n{name}: Error - {e}")
        
        print(f"\n🎯 Total challenges across all tables: {total_challenges}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_data() 