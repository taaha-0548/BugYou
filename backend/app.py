"""
BugYou Flask Backend API
Integrates database with frontend for complete debugging challenge platform
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
from datetime import datetime
import os
import re
import time
from functools import wraps
import json
import hashlib
# from concurrent.futures import ThreadPoolExecutor  # Removed - using sequential execution to avoid rate limiting

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
    'assets': '../Assets'  # Assets directory
}

# Configuration
PISTON_API = 'https://emkc.org/api/v2/piston'

# Simple in-memory cache for frequently accessed data
_cache = {}
_cache_timeout = 300  # 5 minutes

# Cache for code execution results
_execution_cache = {}
_execution_cache_timeout = 60  # 1 minute

# Language configuration for Piston API
PISTON_LANGUAGES = {
    'python': {
        'lang': 'python',
        'version': '3.10.0',
        'filename': 'main.py',
        'template': '''
import sys
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

{user_code}

# Test case execution
test_input = {test_input}
result = {func_name}(test_input)
print(result)
'''
    },
    'javascript': {
        'lang': 'javascript',
        'version': '18.15.0',
        'filename': 'main.js',
        'template': '''
// Common utility functions
const gcd = (a, b) => b === 0 ? a : gcd(b, a % b);
const lcm = (a, b) => (a * b) / gcd(a, b);
const isPrime = n => n > 1 && Array.from({{length: Math.sqrt(n)}}, (_, i) => i + 2).every(i => n % i !== 0);

{user_code}

// Test case execution
const testInput = {test_input};
const result = {func_name}(testInput);
console.log(result);
'''
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
    """Clear the API cache"""
    global _cache
    _cache = {}
    return jsonify({
        'success': True,
        'message': 'Cache cleared successfully',
        'timestamp': datetime.now().isoformat()
    })

# ================================
# SERVE FRONTEND
# ================================

@app.route('/')
def serve_frontend():
    """Serve the main frontend page"""
    return send_from_directory(STATIC_FOLDERS['main'], 'index.html')

@app.route('/login')
def serve_login():
    """Serve the login page"""
    return send_from_directory(STATIC_FOLDERS['login'], 'login.html')

@app.route('/signup')
def serve_signup():
    """Serve the signup page"""
    return send_from_directory(STATIC_FOLDERS['signup'], 'signup.html')

@app.route('/admin')
def serve_admin():
    """Serve the admin page"""
    return send_from_directory(STATIC_FOLDERS['admin'], 'admin.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve files from Assets directory"""
    try:
        return send_from_directory('../Assets', filename)
    except Exception as e:
        print(f"Error serving asset {filename}: {str(e)}")
        return f"Asset {filename} not found", 404

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, etc.)"""
    # First try to serve from the current page's directory
    current_page = request.path.split('/')[1]  # Get the first part of the path
    if current_page in ['login', 'signup', 'admin']:
        folder = STATIC_FOLDERS[current_page]
        if os.path.exists(os.path.join(folder, filename)):
            return send_from_directory(folder, filename)
    
    # Then try other static folders
    for folder_name, folder_path in STATIC_FOLDERS.items():
        if os.path.exists(os.path.join(folder_path, filename)):
            return send_from_directory(folder_path, filename)
    
    # If file not found in any directory, return 404
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
            
        # Run each test case
        test_results = []
        tests_passed = 0
        
        # Run test cases sequentially to avoid rate limiting
        for i, test_case in enumerate(test_cases):
            result = execute_single_test(
                code=code,
                config={'lang': language},
                test_input=test_case['input'],
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
        
        # Run validation against all test cases
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
                result = execute_single_test(
                    code=code,
                    config=lang_config,
                    test_input=test_case['input'],
                    expected=test_case.get('expected'),
                    test_number=test_case['number'],
                    challenge=challenge,
                    func_name=func_name
                )
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
            # Use proper null values for each language
            null_value = 'None' if language == 'python' else 'null'
            test_code = lang_config['template'].format(
                user_code=clean_code,
                test_input=null_value,
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
            print(f"Warning: Unsupported language for function extraction: {language}")
            return None
            
        pattern = patterns[language]
        matches = re.findall(pattern, code, re.MULTILINE)
        
        if matches:
            # Return the first function found
            func_name = matches[0]
            print(f"Extracted function name '{func_name}' for {language}")
            return func_name
        else:
            print(f"No function found in {language} code using pattern: {pattern}")
            print(f"Code preview: {code[:200]}...")
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
    # Run each test case
    test_results = []
    tests_passed = 0
    total_tests = len(challenge['test_cases']) if 'test_cases' in challenge else 0
    for i, test_case in enumerate(challenge.get('test_cases', [])):
        result = execute_single_test(
            code=code,
            config=config,
            test_input=test_case['input'],
            expected=test_case.get('expected_output') or test_case.get('expected', ''),
            test_number=i + 1,
            challenge=challenge,
            func_name=func_name  # Pass the already extracted function name
        )
        if result['passed']:
            tests_passed += 1
        test_results.append(result)
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
    """Convert test input to language-specific format"""
    try:
        # Clean the input string
        test_input = str(test_input).strip()
        
        # For most languages, [1,2,3] works fine
        if language == 'python':
            return test_input
            
        elif language == 'javascript':
            # JavaScript: convert None to null
            if test_input.lower() == 'none':
                return 'null'
            return test_input
            
        elif language == 'java':
            # Java: convert [1,2,3] to {1,2,3} for array initialization
            return test_input.replace('[', '{').replace(']', '}')
            
        elif language == 'cpp':
            # C++: Handle different input types with improved validation
            test_input = test_input.strip()
            
            # Handle empty or null inputs - provide default vector
            if not test_input or test_input in [None, '', 'None', 'none', 'null']:
                return '{1, 2, 3}'  # Default test vector
            
            # If it's a string literal, keep quotes
            if test_input.startswith('"') and test_input.endswith('"'):
                return test_input
            
            # If it's a single number, return as-is
            try:
                # Try to parse as number
                if '.' in test_input:
                    float(test_input)
                    return test_input
                else:
                    int(test_input)
                    return test_input
            except ValueError:
                pass
            
            # If it's an array [1,2,3], convert to C++ vector {1,2,3}
            if test_input.startswith('[') and test_input.endswith(']'):
                content = test_input[1:-1].strip()
                if content:  # Non-empty array
                    return '{' + content + '}'
                else:  # Empty array []
                    return '{1, 2, 3}'  # Default for empty arrays
            
            # If it's already in C++ format {1,2,3}, validate and clean
            if test_input.startswith('{') and test_input.endswith('}'):
                content = test_input[1:-1].strip()
                if content and content != '{}':  # Valid non-empty content
                    return test_input
                else:  # Empty or malformed content
                    return '{1, 2, 3}'  # Default for empty/malformed
            
            # Handle special edge cases that could cause compilation errors
            if test_input in ['{}', '[]', '{}', '{{}}']:
                return '{1, 2, 3}'  # Default for problematic inputs
            
            # Default: assume it's meant to be a vector and wrap it
            return '{' + test_input + '}'
            
        return test_input
        
    except Exception as e:
        print(f"Error converting input format: {e}")
        return test_input

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
        
        # Execute with minimal retry logic for critical failures only
        import time
        max_retries = 2  # Reduced from 3
        base_delay = 0.5  # Reduced from 1 second
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f'{PISTON_API}/execute',
                    headers={'Content-Type': 'application/json'},
                    json=piston_request,
                    timeout=8  # Reduced from 10
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
        
        # Compare with expected output
        passed = compare_outputs(actual_output, expected)
        
        return {
            'test_number': test_number,
            'passed': passed,
            'error': None,
            'output': actual_output,
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