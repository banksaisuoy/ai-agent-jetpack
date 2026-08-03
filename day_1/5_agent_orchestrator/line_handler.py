class HandlerConfig:
    """Configuration for the LineWebhookHandler with filtering capabilities."""
    allowed_event_types: List[str] = field(default_factory=lambda: ["message"])
    allowed_message_types: List[str] = field(default_factory=lambda: ["text", "image"])
    blocked_user_ids: List[str] = field(default_factory=list)
    redis_url: str = "redis://localhost:6379/0"
    
            logger.warning("No userId found in event source.")
            return None
            
        message_data = event.get("message", {})
        msg_type = message_data.get("type")
        text = message_data.get("text", "")
        
        if msg_type == "image":
            message_id = message_data.get("id")
            if text:
                text = f"User uploaded an image. Message ID: {message_id}. Text: {text}. Please analyze it using the process_image tool."
            else:
                text = f"User uploaded an image. Message ID: {message_id}. Please analyze it using the process_image tool."
        elif not text:
            logger.info("No text or supported content in message.")
            return None
            
        context = self.session_manager.get_session(user_id)