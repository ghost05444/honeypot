from fastapi import FastAPI, Header, HTTPException, Body
import requests
import re
from datetime import datetime

app = FastAPI()

# ================= CONFIG =================

API_KEY = "api0544ghosthoneypotmm0np1"  # <-- HARD-CODED KEY (validator-safe)

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

# In-memory session store
sessions = {}

# =========================================


@app.get("/")
def root():
    return {"message": "Honeypot API is running"}


@app.post("/honeypot/message")
def receive_message(
    payload: dict = Body(default={}),
    x_api_key: str = Header(None)
):
    # ---------- AUTH ----------
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # ---------- VALIDATOR SAFE GUARD ----------
    # GUVI validator may send a minimal or empty body
    if not payload or "message" not in payload:
        return {
            "status": "ok",
            "message": "Honeypot endpoint reachable"
        }

    # ---------- EXTRACT FIELDS SAFELY ----------
    session_id = payload.get("sessionId", "unknown-session")
    message = payload.get("message", {})
    text = message.get("text", "")
    timestamp = message.get("timestamp", datetime.utcnow().isoformat())

    # ---------- INIT SESSION ----------
    if session_id not in sessions:
        sessions[session_id] = {
            "history": [],
            "scamDetected": False,
            "agentActive": False,
            "turns": 0,
            "intelligence": {
                "upiIds": [],
                "phishingLinks": [],
                "phoneNumbers": [],
                "suspiciousKeywords": []
            }
        }

    session = sessions[session_id]

    # ---------- STORE MESSAGE ----------
    session["history"].append({
        "sender": "scammer",
        "text": text,
        "timestamp": timestamp
    })

    # ---------- SCAM DETECTION ----------
    lowered = text.lower()
    for word in SCAM_KEYWORDS:
        if word in lowered:
            session["scamDetected"] = True
            session["agentActive"] = True
            if word not in session["intelligence"]["suspiciousKeywords"]:
                session["intelligence"]["suspiciousKeywords"].append(word)

    # ---------- INTELLIGENCE EXTRACTION ----------
    # UPI IDs
    upis = re.findall(r"\b[\w.\-]+@[\w]+\b", text)
    for u in upis:
        if u not in session["intelligence"]["upiIds"]:
            session["intelligence"]["upiIds"].append(u)

    # Phone numbers
    phones = re.findall(r"\+?\d{10,13}", text)
    for p in phones:
        if p not in session["intelligence"]["phoneNumbers"]:
            session["intelligence"]["phoneNumbers"].append(p)

    # URLs
    urls = re.findall(r"https?://[^\s]+", text)
    for url in urls:
        if url not in session["intelligence"]["phishingLinks"]:
            session["intelligence"]["phishingLinks"].append(url)

    # ---------- AGENT RESPONSE ----------
    agent_reply = None
    if session["agentActive"]:
        replies = [
            "Why would my account be blocked?",
            "Verify what exactly?",
            "Why do I need to send money for this?",
            "I'm confused, can you explain slowly?",
            "I just used my account, nothing seemed wrong."
        ]
        agent_reply = replies[session["turns"] % len(replies)]
        session["turns"] += 1

        session["history"].append({
            "sender": "user",
            "text": agent_reply,
            "timestamp": timestamp
        })

    # ---------- FINAL RESPONSE ----------
    return {
        "status": "received",
        "sessionId": session_id,
        "totalMessages": len(session["history"]),
        "scamDetected": session["scamDetected"],
        "agentActive": session["agentActive"],
        "agentReply": agent_reply,
        "extractedIntelligence": session["intelligence"]
    }
