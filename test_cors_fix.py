"""
Test CORS fix - simulate browser request from GUVI tester
"""
import requests

API_URL = "https://agentic-honey-pot-e7mc.onrender.com/honeypot"
API_KEY = "UoxDHBe1m83w5zRtaAwz-FF70-8T94c4O6tZmHmjcu8"

# Test 1: OPTIONS preflight (what browser sends before POST)
print("=" * 80)
print("Testing CORS Preflight (OPTIONS request)")
print("=" * 80)

try:
    response = requests.options(
        API_URL,
        headers={
            "Origin": "https://www.guvi.in",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "x-api-key,content-type"
        },
        timeout=10
    )
    print(f"\n✓ Status Code: {response.status_code}")
    print(f"✓ Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'NOT SET')}")
    print(f"✓ Access-Control-Allow-Methods: {response.headers.get('Access-Control-Allow-Methods', 'NOT SET')}")
    print(f"✓ Access-Control-Allow-Headers: {response.headers.get('Access-Control-Allow-Headers', 'NOT SET')}")
    print(f"✓ Access-Control-Allow-Credentials: {response.headers.get('Access-Control-Allow-Credentials', 'NOT SET')}")
    
    if response.headers.get('Access-Control-Allow-Origin') == '*':
        print("\n✅ CORS FIX IS WORKING! Wildcard origin allowed.")
    
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Actual POST request with Origin header (simulating browser)
print("\n" + "=" * 80)
print("Testing Actual POST Request (with Origin header)")
print("=" * 80)

payload = {
    "sessionId": "test-cors-fix-123",
    "message": {
        "sender": "scammer",
        "text": "Your bank account will be blocked today. Verify immediately.",
        "timestamp": "2026-01-31T10:15:30Z"
    },
    "conversationHistory": [],
    "metadata": {
        "channel": "SMS",
        "language": "English",
        "locale": "IN"
    }
}

try:
    response = requests.post(
        API_URL,
        json=payload,
        headers={
            "x-api-key": API_KEY,
            "Content-Type": "application/json",
            "Origin": "https://www.guvi.in"  # Simulate browser request
        },
        timeout=10
    )
    print(f"\n✓ Status Code: {response.status_code}")
    print(f"✓ Response: {response.json()}")
    print(f"✓ Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'NOT SET')}")
    
    if response.status_code == 200:
        print("\n✅ SUCCESS! API is working with CORS fix!")
    else:
        print(f"\n❌ FAILED with status {response.status_code}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("CONCLUSION: If both tests show ✅, the GUVI tester WILL work!")
print("=" * 80)
