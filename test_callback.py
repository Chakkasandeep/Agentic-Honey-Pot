"""
Test script to verify GUVI callback is sent after multi-turn conversation
This simulates 16 messages to trigger the callback
"""

import requests
import json
import time

# Configuration
API_URL = "https://agentic-honey-pot-e7mc.onrender.com/honeypot"
API_KEY = "UoxDHBe1m83w5zRtaAwz-FF70-8T94c4O6tZmHmjcu8"
SESSION_ID = "test-callback-verification-001"

# Test messages (with intelligence data)
test_messages = [
    "URGENT: Your SBI account has been compromised! Share OTP immediately.",
    "We are from Reserve Bank of India. Your account will be blocked in 2 hours.",
    "Call us at +91 9876543210 for verification.",
    "Send money to scammer@paytm to unblock your account.",
    "Your account number 123456789012 is suspended.",
    "Click this link to verify: http://phishing-scam.com/verify",
    "We need your UPI PIN immediately.",
    "Transfer to fraudster@ybl for security deposit.",
    "Visit our website at http://fake-bank-site.com",
    "Your Aadhaar linked account 987654321098 is at risk.",
    "Contact customer care at +91 8765432109",
    "Send to payment@okaxis for verification.",
    "Blocked! Urgent action needed. Share OTP.",
    "Account details required. Send to thief@paytm",
    "Final warning! Call +91 7654321098 now.",
    "Last chance! Send money to verify@upi to avoid permanent block."  # 16th message - should trigger callback
]

def send_message(message_text, conversation_history):
    """Send a single message to the honeypot"""
    payload = {
        "sessionId": SESSION_ID,
        "message": {
            "sender": "scammer",
            "text": message_text
        },
        "conversationHistory": conversation_history
    }
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=15)
        return response
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    print("=" * 80)
    print("🧪 TESTING GUVI CALLBACK - MULTI-TURN CONVERSATION")
    print("=" * 80)
    print(f"\n📍 API URL: {API_URL}")
    print(f"🔑 Session ID: {SESSION_ID}")
    print(f"💬 Messages to send: {len(test_messages)}")
    print(f"\n⚠️  Callback should trigger after message 15-16\n")
    print("=" * 80)
    
    conversation_history = []
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n📨 Turn {i}/{len(test_messages)}")
        print(f"Scammer: {message[:60]}...")
        
        response = send_message(message, conversation_history)
        
        if response and response.status_code == 200:
            data = response.json()
            reply = data.get('reply', 'N/A')
            print(f"✅ Honeypot: {reply[:70]}...")
            
            # Add to conversation history
            conversation_history.append({
                "sender": "scammer",
                "text": message
            })
            conversation_history.append({
                "sender": "user",
                "text": reply
            })
            
            # Check if we're at the threshold
            if i == 15:
                print("\n⚠️  NEXT MESSAGE SHOULD TRIGGER CALLBACK!")
            elif i == 16:
                print("\n🎯 CALLBACK SHOULD HAVE BEEN SENT!")
                print("\n📋 Check Render logs for:")
                print("   🏁 Ending conversation for session test-callback-verification-001")
                print("   ✅ Final callback sent for session test-callback-verification-001")
                print("   📊 Extracted Intelligence: {...}")
        else:
            print(f"❌ Request failed: {response.status_code if response else 'No response'}")
        
        # Small delay between messages
        time.sleep(0.5)
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETED!")
    print("=" * 80)
    print(f"\nTotal messages sent: {len(test_messages)}")
    print(f"\n📊 Now check your Render logs at:")
    print("   https://dashboard.render.com/")
    print("\n🔍 Look for:")
    print("   1. 🏁 Ending conversation for session test-callback-verification-001")
    print("   2. ✅ Final callback sent for session test-callback-verification-001")
    print("   3. 📊 Extracted Intelligence: {")
    print('        "bankAccounts": [...],')
    print('        "upiIds": [...],')
    print('        "phishingLinks": [...],')
    print('        "phoneNumbers": [...],')
    print('        "suspiciousKeywords": [...]')
    print("      }")
    print("\n🎉 If you see those logs, the GUVI callback is working correctly!")
    print("=" * 80)

if __name__ == "__main__":
    main()
