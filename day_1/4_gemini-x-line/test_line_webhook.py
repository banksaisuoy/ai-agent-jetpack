import json
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, Request

# We need to mock os.environ before importing line_webhook
import os
os.environ['LINE_CHANNEL_SECRET'] = 'test_secret'
os.environ['LINE_CHANNEL_ACCESS_TOKEN'] = 'test_token'
os.environ['GEMINI_API_KEY'] = 'test_gemini_key'

import sys
sys.path.append(os.path.dirname(__file__))

# Mock sys.modules for gemini_service so we don't need to import google.genai
sys.modules['gemini_service'] = MagicMock()
sys.modules['gemini_service.generate_text'] = MagicMock()

import line_webhook
from line_webhook import verify_signature, webhook_listening

# Create a test app since line_webhook.app is only defined in __main__
app = Flask(__name__)
@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    from flask import request
    return webhook_listening(request)

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_verify_signature_valid():
    # Valid body and signature using 'test_secret'
    body = b'test body'
    # Calculated hash for b'test body' with 'test_secret'
    import hmac
    import hashlib
    import base64
    hash_val = hmac.new('test_secret'.encode('utf-8'), body, hashlib.sha256).digest()
    expected_signature = base64.b64encode(hash_val).decode('utf-8')
    
    assert verify_signature(body, expected_signature) is True

def test_verify_signature_invalid():
    body = b'test body'
    invalid_signature = 'invalid_signature'
    assert verify_signature(body, invalid_signature) is False

def test_verify_signature_missing_secret():
    with patch('line_webhook.LINE_CHANNEL_SECRET', None):
        assert verify_signature(b'body', 'signature') is False

def test_webhook_get(client):
    # GET request should hit the UI or return 404
    response = client.get('/')
    # It might return send_file (if file exists) or 404. Let's just assert it doesn't crash
    assert response.status_code in [200, 404]

def test_webhook_missing_signature(client):
    response = client.post('/', data='{}')
    assert response.status_code == 400
    assert response.data == b"Missing Signature"

def test_webhook_invalid_signature(client):
    headers = {'x-line-signature': 'invalid'}
    response = client.post('/', headers=headers, data='{}')
    assert response.status_code == 401
    assert response.data == b"Invalid Signature"

@patch('line_webhook.verify_signature', return_value=True)
@patch('line_webhook.generate_text')
@patch('line_webhook.requests.post')
def test_webhook_text_message(mock_post, mock_generate_text, mock_verify, client):
    mock_generate_text.return_value = 'Mocked response'
    
    payload = {
        "events": [
            {
                "type": "message",
                "replyToken": "test_reply_token",
                "source": {"userId": "test_user"},
                "message": {"type": "text", "text": "Hello"}
            }
        ]
    }
    
    headers = {'x-line-signature': 'valid_signature'}
    response = client.post('/', headers=headers, data=json.dumps(payload))
    
    assert response.status_code == 200
    assert response.data == b"OK"
    
    mock_generate_text.assert_called_once_with('Hello')
    mock_post.assert_called_once()
    
    # Verify the arguments passed to requests.post
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.line.me/v2/bot/message/reply"
    assert kwargs['headers']['Authorization'] == "Bearer test_token"
    assert kwargs['json']['replyToken'] == "test_reply_token"
    assert kwargs['json']['messages'][0]['text'] == "Mocked response"

@patch('line_webhook.verify_signature', return_value=True)
@patch('line_webhook.requests.post')
def test_webhook_postback_event(mock_post, mock_verify, client):
    payload = {
        "events": [
            {
                "type": "postback",
                "replyToken": "test_reply_token",
                "source": {"userId": "test_user"},
                "postback": {"data": "action=buy&itemid=1"}
            }
        ]
    }
    
    headers = {'x-line-signature': 'valid_signature'}
    response = client.post('/', headers=headers, data=json.dumps(payload))
    
    assert response.status_code == 200
    assert response.data == b"OK"
    
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "https://api.line.me/v2/bot/message/reply"
    assert kwargs['json']['messages'][0]['text'] == "Received postback: action=buy&itemid=1"

@patch('line_webhook.verify_signature', return_value=True)
@patch('line_webhook.requests.post')
def test_webhook_no_reply_token(mock_post, mock_verify, client):
    payload = {
        "events": [
            {
                "type": "message",
                "source": {"userId": "test_user"},
                "message": {"type": "text", "text": "Hello"}
            }
        ]
    }
    
    headers = {'x-line-signature': 'valid_signature'}
    response = client.post('/', headers=headers, data=json.dumps(payload))
    
    assert response.status_code == 200
    mock_post.assert_not_called()
