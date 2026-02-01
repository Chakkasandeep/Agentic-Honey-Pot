"""Test all HTTP methods on the honeypot endpoint"""
import requests
import json

API_URL = "https://agentic-honey-pot-e7mc.onrender.com/honeypot"
API_KEY = "UoxDHBe1m83w5zRtaAwz-FF70-8T94c4O6tZmHmjcu8"

methods_to_test = ["OPTIONS", "GET", "POST"]

for method in methods_to_test:
    print(f"\n{'='*70}")
    print(f" Testing {method} request")
    print(f"{'='*70}")
    
    try:
        if method == "OPTIONS":
            response = requests.options(API_URL, headers={"x-api-key": API_KEY}, timeout=10)
        elif method == "GET":
            response = requests.get(API_URL, headers={"x-api-key": API_KEY}, timeout=10)
        elif method == "POST":
            payload = {
                "sessionId": "test-123",
                "message": {
                    "sender": "scammer",
                    "text": "Test message"
                },
                "conversationHistory": []
            }
            response = requests.post(
                API_URL,
                json=payload,
                headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                timeout=10
            )
        
        print(f"Status Code: {response.status_code}")
        print(f"\nResponse Headers:")
        for k, v in response.headers.items():
            if 'access-control' in k.lower() or k.lower() in ['content-type', 'allow']:
                print(f"  {k}: {v}")
        
        if response.text:
            print(f"\nResponse Body:")
            try:
                print(json.dumps(response.json(), indent=2))
            except:
                print(response.text[:500])
        else:
            print("\n(No response body)")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

print(f"\n{'='*70}")
print("Testing completed!")
