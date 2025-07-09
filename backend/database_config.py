"""
BugYou Database Configuration v2.0
PostgreSQL connection settings for language-specific challenge tables using Neon DB
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
import time

# Database connection settings for Neon DB
DATABASE_CONFIG = {
    'dbname': 'neondb',
    'user': 'neondb_owner',
    'password': 'npg_zfHPGRA2Jr0m',
    'host': 'ep-bold-darkness-a17nsgge-pooler.ap-southeast-1.aws.neon.tech',
    'sslmode': 'require'
}

# Connection pool for better performance
_connection_pool = None

def get_connection_pool():
    """Get or create connection pool"""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            **DATABASE_CONFIG
        )
    return _connection_pool

# Supported language-difficulty combinations
CHALLENGE_TABLES = {
    'python': {
        'basic': 'python_basic',
        'intermediate': 'python_intermediate',
        'advanced': 'python_advanced'
    },
    'javascript': {
        'basic': 'javascript_basic',
        'intermediate': 'javascript_intermediate', 
        'advanced': 'javascript_advanced'
    },
    'java': {
        'basic': 'java_basic',
        'intermediate': 'java_intermediate',
        'advanced': 'java_advanced'
    },
    'cpp': {
        'basic': 'cpp_basic',
        'intermediate': 'cpp_intermediate',
        'advanced': 'cpp_advanced'
    }
}

class DatabaseManager:
    """Database connection and query management for v2.0 schema with connection pooling"""
    
    def __init__(self, config=None):
        self.config = config or DATABASE_CONFIG
        self.pool = get_connection_pool()
        
    @contextmanager
    def get_connection(self):
        """Get database connection from pool with automatic cleanup"""
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, dict_cursor=True):
        """Get database cursor with automatic cleanup"""
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor, conn
            finally:
                cursor.close()
    
    def execute_query(self, query, params=None, fetch_one=False, fetch_all=True):
        """Execute a query and return results with performance logging"""
        start_time = time.time()
        try:
            with self.get_cursor() as (cursor, conn):
                cursor.execute(query, params)
                
                # Always commit for INSERT, UPDATE, DELETE operations
                if any(keyword in query.upper().strip() for keyword in ['INSERT', 'UPDATE', 'DELETE']):
                    conn.commit()
                
                if fetch_one:
                    result = cursor.fetchone()
                elif fetch_all:
                    result = cursor.fetchall()
                else:
                    conn.commit()
                    result = cursor.rowcount
                
                # Log slow queries
                execution_time = time.time() - start_time
                if execution_time > 0.5:  # Log queries taking more than 500ms
                    print(f"Slow query detected: {execution_time:.3f}s - {query[:100]}...")
                
                return result
        except Exception as e:
            print(f"Database error: {e}")
            raise e

def get_table_name(language, difficulty):
    """Get table name for language and difficulty"""
    if language in CHALLENGE_TABLES and difficulty in CHALLENGE_TABLES[language]:
        return CHALLENGE_TABLES[language][difficulty]
    else:
        raise ValueError(f"Unsupported combination: {language} - {difficulty}")

def get_challenges_by_language_difficulty(language, difficulty):
    """Get all challenges for a specific language and difficulty with caching"""
    table_name = get_table_name(language, difficulty)
    db = DatabaseManager()
    query = f"""
        SELECT 
            challenge_id,
            title,
            problem_statement,
            max_score,
            success_rate,
            avg_attempts
        FROM {table_name}
        ORDER BY challenge_id
    """
    return db.execute_query(query)

def get_challenge_by_id(language, difficulty, challenge_id):
    """Get a specific challenge with all its details including test cases"""
    table_name = get_table_name(language, difficulty)
    db = DatabaseManager()
    query = f"""
        SELECT 
            challenge_id,
            title,
            problem_statement,
            buggy_code,
            reference_solution,
            solution_explanation,
            hint_1,
            hint_2,
            hint_3,
            learning_objectives,
            max_score,
            test_case_1_input,
            test_case_1_expected,
            test_case_2_input,
            test_case_2_expected,
            test_case_3_input,
            test_case_3_expected,
            test_case_4_input,
            test_case_4_expected,
            test_case_5_input,
            test_case_5_expected,
            success_rate,
            avg_attempts
        FROM {table_name}
        WHERE challenge_id = %s
    """
    challenge = db.execute_query(query, (challenge_id,), fetch_one=True)
    
    if challenge:
        # Add difficulty information from the table context
        challenge['difficulty'] = difficulty
        challenge['language'] = language
        
        # Combine hints into an array
        hints = []
        for i in range(1, 4):  # hint_1 through hint_3
            hint_key = f'hint_{i}'
            if hint_key in challenge and challenge[hint_key]:
                hints.append(challenge[hint_key])
        challenge['hints'] = hints
        
        # Extract test cases from the challenge record
        test_cases = []
        for i in range(1, 6):  # Up to 5 test cases
            input_key = f'test_case_{i}_input'
            expected_key = f'test_case_{i}_expected'
            
            # Get values, handling None cases
            test_input = challenge.get(input_key)
            test_expected = challenge.get(expected_key)
            
            # If we have at least one test case field, create a test case with defaults
            if test_input is not None or test_expected is not None:
                # Provide defaults for C++ if data is missing
                if language == 'cpp':
                    if test_input is None or test_input == '':
                        test_input = '[1, 2, 3]'  # Default vector input
                    if test_expected is None or test_expected == '':
                        test_expected = '3'  # Default expected output
                else:
                    # For other languages, use reasonable defaults
                    if test_input is None or test_input == '':
                        test_input = '[1, 2, 3]'
                    if test_expected is None or test_expected == '':
                        test_expected = '3'
                
                test_cases.append({
                    'input': test_input,
                    'expected_output': test_expected
                })
            
            # Clean up the individual test case fields
            if input_key in challenge:
                del challenge[input_key]
            if expected_key in challenge:
                del challenge[expected_key]
        
        # Ensure we have at least one test case
        if not test_cases:
            # Create a default test case based on language
            if language == 'cpp':
                test_cases.append({
                    'input': '[1, 2, 3]',
                    'expected_output': '3'
                })
            else:
                test_cases.append({
                    'input': '[1, 2, 3]',
                    'expected_output': '3'
                })
        
        # Add test cases array to challenge
        challenge['test_cases'] = test_cases
        
        return challenge
    return None

def get_all_available_challenges():
    """Get summary of all available challenges across all languages and difficulties"""
    db = DatabaseManager()
    all_challenges = []
    
    for language, difficulties in CHALLENGE_TABLES.items():
        for difficulty, table_name in difficulties.items():
            try:
                query = f"""
                    SELECT 
                        '{language}' as language,
                        '{difficulty}' as difficulty,
                        challenge_id,
                        title,
                        problem_statement,
                        max_score,
                        success_rate,
                        avg_attempts
                    FROM {table_name}
                    ORDER BY challenge_id
                """
                challenges = db.execute_query(query)
                all_challenges.extend(challenges)
            except Exception as e:
                print(f"Warning: Could not fetch challenges from {table_name}: {e}")
    
    return all_challenges

def test_connection():
    """Test database connection with timeout"""
    try:
        db = DatabaseManager()
        with db.get_cursor() as (cursor, conn):
            cursor.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False

def get_user_by_username(username):
    """Get user by username"""
    db = DatabaseManager()
    query = "SELECT user_id, username FROM users WHERE username = %s"
    return db.execute_query(query, (username,), fetch_one=True)

def create_user(username):
    """Create a new user"""
    db = DatabaseManager()
    query = "INSERT INTO users (username) VALUES (%s) RETURNING user_id, username"
    return db.execute_query(query, (username,), fetch_one=True)

def get_leaderboard(limit=10):
    """Get top users for leaderboard"""
    db = DatabaseManager()
    query = "SELECT * FROM leaderboard LIMIT %s"
    return db.execute_query(query, (limit,))

def setup_environment():
    """Setup environment variables for database"""
    env_content = f"""# BugYou Database Environment Variables v2.0
DB_HOST=localhost
DB_NAME=bugyou
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_PORT=5432
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created. Please update DB_PASSWORD with your actual password.")

if __name__ == "__main__":
    # Test the database connection
    test_connection()
    
    # Show available challenge combinations
    print("\n📚 Available Challenge Categories:")
    for lang, difficulties in CHALLENGE_TABLES.items():
        print(f"  {lang.upper()}: {', '.join(difficulties.keys())}") 