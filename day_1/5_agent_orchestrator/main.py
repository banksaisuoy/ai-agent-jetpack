
            user_id = event.get("source", {}).get("userId")
            
            if event.get('type') == 'message' and event.get('message', {}).get('type') in ['text', 'image']:
                # Update context with user_id to ensure general_agent_handler has it
                if user_id:
                    ctx = session_manager.get_session(user_id)
                
                if response_text:
                    reply_message(reply_token, response_text)

                
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")