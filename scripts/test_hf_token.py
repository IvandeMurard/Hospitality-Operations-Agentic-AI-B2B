"""Test script to verify HuggingFace token format and authentication"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Get token
token = os.getenv("HF_TOKEN")

print("=" * 60)
print("HUGGINGFACE TOKEN DIAGNOSTIC")
print("=" * 60)

if not token:
    print("[ERROR] HF_TOKEN not found in .env")
    sys.exit(1)

print(f"\n[INFO] Token found in .env")
print(f"[INFO] Token length: {len(token)}")
print(f"[INFO] Token starts with: {token[:10]}...")
print(f"[INFO] Token ends with: ...{token[-5:] if len(token) > 5 else token}")

# Check for common issues
issues = []
if " " in token:
    issues.append("Token contains spaces")
if token.startswith('"') or token.startswith("'"):
    issues.append("Token is wrapped in quotes")
if not token.startswith("hf_"):
    issues.append("Token doesn't start with 'hf_' (might be invalid format)")

if issues:
    print(f"\n[WARN] Potential issues found:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("\n[OK] Token format looks correct")

# Test authentication
print("\n" + "=" * 60)
print("TESTING AUTHENTICATION...")
print("=" * 60)

try:
    from huggingface_hub import HfApi
    
    # Strip any whitespace
    token_clean = token.strip()
    api = HfApi(token=token_clean)
    user_info = api.whoami()
    
    print(f"\n[OK] Authentication successful!")
    print(f"[OK] Authenticated as: {user_info.get('name', 'Unknown')}")
    print(f"[OK] User ID: {user_info.get('id', 'Unknown')}")
    
    # Test listing spaces
    print("\n" + "=" * 60)
    print("TESTING SPACE ACCESS...")
    print("=" * 60)
    
    try:
        spaces = api.list_spaces(author="IvandeMurard")
        space_names = [s.id for s in spaces]
        print(f"[OK] Found {len(space_names)} space(s):")
        for space in space_names:
            print(f"  - {space}")
        
        if "IvandeMurard/fb-agent-api" in space_names:
            print("\n[OK] Target space 'IvandeMurard/fb-agent-api' is accessible")
        else:
            print("\n[WARN] Target space 'IvandeMurard/fb-agent-api' not found in list")
    except Exception as e:
        print(f"[ERROR] Failed to list spaces: {e}")
    
except ImportError:
    print("[ERROR] huggingface_hub not installed")
    print("Install with: pip install huggingface_hub")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] Authentication failed: {e}")
    print("\nPossible causes:")
    print("  1. Token is invalid or expired")
    print("  2. Token doesn't have correct permissions")
    print("  3. Token format is incorrect (spaces, quotes, etc.)")
    print("\nTo fix:")
    print("  1. Go to: https://huggingface.co/settings/tokens")
    print("  2. Create a new token with 'Write' permissions")
    print("  3. Copy the token (it should start with 'hf_')")
    print("  4. Update HF_TOKEN in .env (no quotes, no spaces)")
    sys.exit(1)
