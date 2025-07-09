#!/usr/bin/env python3
"""
Test script to verify challenge loading functionality
"""

from database_config import get_challenges_by_language_difficulty, get_challenge_by_id

def test_challenge_loading():
    """Test the challenge loading functionality"""
    print("🧪 Testing challenge loading functionality...")
    
    # Test getting list of challenges
    print("\n1. Testing get_challenges_by_language_difficulty...")
    challenges = get_challenges_by_language_difficulty('python', 'basic')
    print(f"   Found {len(challenges)} Python basic challenges")
    
    if challenges:
        print(f"   First challenge: {challenges[0]['title']}")
        print(f"   Challenge ID: {challenges[0]['challenge_id']}")
    
    # Test getting specific challenge details
    print("\n2. Testing get_challenge_by_id...")
    if challenges:
        challenge_id = challenges[0]['challenge_id']
        challenge = get_challenge_by_id('python', 'basic', challenge_id)
        
        if challenge:
            print(f"   ✅ Challenge details loaded successfully")
            print(f"   Title: {challenge['title']}")
            print(f"   Test cases available: {len(challenge.get('test_cases', []))}")
            print(f"   Buggy code length: {len(challenge.get('buggy_code', ''))}")
            print(f"   Hints available: {len(challenge.get('hints', []))}")
        else:
            print(f"   ❌ Failed to load challenge details")
    
    # Test other languages
    print("\n3. Testing other languages...")
    for lang in ['javascript', 'java', 'cpp']:
        challenges = get_challenges_by_language_difficulty(lang, 'basic')
        print(f"   {lang}: {len(challenges)} challenges")

if __name__ == "__main__":
    test_challenge_loading() 