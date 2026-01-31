import requests
import json
import time

BASE_URL = "https://agentic-honey-pot-e7mc.onrender.com"
API_URL = f"{BASE_URL}/honeypot"
HEALTH_URL = f"{BASE_URL}/health"
API_KEY = "UoxDHBe1m83w5zRtaAwz-FF70-8T94c4O6tZmHmjcu8"

print(f"Testing Base URL: {BASE_URL}")

# Test Health
print("\n1. Testing Health Endpoint...")
try:
    start = time.time()
    response = requests.get(HEALTH_URL, timeout=60)
    print(f"Health Status: {response.status_code} (took {time.time() - start:.2f}s)")
    print(f"Health Body: {response.text}")
except Exception as e:
    print(f"Health Check Failed: {e}")

# Test Honeypot
print("\n2. Testing Honeypot Endpoint...")
payload = {
    "sessionId": "debug-session-002",
    "message": {
        "sender": "scammer",
        "text": "Hello, this is a test message.",
        "timestamp": "2026-01-31T12:00:00Z"
    },
    "conversationHistory": [],
    "metadata": {
        "channel": "debug"
    }
}

try:
    start = time.time()
    response = requests.post(
        API_URL,
        json=payload,
        headers={
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        },
        timeout=60
    )
    
    print(f"Honeypot Status: {response.status_code} (took {time.time() - start:.2f}s)")
    try:
        print(f"Honeypot Body: {response.json()}")
    except:
        print(f"Honeypot Text: {response.text}")

except Exception as e:
    print(f"Honeypot Request Failed: {e}")
