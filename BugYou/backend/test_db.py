"""
Test script to check database content
"""

from database_config import DatabaseManager, get_challenge_by_id, get_all_available_challenges

def test_database():
    """Test database queries"""
    try:
        print("🔌 Testing database connection...")
        db = DatabaseManager()
        
        # Test basic connection
        with db.get_connection() as conn:
            print("✅ Database connection successful!")
            
            # Check if tables exist
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE '%_basic' OR table_name LIKE '%_intermediate' OR table_name LIKE '%_advanced'
                    ORDER BY table_name
                """)
                tables = cursor.fetchall()
                print(f"📋 Found tables: {[t[0] for t in tables]}")
                
                # Check python_basic table structure
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'python_basic' 
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                print(f"📊 python_basic columns: {[c[0] for c in columns]}")
                
                # Check if there's data in python_basic
                cursor.execute("SELECT COUNT(*) FROM python_basic")
                count = cursor.fetchone()[0]
                print(f"📈 Records in python_basic: {count}")
                
                if count > 0:
                    cursor.execute("SELECT challenge_id, title FROM python_basic LIMIT 3")
                    challenges = cursor.fetchall()
                    print(f"📝 Sample challenges: {challenges}")
        
        # Test our API functions
        print("\n🧪 Testing API functions...")
        
        # Test get_all_available_challenges
        all_challenges = get_all_available_challenges()
        print(f"📚 Total challenges found: {len(all_challenges)}")
        
        # Test get_challenge_by_id
        if all_challenges:
            first_challenge = all_challenges[0]
            challenge = get_challenge_by_id(
                first_challenge['language'], 
                first_challenge['difficulty'], 
                first_challenge['challenge_id']
            )
            if challenge:
                print(f"✅ Found challenge: {challenge['title']}")
                print(f"   Language: {challenge['language']}")
                print(f"   Difficulty: {challenge['difficulty']}")
                print(f"   Test cases: {len(challenge.get('test_cases', []))}")
            else:
                print("❌ Could not fetch challenge by ID")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database() 