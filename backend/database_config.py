"""
BugYou Database Configuration v2.0
PostgreSQL connection settings for language-specific challenge tables
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

# Load configuration from file
def load_config():
    """Load database configuration from config.env file"""
    config = {
        'host': 'localhost',
        'database': 'postgres', 
        'user': 'postgres',
        'password': 'Heroixthunder@1',
        'port': '5432'
    }
    
    try:
        if os.path.exists('config.env'):
            with open('config.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key.startswith('DB_'):
                            db_key = key[3:].lower()  # Remove DB_ prefix and lowercase
                            if db_key == 'name':
                                config['database'] = value
                            else:
                                config[db_key] = value
    except Exception as e:
        print(f"Warning: Could not read config.env: {e}")
    
    return config

# Database connection settings
DATABASE_CONFIG = load_config()

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
    """Database connection and query management for v2.0 schema"""
    
    def __init__(self, config=None):
        self.config = config or DATABASE_CONFIG
        
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = None
        try:
            conn = psycopg2.connect(**self.config)
            yield conn
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
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
        """Execute a query and return results"""
        with self.get_cursor() as (cursor, conn):
            cursor.execute(query, params)
            
            # Always commit for INSERT, UPDATE, DELETE operations
            if any(keyword in query.upper().strip() for keyword in ['INSERT', 'UPDATE', 'DELETE']):
                conn.commit()
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.rowcount

# Utility functions for v2.0 schema

def get_table_name(language, difficulty):
    """Get table name for language and difficulty"""
    if language in CHALLENGE_TABLES and difficulty in CHALLENGE_TABLES[language]:
        return CHALLENGE_TABLES[language][difficulty]
    else:
        raise ValueError(f"Unsupported combination: {language} - {difficulty}")

def get_challenges_by_language_difficulty(language, difficulty):
    """Get all challenges for a specific language and difficulty"""
    table_name = get_table_name(language, difficulty)
    db = DatabaseManager()
    query = f"SELECT * FROM {table_name} WHERE is_active = true ORDER BY challenge_id"
    return db.execute_query(query)

def get_challenge_by_id(language, difficulty, challenge_id):
    """Get a specific challenge with all its details including test cases"""
    table_name = get_table_name(language, difficulty)
    db = DatabaseManager()
    query = f"SELECT * FROM {table_name} WHERE challenge_id = %s AND is_active = true"
    challenge = db.execute_query(query, (challenge_id,), fetch_one=True)
    
    if challenge:
        # Add difficulty information from the table context
        challenge['difficulty'] = difficulty
        challenge['language'] = language
        
        # Extract test cases from the challenge record
        test_cases = []
        for i in range(1, 6):  # Up to 5 test cases
            input_key = f'test_case_{i}_input'
            expected_key = f'test_case_{i}_expected'
            desc_key = f'test_case_{i}_description'
            
            if challenge.get(input_key) and challenge.get(expected_key):
                test_cases.append({
                    'input': challenge[input_key],
                    'expected': challenge[expected_key],
                    'description': challenge.get(desc_key, f'Test case {i}')
                })
        
        challenge['test_cases'] = test_cases
    
    return challenge

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
                        description,
                        max_score,
                        time_limit_minutes,
                        completion_count,
                        success_rate
                    FROM {table_name} 
                    WHERE is_active = true
                    ORDER BY challenge_id
                """
                challenges = db.execute_query(query)
                all_challenges.extend(challenges)
            except Exception as e:
                print(f"Warning: Could not fetch challenges from {table_name}: {e}")
    
    return all_challenges

def save_user_submission_v2(user_id, language, difficulty, challenge_id, submitted_code, score, tests_passed, total_tests, hints_used, attempts):
    """Save a user submission in the v2.0 schema"""
    table_name = get_table_name(language, difficulty)
    db = DatabaseManager()
    
    # Create session
    session_query = """
        INSERT INTO user_sessions (user_id, challenge_table, challenge_id, current_code, hints_used, attempts_made, is_completed)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING session_id
    """
    is_successful = tests_passed == total_tests
    session = db.execute_query(session_query, (user_id, table_name, challenge_id, submitted_code, hints_used, attempts, is_successful), fetch_one=True)
    
    # Save submission - FIXED: Use correct column names
    submission_query = """
        INSERT INTO user_submissions 
        (session_id, user_id, challenge_table, challenge_id, submitted_code, score_achieved, total_tests_passed, total_tests_count, hints_used, attempts_made, is_successful)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING submission_id
    """
    submission = db.execute_query(submission_query, 
        (session['session_id'], user_id, table_name, challenge_id, submitted_code, score, tests_passed, total_tests, hints_used, attempts, is_successful), 
        fetch_one=True)
    
    # Update user progress
    if is_successful:
        progress_query = """
            INSERT INTO user_progress (user_id, challenge_table, challenge_id, best_score, completion_date, attempts_count, hints_used_total, is_completed)
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, true)
            ON CONFLICT (user_id, challenge_table, challenge_id)
            DO UPDATE SET
                best_score = GREATEST(user_progress.best_score, EXCLUDED.best_score),
                completion_date = COALESCE(user_progress.completion_date, EXCLUDED.completion_date),
                attempts_count = user_progress.attempts_count + EXCLUDED.attempts_count,
                hints_used_total = user_progress.hints_used_total + EXCLUDED.hints_used_total,
                is_completed = true
        """
        db.execute_query(progress_query, (user_id, table_name, challenge_id, score, attempts, hints_used), fetch_all=False)
        
        # Update user total score
        update_user_query = """
            UPDATE users SET 
                total_score = (SELECT COALESCE(SUM(best_score), 0) FROM user_progress WHERE user_id = %s),
                challenges_completed = (SELECT COUNT(*) FROM user_progress WHERE user_id = %s AND is_completed = true)
            WHERE user_id = %s
        """
        db.execute_query(update_user_query, (user_id, user_id, user_id), fetch_all=False)
    
    return submission

def get_user_progress_by_language(user_id, language=None, difficulty=None):
    """Get user progress, optionally filtered by language and/or difficulty"""
    db = DatabaseManager()
    
    if language and difficulty:
        table_name = get_table_name(language, difficulty)
        query = """
            SELECT challenge_table, challenge_id, best_score, completion_date, 
                   attempts_count, hints_used_total, is_completed
            FROM user_progress 
            WHERE user_id = %s AND challenge_table = %s
            ORDER BY challenge_id
        """
        return db.execute_query(query, (user_id, table_name))
    elif language:
        # Get all difficulties for this language
        tables = [get_table_name(language, diff) for diff in CHALLENGE_TABLES[language].keys()]
        placeholders = ','.join(['%s'] * len(tables))
        query = f"""
            SELECT challenge_table, challenge_id, best_score, completion_date,
                   attempts_count, hints_used_total, is_completed
            FROM user_progress 
            WHERE user_id = %s AND challenge_table IN ({placeholders})
            ORDER BY challenge_table, challenge_id
        """
        return db.execute_query(query, [user_id] + tables)
    else:
        # Get all progress
        query = """
            SELECT challenge_table, challenge_id, best_score, completion_date,
                   attempts_count, hints_used_total, is_completed
            FROM user_progress 
            WHERE user_id = %s
            ORDER BY challenge_table, challenge_id
        """
        return db.execute_query(query, (user_id,))

def get_language_difficulty_stats():
    """Get statistics for each language-difficulty combination"""
    db = DatabaseManager()
    stats = {}
    
    for language, difficulties in CHALLENGE_TABLES.items():
        stats[language] = {}
        for difficulty, table_name in difficulties.items():
            try:
                query = f"""
                    SELECT 
                        COUNT(*) as total_challenges,
                        AVG(success_rate) as avg_success_rate,
                        SUM(completion_count) as total_completions,
                        AVG(max_score) as avg_max_score
                    FROM {table_name}
                    WHERE is_active = true
                """
                result = db.execute_query(query, fetch_one=True)
                stats[language][difficulty] = result
            except Exception as e:
                print(f"Could not get stats for {table_name}: {e}")
                stats[language][difficulty] = None
    
    return stats

# Utility functions (reused from v1)
def test_connection():
    """Test database connection"""
    try:
        db = DatabaseManager()
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
                print("✅ Database connection successful!")
                return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def get_user_by_username(username):
    """Get user by username"""
    db = DatabaseManager()
    query = "SELECT * FROM users WHERE username = %s"
    return db.execute_query(query, (username,), fetch_one=True)

def create_user(username, email, password_hash, display_name=None):
    """Create a new user"""
    db = DatabaseManager()
    query = """
        INSERT INTO users (username, email, password_hash, display_name)
        VALUES (%s, %s, %s, %s)
        RETURNING user_id
    """
    return db.execute_query(query, (username, email, password_hash, display_name), fetch_one=True)

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