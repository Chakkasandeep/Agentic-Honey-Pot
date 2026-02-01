"""Local test: request validation + extraction (no server)."""
import sys
sys.path.insert(0, ".")

# Test 1: Request body validation (exact GUVI spec)
from main import HoneypotRequest, IntelligenceExtractor, ScamDetector

payload = {
    "sessionId": "wertyu-dfghj-ertyui",
    "message": {
        "sender": "scammer",
        "text": "Your bank account will be blocked today. Verify immediately.",
        "timestamp": "2026-01-21T10:15:30Z"
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
}
req = HoneypotRequest.model_validate(payload)
assert req.sessionId == "wertyu-dfghj-ertyui"
assert "blocked" in req.message.text
print("1. Request body (camelCase): OK")

# Test 2: Extraction
intel = {
    "bankAccounts": [], "upiIds": [], "phishingLinks": [],
    "phoneNumbers": [], "suspiciousKeywords": []
}
text = "Your SBI account 1234567890123456 is blocked! Contact +91-9876543210. UPI: scammer@yesbank. Visit http://fake-bank.com"
IntelligenceExtractor.extract(text, intel)
assert "1234567890123456" in intel["bankAccounts"], f"Bank not found: {intel['bankAccounts']}"
assert any("yesbank" in u for u in intel["upiIds"]), f"UPI not found: {intel['upiIds']}"
assert any("9876543210" in p for p in intel["phoneNumbers"]), f"Phone not found: {intel['phoneNumbers']}"
assert any("fake-bank" in u for u in intel["phishingLinks"]), f"URL not found: {intel['phishingLinks']}"
assert "blocked" in intel["suspiciousKeywords"], f"Keywords: {intel['suspiciousKeywords']}"
print("2. Extraction (bank, UPI, phone, URL, keywords): OK")
print("All local tests passed.")
