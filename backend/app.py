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
import random
import time
from functools import wraps

# Import our database functions
from database_config import (
    get_challenges_by_language_difficulty, 
    get_challenge_by_id,
    get_user_by_username,
    create_user,
    test_connection,
    get_all_available_challenges,
    CHALLENGE_TABLES
)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
PISTON_API = 'https://emkc.org/api/v2/piston'

# Simple in-memory cache for frequently accessed data
_cache = {}
_cache_timeout = 300  # 5 minutes

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

# ================================
# SERVE FRONTEND
# ================================

@app.route('/')
def serve_frontend():
    """Serve the main frontend page"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, etc.)"""
    return send_from_directory('../frontend', filename)

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
            'language': language,
            'difficulty': difficulty,
            'response_time': f'{response_time:.3f}s'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/challenge/<language>/<difficulty>/<int:challenge_id>')
def get_challenge_details(language, difficulty, challenge_id):
    """Get detailed challenge information including test cases and hints"""
    start_time = time.time()
    try:
        challenge = get_challenge_by_id(language, difficulty, challenge_id)
        response_time = time.time() - start_time
        if challenge:
            challenge_data = dict(challenge)
            challenge_data['difficulty'] = difficulty
            challenge_data['language'] = language
            # Ensure 'hints' field is present and is a list
            hints = challenge_data.get('hints', [])
            if isinstance(hints, str):
                import json
                try:
                    hints = json.loads(hints)
                except Exception:
                    hints = []
            if not isinstance(hints, list):
                hints = []
            challenge_data['hints'] = hints
            return jsonify({
                'success': True,
                'challenge': challenge_data,
                'response_time': f'{response_time:.3f}s'
            })
        else:
            return jsonify({'success': False, 'error': 'Challenge not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/execute', methods=['POST'])
def execute_code():
    """Execute user code via Piston API"""
    try:
        data = request.get_json()
        code = data.get('code')
        language = data.get('language')
        
        if not code or not language:
            return jsonify({'success': False, 'error': 'Code and language required'}), 400
        
        # Map language names to Piston API format
        lang_map = {
            'python': {'lang': 'python', 'filename': 'main.py'},
            'javascript': {'lang': 'javascript', 'filename': 'main.js'},
            'java': {'lang': 'java', 'filename': 'Main.java'},
            'cpp': {'lang': 'cpp', 'filename': 'main.cpp'}
        }
        
        if language not in lang_map:
            return jsonify({'success': False, 'error': 'Unsupported language'}), 400
        
        config = lang_map[language]
        
        # Prepare Piston API request
        piston_request = {
            'language': config['lang'],
            'version': '*',
            'files': [{'name': config['filename'], 'content': code}]
        }
        
        # Execute code via Piston API
        response = requests.post(
            f'{PISTON_API}/execute',
            headers={'Content-Type': 'application/json'},
            json=piston_request,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'success': True,
                'result': result
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Execution failed: {response.status_code}'
            }), 500
            
    except requests.RequestException as e:
        return jsonify({'success': False, 'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/validate', methods=['POST'])
def validate_submission():
    """Validate user submission against test cases"""
    try:
        data = request.get_json()
        code = data.get('code')
        language = data.get('language')
        difficulty = data.get('difficulty')
        challenge_id = data.get('challenge_id')
        
        if not all([code, language, difficulty, challenge_id]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Get challenge details with test cases
        challenge = get_challenge_by_id(language, difficulty, challenge_id)
        if not challenge:
            return jsonify({'success': False, 'error': 'Challenge not found'}), 404
        
        # Run validation against all test cases
        results = run_test_validation(code, language, challenge)
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def check_code_compilation(code, language, config):
    """Check if code compiles without running it"""
    try:
        # Prepare Piston API request for compilation check
        piston_request = {
            'language': config['lang'],
            'version': '*',
            'files': [{'name': config['filename'], 'content': code}],
            'compile_timeout': 5000,  # 5 seconds
            'run_timeout': 0,  # Don't run, just compile
            'compile_memory_limit': -1,
            'run_memory_limit': -1
        }
        
        # Execute compilation via Piston API
        response = requests.post(
            f'{PISTON_API}/execute',
            headers={'Content-Type': 'application/json'},
            json=piston_request,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'compiles': not bool(result.get('compile', {}).get('stderr')),
                'error': result.get('compile', {}).get('stderr', '')
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
        # Prepare test code with input
        test_code = code + f"\n\n# Test case {test_number}\n"
        test_code += f"test_input = {test_input}\n"
        test_code += f"result = {extract_function_name(code, config['lang'])}(test_input)\n"
        test_code += "print(result)"
        
        # Execute via Piston API
        piston_request = {
            'language': config['lang'],
            'version': '*',
            'files': [{'name': config['filename'], 'content': test_code}],
            'compile_timeout': 5000,  # 5 seconds
            'run_timeout': 5000,  # 5 seconds
            'compile_memory_limit': -1,
            'run_memory_limit': -1
        }
        
        response = requests.post(
            f'{PISTON_API}/execute',
            headers={'Content-Type': 'application/json'},
            json=piston_request,
            timeout=10
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
        
        # Check for runtime errors
        if result.get('run', {}).get('stderr'):
            return {
                'test_number': test_number,
                'passed': False,
                'error': result['run']['stderr'],
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

@app.route('/api/challenge/random', methods=['GET'])
@app.route('/api/challenge/random/<language>', methods=['GET'])
def get_random_challenge(language=None):
    """Get a random challenge, optionally filtered by language, always include hints"""
    try:
        # Get all challenges
        all_challenges = get_all_available_challenges()
        if not all_challenges:
            return jsonify({'success': False, 'error': 'No challenges available'}), 404
            
        # Filter by language if specified
        if language:
            filtered_challenges = [c for c in all_challenges if c['language'] == language]
            if not filtered_challenges:
                return jsonify({'success': False, 'error': f'No challenges available for {language}'}), 404
            challenges = filtered_challenges
        else:
            challenges = all_challenges
            
        # Select random challenge
        challenge = random.choice(challenges)
        
        # Get full challenge details
        full_challenge = get_challenge_by_id(
            challenge['language'],
            challenge['difficulty'],
            challenge['challenge_id']
        )
        
        if full_challenge:
            challenge_data = dict(full_challenge)
            challenge_data['difficulty'] = challenge['difficulty']
            challenge_data['language'] = challenge['language']
            hints = challenge_data.get('hints', [])
            if isinstance(hints, str):
                import json
                try:
                    hints = json.loads(hints)
                except Exception:
                    hints = []
            if not isinstance(hints, list):
                hints = []
            challenge_data['hints'] = hints
            return jsonify({
                'success': True,
                'challenge': challenge_data,
                'random_info': {
                    'language': challenge['language'],
                    'difficulty': challenge['difficulty'],
                    'challenge_id': challenge['challenge_id']
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Challenge details not found'}), 404
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