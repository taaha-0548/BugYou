#!/usr/bin/env python3

from app import PISTON_LANGUAGES
import requests

def test_templates():
    """Quick test of template generation"""
    print("🧪 Testing Template Generation...\n")
    
    # Sample codes and expected results
    test_cases = {
        'cpp': {
            'func_name': 'countElements',
            'user_code': '''int countElements(std::vector<int>& numbers) {
    return numbers.size();
}''',
            'test_input': 'std::vector<int>{1, 2, 3, 4, 5}',
            'expected': '5'
        },
        'java': {
            'func_name': 'findMin',
            'user_code': '''public static int findMin(int[] numbers) {
    if (numbers.length == 0) return 0;
    int min = numbers[0];
    for (int i = 1; i < numbers.length; i++) {
        if (numbers[i] < min) {
            min = numbers[i];
        }
    }
    return min;
}''',
            'test_input': 'new int[]{1, 2, 3, 4, 5}',
            'expected': '1'
        },
        'javascript': {
            'func_name': 'calculateSum',
            'user_code': '''function calculateSum(arr) {
    return arr.reduce((sum, num) => sum + num, 0);
}''',
            'test_input': '[1, 2, 3, 4, 5]',
            'expected': '15'
        },
        'python': {
            'func_name': 'find_max',
            'user_code': '''def find_max(numbers):
    if not numbers:
        return None
    return max(numbers)''',
            'test_input': '[1, 2, 3, 4, 5]',
            'expected': '5'
        }
    }
    
    for language, test_data in test_cases.items():
        print(f"📌 Testing {language.upper()}...")
        
        if language not in PISTON_LANGUAGES:
            print(f"  ❌ Language {language} not found in PISTON_LANGUAGES")
            continue
            
        lang_config = PISTON_LANGUAGES[language]
        
        # Generate test code
        try:
            test_code = lang_config['template'].format(
                func_name=test_data['func_name'],
                user_code=test_data['user_code'],
                test_input=test_data['test_input']
            )
            
            print(f"  ✅ Template generated successfully")
            print(f"  📝 Generated code length: {len(test_code)} characters")
            
            # Show a snippet of the generated code
            lines = test_code.splitlines()
            print(f"  📄 Generated code preview:")
            for i, line in enumerate(lines[:5], 1):
                print(f"    {i:2}: {line}")
            if len(lines) > 5:
                print(f"    ... ({len(lines) - 5} more lines)")
            
            # Test via Piston API
            print(f"  🚀 Testing execution...")
            
            piston_request = {
                'language': lang_config['lang'],
                'version': lang_config['version'],
                'files': [{'name': lang_config['filename'], 'content': test_code}],
                'compile_timeout': 10000,
                'run_timeout': 10000,
                'compile_memory_limit': -1,
                'run_memory_limit': -1
            }
            
            response = requests.post(
                'https://emkc.org/api/v2/piston/execute',
                headers={'Content-Type': 'application/json'},
                json=piston_request,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check compilation
                if result.get('compile', {}).get('stderr'):
                    print(f"  ❌ Compilation error: {result['compile']['stderr']}")
                    continue
                
                # Check runtime
                if result.get('run', {}).get('stderr'):
                    print(f"  ⚠️ Runtime warning: {result['run']['stderr']}")
                
                # Check output
                actual_output = result.get('run', {}).get('stdout', '').strip()
                expected = test_data['expected']
                
                if actual_output == expected:
                    print(f"  ✅ Execution successful! Output: {actual_output}")
                else:
                    print(f"  ❌ Wrong output. Expected: {expected}, Got: {actual_output}")
                    
            else:
                print(f"  ❌ API call failed: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Template generation failed: {e}")
            
        print()
    
    print("🎯 Template test completed!")

if __name__ == "__main__":
    test_templates() 