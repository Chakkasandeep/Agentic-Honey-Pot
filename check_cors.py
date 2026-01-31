import requests

URL = "https://agentic-honey-pot-e7mc.onrender.com/honeypot"
TEST_ORIGIN = "https://hackathon.guvi.in"

print(f"Checking CORS for: {URL}")
print(f"Simulating Origin: {TEST_ORIGIN}")

try:
    # 1. OPTION Request (Preflight)
    print("\n--- 1. Sending OPTIONS (Preflight) ---")
    headers = {
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,x-api-key",
        "Origin": TEST_ORIGIN
    }
    resp = requests.options(URL, headers=headers)
    print(f"Status: {resp.status_code}")
    print("Relevant Headers:")
    cors_headers = {k: v for k, v in resp.headers.items() if 'access-control' in k.lower()}
    for k, v in cors_headers.items():
        print(f"  {k}: {v}")

    if 'access-control-allow-origin' in [k.lower() for k in cors_headers]:
        print("✅ Preflight CORS headers present")
    else:
        print("❌ Preflight CORS headers MISSING")

    # 2. POST Request (Actual)
    print("\n--- 2. Sending POST (Actual) ---")
    headers = {
        "Content-Type": "application/json",
        "x-api-key": "UoxDHBe1m83w5zRtaAwz-FF70-8T94c4O6tZmHmjcu8",
        "Origin": TEST_ORIGIN
    }
    payload = {
        "sessionId": "cors-check",
        "message": {"sender": "scammer", "text": "hi"},
        "conversationHistory": []
    }
    resp = requests.post(URL, json=payload, headers=headers)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("Response: OK")
    else:
        print(f"Response: {resp.text}")
        
    print("Relevant Headers:")
    cors_headers = {k: v for k, v in resp.headers.items() if 'access-control' in k.lower()}
    for k, v in cors_headers.items():
        print(f"  {k}: {v}")

except Exception as e:
    print(f"Error: {e}")
