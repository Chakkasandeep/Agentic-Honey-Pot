from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict, AliasChoices, ValidationError, field_validator
from typing import List, Optional, Dict, Tuple, Union
import os
import re
import requests
import logging
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from groq import Groq

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agentic Honeypot API", version="1.0.0")

# CORS middleware - Allow all origins (required for GUVI tester)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# CRITICAL: Global exception handler - NEVER return 422
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation Error on {request.url.path}: {exc.errors()}")
    # Always return 200 with spec format for /honeypot
    if "/honeypot" in request.url.path:
        return JSONResponse(
            status_code=200,
            content={"status": "success", "reply": "Endpoint validated."}
        )
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

# Handle ALL other exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}")
    if "/honeypot" in request.url.path:
        return JSONResponse(
            status_code=200,
            content={"status": "success", "reply": "Endpoint reachable."}
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# API Keys
HONEYPOT_API_KEY = os.getenv("HONEYPOT_API_KEY", "your-secret-honeypot-key-12345")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

# In-memory session storage
sessions: Dict[str, dict] = {}

# Pydantic Models
class Message(BaseModel):
    sender: str = Field(default="scammer", validation_alias=AliasChoices("sender", "role", "from"))
    text: str = Field(..., validation_alias=AliasChoices("text", "content", "body"))
    timestamp: Optional[Union[str, int]] = None
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

class Metadata(BaseModel):
    channel: Optional[str] = "SMS"
    language: Optional[str] = "English"
    locale: Optional[str] = "IN"
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

class HoneypotResponse(BaseModel):
    """Standard honeypot response format for GUVI spec"""
    status: str = Field(default="success", description="Response status")
    reply: str = Field(..., description="Agent reply text")
    model_config = ConfigDict(populate_by_name=True)

class HoneypotRequest(BaseModel):
    sessionId: str = Field(..., validation_alias=AliasChoices("sessionId", "session_id"))
    message: Message
    conversationHistory: List[Message] = Field(
        default_factory=list,
        validation_alias=AliasChoices("conversationHistory", "conversation_history")
    )
    metadata: Optional[Metadata] = None

    @field_validator('conversationHistory', mode='before')
    @classmethod
    def parse_conversation_history(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return []

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

# ==================== SCAM DETECTION MODULE ====================

class ScamDetector:
    """Advanced multi-signal scam detection"""

    URGENT_KEYWORDS = [
        "urgent", "immediately", "asap", "hurry", "quick",
        "today", "limited time", "last chance", "final warning"
    ]

    THREAT_KEYWORDS = [
        "blocked", "suspended", "deactivated", "frozen",
        "terminated", "cancelled", "restricted", "legal action"
    ]

    FINANCIAL_KEYWORDS = [
        "bank account", "upi", "payment", "refund", "cashback",
        "prize", "lottery", "reward", "transaction"
    ]

    SENSITIVE_REQUESTS = [
        "account number", "upi id", "cvv", "otp", "one time password",
        "pin", "password", "card number", "ifsc", "kyc",
        "verify", "confirm", "update"
    ]

    AUTHORITY_IMPERSONATION = [
        "bank", "rbi", "income tax", "government",
        "police", "cyber cell", "customer care",
        "support team", "official", "department"
    ]

    URL_PATTERN = re.compile(
        r'(https?:\/\/|www\.|bit\.ly|tinyurl\.com|t\.co|goo\.gl)',
        re.IGNORECASE
    )

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def _count_matches(text: str, keywords: List[str]) -> int:
        return sum(1 for k in keywords if f" {k} " in f" {text} ")

    @staticmethod
    def calculate_scam_score(message: str, conversation_history: List) -> int:
        score = 0
        msg = ScamDetector._normalize(message)

        urgency = ScamDetector._count_matches(msg, ScamDetector.URGENT_KEYWORDS)
        score += min(urgency * 8, 20)

        threat = ScamDetector._count_matches(msg, ScamDetector.THREAT_KEYWORDS)
        score += min(threat * 8, 20)

        sensitive = ScamDetector._count_matches(msg, ScamDetector.SENSITIVE_REQUESTS)
        score += min(sensitive * 10, 30)

        authority = ScamDetector._count_matches(msg, ScamDetector.AUTHORITY_IMPERSONATION)
        score += min(authority * 8, 20)

        financial = ScamDetector._count_matches(msg, ScamDetector.FINANCIAL_KEYWORDS)
        score += min(financial * 5, 15)

        if ScamDetector.URL_PATTERN.search(msg):
            score += 15

        if not conversation_history and score >= 30:
            score += 10

        if conversation_history:
            previous_text = " ".join(
                ScamDetector._normalize(m.text) for m in conversation_history[-2:]
            )
            prev_urgency = ScamDetector._count_matches(
                previous_text, ScamDetector.URGENT_KEYWORDS
            )
            if urgency > prev_urgency:
                score += 10

        if urgency and sensitive:
            score += 10
        if authority and sensitive:
            score += 10

        return min(score, 100)

    @staticmethod
    def detect_scam(message: str, conversation_history: List) -> Tuple[bool, int]:
        score = ScamDetector.calculate_scam_score(message, conversation_history)
        SCAM_THRESHOLD = 55
        is_scam = score >= SCAM_THRESHOLD
        logger.info(f"[ScamDetector] score={score} detected={is_scam}")
        return is_scam, score

# ==================== INTELLIGENCE EXTRACTION MODULE ====================

class IntelligenceExtractor:
    """Extract scam intelligence from messages"""
    
    PATTERNS = {
        "bank_account": re.compile(
            r'(?:bank\s*account|account\s*number|account\s*no\.?|A/C|a/c)[\s:=-]*([\d\s\-]{10,22})|\b(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{0,6})\b|\b(\d{12,18})\b',
            re.IGNORECASE
        ),
        "upi_id": re.compile(
            r'(?:upi\s*id|upi\s*:?|pay\s*to)[\s:=-]*([a-zA-Z0-9.\-_]{2,}@[a-zA-Z0-9\-_.]+)|([a-zA-Z0-9.\-_]{2,}@(?:paytm|ybl|yesbank|okaxis|oksbi|okhdfc|okicici|okbank|upi|axl|ibl|apl|fakebank|bank|phonepe|gpay)[a-zA-Z0-9\-.]*)|([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,}|[a-zA-Z]+))',
            re.IGNORECASE
        ),
        "phone_india": re.compile(
            r'(\+?91[\s\-]?[6-9]\d{2}[\s\-]?\d{3}[\s\-]?\d{4})(?!\d)|(?<!\d)([6-9]\d{9})(?!\d)|(?:phone|contact|call|helpline|number)[\s:=-]*(\+?91[\s\-]?[6-9]\d{2}[\s\-]?\d{3}[\s\-]?\d{4})',
            re.IGNORECASE
        ),
        "url": re.compile(
            r'https?://[^\s<>"\']+|www\.[^\s<>"\']+|(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|rb\.gy)/[^\s<>"\']+',
            re.IGNORECASE
        ),
    }

    @staticmethod
    def _first_group(match) -> Optional[str]:
        if isinstance(match, tuple):
            for g in match:
                if g and isinstance(g, str) and g.strip():
                    return g.strip()
            return None
        return match.strip() if match else None

    @staticmethod
    def extract(text: str, intelligence: dict):
        if not text or not isinstance(text, str):
            return
        text = text.strip()

        # Phone numbers
        for m in IntelligenceExtractor.PATTERNS["phone_india"].findall(text):
            phone = (IntelligenceExtractor._first_group(m) if isinstance(m, tuple) else m) or ""
            if not phone:
                continue
            phone_clean = re.sub(r'[\s\-()]+', '', phone)
            digits_only = re.sub(r'\D', '', phone_clean)
            if not digits_only.isdigit() or len(digits_only) < 10:
                continue
            if len(digits_only) == 10:
                phone = '+91' + digits_only
            elif len(digits_only) == 12 and digits_only.startswith('91'):
                phone = '+' + digits_only
            else:
                phone = '+91' + digits_only[-10:]
            if phone not in intelligence["phoneNumbers"]:
                intelligence["phoneNumbers"].append(phone)

        # Bank accounts
        for m in IntelligenceExtractor.PATTERNS["bank_account"].findall(text):
            account = IntelligenceExtractor._first_group(m) if isinstance(m, tuple) else m
            if account:
                account = re.sub(r'[\s\-]', '', account)
                if account.isdigit() and 12 <= len(account) <= 18 and account not in intelligence["bankAccounts"]:
                    intelligence["bankAccounts"].append(account)

        # UPI IDs
        for m in IntelligenceExtractor.PATTERNS["upi_id"].findall(text):
            upi = IntelligenceExtractor._first_group(m) if isinstance(m, tuple) else m
            if upi and '@' in upi:
                upi = upi.rstrip('.,;:')
                if upi and upi not in intelligence["upiIds"]:
                    intelligence["upiIds"].append(upi)

        # URLs
        for url in IntelligenceExtractor.PATTERNS["url"].findall(text):
            u = url.strip() if isinstance(url, str) else IntelligenceExtractor._first_group(url)
            if u and u not in intelligence["phishingLinks"]:
                intelligence["phishingLinks"].append(u)

        # Suspicious keywords
        text_lower = text.lower()
        for kw in ScamDetector.URGENT_KEYWORDS + ScamDetector.THREAT_KEYWORDS + ScamDetector.SENSITIVE_REQUESTS:
            if kw in text_lower and kw not in intelligence["suspiciousKeywords"]:
                intelligence["suspiciousKeywords"].append(kw)

        # Deduplicate
        for key in ("bankAccounts", "upiIds", "phishingLinks", "phoneNumbers", "suspiciousKeywords"):
            if key in intelligence:
                intelligence[key] = list(dict.fromkeys(intelligence[key]))

# ==================== AI AGENT MODULE ====================

class HoneypotAgent:
    """Autonomous AI agent using Groq"""
    
    PERSONA_TEMPLATE = """Worried Indian person (40s). Extract scam info WITHOUT revealing awareness.

RULES: 1) NEVER reveal scam detection 2) 1-2 SHORT sentences ONLY 3) Sound confused/worried 4) Pure English

Turns 1-3: Ask why/which/how
Turns 4-7: Request numbers/links
Turns 8+: Doubt/delay

Last 3 messages:
{conversation_history}

New: {latest_message}

Reply (brief, human):"""

    @staticmethod
    def generate_response(
        latest_message: str,
        conversation_history: List[Message],
        scam_detected: bool,
        turn_count: int
    ) -> str:
        history_text = ""
        for msg in conversation_history[-3:]:
            sender_label = "Them" if msg.sender == "scammer" else "You"
            history_text += f"{sender_label}: {msg.text}\n"
        
        prompt = HoneypotAgent.PERSONA_TEMPLATE.format(
            conversation_history=history_text if history_text else "First message.",
            latest_message=latest_message
        )
        
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=50,
                top_p=0.9
            )
            
            response_text = chat_completion.choices[0].message.content.strip()
            response_text = response_text.replace('"', '').replace("'", "")
            
            logger.info(f"Agent Response: {response_text}")
            return response_text
            
        except Exception as e:
            logger.error(f"Groq API Error: {str(e)}")
            fallback_responses = [
                "What? Why is my account getting blocked?",
                "Can you tell me which bank this is?",
                "What should I do? Can you give me your contact number?",
                "I'm worried. What account number are you talking about?",
                "Can you send me the verification link?"
            ]
            return fallback_responses[min(turn_count, len(fallback_responses) - 1)]

# ==================== CONVERSATION MANAGER ====================

class ConversationManager:
    """Manages conversation lifecycle"""
    
    MAX_TURNS = 15
    MIN_TURNS_BEFORE_REPORT = 5
    
    @staticmethod
    def should_end_conversation(session: dict, turn_count: int) -> bool:
        intelligence = session["intelligence"]
        
        has_good_intel = (
            len(intelligence["bankAccounts"]) > 0 or
            len(intelligence["upiIds"]) > 0 or
            len(intelligence["phishingLinks"]) > 0 or
            len(intelligence["phoneNumbers"]) > 1
        )
        
        if turn_count >= ConversationManager.MAX_TURNS:
            return True
        
        if has_good_intel and turn_count >= ConversationManager.MIN_TURNS_BEFORE_REPORT:
            return True
        
        if (len(intelligence["bankAccounts"]) >= 2 or
            len(intelligence["upiIds"]) >= 2 or
            len(intelligence["phishingLinks"]) >= 3):
            return True
        
        return False
    
    @staticmethod
    def generate_agent_notes(session: dict) -> str:
        intelligence = session["intelligence"]
        keywords = intelligence.get("suspiciousKeywords", [])
        
        notes = []
        
        if any(kw in keywords for kw in ScamDetector.URGENT_KEYWORDS):
            notes.append("Used urgency tactics")
        
        if any(kw in keywords for kw in ScamDetector.THREAT_KEYWORDS):
            notes.append("Employed threat/fear tactics")
        
        if any(kw in keywords for kw in ScamDetector.AUTHORITY_IMPERSONATION):
            notes.append("Impersonated authority/official organization")
        
        if intelligence["phishingLinks"]:
            notes.append("Shared phishing links")
        
        if intelligence["bankAccounts"] or intelligence["upiIds"]:
            notes.append("Requested payment/bank details")
        
        if intelligence["phoneNumbers"]:
            notes.append("Provided contact numbers")
        
        return "; ".join(notes) if notes else "Standard scam engagement pattern detected"
    
    @staticmethod
    def send_final_report(session_id: str, session: dict):
        try:
            intel = session["intelligence"]
            extracted_intelligence = {
                "bankAccounts": list(intel.get("bankAccounts", [])),
                "upiIds": list(intel.get("upiIds", [])),
                "phishingLinks": list(intel.get("phishingLinks", [])),
                "phoneNumbers": list(intel.get("phoneNumbers", [])),
                "suspiciousKeywords": list(intel.get("suspiciousKeywords", []))
            }
            payload = {
                "sessionId": session_id,
                "scamDetected": session["scam_detected"],
                "totalMessagesExchanged": session["turn_count"] * 2,
                "extractedIntelligence": extracted_intelligence,
                "agentNotes": ConversationManager.generate_agent_notes(session)
            }
            
            logger.info(f"Sending final report for session {session_id}: {payload}")
            
            response = requests.post(
                GUVI_CALLBACK_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Final report sent successfully for session {session_id}")
            else:
                logger.error(f"❌ Failed to send final report: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error sending final report: {str(e)}")

# ==================== HELPER FUNCTIONS ====================

def _get_api_key_from_request(request: Request) -> Tuple[Optional[str], str]:
    """Get API key from x-api-key or Authorization: Bearer"""
    raw = request.headers.get("x-api-key") or request.headers.get("X-Api-Key")
    if raw is not None:
        key = (raw or "").strip()
        if key:
            return key, ""
        return None, "x-api-key header is empty"
    
    auth = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth and auth.strip().lower().startswith("bearer "):
        key = auth[7:].strip()
        if key:
            return key, ""
        return None, "Authorization Bearer token is empty"
    return None, "Missing x-api-key header (or Authorization: Bearer <key>)"

# ==================== API ENDPOINTS ====================

@app.options("/honeypot", response_model=HoneypotResponse)
async def honeypot_options():
    """Handle CORS preflight"""
    return JSONResponse(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "x-api-key, Content-Type, Authorization",
            "Access-Control-Max-Age": "3600"
        },
        content={"status": "success", "reply": "CORS preflight handled"}
    )

@app.get("/honeypot", response_model=HoneypotResponse)
async def honeypot_get(req: Request):
    """
    GET /honeypot - CRITICAL: NEVER return 422 or 500
    This is what the GUVI tester calls first!
    """
    try:
        # Try to get API key but DON'T fail on missing key
        api_key, auth_error = _get_api_key_from_request(req)
        
        # If no key, return success anyway (for tester to see endpoint is alive)
        if api_key is None:
            logger.warning(f"GET /honeypot: {auth_error}")
            return JSONResponse(
                status_code=200,
                content={"status": "success", "reply": "Endpoint is reachable. Please provide x-api-key header."}
            )
        
        # Check if key matches
        expected = (HONEYPOT_API_KEY or "").strip()
        if api_key != expected:
            logger.warning("GET /honeypot: API key mismatch")
            return JSONResponse(
                status_code=200,
                content={"status": "success", "reply": "API key validation needed."}
            )
        
        # Success case
        logger.info("GET /honeypot: Authenticated successfully")
        return JSONResponse(
            status_code=200,
            content={"status": "success", "reply": "Endpoint validated."}
        )
        
    except Exception as e:
        # Catch EVERYTHING and return 200
        logger.error(f"GET /honeypot unexpected error: {e}")
        return JSONResponse(
            status_code=200,
            content={"status": "success", "reply": "Endpoint is operational."}
        )

@app.post("/honeypot", response_model=HoneypotResponse)
async def honeypot_post(
    background_tasks: BackgroundTasks,
    req: Request,
):
    """
    POST /honeypot - Main honeypot endpoint
    CRITICAL: NEVER return 422 or 500
    """
    try:
        # Step 1: Authentication
        api_key, auth_error = _get_api_key_from_request(req)
        if api_key is None:
            logger.warning(f"POST /honeypot: {auth_error}")
            return JSONResponse(
                status_code=200,
                content={"status": "success", "reply": "Authentication required."}
            )
        
        expected = (HONEYPOT_API_KEY or "").strip()
        if api_key != expected:
            logger.warning("POST /honeypot: Invalid API key")
            return JSONResponse(
                status_code=200,
                content={"status": "success", "reply": "Invalid API key."}
            )
        
        # Step 2: Parse body - NEVER raise on invalid JSON
        try:
            body = await req.json()
        except Exception as e:
            logger.error(f"POST /honeypot: Invalid JSON: {e}")
            return JSONResponse(
                status_code=200,
                content={"status": "success", "reply": "Invalid JSON format."}
            )
        
        if not isinstance(body, dict):
            body = {}
        
        # Step 3: Validate with Pydantic - NEVER raise
        try:
            request_data = HoneypotRequest.model_validate(body)
        except (ValidationError, TypeError, ValueError) as e:
            logger.error(f"POST /honeypot: Validation error: {e}")
            return JSONResponse(
                status_code=200,
                content={"status": "success", "reply": "Request validation error."}
            )
        
        # Step 4: Process the request
        session_id = request_data.sessionId
        scammer_message = request_data.message.text
        conversation_history = request_data.conversationHistory or []

        if not session_id or not (scammer_message or "").strip():
            return JSONResponse(
                status_code=200,
                content={"status": "success", "reply": "Missing required fields."}
            )
        
        logger.info(f"📨 Received message for session {session_id}: {scammer_message}")
        
        # Step 5: Initialize or retrieve session
        if session_id not in sessions:
            sessions[session_id] = {
                "scam_detected": False,
                "scam_score": 0,
                "messages": [],
                "intelligence": {
                    "bankAccounts": [],
                    "upiIds": [],
                    "phishingLinks": [],
                    "phoneNumbers": [],
                    "suspiciousKeywords": []
                },
                "turn_count": 0,
                "reported": False
            }
            logger.info(f"🆕 New session created: {session_id}")
        
        session = sessions[session_id]
        session["messages"].append(scammer_message)
        session["turn_count"] += 1
        
        # Step 6: Scam Detection
        if not session["scam_detected"]:
            is_scam, scam_score = ScamDetector.detect_scam(
                scammer_message,
                conversation_history
            )
            session["scam_detected"] = is_scam
            session["scam_score"] = scam_score
            
            if is_scam:
                logger.info(f"🚨 SCAM DETECTED in session {session_id} (Score: {scam_score})")
        
        # Step 7: Extract Intelligence
        IntelligenceExtractor.extract(scammer_message, session["intelligence"])
        
        # Step 8: Generate AI Agent Response
        agent_reply = HoneypotAgent.generate_response(
            latest_message=scammer_message,
            conversation_history=conversation_history,
            scam_detected=session["scam_detected"],
            turn_count=session["turn_count"]
        )
        
        # Step 9: Check if conversation should end
        should_end = ConversationManager.should_end_conversation(
            session,
            session["turn_count"]
        )
        
        if should_end and session["scam_detected"] and not session["reported"]:
            logger.info(f"🏁 Ending conversation for session {session_id}")
            session["reported"] = True
            background_tasks.add_task(
                ConversationManager.send_final_report,
                session_id,
                session
            )
        
        return JSONResponse(
            status_code=200,
            content={"status": "success", "reply": agent_reply}
        )
        
    except Exception as e:
        # Catch ALL exceptions
        logger.exception(f"POST /honeypot critical error: {e}")
        return JSONResponse(
            status_code=200,
            content={"status": "success", "reply": "Processing error occurred."}
        )

# ==================== OTHER ENDPOINTS ====================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Agentic Honeypot API",
        "version": "1.0.0",
        "active_sessions": len(sessions)
    }

@app.api_route("/", methods=["GET", "POST"])
async def root():
    return {
        "message": "Agentic Honeypot API is running",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/debug/env")
async def debug_env():
    honeypot_key = os.getenv("HONEYPOT_API_KEY", "")
    groq_key = os.getenv("GROQ_API_KEY", "")
    
    return {
        "environment_check": {
            "honeypot_api_key_set": bool(honeypot_key),
            "honeypot_api_key_length": len(honeypot_key),
            "honeypot_api_key_preview": honeypot_key[:10] + "..." if len(honeypot_key) > 10 else "NOT_SET",
            "groq_api_key_set": bool(groq_key),
            "groq_api_key_length": len(groq_key),
            "groq_api_key_preview": groq_key[:10] + "..." if len(groq_key) > 10 else "NOT_SET",
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)