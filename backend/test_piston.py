#!/usr/bin/env python3
"""
Test script to verify Piston API integration
"""

import requests
import json

PISTON_API = 'https://emkc.org/api/v2/piston'

def test_piston_api():
    """Test the Piston API integration"""
    print("🧪 Testing Piston API integration...")
    
    # Test 1: Check available languages
    print("\n1. Testing available languages...")
    try:
        response = requests.get(f'{PISTON_API}/runtimes', timeout=10)
        if response.status_code == 200:
            runtimes = response.json()
            python_runtime = next((r for r in runtimes if r['language'] == 'python'), None)
            javascript_runtime = next((r for r in runtimes if r['language'] == 'javascript'), None)
            java_runtime = next((r for r in runtimes if r['language'] == 'java'), None)
            cpp_runtime = next((r for r in runtimes if r['language'] == 'cpp'), None)
            
            print(f"   ✅ API accessible")
            print(f"   Python available: {bool(python_runtime)} {python_runtime['version'] if python_runtime else ''}")
            print(f"   JavaScript available: {bool(javascript_runtime)} {javascript_runtime['version'] if javascript_runtime else ''}")
            print(f"   Java available: {bool(java_runtime)} {java_runtime['version'] if java_runtime else ''}")
            print(f"   C++ available: {bool(cpp_runtime)} {cpp_runtime['version'] if cpp_runtime else ''}")
        else:
            print(f"   ❌ API not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API error: {e}")
        return False
    
    # Test 2: Execute simple Python code
    print("\n2. Testing Python code execution...")
    try:
        test_code = """
def find_max(numbers):
    if not numbers:
        return None
    max_num = numbers[0]
    for num in numbers:
        if num > max_num:
            max_num = num
    return max_num

# Test case
test_input = [1, 2, 3, 4, 5]
result = find_max(test_input)
print(result)
"""
        
        piston_request = {
            'language': 'python',
            'version': '3.10.0',
            'files': [{'name': 'main.py', 'content': test_code}],
            'compile_timeout': 10000,
            'run_timeout': 10000,
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
            stdout = result.get('run', {}).get('stdout', '').strip()
            stderr = result.get('run', {}).get('stderr', '').strip()
            
            if stdout == '5' and not stderr:
                print(f"   ✅ Python execution successful: output = {stdout}")
            else:
                print(f"   ⚠️ Python execution issue: stdout='{stdout}', stderr='{stderr}'")
        else:
            print(f"   ❌ Python execution failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Python execution error: {e}")
    
    # Test 3: Execute simple JavaScript code
    print("\n3. Testing JavaScript code execution...")
    try:
        test_code = """
function calculateSum(arr) {
    if (!arr || arr.length === 0) {
        return 0;
    }
    let sum = 0;
    for (let i = 0; i < arr.length; i++) {
        sum += arr[i];
    }
    return sum;
}

// Test case
const test_input = [1, 2, 3, 4, 5];
const result = calculateSum(test_input);
console.log(result);
"""
        
        piston_request = {
            'language': 'javascript',
            'version': '18.15.0',
            'files': [{'name': 'main.js', 'content': test_code}],
            'compile_timeout': 10000,
            'run_timeout': 10000,
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
            stdout = result.get('run', {}).get('stdout', '').strip()
            stderr = result.get('run', {}).get('stderr', '').strip()
            
            if stdout == '15' and not stderr:
                print(f"   ✅ JavaScript execution successful: output = {stdout}")
            else:
                print(f"   ⚠️ JavaScript execution issue: stdout='{stdout}', stderr='{stderr}'")
        else:
            print(f"   ❌ JavaScript execution failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ JavaScript execution error: {e}")
    
    return True

if __name__ == "__main__":
    test_piston_api() 