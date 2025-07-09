#!/usr/bin/env python3

import requests
import json

def test_api_execution():
    """Test the API directly with simple code"""
    print("🧪 Testing API Execution Directly...\n")
    
    # Test C++ with fixed reference issue
    cpp_test = {
        'code': '''int countElements(std::vector<int>& numbers) {
    return numbers.size();
}''',
        'language': 'cpp',
        'test_cases': [
            {'input': 'std::vector<int>{1, 2, 3, 4, 5}', 'expected_output': '5'},
            {'input': 'std::vector<int>{10, 20}', 'expected_output': '2'}
        ]
    }
    
    print("📌 Testing C++ execution...")
    try:
        response = requests.post(
            'http://localhost:5000/api/execute',
            headers={'Content-Type': 'application/json'},
            json=cpp_test,
            timeout=30
        )
        
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"  Success: {result.get('success')}")
            print(f"  Tests passed: {result.get('tests_passed', 0)}/{result.get('total_tests', 0)}")
            
            for test_result in result.get('test_results', []):
                status = "✅ PASS" if test_result.get('passed') else "❌ FAIL"
                print(f"    Test {test_result.get('test_number')}: {status}")
                if not test_result.get('passed'):
                    print(f"      Expected: {test_result.get('expected')}")
                    print(f"      Got: {test_result.get('output')}")
                    print(f"      Error: {test_result.get('error')}")
        else:
            print(f"  Error: {response.text[:200]}...")
            
    except requests.exceptions.ConnectionError:
        print("  ❌ Server not running. Start with: python start_server.py")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    print()

if __name__ == "__main__":
    test_api_execution() 