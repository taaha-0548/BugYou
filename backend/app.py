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
from database_config import DatabaseManager

# Import our database functions
from database_config import (
    get_challenges_by_language_difficulty, 
    get_challenge_by_id,
    get_user_by_username,
    create_user,
    test_connection,
    CHALLENGE_TABLES
)

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
}

# Configuration
PISTON_API = 'https://emkc.org/api/v2/piston'

# Simple in-memory cache for frequently accessed data
_cache = {}
_cache_timeout = 300  # 5 minutes

# Enhanced cache for code execution results
_execution_cache = {}
_execution_cache_timeout = 300  # 5 minutes (increased for better performance)

# Advanced cache for batch execution results
_batch_cache = {}
_batch_cache_timeout = 600  # 10 minutes

# Language configuration for Piston API
PISTON_LANGUAGES = {
    'python': {
        'lang': 'python',
        'version': '3.10.0',
        'filename': 'main.py',
        'template': Template('''import sys
import json

$user_code

test_input = $test_input

try:
    if isinstance(test_input, list):
        try:
            result = $func_name(*test_input)
        except TypeError:
            result = $func_name(test_input)
    else:
        result = $func_name(test_input)

    print(json.dumps(result))
except Exception as e:
    print(f"ERROR: {str(e)}")
''')
    },
    'javascript': {
        'lang': 'javascript',
        'version': '18.15.0',
        'filename': 'main.js',
        'template': Template('''$user_code

const testInput = $test_input;

try {
    let result;
    if (Array.isArray(testInput)) {
        try {
            result = $func_name(...testInput);
        } catch (e1) {
            result = $func_name(testInput);
        }
    } else {
        result = $func_name(testInput);
    }

    console.log(JSON.stringify(result));
} catch (e) {
    console.log(`ERROR: ${e.message}`);
}
''')
    },
    'java': {
        'lang': 'java',
        'version': '15.0.2',
        'filename': 'Main.java',
        'template': '''
import java.util.*;
import java.io.*;
import java.math.*;

public class Main {{
    {user_code}
    
    public static void main(String[] args) {{
        int[] testInput = {test_input};
        int result = {func_name}(testInput);
        System.out.println(result);
    }}
}}
'''
    },
    'cpp': {
        'lang': 'cpp',
        'version': '10.2.0',
        'filename': 'main.cpp',
        'template': '''
#include <iostream>
#include <vector>
#include <algorithm>
#include <string>
#include <map>
#include <set>
#include <unordered_map>
#include <unordered_set>
#include <queue>
#include <stack>
#include <cmath>
#include <climits>

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

def cache_result(timeout=300):
    """Decorator to cache API results"""
    def decorator(f):
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

@app.route('/api/cache/clear')
def clear_cache():
    """Clear all caches"""
    global _cache, _execution_cache, _batch_cache
    _cache = {}
    _execution_cache = {}
    _batch_cache = {}
    return jsonify({
        'success': True,
        'message': 'All caches cleared successfully (API, execution, batch)',
        'timestamp': datetime.now().isoformat()
    })

# ================================
# SERVE FRONTEND
# ================================

@app.route('/')
def serve_frontend():
    """Serve the main frontend page"""
    return send_from_directory(STATIC_FOLDERS['main'], 'index.html')

@app.route('/home')
def serve_home():
    """Serve the home page"""
    return send_from_directory('../frontend/home', 'home.html')

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
    # Special handling for /home/home.css, /guide/guide.css, /about/about.css
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
# API ENDPOINTS
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
            print(f"Successfully loaded challenge {challenge_id}")
            return jsonify({
                'success': True,
                'challenge': challenge
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
            
                # Extract function name for test case setup  
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
        
        # If batch execution failed, fall back to sequential execution
        if not batch_result.get('success', False):
            print(f"Batch execution failed: {batch_result.get('error', 'Unknown error')}")
            print("Falling back to sequential execution...")
            
            # Run test cases sequentially as fallback
            test_results = []
            tests_passed = 0
            
            for i, test_case in enumerate(test_cases):
                test_input = test_case['input']
                # Convert string input to proper data type
                if isinstance(test_input, str):
                    try:
                        test_input = json.loads(test_input)
                    except:
                        pass  # Keep as string if not valid JSON
                
                result = execute_single_test(
                    code=code,
                    config={'lang': language},
                    test_input=test_input,
                    expected=test_case.get('expected_output') or test_case.get('expected'),
                    test_number=i + 1,
                    challenge={'id': 0},
                    func_name=func_name
                )
                if result['passed']:
                    tests_passed += 1
                test_results.append(result)
                
            result = {
                'success': True,
                'test_results': test_results,
                'tests_passed': tests_passed,
                'total_tests': len(test_cases)
            }
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
        
        # Run hidden tests if all visible tests passed
        if results['tests_passed'] == len(visible_tests):
            # Get language configuration
            if language not in PISTON_LANGUAGES:
                return jsonify({
                    'success': False,
                    'error': f'Unsupported language: {language}',
                    'visible_results': results,
                    'all_passed': False
                })
            
            lang_config = {'lang': language}  # Simple config for execute_single_test
            
            # Extract function name for hidden tests
            func_name = extract_function_name(code, language)
            if not func_name:
                return jsonify({
                    'success': False,
                    'error': 'Could not identify main function for hidden tests',
                    'visible_results': results,
                    'all_passed': False
                })
            
            for test_case in hidden_tests:
                test_input = test_case['input']
                # Convert string input to proper data type (like in visible tests)
                if isinstance(test_input, str):
                    try:
                        test_input = json.loads(test_input)
                    except Exception:
                        pass  # Keep as string if not valid JSON
                result = execute_single_test(
                    code=code,
                    config=lang_config,
                    test_input=test_input,
                    expected=test_case.get('expected'),
                    test_number=test_case['number'],
                    challenge=challenge,
                    func_name=func_name
                )
                print(f"[DEBUG] Hidden Test #{test_case['number']} - Input: {test_case['input']} | Expected: {test_case.get('expected')} | Output: {result.get('output')} | Passed: {result.get('passed')}")
                if not result['passed']:
                    return jsonify({
                        'success': False,
                        'error': 'Hidden test cases failed',
                        'visible_results': results,
                        'all_passed': False
                    })
            
            # All tests passed (visible and hidden)
            return jsonify({
                'success': True,
                'message': 'All test cases passed!',
                'visible_results': results,
                'all_passed': True,
                'score': results['score']
            })
        else:
            # Not all visible tests passed
            return jsonify({
                'success': False,
                'error': 'Not all visible test cases passed',
                'visible_results': results,
                'all_passed': False
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
        if language in ['python', 'javascript']:
            # Use convert_input_format to properly format null/None values
            converted_null = convert_input_format(None, language)
            # lang_config['template'] is already a Template object
            test_code = lang_config['template'].substitute(
                user_code=clean_code,
                test_input=converted_null,
                func_name=func_name  # Use actual function name
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
                func_name=func_name  # Use actual function name
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
            # Fall back to sequential execution
            print(f"Batch validation failed: {batch_result.get('error', 'Unknown error')}")
            print("Falling back to sequential validation...")
            
            test_results = []
            tests_passed = 0
            for i, test_case in enumerate(test_cases):
                result = execute_single_test(
                    code=code,
                    config=config,
                    test_input=test_case['input'],
                    expected=test_case.get('expected_output') or test_case.get('expected', ''),
                    test_number=i + 1,
                    challenge=challenge,
                    func_name=func_name
                )
                if result['passed']:
                    tests_passed += 1
                test_results.append(result)
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

def execute_single_test(code, config, test_input, expected, test_number, challenge, func_name):
    """Execute a single test case"""
    try:
        # No artificial delays - let the system handle rate limiting naturally
        
        # Get language config
        lang_config = PISTON_LANGUAGES.get(config['lang'])
        if not lang_config:
            return {
                'test_number': test_number,
                'passed': False,
                'error': f'Unsupported language: {config["lang"]}',
                'output': None,
                'expected': expected
            }

        # Function name is now passed as parameter - no need to extract again
        if not func_name:
            return {
                'test_number': test_number,
                'passed': False,
                'error': 'Could not identify main function',
                'output': None,
                'expected': expected
            }

        # Clean user code by removing any existing main/test functions
        clean_code = clean_user_code(code, config['lang'])
        
        # Convert input format for the specific language
        converted_input = convert_input_format(test_input, config['lang'])
        
        # Prepare test code using template
        if config['lang'] in ['python', 'javascript']:
            # lang_config['template'] is already a Template object
            test_code = lang_config['template'].substitute(
                func_name=func_name,
                user_code=clean_code,
                test_input=converted_input
            )
        else:
            # Use .format() for Java and C++ (they still use {{ }} escaping)
            test_code = lang_config['template'].format(
                func_name=func_name,
                user_code=clean_code,
                test_input=converted_input
            )
        
        # Removed debug output for performance
        
        # Validate and prepare Piston API request with error checking
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
            if config['lang'] == 'cpp':
                filename = 'main.cpp'
            elif config['lang'] == 'java':
                filename = 'Main.java'
            elif config['lang'] == 'python':
                filename = 'main.py'
            elif config['lang'] == 'javascript':
                filename = 'main.js'
            else:
                filename = 'main.txt'
        
        piston_request = {
            'language': lang_config['lang'],
            'version': lang_config['version'],
            'files': [
                {
                    'name': filename,
                    'content': test_code
                }
            ],
            'stdin': '',  # Add input if needed
            'compile_timeout': 10000,  # 10 seconds
            'run_timeout': 10000,  # 10 seconds
            'compile_memory_limit': -1,  # No limit
            'run_memory_limit': -1  # No limit
        }
        
        # Optimized retry logic with faster timeouts for single test execution
        import time
        max_retries = 1  # Single retry for speed
        base_delay = 0.3  # Even faster retry
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f'{PISTON_API}/execute',
                    headers={'Content-Type': 'application/json'},
                    json=piston_request,
                    timeout=6  # Reduced timeout for faster failure detection
                )
                
                if response.status_code == 200:
                    break  # Success, exit retry loop
                elif response.status_code == 429:  # Rate limit
                    if attempt < max_retries - 1:  # Not the last attempt
                        delay = base_delay * (1.5 ** attempt)  # Gentler backoff: 0.5s, 0.75s
                        print(f"Rate limited (429), retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        return {
                            'test_number': test_number,
                            'passed': False,
                            'error': 'Rate limit exceeded. Please try again in a few moments.',
                            'output': 'Rate Limited',
                            'expected': expected
                        }
                else:
                    return {
                        'test_number': test_number,
                        'passed': False,
                        'error': f'API Error: {response.status_code}',
                        'output': f'Error {response.status_code}',
                        'expected': expected
                    }
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (1.5 ** attempt)  # Gentler backoff
                    print(f"Request failed: {e}, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    return {
                        'test_number': test_number,
                        'passed': False,
                        'error': f'Network error: {str(e)}',
                        'output': 'Network Error',
                        'expected': expected
                    }
        else:
            # This should not happen, but just in case
            return {
                'test_number': test_number,
                'passed': False,
                'error': 'Max retries exceeded',
                'output': 'Max Retries Exceeded',
                'expected': expected
            }
            
        result = response.json()
        
        # Check for compilation errors with detailed analysis
        if result.get('compile', {}).get('stderr'):
            compile_error = result["compile"]["stderr"]
            
            # Analyze common error patterns and provide helpful messages
            if 'main.cpp.cpp' in compile_error:
                error_msg = 'File naming issue detected. Please try again.'
            elif 'cannot access' in compile_error and 'a.out' in compile_error:
                error_msg = 'Compilation failed - executable could not be created.'
            elif 'error:' in compile_error.lower():
                # Extract the main error message
                lines = compile_error.split('\n')
                error_line = next((line for line in lines if 'error:' in line.lower()), compile_error)
                error_msg = f'Compilation error: {error_line.strip()}'
            else:
                error_msg = f'Compilation error: {compile_error.strip()}'
            
            return {
                'test_number': test_number,
                'passed': False,
                'error': error_msg,
                'output': None,
                'expected': expected,
                'debug_info': {
                    'filename': filename,
                    'language': config['lang'],
                    'full_error': compile_error
                }
            }
        
        # Check for runtime errors
        if result.get('run', {}).get('stderr'):
            runtime_error = result["run"]["stderr"]
            return {
                'test_number': test_number,
                'passed': False,
                'error': f'Runtime error: {runtime_error.strip()}',
                'output': None,
                'expected': expected
            }
            
        # Get actual output
        actual_output = result.get('run', {}).get('stdout', '').strip()
        
        # Parse JSON output if possible, then compare properly
        try:
            parsed_output = json.loads(actual_output)
        except (json.JSONDecodeError, ValueError):
            # If JSON parsing fails, check if it's a special case
            actual_output_lower = actual_output.lower().strip()
            if actual_output_lower == 'none':
                parsed_output = None
            elif actual_output_lower == 'null':
                parsed_output = None
            else:
                parsed_output = actual_output
        
        # Compare with expected output using smart comparison
        passed = compare_outputs_smart(parsed_output, expected)
        
        return {
            'test_number': test_number,
            'passed': passed,
            'error': None,
            'output': parsed_output,
            'expected': expected
        }
        
    except Exception as e:
        return {
            'test_number': test_number,
            'passed': False,
            'error': str(e),
            'output': None,
            'expected': expected
        }

def compare_outputs(actual, expected, comparison_type='exact'):
    """Compare actual and expected outputs"""
    if comparison_type == 'exact':
        return str(actual).strip() == str(expected).strip()
    else:
        # Add more comparison types if needed
        return False

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
            # Python batch template - reads all inputs from stdin
            batch_code = f"""
import sys
import json
import math
import collections
from collections import defaultdict, deque, Counter
import heapq
import bisect
import itertools
import functools
from functools import lru_cache
import re
import string

{clean_code}

# Read all test cases from stdin
test_inputs = []
for line in sys.stdin:
    line = line.strip()
    if line:
        test_inputs.append(json.loads(line))

# Execute each test case and output results
for test_input in test_inputs:
    try:
        # Smart argument handling: try both approaches and use the one that works
        result = None
        error = None
        
        # First try: assume function takes individual arguments (e.g., add(a, b))
        if isinstance(test_input, list):
            try:
                result = {func_name}(*test_input)
            except TypeError as e1:
                error = e1
                # If spreading fails, it's likely the function expects the list itself
                try:
                    result = {func_name}(test_input)
                    error = None
                except Exception as e2:
                    error = e2
        else:
            # Single argument or non-list input
            result = {func_name}(test_input)
        
        if error:
            print(f"ERROR: {{str(error)}}")
        else:
            print(json.dumps(result))
    except Exception as e:
        print(f"ERROR: {{str(e)}}")
"""
        
        elif language == 'javascript':
            # JavaScript batch template - fixed brace escaping
            batch_code = f"""
const readline = require('readline');
const rl = readline.createInterface({{
    input: process.stdin,
    output: process.stdout,
    terminal: false
}});

// Common utility functions
const gcd = (a, b) => b === 0 ? a : gcd(b, a % b);
const lcm = (a, b) => (a * b) / gcd(a, b);
const isPrime = n => n > 1 && Array.from({{length: Math.sqrt(n)}}, (_, i) => i + 2).every(i => n % i !== 0);

{clean_code}

const testInputs = [];
rl.on('line', (line) => {{
    if (line.trim()) {{
        testInputs.push(JSON.parse(line));
    }}
}});

rl.on('close', () => {{
    testInputs.forEach(testInput => {{
        try {{
            // Smart argument handling: try both approaches and use the one that works
            let result;
            let error = null;
            
            // First try: assume function takes individual arguments (e.g., add(a, b))
            if (Array.isArray(testInput)) {{
                try {{
                    result = {func_name}(...testInput);
                }} catch (e1) {{
                    error = e1;
                    // If spreading fails, it's likely the function expects the array itself
                    try {{
                        result = {func_name}(testInput);
                        error = null;
                    }} catch (e2) {{
                        error = e2;
                    }}
                }}
            }} else {{
                // Single argument or non-array input
                result = {func_name}(testInput);
            }}
            
            if (error) {{
                console.log(`ERROR: ${{error.message}}`);
            }} else {{
                console.log(JSON.stringify(result));
            }}
        }} catch (e) {{
            console.log(`ERROR: ${{e.message}}`);
        }}
    }});
}});
"""
        
        elif language == 'java':
            # Java batch template
            batch_code = f"""
import java.util.*;
import java.io.*;
import java.math.*;

public class Main {{
    {clean_code}
    
    public static void main(String[] args) throws IOException {{
        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
        String line;
        
        while ((line = br.readLine()) != null) {{
            line = line.trim();
            if (!line.isEmpty()) {{
                try {{
                    // Parse input array
                    String[] parts = line.replace("[", "").replace("]", "").split(",");
                    int[] testInput = new int[parts.length];
                    for (int i = 0; i < parts.length; i++) {{
                        testInput[i] = Integer.parseInt(parts[i].trim());
                    }}
                    
                    int result = {func_name}(testInput);
                    System.out.println(result);
                }} catch (Exception e) {{
                    System.out.println("ERROR: " + e.getMessage());
                }}
            }}
        }}
    }}
}}
"""
        
        elif language == 'cpp':
            # C++ batch template
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
            // Parse input vector [1,2,3] format
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
        
        # Prepare input data for all test cases
        input_lines = []
        for test_case in test_cases:
            test_input = test_case.get('input', [])
            # Convert string input to proper data type
            if isinstance(test_input, str):
                try:
                    test_input = json.loads(test_input)
                except:
                    pass  # Keep as string if not valid JSON
            
            if language in ['python', 'javascript']:
                input_lines.append(json.dumps(test_input))
            else:  # java, cpp
                input_lines.append(str(test_input))
        
        stdin_data = '\n'.join(input_lines)
        
        # Prepare Piston API request
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
            'compile_timeout': 8000,  # 8 seconds
            'run_timeout': 10000,     # 10 seconds
            'compile_memory_limit': -1,
            'run_memory_limit': -1
        }
        
        # Execute batch request
        response = requests.post(
            f'{PISTON_API}/execute',
            headers={'Content-Type': 'application/json'},
            json=piston_request,
            timeout=20  # Generous timeout for batch execution
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
        
        # Check for compilation errors
        if result.get('compile', {}).get('stderr'):
            return {
                'success': False,
                'error': f'Compilation error: {result["compile"]["stderr"]}',
                'tests_passed': 0,
                'total_tests': len(test_cases),
                'test_results': []
            }
        
        # Check for runtime errors
        if result.get('run', {}).get('stderr'):
            return {
                'success': False,
                'error': f'Runtime error: {result["run"]["stderr"]}',
                'tests_passed': 0,
                'total_tests': len(test_cases),
                'test_results': []
            }
        
        # Parse batch output
        output = result.get('run', {}).get('stdout', '').strip()
        output_lines = output.split('\n') if output else []
        
        # Process results for each test case
        test_results = []
        tests_passed = 0
        
        for i, test_case in enumerate(test_cases):
            expected = test_case.get('expected_output') or test_case.get('expected', '')
            
            if i < len(output_lines):
                actual = output_lines[i].strip()
                
                # Check for error output
                if actual.startswith('ERROR:'):
                    test_results.append({
                        'test_number': i + 1,
                        'passed': False,
                        'error': actual,
                        'output': None,
                        'expected': expected
                    })
                else:
                    # Parse JSON output and compare properly
                    try:
                        # Try to parse the JSON output back to Python object
                        parsed_actual = json.loads(actual)
                    except (json.JSONDecodeError, ValueError):
                        # If JSON parsing fails, check if it's a special case like "null" or "None"
                        actual_lower = actual.lower().strip()
                        if actual_lower == 'none':
                            parsed_actual = None
                        elif actual_lower == 'null':
                            parsed_actual = None
                        else:
                            # If not valid JSON, treat as string
                            parsed_actual = actual
                    
                    # Smart comparison that handles different data types
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
                # Missing output for this test case
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
        
        # Cache successful batch execution
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

@app.route('/api/user/<username>')
def get_user_info(username):
    """Get user information"""
    try:
        user = get_user_by_username(username)
        if not user:
            # Create new user if doesn't exist
            user = create_user(username)
            
        return jsonify({
            'success': True,
            'user': user
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/challenges', methods=['POST'])
def add_challenge():
    """Add a new challenge"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['language', 'difficulty', 'title', 'description', 'buggy_code', 'solution', 'test_cases']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Validate test cases
        if len(data['test_cases']) < 3:
            return jsonify({
                'success': False,
                'error': 'At least 3 test cases are required'
            }), 400

        # Validate language
        if data['language'] not in PISTON_LANGUAGES:
            return jsonify({
                'success': False,
                'error': f'Unsupported language. Must be one of: {", ".join(PISTON_LANGUAGES.keys())}'
            }), 400

        # Validate difficulty
        valid_difficulties = ['basic', 'intermediate', 'advanced']
        if data['difficulty'].lower() not in valid_difficulties:
            return jsonify({
                'success': False,
                'error': f'Invalid difficulty. Must be one of: {", ".join(valid_difficulties)}'
            }), 400

        # TODO: Add the challenge to the database
        # This will be implemented when we add the database function
        
        return jsonify({
            'success': True,
            'message': 'Challenge added successfully',
            'data': {
                'title': data['title'],
                'language': data['language'],
                'difficulty': data['difficulty']
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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
    return redirect('/home')

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