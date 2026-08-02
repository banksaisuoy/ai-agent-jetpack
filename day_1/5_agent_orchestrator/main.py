import json
import hmac
import hashlib
import base64
from fastapi import FastAPI, Request, HTTPException
from config import settings
from line_client import reply_message
import logging

from line_handler import LineWebhookHandler, HandlerConfig, RedisSessionManager, NLUParser, AgentRouter
from agent_core import process_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize the new handler components
config = HandlerConfig()
session_manager = RedisSessionManager(redis_url="redis://localhost:6379/0")
parser = NLUParser()
router = AgentRouter()

# Map the general intent to the original process_message logic
def general_agent_handler(text: str, context: dict) -> str:
    user_id = context.get("user_id", "unknown")
    return process_message(user_id, text)

# Map some standard behaviors
def weather_agent_handler(text: str, context: dict) -> str:
    return "The weather is currently sunny."

router.register_route("general", general_agent_handler)
router.register_route("weather", weather_agent_handler)
router.set_default_route(general_agent_handler)

webhook_handler = LineWebhookHandler(
    config=config,
    session_manager=session_manager,
    parser=parser,
    router=router
)

def verify_signature(body: bytes, signature: str) -> bool:
    hash_val = hmac.new(settings.line_channel_secret.encode('utf-8'), body, hashlib.sha256).digest()
    expected_signature = base64.b64encode(hash_val).decode('utf-8')
    return hmac.compare_digest(expected_signature, signature)

@app.post("/webhook/line")
async def line_webhook(request: Request):
    signature = request.headers.get('x-line-signature')
    body = await request.body()

    if not signature or not verify_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        payload = json.loads(body.decode('utf-8'))
        events = payload.get('events', [])
        
        for event in events:
            reply_token = event.get('replyToken')
            if not reply_token:
                continue

            user_id = event.get("source", {}).get("userId")
            
            if event.get('type') == 'message' and event.get('message', {}).get('type') == 'text':
                # Update context with user_id to ensure general_agent_handler has it
                if user_id:
                    ctx = session_manager.get_session(user_id)
                    ctx["user_id"] = user_id
                    session_manager.save_session(user_id, ctx)
                
                # Delegate to the LineWebhookHandler
                response_text = webhook_handler.handle_event(event)
                
                if response_text:
                    reply_message(reply_token, response_text)
            elif event.get('type') == 'message':
                reply_message(reply_token, "I can only process text messages for now.")
                
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return "Error"

    return "OK"