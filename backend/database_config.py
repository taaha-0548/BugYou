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
import json
from datetime import datetime

# Database connection settings for Neon DB
DATABASE_CONFIG = {
    'dbname': os.environ.get('DB_NAME'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'host': os.environ.get('DB_HOST'),
    'sslmode': os.environ.get('DB_SSLMODE', 'require')
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
    """Get a specific challenge with all its details including test cases and driver_code"""
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
            hidden_test_1_input,
            hidden_test_1_expected,
            hidden_test_2_input,
            hidden_test_2_expected,
            driver_code,
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
                    # Convert [1, 2, 3] to {1,2,3} for C++
                    if isinstance(test_input, str) and test_input.startswith('['):
                        test_input = '{' + test_input.strip('[]').replace(' ', '') + '}'
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
                    'input': '{1,2,3}',
                    'expected_output': '3'
                })
            else:
                test_cases.append({
                    'input': '[1, 2, 3]',
                    'expected_output': '3'
                })
        
        # Add test cases array to challenge
        challenge['test_cases'] = test_cases

        # Extract hidden test cases from the challenge record
        hidden_test_cases = []
        for i in range(1, 3):  # Up to 2 hidden test cases
            input_key = f'hidden_test_{i}_input'
            expected_key = f'hidden_test_{i}_expected'
            test_input = challenge.get(input_key)
            test_expected = challenge.get(expected_key)
            if test_input is not None or test_expected is not None:
                hidden_test_cases.append({
                    'input': test_input,
                    'expected_output': test_expected
                })
            # Clean up the individual hidden test case fields
            if input_key in challenge:
                del challenge[input_key]
            if expected_key in challenge:
                del challenge[expected_key]
        challenge['hidden_test_cases'] = hidden_test_cases
        
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

def insert_challenge(language, difficulty, data):
    """Insert a new challenge into the correct table based on language and difficulty."""
    table_name = get_table_name(language, difficulty)
    db = DatabaseManager()
    # Map fields to columns
    columns = [
        'title',
        'problem_statement',
        'buggy_code',
        'reference_solution',
        'solution_explanation',
        'hint_1', 'hint_2', 'hint_3',
        'learning_objectives',
        'test_case_1_input', 'test_case_1_expected',
        'test_case_2_input', 'test_case_2_expected',
        'test_case_3_input', 'test_case_3_expected',
        'test_case_4_input', 'test_case_4_expected',
        'test_case_5_input', 'test_case_5_expected',
        'hidden_test_1_input', 'hidden_test_1_expected',
        'hidden_test_2_input', 'hidden_test_2_expected',
        'driver_code'
    ]
    # Prepare values from data
    values = [
        data.get('title'),
        data.get('description'),
        data.get('buggy_code'),
        data.get('reference_solution'),
        data.get('solution_explanation'),
        data['hints'][0] if len(data['hints']) > 0 else None,
        data['hints'][1] if len(data['hints']) > 1 else None,
        data['hints'][2] if len(data['hints']) > 2 else None,
        data.get('learning_objective'),
        # Visible test cases (up to 5)
        data['test_cases'][0]['input'] if len(data['test_cases']) > 0 else None,
        data['test_cases'][0]['expected'] if len(data['test_cases']) > 0 else None,
        data['test_cases'][1]['input'] if len(data['test_cases']) > 1 else None,
        data['test_cases'][1]['expected'] if len(data['test_cases']) > 1 else None,
        data['test_cases'][2]['input'] if len(data['test_cases']) > 2 else None,
        data['test_cases'][2]['expected'] if len(data['test_cases']) > 2 else None,
        data['test_cases'][3]['input'] if len(data['test_cases']) > 3 else None,
        data['test_cases'][3]['expected'] if len(data['test_cases']) > 3 else None,
        data['test_cases'][4]['input'] if len(data['test_cases']) > 4 else None,
        data['test_cases'][4]['expected'] if len(data['test_cases']) > 4 else None,
        # Hidden test cases (always 2)
        data['hidden_test_cases'][0]['input'] if len(data['hidden_test_cases']) > 0 else None,
        data['hidden_test_cases'][0]['expected'] if len(data['hidden_test_cases']) > 0 else None,
        data['hidden_test_cases'][1]['input'] if len(data['hidden_test_cases']) > 1 else None,
        data['hidden_test_cases'][1]['expected'] if len(data['hidden_test_cases']) > 1 else None,
        data.get('driver_code')
    ]
    placeholders = ', '.join(['%s'] * len(columns))
    colnames = ', '.join(columns)
    query = f"""
        INSERT INTO {table_name} ({colnames})
        VALUES ({placeholders})
        RETURNING challenge_id
    """
    return db.execute_query(query, values, fetch_one=True)

def create_xp_trigger():
    """Create trigger for automatic XP and level management"""
    try:
        print("🔧 Creating XP trigger...")
        
        # First check if users table exists
        db = DatabaseManager()
        check_table_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'users'
        );
        """
        table_exists = db.execute_query(check_table_query, fetch_one=True)
        
        if not table_exists or not table_exists['exists']:
            print("❌ Users table does not exist. Please create the users table first.")
            return False
        
        print("✅ Users table exists, proceeding with trigger creation...")
        
        # Create trigger function
        trigger_function = """
        CREATE OR REPLACE FUNCTION handle_xp_and_level()
        RETURNS TRIGGER AS $$
        BEGIN
          -- If XP reaches or exceeds 100, increase level and reset XP
          IF NEW.xp >= 100 THEN
            NEW.level := NEW.level + 1;
            NEW.xp := NEW.xp - 100;  -- Keep remainder XP
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        # Create trigger
        trigger = """
        DROP TRIGGER IF EXISTS xp_level_trigger ON users;
        CREATE TRIGGER xp_level_trigger
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION handle_xp_and_level();
        """
        
        # Execute DDL statements without expecting results
        print("🔧 Creating trigger function...")
        db.execute_query(trigger_function, fetch_all=False)
        print("✅ Trigger function created successfully!")
        
        print("🔧 Creating trigger...")
        db.execute_query(trigger, fetch_all=False)
        print("✅ Trigger created successfully!")
        
        print("✅ XP trigger system created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating XP trigger: {e}")
        print(f"Error type: {type(e).__name__}")
        return False



def is_challenge_completed(username, language, difficulty, challenge_id):
    """Check if a user has already completed a specific challenge"""
    try:
        db = DatabaseManager()
        query = """
        SELECT id FROM user_completed_challenges 
        WHERE user_id = (SELECT user_id FROM users WHERE username = %s)
        AND language = %s AND difficulty = %s AND challenge_id = %s
        """
        result = db.execute_query(query, (username, language, difficulty, challenge_id), fetch_one=True)
        
        is_completed = result is not None
        print(f"🔍 Checking if challenge is completed:")
        print(f"   User: {username}")
        print(f"   Challenge: {language} {difficulty} #{challenge_id}")
        print(f"   Already completed: {is_completed}")
        
        return is_completed
    except Exception as e:
        print(f"❌ Error checking challenge completion: {e}")
        return False

def mark_challenge_completed(username, language, difficulty, challenge_id):
    """Mark a challenge as completed for a user"""
    try:
        db = DatabaseManager()
        query = """
        INSERT INTO user_completed_challenges (user_id, language, difficulty, challenge_id)
        VALUES ((SELECT user_id FROM users WHERE username = %s), %s, %s, %s)
        ON CONFLICT (user_id, language, difficulty, challenge_id) DO NOTHING
        """
        # Don't fetch results for INSERT statements
        db.execute_query(query, (username, language, difficulty, challenge_id), fetch_one=False, fetch_all=False)
        return True
    except Exception as e:
        print(f"❌ Error marking challenge completed: {e}")
        return False

def add_solved_problem_to_user(username, language, difficulty, challenge_id, challenge_title=None, time_taken=None):
    """Add a solved problem to user_completed_challenges table"""
    try:
        db = DatabaseManager()
        
        # First check if the problem is already completed
        already_solved = is_challenge_completed(username, language, difficulty, challenge_id)
        
        if already_solved:
            print(f"⚠️ Problem already solved by {username} - skipping database entry")
            return True
        
        # Add to user_completed_challenges table with time_taken
        query = """
        INSERT INTO user_completed_challenges (user_id, language, difficulty, challenge_id, completed_at, time_taken)
        VALUES ((SELECT user_id FROM users WHERE username = %s), %s, %s, %s, NOW(), %s)
        """
        time_taken_value = time_taken if time_taken is not None else 0
        
        print(f"💾 Storing completion data:")
        print(f"   User: {username}")
        print(f"   Challenge: {language} {difficulty} #{challenge_id}")
        print(f"   Time taken: {time_taken_value}s")
        print(f"   SQL Parameters: {[username, language, difficulty, challenge_id, time_taken_value]}")
        
        try:
            result = db.execute_query(query, (username, language, difficulty, challenge_id, time_taken_value), fetch_all=False)
            print(f"✅ Added solved problem to {username}: {language} {difficulty} challenge {challenge_id} (Time: {time_taken_value}s)")
            return True
        except Exception as insert_error:
            print(f"❌ Database error: {insert_error}")
            raise insert_error
            
    except Exception as e:
        print(f"❌ Error adding solved problem: {e}")
        return False

def get_user_solved_problems(username):
    """Get all solved problems for a user from user_completed_challenges table"""
    try:
        db = DatabaseManager()
        query = """
        SELECT 
            ucc.language,
            ucc.difficulty,
            ucc.challenge_id,
            c.title,
            ucc.completed_at,
            ucc.time_taken
        FROM user_completed_challenges ucc
        LEFT JOIN (
            SELECT 'python' as language, 'basic' as difficulty, challenge_id, title FROM python_basic
            UNION ALL SELECT 'python', 'intermediate', challenge_id, title FROM python_intermediate
            UNION ALL SELECT 'python', 'advanced', challenge_id, title FROM python_advanced
            UNION ALL SELECT 'cpp', 'basic', challenge_id, title FROM cpp_basic
            UNION ALL SELECT 'cpp', 'intermediate', challenge_id, title FROM cpp_intermediate
            UNION ALL SELECT 'cpp', 'advanced', challenge_id, title FROM cpp_advanced
            UNION ALL SELECT 'java', 'basic', challenge_id, title FROM java_basic
            UNION ALL SELECT 'java', 'intermediate', challenge_id, title FROM java_intermediate
            UNION ALL SELECT 'java', 'advanced', challenge_id, title FROM java_advanced
            UNION ALL SELECT 'javascript', 'basic', challenge_id, title FROM javascript_basic
            UNION ALL SELECT 'javascript', 'intermediate', challenge_id, title FROM javascript_intermediate
            UNION ALL SELECT 'javascript', 'advanced', challenge_id, title FROM javascript_advanced
        ) c ON ucc.language = c.language AND ucc.difficulty = c.difficulty AND ucc.challenge_id = c.challenge_id
        WHERE ucc.user_id = (SELECT user_id FROM users WHERE username = %s)
        ORDER BY ucc.completed_at DESC
        """
        results = db.execute_query(query, (username,))
        
        solved_problems = []
        for result in results:
            solved_problems.append({
                'language': result['language'],
                'difficulty': result['difficulty'],
                'challenge_id': result['challenge_id'],
                'title': result['title'],
                'solved_at': result['completed_at'].isoformat() if result['completed_at'] else None,
                'time_taken': result['time_taken'] or 0
            })
        
        return solved_problems
            
    except Exception as e:
        print(f"❌ Error getting solved problems: {e}")
        return []

def get_user_solved_stats(username):
    """Get solved problems statistics for a user"""
    try:
        solved_problems = get_user_solved_problems(username)
        
        # Calculate statistics
        total_solved = len(solved_problems)
        
        # Group by language
        language_stats = {}
        for problem in solved_problems:
            lang = problem['language']
            if lang not in language_stats:
                language_stats[lang] = {'total': 0, 'basic': 0, 'intermediate': 0, 'advanced': 0}
            language_stats[lang]['total'] += 1
            language_stats[lang][problem['difficulty']] += 1
        
        return {
            'total_solved': total_solved,
            'language_stats': language_stats,
            'solved_problems': solved_problems
        }
        
    except Exception as e:
        print(f"❌ Error getting solved stats: {e}")
        return {
            'total_solved': 0,
            'language_stats': {},
            'solved_problems': []
        }

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

def award_xp_to_user(username, xp_amount):
    """Award XP to a user and automatically handle level progression"""
    try:
        query = """
        UPDATE users 
        SET xp = xp + %s 
        WHERE username = %s
        RETURNING user_id, username, xp, level
        """
        db = DatabaseManager()
        result = db.execute_query(query, (xp_amount, username), fetch_one=True)
        
        if result:
            print(f"✅ Awarded {xp_amount} XP to {username}. New XP: {result['xp']}, Level: {result['level']}")
            return result
        else:
            print(f"❌ User {username} not found")
            return None
    except Exception as e:
        print(f"❌ Error awarding XP: {e}")
        return None

def get_user_stats(username):
    """Get user's XP and level"""
    try:
        query = """
        SELECT user_id, username, xp, level 
        FROM users 
        WHERE username = %s
        """
        db = DatabaseManager()
        result = db.execute_query(query, (username,), fetch_one=True)
        return result
    except Exception as e:
        print(f"❌ Error getting user stats: {e}")
        return None

def update_user_score(username, score_to_add):
    """Award XP based on final score"""
    try:
        # XP equals the final score (after all deductions)
        xp_to_award = score_to_add
        
        # Get current user stats before awarding XP
        current_stats = get_user_stats(username)
        old_level = current_stats['level'] if current_stats else 1
        
        # Award XP directly (this will trigger level increase if needed)
        xp_result = award_xp_to_user(username, xp_to_award)
        if xp_result:
            new_level = xp_result['level']
            level_up = new_level > old_level
            
            return {
                'score_added': score_to_add,
                'xp_awarded': xp_to_award,
                'new_xp': xp_result['xp'],
                'new_level': new_level,
                'level_up': level_up
            }
        
        return None
    except Exception as e:
        print(f"❌ Error updating user score: {e}")
        return None

def update_leaderboard_entry(username):
    """Update or create leaderboard entry for a user"""
    try:
        db = DatabaseManager()
        
        # Get user stats
        user_stats = get_user_stats(username)
        if not user_stats:
            return False
            
        # Get solved problems stats
        solved_stats = get_user_solved_stats(username)
        
        # Calculate best language and difficulty
        best_language = None
        best_difficulty = None
        max_solved = 0
        
        for lang, stats in solved_stats['language_stats'].items():
            if stats['total'] > max_solved:
                max_solved = stats['total']
                best_language = lang
                
        # Determine best difficulty
        if solved_stats['language_stats']:
            for lang, stats in solved_stats['language_stats'].items():
                for difficulty in ['advanced', 'intermediate', 'basic']:
                    if stats[difficulty] > 0:
                        best_difficulty = difficulty
                        break
                if best_difficulty:
                    break
        
        # Calculate streak (simplified - can be enhanced later)
        streak_days = 0  # TODO: Implement proper streak calculation
        
        # Insert or update leaderboard entry
        query = """
        INSERT INTO leaderboard (user_id, username, total_score, total_solved, total_xp, level, 
                               best_language, best_difficulty, streak_days, last_activity)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (user_id) DO UPDATE SET
            total_score = EXCLUDED.total_score,
            total_solved = EXCLUDED.total_solved,
            total_xp = EXCLUDED.total_xp,
            level = EXCLUDED.level,
            best_language = EXCLUDED.best_language,
            best_difficulty = EXCLUDED.best_difficulty,
            streak_days = EXCLUDED.streak_days,
            last_activity = NOW(),
            updated_at = NOW()
        """
        
        db.execute_query(query, (
            user_stats['user_id'],
            username,
            user_stats['xp'] or 0,  # Use XP as total score for now
            solved_stats['total_solved'],
            user_stats['xp'] or 0,
            user_stats['level'] or 1,
            best_language,
            best_difficulty,
            streak_days
        ), fetch_all=False)
        
        # Update rank positions
        update_leaderboard_ranks()
        
        print(f"✅ Updated leaderboard entry for {username}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating leaderboard entry: {e}")
        return False

def update_leaderboard_ranks():
    """Update rank positions for all users"""
    try:
        db = DatabaseManager()
        
        # Update rank positions based on total_score
        query = """
        UPDATE leaderboard 
        SET rank_position = subquery.rank
        FROM (
            SELECT id, ROW_NUMBER() OVER (ORDER BY total_score DESC, total_solved DESC, level DESC) as rank
            FROM leaderboard
        ) subquery
        WHERE leaderboard.id = subquery.id
        """
        
        db.execute_query(query, fetch_all=False)
        print("✅ Updated leaderboard ranks")
        
    except Exception as e:
        print(f"❌ Error updating leaderboard ranks: {e}")

def get_leaderboard_data(limit=50, filter_type='overall', filter_value=None):
    """Get leaderboard data including ALL users"""
    try:
        db = DatabaseManager()
        
        # Join users table with leaderboard table (LEFT JOIN to include all users)
        base_query = """
        SELECT 
            COALESCE(lb.rank_position, 999999) as rank_position,
            u.username,
            COALESCE(lb.total_score, 0) as total_score,
            COALESCE(lb.total_solved, 0) as total_solved,
            COALESCE(lb.total_xp, u.xp) as total_xp,
            COALESCE(lb.level, u.level) as level,
            lb.best_language,
            lb.best_difficulty,
            COALESCE(lb.streak_days, 0) as streak_days,
            lb.last_activity
        FROM users u
        LEFT JOIN leaderboard lb ON u.user_id = lb.user_id
        """
        
        where_clause = ""
        params = []
        
        # Apply filters
        if filter_type == 'language' and filter_value:
            where_clause = "WHERE lb.best_language = %s"
            params.append(filter_value)
        elif filter_type == 'difficulty' and filter_value:
            where_clause = "WHERE lb.best_difficulty = %s"
            params.append(filter_value)
        elif filter_type == 'streak':
            where_clause = "WHERE lb.streak_days > 0"
        
        query = base_query + where_clause + " ORDER BY total_score DESC, total_solved DESC, level DESC LIMIT %s"
        params.append(limit)
        
        results = db.execute_query(query, params)
        
        # Add rank positions and medals
        for i, result in enumerate(results):
            result['rank_position'] = i + 1
            if result['rank_position'] == 1:
                result['medal'] = '🥇'
            elif result['rank_position'] == 2:
                result['medal'] = '🥈'
            elif result['rank_position'] == 3:
                result['medal'] = '🥉'
            else:
                result['medal'] = f"#{result['rank_position']}"
        
        return results
        
    except Exception as e:
        print(f"❌ Error getting leaderboard data: {e}")
        return []

def get_user_leaderboard_position(username):
    """Get user's current leaderboard position"""
    try:
        db = DatabaseManager()
        
        # Use LEFT JOIN to include users not in leaderboard yet
        query = """
        SELECT 
            COALESCE(lb.rank_position, 999999) as rank_position,
            COALESCE(lb.total_score, 0) as total_score,
            COALESCE(lb.total_solved, 0) as total_solved,
            COALESCE(lb.level, u.level) as level
        FROM users u
        LEFT JOIN leaderboard lb ON u.user_id = lb.user_id
        WHERE u.username = %s
        """
        
        result = db.execute_query(query, (username,), fetch_one=True)
        return result
        
    except Exception as e:
        print(f"❌ Error getting user leaderboard position: {e}")
        return None

def initialize_user_leaderboard(username):
    """Initialize leaderboard entry for new user"""
    try:
        db = DatabaseManager()
        
        # Get user stats
        user_stats = get_user_stats(username)
        if not user_stats:
            return False
        
        # Create initial leaderboard entry
        query = """
        INSERT INTO leaderboard (user_id, username, total_score, total_solved, total_xp, level, 
                               best_language, best_difficulty, streak_days, last_activity)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (user_id) DO NOTHING
        """
        
        db.execute_query(query, (
            user_stats['user_id'],
            username,
            0,  # Initial score
            0,  # Initial solved count
            user_stats['xp'] or 0,
            user_stats['level'] or 1,
            None,  # No best language yet
            None,  # No best difficulty yet
            0      # No streak yet
        ), fetch_all=False)
        
        print(f"✅ Initialized leaderboard entry for {username}")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing leaderboard: {e}")
        return False

def update_all_users_leaderboard():
    """Update leaderboard entries for ALL users"""
    try:
        db = DatabaseManager()
        
        # Get all users
        users_query = "SELECT user_id, username, xp, level FROM users"
        users = db.execute_query(users_query)
        
        for user in users:
            update_leaderboard_entry(user['username'])
            
        print(f"✅ Updated leaderboard for {len(users)} users")
        
    except Exception as e:
        print(f"❌ Error updating all users: {e}")

if __name__ == "__main__":
    # Test the database connection
    test_connection()
    
    # Show available challenge combinations
    print("\n📚 Available Challenge Categories:")
    for lang, difficulties in CHALLENGE_TABLES.items():
        print(f"  {lang.upper()}: {', '.join(difficulties.keys())}") 