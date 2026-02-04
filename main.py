from fastapi import FastAPI, Header, Request
import json

app = FastAPI()

# Your registered key – double-check it matches exactly what you entered in GUVI
API_KEY = "api0544ghosthoneypotmm0np1"

@app.get("/")
async def health():
    return {"status": "alive"}

@app.post("/honeypot/message")
async def honeypot_message(request: Request, x_api_key: str | None = Header(default=None)):
    # 1. Authentication
    if x_api_key != API_KEY:
        return {"status": "unauthorized"}

    # 2. Read raw bytes to detect empty body reliably
    body_bytes = await request.body()

    # Case A: GUVI ping / empty body test → MUST return this exact response
    if not body_bytes:
        return {
            "status": "ok",
            "message": "Honeypot endpoint reachable"
        }

    # Case B: There is some body → try to parse it
    try:
        payload = json.loads(body_bytes.decode("utf-8"))
        # If we got here → valid JSON arrived → return success shape
        return {
            "status": "success",
            "reply": "What is this about? Can you explain again?"
        }
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Invalid JSON → treat same as ping (safe fallback)
        return {
            "status": "ok",
            "message": "Honeypot endpoint reachable"
        }
