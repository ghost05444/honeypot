from fastapi import FastAPI, Header, Request
import json

app = FastAPI()

API_KEY = "api0544ghosthoneypotmm0np1"


@app.get("/")
def health():
    return {"status": "alive"}


@app.post("/honeypot/message")
async def honeypot(request: Request, x_api_key: str | None = Header(None)):
    # --- AUTH ---
    if x_api_key != API_KEY:
        return {"status": "unauthorized"}

    # --- RAW BODY HANDLING ---
    try:
        body_bytes = await request.body()
        if not body_bytes:
            # GUVI validator ping
            return {
                "status": "ok",
                "message": "Honeypot endpoint reachable"
            }

        payload = json.loads(body_bytes.decode("utf-8"))

    except Exception:
        # Malformed JSON or weird validator request
        return {
            "status": "ok",
            "message": "Honeypot endpoint reachable"
        }

    # --- SAFE FIELD EXTRACTION ---
    session_id = payload.get("sessionId")
    message = payload.get("message", {})
    text = message.get("text", "")

    # --- MINIMAL AGENT RESPONSE (FOR NOW) ---
    return {
        "status": "success",
        "reply": "Why is my account being suspended?"
    }
