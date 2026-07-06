import pytest
import os
from unittest.mock import MagicMock

# Setting up env vars required by line_webhook at import time
os.environ["LINE_CHANNEL_ACCESS_TOKEN"] = "fake-token"
os.environ["LINE_CHANNEL_SECRET"] = "fake-secret"
os.environ["GEMINI_API_KEY"] = "fake-gemini-key"

from flask import Request
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import TextMessageContent, ImageMessageContent, FileMessageContent, MessageEvent, UserSource
import line_webhook

def test_webhook_listening_missing_signature(mocker):
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {}

    response, status_code = line_webhook.webhook_listening(mock_request)

    assert status_code == 400
    assert response == "Missing X-Line-Signature"

def test_webhook_listening_invalid_signature(mocker):
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {"X-Line-Signature": "invalid"}
    mock_request.get_data.return_value = "body"

    mocker.patch.object(line_webhook.handler, 'handle', side_effect=InvalidSignatureError("invalid signature"))

    response, status_code = line_webhook.webhook_listening(mock_request)

    assert status_code == 403
    assert response == "Invalid signature"

def test_webhook_listening_success(mocker):
    mock_request = MagicMock(spec=Request)
    mock_request.headers = {"X-Line-Signature": "valid"}
    mock_request.get_data.return_value = "body"

    mocker.patch.object(line_webhook.handler, 'handle')

    response = line_webhook.webhook_listening(mock_request)

    assert response == "OK"

def test_handle_text_message_success(mocker):
    mock_event = MagicMock(spec=MessageEvent)
    mock_event.source = MagicMock(spec=UserSource)
    mock_event.source.user_id = "user1"
    mock_event.message = MagicMock(spec=TextMessageContent)
    mock_event.message.text = "Hello"
    mock_event.reply_token = "reply_token_1"

    mocker.patch("line_webhook.generate_text", return_value="Hi there!")
    mock_reply = mocker.patch("line_webhook.line_bot_api.reply_message")
    mocker.patch("line_webhook.line_bot_api.show_loading_animation")

    line_webhook.handle_text_message(mock_event)

    mock_reply.assert_called_once()
    args, kwargs = mock_reply.call_args
    assert args[0].messages[0].text == "Hi there!"

def test_handle_text_message_error(mocker):
    mock_event = MagicMock(spec=MessageEvent)
    mock_event.source = MagicMock(spec=UserSource)
    mock_event.source.user_id = "user1"
    mock_event.message = MagicMock(spec=TextMessageContent)
    mock_event.message.text = "Hello"
    mock_event.reply_token = "reply_token_1"

    mocker.patch("line_webhook.generate_text", side_effect=Exception("API failure"))
    mock_reply = mocker.patch("line_webhook.line_bot_api.reply_message")
    mocker.patch("line_webhook.line_bot_api.show_loading_animation")

    line_webhook.handle_text_message(mock_event)

    mock_reply.assert_called_once()
    args, kwargs = mock_reply.call_args
    assert args[0].messages[0].text == "ขออภัยค่ะ ระบบขัดข้องชั่วคราว เมี๊ยว~"

def test_handle_image_message_success(mocker):
    mock_event = MagicMock(spec=MessageEvent)
    mock_event.source = MagicMock(spec=UserSource)
    mock_event.source.user_id = "user1"
    mock_event.message = MagicMock(spec=ImageMessageContent)
    mock_event.message.id = "img1"
    mock_event.reply_token = "reply_token_1"

    mocker.patch("line_webhook.line_bot_blob_api.get_message_content", return_value=b"image_bytes")
    mocker.patch("line_webhook.image_understanding", return_value="A cute cat")
    mock_reply = mocker.patch("line_webhook.line_bot_api.reply_message")
    mocker.patch("line_webhook.line_bot_api.show_loading_animation_with_http_info")

    line_webhook.handle_image_message(mock_event)

    mock_reply.assert_called_once()
    args, kwargs = mock_reply.call_args
    assert args[0].messages[0].text == "A cute cat"

def test_handle_image_message_error(mocker):
    mock_event = MagicMock(spec=MessageEvent)
    mock_event.source = MagicMock(spec=UserSource)
    mock_event.source.user_id = "user1"
    mock_event.message = MagicMock(spec=ImageMessageContent)
    mock_event.message.id = "img1"
    mock_event.reply_token = "reply_token_1"

    mocker.patch("line_webhook.line_bot_blob_api.get_message_content", return_value=b"image_bytes")
    mocker.patch("line_webhook.image_understanding", side_effect=Exception("Processing failure"))
    mock_reply = mocker.patch("line_webhook.line_bot_api.reply_message")
    mocker.patch("line_webhook.line_bot_api.show_loading_animation_with_http_info")

    line_webhook.handle_image_message(mock_event)

    mock_reply.assert_called_once()
    args, kwargs = mock_reply.call_args
    assert args[0].messages[0].text == "ขออภัยค่ะ ระบบขัดข้องชั่วคราว เมี๊ยว~"
