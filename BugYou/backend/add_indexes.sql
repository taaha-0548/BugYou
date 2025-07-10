-- Add indexes for performance optimization

-- Python tables
CREATE INDEX IF NOT EXISTS idx_python_basic_challenge_id ON python_basic(challenge_id);
CREATE INDEX IF NOT EXISTS idx_python_intermediate_challenge_id ON python_intermediate(challenge_id);
CREATE INDEX IF NOT EXISTS idx_python_advanced_challenge_id ON python_advanced(challenge_id);

-- JavaScript tables
CREATE INDEX IF NOT EXISTS idx_javascript_basic_challenge_id ON javascript_basic(challenge_id);
CREATE INDEX IF NOT EXISTS idx_javascript_intermediate_challenge_id ON javascript_intermediate(challenge_id);
CREATE INDEX IF NOT EXISTS idx_javascript_advanced_challenge_id ON javascript_advanced(challenge_id);

-- Java tables
CREATE INDEX IF NOT EXISTS idx_java_basic_challenge_id ON java_basic(challenge_id);
CREATE INDEX IF NOT EXISTS idx_java_intermediate_challenge_id ON java_intermediate(challenge_id);
CREATE INDEX IF NOT EXISTS idx_java_advanced_challenge_id ON java_advanced(challenge_id);

-- C++ tables
CREATE INDEX IF NOT EXISTS idx_cpp_basic_challenge_id ON cpp_basic(challenge_id);
CREATE INDEX IF NOT EXISTS idx_cpp_intermediate_challenge_id ON cpp_intermediate(challenge_id);
CREATE INDEX IF NOT EXISTS idx_cpp_advanced_challenge_id ON cpp_advanced(challenge_id);

-- Add composite indexes for commonly queried fields
CREATE INDEX IF NOT EXISTS idx_python_basic_title_score ON python_basic(title, max_score);
CREATE INDEX IF NOT EXISTS idx_python_intermediate_title_score ON python_intermediate(title, max_score);
CREATE INDEX IF NOT EXISTS idx_python_advanced_title_score ON python_advanced(title, max_score);

CREATE INDEX IF NOT EXISTS idx_javascript_basic_title_score ON javascript_basic(title, max_score);
CREATE INDEX IF NOT EXISTS idx_javascript_intermediate_title_score ON javascript_intermediate(title, max_score);
CREATE INDEX IF NOT EXISTS idx_javascript_advanced_title_score ON javascript_advanced(title, max_score);

CREATE INDEX IF NOT EXISTS idx_java_basic_title_score ON java_basic(title, max_score);
CREATE INDEX IF NOT EXISTS idx_java_intermediate_title_score ON java_intermediate(title, max_score);
CREATE INDEX IF NOT EXISTS idx_java_advanced_title_score ON java_advanced(title, max_score);

CREATE INDEX IF NOT EXISTS idx_cpp_basic_title_score ON cpp_basic(title, max_score);
CREATE INDEX IF NOT EXISTS idx_cpp_intermediate_title_score ON cpp_intermediate(title, max_score);
CREATE INDEX IF NOT EXISTS idx_cpp_advanced_title_score ON cpp_advanced(title, max_score);

-- Add indexes for success rate and attempts for sorting
CREATE INDEX IF NOT EXISTS idx_python_basic_success ON python_basic(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_python_intermediate_success ON python_intermediate(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_python_advanced_success ON python_advanced(success_rate DESC);

CREATE INDEX IF NOT EXISTS idx_javascript_basic_success ON javascript_basic(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_javascript_intermediate_success ON javascript_intermediate(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_javascript_advanced_success ON javascript_advanced(success_rate DESC);

CREATE INDEX IF NOT EXISTS idx_java_basic_success ON java_basic(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_java_intermediate_success ON java_intermediate(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_java_advanced_success ON java_advanced(success_rate DESC);

CREATE INDEX IF NOT EXISTS idx_cpp_basic_success ON cpp_basic(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_cpp_intermediate_success ON cpp_intermediate(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_cpp_advanced_success ON cpp_advanced(success_rate DESC); 