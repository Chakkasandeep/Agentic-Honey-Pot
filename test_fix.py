"""
Quick test to verify the fix handles POST with no body
"""
import requests

API_KEY = "UoxDHBe1m83w5zRtaAwz-FF70-8T94c4O6tZmHmjcu8"

print("=" * 80)
print("TESTING FIX FOR GUVI TESTER (POST with no body)")
print("=" * 80)

# Test locally first
LOCAL_URL = "http://localhost:8000/honeypot"

print("\n📋 Testing POST with no JSON body (what GUVI sends)...")
try:
    response = requests.post(
        LOCAL_URL,
        headers={"x-api-key": API_KEY}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ SUCCESS! Response: {response.json()}")
    else:
        print(f"❌ FAILED! Response: {response.text}")
except requests.exceptions.ConnectionError:
    print("⚠️  Local server not running - deploy to test on Render")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
