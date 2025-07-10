#!/usr/bin/env python3

import re
import json

class ErrorHandler:
    """Enhanced error handling for different types of coding issues"""
    
    @staticmethod
    def detect_logical_indentation_issues(code, language):
        """Detect common logical mistakes that are syntactically valid but logically wrong"""
        if language == 'python':
            return ErrorHandler._detect_python_logical_issues(code)
        elif language == 'cpp':
            return ErrorHandler._detect_cpp_logical_issues(code)
        elif language == 'javascript':
            return ErrorHandler._detect_javascript_logical_issues(code)
        elif language == 'java':
            return ErrorHandler._detect_java_logical_issues(code)
        else:
            return None
    
    @staticmethod
    def _detect_cpp_logical_issues(code):
        """Detect common C++ logical issues"""
        lines = code.split('\n')
        issues = []
        
        # Pattern 1: Uninitialized variables (C++ specific - others caught by real compilers)
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Look for uninitialized int variables (only flag if they're used in loops for counting)
            if re.match(r'\s*int\s+\w+\s*;', stripped_line):
                var_match = re.search(r'int\s+(\w+)\s*;', stripped_line)
                if var_match:
                    var_name = var_match.group(1)
                    # Only flag if the variable is used in a counting pattern (common beginner mistake)
                    for j in range(i + 1, min(i + 10, len(lines))):
                        if j >= len(lines):
                            break
                        next_line = lines[j].strip()
                        if f'{var_name}++' in next_line or f'++{var_name}' in next_line:
                            issues.append({
                                'type': 'UNINITIALIZED_COUNTER',
                                'line': i + 1,
                                'message': f'Uninitialized variable error',
                                'suggestion': '',
                                'severity': 'COMPILATION',
                                'code_snippet': f'Declaration: {stripped_line}'
                            })
                            break
        
        # Pattern 2: Out-of-bounds loop conditions (i <= size() instead of i < size())
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Look for for loops with <= size() condition
            if 'for' in stripped_line and '<=' in stripped_line and 'size()' in stripped_line:
                # Check for patterns like "i <= vector.size()" or "i <= arr.size()"
                if re.search(r'\w+\s*<=\s*\w+\.size\(\)', stripped_line):
                    issues.append({
                        'type': 'OUT_OF_BOUNDS_LOOP',
                        'line': i + 1,
                        'message': f'Out of bounds error',
                        'suggestion': '',
                        'severity': 'COMPILATION',
                        'code_snippet': f'Loop: {stripped_line}'
                    })
        
        # Pattern 3: Negative array index access (dangerous in C++)
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Look for array access with negative literal indices
            if re.search(r'\w+\[-\d+\]', stripped_line):
                issues.append({
                    'type': 'NEGATIVE_INDEX_ACCESS',
                    'line': i + 1,
                    'message': f'Negative index error',
                    'suggestion': '',
                    'severity': 'COMPILATION',
                    'code_snippet': f'Array access: {stripped_line}'
                })
        
        # Pattern 3: Removed - inefficient loop detection was too aggressive
        # Code that doesn't access array elements is inefficient but not a compilation error
        
        return issues
    
    @staticmethod
    def _detect_javascript_logical_issues(code):
        """Detect common JavaScript logical issues"""
        lines = code.split('\n')
        issues = []
        
        # Pattern 1: Using = instead of === for comparison
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Look for single = in if statements (assignment instead of comparison)
            if ('if' in stripped_line and 
                re.search(r'if\s*\([^)]*[^=!<>]=\s*[^=]', stripped_line) and
                '==' not in stripped_line and '!=' not in stripped_line):
                issues.append({
                    'type': 'ASSIGNMENT_IN_CONDITION',
                    'line': i + 1,
                    'message': f'Assignment operator error',
                    'suggestion': '',
                    'severity': 'COMPILATION',
                    'code_snippet': f'Condition: {stripped_line}'
                })
        
        # Pattern 2: Return statement inside for/while loop (similar to Python)
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Check if this line starts a loop
            if (stripped_line.startswith(('for ', 'while ')) and 
                (stripped_line.endswith('{') or '{' in stripped_line)):
                
                # Look for return statements inside the loop
                brace_count = stripped_line.count('{') - stripped_line.count('}')
                
                for j in range(i + 1, min(i + 20, len(lines))):
                    if j >= len(lines):
                        break
                    next_line = lines[j]
                    next_stripped = next_line.strip()
                    
                    # Update brace count
                    brace_count += next_line.count('{') - next_line.count('}')
                    
                    # If we've closed all braces, we're out of the loop
                    if brace_count <= 0:
                        break
                    
                    # Check for return statement inside the loop
                    if next_stripped.startswith('return '):
                        # Check if this looks like it should be outside the loop
                        if any(keyword in stripped_line.lower() for keyword in ['length', 'size', '.length']):
                            issues.append({
                                'type': 'LOGICAL_INDENTATION_ERROR',
                                'line': j + 1,
                                'message': f'Indentation error',
                                'suggestion': '',
                                'severity': 'COMPILATION',
                                'code_snippet': f'Loop: {stripped_line}\\nReturn: {next_stripped}'
                            })
                            break
        
        # Pattern 3: Array access without bounds checking
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Look for array access patterns
            array_access = re.findall(r'(\w+)\[(\w+)\]', stripped_line)
            for array_name, index_var in array_access:
                # Check if there's a loop with <= condition using the same index
                for j in range(max(0, i-5), min(i+5, len(lines))):
                    if j >= len(lines):
                        break
                    check_line = lines[j].strip()
                    if (f'for' in check_line and 
                        f'{index_var}' in check_line and 
                        '<=' in check_line and 
                        'length' in check_line):
                        issues.append({
                            'type': 'POTENTIAL_OUT_OF_BOUNDS',
                            'line': i + 1,
                            'message': f'Out of bounds error',
                            'suggestion': '',
                            'severity': 'COMPILATION',
                            'code_snippet': f'Array access: {stripped_line}\\nLoop condition: {check_line}'
                        })
                        break
        
        # Pattern 4: Negative array index access (returns undefined in JavaScript - likely unintended)
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Look for array access with negative literal indices
            if re.search(r'\w+\[-\d+\]', stripped_line):
                issues.append({
                    'type': 'NEGATIVE_INDEX_ACCESS',
                    'line': i + 1,
                    'message': f'Negative index error',
                    'suggestion': '',
                    'severity': 'COMPILATION',
                    'code_snippet': f'Array access: {stripped_line}'
                })
        
        return issues
    
    @staticmethod
    def _detect_java_logical_issues(code):
        """Detect common Java logical issues"""
        lines = code.split('\n')
        issues = []
        
        # Pattern 1: Skip uninitialized variables - Java compiler already catches these
        
        # Pattern 2: Array index out of bounds (similar to C++)
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Look for for loops with <= length condition
            if ('for' in stripped_line and '<=' in stripped_line and 
                ('length' in stripped_line or 'size()' in stripped_line)):
                # Check for patterns like "i <= array.length" or "i <= list.size()"
                if re.search(r'\w+\s*<=\s*\w+\.(length|size\(\))', stripped_line):
                    issues.append({
                        'type': 'OUT_OF_BOUNDS_LOOP',
                        'line': i + 1,
                        'message': f'Out of bounds error',
                        'suggestion': '',
                        'severity': 'COMPILATION',
                        'code_snippet': f'Loop: {stripped_line}'
                    })
        
        # Pattern 2b: Negative array index access (throws exception in Java)
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Look for array access with negative literal indices
            if re.search(r'\w+\[-\d+\]', stripped_line):
                issues.append({
                    'type': 'NEGATIVE_INDEX_ACCESS',
                    'line': i + 1,
                    'message': f'Negative index error',
                    'suggestion': '',
                    'severity': 'COMPILATION',
                    'code_snippet': f'Array access: {stripped_line}'
                })
        
        # Pattern 3: String comparison with == instead of .equals()
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Look for string comparison with ==
            if ('==' in stripped_line and 'String' in stripped_line and '.equals(' not in stripped_line):
                # Check if it's likely a string comparison (more flexible pattern)
                if re.search(r'\w+\s*==\s*\w+', stripped_line) and ('String' in stripped_line or 'if' in stripped_line):
                    issues.append({
                        'type': 'STRING_COMPARISON_ERROR',
                        'line': i + 1,
                        'message': f'String comparison error',
                        'suggestion': '',
                        'severity': 'COMPILATION',
                        'code_snippet': f'Comparison: {stripped_line}'
                    })
        
        # Pattern 4: Missing return statement in non-void methods
        method_return_types = ['int', 'boolean', 'double', 'float', 'String', 'long']
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Look for method declarations with return types
            if ('public' in stripped_line and 
                any(ret_type in stripped_line for ret_type in method_return_types) and
                '(' in stripped_line and ')' in stripped_line and '{' in stripped_line):
                
                # Check if there's a return statement in the method
                brace_count = stripped_line.count('{') - stripped_line.count('}')
                found_return = False
                
                for j in range(i + 1, min(i + 30, len(lines))):
                    if j >= len(lines):
                        break
                    check_line = lines[j]
                    brace_count += check_line.count('{') - check_line.count('}')
                    
                    if 'return ' in check_line.strip():
                        found_return = True
                        break
                    
                    # If we've closed all braces, we're out of the method
                    if brace_count <= 0:
                        break
                
                if not found_return:
                    issues.append({
                        'type': 'MISSING_RETURN_STATEMENT',
                        'line': i + 1,
                        'message': f'Missing return statement error',
                        'suggestion': '',
                        'severity': 'COMPILATION',
                        'code_snippet': f'Method: {stripped_line}'
                    })
        
        return issues
    
    @staticmethod
    def _detect_python_logical_issues(code):
        """Detect common Python logical issues"""
        lines = code.split('\n')
        issues = []
        
        # Pattern 1: Return statement inside for/while loop (most common mistake)
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Check if this line starts a loop
            if stripped_line.startswith(('for ', 'while ')) and stripped_line.endswith(':'):
                loop_indent = len(line) - len(line.lstrip())
                
                # Look for return statements at the same level or deeper than loop body
                for j in range(i + 1, len(lines)):
                    next_line = lines[j]
                    if next_line.strip() == '':
                        continue
                    
                    next_indent = len(next_line) - len(next_line.lstrip())
                    next_stripped = next_line.strip()
                    
                    # If we've dedented back to loop level or beyond, we're out of the loop
                    if next_indent <= loop_indent and next_stripped:
                        break
                    
                    # Check for return statement inside the loop
                    if next_stripped.startswith('return ') and next_indent > loop_indent:
                        # Check if this looks like it should be outside the loop
                        # Common pattern: counting/accumulating then returning
                        loop_line = stripped_line.lower()
                        if any(keyword in loop_line for keyword in ['range(len(', 'in ', 'enumerate(']):
                            issues.append({
                                'type': 'LOGICAL_INDENTATION_ERROR',
                                'line': j + 1,
                                'message': f'Indentation error',
                                'suggestion': '',
                                'severity': 'COMPILATION',
                                'code_snippet': f'Loop: {stripped_line}\\nReturn: {next_stripped}'
                            })
                            break
        
        # Pattern 2: Function with only loop and return inside it (no statements after loop)
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Check for function definition
            if stripped_line.startswith('def ') and stripped_line.endswith(':'):
                func_indent = len(line) - len(line.lstrip())
                has_loop_with_early_return = False
                
                # Look inside the function
                j = i + 1
                while j < len(lines):
                    next_line = lines[j]
                    if next_line.strip() == '':
                        j += 1
                        continue
                    
                    next_indent = len(next_line) - len(next_line.lstrip())
                    next_stripped = next_line.strip()
                    
                    # If we've dedented back to function level or beyond, we're out of the function
                    if next_indent <= func_indent and next_stripped:
                        break
                    
                    # Look for loops followed immediately by return
                    if next_stripped.startswith(('for ', 'while ')) and next_stripped.endswith(':'):
                        loop_indent = next_indent
                        
                        # Check what comes after the loop
                        k = j + 1
                        found_return_in_loop = False
                        while k < len(lines):
                            check_line = lines[k]
                            if check_line.strip() == '':
                                k += 1
                                continue
                            
                            check_indent = len(check_line) - len(check_line.lstrip())
                            check_stripped = check_line.strip()
                            
                            # If we're back at loop level or higher, check for return
                            if check_indent <= loop_indent:
                                if check_stripped.startswith('return '):
                                    # This might be correct
                                    pass
                                break
                            else:
                                # Inside the loop
                                if check_stripped.startswith('return '):
                                    found_return_in_loop = True
                                    issues.append({
                                        'type': 'LOGICAL_INDENTATION_ERROR', 
                                        'line': k + 1,
                                        'message': f'Indentation error',
                                        'suggestion': '',
                                        'severity': 'COMPILATION',
                                        'code_snippet': f'Function: {stripped_line}\\nLoop: {next_stripped}\\nReturn: {check_stripped}'
                                    })
                                    break
                            k += 1
                        break
                    j += 1
        
        return issues

    @staticmethod
    def categorize_compilation_error(error_message, language):
        """Categorize and provide helpful messages for compilation errors"""
        error_message = error_message.lower().strip()
        
        # Python-specific errors
        if language == 'python':
            if 'indentationerror' in error_message or 'indentation' in error_message:
                return {
                    'category': 'INDENTATION_ERROR',
                    'user_message': 'Indentation Error: Python requires consistent indentation. Make sure your code blocks are properly indented.',
                    'helpful_tip': 'Use spaces or tabs consistently (Python recommends 4 spaces per indentation level)',
                    'severity': 'COMPILATION'
                }
            elif 'syntaxerror' in error_message:
                if 'unexpected eof' in error_message:
                    return {
                        'category': 'SYNTAX_ERROR',
                        'user_message': 'Syntax Error: Unexpected end of file. You might be missing closing brackets, parentheses, or quotes.',
                        'helpful_tip': 'Check for unmatched brackets: (), [], {}, or unclosed strings',
                        'severity': 'COMPILATION'
                    }
                elif 'invalid syntax' in error_message:
                    return {
                        'category': 'SYNTAX_ERROR', 
                        'user_message': 'Syntax Error: Invalid syntax detected. Check your code structure.',
                        'helpful_tip': 'Common issues: missing colons after if/for/while, incorrect operators, or typos',
                        'severity': 'COMPILATION'
                    }
            elif 'nameerror' in error_message:
                return {
                    'category': 'NAME_ERROR',
                    'user_message': 'Name Error: Using undefined variable or function.',
                    'helpful_tip': 'Make sure all variables are defined before use, and check for typos in variable names',
                    'severity': 'COMPILATION'
                }
        
        # C++ specific errors
        elif language == 'cpp':
            if 'expected' in error_message and ';' in error_message:
                return {
                    'category': 'SYNTAX_ERROR',
                    'user_message': 'Syntax Error: Missing semicolon or incorrect syntax.',
                    'helpful_tip': 'Every C++ statement must end with a semicolon (;)',
                    'severity': 'COMPILATION'
                }
            elif 'undeclared' in error_message or 'not declared' in error_message:
                return {
                    'category': 'UNDECLARED_ERROR',
                    'user_message': 'Declaration Error: Using undeclared variable or function.',
                    'helpful_tip': 'Make sure variables are declared with proper types (int, string, etc.)',
                    'severity': 'COMPILATION'
                }
            elif 'no matching function' in error_message:
                return {
                    'category': 'FUNCTION_ERROR',
                    'user_message': 'Function Error: Function signature doesn\'t match what\'s expected.',
                    'helpful_tip': 'Check function name, parameter types, and return type',
                    'severity': 'COMPILATION'
                }
        
        # Java specific errors
        elif language == 'java':
            if 'cannot find symbol' in error_message:
                return {
                    'category': 'SYMBOL_ERROR',
                    'user_message': 'Symbol Error: Using undefined variable, method, or class.',
                    'helpful_tip': 'Check spelling and make sure variables are declared with proper types',
                    'severity': 'COMPILATION'
                }
            elif 'expected' in error_message:
                return {
                    'category': 'SYNTAX_ERROR',
                    'user_message': 'Syntax Error: Missing or incorrect syntax element.',
                    'helpful_tip': 'Common issues: missing semicolons, brackets, or incorrect method signatures',
                    'severity': 'COMPILATION'
                }
        
        # JavaScript specific errors
        elif language == 'javascript':
            if 'syntaxerror' in error_message:
                return {
                    'category': 'SYNTAX_ERROR',
                    'user_message': 'Syntax Error: Invalid JavaScript syntax.',
                    'helpful_tip': 'Check for missing brackets, semicolons, or incorrect function syntax',
                    'severity': 'COMPILATION'
                }
        
        # Generic compilation error
        return {
            'category': 'COMPILATION_ERROR',
            'user_message': 'Compilation Error: Your code has syntax issues that prevent it from running.',
            'helpful_tip': 'Review your code for syntax errors, missing brackets, or typos',
            'severity': 'COMPILATION',
            'raw_error': error_message
        }
    
    @staticmethod
    def categorize_runtime_error(error_message, language):
        """Categorize and provide helpful messages for runtime errors"""
        error_message = error_message.lower().strip()
        
        # Index/Array out of bounds
        if any(keyword in error_message for keyword in ['index', 'out of bounds', 'out of range', 'indexerror']):
            return {
                'category': 'INDEX_OUT_OF_BOUNDS',
                'user_message': 'Index Error: Trying to access an array element that doesn\'t exist.',
                'helpful_tip': 'Check array bounds: make sure index < array.length and index >= 0',
                'severity': 'RUNTIME',
                'debugging_suggestion': 'Add bounds checking: if (index >= 0 && index < array.length)'
            }
        
        # Null pointer/None reference
        if any(keyword in error_message for keyword in ['null', 'none', 'nullpointer', 'nonetype']):
            return {
                'category': 'NULL_REFERENCE',
                'user_message': 'Null Reference Error: Trying to use a variable that is null/None.',
                'helpful_tip': 'Check if variables are properly initialized before using them',
                'severity': 'RUNTIME',
                'debugging_suggestion': 'Add null checks: if (variable != null) or if variable is not None'
            }
        
        # Division by zero
        if 'division' in error_message and 'zero' in error_message:
            return {
                'category': 'DIVISION_BY_ZERO',
                'user_message': 'Division by Zero Error: Cannot divide by zero.',
                'helpful_tip': 'Add a check to ensure the divisor is not zero before division',
                'severity': 'RUNTIME',
                'debugging_suggestion': 'Add check: if (divisor != 0) before division'
            }
        
        # Type errors
        if 'type' in error_message and any(keyword in error_message for keyword in ['error', 'mismatch']):
            return {
                'category': 'TYPE_ERROR',
                'user_message': 'Type Error: Incorrect data type usage.',
                'helpful_tip': 'Check that you\'re using the correct data types (int, string, list, etc.)',
                'severity': 'RUNTIME',
                'debugging_suggestion': 'Verify variable types and casting operations'
            }
        
        # Stack overflow (infinite recursion)
        if any(keyword in error_message for keyword in ['stack overflow', 'maximum recursion', 'stack space']):
            return {
                'category': 'STACK_OVERFLOW',
                'user_message': 'Stack Overflow: Infinite recursion or too many nested function calls.',
                'helpful_tip': 'Check recursive functions for proper base cases',
                'severity': 'RUNTIME',
                'debugging_suggestion': 'Ensure recursive functions have valid stopping conditions'
            }
        
        # Memory errors
        if any(keyword in error_message for keyword in ['memory', 'allocation', 'segmentation']):
            return {
                'category': 'MEMORY_ERROR',
                'user_message': 'Memory Error: Invalid memory access or allocation failure.',
                'helpful_tip': 'Check array bounds and pointer usage',
                'severity': 'RUNTIME',
                'debugging_suggestion': 'Review pointer operations and array access patterns'
            }
        
        # Generic runtime error
        return {
            'category': 'RUNTIME_ERROR',
            'user_message': 'Runtime Error: An error occurred while executing your code.',
            'helpful_tip': 'Check your logic and ensure all variables are properly initialized',
            'severity': 'RUNTIME',
            'raw_error': error_message
        }
    
    @staticmethod
    def categorize_logic_error(expected, actual, test_case_input):
        """Categorize logic errors based on expected vs actual output"""
        
        # Convert to strings for comparison
        expected_str = str(expected).strip()
        actual_str = str(actual).strip()
        
        # No output when output expected
        if not actual_str and expected_str:
            return {
                'category': 'NO_OUTPUT',
                'user_message': 'Test case failed.',
                'helpful_tip': 'Make sure your function has a return statement',
                'severity': 'LOGIC',
                'debugging_suggestion': ''
            }
        
        # Wrong data type
        try:
            if expected_str.isdigit() and not actual_str.isdigit():
                return {
                    'category': 'WRONG_TYPE',
                    'user_message': 'Test case failed.',
                    'helpful_tip': 'Check if you\'re returning the correct data type',
                    'severity': 'LOGIC',
                    'debugging_suggestion': ''
                }
        except:
            pass
        
        # Removed "off by one" logic error - these should be caught at compilation time instead
        
        # Default logic error - simplified to avoid giving away solutions
        return {
            'category': 'WRONG_OUTPUT',
            'user_message': 'Test case failed.',
            'helpful_tip': 'Check your algorithm logic',
            'severity': 'LOGIC',
            'debugging_suggestion': ''
        }
    
    @staticmethod
    def format_error_response(error_info, test_number=None):
        """Format error information into a user-friendly response"""
        
        # Color coding based on severity
        severity_colors = {
            'COMPILATION': '🔴',  # Red - critical
            'RUNTIME': '🟠',      # Orange - serious
            'LOGIC': '🟡'         # Yellow - logic issue
        }
        
        color = severity_colors.get(error_info['severity'], '⚪')
        
        response = {
            'category': error_info['category'],
            'severity': error_info['severity'],
            'user_message': f"{color} {error_info['user_message']}",
            'helpful_tip': error_info['helpful_tip'],
            'debugging_suggestion': error_info.get('debugging_suggestion', ''),
        }
        
        if test_number:
            response['test_number'] = test_number
            response['message'] = f"Test {test_number} failed: {response['user_message']}"
        
        # Add raw error for debugging if available
        if 'raw_error' in error_info:
            response['raw_error'] = error_info['raw_error']
        
        return response

# Example usage functions
def handle_compilation_error(error_message, language):
    """Handle compilation errors with enhanced feedback"""
    error_info = ErrorHandler.categorize_compilation_error(error_message, language)
    return ErrorHandler.format_error_response(error_info)

def handle_runtime_error(error_message, language, test_number=None):
    """Handle runtime errors with enhanced feedback"""
    error_info = ErrorHandler.categorize_runtime_error(error_message, language)
    return ErrorHandler.format_error_response(error_info, test_number)

def handle_logic_error(expected, actual, test_input, test_number=None):
    """Handle logic errors with enhanced feedback"""
    error_info = ErrorHandler.categorize_logic_error(expected, actual, test_input)
    return ErrorHandler.format_error_response(error_info, test_number)

# Test the error handler
if __name__ == "__main__":
    # Test compilation errors
    print("=== Compilation Error Examples ===")
    print(json.dumps(handle_compilation_error("IndentationError: expected an indented block", "python"), indent=2))
    print(json.dumps(handle_compilation_error("error: expected ';' before 'return'", "cpp"), indent=2))
    
    # Test runtime errors
    print("\n=== Runtime Error Examples ===")
    print(json.dumps(handle_runtime_error("IndexError: list index out of range", "python", 1), indent=2))
    print(json.dumps(handle_runtime_error("NullPointerException", "java", 2), indent=2))
    
    # Test logic errors
    print("\n=== Logic Error Examples ===")
    print(json.dumps(handle_logic_error("5", "6", "[1,2,3,4,5]", 1), indent=2))
    print(json.dumps(handle_logic_error("10", "", "[1,2,3]", 2), indent=2)) 