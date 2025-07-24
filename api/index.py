"""
BugYou Flask Backend API
Integrates database with frontend for complete debugging challenge platform
"""

from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
import requests
from datetime import datetime
import os
import re
import time
import json
from functools import wraps
import hashlib
from string import Template
# from concurrent.futures import ThreadPoolExecutor  # Removed - using sequential execution to avoid rate limiting
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, Email
# Import our database functions
from database_config import (
    get_challenges_by_language_difficulty, 
    get_challenge_by_id,
    get_user_by_username,
    create_user,
    test_connection,
    CHALLENGE_TABLES,
    insert_challenge,
    get_user_stats,
    update_user_score,
    DatabaseManager,
    is_challenge_completed,
    mark_challenge_completed,
    add_solved_problem_to_user,
    get_user_solved_stats,
    get_leaderboard_data,
    get_user_leaderboard_position,
    update_leaderboard_entry,
    update_leaderboard_ranks
)

# --- Additions from app.py for backend optimizations ---
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Filename sanitization utility
# Initialize Flask app with multiple static folders
app = Flask(__name__)
app.static_folder = '../frontend/main_page'  # Primary static folder
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Enable CORS for API endpoints

# Additional static folders
STATIC_FOLDERS = {
     'main': '../frontend/main_page',
    'login': '../frontend/login',
    'signup': '../frontend/signup',
    'admin': '../frontend/admin',
    'assets': '../Assets',
    'home': '../frontend/home',         # <-- Add this line
    'guide': '../frontend/guide',       # <-- (Optional, for guide.css)
    'about': '../frontend/about',       # <-- (Optional, for about.css)
    'user_profile': '../frontend/user_profile',  # <-- Add user profile folder
    'leaderboard': '../frontend/leaderboard',  # <-- Add leaderboard folder
}

# --- Standard headers/imports for each language ---
STANDARD_HEADERS = {
    'cpp': '#include <bits/stdc++.h>\nusing namespace std;\n',
    'python': 'import sys\nimport math\nimport collections\nfrom collections import defaultdict, deque, Counter\nimport heapq\nimport bisect\nimport itertools\nimport functools\nfrom functools import lru_cache\nimport re\nimport string\n',
    'java': 'import java.util.*;\nimport java.io.*;\nimport java.lang.*;\n',
    'javascript': '// No special headers needed\n'
}

# --- Build executable code for the runner ---
def build_executable_code(user_code, language, driver_code):
    headers = STANDARD_HEADERS.get(language, '')
    if language == 'java':
        # Wrap both user_code and driver_code inside Solution class
        return f"{headers}\npublic class Solution {{\n{user_code}\n{driver_code}\n}}"
    else:
        return f"{headers}\n{user_code}\n{driver_code}"

def sanitize_filename(name: str) -> str:
    base, ext = os.path.splitext(name)
    return f"{base}.{ext.lstrip('.')}" if ext else name

# Session with retries for outbound requests
_session = requests.Session()
_retries = Retry(
    total=2,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["POST"]
)
_session.mount("https://", HTTPAdapter(max_retries=_retries))

# Multi-level caching
_cache = {}
_cache_timeout = 300  # 5 minutes
_execution_cache = {}
_execution_cache_timeout = 300  # 5 minutes
_batch_cache = {}
_batch_cache_timeout = 600  # 10 minutes

def cache_result(timeout=300):
    """Decorator to cache API results"""
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f.__name__ + str(args) + str(sorted(kwargs.items()))
            current_time = time.time()
            # Check if cached result exists and is still valid
            if cache_key in _cache:
                cached_time, cached_result = _cache[cache_key]
                if current_time - cached_time < timeout:
                    return cached_result
            # Execute function and cache result
            result = f(*args, **kwargs)
            _cache[cache_key] = (current_time, result)
            return result
        return decorated_function
    return decorator

# Cache clearing endpoint
@app.route('/api/cache/clear')
def clear_cache():
    global _cache, _execution_cache, _batch_cache
    _cache = {}
    _execution_cache = {}
    _batch_cache = {}
    return jsonify({
        'success': True,
        'message': 'All caches cleared successfully (API, execution, batch)',
        'timestamp': datetime.now().isoformat()
    })

# Example: Add cache_result to ts (do not remove existing decorators)
try:
    app.view_functions['get_challenges'] = cache_result(timeout=60)(app.view_functions['get_challenges'])
except Exception:
    pass
try:
    app.view_functions['get_challenges_by_lang_diff'] = cache_result(timeout=60)(app.view_functions['get_challenges_by_lang_diff'])
except Exception:
    pass
try:
    app.view_functions['get_first_challenge'] = cache_result(timeout=60)(app.view_functions['get_first_challenge'])
except Exception:
    pass

# --- Early syntax validation for Python/JS in code execution endpoint ---
# (Add this logic at the start of your execute_code endpoint, before sending to Piston API)
# Example:
# if language == 'python':
#     import ast
#     try:
#         ast.parse(code)
#     except Exception as e:
#         return jsonify({'success': False, 'error': f'Python syntax error: {e}'}), 400
# elif language == 'javascript':
#     if 'function ' not in code:
#         return jsonify({'success': False, 'error': 'JavaScript code must define at least one function.'}), 400

# --- Defensive programming for missing parameters and error handling ---
# (Add checks for required parameters in endpoints, e.g. if not code or not language: ...)
# --- Add response timing where relevant (e.g. start_time = time.time(); response_time = time.time() - start_time) ---


# Configuration
PISTON_API = 'https://emkc.org/api/v2/piston'

# Simple in-memory cache for frequently accessed data
# _cache = {}
# _cache_timeout = 300  # 5 minutes

# Enhanced cache for code execution results
# _execution_cache = {}
# _execution_cache_timeout = 300  # 5 minutes (increased for better performance)

# Advanced cache for batch execution results
# _batch_cache = {}
# _batch_cache_timeout = 600  # 10 minutes

# Language configuration for Piston API
PISTON_LANGUAGES = {
    'python': {
        'lang': 'python',
        'version': '3.10.0',
        'filename': 'main.py',
    },
    'javascript': {
        'lang': 'javascript',
        'version': '18.15.0',
        'filename': 'main.js',
    },
    'java': {
        'lang': 'java',
        'version': '15.0.2',
        'filename': 'Solution.java',  # <-- Change to Solution.java
    },
    'cpp': {
        'lang': 'cpp',
        'version': '10.2.0',
        'filename': 'main.cpp',
    },
}

def get_cache_key(user_code, language, driver_code):
    key_str = f"{user_code}::{language}::{driver_code}"
    return hashlib.md5(key_str.encode()).hexdigest()

def get_cached_execution(user_code, language, driver_code):
    cache_key = get_cache_key(user_code, language, driver_code)
    if cache_key in _execution_cache:
        result, timestamp = _execution_cache[cache_key]
        if time.time() - timestamp < _execution_cache_timeout:
            return result
        del _execution_cache[cache_key]
    return None

def set_cached_execution(user_code, language, driver_code, result):
    cache_key = get_cache_key(user_code, language, driver_code)
    _execution_cache[cache_key] = (result, time.time())
    # Clean old cache entries
    current_time = time.time()
    expired_keys = [
        k for k, (_, t) in _execution_cache.items()
        if current_time - t > _execution_cache_timeout
    ]
    for k in expired_keys:
        del _execution_cache[k]

def get_batch_cache_key(code, language, test_cases, func_name=None):
    """Generate a specialized cache key for batch execution"""
    import hashlib
    # Use function signature for better cache hits across similar code
    code_hash = hashlib.md5(code.encode()).hexdigest()
    test_cases_str = json.dumps(test_cases, sort_keys=True)
    test_cases_hash = hashlib.md5(test_cases_str.encode()).hexdigest()
    return f"batch:{language}:{code_hash}:{test_cases_hash}"

def get_cached_batch_execution(code, language, test_cases, func_name=None):
    """Get cached batch execution result if available"""
    cache_key = get_batch_cache_key(code, language, test_cases, func_name)
    if cache_key in _batch_cache:
        result, timestamp = _batch_cache[cache_key]
        if time.time() - timestamp < _batch_cache_timeout:
            print(f"✅ Cache hit for batch execution: {cache_key[:30]}...")
            return result
        del _batch_cache[cache_key]
    return None

def set_cached_batch_execution(code, language, test_cases, result, func_name=None):
    """Cache batch execution result"""
    cache_key = get_batch_cache_key(code, language, test_cases, func_name)
    _batch_cache[cache_key] = (result, time.time())
    
    print(f"💾 Cached batch execution: {cache_key[:30]}...")
    
    # Clean old cache entries
    current_time = time.time()
    expired_keys = [
        k for k, (_, t) in _batch_cache.items() 
        if current_time - t > _batch_cache_timeout
    ]
    for k in expired_keys:
        del _batch_cache[k]

# For Java, user_code must be ONLY the method(s), no class, no closing brace. The backend will wrap it.
def run_all_tests_in_batch(user_code, language, driver_code, test_cases):
    """
    Dynamically generate driver code for all test cases using the driver_code as an initialization/call snippet.
    For each test case, replace TEST_INPUT in driver_code with the test case input, call the function, and print the result.
    Combine all into a main (or equivalent) function for batch execution.
    """
    # Determine the function call/print pattern based on language
    if language == 'cpp':
        driver_lines = ["int main() {"]
        for test_case in test_cases:
            test_input = test_case.get('input')
            snippet = driver_code.replace('TEST_INPUT', str(test_input))
            driver_lines.append(f"    {snippet}")
        driver_lines.append("    return 0;")
        driver_lines.append("}")
        generated_driver_code = '\n'.join(driver_lines)
    elif language == 'python':
        driver_lines = ["import ast", "if __name__ == '__main__':"]
        for test_case in test_cases:
            test_input = test_case.get('input')
            # If input is a string, use ast.literal_eval; otherwise, use as is
            if isinstance(test_input, str):
                snippet = driver_code.replace('TEST_INPUT', f"ast.literal_eval({repr(test_input)})")
            else:
                snippet = driver_code.replace('TEST_INPUT', repr(test_input))
            driver_lines.append(f"    print({snippet})")
        generated_driver_code = '\n'.join(driver_lines)
    elif language == 'java':
        # Use the global java_input_literal for input conversion
        driver_lines = ["    public static void main(String[] args) {"]
        for test_case in test_cases:
            test_input = test_case.get('input')
            java_input = java_input_literal(test_input)
            snippet = driver_code.replace('TEST_INPUT', java_input)
            driver_lines.append(f"        {snippet}")
        driver_lines.append("    }")
        generated_driver_code = '\n'.join(driver_lines)
        # Always wrap user_code and main in Solution
        full_code = (
            f"{STANDARD_HEADERS['java']}\n"
            f"public class Solution {{\n"
            f"{user_code}\n"
            f"{generated_driver_code}\n"
            f"}}"
        )
    elif language == 'javascript':
        # Build a single test harness that iterates over all test cases
        driver_lines = ["const testCases = ["]
        for test_case in test_cases:
            test_input = test_case.get('input')
            driver_lines.append(f"  {js_input_literal(test_input)},")
        driver_lines.append("];")
        driver_lines.append("for (const tc of testCases) {")
        driver_lines.append(f"  {driver_code}")
        driver_lines.append("}")
        generated_driver_code = '\n'.join(driver_lines)
    else:
        return {
            'success': False,
            'error': f'Unsupported language: {language}',
            'test_results': []
        }
    full_code = build_executable_code(user_code, language, generated_driver_code)
    print("[DEBUG] Generated code to send to Piston:")
    print(full_code)
    lang_config = PISTON_LANGUAGES.get(language)
    if not lang_config:
        return {
            'success': False,
            'error': f'Unsupported language: {language}',
            'test_results': []
        }
    data = {
        'language': lang_config['lang'],
        'version': lang_config['version'],
        'files': [{
            'name': lang_config['filename'],
            'content': full_code
        }]
    }
 
    try:
        response = requests.post(f"{PISTON_API}/execute", json=data, timeout=20)
        if response.status_code != 200:
            return {'success': False, 'error': f'API Error: {response.status_code}', 'test_results': []}
        result = response.json()
        if result.get('compile', {}).get('stderr'):
            return {'success': False, 'error': result['compile']['stderr'], 'test_results': []}
        if result.get('run', {}).get('stderr'):
            return {'success': False, 'error': result['run']['stderr'], 'test_results': []}
        output = result.get('run', {}).get('stdout', '').strip()
        output_lines = output.split('\n') if output else []
        test_results = []
        for i, test_case in enumerate(test_cases):
            expected = test_case.get('expected_output') or test_case.get('expected', '')
            actual = output_lines[i].strip() if i < len(output_lines) else None
            passed = (str(actual).strip() == str(expected).strip())
            test_results.append({'test_number': i+1, 'passed': passed, 'actual': actual, 'expected': expected})
        return {'success': True, 'test_results': test_results}
    except Exception as e:
        return {'success': False, 'error': str(e), 'test_results': []}

# ================================
# SERVE FRONTEND
# ================================

@app.route('/')
def serve_frontend():
    """Serve the home page"""
    return send_from_directory('../frontend/home', 'home.html')

@app.route('/main_page')
def serve_main_page():
    """Serve the main code editor page"""
    return send_from_directory(STATIC_FOLDERS['main'], 'index.html')

@app.route('/login')
def serve_login():
    """Serve the login page"""
    return send_from_directory(STATIC_FOLDERS['login'], 'login.html')

@app.route('/signup')
def serve_signup():
    """Serve the signup page"""
    return send_from_directory(STATIC_FOLDERS['signup'], 'signup.html')

@app.route('/guide')
def serve_guide():
    """Serve the guide page"""
    return send_from_directory('../frontend/guide', 'guide.html')

@app.route('/admin')
def serve_admin():
    """Serve the admin page"""
    return send_from_directory(STATIC_FOLDERS['admin'], 'admin.html')

@app.route('/about')
def serve_about():
    """Serve the about page"""
    return send_from_directory(STATIC_FOLDERS['about'], 'about.html')

@app.route('/user_profile')
def serve_user_profile():
    """Serve the user profile page"""
    return send_from_directory('../frontend/user_profile', 'user.html')

@app.route('/leaderboard')
def serve_leaderboard():
    """Serve the leaderboard page"""
    return send_from_directory('../frontend/leaderboard', 'leaderboard.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve files from Assets directory"""
    try:
        return send_from_directory(STATIC_FOLDERS['assets'], filename)
    except Exception as e:
        print(f"Error serving asset {filename}: {str(e)}")
        return f"Asset {filename} not found", 404

@app.route('/<path:filename>')
def serve_static(filename):
    # Special handling for /home/home.css, /guide/guide.css, /about/about.css, /user_profile/user.css
    if filename.startswith('home/'):
        subfile = filename[len('home/'):]
        folder = STATIC_FOLDERS['home']
        if os.path.exists(os.path.join(folder, subfile)):
            return send_from_directory(folder, subfile)
    if filename.startswith('guide/'):
        subfile = filename[len('guide/'):]
        folder = STATIC_FOLDERS['guide']
        if os.path.exists(os.path.join(folder, subfile)):
            return send_from_directory(folder, subfile)
    if filename.startswith('about/'):
        subfile = filename[len('about/'):]
        folder = STATIC_FOLDERS['about']
        if os.path.exists(os.path.join(folder, subfile)):
            return send_from_directory(folder, subfile)
    if filename.startswith('user_profile/'):
        subfile = filename[len('user_profile/'):]
        folder = STATIC_FOLDERS['user_profile']
        if os.path.exists(os.path.join(folder, subfile)):
            return send_from_directory(folder, subfile)
    if filename.startswith('leaderboard/'):
        subfile = filename[len('leaderboard/'):]
        folder = STATIC_FOLDERS['leaderboard']
        if os.path.exists(os.path.join(folder, subfile)):
            return send_from_directory(folder, subfile)
    # Existing logic for login, signup, admin
    current_page = request.path.split('/')[1] if '/' in request.path else ''
    if current_page in ['login', 'signup', 'admin']:
        folder = STATIC_FOLDERS[current_page]
        if os.path.exists(os.path.join(folder, filename)):
            return send_from_directory(folder, filename)
    # Fallback: try all folders
    for folder_name, folder_path in STATIC_FOLDERS.items():
        if os.path.exists(os.path.join(folder_path, filename)):
            return send_from_directory(folder_path, filename)
    return f"File {filename} not found", 404

# ================================

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    start_time = time.time()
    db_status = test_connection()
    response_time = time.time() - start_time
    
    return jsonify({
        'status': 'healthy',
        'database': 'connected' if db_status else 'disconnected',
        'response_time': f'{response_time:.3f}s',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/challenges')
@cache_result(timeout=60)  # Cache for 1 minute
def get_challenges():
    """Get all available challenges"""
    start_time = time.time()
    try:
        challenges = get_all_available_challenges()
        response_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'challenges': challenges,
            'count': len(challenges),
            'response_time': f'{response_time:.3f}s'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/challenges/<language>/<difficulty>')
@cache_result(timeout=60)  # Cache for 1 minute
def get_challenges_by_lang_diff(language, difficulty):
    """Get challenges for specific language and difficulty"""
    start_time = time.time()
    try:
        challenges = get_challenges_by_language_difficulty(language, difficulty)
        response_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'challenges': challenges,
            'count': len(challenges),
            'response_time': f'{response_time:.3f}s'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/challenge/<language>/<difficulty>/first')
@cache_result(timeout=60)  # Cache for 1 minute
def get_first_challenge(language, difficulty):
    """Get the first available challenge for a language and difficulty"""
    try:
        print(f"Loading first challenge for {language} - {difficulty}")
        # Get all challenges for this language and difficulty
        challenges = get_challenges_by_language_difficulty(language, difficulty)
        
        if not challenges:
            print(f"No challenges found for {language} - {difficulty}")
            return jsonify({
                'success': False,
                'error': f'No challenges available for {language} - {difficulty}'
            }), 404
            
        # Get the first challenge
        first_challenge = challenges[0]
        challenge_id = first_challenge['challenge_id']
        print(f"Found first challenge: {challenge_id}")
        
        # Get full challenge details
        full_challenge = get_challenge_by_id(language, difficulty, challenge_id)
        
        if full_challenge:
            print(f"Successfully loaded challenge details for {challenge_id}")
            return jsonify({
                'success': True,
                'challenge': full_challenge
            })
        else:
            print(f"Failed to load challenge details for {challenge_id}")
            return jsonify({
                'success': False,
                'error': 'Challenge details not found'
            }), 404
            
    except ValueError as e:
        print(f"Invalid language/difficulty: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Invalid language or difficulty: {str(e)}'
        }), 400
    except Exception as e:
        print(f"Error loading first challenge: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/challenge/<language>/<difficulty>/<int:challenge_id>')
def get_challenge_details(language, difficulty, challenge_id):
    """Get details for a specific challenge"""
    try:
        print(f"Loading challenge {challenge_id} for {language} - {difficulty}")
        challenge = get_challenge_by_id(language, difficulty, challenge_id)
        if challenge:
            # Check if user is logged in and has solved this challenge
            username = request.args.get('username')
            is_solved = False
            if username:
                is_solved = is_challenge_completed(username, language, difficulty, challenge_id)
            
            print(f"Successfully loaded challenge {challenge_id}")
            return jsonify({
                'success': True,
                'challenge': challenge,
                'is_solved': is_solved
            })
        else:
            print(f"Challenge {challenge_id} not found")
            return jsonify({
                'success': False,
                'error': 'Challenge not found'
            }), 404
    except ValueError as e:
        print(f"Invalid language/difficulty: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Invalid language or difficulty: {str(e)}'
        }), 400
    except Exception as e:
        print(f"Error loading challenge {challenge_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def get_cache_key(code, language, test_cases):
    """Generate a cache key for code execution"""
    test_cases_str = json.dumps(test_cases, sort_keys=True)
    return f"{language}:{hashlib.md5((code + test_cases_str).encode()).hexdigest()}"

def get_cached_execution(code, language, test_cases):
    """Get cached execution result if available"""
    cache_key = get_cache_key(code, language, test_cases)
    if cache_key in _execution_cache:
        result, timestamp = _execution_cache[cache_key]
        if time.time() - timestamp < _execution_cache_timeout:
            return result
        del _execution_cache[cache_key]
    return None

def set_cached_execution(code, language, test_cases, result):
    """Cache execution result"""
    cache_key = get_cache_key(code, language, test_cases)
    _execution_cache[cache_key] = (result, time.time())
    
    # Clean old cache entries
    current_time = time.time()
    expired_keys = [
        k for k, (_, t) in _execution_cache.items() 
        if current_time - t > _execution_cache_timeout
    ]
    for k in expired_keys:
        del _execution_cache[k]

def get_batch_cache_key(code, language, test_cases, func_name=None):
    """Generate a specialized cache key for batch execution"""
    import hashlib
    # Use function signature for better cache hits across similar code
    code_hash = hashlib.md5(code.encode()).hexdigest()
    test_cases_str = json.dumps(test_cases, sort_keys=True)
    test_cases_hash = hashlib.md5(test_cases_str.encode()).hexdigest()
    return f"batch:{language}:{code_hash}:{test_cases_hash}"

def get_cached_batch_execution(code, language, test_cases, func_name=None):
    """Get cached batch execution result if available"""
    cache_key = get_batch_cache_key(code, language, test_cases, func_name)
    if cache_key in _batch_cache:
        result, timestamp = _batch_cache[cache_key]
        if time.time() - timestamp < _batch_cache_timeout:
            print(f"✅ Cache hit for batch execution: {cache_key[:30]}...")
            return result
        del _batch_cache[cache_key]
    return None

def set_cached_batch_execution(code, language, test_cases, result, func_name=None):
    """Cache batch execution result"""
    cache_key = get_batch_cache_key(code, language, test_cases, func_name)
    _batch_cache[cache_key] = (result, time.time())
    
    print(f"💾 Cached batch execution: {cache_key[:30]}...")
    
    # Clean old cache entries
    current_time = time.time()
    expired_keys = [
        k for k, (_, t) in _batch_cache.items() 
        if current_time - t > _batch_cache_timeout
    ]
    for k in expired_keys:
        del _batch_cache[k]

# ────────────── Input Conversion Helpers ──────────────
def python_input_literal(val):
    # For Python, use ast.literal_eval for all inputs
    return f"ast.literal_eval({repr(val)})" if isinstance(val, str) else repr(val)

def cpp_input_literal(val):
    import ast
    if isinstance(val, str) and val.strip().startswith('['):
        py_val = ast.literal_eval(val)
        def to_cpp(v):
            if isinstance(v, list):
                return '{' + ','.join(map(to_cpp, v)) + '}'
            return str(v)
        return to_cpp(py_val)
    return str(val)

def java_input_literal(val):
    import ast
    if isinstance(val, str) and val.strip().startswith('['):
        py_val = ast.literal_eval(val)
        def to_java(v):
            if isinstance(v, list):
                return '{' + ','.join(map(to_java, v)) + '}'
            return str(v)
        # 1D or 2D array
        if isinstance(py_val[0], list):
            return f"new int[][]{to_java(py_val)}"
        else:
            return f"new int[]{to_java(py_val)}"
    return str(val)

def js_input_literal(val):
    # For JS, use JSON.parse for arrays/objects, as-is for numbers/strings
    if isinstance(val, str) and (val.strip().startswith('[') or val.strip().startswith('{')):
        return f"JSON.parse({json.dumps(val)})"
    return json.dumps(val)

@app.route('/api/execute', methods=['POST'])
def execute_code():
    """Execute user code against visible test cases only"""
    try:
        data = request.get_json()
        code = data.get('code')
        language = data.get('language')
        test_cases = data.get('test_cases')
        challenge_id = data.get('challenge_id')
        difficulty = data.get('difficulty')
        # --- Signature discovery and driver generation ---
        try:
            if language == 'python':
                func_name, param_names = discover_python_signature(code)
                input_literal = python_input_literal
            elif language == 'cpp':
                func_name, param_names = discover_cpp_signature(code)
                input_literal = cpp_input_literal
            elif language == 'java':
                func_name, param_names = discover_java_signature(code)
                input_literal = java_input_literal
            elif language == 'javascript':
                func_name, param_names = discover_js_signature(code)
                input_literal = js_input_literal
            else:
                return jsonify({'success': False, 'error': f'Unsupported language: {language}'}), 400
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        driver_snippet = build_driver_snippet(func_name, param_names, language)
        # Build per-test driver code for batch execution
        driver_lines = []
        if language == 'python':
            # Only pass the function call snippet, not the full main block
            generated_driver_code = driver_snippet
        elif language == 'cpp':
            generated_driver_code = driver_snippet
        elif language == 'java':
            # Only pass the function call snippet, not the full main method
            generated_driver_code = driver_snippet
        elif language == 'javascript':
            # Only pass the function call snippet, not the full test harness
            generated_driver_code = driver_snippet
        else:
            return jsonify({'success': False, 'error': f'Unsupported language: {language}'}), 400
        # Now call run_all_tests_in_batch with the generated driver code
        result = run_all_tests_in_batch(code, language, generated_driver_code, test_cases)
        return jsonify(result)
    except Exception as e:
        print(f"[DEBUG] Exception in /api/execute: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/validate', methods=['POST'])
def validate_submission():
    """Validate user submission against all test cases (visible and hidden)"""
    try:
        data = request.get_json()
        code = data.get('code')
        language = data.get('language')
        test_cases = data.get('test_cases')
        challenge_id = data.get('challenge_id')
        difficulty = data.get('difficulty')
        # --- Fetch hidden test cases if challenge_id/difficulty provided ---
        all_test_cases = test_cases or []
        if challenge_id and difficulty:
            challenge = get_challenge_by_id(language, difficulty, challenge_id)
            if challenge:
                visible = challenge.get('test_cases', [])
                hidden = challenge.get('hidden_test_cases', [])
                # If no test_cases provided, use all from DB
                if not test_cases:
                    all_test_cases = visible + hidden
                # If test_cases provided, append hidden
                else:
                    all_test_cases = test_cases + hidden
        # --- Signature discovery and driver generation ---
        try:
            if language == 'python':
                func_name, param_names = discover_python_signature(code)
                input_literal = python_input_literal
            elif language == 'cpp':
                func_name, param_names = discover_cpp_signature(code)
                input_literal = cpp_input_literal
            elif language == 'java':
                func_name, param_names = discover_java_signature(code)
                input_literal = java_input_literal
            elif language == 'javascript':
                func_name, param_names = discover_js_signature(code)
                input_literal = js_input_literal
            else:
                return jsonify({'success': False, 'error': f'Unsupported language: {language}'}), 400
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        driver_snippet = build_driver_snippet(func_name, param_names, language)
        # Build per-test driver code for batch execution
        driver_lines = []
        if language == 'python':
            # Only pass the function call snippet, not the full main block
            generated_driver_code = driver_snippet
        elif language == 'cpp':
            generated_driver_code = driver_snippet
        elif language == 'java':
            # Only pass the function call snippet, not the full main method
            generated_driver_code = driver_snippet
        elif language == 'javascript':
            # Only pass the function call snippet, not the full test harness
            generated_driver_code = driver_snippet
        else:
            return jsonify({'success': False, 'error': f'Unsupported language: {language}'}), 400
        # Now call run_all_tests_in_batch with the generated driver code
        result = run_all_tests_in_batch(code, language, generated_driver_code, all_test_cases)
        # Patch: always return success, all_passed, test_results, error
        response = {
            "success": result.get("success", False),
            "all_passed": all(r.get("passed") for r in result.get("test_results", [])) if "test_results" in result else False,
            "test_results": result.get("test_results", []),
        }
        if "error" in result:
            response["error"] = result["error"]
        return jsonify(response)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def check_code_compilation(user_code, language, driver_code, test_cases):
    """
    Check if code compiles and runs using the first test case only, without comparing output.
    Uses the same dynamic driver code generation as batch execution.
    """
    if not test_cases:
        return {
            'success': False,
            'compiles': False,
            'error': 'No test cases available for compilation check.'
        }
    first_test_case = [test_cases[0]]
    # Use the global java_input_literal for input conversion
    if language == 'cpp':
        driver_lines = ["int main() {"]
        test_input = first_test_case[0].get('input')
        snippet = driver_code.replace('TEST_INPUT', str(test_input))
        driver_lines.append(f"    {snippet}")
        driver_lines.append("    return 0;")
        driver_lines.append("}")
        generated_driver_code = '\n'.join(driver_lines)
    elif language == 'python':
        driver_lines = ["import ast", "if __name__ == '__main__':"]
        test_input = first_test_case[0].get('input')
        # If input is a string, use ast.literal_eval; otherwise, use as is
        if isinstance(test_input, str):
            snippet = driver_code.replace('TEST_INPUT', f"ast.literal_eval({repr(test_input)})")
        else:
            snippet = driver_code.replace('TEST_INPUT', repr(test_input))
        driver_lines.append(f"    {snippet}")
        generated_driver_code = '\n'.join(driver_lines)
    elif language == 'java':
        # Use the global java_input_literal for input conversion
        driver_lines = ["    public static void main(String[] args) {"]
        for test_case in test_cases:
            test_input = test_case.get('input')
            java_input = java_input_literal(test_input)
            snippet = driver_code.replace('TEST_INPUT', java_input)
            driver_lines.append(f"        {snippet}")
        driver_lines.append("    }")
        generated_driver_code = '\n'.join(driver_lines)
        # Always wrap user_code and main in Solution
        full_code = (
            f"{STANDARD_HEADERS['java']}\n"
            f"public class Solution {{\n"
            f"{user_code}\n"
            f"{generated_driver_code}\n"
            f"}}"
        )
    elif language == 'javascript':
        driver_lines = []
        for test_case in test_cases:
            test_input = test_case.get('input')
            # If input is a string, use JSON.parse; otherwise, use as is
            if isinstance(test_input, str):
                snippet = driver_code.replace('TEST_INPUT', f"JSON.parse({json.dumps(test_input)})")
            else:
                snippet = driver_code.replace('TEST_INPUT', json.dumps(test_input))
            driver_lines.append(snippet)
        generated_driver_code = '\n'.join(driver_lines)
    else:
        return {
            'success': False,
            'compiles': False,
            'error': f'Unsupported language: {language}'
        }
    full_code = build_executable_code(user_code, language, generated_driver_code)
    print(f"[DEBUG] Full code: {full_code}")
    lang_config = PISTON_LANGUAGES.get(language)
    if not lang_config:
        return {
            'success': False,
            'compiles': False,
            'error': f'Unsupported language: {language}'
        }
    data = {
        'language': lang_config['lang'],
        'version': lang_config['version'],
        'files': [{
            'name': lang_config['filename'],
            'content': full_code
        }]
    }
    try:
        response = requests.post(
            f"{PISTON_API}/execute",
            json=data,
            timeout=10
        )
        if response.status_code != 200:
            return {
                'success': False,
                'compiles': False,
                'error': f'Piston API error: {response.status_code}'
            }
        result = response.json()
        if result.get('compile', {}).get('stderr'):
            return {
                'success': True,
                'compiles': False,
                'error': result['compile']['stderr']
            }
        if result.get('run', {}).get('stderr'):
            return {
                'success': True,
                'compiles': False,
                'error': result['run']['stderr']
            }
        # If we get here, it compiled and ran successfully
        return {
            'success': True,
            'compiles': True,
            'message': 'Code compiles and runs successfully'
        }
    except Exception as e:
        return {
            'success': False,
            'compiles': False,
            'error': f'Compilation check failed: {str(e)}'
        }

def run_test_validation(user_code, language, challenge):
    """Run all test cases for a submission using the new driver code system."""
    # Get test cases from the challenge
    test_cases = challenge.get('test_cases', [])
    if not test_cases:
        return {
            'success': False,
            'error': 'No test cases found for this challenge',
            'test_results': []
        }
    driver_code = challenge.get('driver_code', '')
    batch_result = run_all_tests_in_batch(user_code, language, driver_code, test_cases)
    if batch_result.get('success', False):
        test_results = batch_result.get('test_results', [])
        tests_passed = sum(1 for r in test_results if r['passed'])
    else:
        return {
            'success': False,
            'error': batch_result.get('error', 'Batch execution failed'),
            'test_results': []
        }
    score = int((tests_passed / len(test_cases)) * challenge['max_score']) if test_cases and 'max_score' in challenge else 0
    return {
        'success': True,
        'tests_passed': tests_passed,
        'total_tests': len(test_cases),
        'score': score,
        'test_results': test_results
    }

def compare_outputs_smart(actual, expected):
    """Smart comparison that handles different data types properly"""
    # Auto-fix stringified list like "[0,1]" into real list
    if isinstance(expected, str) and expected.startswith('[') and expected.endswith(']'):
        try:
            expected = json.loads(expected)
        except json.JSONDecodeError:
            pass
    # Handle None comparisons
    if expected is None:
        return actual is None
    if actual is None:
        return expected is None
    
    # Handle numeric comparisons (int, float)
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return actual == expected
    
    # Handle string comparisons
    if isinstance(expected, str) and isinstance(actual, str):
        return actual.strip() == expected.strip()
    
    # Handle list/array comparisons
    if isinstance(expected, list) and isinstance(actual, list):
        return actual == expected
    
    # Handle mixed type comparisons (e.g., int vs string)
    try:
        # Try to convert both to the same type for comparison
        if isinstance(expected, (int, float)):
            # Expected is numeric, try to convert actual to numeric
            if isinstance(actual, str):
                # Handle special string cases first
                if actual.lower().strip() in ['null', 'none']:
                    return False  # None/null is not equal to a number
                try:
                    actual_num = float(actual) if '.' in actual else int(actual)
                    return actual_num == expected
                except ValueError:
                    return False  # Can't convert, so not equal
        elif isinstance(actual, (int, float)):
            # Actual is numeric, try to convert expected to numeric
            if isinstance(expected, str):
                # Handle special string cases first
                if expected.lower().strip() in ['null', 'none']:
                    return False  # None/null is not equal to a number
                try:
                    expected_num = float(expected) if '.' in expected else int(expected)
                    return actual == expected_num
                except ValueError:
                    return False  # Can't convert, so not equal
    except Exception as e:
        # If any comparison operation fails, log it and return False
        print(f"Comparison error in compare_outputs_smart: {e}")
        return False
    
    # Fallback to string comparison
    return str(actual).strip() == str(expected).strip()

@app.route('/api/user/<username>')
def get_user_info(username):
    """Get user information including XP and level"""
    try:
        user_stats = get_user_stats(username)
        if not user_stats:
            # Create new user if doesn't exist
            user = create_user(username)
            if user:
                user_stats = get_user_stats(username)
            
        if user_stats:
            return jsonify({
                'success': True,
                'user': {
                    'user_id': user_stats['user_id'],
                    'username': user_stats['username'],
                    'level': user_stats['level'] or 1,
                    'xp': user_stats['xp'] or 0
                }
            })
        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/<username>/profile')
def get_user_profile(username):
    """Get user profile information including solved problems"""
    try:
        # Get basic user stats
        user_stats = get_user_stats(username)
        if not user_stats:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get solved problems statistics
        solved_stats = get_user_solved_stats(username)
        
        return jsonify({
            'success': True,
            'profile': {
                'user_id': user_stats['user_id'],
                'username': user_stats['username'],
                'level': user_stats['level'] or 1,
                'xp': user_stats['xp'] or 0,
                'total_solved': solved_stats['total_solved'],
                'language_stats': solved_stats['language_stats'],
                'recent_solved': solved_stats['solved_problems'][-5:] if solved_stats['solved_problems'] else []
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/user/stats/<username>')
def get_user_stats_endpoint(username):
    """Get user stats for XP display"""
    try:
        user_stats = get_user_stats(username)
        if user_stats:
            return jsonify({
                'success': True,
                'xp': user_stats['xp'] or 0,
                'level': user_stats['level'] or 1
            })
        else:
            return jsonify({'success': False, 'error': 'User not found'})
    except Exception as e:
        print(f"Error getting user stats: {e}")
        return jsonify({'success': False, 'error': 'Failed to get user stats'})

@app.route('/api/challenge/complete', methods=['POST'])
def mark_challenge_completed_api():
    """Mark a challenge as completed for a user"""
    try:
        data = request.get_json()
        username = data.get('username')
        language = data.get('language')
        difficulty = data.get('difficulty')
        challenge_id = data.get('challenge_id')
        challenge_title = data.get('challenge_title')
        time_taken = data.get('time_taken', 0)
        score = data.get('score', 0)
        
        print(f"⏱️ Received completion request:")
        print(f"   User: {username}")
        print(f"   Challenge: {language} {difficulty} #{challenge_id}")
        print(f"   Time taken: {time_taken} seconds ({time_taken//60}:{time_taken%60:02d})")
        print(f"   Score: {score} XP")
        
        if not all([username, language, difficulty, challenge_id]):
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
        
        # Add to solved problems (for profile page) with time_taken
        # This function handles both marking as completed and storing time_taken
        result = add_solved_problem_to_user(username, language, difficulty, challenge_id, challenge_title, time_taken)
        
        # Award XP if challenge was not already completed
        xp_result = None
        if result:
            from database_config import update_user_score
            xp_result = update_user_score(username, score)
        
        response_data = {'success': True, 'message': 'Challenge marked as completed'}
        
        if xp_result:
            response_data.update({
                'xp_awarded': score,
                'new_xp': xp_result['new_xp'],
                'current_level': xp_result['new_level'],
                'new_level': xp_result['new_level'] if xp_result.get('level_up', False) else None
            })
        
        return jsonify(response_data)
    except Exception as e:
        print(f"Error marking challenge completed: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leaderboard')
def get_leaderboard():
    """Get leaderboard data with optional filters"""
    try:
        filter_type = request.args.get('filter_type', 'overall')
        filter_value = request.args.get('filter_value')
        limit = int(request.args.get('limit', 50))
        
        leaderboard_data = get_leaderboard_data(limit, filter_type, filter_value)
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leaderboard/user/<username>')
def get_user_leaderboard_position(username):
    """Get user's current leaderboard position"""
    try:
        position_data = get_user_leaderboard_position(username)
        
        if position_data:
            return jsonify({
                'success': True,
                'position': position_data
            })
        else:
            return jsonify({'success': False, 'error': 'User not found in leaderboard'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/challenges', methods=['POST'])
def add_challenge():
    """Add a new challenge"""
    try:
        data = request.get_json()
        print("[DEBUG] Received challenge data:", data)
        # Validate required fields
        required_fields = ['language', 'difficulty', 'title', 'description', 'buggy_code', 'reference_solution', 'solution_explanation', 'hints', 'test_cases', 'hidden_test_cases', 'driver_code']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            print(f"[DEBUG] Missing fields: {missing_fields}")
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        # Validate test cases
        if not isinstance(data['test_cases'], list) or len(data['test_cases']) < 3:
            print("[DEBUG] Not enough visible test cases")
            return jsonify({
                'success': False,
                'error': 'At least 3 visible test cases are required'
            }), 400
        # Validate hidden test cases
        if not isinstance(data['hidden_test_cases'], list) or len(data['hidden_test_cases']) != 2:
            print("[DEBUG] Incorrect number of hidden test cases")
            return jsonify({
                'success': False,
                'error': 'Exactly 2 hidden test cases are required'
            }), 400
        # Validate hints
        if not isinstance(data['hints'], list) or len(data['hints']) != 3:
            print("[DEBUG] Incorrect number of hints")
            return jsonify({
                'success': False,
                'error': 'Exactly 3 hints are required'
            }), 400
        # Validate language
        if data['language'] not in PISTON_LANGUAGES:
            print(f"[DEBUG] Unsupported language: {data['language']}")
            return jsonify({
                'success': False,
                'error': f'Unsupported language. Must be one of: {", ".join(PISTON_LANGUAGES.keys())}'
            }), 400
        # Validate difficulty
        valid_difficulties = ['basic', 'intermediate', 'advanced']
        if data['difficulty'].lower() not in valid_difficulties:
            print(f"[DEBUG] Invalid difficulty: {data['difficulty']}")
            return jsonify({
                'success': False,
                'error': f'Invalid difficulty. Must be one of: {", ".join(valid_difficulties)}'
            }), 400
        # Insert challenge into DB
        try:
            result = insert_challenge(data['language'], data['difficulty'].lower(), data)
            print("[DEBUG] Insert result:", result)
            if result and 'challenge_id' in result:
                print(f"[DEBUG] Challenge added with ID: {result['challenge_id']}")
                return jsonify({
                    'success': True,
                    'message': 'Challenge added successfully',
                    'challenge_id': result['challenge_id']
                })
            else:
                print("[DEBUG] Failed to insert challenge into database.")
                return jsonify({
                    'success': False,
                    'error': 'Failed to insert challenge into database.'
                }), 500
        except Exception as db_exc:
            print(f"[DEBUG] Database error: {db_exc}")
            return jsonify({
                'success': False,
                'error': f'Database error: {str(db_exc)}'
            }), 500
    except Exception as e:
        print(f"[DEBUG] General error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required.'}), 400
    db = DatabaseManager()
    query = "SELECT user_id, username, password FROM users WHERE username = %s"
    user = db.execute_query(query, (username,), fetch_one=True)
    if not user:
        return jsonify({'success': False, 'error': 'No account found with that username.'}), 404
    if not bcrypt.check_password_hash(user['password'], password):
        return jsonify({'success': False, 'error': 'Incorrect password.'}), 401
    return jsonify({'success': True, 'user': {'user_id': user['user_id'], 'username': user['username']}})

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.get_json()
    fullname = data.get('fullname')
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    if not all([fullname, email, username, password]):
        return jsonify({'success': False, 'error': 'Please fill in all fields.'}), 400
    db = DatabaseManager()
    check_query = "SELECT user_id FROM users WHERE username = %s"
    existing_user = db.execute_query(check_query, (username,), fetch_one=True)
    if existing_user:
        return jsonify({'success': False, 'error': 'Oops! That username is already taken. Please choose another.'}), 409
    try:
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        insert_query = """
            INSERT INTO users (username, password, emailaddress, fullname)
            VALUES (%s, %s, %s, %s)
            RETURNING user_id, username
        """
        result = db.execute_query(insert_query, (username, hashed_pw, email, fullname), fetch_one=True)
        if result:
            # Initialize leaderboard entry for new user
            from database_config import initialize_user_leaderboard
            initialize_user_leaderboard(username)
            
            return jsonify({'success': True, 'user': {'user_id': result['user_id'], 'username': result['username']}})
        else:
            return jsonify({'success': False, 'error': 'Signup failed. Please try again.'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error: {str(e)}'}), 500

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-secret')
bcrypt = Bcrypt(app)
db = DatabaseManager()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    query = "SELECT user_id, username FROM users WHERE user_id = %s"
    result = db.execute_query(query, (user_id,), fetch_one=True)
    return User(result['user_id'], result['username']) if result else None

class RegisterForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Email()], render_kw={"placeholder": "Email"})
    fullname = StringField(validators=[InputRequired(), Length(min=2, max=50)], render_kw={"placeholder": "Full Name"})
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Register')
    def validate_username(self, username):
        query = "SELECT user_id FROM users WHERE username = %s"
        if db.execute_query(query, (username.data,), fetch_one=True):
            raise ValidationError('Username already exists.')

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired()], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired()], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            query = "SELECT user_id, username, password FROM users WHERE username = %s"
            result = db.execute_query(query, (username,), fetch_one=True)
            if result and bcrypt.check_password_hash(result['password'], password):
                login_user(User(result['user_id'], result['username']))
                return redirect('/')
    return send_from_directory(STATIC_FOLDERS['login'], 'login.html')

@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        fullname = request.form.get('fullname')
        username = request.form.get('username')
        password = request.form.get('password')
        if email and fullname and username and password:
            check_query = "SELECT user_id FROM users WHERE username = %s"
            existing_user = db.execute_query(check_query, (username,), fetch_one=True)
            if not existing_user:
                hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
                insert_query = """
                    INSERT INTO users (username, password, emailaddress, fullname)
                    VALUES (%s, %s, %s, %s)
                    RETURNING user_id, username
                """
                result = db.execute_query(insert_query, (username, hashed_pw, email, fullname), fetch_one=True)
                if result:
                    login_user(User(result['user_id'], result['username']))
                    return redirect('/')
    return send_from_directory(STATIC_FOLDERS['signup'], 'signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

def get_all_available_challenges():
    """Return a list of all available challenges across all languages and difficulties."""
    # This function should aggregate all challenges from the database.
    # You may need to adjust this logic to match your DB schema.
    all_challenges = []
    for lang in PISTON_LANGUAGES.keys():
        for diff in ['basic', 'intermediate', 'advanced']:
            try:
                challenges = get_challenges_by_language_difficulty(lang, diff)
                if challenges:
                    all_challenges.extend(challenges)
            except Exception:
                continue
    return all_challenges

# ────────────── Signature Discovery Helpers ──────────────
import ast
import re

def discover_python_signature(user_code: str):
    tree = ast.parse(user_code)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            params = [arg.arg for arg in node.args.args]
            return node.name, params
    raise ValueError("No top-level function definition found in Python code.")

_cpp_signature_regex = re.compile(
    r'^\s*([A-Za-z_]\w*)\s+'   # return type
    r'([A-Za-z_]\w*)\s*'       # function name
    r'\(\s*([^)]*)\)',         # param list
    re.MULTILINE
)
def discover_cpp_signature(user_code: str):
    m = _cpp_signature_regex.search(user_code)
    if not m:
        raise ValueError("No free function signature found in C++ code.")
    _, name, params = m.groups()
    param_names = [p.strip().split()[-1] for p in params.split(',') if p.strip()]
    return name, param_names

_java_signature_regex = re.compile(
    r'public\s+static\s+\w+\s+([A-Za-z_]\w*)\s*\(([^)]*)\)'
)
def discover_java_signature(user_code: str):
    m = _java_signature_regex.search(user_code)
    if not m:
        raise ValueError("No static method signature found in Java code.")
    name, params = m.groups()
    param_names = [p.strip().split()[-1] for p in params.split(',') if p.strip()]
    return name, param_names

_js_signature_regex = re.compile(
    r'function\s+([A-Za-z_]\w*)\s*\(([^)]*)\)'
)
def discover_js_signature(user_code: str):
    m = _js_signature_regex.search(user_code)
    if not m:
        raise ValueError("No function signature found in JavaScript code.")
    name, params = m.groups()
    param_names = [p.strip() for p in params.split(',') if p.strip()]
    return name, param_names

# ────────────── Driver Builder ──────────────
def build_driver_snippet(func_name, param_names, language):
    if language == 'javascript':
        if len(param_names) == 1:
            # Single parameter: pass tc directly
            return f"console.log({func_name}(tc));"
        else:
            args = ", ".join(f"tc[{i}]" for i in range(len(param_names)))
            return f"console.log({func_name}({args}));"
    elif language == 'java':
        # Use TEST_INPUT placeholder for Java, to be replaced in run_all_tests_in_batch
        return f"System.out.println({func_name}(TEST_INPUT));"
    elif language == 'python':
        # Use TEST_INPUT placeholder for Python, to be replaced in run_all_tests_in_batch
        return f"{func_name}(TEST_INPUT)"
    elif language == 'cpp':
        # Use TEST_INPUT placeholder for C++, to be replaced in run_all_tests_in_batch
        return f"cout << {func_name}(TEST_INPUT) << endl;"
    else:
        args = ", ".join(f"tc[{i}]" for i in range(len(param_names)))
        return f"{func_name}({args})"

# Remove the __main__ block for serverless deployment
# Add vercel_wsgi handler for Vercel
from vercel_wsgi import make_lambda_handler
handler = make_lambda_handler(app)