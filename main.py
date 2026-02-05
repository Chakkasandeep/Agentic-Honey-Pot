# ================================
# AEGIS AI — FIXED VERSION
# ================================

import os
import re
import json
import logging
import traceback
import random
from dataclasses import dataclass, field, asdict
from typing import Dict, List
from threading import Lock
from functools import wraps

from flask import Flask, request, jsonify, make_response
from groq import Groq
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PORT = int(os.getenv("PORT", 5000))

if not API_KEY:
    raise RuntimeError("Missing API_KEY")

CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

groq = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AEGIS")

app = Flask(__name__)

session_store: Dict[str, "Session"] = {}
lock = Lock()

# =====================================================
# MODELS
# =====================================================

@dataclass
class Intelligence:
    bankAccounts: List[str] = field(default_factory=list)
    upiIds: List[str] = field(default_factory=list)
    phishingLinks: List[str] = field(default_factory=list)
    phoneNumbers: List[str] = field(default_factory=list)
    suspiciousKeywords: List[str] = field(default_factory=list)
    employeeIds: List[str] = field(default_factory=list)


@dataclass
class Session:
    id: str
    total_messages: int = 0  # Total messages in conversation (both scammer + honeypot)
    scammer_messages: int = 0  # Only scammer messages
    scam_detected: bool = False
    scam_type: str = "unknown"
    intelligence: Intelligence = field(default_factory=Intelligence)
    full_conversation: str = ""  # Store entire conversation for final extraction
    callback_sent: bool = False  # Prevent duplicate callbacks


# =====================================================
# AUTH
# =====================================================

def require_api_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.headers.get("x-api-key") != API_KEY:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper


# =====================================================
# IMPROVED EXTRACTOR
# =====================================================

class Extractor:
    
    # ✅ FIXED: Better bank account pattern (10-18 digits)
    BANK = re.compile(r'\b\d{10,18}\b')
    
    # ✅ FIXED: Employee ID pattern (supports "ID is 45678" format)
    EMPLOYEE = re.compile(
        r'(?:employee\s*(?:id|ID|Id)|ID|id)\s*(?:is|:)?\s*([A-Z0-9]{4,10})\b',
        re.I
    )
    
    # ✅ FIXED: Phone patterns (normalize to +91XXXXXXXXXX format)
    PHONE_PATTERNS = [
        re.compile(r'\+91[-\s]?(\d{10})'),           # +91-9876543210
        re.compile(r'\b91[-\s]?(\d{10})'),            # 91-9876543210
        re.compile(r'\b([6-9]\d{9})\b'),              # 9876543210
    ]
    
    # ✅ UPI pattern
    UPI = re.compile(
        r'\b([\w.-]{3,}@(?:upi|ybl|okaxis|oksbi|paytm|ibl|axl|okicici|okhdfcbank|phonepe|googlepay|airtel))\b',
        re.I
    )
    
    # ✅ URL pattern
    URL = re.compile(r'https?://[^\s<>"\']+|www\.[^\s<>"\']+')
    
    # ✅ Suspicious keywords
    KEYWORDS = {
        "otp", "urgent", "verify", "blocked", "suspended",
        "bank", "upi", "account", "click", "transfer",
        "security", "alert", "locked", "immediately", "confirm"
    }

    @classmethod
    def extract(cls, text):
        """Extract intelligence from text with improved patterns"""
        
        # Extract bank accounts
        bank_accounts = list(set(cls.BANK.findall(text)))
        
        # Extract employee IDs
        employee_ids = []
        for match in cls.EMPLOYEE.finditer(text):
            emp_id = match.group(1).upper()
            if emp_id and emp_id not in employee_ids:
                employee_ids.append(emp_id)
        
        # Extract and normalize phone numbers
        phones = set()
        for pattern in cls.PHONE_PATTERNS:
            for match in pattern.finditer(text):
                # Get just the 10-digit number
                digits = ''.join(filter(str.isdigit, match.group(0)))[-10:]
                if len(digits) == 10 and digits[0] in '6789':
                    phones.add(f"+91{digits}")
        
        # Extract UPI IDs
        upis = {match[0].lower() for match in cls.UPI.findall(text)}
        
        # Extract URLs
        urls = list(set(cls.URL.findall(text)))
        
        # Extract keywords
        text_lower = text.lower()
        keywords = [k for k in cls.KEYWORDS if k in text_lower]
        
        return {
            "bankAccounts": bank_accounts,
            "employeeIds": employee_ids,
            "phoneNumbers": list(phones),
            "upiIds": list(upis),
            "phishingLinks": urls,
            "suspiciousKeywords": keywords
        }


# =====================================================
# SCAM DETECTOR
# =====================================================

class Detector:

    HIGH = {"otp", "pin", "password", "cvv", "card"}
    MED = {"urgent", "blocked", "verify", "suspended", "locked"}
    CTX = {"bank", "account", "payment", "upi", "transfer"}

    @classmethod
    def detect(cls, text, intel):
        """Detect if message is a scam"""
        
        t = text.lower()
        
        score = (
            0.3 * sum(w in t for w in cls.HIGH) +
            0.15 * sum(w in t for w in cls.MED) +
            0.1 * sum(w in t for w in cls.CTX)
        )
        
        if intel["upiIds"]:
            score += 0.25
        if intel["bankAccounts"]:
            score += 0.25
        if intel["phoneNumbers"]:
            score += 0.15
        if intel["employeeIds"]:
            score += 0.15
            
        return score >= 0.35


# =====================================================
# AGENT WITH VARIED RESPONSES
# =====================================================

SYSTEM_PROMPT = """You are Ramesh, a 67-year-old retired Indian man.

PERSONALITY:
- Polite, worried, not tech-savvy
- Confused by technical terms
- Want to verify everything before acting
- Concerned about account safety

BEHAVIOR:
- Never reveal you detect scams
- Ask natural questions to extract information
- Show genuine concern and confusion
- Vary your responses - don't repeat same questions
- Keep replies to 1-2 short sentences

GOALS (extract naturally):
- Bank account numbers
- Phone numbers
- Employee IDs
- OTP requests
- Verification methods

Return ONLY valid JSON:
{
  "reply": "your response here",
  "intelligence": {
    "bankAccounts": [],
    "phoneNumbers": [],
    "employeeIds": [],
    "upiIds": []
  }
}"""

# ✅ VARIED fallback responses to prevent repetition
FALLBACK_POOL = [
    "Oh my... I'm very worried. What exactly do I need to do?",
    "I don't understand computers well. Can you help me step by step?",
    "How can I verify you are really from the bank?",
    "Should I go to the bank branch instead? I'm not sure about this.",
    "My grandson usually helps me with these things. Can I call him first?",
    "I'm confused. Can you explain this more simply?",
    "What happens if I don't do this right now?",
    "Can I verify this through the bank's official website?",
]

USED_FALLBACKS = {}  # Track used fallbacks per session


def agent_reply(msg, history, session):
    """Generate agent reply with variety and intelligence extraction"""
    
    if not groq:
        # Use varied fallbacks
        if session.id not in USED_FALLBACKS:
            USED_FALLBACKS[session.id] = []
        
        available = [f for f in FALLBACK_POOL if f not in USED_FALLBACKS[session.id]]
        if not available:
            USED_FALLBACKS[session.id] = []
            available = FALLBACK_POOL
        
        reply = random.choice(available)
        USED_FALLBACKS[session.id].append(reply)
        return reply, {}

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Include last 6 messages for context
    for h in history[-6:]:
        role = "assistant" if h["sender"] == "user" else "user"
        messages.append({"role": role, "content": h["text"]})
    
    messages.append({"role": "user", "content": msg})

    try:
        completion = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0.8,  # Higher temp for more variety
            max_tokens=150,  # Reduced token usage
            response_format={"type": "json_object"},
            messages=messages
        )
        
        result = json.loads(completion.choices[0].message.content)
        
        reply = result.get("reply", "")
        intel = result.get("intelligence", {})
        
        # Fallback if reply is empty
        if not reply or len(reply.strip()) < 5:
            reply = random.choice(FALLBACK_POOL)
        
        return reply, intel
        
    except Exception as e:
        logger.error(f"Agent error: {e}")
        return random.choice(FALLBACK_POOL), {}


# =====================================================
# INTELLIGENCE MERGER
# =====================================================

def merge(existing, *sources):
    """Merge intelligence from multiple sources"""
    
    def combine(k):
        data = set(getattr(existing, k))
        for s in sources:
            data.update(s.get(k, []))
        return list(data)
    
    return Intelligence(
        bankAccounts=combine("bankAccounts"),
        upiIds=combine("upiIds"),
        phishingLinks=combine("phishingLinks"),
        phoneNumbers=combine("phoneNumbers"),
        suspiciousKeywords=combine("suspiciousKeywords"),
        employeeIds=combine("employeeIds")
    )


# =====================================================
# SESSION CONTROL
# =====================================================

def should_end(session):
    """Determine if conversation should end"""
    
    intel_count = sum(len(v) for v in asdict(session.intelligence).values())
    
    # End conditions:
    # 1. At least 10 total messages exchanged AND gathered some intelligence
    # 2. OR gathered significant intelligence (5+ items)
    
    if session.scammer_messages >= 7 and intel_count >= 3:
        return True
    
    if intel_count >= 5:
        return True
    
    # Max conversation length
    if session.scammer_messages >= 12:
        return True
        
    return False


def get_session(sid):
    """Get or create session"""
    with lock:
        if sid not in session_store:
            session_store[sid] = Session(id=sid)
        return session_store[sid]


# =====================================================
# FINAL EXTRACTION & CALLBACK
# =====================================================

def final_extraction(session):
    """Perform final extraction on entire conversation before callback"""
    
    # Re-extract from full conversation text
    final_intel = Extractor.extract(session.full_conversation)
    
    # Merge with existing intelligence
    session.intelligence = merge(session.intelligence, final_intel)
    
    logger.info(f"Final extraction complete: {asdict(session.intelligence)}")


def send_callback(session):
    """Send final results to evaluation endpoint"""
    
    if session.callback_sent:
        logger.warning(f"Callback already sent for session {session.id}")
        return
    
    # Perform final extraction
    final_extraction(session)
    
    payload = {
        "sessionId": session.id,
        "scamDetected": True,
        "totalMessagesExchanged": session.total_messages,
        "extractedIntelligence": asdict(session.intelligence),
        "agentNotes": f"Scam engagement completed. {session.scammer_messages} scammer messages analyzed."
    }
    
    logger.info(f"CALLBACK PAYLOAD:\n{json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(CALLBACK_URL, json=payload, timeout=10)
        logger.info(f"Callback response: {response.status_code}")
        session.callback_sent = True
    except Exception as e:
        logger.error(f"Callback failed: {e}")
    
    # Clean up session after callback
    with lock:
        session_store.pop(session.id, None)


# =====================================================
# ROUTES
# =====================================================

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/honeypot", methods=["POST", "OPTIONS"])
@require_api_key
def honeypot():
    """Main honeypot endpoint"""
    
    if request.method == "OPTIONS":
        return make_response("", 204)
    
    data = request.get_json(silent=True)
    
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400
    
    sid = data.get("sessionId")
    text = data.get("message", {}).get("text", "").strip()
    history = data.get("conversationHistory", [])
    
    if not sid or not text:
        return jsonify({"status": "error", "message": "Bad request"}), 400
    
    session = get_session(sid)
    
    # ✅ FIX: Count total messages correctly
    # total_messages = scammer messages + honeypot messages
    # We receive scammer message -> reply with honeypot message
    session.scammer_messages += 1
    session.total_messages = len(history) + 1  # history + current scammer message
    
    # Store conversation for final extraction
    session.full_conversation += f"\nScammer: {text}"
    
    # Extract intelligence from current message
    regex_intel = Extractor.extract(text)
    
    # Also extract from entire conversation history
    history_text = " ".join([h["text"] for h in history])
    history_intel = Extractor.extract(history_text)
    
    # Detect scam
    is_scam = Detector.detect(text, regex_intel)
    
    # Force engagement in early messages
    if session.scammer_messages <= 5:
        is_scam = True
    
    if is_scam:
        session.scam_detected = True
    
    # Generate reply
    reply, llm_intel = agent_reply(text, history, session)
    
    # Add honeypot reply to conversation
    session.full_conversation += f"\nHoneypot: {reply}"
    session.total_messages += 1  # Now add the honeypot response
    
    # Merge all intelligence
    session.intelligence = merge(session.intelligence, regex_intel, history_intel, llm_intel)
    
    logger.info(f"Session {sid}: Message {session.scammer_messages}, Total: {session.total_messages}")
    logger.info(f"Extracted: {asdict(session.intelligence)}")
    
    # Check if should end
    if should_end(session):
        logger.info(f"Ending session {sid}")
        send_callback(session)
    
    return jsonify({
        "status": "success",
        "reply": reply
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)