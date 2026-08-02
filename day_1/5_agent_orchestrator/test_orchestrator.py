import json
import hmac
import hashlib
import base64
from unittest.mock import patch
from fastapi.testclient import TestClient

from main import app, verify_signature
from config import settings

client = TestClient(app)

def test_retry_scheduler_values():
    scheduler = RetryScheduler()
    # attempt 0 -> 1 * 2**0 = 1
    # attempt 3 -> >= max_retries (3) -> None
    assert scheduler.schedule_retry("task_1", 3, max_retries=3, base_delay=1) is None

@patch('main.reply_message')
@patch('redis.Redis.get')
@patch('redis.Redis.setex')
@patch('main.process_message')
def test_webhook_successful_process(mock_process, mock_redis_set, mock_redis_get, mock_reply):
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
    
    hash_val = hmac.new('test_secret'.encode('utf-8'), body, hashlib.sha256).digest()
    signature = base64.b64encode(hash_val).decode('utf-8')
    headers = {'x-line-signature': signature}
    
    response = client.post("/webhook/line", headers=headers, content=body)
    
    assert response.status_code == 200
    assert response.text == '"OK"'
    
    mock_process.assert_called_once_with("test_user", "Hello")
    mock_reply.assert_called_once_with("test_reply_token", "Mock response")

@patch('main.reply_message')
@patch('redis.Redis.get')
@patch('redis.Redis.setex')
@patch('main.process_message')
def test_webhook_retries_on_failure(mock_process, mock_redis_set, mock_redis_get, mock_reply):
    mock_process.side_effect = Exception("Simulated failure")
    mock_redis_get.return_value = json.dumps({"user_id": "test_user"})
    
    payload = {
        "events": [
    response = client.post("/webhook/line", headers=headers, content=body)
    
    assert response.status_code == 200
    assert response.text == '"OK"'
    
    # Due to Tenacity in LineWebhookHandler with stop_after_attempt(3)
    # The first call + 2 retries = 3 calls total
    assert mock_process.call_count == 3
    # Our fallback message should be sent
    mock_reply.assert_called_once_with("test_reply_token", "I am currently experiencing technical difficulties. Please try again later.")

@patch('main.reply_message')
def test_webhook_non_text_message(mock_reply):
    payload = {
        "events": [
            {
                "type": "message",
                "replyToken": "test_reply_token",
                "source": {"userId": "test_user"},
                "message": {"type": "image", "id": "test_msg_id"}
            }
        ]
    }
    body = json.dumps(payload).encode('utf-8')
    
    hash_val = hmac.new('test_secret'.encode('utf-8'), body, hashlib.sha256).digest()
    signature = base64.b64encode(hash_val).decode('utf-8')
    headers = {'x-line-signature': signature}
    
    response = client.post("/webhook/line", headers=headers, content=body)
    
    assert response.status_code == 200
    assert response.text == '"OK"'
    
    mock_reply.assert_called_once_with("test_reply_token", "I can only process text messages for now.")
