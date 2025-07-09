from database_config import get_challenge_by_id, DatabaseManager
import json

def test_current_data():
    print("🔍 Testing current challenge data and input formats...\n")
    
    try:
        # Check C++ challenge using the proper function
        print("📌 C++ Basic Challenge:")
        cpp_challenge = get_challenge_by_id('cpp', 'basic', 1)
        if cpp_challenge:
            print(f"  Title: {cpp_challenge['title']}")
            print(f"  Test 1: Input='{cpp_challenge.get('test_case_1_input')}' Expected='{cpp_challenge.get('test_case_1_expected')}'")
            print(f"  Test 2: Input='{cpp_challenge.get('test_case_2_input')}' Expected='{cpp_challenge.get('test_case_2_expected')}'")
            print(f"  Test 3: Input='{cpp_challenge.get('test_case_3_input')}' Expected='{cpp_challenge.get('test_case_3_expected')}'")
            print(f"  Test Cases Array: {cpp_challenge.get('test_cases', [])}")
        else:
            print("  No C++ challenge found")
            
        print()
        
        # Check Java challenge
        print("📌 Java Basic Challenge:")
        java_challenge = get_challenge_by_id('java', 'basic', 1)
        if java_challenge:
            print(f"  Title: {java_challenge['title']}")
            print(f"  Test 1: Input='{java_challenge.get('test_case_1_input')}' Expected='{java_challenge.get('test_case_1_expected')}'")
            print(f"  Test 2: Input='{java_challenge.get('test_case_2_input')}' Expected='{java_challenge.get('test_case_2_expected')}'")
            print(f"  Test 3: Input='{java_challenge.get('test_case_3_input')}' Expected='{java_challenge.get('test_case_3_expected')}'")
            print(f"  Test Cases Array: {java_challenge.get('test_cases', [])}")
        else:
            print("  No Java challenge found")
            
        print()
        
        # Check Python challenge for comparison
        print("📌 Python Basic Challenge:")
        python_challenge = get_challenge_by_id('python', 'basic', 1)
        if python_challenge:
            print(f"  Title: {python_challenge['title']}")
            print(f"  Test 1: Input='{python_challenge.get('test_case_1_input')}' Expected='{python_challenge.get('test_case_1_expected')}'")
            print(f"  Test 2: Input='{python_challenge.get('test_case_2_input')}' Expected='{python_challenge.get('test_case_2_expected')}'")
            print(f"  Test Cases Array: {python_challenge.get('test_cases', [])}")
        else:
            print("  No Python challenge found")
            
        print()
        
        # Check JavaScript challenge for comparison
        print("📌 JavaScript Basic Challenge:")
        js_challenge = get_challenge_by_id('javascript', 'basic', 1)
        if js_challenge:
            print(f"  Title: {js_challenge['title']}")
            print(f"  Test 1: Input='{js_challenge.get('test_case_1_input')}' Expected='{js_challenge.get('test_case_1_expected')}'")
            print(f"  Test 2: Input='{js_challenge.get('test_case_2_input')}' Expected='{js_challenge.get('test_case_2_expected')}'")
            print(f"  Test Cases Array: {js_challenge.get('test_cases', [])}")
        else:
            print("  No JavaScript challenge found")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_current_data() 