#!/usr/bin/env python3

import requests
import json
from database_config import get_challenge_by_id

def test_language_execution(language, difficulty, challenge_id):
    """Test code execution for a specific language challenge"""
    print(f"\n🧪 Testing {language.upper()} execution...")
    
    try:
        # Get challenge data
        challenge = get_challenge_by_id(language, difficulty, challenge_id)
        if not challenge:
            print(f"  ❌ No challenge found for {language}/{difficulty}/{challenge_id}")
            return False
            
        print(f"  📝 Challenge: {challenge['title']}")
        print(f"  🎯 Test cases: {len(challenge.get('test_cases', []))}")
        
        # Get the buggy code for testing
        test_code = challenge.get('buggy_code', '')
        if not test_code:
            print(f"  ❌ No buggy code found")
            return False
            
        # Show test cases
        test_cases = challenge.get('test_cases', [])
        for i, test_case in enumerate(test_cases[:2], 1):  # Show first 2 test cases
            expected = test_case.get('expected_output') or test_case.get('expected', 'N/A')
            print(f"    Test {i}: {test_case['input']} → {expected}")
        
        # Test execution via API
        payload = {
            'code': test_code,
            'language': language,
            'test_cases': test_cases[:2]  # Test with first 2 cases
        }
        
        print(f"  🚀 Executing code...")
        response = requests.post(
            'http://localhost:5000/api/execute',
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"  ✅ Execution successful!")
                print(f"  📊 Tests passed: {result.get('tests_passed', 0)}/{result.get('total_tests', 0)}")
                
                # Show test results
                for test_result in result.get('test_results', []):
                    status = "✅ PASS" if test_result.get('passed') else "❌ FAIL"
                    print(f"    Test {test_result.get('test_number', '?')}: {status}")
                    if not test_result.get('passed'):
                        print(f"      Expected: {test_result.get('expected')}")
                        print(f"      Got: {test_result.get('output')}")
                        if test_result.get('error'):
                            print(f"      Error: {test_result.get('error')}")
                            
                return result.get('tests_passed', 0) > 0
            else:
                print(f"  ❌ Execution failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"  ❌ API call failed: {response.status_code}")
            if response.text:
                print(f"  Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_all_languages():
    """Test code execution for all available languages"""
    print("🚀 Testing code execution for all languages...\n")
    
    # Test cases: (language, difficulty, challenge_id)
    tests = [
        ('python', 'basic', 1),
        ('javascript', 'basic', 1),
        ('java', 'basic', 1),
        ('cpp', 'basic', 1)
    ]
    
    results = {}
    for language, difficulty, challenge_id in tests:
        try:
            success = test_language_execution(language, difficulty, challenge_id)
            results[language] = success
        except Exception as e:
            print(f"  ❌ {language} test failed with exception: {e}")
            results[language] = False
    
    # Summary
    print("\n" + "="*50)
    print("📊 EXECUTION TEST SUMMARY")
    print("="*50)
    
    for language, success in results.items():
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"  {language.upper():<12}: {status}")
    
    working_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    print(f"\n🎯 Overall: {working_count}/{total_count} languages working")
    
    if working_count == total_count:
        print("🎉 All languages are working correctly!")
    else:
        print("⚠️ Some languages need fixing. Check the errors above.")
    
    return results

def main():
    print("🔍 BugYou Code Execution Test Suite")
    print("="*50)
    
    # Check if server is running
    try:
        response = requests.get('http://localhost:5000/api/health', timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding properly. Make sure it's running on localhost:5000")
            return
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to server. Make sure it's running on localhost:5000")
        return
    
    print("✅ Server is running")
    
    # Run tests
    test_all_languages()

if __name__ == "__main__":
    main() 