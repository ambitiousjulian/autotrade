#!/usr/bin/env python3
"""
Debug Schwab API Authentication Issues
"""

import base64
import requests
from urllib.parse import quote

# Your credentials
APP_KEY = "9fFeTEuASMsx30SbPQRB1UDwGPiFc3Zu"  # Replace with your actual app key
APP_SECRET = "6tmEJ2GLAOgHyFev"  # Replace with your actual app secret
REDIRECT_URI = "https://127.0.0.1:8182"

print("=== Schwab API Debug ===\n")

# 1. Check credential format
print("1. Checking credentials format:")
print(f"   App Key length: {len(APP_KEY)} chars")
print(f"   App Secret length: {len(APP_SECRET)} chars")
print(f"   App Key format: {APP_KEY[:8]}...{APP_KEY[-4:]}")
print(f"   Redirect URI: {REDIRECT_URI}")

# 2. Test different encoding methods
print("\n2. Testing Basic Auth encoding methods:")

# Method 1: Standard Basic Auth
creds1 = f"{APP_KEY}:{APP_SECRET}"
basic1 = base64.b64encode(creds1.encode()).decode()
print(f"   Method 1 (standard): Basic {basic1[:20]}...")

# Method 2: URL encoded credentials first
creds2 = f"{quote(APP_KEY)}:{quote(APP_SECRET)}"
basic2 = base64.b64encode(creds2.encode()).decode()
print(f"   Method 2 (URL encoded): Basic {basic2[:20]}...")

# 3. Test token endpoint directly
print("\n3. Testing token endpoint with different methods:")

test_code = "test_auth_code"  # This will fail but shows the error
token_url = "https://api.schwabapi.com/v1/oauth/token"

for i, (method_name, auth_header) in enumerate([
    ("Standard", f"Basic {basic1}"),
    ("URL Encoded", f"Basic {basic2}"),
    ("Direct credentials", None)
], 1):
    print(f"\n   Test {i}: {method_name}")
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    if auth_header:
        headers["Authorization"] = auth_header
        data = {
            "grant_type": "authorization_code",
            "code": test_code,
            "redirect_uri": REDIRECT_URI
        }
    else:
        # Try client credentials in body
        data = {
            "grant_type": "authorization_code",
            "code": test_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": APP_KEY,
            "client_secret": APP_SECRET
        }
    
    try:
        response = requests.post(token_url, headers=headers, data=data, timeout=10)
        print(f"   Response: {response.status_code}")
        print(f"   Body: {response.text[:100]}...")
    except Exception as e:
        print(f"   Error: {e}")

# 4. Check if we need to wait
print("\n4. Important notes:")
print("   - It can take 5-10 minutes for a new app to be fully activated")
print("   - Make sure your app status shows 'Ready For Use'")
print("   - The callback URL must match EXACTLY (including https://)")
print("   - Try logging out and back into the developer portal")

# 5. Alternative approach
print("\n5. Alternative manual approach:")
print(f"""
   Try this manual URL in your browser:
   
   https://api.schwabapi.com/v1/oauth/authorize?response_type=code&client_id={APP_KEY}&redirect_uri={quote(REDIRECT_URI)}
   
   If this gives an error, the issue is with the app registration.
""")

# 6. Common issues
print("\n6. Common issues to check:")
print("   ✓ App status is 'Ready For Use' (not 'Pending')")
print("   ✓ You're using Production keys (not Sandbox)")
print("   ✓ The callback URL in your app matches exactly: https://127.0.0.1:8182")
print("   ✓ You've waited at least 10 minutes after creating the app")
print("   ✓ Your app has the correct APIs enabled (Accounts and Trading + Market Data)")
print("   ✓ No extra spaces in the App Key or Secret")

print("\n7. If still failing, try:")
print("   - Delete and recreate the app")
print("   - Use a different callback URL like https://localhost:8182")
print("   - Contact Schwab API support")