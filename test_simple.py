"""
Simulate EXACTLY what GUVI tester might be sending
"""
import requests
import json

print("="*80)
print("SIMULATING GUVI TESTER REQUEST")
print("="*80)

url = "https://agentic-honey-pot-e7mc.onrender.com/honeypot"
api_key = "UoxDHBe1m83w5zRtaAwz-FF70-8T94c4O6tZmHmjcu8"

# Test 1: Exactly as shown in GUVI tester
headers = {
    "x-api-key": api_key,
    "Content-Type": "application/json"
}

# Minimal payload as GUVI might send
payload = {
    "sessionId": "test-guvi-123",
    "message": {
        "sender": "scammer",
        "text": "Test message"
    },
    "conversationHistory": []
}

print(f"\nURL: {url}")
print(f"Headers: {headers}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("\nSending request...")

try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"\n✓ Status Code: {response.status_code}")
    print(f"✓ Response: {response.text}")
    
    if response.status_code == 200:
        print("\n✅ SUCCESS - API IS WORKING!")
    elif response.status_code == 401:
        print("\n❌ 401 UNAUTHORIZED - API KEY ISSUE")
        print(f"Response detail: {response.json()}")
    else:
        print(f"\n❌ FAILED with status {response.status_code}")
        
except requests.exceptions.Timeout:
    print("\n❌ TIMEOUT - Render might be asleep or overloaded")
except requests.exceptions.ConnectionError as e:
    print(f"\n❌ CONNECTION ERROR: {e}")
except Exception as e:
    print(f"\n❌ ERROR: {e}")

print("="*80)
