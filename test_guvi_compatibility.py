"""
Test script to diagnose GUVI API Tester compatibility issues
"""
import requests
import json

API_URL = "https://agentic-honey-pot-e7mc.onrender.com/honeypot"
API_KEY = "UoxDHBe1m83w5zRtaAwz-FF70-8T94c4O6tZmHmjcu8"

def test_with_different_header_formats():
    """Test the API with different header formats to identify the issue"""
    
    payload = {
        "sessionId": "test-session-123",
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
    
    print("=" * 80)
    print("GUVI API Compatibility Test")
    print("=" * 80)
    
    # Test 1: Standard x-api-key header (what GUVI should send)
    print("\n Test 1: Using 'x-api-key' header...")
    try:
        response = requests.post(
            API_URL,
            json=payload,
            headers={
                "x-api-key": API_KEY,
                "Content-Type": "application/json"
            },
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Case variations
    print("\n✓ Test 2: Using 'X-API-KEY' header (uppercase)...")
    try:
        response = requests.post(
            API_URL,
            json=payload,
            headers={
                "X-API-KEY": API_KEY,
                "Content-Type": "application/json"
            },
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Without Content-Type
    print("\n✓ Test 3: Without explicit Content-Type...")
    try:
        response = requests.post(
            API_URL,
            json=payload,
            headers={
                "x-api-key": API_KEY
            },
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 4: With Authorization header
    print("\n✓ Test 4: Using 'Authorization: Bearer' format...")
    try:
        response = requests.post(
            API_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 5: OPTIONS request (CORS preflight)
    print("\n✓ Test 5: Testing CORS preflight (OPTIONS request)...")
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
        print(f"Status Code: {response.status_code}")
        print(f"CORS Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)

if __name__ == "__main__":
    test_with_different_header_formats()
