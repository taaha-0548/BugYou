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
from functools import wraps
import json
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
        'template': Template('''import json

$user_code

test_inputs = $test_inputs
for raw in test_inputs:
    try:
        # support __args__ (list), __kwargs__ (dict), list, single
        if isinstance(raw, dict) and "__args__" in raw:
            result = $func_name(*raw["__args__"])
        elif isinstance(raw, dict) and "__kwargs__" in raw:
            result = $func_name(**raw["__kwargs__"])
        elif isinstance(raw, list):
            try: result = $func_name(*raw)
            except TypeError: result = $func_name(raw)
        else:
            result = $func_name(raw)

        # void: echo args back
        if isinstance(raw, dict) and raw.get("__void__"):
            obj = raw.get("__args__", raw)
        else:
            obj = result

        print(json.dumps(obj, default=str))
    except Exception as e:
        print("ERROR: " + str(e))
''')
    },
  'javascript': {
        'lang': 'javascript',
        'version': '18.15.0',
        'filename': 'main.js',
        'template': Template('''$user_code

const rl = require('readline')
  .createInterface({{ input: process.stdin, output: process.stdout }});
const lines = [];
rl.on('line', l => lines.push(l));
rl.on('close', async () => {{
  for (const raw of lines) {{
    try {{
      const t = JSON.parse(raw);
      let result;
      if (t && t.__args__) {{
        result = await $func_name(...t.__args__);
      }} else if (t && t.__kwargs__) {{
        result = await $func_name(t.__kwargs__);
      }} else if (Array.isArray(t)) {{
        result = await $func_name(t);
      }} else {{
        result = await $func_name(t);
      }}

      const out = (t && t.__void__)
        ? JSON.stringify(t.__args__ || t)
        : JSON.stringify(result);
      console.log(out);
    }} catch (e) {{
      console.log("ERROR: " + e.message);
    }}
  }}
}});
''')
    },
    'java': {
        'lang': 'java',
        'version': '15.0.2',
        'filename': 'Main.java',
        'template': '''
import java.util.*;
import java.io.*;
import java.lang.reflect.*;

public class Main {{
    {user_code}

    public static void main(String[] args) throws Exception {{
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        String line;
        while ((line = br.readLine()) != null) {{
            line = line.trim();
            if (line.isEmpty()) continue;
            try {{
                Object result;
                boolean isVoid = line.contains("\\\"__void__\\\":true");
                // Multi-arg: {{"__args__":[...]}}

                if (line.startsWith("{{") && line.contains("__args__")) {{
                    int idx = line.indexOf("__args__");
                    int start = line.indexOf('[', idx);
                    int end = line.indexOf(']', start);
                    String arrPart = line.substring(start + 1, end);
                    String[] toks = arrPart.split(",");
                    List<Object> items = new ArrayList<>();
                    for (String t : toks) {{
                        t = t.trim().replaceAll("^\\\"|\\\"$", "");
                        if (!t.isEmpty()) {{
                            if (t.matches("^-?\\\\d+$")) items.add(Integer.parseInt(t));
                            else if (t.matches("^-?\\\\d+\\\\.\\\\d+$")) items.add(Double.parseDouble(t));
                            else if (t.equalsIgnoreCase("true")||t.equalsIgnoreCase("false")) items.add(Boolean.parseBoolean(t));
                            else items.add(t);
                        }}
                    }}
                    Class<?>[]  pTypes = new Class<?>[items.size()];
                    Object[]    pVals  = new Object[items.size()];
                    for (int i = 0; i < items.size(); i++) {{
                        Object v = items.get(i);
                        if (v instanceof Integer) pTypes[i] = int.class;
                        else if (v instanceof Double) pTypes[i] = double.class;
                        else if (v instanceof Boolean) pTypes[i] = boolean.class;
                        else pTypes[i] = String.class;
                        pVals[i] = v;
                    }}
                    Method m = Main.class.getDeclaredMethod("{func_name}", pTypes);
                    result = m.invoke(null, pVals);
                }}
                else if (line.startsWith("[")) {{
                    String inner = line.substring(1, line.length()-1).trim();
                    String[] parts = inner.isEmpty() ? new String[0] : inner.split(",");
                    int[] arr = new int[parts.length];
                    for (int i = 0; i < parts.length; i++) {{
                        arr[i] = Integer.parseInt(parts[i].trim());
                    }}
                    result = Main.class.getDeclaredMethod("{func_name}", int[].class)
                                       .invoke(null, (Object)arr);
                }}
                else {{
                    String v = line.replaceAll("\\\"", "").trim();
                    int iv = Integer.parseInt(v);
                    result = Main.class.getDeclaredMethod("{func_name}", int.class)
                                       .invoke(null, iv);
                }}

                if (isVoid) {{
                    System.out.println(line);
                }} else {{
                    if (result instanceof int[]) {{
                        System.out.println(Arrays.toString((int[])result));
                    }} else if (result != null) {{
                        System.out.println(result.toString());
                    }}
                }}
            }} catch (Exception e) {{
                System.out.println("ERROR: " + (e.getCause() != null ? e.getCause().getMessage() : e.getMessage()));
            }}
        }}
    }}
}}
'''
    },
    'cpp': {
        'lang': 'cpp',
        'version': '10.2.0',
        'filename': 'main.cpp',
        'template': '''
#include <bits/stdc++.h>

using namespace std;

{user_code}

int main() {{
    vector<int> testInput = {test_input};
    auto result = {func_name}(testInput);
    cout << result << endl;
    return 0;
}}
'''
    }
}

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
    if func_name is None:
        func_name = extract_function_name(code, language)
    code_hash = hashlib.md5(code.encode()).hexdigest()
    test_cases_str = json.dumps(test_cases, sort_keys=True)
    test_cases_hash = hashlib.md5(test_cases_str.encode()).hexdigest()
    return f"batch:{language}:{func_name}:{code_hash}:{test_cases_hash}"

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
    if func_name is None:
        func_name = extract_function_name(code, language)
    code_hash = hashlib.md5(code.encode()).hexdigest()
    test_cases_str = json.dumps(test_cases, sort_keys=True)
    test_cases_hash = hashlib.md5(test_cases_str.encode()).hexdigest()
    return f"batch:{language}:{func_name}:{code_hash}:{test_cases_hash}"

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

@app.route('/api/execute', methods=['POST'])
def execute_code():
    """Execute user code against visible test cases only"""
    try:
        data = request.get_json()
        code = data.get('code')
        language = data.get('language')
        test_cases = data.get('test_cases', [])
        
        if not code or not language:
            return jsonify({'success': False, 'error': 'Code and language required'}), 400
        # --- Early syntax validation for Python/JS ---
        if language == 'python':
            import ast
            try:
                ast.parse(code)
            except Exception as e:
                return jsonify({'success': False, 'error': f'Python syntax error: {e}'}), 400
        elif language == 'javascript':
            if 'function ' not in code:
                return jsonify({'success': False, 'error': 'JavaScript code must define at least one function.'}), 400
        # ... existing code ...
        # Check cache first
        cached_result = get_cached_execution(code, language, test_cases)
        if cached_result:
            return jsonify(cached_result)
        # Check if language is supported
        if language not in PISTON_LANGUAGES:
            return jsonify({'success': False, 'error': 'Unsupported language'}), 400
        config = PISTON_LANGUAGES[language]
        # First check if code compiles
        compilation = check_code_compilation(code, language, config)
        if not compilation['success'] or not compilation['compiles']:
            result = {
                'success': False,
                'error': 'Compilation failed',
                'details': compilation['error']
            }
            set_cached_execution(code, language, test_cases, result)
            return jsonify(result), 400
        func_name = extract_function_name(code, language)
        if not func_name:
            result = {
                'success': False,
                'error': 'Could not identify main function'
            }
            set_cached_execution(code, language, test_cases, result)
            return jsonify(result), 400
        # Use batch execution for optimal performance
        batch_result = run_all_tests_in_batch(code, language, test_cases, func_name)
        # If batch execution failed, return error (do not fall back to sequential)
        if not batch_result.get('success', False):
            print(f"Batch execution failed: {batch_result.get('error', 'Unknown error')}")
            return jsonify({
                'success': False,
                'error': batch_result.get('error', 'Batch execution failed'),
                'test_results': [],
                'tests_passed': 0,
                'total_tests': len(test_cases)
            }), 500
        else:
            # Use batch execution results
            result = batch_result
        # Cache successful result
        set_cached_execution(code, language, test_cases, result)
        return jsonify(result)
    except requests.RequestException as e:
        return jsonify({'success': False, 'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/validate', methods=['POST'])
def validate_submission():
    """Validate user submission against all test cases (visible and hidden)"""
    try:
        data = request.get_json()
        code = data.get('code')
        language = data.get('language')
        challenge_id = data.get('challenge_id')
        difficulty = data.get('difficulty')
        username = data.get('username')  # Get username from request
        
        if not all([code, language, challenge_id, difficulty]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Get challenge details with test cases
        challenge = get_challenge_by_id(language, difficulty, challenge_id)
        if not challenge:
            return jsonify({'success': False, 'error': 'Challenge not found'}), 404
        
        # Run validation against all test cases using batch execution
        results = run_test_validation(code, language, challenge)
        
        # Check if all tests passed (including hidden tests)
        visible_tests = challenge.get('test_cases', []) 
        hidden_tests = []
        for i in range(1, 3):  # Up to 2 hidden tests
            input_key = f'hidden_test_{i}_input'
            expected_key = f'hidden_test_{i}_expected'
            if challenge.get(input_key) and challenge.get(expected_key):
                hidden_tests.append({
                    'input': challenge[input_key],
                    'expected': challenge[expected_key],
                    'number': len(visible_tests) + i
                })
        
        # Run hidden tests in batch if all visible tests passed
        if results['tests_passed'] == len(visible_tests):
            if language not in PISTON_LANGUAGES:
                return jsonify({
                    'success': False,
                    'error': f'Unsupported language: {language}',
                    'visible_results': results,
                    'all_passed': False
                })
            func_name = extract_function_name(code, language)
            if not func_name:
                return jsonify({
                    'success': False,
                    'error': 'Could not identify main function for hidden tests',
                    'visible_results': results,
                    'all_passed': False
                })
            # Prepare hidden test cases for batch execution
            batch_hidden_tests = []
            for test_case in hidden_tests:
                test_input = test_case['input']
                if isinstance(test_input, str):
                    try:
                        test_input = json.loads(test_input)
                    except Exception:
                        pass  # Keep as string if not valid JSON
                batch_hidden_tests.append({
                    'input': test_input,
                    'expected': test_case.get('expected')
                })
            if batch_hidden_tests:
                hidden_batch_result = run_all_tests_in_batch(code, language, batch_hidden_tests, func_name)
                # If any hidden test fails, return failure
                if not hidden_batch_result.get('success', False):
                    return jsonify({
                        'success': False,
                        'error': hidden_batch_result.get('error', 'Hidden test cases failed'),
                        'visible_results': results,
                        'all_passed': False,
                        'test_results': results.get('test_results', [])
                    })
                for hidden_result in hidden_batch_result.get('test_results', []):
                    if not hidden_result.get('passed', False):
                        return jsonify({
                            'success': False,
                            'error': 'Hidden test cases failed',
                            'visible_results': results,
                            'all_passed': False,
                            'test_results': results.get('test_results', [])
                        })
            # All tests passed (visible and hidden) - Check if already completed
            xp_reward = None
            if username:
                # Check if user has already completed this challenge
                if is_challenge_completed(username, language, difficulty, challenge_id):
                    # Challenge already completed - no XP reward
                    return jsonify({
                        'success': True,
                        'message': '',  # Removed 'All test cases passed!'
                        'visible_results': results,
                        'all_passed': True,
                        'score': results['score'],
                        'xp_reward': None,
                        'already_completed': True,
                        'test_results': results.get('test_results', [])
                    })
                else:
                    # First time completing this challenge - Award XP
                    score_to_award = results['score']
                    xp_reward = update_user_score(username, score_to_award)
                    from database_config import update_leaderboard_entry
                    update_leaderboard_entry(username)
            return jsonify({
                'success': True,
                'message': '',  # Removed 'All test cases passed!'
                'visible_results': results,
                'all_passed': True,
                'score': results['score'],
                'xp_reward': xp_reward,
                'test_results': results.get('test_results', [])
            })
        else:
            # Not all visible tests passed
            return jsonify({
                'success': False,
                'error': 'Not all visible test cases passed',
                'visible_results': results,
                'all_passed': False,
                'test_results': results.get('test_results', [])
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def check_code_compilation(code, language, config):
    """Check if code compiles without running it"""
    try:
        # Clean user code
        clean_code = clean_user_code(code, language)
        
        # Get proper template from PISTON_LANGUAGES
        lang_config = PISTON_LANGUAGES.get(language)
        if not lang_config:
            return {
                'success': False,
                'compiles': False,
                'error': f'Unsupported language: {language}'
            }
        
        # Extract the actual function name from user code
        func_name = extract_function_name(code, language)
        if not func_name:
            return {
                'success': False,
                'compiles': False,
                'error': 'Could not identify function to test'
            }
        
        # For interpreted languages, we'll do a syntax check
        if language == 'python':
            # Use a dummy test_inputs for syntax check
            test_inputs = json.dumps([None])
            test_code = lang_config['template'].substitute(
                user_code=clean_code,
                test_inputs=test_inputs,
                func_name=func_name
            )
        elif language == 'javascript':
            converted_null = convert_input_format(None, language)
            test_code = lang_config['template'].substitute(
                user_code=clean_code,
                test_input=converted_null,
                func_name=func_name
            )
        else:
            # For compiled languages (Java, C++), use proper null initialization
            if language == 'java':
                null_value = 'new int[0]'  # Empty array for Java
            elif language == 'cpp':
                null_value = '{1, 2, 3}'  # Safe default for C++ (not empty)
            else:
                null_value = 'null'
            test_code = lang_config['template'].format(
                user_code=clean_code,
                test_input=null_value,
                func_name=func_name
            )
        
        # Validate filename to prevent double extension issues
        filename = lang_config['filename']
        
        # Ensure filename doesn't have double extensions (fix for main.cpp.cpp issue)
        if filename.count('.') > 1:
            # Extract the base name and last extension
            parts = filename.split('.')
            if len(parts) >= 3:  # main.cpp.cpp -> parts = ['main', 'cpp', 'cpp']
                filename = parts[0] + '.' + parts[-1]  # main.cpp
            elif len(parts) == 2 and parts[0] == '':  # .cpp.cpp -> parts = ['', 'cpp', 'cpp']
                filename = 'main.' + parts[-1]
        
        # Additional validation for common issues
        if not filename or filename.startswith('.') or filename.endswith('.'):
            # Fallback to language-specific default filenames
            if language == 'cpp':
                filename = 'main.cpp'
            elif language == 'java':
                filename = 'Main.java'
            elif language == 'python':
                filename = 'main.py'
            elif language == 'javascript':
                filename = 'main.js'
            else:
                filename = 'main.txt'
        
        # Execute the code
        data = {
            'language': lang_config['lang'],
            'version': lang_config['version'],
            'files': [{
                'name': filename,
                'content': test_code
            }]
        }
        
        response = requests.post(
            f"{PISTON_API}/execute",
            json=data,
            timeout=10  # Add timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Check for compilation errors
            if result.get('compile') and result['compile'].get('stderr'):
                return {
                    'success': True,
                    'compiles': False,
                    'error': result['compile']['stderr']
                }
            
            # If we get here, it compiled successfully
            return {
                'success': True,
                'compiles': True,
                'message': 'Code compiles successfully'
            }
        else:
            return {
                'success': False,
                'compiles': False,
                'error': f'Piston API error: {response.status_code}'
            }
            
    except Exception as e:
        return {
            'success': False,
            'compiles': False,
            'error': f'Compilation check failed: {str(e)}'
        }

def extract_function_name(code, language):
    """Extract the main function name from code"""
    try:
        patterns = {
            'python': r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            'javascript': r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            'java': r'public\s+static\s+(?:int|void|boolean|String|long|double|float)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            'cpp': r'(?:int|void|bool|long|double|float|string|char|auto|vector<[^>]+>)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{'
        }
        
        if language not in patterns:
            return None
            
        pattern = patterns[language]
        matches = re.findall(pattern, code, re.MULTILINE)
        
        if matches:
            # Return the first function found
            func_name = matches[0]
            return func_name
        else:
            return None
            
    except Exception as e:
        print(f"Error extracting function name for {language}: {e}")
        return None


def run_test_validation(code, language, challenge):
    """Run all test cases for a submission"""
    lang_map = {
        'python': {'lang': 'python', 'filename': 'main.py'},
        'javascript': {'lang': 'javascript', 'filename': 'main.js'},
        'java': {'lang': 'java', 'filename': 'Main.java'},
        'cpp': {'lang': 'cpp', 'filename': 'main.cpp'}
    }
    if language not in lang_map:
        raise ValueError('Unsupported language')
    config = lang_map[language]
    # First check if code compiles
    compilation = check_code_compilation(code, language, config)
    if not compilation['success'] or not compilation['compiles']:
        return {
            'success': False,
            'error': 'Compilation failed',
            'details': compilation['error'],
            'tests_passed': 0,
            'total_tests': len(challenge['test_cases']) if 'test_cases' in challenge else 0,
            'score': 0
        }
    # Extract function name for test case setup
    func_name = extract_function_name(code, language)
    if not func_name:
        return {
            'success': False,
            'error': 'Could not identify main function',
            'tests_passed': 0,
            'total_tests': len(challenge['test_cases']) if 'test_cases' in challenge else 0,
            'score': 0
        }
    # Use batch execution for better performance
    test_cases = challenge.get('test_cases', [])
    total_tests = len(test_cases)
    if test_cases:
        batch_result = run_all_tests_in_batch(code, language, test_cases, func_name)
        if batch_result.get('success', False):
            # Use batch execution results
            test_results = batch_result.get('test_results', [])
            tests_passed = batch_result.get('tests_passed', 0)
        else:
            # If batch execution fails, return error (do not fall back to sequential)
            return {
                'success': False,
                'error': batch_result.get('error', 'Batch execution failed'),
                'tests_passed': 0,
                'total_tests': total_tests,
                'score': 0,
                'test_results': []
            }
    else:
        test_results = []
        tests_passed = 0
    # Calculate final score
    score = int((tests_passed / total_tests) * challenge['max_score']) if total_tests and 'max_score' in challenge else 0
    return {
        'success': True,
        'tests_passed': tests_passed,
        'total_tests': total_tests,
        'score': score,
        'test_results': test_results
    }

def convert_input_format(test_input, language):
    """Convert test input to language-specific format for template substitution"""
    try:
        if language == 'python':
            return json.dumps(test_input)
        elif language == 'javascript':
            return json.dumps(test_input)
            
        elif language == 'java':
            # Java: convert [1,2,3] to {1,2,3} for array initialization
            if isinstance(test_input, list):
                content = ', '.join(str(x) for x in test_input)
                return '{' + content + '}'
            else:
                test_input_str = str(test_input)
                return test_input_str.replace('[', '{').replace(']', '}')
            
        elif language == 'cpp':
            # C++: Handle different input types with improved validation
            if isinstance(test_input, list):
                if not test_input:  # Empty array
                    return '{1, 2, 3}'  # Default for empty arrays
                content = ', '.join(str(x) for x in test_input)
                return '{' + content + '}'
            else:
                test_input_str = str(test_input).strip()
                
                # Handle empty or null inputs - provide default vector
                if not test_input_str or test_input_str in ['None', 'none', 'null']:
                    return '{1, 2, 3}'  # Default test vector
                
                # If it's an array [1,2,3], convert to C++ vector {1,2,3}
                if test_input_str.startswith('[') and test_input_str.endswith(']'):
                    content = test_input_str[1:-1].strip()
                    if content:  # Non-empty array
                        return '{' + content + '}'
                    else:  # Empty array []
                        return '{1, 2, 3}'  # Default for empty arrays
                
                # If it's already in C++ format {1,2,3}, validate and clean
                if test_input_str.startswith('{') and test_input_str.endswith('}'):
                    content = test_input_str[1:-1].strip()
                    if content and content != '{}':  # Valid non-empty content
                        return test_input_str
                    else:  # Empty or malformed content
                        return '{1, 2, 3}'  # Default for empty/malformed
                
                # Single number or other value
                return test_input_str
            
        return str(test_input)
        
    except Exception as e:
        print(f"Error converting input format: {e}")
        return str(test_input)

def run_all_tests_in_batch(code, language, test_cases, func_name):
    """
    Execute all test cases in a single API call for maximum performance
    This is the main optimization that reduces execution time by 90%+
    """
    try:
        if not test_cases:
            return {
                'success': True,
                'tests_passed': 0,
                'total_tests': 0,
                'test_results': []
            }
        # Check batch cache first
        cached_result = get_cached_batch_execution(code, language, test_cases, func_name)
        if cached_result:
            return cached_result
        # Get language configuration
        lang_config = PISTON_LANGUAGES.get(language)
        if not lang_config:
            return {
                'success': False,
                'error': f'Unsupported language: {language}',
                'tests_passed': 0,
                'total_tests': len(test_cases),
                'test_results': []
            }
         # Clean user code
        clean_code = clean_user_code(code, language)
        
        # Create batch test code based on language
        if language == 'python':
            batch_code = f"""
import sys
import json

{clean_code}

test_inputs = []
for line in sys.stdin:
    line = line.strip()
    if line:
        test_inputs.append(json.loads(line))
for raw in test_inputs:
    try:
        # support __args__ (list), __kwargs__ (dict), list, single
        if isinstance(raw, dict) and "__args__" in raw:
            result = {func_name}(*raw["__args__"])
        elif isinstance(raw, dict) and "__kwargs__" in raw:
            result = {func_name}(**raw["__kwargs__"])
        elif isinstance(raw, list):
            try: result = {func_name}(*raw)
            except TypeError: result = {func_name}(raw)
        else:
            result = {func_name}(raw)
        # void: echo args back
        if isinstance(raw, dict) and raw.get("__void__"):
            obj = raw.get("__args__", raw)
        else:
            obj = result
        print(json.dumps(obj, default=str))
    except Exception as e:
        print("ERROR: " + str(e))
"""
        
        elif language == 'javascript':
            batch_code = f"""
{clean_code}

const rl = require('readline')
  .createInterface({{ input: process.stdin, output: process.stdout }});
const lines = [];
rl.on('line', l => lines.push(l));
rl.on('close', async () => {{
  for (const raw of lines) {{
    try {{
      const t = JSON.parse(raw);
      let result;
      if (t && t.__args__) {{
        result = await {func_name}(...t.__args__);
      }} else if (t && t.__kwargs__) {{
        result = await {func_name}(t.__kwargs__);
      }} else if (Array.isArray(t)) {{
        result = await {func_name}(t);
      }} else {{
        result = await {func_name}(t);
      }}

      const out = (t && t.__void__)
        ? JSON.stringify(t.__args__ || t)
        : JSON.stringify(result);
      console.log(out);
    }} catch (e) {{
      console.log("ERROR: " + e.message);
    }}
  }}
}});
"""
        elif language == 'java':
            batch_code = """
import java.io.*;
import java.util.*;
import java.util.stream.*;

public class Main {{
    // === User's method ===
{user_code}
    // =====================

    public static void main(String[] args) throws Exception {{
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        String line;
        while ((line = br.readLine()) != null) {{
            line = line.trim();
            if (line.isEmpty()) continue;

            // Simple JSON-array parser: "[1,2,3]" → int[]{{1,2,3}}
            String inside = line.substring(1, line.length() - 1).trim();
            int[] nums;
            if (inside.isEmpty()) {{
                nums = new int[0];
            }} else {{
                nums = Arrays.stream(inside.split(","))
                             .map(String::trim)
                             .mapToInt(Integer::parseInt)
                             .toArray();
            }}

            // Call the user function
            int result = {func_name}(nums);

            // Print the result
            System.out.println(result);
        }}
    }}
}}
""".format(user_code=clean_code, func_name=func_name)
        elif language == 'cpp':
            batch_code = f"""
#include <iostream>
#include <vector>
#include <sstream>
#include <string>
#include <algorithm>
using namespace std;
{clean_code}
int main() {{
    string line;
    while (getline(cin, line)) {{
        if (line.empty()) continue;
        try {{
            line.erase(remove(line.begin(), line.end(), '['), line.end());
            line.erase(remove(line.begin(), line.end(), ']'), line.end());
            line.erase(remove(line.begin(), line.end(), ' '), line.end());
            vector<int> testInput;
            stringstream ss(line);
            string num;
            while (getline(ss, num, ',')) {{
                if (!num.empty()) {{
                    testInput.push_back(stoi(num));
                }}
            }}
            auto result = {func_name}(testInput);
            cout << result << endl;
        }} catch (const exception& e) {{
            cout << "ERROR: " << e.what() << endl;
        }}
    }}
    return 0;
}}
"""
        else:
            return {
                'success': False,
                'error': f'Batch execution not implemented for {language}',
                'tests_passed': 0,
                'total_tests': len(test_cases),
                'test_results': []
            }
        input_lines = []
        for test_case in test_cases:
            test_input = test_case.get('input', [])
            if isinstance(test_input, str):
                try:
                    test_input = json.loads(test_input)
                except:
                    pass
            if language in ['python', 'javascript']:
                input_lines.append(json.dumps(test_input))
            else:
                input_lines.append(str(test_input))
        stdin_data = '\n'.join(input_lines)
        piston_request = {
            'language': lang_config['lang'],
            'version': lang_config['version'],
            'files': [
                {
                    'name': lang_config['filename'],
                    'content': batch_code
                }
            ],
            'stdin': stdin_data,
            'compile_timeout': 8000,
            'run_timeout': 10000,
            'compile_memory_limit': -1,
            'run_memory_limit': -1
        }
        response = requests.post(
            f'{PISTON_API}/execute',
            headers={'Content-Type': 'application/json'},
            json=piston_request,
            timeout=20
        )
        if response.status_code != 200:
            return {
                'success': False,
                'error': f'API Error: {response.status_code}',
                'tests_passed': 0,
                'total_tests': len(test_cases),
                'test_results': []
            }
        result = response.json()
        if result.get('compile', {}).get('stderr'):
            return {
                'success': False,
                'error': f'Compilation error: {result["compile"]["stderr"]}',
                'tests_passed': 0,
                'total_tests': len(test_cases),
                'test_results': []
            }
        if result.get('run', {}).get('stderr'):
            return {
                'success': False,
                'error': f'Runtime error: {result["run"]["stderr"]}',
                'tests_passed': 0,
                'total_tests': len(test_cases),
                'test_results': []
            }
        output = result.get('run', {}).get('stdout', '').strip()
        output_lines = output.split('\n') if output else []
        test_results = []
        tests_passed = 0
        for i, test_case in enumerate(test_cases):
            expected = test_case.get('expected_output') or test_case.get('expected', '')
            if i < len(output_lines):
                actual = output_lines[i].strip()
                if actual.startswith('ERROR:'):
                    test_results.append({
                        'test_number': i + 1,
                        'passed': False,
                        'error': actual,
                        'output': None,
                        'expected': expected
                    })
                else:
                    try:
                        parsed_actual = json.loads(actual)
                    except (json.JSONDecodeError, ValueError):
                        actual_lower = actual.lower().strip()
                        if actual_lower == 'none':
                            parsed_actual = None
                        elif actual_lower == 'null':
                            parsed_actual = None
                        else:
                            parsed_actual = actual
                    passed = compare_outputs_smart(parsed_actual, expected)
                    if passed:
                        tests_passed += 1
                    test_results.append({
                        'test_number': i + 1,
                        'passed': passed,
                        'error': None,
                        'output': parsed_actual,
                        'expected': expected
                    })
            else:
                test_results.append({
                    'test_number': i + 1,
                    'passed': False,
                    'error': 'No output received',
                    'output': None,
                    'expected': expected
                })
        result = {
            'success': True,
            'tests_passed': tests_passed,
            'total_tests': len(test_cases),
            'test_results': test_results
        }
        set_cached_batch_execution(code, language, test_cases, result, func_name)
        return result
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'Network error: {str(e)}',
            'tests_passed': 0,
            'total_tests': len(test_cases),
            'test_results': []
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Batch execution failed: {str(e)}',
            'tests_passed': 0,
            'total_tests': len(test_cases),
            'test_results': []
        }

def clean_user_code(code, language):
    """Remove main function and test-related code from user code while preserving imports"""
    if language == 'python':
        # Split into lines and filter out test-related code, but preserve imports
        lines = code.split('\n')
        clean_lines = []
        for line in lines:
            line_lower = line.lower().strip()
            # Skip test-related lines but preserve imports and function definitions
            if not any(x in line_lower for x in ['test_input', 'print(result)', 'print(', '#test']):
                # Allow import statements and function definitions
                if (line_lower.startswith('import ') or 
                    line_lower.startswith('from ') or 
                    line_lower.startswith('def ') or 
                    line.strip() == '' or
                    not line_lower.startswith('print(') and 'test_input' not in line_lower):
                    clean_lines.append(line)
        return '\n'.join(clean_lines)
    elif language == 'javascript':
        # Remove test-related code but preserve utility functions and imports
        lines = code.split('\n')
        clean_lines = []
        for line in lines:
            line_lower = line.lower().strip()
            # Skip test-related lines but preserve function definitions and utility code
            if not any(x in line_lower for x in ['test_input', 'console.log(result)', '//test']):
                # Allow const, function definitions, and other non-test code
                if (line_lower.startswith('const ') or 
                    line_lower.startswith('function ') or 
                    line_lower.startswith('let ') or 
                    line_lower.startswith('var ') or
                    line.strip() == '' or
                    'test_input' not in line_lower and 'console.log(' not in line_lower):
                    clean_lines.append(line)
        return '\n'.join(clean_lines)
    elif language == 'java':
        # Remove main method and test code but preserve imports and class structure
        # First remove main method
        code = re.sub(r'public\s+static\s+void\s+main\s*\([^)]*\)\s*\{[^}]*\}', '', code, flags=re.DOTALL)
        # Remove test-related lines but preserve imports
        lines = code.split('\n')
        clean_lines = []
        for line in lines:
            line_lower = line.lower().strip()
            if not any(x in line_lower for x in ['test_input', 'system.out.println(result)', '//test']):
                # Allow imports, class definitions, and method definitions
                if (line_lower.startswith('import ') or 
                    line_lower.startswith('public class') or 
                    line_lower.startswith('public static') or 
                    line_lower.startswith('private') or
                    line.strip() == '' or
                    'test_input' not in line_lower):
                    clean_lines.append(line)
        return '\n'.join(clean_lines)
    elif language == 'cpp':
        # Remove main function and test code but preserve includes and function definitions
        # First remove main function
        code = re.sub(r'int\s+main\s*\([^)]*\)\s*\{[^}]*\}', '', code, flags=re.DOTALL)
        # Remove test-related lines but preserve includes and typedefs
        lines = code.split('\n')
        clean_lines = []
        for line in lines:
            line_lower = line.lower().strip()
            if not any(x in line_lower for x in ['test_input', 'cout << result', '//test']):
                # Allow includes, using statements, typedefs, defines, and function definitions
                if (line_lower.startswith('#include') or 
                    line_lower.startswith('using ') or 
                    line_lower.startswith('typedef') or 
                    line_lower.startswith('#define') or 
                    line.strip() == '' or
                    ('test_input' not in line_lower and 'cout <<' not in line_lower)):
                    clean_lines.append(line)
        return '\n'.join(clean_lines)
    return code

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
        required_fields = ['language', 'difficulty', 'title', 'description', 'buggy_code', 'reference_solution', 'solution_explanation', 'hints', 'test_cases', 'hidden_test_cases']
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

app.config['SECRET_KEY'] = 'thisisasecretkey'
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

if __name__ == '__main__':
    print("🔌 Testing database connection...")
    if test_connection():
        print("✅ Database connected successfully!")
        
        print("🚀 Starting BugYou Flask server...")
        print("📍 Frontend: http://localhost:5000")
        print("🔗 API Health: http://localhost:5000/api/health")
        app.run(host='0.0.0.0', debug=True)
    else:
        print("❌ Failed to connect to database. Please check your configuration.")
        exit(1)