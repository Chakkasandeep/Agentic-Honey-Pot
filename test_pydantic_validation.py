"""Test Pydantic validation with exact GUVI spec format"""
from pydantic import BaseModel, Field, ConfigDict, AliasChoices
from typing import List, Optional, Union

class Message(BaseModel):
    sender: str
    text: str
    timestamp: Optional[Union[str, int]] = None
    
    model_config = ConfigDict(populate_by_name=True)

class Metadata(BaseModel):
    channel: Optional[str] = "SMS"
    language: Optional[str] = "English"
    locale: Optional[str] = "IN"
    
    model_config = ConfigDict(populate_by_name=True)

class HoneypotRequest(BaseModel):
    """Request body per GUVI spec: camelCase keys (sessionId, message, conversationHistory, metadata)."""
    sessionId: str = Field(..., validation_alias=AliasChoices("sessionId", "session_id"))
    message: Message
    conversationHistory: List[Message] = Field(
        default_factory=list,
        validation_alias=AliasChoices("conversationHistory", "conversation_history")
    )
    metadata: Optional[Metadata] = None

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

# Test 1: GUVI spec format (first message)
test_data_1 = {
    "sessionId": "test-123",
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

# Test 2: GUVI spec format (second message)
test_data_2 = {
    "sessionId": "wertyu-dfghj-ertyui",
    "message": {
        "sender": "scammer",
        "text": "Share your UPI ID to avoid account suspension.",
        "timestamp": "2026-01-21T10:17:10Z"
    },
    "conversationHistory": [
        {
            "sender": "scammer",
            "text": "Your bank account will be blocked today. Verify immediately.",
            "timestamp": "2026-01-21T10:15:30Z"
        },
        {
            "sender": "user",
            "text": "Why will my account be blocked?",
            "timestamp": "2026-01-21T10:16:10Z"
        }
    ],
    "metadata": {
        "channel": "SMS",
        "language": "English",
        "locale": "IN"
    }
}

# Test 3: Minimal required fields (no metadata)
test_data_3 = {
    "sessionId": "test-456",
    "message": {
        "sender": "scammer",
        "text": "Urgent! Your account will be suspended."
    }
}

# Test 4: No conversationHistory field at all
test_data_4 = {
    "sessionId": "test-789",
    "message": {
        "sender": "scammer",
        "text": "Send me your UPI ID",
        "timestamp": "2026-01-21T10:15:30Z"
    },
    "metadata": {
        "channel": "SMS",
        "language": "English",
        "locale": "IN"
    }
}

print("Testing Pydantic validation:")
print("=" * 60)

for i, test_data in enumerate([test_data_1, test_data_2, test_data_3, test_data_4], 1):
    print(f"\n✅ Test {i}: ", end="")
    try:
        request = HoneypotRequest.model_validate(test_data)
        print(f"PASSED")
        print(f"   sessionId: {request.sessionId}")
        print(f"   message.text: {request.message.text}")
        print(f"   conversationHistory length: {len(request.conversationHistory)}")
        print(f"   metadata: {request.metadata}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Test data: {test_data}")

print("\n" + "=" * 60)
print("All tests completed!")
