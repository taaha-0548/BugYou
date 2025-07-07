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
from concurrent.futures import ThreadPoolExecutor

# Import our database functions
from database_config import (
    get_challenges_by_language_difficulty, 
    get_challenge_by_id,
    get_user_by_username,
    create_user,
    test_connection,
    CHALLENGE_TABLES
)

app = Flask(__name__, static_folder='../frontend')
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Enable CORS for API endpoints

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
def {func_name}(input_value):
    # User code here
    {user_code}

# Test case
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
function {func_name}(input) {{
    // User code here
    {user_code}
}}

// Test case
const test_input = {test_input};
const result = {func_name}(test_input);
console.log(result);
'''
    },
    'java': {
        'lang': 'java',
        'version': '19.0.2',
        'filename': 'Main.java',
        'template': '''
public class Main {{
    {user_code}

    public static void main(String[] args) {{
        var test_input = {test_input};
        var result = {func_name}(test_input);
        System.out.println(result);
    }}
}}
'''
    },
    'cpp': {
        'lang': 'cpp',
        'version': '11.2.0',
        'filename': 'main.cpp',
        'template': '''
#include <iostream>
#include <string>
using namespace std;

{user_code}

int main() {{
    auto test_input = {test_input};
    auto result = {func_name}(test_input);
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
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, etc.)"""
    return send_from_directory(app.static_folder, filename)

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
        
        # Run test cases in parallel for better performance
        with ThreadPoolExecutor(max_workers=min(4, len(test_cases))) as executor:
            futures = [
                executor.submit(
                    execute_single_test,
                    code=code,
                    config={'lang': language},
                    test_input=test_case['input'],
                    expected=test_case['expected_output'] or test_case['expected'],
                    test_number=i + 1,
                    challenge={'id': 0}
                )
                for i, test_case in enumerate(test_cases)
            ]
            
            for future in futures:
                result = future.result()
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
            for test_case in hidden_tests:
                result = execute_single_test(
                    code=code,
                    config=lang_map[language],
                    test_input=test_case['input'],
                    expected=test_case['expected'],
                    test_number=test_case['number'],
                    challenge=challenge
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
        
        # For interpreted languages, we'll do a syntax check
        if language in ['python', 'javascript']:
            # Create a minimal test code that just defines the function
            test_code = config['template'].format(
                func_name='test_function',
                user_code=clean_code,
                test_input='null'
            )
        else:
            # For compiled languages, we'll try to compile the full program
            test_code = config['template'].format(
                func_name=extract_function_name(code, language) or 'main',
                user_code=clean_code,
                test_input='0'  # Dummy input that should compile
            )
        
        # Execute compilation via Piston API
        piston_request = {
            'language': config['lang'],
            'version': config['version'],
            'files': [{'name': config['filename'], 'content': test_code}],
            'compile_timeout': 10000,  # 10 seconds
            'run_timeout': 0,  # Don't run, just compile
            'compile_memory_limit': -1,
            'run_memory_limit': -1
        }
        
        response = requests.post(
            f'{PISTON_API}/execute',
            headers={'Content-Type': 'application/json'},
            json=piston_request,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            compile_error = result.get('compile', {}).get('stderr', '')
            
            # For interpreted languages, runtime errors during parsing are compilation errors
            if language in ['python', 'javascript']:
                compile_error = compile_error or result.get('run', {}).get('stderr', '')
            
            return {
                'success': True,
                'compiles': not bool(compile_error),
                'error': compile_error
            }
        else:
            return {
                'success': False,
                'compiles': False,
                'error': f'Compilation check failed: {response.status_code}'
            }
            
    except Exception as e:
        return {
            'success': False,
            'compiles': False,
            'error': str(e)
        }

def extract_function_name(code, language):
    """Extract the main function name from code"""
    patterns = {
        'python': r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        'javascript': r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        'java': r'public\s+static\s+\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        'cpp': r'\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    }
    if language not in patterns:
        return None
    matches = re.findall(patterns[language], code)
    return matches[0] if matches else None


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
    for test_case in challenge.get('test_cases', []):
        result = execute_single_test(
            code=code,
            config=config,
            test_input=test_case['input'],
            expected=test_case['expected'],
            test_number=test_case['number'],
            challenge=challenge
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

def execute_single_test(code, config, test_input, expected, test_number, challenge):
    """Execute a single test case"""
    try:
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

        # Extract function name
        func_name = extract_function_name(code, config['lang'])
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
        
        # Prepare test code using template
        test_code = lang_config['template'].format(
            func_name=func_name,
            user_code=clean_code,
            test_input=test_input
        )
        
        # Execute via Piston API
        piston_request = {
            'language': lang_config['lang'],
            'version': lang_config['version'],
            'files': [
                {
                    'name': lang_config['filename'],
                    'content': test_code
                }
            ],
            'stdin': '',  # Add input if needed
            'compile_timeout': 10000,  # 10 seconds
            'run_timeout': 10000,  # 10 seconds
            'compile_memory_limit': -1,  # No limit
            'run_memory_limit': -1  # No limit
        }
        
        response = requests.post(
            f'{PISTON_API}/execute',
            headers={'Content-Type': 'application/json'},
            json=piston_request,
            timeout=15
        )
        
        if response.status_code != 200:
            return {
                'test_number': test_number,
                'passed': False,
                'error': f'Execution failed: {response.status_code}',
                'output': None,
                'expected': expected
            }
            
        result = response.json()
        
        # Check for compilation errors
        if result.get('compile', {}).get('stderr'):
            return {
                'test_number': test_number,
                'passed': False,
                'error': f'Compilation error: {result["compile"]["stderr"]}',
                'output': None,
                'expected': expected
            }
        
        # Check for runtime errors
        if result.get('run', {}).get('stderr'):
            return {
                'test_number': test_number,
                'passed': False,
                'error': f'Runtime error: {result["run"]["stderr"]}',
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
    """Remove main function and test-related code from user code"""
    if language == 'python':
        # Remove any existing test code
        lines = code.split('\n')
        clean_lines = [
            line for line in lines 
            if not any(x in line.lower() for x in ['test_input', 'print(', '#test'])
        ]
        return '\n'.join(clean_lines)
    elif language == 'javascript':
        # Remove any existing test code
        lines = code.split('\n')
        clean_lines = [
            line for line in lines 
            if not any(x in line.lower() for x in ['test_input', 'console.log(', '//test'])
        ]
        return '\n'.join(clean_lines)
    elif language == 'java':
        # Remove main method and test code
        code = re.sub(r'public\s+static\s+void\s+main\s*\([^)]*\)\s*{[^}]*}', '', code)
        return code
    elif language == 'cpp':
        # Remove main function and test code
        code = re.sub(r'int\s+main\s*\([^)]*\)\s*{[^}]*}', '', code)
        return code
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