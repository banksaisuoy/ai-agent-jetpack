import pytest
import hmac
import hashlib
import base64
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Patch environment variables before imports
patch.dict('os.environ', {
    'GEMINI_API_KEY': 'test_gemini_key',
    'LINE_CHANNEL_SECRET': 'test_secret',
    'LINE_CHANNEL_ACCESS_TOKEN': 'test_token',
    'N8N_WEBHOOK_URL': 'http://test-n8n-url'
}).start()

from main import app, verify_signature
from config import settings

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_verify_signature_valid():
    body = b'test body'
    hash_val = hmac.new('test_secret'.encode('utf-8'), body, hashlib.sha256).digest()
    expected_signature = base64.b64encode(hash_val).decode('utf-8')
    assert verify_signature(body, expected_signature) is True

def test_webhook_missing_signature():
    response = client.post("/webhook/line", data="{}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Missing Signature"

def test_webhook_invalid_signature():
    headers = {'x-line-signature': 'invalid_signature'}
    response = client.post("/webhook/line", headers=headers, data="{}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Signature"

@patch('main.process_message')
@patch('main.reply_message')
def test_webhook_text_message(mock_reply, mock_process_message):
    mock_process_message.return_value = "Mocked Agent Response"
    
    payload = {
        "events": [
            {
                "type": "message",
                "replyToken": "test_reply_token",
                "source": {"userId": "test_user"},
                "message": {"type": "text", "text": "Hello Agent"}
            }
        ]
    }
    body = json.dumps(payload).encode('utf-8')
    
    # Calculate valid signature
    hash_val = hmac.new('test_secret'.encode('utf-8'), body, hashlib.sha256).digest()
    signature = base64.b64encode(hash_val).decode('utf-8')
    headers = {'x-line-signature': signature}
    
    response = client.post("/webhook/line", headers=headers, content=body)
    
    assert response.status_code == 200
    assert response.text == "OK"
    
    mock_process_message.assert_called_once_with("test_user", "Hello Agent")
    mock_reply.assert_called_once_with("test_reply_token", "Mocked Agent Response")

@patch('main.process_message')
@patch('main.reply_message')
def test_webhook_non_text_message(mock_reply, mock_process_message):
    payload = {
        "events": [
            {
                "type": "message",
                "replyToken": "test_reply_token",
                "source": {"userId": "test_user"},
                "message": {"type": "image"}
            }
        ]
    }
    body = json.dumps(payload).encode('utf-8')
    
    hash_val = hmac.new('test_secret'.encode('utf-8'), body, hashlib.sha256).digest()
    signature = base64.b64encode(hash_val).decode('utf-8')
    headers = {'x-line-signature': signature}
    
    response = client.post("/webhook/line", headers=headers, content=body)
    
    assert response.status_code == 200
    assert response.text == "OK"
    
    mock_process_message.assert_not_called()
    mock_reply.assert_called_once_with("test_reply_token", "I can only process text messages for now.")
