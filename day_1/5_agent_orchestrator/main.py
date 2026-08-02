from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import json
import hmac
import hashlib
import base64
from config import settings
from agent_core import process_message
from line_client import reply_message
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Line Agent Orchestrator")

def verify_signature(body: bytes, signature: str) -> bool:
    """Verifies the LINE webhook signature."""
    if not settings.line_channel_secret:
        return False
    hash_val = hmac.new(
        settings.line_channel_secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(hash_val).decode('utf-8')
    return hmac.compare_digest(signature, expected_signature)

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/webhook/line")
async def line_webhook(request: Request):
    """Receives LINE webhook events."""
    signature = request.headers.get("x-line-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Signature")

    body = await request.body()
    
    if not verify_signature(body, signature):
        logger.warning("Invalid signature.")
        raise HTTPException(status_code=401, detail="Invalid Signature")

    try:
        payload = json.loads(body.decode('utf-8'))
        events = payload.get('events', [])
        
        for event in events:
            reply_token = event.get('replyToken')
            if not reply_token:
                continue
                
            event_type = event.get('type')
            if event_type == 'message':
                message_type = event.get('message', {}).get('type')
                if message_type == 'text':
                    text = event['message']['text']
                    user_id = event.get('source', {}).get('userId', 'unknown')
                    
                    try:
                        reply_text = process_message(user_id, text)
                        reply_message(reply_token, reply_text)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                else:
                    reply_message(reply_token, "I can only process text messages for now.")
            else:
                logger.info(f"Ignoring event type: {event_type}")
                
        return PlainTextResponse("OK", status_code=200)
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return PlainTextResponse("Internal Server Error", status_code=500)