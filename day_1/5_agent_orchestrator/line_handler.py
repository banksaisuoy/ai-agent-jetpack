import json
import logging
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
import redis
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

@dataclass
class HandlerConfig:
    """Configuration for the LineWebhookHandler with filtering capabilities."""
    allowed_event_types: List[str] = field(default_factory=lambda: ["message"])
    allowed_message_types: List[str] = field(default_factory=lambda: ["text"])
    blocked_user_ids: List[str] = field(default_factory=list)
    redis_url: str = "redis://localhost:6379/0"
    
    def is_allowed(self, event: Dict[str, Any]) -> bool:
        event_type = event.get("type")
        if event_type not in self.allowed_event_types:
            return False
            
        if event_type == "message":
            msg_type = event.get("message", {}).get("type")
            if msg_type not in self.allowed_message_types:
                return False
                
        user_id = event.get("source", {}).get("userId")
        if user_id in self.blocked_user_ids:
            return False
            
        return True

class RedisSessionManager:
    """Manages session state and context preservation across requests using Redis."""
    
    def __init__(self, redis_url: str, session_ttl: int = 3600):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.session_ttl = session_ttl
        
    def get_session(self, user_id: str) -> Dict[str, Any]:
        """Retrieves session context for a user."""
        try:
            data = self.redis_client.get(f"session:{user_id}")
            if data:
                return json.loads(data)
            return {}
        except redis.RedisError as e:
            logger.error(f"Redis get error for user {user_id}: {e}")
            return {}
            
    def save_session(self, user_id: str, context: Dict[str, Any]) -> bool:
        """Saves session context for a user."""
        try:
            self.redis_client.setex(
                f"session:{user_id}", 
                self.session_ttl, 
                json.dumps(context)
            )
            return True
        except redis.RedisError as e:
            logger.error(f"Redis save error for user {user_id}: {e}")
            return False
            
    def clear_session(self, user_id: str) -> bool:
        """Clears session context for a user."""
        try:
            self.redis_client.delete(f"session:{user_id}")
            return True
        except redis.RedisError as e:
            logger.error(f"Redis delete error for user {user_id}: {e}")
            return False

class NLUParser:
    """Mock NLU Parser for detecting agent categories based on intents and message types."""
    
    def parse(self, text: str) -> str:
        """Parses text and returns the detected intent/category."""
        text_lower = text.lower()
        if "weather" in text_lower or "forecast" in text_lower:
            return "weather"
        elif "book" in text_lower or "flight" in text_lower or "hotel" in text_lower:
            return "booking"
        elif "help" in text_lower or "support" in text_lower:
            return "support"
        else:
            return "general"

class AgentRouter:
    """Handles type-based and intent-based agent selection, mapping intents to specific agent implementations."""
    
    def __init__(self):
        self.routes: Dict[str, Callable[[str, Dict[str, Any]], str]] = {}
        self.default_route: Optional[Callable[[str, Dict[str, Any]], str]] = None
        
    def register_route(self, intent: str, handler: Callable[[str, Dict[str, Any]], str]):
        """Registers a handler for a specific intent."""
        self.routes[intent] = handler
        
    def set_default_route(self, handler: Callable[[str, Dict[str, Any]], str]):
        """Sets the default handler for unknown intents."""
        self.default_route = handler
        
    def route(self, intent: str, message: str, context: Dict[str, Any]) -> str:
        """Routes the message to the appropriate handler based on the intent."""
        handler = self.routes.get(intent, self.default_route)
        if handler:
            return handler(message, context)
        return "Sorry, I am not equipped to handle this request right now."

class LineWebhookHandler:
    """Main processor utilizing the parser, router, and session manager with retry mechanisms."""
    
    def __init__(self, config: HandlerConfig, session_manager: RedisSessionManager, parser: NLUParser, router: AgentRouter):
        self.config = config
        self.session_manager = session_manager
        self.parser = parser
        self.router = router

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def _process_with_retry(self, intent: str, text: str, context: Dict[str, Any]) -> str:
        """Processes the message with automatic retries on failure."""
        return self.router.route(intent, text, context)

    def handle_event(self, event: Dict[str, Any]) -> Optional[str]:
        """Handles a single LINE webhook event."""
        if not self.config.is_allowed(event):
            logger.info("Event ignored by configuration filters.")
            return None
            
        user_id = event.get("source", {}).get("userId")
        if not user_id:
            logger.warning("No userId found in event source.")
            return None
            
        text = event.get("message", {}).get("text", "")
        if not text:
            logger.info("No text content in message.")
            return None
            
        context = self.session_manager.get_session(user_id)
        
        # Parse message to detect intent/category
        intent = self.parser.parse(text)
        logger.info(f"Detected intent: {intent} for user: {user_id}")
        
        try:
            # Route the intent to the specific agent implementation with retry mechanism
            response = self._process_with_retry(intent, text, context)
            
            # Update session context
            context["last_intent"] = intent
            self.session_manager.save_session(user_id, context)
            
            return response
        except Exception as e:
            logger.error(f"Failed to process message after retries: {e}")
            return "I am currently experiencing technical difficulties. Please try again later."