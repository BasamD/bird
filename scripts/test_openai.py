#!/usr/bin/env python3
"""
Quick test script to verify OpenAI API key is working correctly.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_openai():
    print("=" * 62)
    print("Testing OpenAI API Key")
    print("=" * 62)
    print()

    try:
        import config
        api_key = config.OPENAI_API_KEY

        if not api_key:
            print("❌ ERROR: No API key found!")
            print("   Please set OPENAI_API_KEY in .env file or config.py")
            return False

        print(f"API Key: {api_key[:8]}...{api_key[-8:]}")
        print(f"Length: {len(api_key)} characters")
        print()

    except ModuleNotFoundError as e:
        if "dotenv" in str(e):
            print(f"⚠️  WARNING: python-dotenv not installed")
            print(f"   Run: pip install python-dotenv")
            print()
            print("Trying hardcoded fallback...")
            api_key = "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"
            print(f"API Key: {api_key[:8]}...{api_key[-8:]}")
            print(f"Length: {len(api_key)} characters")
            print()
        else:
            raise
    except Exception as e:
        print(f"❌ ERROR loading config: {e}")
        return False

    try:
        from openai import OpenAI
        print("✅ OpenAI library imported successfully")
        print()
    except ImportError as e:
        print(f"❌ ERROR: OpenAI library not installed!")
        print(f"   Run: pip install openai")
        print(f"   Details: {e}")
        return False

    try:
        print("Initializing OpenAI client...")
        client = OpenAI(
            api_key=api_key,
            timeout=30.0,
            max_retries=3
        )
        print("✅ Client initialized")
        print()
    except Exception as e:
        print(f"❌ ERROR initializing client: {e}")
        return False

    try:
        print("Making test API call...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Say 'API key is working!' and nothing else."}
            ],
            max_tokens=10
        )

        result = response.choices[0].message.content.strip()
        print(f"✅ API call successful!")
        print(f"Response: {result}")
        print()

    except Exception as e:
        print(f"❌ ERROR making API call: {e}")
        print()

        error_str = str(e)
        if "401" in error_str or "invalid_api_key" in error_str:
            print("🔑 API key is INVALID or EXPIRED")
            print("   1. Check https://platform.openai.com/api-keys")
            print("   2. Regenerate your API key if needed")
            print("   3. Update .env file and config.py with new key")
        elif "429" in error_str or "quota" in error_str.lower():
            print("💳 Quota or rate limit exceeded")
            print("   1. Check https://platform.openai.com/usage")
            print("   2. Add billing method or wait for quota reset")
        else:
            print("🌐 Network or server error")
            print("   1. Check internet connection")
            print("   2. Try again in a few seconds")
            print("   3. Check https://status.openai.com/")

        return False

    print("=" * 62)
    print("SUCCESS: OpenAI API key is valid and working!")
    print("=" * 62)
    return True


if __name__ == "__main__":
    success = test_openai()
    sys.exit(0 if success else 1)
