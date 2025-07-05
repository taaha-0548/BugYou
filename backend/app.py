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

# Import our database functions
from database_config import (
    get_challenges_by_language_difficulty, 
    get_challenge_by_id,
    get_user_by_username,
    save_user_submission_v2,
    get_leaderboard,
    test_connection,
    get_all_available_challenges,
    CHALLENGE_TABLES
)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Configuration
PISTON_API = 'https://emkc.org/api/v2/piston'

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
    db_status = test_connection()
    return jsonify({
        'status': 'healthy',
        'database': 'connected' if db_status else 'disconnected',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/challenges')
def get_challenges():
    """Get all available challenges"""
    try:
        challenges = get_all_available_challenges()
        return jsonify({
            'success': True,
            'challenges': challenges,
            'count': len(challenges)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/challenges/<language>/<difficulty>')
def get_challenges_by_lang_diff(language, difficulty):
    """Get challenges for specific language and difficulty"""
    try:
        challenges = get_challenges_by_language_difficulty(language, difficulty)
        return jsonify({
            'success': True,
            'challenges': challenges,
            'language': language,
            'difficulty': difficulty
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/challenge/<language>/<difficulty>/<int:challenge_id>')
def get_challenge_details(language, difficulty, challenge_id):
    """Get detailed challenge information including test cases"""
    try:
        challenge = get_challenge_by_id(language, difficulty, challenge_id)
        if challenge:
            # Convert to dict and remove hidden test cases from response
            challenge_data = dict(challenge)
            
            # Ensure difficulty and language fields are present
            challenge_data['difficulty'] = difficulty
            challenge_data['language'] = language
            
            # Remove hidden test case data from response
            hidden_fields = [f'hidden_test_{i}_{field}' for i in range(1, 5) for field in ['input', 'expected', 'description']]
            for field in hidden_fields:
                challenge_data.pop(field, None)
            
            return jsonify({
                'success': True,
                'challenge': challenge_data
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
        user_id = data.get('user_id', 1)  # Default to admin user for now
        
        if not all([code, language, difficulty, challenge_id]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Get challenge details with test cases
        challenge = get_challenge_by_id(language, difficulty, challenge_id)
        if not challenge:
            return jsonify({'success': False, 'error': 'Challenge not found'}), 404
        
        # Run validation against all test cases
        results = run_test_validation(code, language, challenge)
        
        # Save submission to database
        if results['total_tests'] > 0:
            submission = save_user_submission_v2(
                user_id=user_id,
                language=language,
                difficulty=difficulty,
                challenge_id=challenge_id,
                submitted_code=code,
                score=results['score'],
                tests_passed=results['passed_tests'],
                total_tests=results['total_tests'],
                hints_used=data.get('hints_used', 0),
                attempts=data.get('attempts', 1)
            )
            results['submission_id'] = submission['submission_id']
        
        return jsonify({
            'success': True,
            'validation': results
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def check_code_compilation(code, language, config):
    """Check if code compiles/runs properly before testing"""
    try:
        # Create a simple compilation test
        if language == 'python':
            # For Python, try to compile the code
            test_code = f"{code}\n\n# Compilation test\nprint('COMPILATION_SUCCESS')"
        elif language == 'javascript':
            # For JavaScript, try to run basic syntax check
            test_code = f"{code}\n\n// Compilation test\nconsole.log('COMPILATION_SUCCESS');"
        elif language == 'java':
            # For Java, try to compile the class
            test_code = f"{code}\n\n// Compilation test\npublic static void main(String[] args) {{\n    System.out.println(\"COMPILATION_SUCCESS\");\n}}"
        elif language == 'cpp':
            # For C++, try to compile
            test_code = f"{code}\n\n// Compilation test\nint main() {{\n    std::cout << \"COMPILATION_SUCCESS\" << std::endl;\n    return 0;\n}}"
        else:
            test_code = code

        # Execute compilation test
        piston_request = {
            'language': config['lang'],
            'version': '*',
            'files': [{'name': config['filename'], 'content': test_code}]
        }
        
        response = requests.post(
            f'{PISTON_API}/execute',
            headers={'Content-Type': 'application/json'},
            json=piston_request,
            timeout=10
        )
        
        if response.status_code == 200:
            execution_result = response.json()
            
            # Check for compilation errors
            stderr = execution_result.get('run', {}).get('stderr', '')
            stdout = execution_result.get('run', {}).get('stdout', '')
            
            # Check for compilation/syntax errors
            if stderr and any(error_keyword in stderr.lower() for error_keyword in [
                'syntaxerror', 'syntax error', 'indentationerror', 'nameerror',
                'error:', 'exception:', 'traceback', 'compile error',
                'compilation failed', 'cannot find symbol'
            ]):
                return {
                    'status': 'failed',
                    'error': f'Compilation/Syntax Error:\n{stderr.strip()}'
                }
            
            # Check if basic execution worked
            if 'COMPILATION_SUCCESS' in stdout or not stderr:
                return {'status': 'success', 'error': None}
            else:
                return {
                    'status': 'failed',
                    'error': f'Code execution failed:\n{stderr.strip() if stderr else "Unknown execution error"}'
                }
        else:
            return {
                'status': 'failed',
                'error': f'Execution service error: HTTP {response.status_code}'
            }
            
    except requests.RequestException as e:
        return {
            'status': 'failed',
            'error': f'Network error during compilation check: {str(e)}'
        }
    except Exception as e:
        return {
            'status': 'failed',
            'error': f'Unexpected error during compilation check: {str(e)}'
        }

def extract_function_name(code, language):
    """Extract function name from code dynamically"""
    if language == 'python':
        match = re.search(r'def\s+(\w+)\s*\(', code)
        return match.group(1) if match else 'main_function'
        
    elif language == 'javascript':
        match = re.search(r'function\s+(\w+)\s*\(', code) or re.search(r'const\s+(\w+)\s*=') or re.search(r'let\s+(\w+)\s*=')
        return match.group(1) if match else 'main_function'
        
    elif language == 'java':
        match = re.search(r'public\s+static\s+\w+\s+(\w+)\s*\(', code)
        return match.group(1) if match else 'main_function'
        
    elif language == 'cpp':
        match = re.search(r'\w+\s+(\w+)\s*\([^)]*\)\s*{', code) or re.search(r'(\w+)\s*\([^)]*\)\s*{', code)
        if match and match.group(1) not in ['main', 'int', 'void', 'string', 'using', 'include']:
            return match.group(1)
        return 'calculateSum'  # fallback for C++
        
    return 'main_function'

def run_test_validation(code, language, challenge):
    """Run user code against all test cases and return detailed results"""
    results = {
        'passed_tests': 0,
        'total_tests': 0,
        'score': 0,
        'test_results': [],
        'hidden_tests_passed': 0,
        'hidden_tests_total': 0,
        'compilation_status': 'unknown',
        'compilation_error': None
    }
    
    # Map language to execution config
    lang_map = {
        'python': {'lang': 'python', 'filename': 'main.py'},
        'javascript': {'lang': 'javascript', 'filename': 'main.js'},
        'java': {'lang': 'java', 'filename': 'Main.java'},
        'cpp': {'lang': 'cpp', 'filename': 'main.cpp'}
    }
    
    config = lang_map.get(language)
    if not config:
        results['compilation_error'] = f'Unsupported language: {language}'
        return results
    
    # STEP 1: Check if code compiles/runs properly
    compilation_result = check_code_compilation(code, language, config)
    results['compilation_status'] = compilation_result['status']
    
    if compilation_result['status'] == 'failed':
        results['compilation_error'] = compilation_result['error']
        return results  # Don't run tests if compilation fails
    
    # Extract function name dynamically
    function_name = extract_function_name(code, language)
    
    # Test visible test cases
    for i in range(1, 6):
        test_input = challenge.get(f'test_case_{i}_input')
        expected = challenge.get(f'test_case_{i}_expected')
        weight = challenge.get(f'test_case_{i}_weight', 1)
        description = challenge.get(f'test_case_{i}_description', f'Test case {i}')
        
        if test_input and expected:
            results['total_tests'] += 1
            
            # Create test code by calling the function with test input
            if language == 'python':
                test_code = f"{code}\n\n# Test case {i}\nresult = {function_name}({test_input})\nprint(result)"
            elif language == 'javascript':
                test_code = f"{code}\n\n// Test case {i}\nconst result = {function_name}({test_input});\nconsole.log(result);"
            elif language == 'java':
                # Convert array notation [1,2,3] to {1,2,3} for Java
                java_input = test_input.replace('[', '{').replace(']', '}')
                test_code = f"{code}\n\n// Test case {i}\npublic static void testCase{i}() {{\n    int[] testArray = {java_input};\n    int result = {function_name}(testArray);\n    System.out.println(result);\n}}\n\npublic static void main(String[] args) {{\n    testCase{i}();\n}}"
            elif language == 'cpp':
                # Handle C++ vector initialization
                if test_input == '[]':
                    test_code = f"{code}\n\n// Test case {i}\nint main() {{\n    vector<int> testVector;\n    int result = {function_name}(testVector);\n    cout << result << endl;\n    return 0;\n}}"
                else:
                    cpp_input = test_input.replace('[', '{').replace(']', '}')
                    test_code = f"{code}\n\n// Test case {i}\nint main() {{\n    vector<int> testVector{cpp_input};\n    int result = {function_name}(testVector);\n    cout << result << endl;\n    return 0;\n}}"
            else:
                test_code = code  # Basic fallback
            
            # Execute test
            test_result = execute_single_test(test_code, config, test_input, expected, weight, description, i, challenge)
            results['test_results'].append(test_result)
            
            if test_result['passed']:
                results['passed_tests'] += 1
                results['score'] += weight
    
    return results

def execute_single_test(test_code, config, test_input, expected, weight, description, test_number, challenge):
    """Execute a single test case with detailed error handling"""
    try:
        piston_request = {
            'language': config['lang'],
            'version': '*',
            'files': [{'name': config['filename'], 'content': test_code}]
        }
        
        response = requests.post(
            f'{PISTON_API}/execute',
            headers={'Content-Type': 'application/json'},
            json=piston_request,
            timeout=5
        )
        
        if response.status_code == 200:
            execution_result = response.json()
            stdout = execution_result.get('run', {}).get('stdout', '').strip()
            stderr = execution_result.get('run', {}).get('stderr', '').strip()
            
            # Check for runtime errors
            if stderr and any(error_keyword in stderr.lower() for error_keyword in [
                'error:', 'exception:', 'traceback', 'runtime error', 'zerodivisionerror',
                'typeerror', 'valueerror', 'indexerror', 'keyerror', 'attributeerror'
            ]):
                return {
                    'test_case': test_number,
                    'input': test_input,
                    'expected': expected,
                    'actual': f'Runtime Error: {stderr}',
                    'passed': False,
                    'weight': weight,
                    'description': description,
                    'error_type': 'runtime'
                }
            
            # If no errors, compare the output
            actual_output = stdout
            passed = compare_outputs(actual_output, expected, challenge.get('output_comparison_type', 'exact'))
            
            return {
                'test_case': test_number,
                'input': test_input,
                'expected': expected,
                'actual': actual_output,
                'passed': passed,
                'weight': weight,
                'description': description,
                'error_type': 'none' if passed else 'output_mismatch'
            }
        else:
            return {
                'test_case': test_number,
                'input': test_input,
                'expected': expected,
                'actual': f'Execution Service Error (HTTP {response.status_code})',
                'passed': False,
                'weight': weight,
                'description': description,
                'error_type': 'service'
            }
            
    except requests.RequestException as e:
        return {
            'test_case': test_number,
            'input': test_input,
            'expected': expected,
            'actual': f'Network Error: {str(e)}',
            'passed': False,
            'weight': weight,
            'description': description,
            'error_type': 'network'
        }
    except Exception as e:
        return {
            'test_case': test_number,
            'input': test_input,
            'expected': expected,
            'actual': f'Unexpected Error: {str(e)}',
            'passed': False,
            'weight': weight,
            'description': description,
            'error_type': 'unexpected'
        }

def compare_outputs(actual, expected, comparison_type='exact'):
    """Compare actual vs expected output based on comparison type"""
    if comparison_type == 'exact':
        return str(actual).strip() == str(expected).strip()
    elif comparison_type == 'numeric':
        try:
            return abs(float(actual) - float(expected)) < 0.000001
        except (ValueError, TypeError):
            return str(actual).strip() == str(expected).strip()
    elif comparison_type == 'ignore_whitespace':
        return ''.join(str(actual).split()) == ''.join(str(expected).split())
    else:
        return str(actual).strip() == str(expected).strip()

@app.route('/api/user/<username>')
def get_user_info(username):
    """Get user information"""
    try:
        user = get_user_by_username(username)
        if user:
            # Don't send password hash
            user_data = dict(user)
            user_data.pop('password_hash', None)
            return jsonify({
                'success': True,
                'user': user_data
            })
        else:
            return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/leaderboard')
def api_leaderboard():
    """Get leaderboard data"""
    try:
        limit = request.args.get('limit', 10, type=int)
        leaderboard_data = get_leaderboard(limit)
        return jsonify({
            'success': True,
            'leaderboard': leaderboard_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin')
def admin_page():
    """Serve the admin page for adding challenges"""
    return send_from_directory('../frontend', 'add_challenge.html')

@app.route('/api/admin/add-challenge', methods=['POST'])
def add_challenge():
    """Add a new challenge to the database"""
    try:
        from database_config import DatabaseManager, get_table_name
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['language', 'difficulty', 'title', 'description', 'buggyCode', 
                          'testCase1Input', 'testCase1Expected', 'testCase2Input', 'testCase2Expected',
                          'testCase3Input', 'testCase3Expected']
        
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Get table name
        try:
            table_name = get_table_name(data['language'], data['difficulty'])
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        
        # Insert challenge into database
        db = DatabaseManager()
        
        # Debug: Print what we're trying to insert
        print(f"🔍 DEBUG: Inserting challenge into {table_name}")
        print(f"   Title: {data['title']}")
        print(f"   Problem Statement: {data.get('problemStatement', 'NOT PROVIDED')}")
        print(f"   Test Case 1 Input: {data.get('testCase1Input', 'NOT PROVIDED')}")
        
        # Fixed INSERT query to match exact database schema
        insert_query = f"""
            INSERT INTO {table_name} (
                title, description, problem_statement, buggy_code,
                reference_solution, solution_explanation,
                hint_1, hint_2, hint_3,
                learning_objectives, common_mistakes, tips,
                test_case_1_input, test_case_1_expected, test_case_1_description, test_case_1_weight,
                test_case_2_input, test_case_2_expected, test_case_2_description, test_case_2_weight,
                test_case_3_input, test_case_3_expected, test_case_3_description, test_case_3_weight,
                test_case_4_input, test_case_4_expected, test_case_4_description, test_case_4_weight,
                test_case_5_input, test_case_5_expected, test_case_5_description, test_case_5_weight,
                hidden_test_1_input, hidden_test_1_expected,
                hidden_test_2_input, hidden_test_2_expected
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING challenge_id
        """
        
        # Ensure required fields are never None/null
        problem_statement = data.get('problemStatement')
        if not problem_statement or problem_statement.strip() == '':
            problem_statement = f"This challenge focuses on {data['title'].lower()}. Students need to identify and fix the bug in the provided code."
        
        test_case_1_input = data.get('testCase1Input')
        if not test_case_1_input or test_case_1_input.strip() == '':
            raise ValueError("Test Case 1 Input is required but was empty")
            
        test_case_1_expected = data.get('testCase1Expected') 
        if not test_case_1_expected or test_case_1_expected.strip() == '':
            raise ValueError("Test Case 1 Expected output is required but was empty")
            
        test_case_2_input = data.get('testCase2Input')
        if not test_case_2_input or test_case_2_input.strip() == '':
            raise ValueError("Test Case 2 Input is required but was empty")
            
        test_case_2_expected = data.get('testCase2Expected')
        if not test_case_2_expected or test_case_2_expected.strip() == '':
            raise ValueError("Test Case 2 Expected output is required but was empty")
            
        test_case_3_input = data.get('testCase3Input')
        if not test_case_3_input or test_case_3_input.strip() == '':
            raise ValueError("Test Case 3 Input is required but was empty")
            
        test_case_3_expected = data.get('testCase3Expected')
        if not test_case_3_expected or test_case_3_expected.strip() == '':
            raise ValueError("Test Case 3 Expected output is required but was empty")
        
        values = (
            data['title'],
            data['description'],
            problem_statement,
            data['buggyCode'],
            data.get('referenceSolution', '# Reference solution not provided'),
            data.get('solutionExplanation', 'The solution involves fixing the identified bug in the code.'),
            data.get('hint1', 'Carefully examine the code logic and look for common programming errors.'),
            data.get('hint2', 'Pay attention to variable initialization, loop conditions, and data types.'),
            data.get('hint3', 'Consider edge cases and boundary conditions that might cause issues.'),
            data.get('learningObjectives', f"Students will learn debugging techniques and improve their {data['language']} programming skills."),
            data.get('commonMistakes', 'Common mistakes include off-by-one errors, uninitialized variables, and incorrect conditional logic.'),
            data.get('tips', 'Always test your code with different inputs, especially edge cases and boundary values.'),
            # Test case 1 (required)
            test_case_1_input,
            test_case_1_expected,
            data.get('testCase1Description', 'Basic test case'),
            int(data.get('testCase1Weight', 1)),
            # Test case 2 (required)
            test_case_2_input,
            test_case_2_expected,
            data.get('testCase2Description', 'Second test case'),
            int(data.get('testCase2Weight', 1)),
            # Test case 3 (required)
            test_case_3_input,
            test_case_3_expected,
            data.get('testCase3Description', 'Third test case'),
            int(data.get('testCase3Weight', 1)),
            # Test case 4 (optional)
            data.get('testCase4Input') or None,
            data.get('testCase4Expected') or None,
            data.get('testCase4Description') or None,
            int(data.get('testCase4Weight', 1)) if data.get('testCase4Input') else None,
            # Test case 5 (optional)
            data.get('testCase5Input') or None,
            data.get('testCase5Expected') or None,
            data.get('testCase5Description') or None,
            int(data.get('testCase5Weight', 1)) if data.get('testCase5Input') else None,
            # Hidden tests
            data.get('hiddenTest1Input') or None,
            data.get('hiddenTest1Expected') or None,
            data.get('hiddenTest2Input') or None,
            data.get('hiddenTest2Expected') or None
        )
        
        print(f"🔍 DEBUG: Values tuple length: {len(values)}")
        print(f"🔍 DEBUG: Query parameter count: {insert_query.count('%s')}")
        
        print(f"🔍 DEBUG: Executing INSERT query...")
        result = db.execute_query(insert_query, values, fetch_one=True)
        
        if result:
            challenge_id = result['challenge_id']
            print(f"✅ DEBUG: INSERT returned challenge_id: {challenge_id}")
            
            # Verify the challenge was actually saved
            verify_query = f"SELECT challenge_id, title, problem_statement FROM {table_name} WHERE challenge_id = %s"
            verification = db.execute_query(verify_query, (challenge_id,), fetch_one=True)
            
            if verification:
                print(f"✅ DEBUG: Challenge verified in database: '{verification['title']}'")
                return jsonify({
                    'success': True,
                    'message': f'Challenge added successfully to {table_name}',
                    'challenge_id': challenge_id,
                    'table': table_name
                })
            else:
                print(f"❌ DEBUG: Challenge {challenge_id} NOT found in database after insert!")
                return jsonify({
                    'success': False,
                    'error': f'Challenge was not saved to database (ID {challenge_id} not found)'
                }), 500
        else:
            print(f"❌ DEBUG: INSERT query returned no result")
            return jsonify({
                'success': False,
                'error': 'INSERT query did not return a challenge_id'
            }), 500
        
    except Exception as e:
        print(f"Error adding challenge: {e}")
        return jsonify({
            'success': False,
            'error': f'Database error: {str(e)}'
        }), 500

@app.route('/api/challenge/random', methods=['GET'])
@app.route('/api/challenge/random/<language>', methods=['GET'])
def get_random_challenge(language=None):
    """Get a random challenge from available challenges, optionally filtered by language"""
    try:
        # Get all available challenges
        all_challenges = []
        
        # If language is specified, filter by that language only
        if language:
            if language in CHALLENGE_TABLES:
                difficulties = CHALLENGE_TABLES[language]
                for difficulty, table_name in difficulties.items():
                    try:
                        # Get challenges from this specific language/difficulty table
                        challenges = get_challenges_by_language_difficulty(language, difficulty)
                        
                        for challenge in challenges:
                            all_challenges.append({
                                'language': language,
                                'difficulty': difficulty,
                                'challenge_id': challenge['challenge_id'],
                                'title': challenge['title'],
                                'table_name': table_name
                            })
                    except Exception as e:
                        print(f"Error getting {language} {difficulty} challenges: {e}")
                        continue
            else:
                return jsonify({
                    'success': False,
                    'error': f'Unsupported language: {language}'
                }), 400
        else:
            # Original behavior: get challenges from all languages
            for lang, difficulties in CHALLENGE_TABLES.items():
                for difficulty, table_name in difficulties.items():
                    try:
                        # Get challenges from this table
                        challenges = get_challenges_by_language_difficulty(lang, difficulty)
                        
                        for challenge in challenges:
                            all_challenges.append({
                                'language': lang,
                                'difficulty': difficulty,
                                'challenge_id': challenge['challenge_id'],
                                'title': challenge['title'],
                                'table_name': table_name
                            })
                    except Exception as e:
                        print(f"Error getting challenges from {table_name}: {e}")
                        continue
        
        if not all_challenges:
            error_msg = f'No challenges available for {language}' if language else 'No challenges available for random selection'
            return jsonify({
                'success': False,
                'error': error_msg
            }), 404
        
        # Pick a random challenge
        random_challenge_info = random.choice(all_challenges)
        
        # Get the full challenge data
        challenge = get_challenge_by_id(
            random_challenge_info['language'], 
            random_challenge_info['difficulty'], 
            random_challenge_info['challenge_id']
        )
        
        if not challenge:
            return jsonify({
                'success': False,
                'error': 'Failed to load random challenge data'
            }), 500
        
        return jsonify({
            'success': True,
            'challenge': challenge,
            'random_info': {
                'language': random_challenge_info['language'],
                'difficulty': random_challenge_info['difficulty'],
                'challenge_id': random_challenge_info['challenge_id'],
                'total_available': len(all_challenges),
                'filtered_by_language': language is not None
            }
        })
        
    except Exception as e:
        print(f"Error getting random challenge: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get random challenge: {str(e)}'
        }), 500

@app.route('/api/submit', methods=['POST'])
def submit_challenge():
    """Submit a challenge solution"""
    try:
        data = request.get_json()
        
        # Extract submission data
        challenge_id = data.get('challenge_id')
        language = data.get('language')
        difficulty = data.get('difficulty')
        code = data.get('code')
        score = data.get('score', 0)
        attempts = data.get('attempts', 1)
        hints_used = data.get('hints_used', 0)
        elapsed_time = data.get('elapsed_time', 0)
        visible_tests_passed = data.get('visible_tests_passed', 0)
        visible_tests_total = data.get('visible_tests_total', 0)
        hidden_tests_passed = data.get('hidden_tests_passed', 0)
        hidden_tests_total = data.get('hidden_tests_total', 0)
        all_tests_passed = data.get('all_tests_passed', 0)
        all_tests_total = data.get('all_tests_total', 0)
        
        # Validate required fields
        if not all([challenge_id, language, difficulty, code]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: challenge_id, language, difficulty, code'
            }), 400
        
        # Default user (for now - in future this would come from authentication)
        user_id = 1  # Default admin user
        
        # Save submission to database
        submission = save_user_submission_v2(
            user_id=user_id,
            language=language,
            difficulty=difficulty,
            challenge_id=challenge_id,
            submitted_code=code,
            score=score,
            tests_passed=all_tests_passed,
            total_tests=all_tests_total,
            hints_used=hints_used,
            attempts=attempts
        )
        
        # Determine if submission was successful
        success_rate = all_tests_passed / all_tests_total if all_tests_total > 0 else 0
        is_successful = success_rate >= 0.8  # 80% pass rate for success
        
        return jsonify({
            'success': True,
            'submission_id': submission.get('submission_id'),
            'is_successful': is_successful,
            'score_achieved': score,
            'tests_passed': all_tests_passed,
            'total_tests': all_tests_total,
            'success_rate': round(success_rate * 100, 1),
            'message': f'Submission successful! {all_tests_passed}/{all_tests_total} tests passed.',
            'elapsed_time': elapsed_time
        })
        
    except Exception as e:
        print(f"Submission error: {e}")
        return jsonify({
            'success': False,
            'error': f'Submission failed: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Test database connection on startup
    print("🔌 Testing database connection...")
    if test_connection():
        print("✅ Database connected successfully!")
    else:
        print("❌ Database connection failed!")
        print("💡 Make sure PostgreSQL is running and check database_config.py")
    
    print("🚀 Starting BugYou Flask server...")
    print("📍 Frontend: http://localhost:5000")
    print("🔗 API Health: http://localhost:5000/api/health")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 