from fastapi import FastAPI, Header, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import re
import time
from fastapi.responses import JSONResponse
import os

# python -m uvicorn main:app

# IMPORTANT: requests import
import requests

app = FastAPI()

# ================= CONFIG =================

API_KEY = "api0544ghosthoneypotmm0np1"

GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

SCAM_KEYWORDS = [
    "blocked",
    "verify",
    "urgent",
    "account",
    "suspended",
    "click",
    "immediately"
]

AGENT_TACTICS = [
    "I'm not sure why my account would be blocked. Can you explain?",
    "Okay, what do I need to do to fix this?",
    "Is this really from the bank? I'm a bit worried.",
    "One second, my phone is slow. Please tell me again."
]

sessions = {}

# ================= MODELS =================

class Message(BaseModel):
    sender: str
    text: str
    timestamp: str

class Metadata(BaseModel):
    channel: Optional[str] = None
    language: Optional[str] = None
    locale: Optional[str] = None

class HoneypotRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Message] = []
    metadata: Optional[Metadata] = None

# ================= CALLBACK =================

def send_final_callback(session_id: str, session: dict):
    payload = {
        "sessionId": session_id,
        "scamDetected": session["scamDetected"],
        "totalMessagesExchanged": len(session["history"]),
        "extractedIntelligence": {
            "bankAccounts": [],
            "upiIds": session["intelligence"]["upiIds"],
            "phishingLinks": session["intelligence"]["phishingLinks"],
            "phoneNumbers": session["intelligence"]["phoneNumbers"],
            "suspiciousKeywords": session["intelligence"]["suspiciousKeywords"]
        },
        "agentNotes": "Scammer used urgency tactics and payment redirection"
    }

    try:
        r = requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
        print(f">>> GUVI CALLBACK SENT [{r.status_code}] for session {session_id}")
    except Exception as e:
        # NEVER crash API
        print(">>> GUVI CALLBACK FAILED (safe ignore):", e)

# ================= ROUTES =================

@app.get("/")
def root():
    return {"message": "Honeypot API is running"}

@app.post("/honeypot/message")
def receive_message(
    payload: HoneypotRequest,
    x_api_key: str = Header(None)
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    session_id = payload.sessionId
    text = payload.message.text
    text_lower = text.lower()

    if session_id not in sessions:
        sessions[session_id] = {
            "history": [],
            "scamDetected": False,
            "agentActive": False,
            "agentTurn": 0,
            "finalCallbackSent": False,
            "intelligence": {
                "upiIds": [],
                "phishingLinks": [],
                "phoneNumbers": [],
                "suspiciousKeywords": []
            }
        }

    session = sessions[session_id]

    # Store message
    session["history"].append({
        "sender": payload.message.sender,
        "text": text,
        "timestamp": payload.message.timestamp
    })

    # Scam detection + keywords
    for word in SCAM_KEYWORDS:
        if word in text_lower:
            session["scamDetected"] = True
            if word not in session["intelligence"]["suspiciousKeywords"]:
                session["intelligence"]["suspiciousKeywords"].append(word)

    # UPI extraction
    for upi in re.findall(r"[a-zA-Z0-9._-]+@[a-zA-Z]+", text):
        if upi not in session["intelligence"]["upiIds"]:
            session["intelligence"]["upiIds"].append(upi)

    # URL extraction
    for url in re.findall(r"https?://[^\s]+", text):
        if url not in session["intelligence"]["phishingLinks"]:
            session["intelligence"]["phishingLinks"].append(url)

    # Phone number extraction
    for phone in re.findall(r"(?:\+91[\-\s]?)?[6-9]\d{9}", text):
        if phone not in session["intelligence"]["phoneNumbers"]:
            session["intelligence"]["phoneNumbers"].append(phone)

    # Agent activation
    if session["scamDetected"]:
        session["agentActive"] = True

        agent_reply = None

    if session["agentActive"]:
        agent_reply = AGENT_TACTICS[session["agentTurn"] % len(AGENT_TACTICS)]
        session["history"].append({
            "sender": "user",
            "text": agent_reply,
            "timestamp": payload.message.timestamp
        })
        session["agentTurn"] += 1

    # FINAL CALLBACK (safe)
    if session["agentTurn"] >= 3 and not session["finalCallbackSent"]:
        send_final_callback(session_id, session)
        session["finalCallbackSent"] = True

    # 🚨 UNCONDITIONAL RETURN — THIS FIXES NULL 🚨
    return {
        "status": "received",
        "sessionId": session_id,
        "totalMessages": len(session["history"]),
        "scamDetected": session["scamDetected"],
        "agentActive": session["agentActive"],
        "agentReply": agent_reply,
        "extractedIntelligence": session["intelligence"]
    }



