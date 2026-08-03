import pytest
import json
import hmac
import hashlib
import base64
from unittest.mock import patch, MagicMock
from flask import Flask

# Need to update sys.path to import line_webhook properly if it's in a subfolder
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../day_1/4_gemini-x-line')))

import line_webhook

@pytest.fixture
def app():
    app = Flask(__name__)
    @app.route('/', methods=['GET', 'POST'])
    def handle_root():
        from flask import request
        return line_webhook.webhook_listening(request)
        
    @app.route('/api/chat', methods=['POST'])
    def handle_chat():
        from flask import request
        return line_webhook.webhook_listening(request)
        
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def valid_signature():
    def _generate_signature(body, secret):
        hash_val = hmac.new(secret.encode('utf-8'), body.encode('utf-8'), hashlib.sha256).digest()
        return base64.b64encode(hash_val).decode('utf-8')
    return _generate_signature

def test_webhook_listening_get(client):
    response = client.get('/')
    assert response.status_code == 404
    assert response.data == b"Not Found"

def test_webhook_missing_signature(client):
    response = client.post('/')
    assert response.status_code == 400
    assert response.data == b"Missing Signature"

@patch('line_webhook.LINE_CHANNEL_SECRET', 'test_secret')
def test_webhook_invalid_signature(client):
    headers = {'x-line-signature': 'invalid_signature'}
    response = client.post('/', headers=headers, data=json.dumps({"events": []}))
    assert response.status_code == 401
    assert response.data == b"Invalid Signature"

@patch('line_webhook.LINE_CHANNEL_SECRET', 'test_secret')
def test_webhook_valid_signature_empty_events(client, valid_signature):
    body = json.dumps({"events": []})
    sig = valid_signature(body, 'test_secret')
    
    headers = {'x-line-signature': sig}
    response = client.post('/', headers=headers, data=body)
    
    assert response.status_code == 200
    assert response.data == b"OK"

@patch('line_webhook.generate_text')
def test_api_chat(mock_generate, client):
    mock_generate.return_value = "Hello from Gemini"
    
    response = client.post('/api/chat', json={"text": "Hi"})
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["reply"] == "Hello from Gemini"
    mock_generate.assert_called_once_with("Hi")