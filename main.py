from fastapi import FastAPI, Header, Body
from typing import Optional

app = FastAPI()

API_KEY = "api0544ghosthoneypotmm0np1"

@app.get("/")
def health():
    return {"status": "alive"}

@app.post("/honeypot/message")
def honeypot(
    payload: Optional[dict] = Body(None),
    x_api_key: Optional[str] = Header(None)
):
    if x_api_key != API_KEY:
        return {"status": "unauthorized"}

    # GUVI may send empty body
    if payload is None:
        return {
            "status": "ok",
            "message": "Honeypot endpoint reachable"
        }

    return {
        "status": "received",
        "sessionId": payload.get("sessionId"),
        "message": "Message accepted"
    }
