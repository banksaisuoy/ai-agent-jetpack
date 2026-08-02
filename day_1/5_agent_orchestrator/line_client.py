from linebot.v3.messaging import ApiClient, MessagingApi, Configuration, ReplyMessageRequest, TextMessage
from linebot.v3.exceptions import InvalidSignatureError
from config import settings
import logging

logger = logging.getLogger(__name__)

configuration = Configuration(access_token=settings.line_channel_access_token)

def reply_message(reply_token: str, text: str) -> None:
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=text)]
                )
            )
    except Exception as e:
        logger.error(f"Error replying message: {e}")
        raise