from main import app, verify_signature
from config import settings
from scheduler import RetryScheduler
from fastapi.testclient import TestClient
import json, hmac, hashlib, base64
from unittest.mock import patch, MagicMock

client = TestClient(app)

@patch('redis.Redis.setex')
@patch('main.process_message')
def test_webhook_successful_process(mock_process, mock_redis_set, mock_redis_get, mock_reply, mock_verify):
    # Fix test for new signature
    mock_process.return_value = "Mock response"
    mock_redis_get.return_value = json.dumps({"user_id": "test_user"})
    
    payload = {
        "events": [
            {
                "type": "message",
                "replyToken": "test_reply_token",
                "source": {"userId": "test_user"},
                "message": {"type": "text", "text": "Hello", "id": "test_msg_id"}
            }
        ]
    }
    body = json.dumps(payload).encode('utf-8')
    headers = {'x-line-signature': 'signature'}
    client.post("/webhook/line", headers=headers, content=body)

    mock_process.assert_called_once_with("test_user", "Hello")
    mock_reply.assert_called_once_with("test_reply_token", "Mock response")

def test_webhook_non_text_message(mock_reply, mock_verify):
    payload = {
        "events": [
            {                "type": "message",
                "replyToken": "test_reply_token",
                "source": {"userId": "test_user"},
                "message": {"type": "sticker", "id": "test_msg_id"}
            }
        ]
    }
    body = json.dumps(payload).encode("utf-8")
    hash_val = hmac.new("test_secret".encode("utf-8"), body, hashlib.sha256).digest()
    signature = base64.b64encode(hash_val).decode("utf-8")
    headers = {"x-line-signature": signature}
    response = client.post("/webhook/line", headers=headers, content=body)
    assert response.status_code == 200