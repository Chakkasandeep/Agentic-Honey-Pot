"""
Agentic Honey-Pot for Scam Detection & Intelligence Extraction
TOKEN-OPTIMIZED VERSION - Final Intelligence Return Only
"""

import os
import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict, field
from functools import wraps

from flask import Flask, request, jsonify, make_response
from groq import Groq
import requests

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration
API_KEY = os.getenv('API_KEY', 'UoxDHBe1m83w5zRtaAwz-FF70-8T94c4O6tZmHmjcu8')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# Initialize Groq client
groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
        logger.info("✅ Groq client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Groq: {e}")
else:
    logger.warning("⚠️  GROQ_API_KEY not set!")

# Session storage
session_store = {}


# ==================== CORS ====================

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, x-api-key, Authorization'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response


# ==================== DATA MODELS ====================

@dataclass
class ExtractedIntelligence:
    bankAccounts: List[str] = field(default_factory=list)
    upiIds: List[str] = field(default_factory=list)
    phishingLinks: List[str] = field(default_factory=list)
    phoneNumbers: List[str] = field(default_factory=list)
    suspiciousKeywords: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {k: v for k, v in asdict(self).items() if v}


@dataclass
class SessionData:
    session_id: str
    message_count: int = 0
    scam_detected: bool = False
    scam_confidence: float = 0.0
    intelligence: ExtractedIntelligence = field(default_factory=ExtractedIntelligence)
    agent_notes: List[str] = field(default_factory=list)
    asked_topics: Set[str] = field(default_factory=set)


# ==================== PATTERN EXTRACTION ====================

class PatternExtractor:
    
    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        phones = []
        patterns = [
            r'\+91[\s\-]?([6-9]\d{9})',
            r'\b([6-9]\d{9})\b',
            r'\b91[\s\-]?([6-9]\d{9})\b'
        ]
        for pattern in patterns:
            phones.extend(re.findall(pattern, text))
        
        validated = []
        for phone in phones:
            clean = re.sub(r'[\s\-]', '', phone)
            if len(clean) == 10 and clean[0] in '6789':
                validated.append(f"+91{clean}")
        return list(set(validated))
    
    @staticmethod
    def extract_upi_ids(text: str) -> List[str]:
        pattern = r'\b([\w\.\-]{3,}@(?:upi|paytm|ybl|okaxis|okicici|okhdfcbank|axl|ibl|oksbi|fbl|apl|barodampay|cnrb|ezeepay|fam|hdfcbank|icici|indus|idfcbank|jupiteraxis|kotak|myairtel|pockets|sbi|hsbc|timecosmos|wahaciti))\b'
        upis = re.findall(pattern, text, re.IGNORECASE)
        return [u.lower() for u in upis if '@' in u and len(u.split('@')[0]) >= 3]
    
    @staticmethod
    def extract_urls(text: str) -> List[str]:
        urls = []
        patterns = [
            r'https?://[^\s<>"\'\[\]{}\\^`|]+',
            r'\b(?:bit\.ly|tinyurl\.com|goo\.gl|ow\.ly)/\w+',
            r'\b(?:www\.)?[\w\-]+\.(?:tk|ml|ga|cf|gq|xyz|top|club|site|online)\b'
        ]
        urls.extend(re.findall(patterns[0], text))
        urls.extend([f"http://{u}" for u in re.findall(patterns[1], text)])
        urls.extend([f"http://{u}" for u in re.findall(patterns[2], text, re.IGNORECASE)])
        return list(set(urls))
    
    @staticmethod
    def extract_bank_accounts(text: str) -> List[str]:
        matches = re.findall(r'\b(\d{11,18})\b', text)
        return [acc for acc in matches if len(acc) >= 11 and not (len(acc) == 10 and acc[0] in '6789')]
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        keywords = {
            'urgency': ['urgent', 'immediately', 'now', 'asap', 'expire'],
            'threat': ['blocked', 'suspended', 'locked', 'freeze'],
            'verify': ['verify', 'confirm', 'validate', 'authenticate'],
            'financial': ['bank', 'account', 'payment', 'transaction', 'transfer'],
            'creds': ['otp', 'pin', 'password', 'cvv'],
            'action': ['click', 'link', 'update', 'share'],
            'reward': ['prize', 'winner', 'refund', 'cashback'],
            'authority': ['rbi', 'customer care', 'support team']
        }
        text_lower = text.lower()
        found = []
        for category, kws in keywords.items():
            found.extend([kw for kw in kws if kw in text_lower])
        return list(set(found))
    
    @classmethod
    def extract_all(cls, text: str) -> Dict[str, List[str]]:
        return {
            'phoneNumbers': cls.extract_phone_numbers(text),
            'upiIds': cls.extract_upi_ids(text),
            'phishingLinks': cls.extract_urls(text),
            'bankAccounts': cls.extract_bank_accounts(text),
            'suspiciousKeywords': cls.extract_keywords(text)
        }


# ==================== SCAM DETECTION ====================

class ScamDetector:
    SIGNALS = {
        'high': ['otp', 'pin', 'cvv', 'password', 'blocked', 'suspended'],
        'med': ['urgent', 'immediately', 'verify', 'confirm', 'expire'],
        'ctx': ['bank', 'account', 'payment', 'upi', 'transfer']
    }
    
    @classmethod
    def calculate_risk(cls, text: str, has_url: bool, has_phone: bool) -> float:
        text_lower = text.lower()
        score = sum(0.3 for kw in cls.SIGNALS['high'] if kw in text_lower)
        score += sum(0.15 for kw in cls.SIGNALS['med'] if kw in text_lower)
        score += sum(0.1 for kw in cls.SIGNALS['ctx'] if kw in text_lower)
        if has_url: score += 0.2
        if has_phone: score += 0.15
        return min(score, 1.0)
    
    @classmethod
    def is_likely_scam(cls, text: str, intel: Dict) -> Tuple[bool, float]:
        has_url = len(intel.get('phishingLinks', [])) > 0
        has_phone = len(intel.get('phoneNumbers', [])) > 0
        score = cls.calculate_risk(text, has_url, has_phone)
        return score >= 0.4, score


# ==================== AI AGENT (OPTIMIZED PROMPT) ====================

class Agent:
    # REDUCED TOKEN PROMPT - Concise but effective
    SYSTEM_PROMPT = """You are Ramesh Kumar, 67, retired teacher from India.

PERSONA:
- Polite, worried, tech-confused
- Simple English, occasional Hindi
- Trusting but asks questions
- Concerned about money/account

STRATEGY:
- NEVER reveal scam detection
- Ask: employee ID, callback number, UPI details, verification steps
- NO repeat questions (check history)
- 1-2 short sentences max
- Use: "Oh dear", "Accha", "Haan ji"

EXTRACT: phone, UPI, bank account, URL, employee details

OUTPUT JSON ONLY:
{
  "is_scam": true/false,
  "confidence": 0.0-1.0,
  "reply": "response here",
  "intelligence": {
    "bankAccounts": [],
    "upiIds": [],
    "phishingLinks": [],
    "phoneNumbers": [],
    "suspiciousKeywords": []
  }
}"""
    
    @classmethod
    def generate_response(
        cls, 
        msg: str,
        history: List[Dict],
        session: SessionData,
        regex_intel: Dict
    ) -> Tuple[bool, float, str, Dict]:
        
        if not groq_client:
            return cls._fallback(msg, session)
        
        # Build compact messages
        messages = [{"role": "system", "content": cls.SYSTEM_PROMPT}]
        
        # Last 4 messages only (save tokens)
        recent = history[-4:] if len(history) > 4 else history
        for m in recent:
            role = "assistant" if m['sender'] == 'user' else "user"
            messages.append({"role": role, "content": m['text']})
        
        messages.append({"role": "user", "content": msg})
        
        # COMPACT context (minimal tokens)
        context = f"""Msg #{session.message_count}
Asked: {', '.join(list(session.asked_topics)[-3:])}
Regex: {json.dumps(regex_intel)}
Respond as Ramesh. Extract NEW intel. JSON only."""
        
        messages.append({"role": "user", "content": context})
        
        try:
            logger.info(f"🤖 LLM call for session {session.session_id}")
            
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.8,
                max_tokens=300,  # Reduced from 400
                response_format={"type": "json_object"}
            )
            
            response = completion.choices[0].message.content.strip()
            result = json.loads(response)
            
            is_scam = result.get('is_scam', False)
            confidence = float(result.get('confidence', 0.7))
            reply = result.get('reply', "I'm not sure. Can you explain?")
            llm_intel = result.get('intelligence', {})
            
            # Track question topic
            if '?' in reply:
                topic = cls._extract_topic(reply)
                if topic:
                    session.asked_topics.add(topic)
            
            logger.info(f"✅ Scam: {is_scam} | Conf: {confidence:.2f}")
            return is_scam, confidence, reply, llm_intel
            
        except Exception as e:
            logger.error(f"❌ LLM error: {e}")
            return cls._fallback(msg, session)
    
    @staticmethod
    def _extract_topic(reply: str) -> Optional[str]:
        topics = {
            'employee': ['employee', 'id'],
            'phone': ['phone', 'number', 'contact'],
            'upi': ['upi', 'payment'],
            'account': ['account', 'bank'],
            'process': ['how', 'what', 'next']
        }
        reply_lower = reply.lower()
        for topic, kws in topics.items():
            if any(kw in reply_lower for kw in kws):
                return topic
        return None
    
    @staticmethod
    def _fallback(msg: str, session: SessionData) -> Tuple[bool, float, str, Dict]:
        import random
        logger.warning("⚠️ Fallback mode")
        
        text_lower = msg.lower()
        signals = ['otp', 'pin', 'blocked', 'suspended', 'urgent']
        count = sum(1 for s in signals if s in text_lower)
        
        is_scam = count >= 2
        confidence = min(count * 0.3, 0.9)
        
        if session.message_count <= 2:
            replies = [
                "Oh my! Can you tell me your employee ID?",
                "Which bank department? What's your number?",
                "How do I know this is real? Your contact?"
            ]
        elif session.message_count <= 5:
            replies = [
                "I'm confused. What should I do?",
                "My son handles this. Explain simply?",
                "Is this urgent? Call my daughter?"
            ]
        else:
            replies = [
                "What's the next step?",
                "I don't understand computers well.",
                "What details do you need?"
            ]
        
        return is_scam, confidence, random.choice(replies), {}


# ==================== INTELLIGENCE MERGER ====================

class IntelMerger:
    @staticmethod
    def merge(regex: Dict, llm: Dict, existing: ExtractedIntelligence) -> ExtractedIntelligence:
        def combine(*lists):
            combined = []
            for lst in lists:
                if lst:
                    combined.extend(lst)
            return sorted(list(set(filter(None, combined))))
        
        return ExtractedIntelligence(
            bankAccounts=combine(existing.bankAccounts, regex.get('bankAccounts', []), llm.get('bankAccounts', [])),
            upiIds=combine(existing.upiIds, regex.get('upiIds', []), llm.get('upiIds', [])),
            phishingLinks=combine(existing.phishingLinks, regex.get('phishingLinks', []), llm.get('phishingLinks', [])),
            phoneNumbers=combine(existing.phoneNumbers, regex.get('phoneNumbers', []), llm.get('phoneNumbers', [])),
            suspiciousKeywords=combine(existing.suspiciousKeywords, regex.get('suspiciousKeywords', []), llm.get('suspiciousKeywords', []))
        )


# ==================== SESSION MANAGEMENT ====================

def get_or_create_session(session_id: str) -> SessionData:
    if session_id not in session_store:
        session_store[session_id] = SessionData(session_id=session_id)
        logger.info(f"📝 New session: {session_id}")
    return session_store[session_id]


def should_end_conversation(session: SessionData) -> bool:
    if session.message_count < 8:
        return False
    
    intel = session.intelligence
    score = (
        len(intel.bankAccounts) * 2 +
        len(intel.upiIds) * 2 +
        len(intel.phishingLinks) * 1.5 +
        len(intel.phoneNumbers) * 1.5 +
        len(intel.suspiciousKeywords) * 0.5
    )
    
    if session.message_count >= 20:
        return True
    if score >= 8 and session.message_count >= 10:
        return True
    if session.message_count >= 15 and score >= 4:
        return True
    
    return False


def send_final_callback(session: SessionData):
    """Send ONLY at conversation end - as per requirement"""
    payload = {
        "sessionId": session.session_id,
        "scamDetected": session.scam_detected,
        "totalMessagesExchanged": session.message_count,
        "extractedIntelligence": session.intelligence.to_dict(),
        "agentNotes": " | ".join(session.agent_notes) if session.agent_notes else "Scam engagement completed"
    }
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🏁 FINAL CALLBACK - SESSION: {session.session_id}")
    logger.info(f"{'='*60}")
    logger.info(json.dumps(payload, indent=2))
    logger.info(f"{'='*60}\n")
    
    for attempt in range(3):
        try:
            response = requests.post(
                GUVI_CALLBACK_URL,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Callback success (attempt {attempt + 1})")
                return True
            else:
                logger.warning(f"⚠️  Attempt {attempt + 1} failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Attempt {attempt + 1} error: {e}")
        
        if attempt < 2:
            import time
            time.sleep(1)
    
    logger.error(f"❌ All callback attempts failed: {session.session_id}")
    return False


# ==================== AUTH ====================

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('x-api-key')
        if not api_key or api_key != API_KEY:
            logger.warning(f"Unauthorized: {request.remote_addr}")
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


# ==================== ENDPOINTS ====================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Honeypot API",
        "version": "2.1-token-optimized",
        "llm_available": groq_client is not None,
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route('/honeypot', methods=['GET', 'POST', 'OPTIONS'])
def honeypot_endpoint():
    if request.method == 'OPTIONS':
        return make_response('', 204)
    
    if request.method == 'GET':
        return jsonify({
            "status": "success",
            "message": "Honeypot API operational",
            "version": "2.1-token-optimized"
        }), 200
    
    # Validate API key
    api_key = request.headers.get('x-api-key')
    if not api_key or api_key != API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400
        
        session_id = data.get('sessionId')
        message = data.get('message', {})
        history = data.get('conversationHistory', [])
        
        if not session_id or not message:
            return jsonify({"status": "error", "message": "Missing sessionId or message"}), 400
        
        text = message.get('text', '').strip()
        if not text:
            return jsonify({"status": "error", "message": "Empty message text"}), 400
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📨 SESSION: {session_id} | MSG #{len(history) + 1}")
        logger.info(f"📩 Scammer: {text[:80]}")
        logger.info(f"{'='*60}")
        
        # Get/create session
        session = get_or_create_session(session_id)
        session.message_count += 1
        
        # === PROCESSING ===
        
        # Extract with regex
        regex_intel = PatternExtractor.extract_all(text)
        logger.info(f"🔍 Regex: {sum(len(v) for v in regex_intel.values())} items")
        
        # Scam detection
        likely_scam, risk = ScamDetector.is_likely_scam(text, regex_intel)
        
        # Force LLM for first 3 messages
        if session.message_count <= 3:
            likely_scam = True
        
        # Generate response
        if not likely_scam and not session.scam_detected:
            reply = "I'm not sure I understand. Can you explain?"
            is_scam, confidence = False, risk
            llm_intel = {}
        else:
            is_scam, confidence, reply, llm_intel = Agent.generate_response(
                text, history, session, regex_intel
            )
        
        # Update scam status
        if is_scam and not session.scam_detected:
            session.scam_detected = True
            session.scam_confidence = confidence
            session.agent_notes.append(f"Scam detected at msg {session.message_count} (conf: {confidence:.2f})")
            logger.info(f"🚨 SCAM DETECTED | Confidence: {confidence:.2f}")
        
        # Merge intelligence
        session.intelligence = IntelMerger.merge(regex_intel, llm_intel, session.intelligence)
        
        logger.info(f"💬 Reply: {reply[:60]}")
        logger.info(f"📊 Total intel: {sum(len(v) for v in asdict(session.intelligence).values())} items")
        
        # Check end condition
        if should_end_conversation(session):
            logger.info(f"🏁 Ending session {session_id}")
            send_final_callback(session)  # ONLY HERE - Final callback
            if session_id in session_store:
                del session_store[session_id]
        
        # Return ONLY reply - NO intelligence in response (as per optimization)
        return jsonify({
            "status": "success",
            "reply": reply
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "message": "Internal error"}), 500


@app.route('/stats', methods=['GET'])
@require_api_key
def get_stats():
    total_intel = {}
    for session in session_store.values():
        for key, values in asdict(session.intelligence).items():
            total_intel[key] = total_intel.get(key, 0) + len(values)
    
    return jsonify({
        "status": "success",
        "active_sessions": len(session_store),
        "total_intelligence": total_intel,
        "sessions": [
            {
                "id": s.session_id,
                "messages": s.message_count,
                "scam_detected": s.scam_detected,
                "intel_items": sum(len(v) for v in asdict(s.intelligence).values())
            }
            for s in session_store.values()
        ]
    }), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"status": "error", "message": "Internal error"}), 500


# ==================== MAIN ====================

if __name__ == '__main__':
    logger.info("\n" + "="*60)
    logger.info("🚀 HONEYPOT API - TOKEN OPTIMIZED v2.1")
    logger.info("="*60)
    logger.info(f"✅ API Key: {'Set' if API_KEY else 'Not set'}")
    logger.info(f"✅ Groq LLM: {'Ready' if groq_client else 'Fallback mode'}")
    logger.info(f"✅ Callback: {GUVI_CALLBACK_URL}")
    logger.info("="*60 + "\n")
    
    if not GROQ_API_KEY:
        logger.warning("⚠️  Set GROQ_API_KEY for best performance")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)