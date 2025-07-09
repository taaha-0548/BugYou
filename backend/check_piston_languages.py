import requests

def check_piston_languages():
    try:
        response = requests.get('https://emkc.org/api/v2/piston/runtimes')
        if response.status_code == 200:
            runtimes = response.json()
            
            print("🔍 Available Piston API Languages:")
            
            # Check C++ specifically
            cpp_langs = [lang for lang in runtimes if 'c++' in lang['language'].lower() or 'cpp' in lang['language'].lower()]
            print("\n📌 C++ Versions:")
            if cpp_langs:
                for lang in cpp_langs:
                    print(f"  ✅ {lang['language']} v{lang['version']}")
            else:
                print("  ❌ No C++ versions found")
            
            # Check Java
            java_langs = [lang for lang in runtimes if 'java' in lang['language'].lower()]
            print("\n📌 Java Versions:")
            for lang in java_langs:
                print(f"  ✅ {lang['language']} v{lang['version']}")
            
            # Check Python
            python_langs = [lang for lang in runtimes if 'python' in lang['language'].lower()]
            print("\n📌 Python Versions:")
            for lang in python_langs:
                print(f"  ✅ {lang['language']} v{lang['version']}")
                
            # Check JavaScript
            js_langs = [lang for lang in runtimes if 'javascript' in lang['language'].lower() or lang['language'].lower() == 'node']
            print("\n📌 JavaScript Versions:")
            for lang in js_langs:
                print(f"  ✅ {lang['language']} v{lang['version']}")
                
            return runtimes
        else:
            print(f"❌ Failed to fetch runtimes: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    check_piston_languages() 