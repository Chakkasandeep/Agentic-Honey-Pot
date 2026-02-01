"""Test against the live GUVI API"""
import requests
import json

# Your deployed API
API_URL = "https://agentic-honey-pot-e7mc.onrender.com/honeypot"
API_KEY = "UoxDHBe1m83w5zRtaAwz-FF70-8T94c4O6tZmHmjcu8"

# GUVI spec format - EXACTLY as shown in the requirements
test_payload = {
    "sessionId": "wertyu-dfghj-ertyui",
    "message": {
        "sender": "scammer",
        "text": "Your bank account will be blocked today. Verify immediately.",
        "timestamp": "2026-01-21T10:15:30Z"
    },
    "conversationHistory": [],
    "metadata": {
        "channel": "SMS",
        "language": "English",
        "locale": "IN"
    }
}

print("Testing live API with GUVI spec format...")
print("=" * 70)
print(f"\n📤 Sending Request to: {API_URL}")
print(f"🔑 API Key: {API_KEY[:20]}...")
print(f"\n📦 Payload:")
print(json.dumps(test_payload, indent=2))

try:
    response = requests.post(
        API_URL,
        json=test_payload,
        headers={
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        },
        timeout=30
    )
    
    print(f"\n✅ Response Status: {response.status_code}")
    print(f"📥 Response Headers:")
    for key, value in response.headers.items():
        if key.lower() in ['content-type', 'access-control-allow-origin', 'access-control-allow-methods']:
            print(f"   {key}: {value}")
    
    print(f"\n📄 Response Body:")
    print(json.dumps(response.json(), indent=2))
    
    # Validate response format
    resp_data = response.json()
    if "status" in resp_data and "reply" in resp_data:
        print("\n✅ Response format is CORRECT (has 'status' and 'reply')")
    else:
        print(f"\n❌ Response format is INCORRECT!")
        print(f"   Expected: {{'status': '...', 'reply': '...'}}")
        print(f"   Got: {list(resp_data.keys())}")
    
    # Check for extra keys
    expected_keys = {"status", "reply"}
    actual_keys = set(resp_data.keys())
    extra_keys = actual_keys - expected_keys
    if extra_keys:
        print(f"\n⚠️ Response has extra keys: {extra_keys}")
    
except requests.exceptions.RequestException as e:
    print(f"\n❌ Request failed: {str(e)}")
except json.JSONDecodeError as e:
    print(f"\n❌ Could not decode JSON response: {str(e)}")
    print(f"   Raw response: {response.text}")
except Exception as e:
    print(f"\n❌ Unexpected error: {type(e).__name__}: {str(e)}")

print("\n" + "=" * 70)
