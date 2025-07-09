#!/usr/bin/env python3

from database_config import get_challenge_by_id
import re

def check_buggy_code():
    """Check buggy code for all languages and identify issues"""
    print("🔍 Checking buggy code for formatting issues...\n")
    
    languages = [
        ('python', 'basic', 1),
        ('javascript', 'basic', 1),
        ('java', 'basic', 1),
        ('cpp', 'basic', 1)
    ]
    
    for language, difficulty, challenge_id in languages:
        print(f"📌 {language.upper()} Challenge:")
        try:
            challenge = get_challenge_by_id(language, difficulty, challenge_id)
            if challenge:
                buggy_code = challenge.get('buggy_code', '')
                print(f"  Title: {challenge['title']}")
                print(f"  Code length: {len(buggy_code)} characters")
                print(f"  Lines: {len(buggy_code.splitlines())}")
                
                # Show the actual code
                print("  Buggy Code:")
                for i, line in enumerate(buggy_code.splitlines()[:10], 1):  # Show first 10 lines
                    print(f"    {i:2}: {repr(line)}")
                if len(buggy_code.splitlines()) > 10:
                    print(f"    ... ({len(buggy_code.splitlines()) - 10} more lines)")
                
                # Check for specific issues
                issues = []
                
                if language == 'python':
                    # Check indentation
                    lines = buggy_code.splitlines()
                    for i, line in enumerate(lines[1:], 2):  # Skip first line
                        if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                            if i > 1 and lines[i-2].strip().endswith(':'):
                                issues.append(f"Line {i}: Missing indentation after colon")
                
                elif language == 'javascript':
                    # Check for return statements
                    if 'return' not in buggy_code:
                        issues.append("Missing return statement")
                
                elif language == 'cpp':
                    # Check for reference parameters
                    if '&' in buggy_code:
                        issues.append("Uses reference parameters")
                
                # Extract function name
                patterns = {
                    'python': r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                    'javascript': r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                    'java': r'public\s+static\s+\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                    'cpp': r'\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
                }
                matches = re.findall(patterns[language], buggy_code)
                if matches:
                    print(f"  Function name: {matches[0]}")
                else:
                    issues.append("Cannot extract function name")
                
                if issues:
                    print(f"  ⚠️ Issues found:")
                    for issue in issues:
                        print(f"    - {issue}")
                else:
                    print(f"  ✅ No obvious issues")
                    
            else:
                print(f"  ❌ Challenge not found")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        print()

if __name__ == "__main__":
    check_buggy_code() 