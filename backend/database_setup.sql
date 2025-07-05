-- BugYou Database Setup Script v3.0
-- Output-Based Validation: Multiple Solutions Allowed
-- Focus on test case results, not specific solution implementations

-- Create the database (run this separately as superuser)
-- CREATE DATABASE bugyou;

-- Connect to bugyou database and run the following:

-- Drop existing tables if they exist
DROP TABLE IF EXISTS user_submissions CASCADE;
DROP TABLE IF EXISTS user_progress CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;

-- Drop all challenge tables
DROP TABLE IF EXISTS python_basic CASCADE;
DROP TABLE IF EXISTS python_intermediate CASCADE;
DROP TABLE IF EXISTS python_advanced CASCADE;
DROP TABLE IF EXISTS javascript_basic CASCADE;
DROP TABLE IF EXISTS javascript_intermediate CASCADE;
DROP TABLE IF EXISTS javascript_advanced CASCADE;
DROP TABLE IF EXISTS java_basic CASCADE;
DROP TABLE IF EXISTS java_intermediate CASCADE;
DROP TABLE IF EXISTS java_advanced CASCADE;
DROP TABLE IF EXISTS cpp_basic CASCADE;
DROP TABLE IF EXISTS cpp_intermediate CASCADE;
DROP TABLE IF EXISTS cpp_advanced CASCADE;

DROP TABLE IF EXISTS users CASCADE;

-- Users table
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    total_score INTEGER DEFAULT 0,
    challenges_completed INTEGER DEFAULT 0,
    rank_position INTEGER,
    is_active BOOLEAN DEFAULT true
);

-- ================================
-- PYTHON CHALLENGE TABLES
-- ================================

-- Python Basic Challenges
CREATE TABLE python_basic (
    challenge_id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    problem_statement TEXT NOT NULL,
    buggy_code TEXT NOT NULL,
    
    -- Reference solution (optional - just one possible fix, not the only one!)
    reference_solution TEXT, -- Optional: Shows one way to fix it, but users can solve differently
    solution_explanation TEXT, -- Explains the approach used in reference solution
    
    -- Hints for debugging
    hint_1 TEXT,
    hint_2 TEXT,
    hint_3 TEXT,
    
    -- Educational content
    learning_objectives TEXT,
    common_mistakes TEXT, -- What mistakes students usually make
    tips TEXT,
    
    -- Scoring and timing
    max_score INTEGER DEFAULT 10,
    time_limit_minutes INTEGER DEFAULT 15,
    
    -- Test Cases - THE CORE VALIDATION MECHANISM
    test_case_1_input TEXT NOT NULL,
    test_case_1_expected TEXT NOT NULL,
    test_case_1_description TEXT DEFAULT 'Basic test case',
    test_case_1_weight INTEGER DEFAULT 1, -- Some test cases can be worth more points
    
    test_case_2_input TEXT NOT NULL,
    test_case_2_expected TEXT NOT NULL,
    test_case_2_description TEXT DEFAULT 'Edge case test',
    test_case_2_weight INTEGER DEFAULT 1,
    
    test_case_3_input TEXT NOT NULL,
    test_case_3_expected TEXT NOT NULL,
    test_case_3_description TEXT DEFAULT 'Advanced test case',
    test_case_3_weight INTEGER DEFAULT 1,
    
    -- Additional test cases (optional)
    test_case_4_input TEXT,
    test_case_4_expected TEXT,
    test_case_4_description TEXT,
    test_case_4_weight INTEGER DEFAULT 1,
    
    test_case_5_input TEXT,
    test_case_5_expected TEXT,
    test_case_5_description TEXT,
    test_case_5_weight INTEGER DEFAULT 1,
    
    -- Hidden test cases (for preventing hardcoding)
    hidden_test_1_input TEXT,
    hidden_test_1_expected TEXT,
    hidden_test_1_description TEXT DEFAULT 'Hidden validation test',
    
    hidden_test_2_input TEXT,
    hidden_test_2_expected TEXT,
    hidden_test_2_description TEXT DEFAULT 'Hidden edge case',
    
    -- Output validation settings
    output_comparison_type VARCHAR(20) DEFAULT 'exact', -- 'exact', 'numeric', 'ignore_whitespace'
    tolerance_for_float DECIMAL(10,6) DEFAULT 0.000001, -- For floating point comparisons
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    is_active BOOLEAN DEFAULT true,
    completion_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    avg_attempts DECIMAL(5,2) DEFAULT 0.0
);

-- Python Intermediate Challenges
CREATE TABLE python_intermediate (
    challenge_id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    problem_statement TEXT NOT NULL,
    buggy_code TEXT NOT NULL,
    
    -- Reference solution (one of many possible solutions)
    reference_solution TEXT,
    solution_explanation TEXT,
    alternative_approaches TEXT, -- Describe other ways to solve it
    
    -- More hints for intermediate level
    hint_1 TEXT,
    hint_2 TEXT,
    hint_3 TEXT,
    hint_4 TEXT,
    
    -- Educational content
    learning_objectives TEXT,
    prerequisites TEXT,
    common_mistakes TEXT,
    tips TEXT,
    
    -- Scoring and timing
    max_score INTEGER DEFAULT 15,
    time_limit_minutes INTEGER DEFAULT 25,
    
    -- Test Cases
    test_case_1_input TEXT NOT NULL,
    test_case_1_expected TEXT NOT NULL,
    test_case_1_description TEXT DEFAULT 'Basic functionality',
    test_case_1_weight INTEGER DEFAULT 1,
    
    test_case_2_input TEXT NOT NULL,
    test_case_2_expected TEXT NOT NULL,
    test_case_2_description TEXT DEFAULT 'Edge case handling',
    test_case_2_weight INTEGER DEFAULT 2, -- Worth more points
    
    test_case_3_input TEXT NOT NULL,
    test_case_3_expected TEXT NOT NULL,
    test_case_3_description TEXT DEFAULT 'Complex scenario',
    test_case_3_weight INTEGER DEFAULT 2,
    
    test_case_4_input TEXT,
    test_case_4_expected TEXT,
    test_case_4_description TEXT,
    test_case_4_weight INTEGER DEFAULT 1,
    
    test_case_5_input TEXT,
    test_case_5_expected TEXT,
    test_case_5_description TEXT,
    test_case_5_weight INTEGER DEFAULT 1,
    
    -- Hidden test cases
    hidden_test_1_input TEXT,
    hidden_test_1_expected TEXT,
    hidden_test_1_description TEXT DEFAULT 'Hidden validation test',
    
    hidden_test_2_input TEXT,
    hidden_test_2_expected TEXT,
    hidden_test_2_description TEXT DEFAULT 'Hidden performance test',
    
    hidden_test_3_input TEXT,
    hidden_test_3_expected TEXT,
    hidden_test_3_description TEXT DEFAULT 'Hidden edge case',
    
    -- Output validation settings
    output_comparison_type VARCHAR(20) DEFAULT 'exact',
    tolerance_for_float DECIMAL(10,6) DEFAULT 0.000001,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    is_active BOOLEAN DEFAULT true,
    completion_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    avg_attempts DECIMAL(5,2) DEFAULT 0.0
);

-- Python Advanced Challenges
CREATE TABLE python_advanced (
    challenge_id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    problem_statement TEXT NOT NULL,
    buggy_code TEXT NOT NULL,
    
    -- Reference solution and alternatives
    reference_solution TEXT,
    solution_explanation TEXT,
    alternative_approaches TEXT,
    algorithm_explanation TEXT,
    
    -- More hints for advanced level
    hint_1 TEXT,
    hint_2 TEXT,
    hint_3 TEXT,
    hint_4 TEXT,
    hint_5 TEXT,
    
    -- Educational content
    learning_objectives TEXT,
    prerequisites TEXT,
    common_mistakes TEXT,
    tips TEXT,
    
    -- Scoring and timing
    max_score INTEGER DEFAULT 20,
    time_limit_minutes INTEGER DEFAULT 35,
    
    -- Test Cases (more comprehensive for advanced)
    test_case_1_input TEXT NOT NULL,
    test_case_1_expected TEXT NOT NULL,
    test_case_1_description TEXT DEFAULT 'Basic functionality',
    test_case_1_weight INTEGER DEFAULT 1,
    
    test_case_2_input TEXT NOT NULL,
    test_case_2_expected TEXT NOT NULL,
    test_case_2_description TEXT DEFAULT 'Edge case handling',
    test_case_2_weight INTEGER DEFAULT 2,
    
    test_case_3_input TEXT NOT NULL,
    test_case_3_expected TEXT NOT NULL,
    test_case_3_description TEXT DEFAULT 'Complex scenario',
    test_case_3_weight INTEGER DEFAULT 3,
    
    test_case_4_input TEXT NOT NULL,
    test_case_4_expected TEXT NOT NULL,
    test_case_4_description TEXT DEFAULT 'Performance test',
    test_case_4_weight INTEGER DEFAULT 3,
    
    test_case_5_input TEXT NOT NULL,
    test_case_5_expected TEXT NOT NULL,
    test_case_5_description TEXT DEFAULT 'Stress test',
    test_case_5_weight INTEGER DEFAULT 3,
    
    -- More hidden test cases for advanced
    hidden_test_1_input TEXT,
    hidden_test_1_expected TEXT,
    hidden_test_1_description TEXT DEFAULT 'Hidden validation test',
    
    hidden_test_2_input TEXT,
    hidden_test_2_expected TEXT,
    hidden_test_2_description TEXT DEFAULT 'Hidden performance test',
    
    hidden_test_3_input TEXT,
    hidden_test_3_expected TEXT,
    hidden_test_3_description TEXT DEFAULT 'Hidden edge case',
    
    hidden_test_4_input TEXT,
    hidden_test_4_expected TEXT,
    hidden_test_4_description TEXT DEFAULT 'Hidden stress test',
    
    -- Output validation settings
    output_comparison_type VARCHAR(20) DEFAULT 'exact',
    tolerance_for_float DECIMAL(10,6) DEFAULT 0.000001,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    is_active BOOLEAN DEFAULT true,
    completion_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    avg_attempts DECIMAL(5,2) DEFAULT 0.0
);

-- ================================
-- JAVASCRIPT CHALLENGE TABLES
-- ================================

-- JavaScript Basic Challenges (similar structure to Python)
CREATE TABLE javascript_basic (
    challenge_id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    problem_statement TEXT NOT NULL,
    buggy_code TEXT NOT NULL,
    
    reference_solution TEXT,
    solution_explanation TEXT,
    
    hint_1 TEXT,
    hint_2 TEXT,
    hint_3 TEXT,
    
    learning_objectives TEXT,
    common_mistakes TEXT,
    tips TEXT,
    
    max_score INTEGER DEFAULT 10,
    time_limit_minutes INTEGER DEFAULT 15,
    
    -- Test Cases
    test_case_1_input TEXT NOT NULL,
    test_case_1_expected TEXT NOT NULL,
    test_case_1_description TEXT DEFAULT 'Basic test case',
    test_case_1_weight INTEGER DEFAULT 1,
    
    test_case_2_input TEXT NOT NULL,
    test_case_2_expected TEXT NOT NULL,
    test_case_2_description TEXT DEFAULT 'Edge case test',
    test_case_2_weight INTEGER DEFAULT 1,
    
    test_case_3_input TEXT NOT NULL,
    test_case_3_expected TEXT NOT NULL,
    test_case_3_description TEXT DEFAULT 'Advanced test case',
    test_case_3_weight INTEGER DEFAULT 1,
    
    test_case_4_input TEXT,
    test_case_4_expected TEXT,
    test_case_4_description TEXT,
    test_case_4_weight INTEGER DEFAULT 1,
    
    test_case_5_input TEXT,
    test_case_5_expected TEXT,
    test_case_5_description TEXT,
    test_case_5_weight INTEGER DEFAULT 1,
    
    -- Hidden test cases
    hidden_test_1_input TEXT,
    hidden_test_1_expected TEXT,
    hidden_test_1_description TEXT DEFAULT 'Hidden validation test',
    
    hidden_test_2_input TEXT,
    hidden_test_2_expected TEXT,
    hidden_test_2_description TEXT DEFAULT 'Hidden edge case',
    
    -- Output validation settings
    output_comparison_type VARCHAR(20) DEFAULT 'exact',
    tolerance_for_float DECIMAL(10,6) DEFAULT 0.000001,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES users(user_id),
    is_active BOOLEAN DEFAULT true,
    completion_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    avg_attempts DECIMAL(5,2) DEFAULT 0.0
);

-- For brevity, other language tables follow the same pattern
-- JavaScript Intermediate & Advanced
CREATE TABLE javascript_intermediate (LIKE javascript_basic INCLUDING ALL);
ALTER TABLE javascript_intermediate ADD COLUMN hint_4 TEXT;
ALTER TABLE javascript_intermediate ADD COLUMN prerequisites TEXT;
ALTER TABLE javascript_intermediate ADD COLUMN alternative_approaches TEXT;
ALTER TABLE javascript_intermediate ADD COLUMN hidden_test_3_input TEXT;
ALTER TABLE javascript_intermediate ADD COLUMN hidden_test_3_expected TEXT;
ALTER TABLE javascript_intermediate ADD COLUMN hidden_test_3_description TEXT;
ALTER TABLE javascript_intermediate ALTER COLUMN max_score SET DEFAULT 15;
ALTER TABLE javascript_intermediate ALTER COLUMN time_limit_minutes SET DEFAULT 25;

CREATE TABLE javascript_advanced (LIKE javascript_basic INCLUDING ALL);
ALTER TABLE javascript_advanced ADD COLUMN hint_4 TEXT;
ALTER TABLE javascript_advanced ADD COLUMN hint_5 TEXT;
ALTER TABLE javascript_advanced ADD COLUMN prerequisites TEXT;
ALTER TABLE javascript_advanced ADD COLUMN alternative_approaches TEXT;
ALTER TABLE javascript_advanced ADD COLUMN algorithm_explanation TEXT;
ALTER TABLE javascript_advanced ADD COLUMN hidden_test_3_input TEXT;
ALTER TABLE javascript_advanced ADD COLUMN hidden_test_3_expected TEXT;
ALTER TABLE javascript_advanced ADD COLUMN hidden_test_3_description TEXT;
ALTER TABLE javascript_advanced ADD COLUMN hidden_test_4_input TEXT;
ALTER TABLE javascript_advanced ADD COLUMN hidden_test_4_expected TEXT;
ALTER TABLE javascript_advanced ADD COLUMN hidden_test_4_description TEXT;
ALTER TABLE javascript_advanced ALTER COLUMN max_score SET DEFAULT 20;
ALTER TABLE javascript_advanced ALTER COLUMN time_limit_minutes SET DEFAULT 35;

-- Java tables (similar pattern)
CREATE TABLE java_basic (LIKE javascript_basic INCLUDING ALL);
ALTER TABLE java_basic ALTER COLUMN time_limit_minutes SET DEFAULT 20;

CREATE TABLE java_intermediate (LIKE javascript_intermediate INCLUDING ALL);
ALTER TABLE java_intermediate ALTER COLUMN time_limit_minutes SET DEFAULT 30;

CREATE TABLE java_advanced (LIKE javascript_advanced INCLUDING ALL);
ALTER TABLE java_advanced ALTER COLUMN time_limit_minutes SET DEFAULT 40;

-- C++ tables (similar pattern, longer time limits)
CREATE TABLE cpp_basic (LIKE javascript_basic INCLUDING ALL);
ALTER TABLE cpp_basic ALTER COLUMN max_score SET DEFAULT 12;
ALTER TABLE cpp_basic ALTER COLUMN time_limit_minutes SET DEFAULT 25;

CREATE TABLE cpp_intermediate (LIKE javascript_intermediate INCLUDING ALL);
ALTER TABLE cpp_intermediate ALTER COLUMN max_score SET DEFAULT 18;
ALTER TABLE cpp_intermediate ALTER COLUMN time_limit_minutes SET DEFAULT 35;

CREATE TABLE cpp_advanced (LIKE javascript_advanced INCLUDING ALL);
ALTER TABLE cpp_advanced ALTER COLUMN max_score SET DEFAULT 25;
ALTER TABLE cpp_advanced ALTER COLUMN time_limit_minutes SET DEFAULT 45;

-- ================================
-- USER TRACKING TABLES
-- ================================

-- User sessions table
CREATE TABLE user_sessions (
    session_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    challenge_table VARCHAR(50) NOT NULL,
    challenge_id INTEGER NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    current_code TEXT,
    hints_used INTEGER DEFAULT 0,
    attempts_made INTEGER DEFAULT 0,
    time_elapsed_seconds INTEGER DEFAULT 0,
    is_completed BOOLEAN DEFAULT false,
    
    -- Track which test cases were passed
    visible_tests_passed INTEGER DEFAULT 0,
    visible_tests_total INTEGER DEFAULT 0,
    hidden_tests_passed INTEGER DEFAULT 0,
    hidden_tests_total INTEGER DEFAULT 0
);

-- User submissions table
CREATE TABLE user_submissions (
    submission_id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    challenge_table VARCHAR(50) NOT NULL,
    challenge_id INTEGER NOT NULL,
    submitted_code TEXT NOT NULL,
    submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Test results (the core of validation)
    visible_tests_passed INTEGER DEFAULT 0,
    visible_tests_total INTEGER DEFAULT 0,
    hidden_tests_passed INTEGER DEFAULT 0,
    hidden_tests_total INTEGER DEFAULT 0,
    total_tests_passed INTEGER DEFAULT 0,
    total_tests_count INTEGER DEFAULT 0,
    
    -- Scoring based on test results
    score_achieved INTEGER DEFAULT 0,
    weighted_score DECIMAL(5,2) DEFAULT 0.0, -- Considers test case weights
    
    -- Performance metrics
    execution_time_ms INTEGER,
    hints_used INTEGER DEFAULT 0,
    attempts_made INTEGER DEFAULT 1,
    is_successful BOOLEAN DEFAULT false, -- All tests passed
    
    -- Validation details (JSON format for detailed test results)
    test_results_json TEXT -- Store detailed results for each test case
);

-- User progress table
CREATE TABLE user_progress (
    progress_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    challenge_table VARCHAR(50) NOT NULL,
    challenge_id INTEGER NOT NULL,
    best_score INTEGER DEFAULT 0,
    best_weighted_score DECIMAL(5,2) DEFAULT 0.0,
    best_time_seconds INTEGER,
    completion_date TIMESTAMP,
    attempts_count INTEGER DEFAULT 0,
    hints_used_total INTEGER DEFAULT 0,
    is_completed BOOLEAN DEFAULT false,
    
    -- Track the best test results achieved
    best_visible_tests_passed INTEGER DEFAULT 0,
    best_hidden_tests_passed INTEGER DEFAULT 0,
    total_tests_count INTEGER DEFAULT 0,
    
    UNIQUE(user_id, challenge_table, challenge_id)
);

-- ================================
-- INDEXES FOR PERFORMANCE
-- ================================

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_total_score ON users(total_score DESC);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_challenge ON user_sessions(challenge_table, challenge_id);
CREATE INDEX idx_user_submissions_user_id ON user_submissions(user_id);
CREATE INDEX idx_user_submissions_challenge ON user_submissions(challenge_table, challenge_id);
CREATE INDEX idx_user_progress_user_id ON user_progress(user_id);

-- ================================
-- SAMPLE DATA WITH OUTPUT VALIDATION FOCUS
-- ================================

-- Insert sample admin user
INSERT INTO users (username, email, password_hash, display_name, total_score) VALUES
('admin', 'admin@bugyou.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewbBQM/LLt.zp.Sq', 'Admin User', 0);

-- Python Basic Challenge: Multiple solutions possible!
INSERT INTO python_basic (
    title, description, problem_statement, buggy_code, 
    reference_solution, solution_explanation,
    hint_1, hint_2, hint_3, 
    learning_objectives, common_mistakes, tips,
    test_case_1_input, test_case_1_expected, test_case_1_description, test_case_1_weight,
    test_case_2_input, test_case_2_expected, test_case_2_description, test_case_2_weight,
    test_case_3_input, test_case_3_expected, test_case_3_description, test_case_3_weight,
    hidden_test_1_input, hidden_test_1_expected,
    hidden_test_2_input, hidden_test_2_expected
) VALUES (
    'Fix the Average Calculator',
    'A function to calculate averages has a division by zero bug. Multiple solutions are valid!',
    'Fix the buggy calculate_average function that crashes when given an empty list. Any approach that handles empty lists properly is acceptable.',
    'def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    # Bug: Division by zero when list is empty!
    return total / len(numbers)

# Test the function
print("Function ready for testing")',
    'def calculate_average(numbers):
    if len(numbers) == 0:
        return 0  # One possible approach
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)',
    'This is just ONE way to fix it. You could also return None, raise an exception, or use other approaches as long as the test cases pass.',
    'What happens when you divide by zero? Check if the list is empty first!',
    'You could return 0, return None, or handle it differently - just make sure your output matches the expected results.',
    'There are multiple valid ways to fix this. Choose the approach that makes sense to you.',
    'Learn about edge case handling and multiple solution approaches. Understand that programming problems often have many valid solutions.',
    'Students often think there''s only one "correct" way to fix a bug. In reality, multiple approaches can work.',
    'Test your solution with the given test cases. As long as your output matches the expected output, your solution is valid!',
    '[1, 2, 3, 4, 5]', '3.0', 'Standard case with multiple numbers', 1,
    '[10, 20]', '15.0', 'Simple case with two numbers', 1,
    '[]', '0', 'Edge case: empty list should return 0', 2,
    '[0, 0, 0]', '0.0', -- Hidden test: all zeros
    '[-1, 1]', '0.0' -- Hidden test: positive and negative
);

-- JavaScript Basic Challenge: Multiple solutions approach
INSERT INTO javascript_basic (
    title, description, problem_statement, buggy_code,
    reference_solution, solution_explanation,
    hint_1, hint_2, hint_3,
    learning_objectives, common_mistakes, tips,
    test_case_1_input, test_case_1_expected, test_case_1_description, test_case_1_weight,
    test_case_2_input, test_case_2_expected, test_case_2_description, test_case_2_weight,
    test_case_3_input, test_case_3_expected, test_case_3_description, test_case_3_weight,
    hidden_test_1_input, hidden_test_1_expected,
    hidden_test_2_input, hidden_test_2_expected
) VALUES (
    'Fix the Max Finder',
    'A function to find maximum values fails with negative numbers. Fix it your way!',
    'Fix the findMax function that won''t work correctly for arrays containing only negative numbers. Any solution that passes the test cases is valid.',
    'function findMax(arr) {
    let max = 0; // Bug: Won''t work for negative arrays!
    for (let i = 0; i < arr.length; i++) {
        if (arr[i] > max) {
            max = arr[i];
        }
    }
    return max;
}

console.log("Function ready for testing");',
    'function findMax(arr) {
    if (arr.length === 0) return undefined;
    let max = arr[0];  // Initialize with first element
    for (let i = 1; i < arr.length; i++) {
        if (arr[i] > max) {
            max = arr[i];
        }
    }
    return max;
}',
    'This is one approach. You could also use Math.max(...arr), a reduce function, or other methods.',
    'Starting with max = 0 won''t work for arrays with only negative numbers!',
    'Try initializing max with the first element of the array, or use built-in JavaScript methods.',
    'Handle empty arrays appropriately - they should return undefined.',
    'Learn about proper variable initialization and different approaches to finding maximum values.',
    'Assuming 0 is a good initial value. This fails when all numbers are negative.',
    'Multiple solutions exist: Math.max, reduce, traditional loops, etc. Pick what feels natural to you!',
    '[3, 7, 2, 9, 1]', '9', 'Standard case with positive numbers', 1,
    '[-5, -2, -8, -1]', '-1', 'Edge case: all negative numbers', 2,
    '[]', 'undefined', 'Edge case: empty array', 1,
    '[0]', '0', -- Hidden test: single zero
    '[-10, -20, -5]', '-5' -- Hidden test: all negative
);

-- ================================
-- VIEWS FOR REPORTING
-- ================================

-- Enhanced leaderboard view
CREATE VIEW leaderboard AS
SELECT 
    u.username,
    u.display_name,
    u.total_score,
    u.challenges_completed,
    RANK() OVER (ORDER BY u.total_score DESC, u.challenges_completed DESC) as rank_position
FROM users u
WHERE u.is_active = true
ORDER BY u.total_score DESC, u.challenges_completed DESC;

-- Challenge success statistics
CREATE VIEW challenge_success_stats AS
SELECT 
    'python_basic' as challenge_table,
    challenge_id,
    title,
    completion_count,
    success_rate,
    avg_attempts,
    max_score
FROM python_basic WHERE is_active = true
UNION ALL
SELECT 
    'javascript_basic' as challenge_table,
    challenge_id,
    title,
    completion_count,
    success_rate,
    avg_attempts,
    max_score
FROM javascript_basic WHERE is_active = true;

-- User progress summary
CREATE VIEW user_progress_summary AS
SELECT 
    u.user_id,
    u.username,
    u.total_score,
    COUNT(up.progress_id) as total_attempts,
    COUNT(CASE WHEN up.is_completed THEN 1 END) as completed_challenges,
    ROUND(AVG(up.best_weighted_score), 2) as avg_weighted_score,
    SUM(up.hints_used_total) as total_hints_used
FROM users u
LEFT JOIN user_progress up ON u.user_id = up.user_id
GROUP BY u.user_id, u.username, u.total_score;

-- Display setup completion message
SELECT 'BugYou database v3.0 setup completed successfully!' as status,
       'Output-based validation: Multiple solutions allowed!' as approach,
       'Focus on test case results, not specific implementations' as philosophy; 