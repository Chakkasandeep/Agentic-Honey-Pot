"""
Test what the GUVI API Endpoint Tester might be sending
to understand why we get 422 error
"""
import requests
import json

API_URL = "https://agentic-honey-pot-e7mc.onrender.com/honeypot"
API_KEY = "UoxDHBe1m83w5zRtaAwz-FF70-8T94c4O6tZmHmjcu8"

print("=" * 80)
print("TESTING GUVI API ENDPOINT TESTER SCENARIOS")
print("=" * 80)

# Scenario 1: GET request (what GUVI might send first to validate)
print("\n📋 Test 1: GET request with x-api-key")
try:
    response = requests.get(
        API_URL,
        headers={"x-api-key": API_KEY}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Scenario 2: POST with empty body (what tester might send)
print("\n📋 Test 2: POST with empty body")
try:
    response = requests.post(
        API_URL,
        headers={"x-api-key": API_KEY},
        json={}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 422:
        print(f"❌ 422 Error - Validation failed!")
        print(f"Response: {response.json()}")
    else:
        print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Scenario 3: POST with minimal valid payload
print("\n📋 Test 3: POST with minimal valid payload")
try:
    response = requests.post(
        API_URL,
        headers={"x-api-key": API_KEY},
        json={
            "sessionId": "guvi-test",
            "message": {
                "sender": "scammer",
                "text": "Test"
            }
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Scenario 4: POST with snake_case field names (what GUVI might use)
print("\n📋 Test 4: POST with snake_case (session_id instead of sessionId)")
try:
    response = requests.post(
        API_URL,
        headers={"x-api-key": API_KEY},
        json={
            "session_id": "guvi-test",
            "message": {
                "sender": "scammer",
                "text": "Test"
            }
        }
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Scenario 5: POST with no body at all
print("\n📋 Test 5: POST with no JSON body")
try:
    response = requests.post(
        API_URL,
        headers={"x-api-key": API_KEY}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 422:
        print(f"❌ 422 Error - This is likely what GUVI is sending!")
        print(f"Response: {response.json()}")
    else:
        print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
