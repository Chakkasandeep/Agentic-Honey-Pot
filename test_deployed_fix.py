"""
Test the deployed fix on Render
"""
import requests
import time

API_URL = "https://agentic-honey-pot-e7mc.onrender.com/honeypot"
API_KEY = "UoxDHBe1m83w5zRtaAwz-FF70-8T94c4O6tZmHmjcu8"

print("=" * 80)
print("TESTING DEPLOYED FIX ON RENDER")
print("=" * 80)

print("\n⏳ Waiting 30 seconds for Render to deploy...")
time.sleep(30)

print("\n📋 Test: POST with no body (what GUVI tester sends)...")
try:
    response = requests.post(
        API_URL,
        headers={"x-api-key": API_KEY},
        timeout=15
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ SUCCESS! The fix works!")
        print(f"Response: {response.json()}")
        print("\n🎉 GUVI tester should now work!")
    elif response.status_code == 422:
        print(f"❌ Still getting 422 - deployment might not be live yet")
        print(f"Response: {response.text}")
    else:
        print(f"⚠️  Unexpected status: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
