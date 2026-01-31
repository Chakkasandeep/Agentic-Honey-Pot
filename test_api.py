"""
Test script for Honeypot API
Run this to validate your deployment
"""

import requests
import json
import time

# Configuration
# Configuration
API_URL = "http://localhost:8000/honeypot"  # Pointing to the specific endpoint
# Should load from .env or be set manually
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("HONEYPOT_API_KEY", "your-secret-key")  # Load from .env

def test_scam_detection():
    """Test 1: Basic scam detection"""
    print("\n" + "="*60)
    print("TEST 1: Basic Scam Detection")
    print("="*60)
    
    payload = {
        "sessionId": "test-session-001",
        "message": {
            "sender": "scammer",
            "text": "Your bank account will be blocked today. Verify immediately at http://fake-bank.com",
            "timestamp": "2026-01-31T10:00:00Z"
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    response = requests.post(
        API_URL,
        json=payload,
        headers={
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        }
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    assert response.status_code == 200, "API should return 200"
    assert response.json()["status"] == "success", "Status should be success"
    assert len(response.json()["reply"]) > 0, "Reply should not be empty"
    
    print("✅ Test 1 PASSED")
    return response.json()["reply"]

def test_multi_turn_conversation():
    """Test 2: Multi-turn conversation"""
    print("\n" + "="*60)
    print("TEST 2: Multi-Turn Conversation")
    print("="*60)
    
    session_id = "test-session-002"
    conversation = []
    
    # Turn 1
    scammer_msg_1 = "Urgent! Your SBI account shows suspicious activity."
    conversation.append({"sender": "scammer", "text": scammer_msg_1, "timestamp": "2026-01-31T10:00:00Z"})
    
    response_1 = requests.post(
        API_URL,
        json={
            "sessionId": session_id,
            "message": {"sender": "scammer", "text": scammer_msg_1, "timestamp": "2026-01-31T10:00:00Z"},
            "conversationHistory": [],
            "metadata": {"channel": "SMS"}
        },
        headers={"x-api-key": API_KEY}
    )
    
    user_reply_1 = response_1.json()["reply"]
    conversation.append({"sender": "user", "text": user_reply_1, "timestamp": "2026-01-31T10:01:00Z"})
    print(f"Turn 1 - Scammer: {scammer_msg_1}")
    print(f"Turn 1 - Agent: {user_reply_1}")
    
    time.sleep(1)
    
    # Turn 2
    scammer_msg_2 = "Share your UPI ID immediately to verify your account."
    conversation.append({"sender": "scammer", "text": scammer_msg_2, "timestamp": "2026-01-31T10:02:00Z"})
    
    response_2 = requests.post(
        API_URL,
        json={
            "sessionId": session_id,
            "message": {"sender": "scammer", "text": scammer_msg_2, "timestamp": "2026-01-31T10:02:00Z"},
            "conversationHistory": conversation[:-1],
            "metadata": {"channel": "SMS"}
        },
        headers={"x-api-key": API_KEY}
    )
    
    user_reply_2 = response_2.json()["reply"]
    print(f"Turn 2 - Scammer: {scammer_msg_2}")
    print(f"Turn 2 - Agent: {user_reply_2}")
    
    assert response_2.status_code == 200, "Multi-turn should work"
    print("✅ Test 2 PASSED")

def test_intelligence_extraction():
    """Test 3: Intelligence extraction"""
    print("\n" + "="*60)
    print("TEST 3: Intelligence Extraction")
    print("="*60)
    
    payload = {
        "sessionId": "test-session-003",
        "message": {
            "sender": "scammer",
            "text": "Transfer money to account 1234567890123, UPI: scammer@paytm, or call 9876543210. Visit http://malicious.link",
            "timestamp": "2026-01-31T10:00:00Z"
        },
        "conversationHistory": [],
        "metadata": {"channel": "SMS"}
    }
    
    response = requests.post(
        API_URL,
        json=payload,
        headers={"x-api-key": API_KEY}
    )
    
    print(f"Message with intelligence: {payload['message']['text']}")
    print(f"Agent Reply: {response.json()['reply']}")
    print("✅ Test 3 PASSED (Check server logs for extracted intelligence)")

def test_authentication():
    """Test 4: API authentication"""
    print("\n" + "="*60)
    print("TEST 4: Authentication")
    print("="*60)
    
    # Test with wrong API key
    response = requests.post(
        API_URL,
        json={"sessionId": "test", "message": {"sender": "scammer", "text": "test", "timestamp": "2026-01-31T10:00:00Z"}},
        headers={"x-api-key": "wrong-key"}
    )
    
    print(f"Wrong key status: {response.status_code}")
    assert response.status_code == 401, "Should reject invalid API key"
    
    # Test with correct API key
    response = requests.post(
        API_URL,
        json={"sessionId": "test", "message": {"sender": "scammer", "text": "test", "timestamp": "2026-01-31T10:00:00Z"}},
        headers={"x-api-key": API_KEY}
    )
    
    print(f"Correct key status: {response.status_code}")
    assert response.status_code == 200, "Should accept valid API key"
    print("✅ Test 4 PASSED")

def test_health_endpoint():
    """Test 5: Health check"""
    print("\n" + "="*60)
    print("TEST 5: Health Check")
    print("="*60)
    
    response = requests.get(API_URL.replace("/honeypot", "/health"))
    print(f"Health: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200, "Health endpoint should work"
    print("✅ Test 5 PASSED")

def run_all_tests():
    """Run all tests"""
    print("\n" + "🍯 HONEYPOT API TEST SUITE")
    print("="*60)
    
    try:
        test_health_endpoint()
        test_authentication()
        test_scam_detection()
        test_multi_turn_conversation()
        test_intelligence_extraction()
        
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        print("\nYour honeypot API is working correctly!")
        print("Next steps:")
        print("1. Deploy to Railway/Render/Fly.io")
        print("2. Update API_URL in this test script to your public URL")
        print("3. Run tests again to verify deployment")
        print("4. Submit your public URL to GUVI")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except requests.exceptions.ConnectionError:
        print(f"\n❌ CONNECTION ERROR: Cannot connect to {API_URL}")
        print("Make sure the API is running:")
        print("  python main.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    print("\n⚙️  Configuration:")
    print(f"API URL: {API_URL}")
    print(f"API Key: {API_KEY}")
    print("\n⚠️  Update these values before running tests!\n")
    
    input("Press Enter to start tests...")
    run_all_tests()