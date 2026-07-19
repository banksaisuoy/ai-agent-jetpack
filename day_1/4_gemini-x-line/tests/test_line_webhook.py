import pytest
from unittest.mock import MagicMock, patch
import os

os.environ["LINE_CHANNEL_ACCESS_TOKEN"] = "test_token"
os.environ["LINE_CHANNEL_SECRET"] = "test_secret"
os.environ["GEMINI_API_KEY"] = "test_gemini"

import line_webhook
from linebot.v3.exceptions import InvalidSignatureError

def test_webhook_listening_missing_signature(mocker):
    request = MagicMock()
    request.headers.get.return_value = None

    result, status = line_webhook.webhook_listening(request)
    assert status == 400
    assert result == "Missing Signature"

def test_webhook_listening_invalid_signature(mocker):
    request = MagicMock()
    request.headers.get.return_value = "invalid_sig"
    request.get_data.return_value = "body"

    mocker.patch('line_webhook.handler.handle', side_effect=InvalidSignatureError("invalid"))

    result, status = line_webhook.webhook_listening(request)
    assert status == 400
    assert result == "Invalid signature"

def test_webhook_listening_success(mocker):
    request = MagicMock()
    request.headers.get.return_value = "valid_sig"
    request.get_data.return_value = "body"

    mock_handle = mocker.patch('line_webhook.handler.handle')

    result = line_webhook.webhook_listening(request)
    assert result == "OK"
    mock_handle.assert_called_once_with("body", "valid_sig")


@patch('line_webhook.safe_show_loading')
@patch('line_webhook.safe_reply')
@patch('line_webhook.generate_text')
def test_handle_text_message(mock_generate_text, mock_safe_reply, mock_safe_show_loading):
    event = MagicMock()
    event.source.user_id = "user123"
    event.message.text = "Hello!"
    event.reply_token = "reply_token_123"

    mock_generate_text.return_value = "Gemini Response"

    line_webhook.handle_text_message(event)

    mock_safe_show_loading.assert_called_once_with("user123")
    mock_generate_text.assert_called_once_with("Hello!", user_id="user123")
    mock_safe_reply.assert_called_once_with("reply_token_123", "Gemini Response")

@patch('line_webhook.safe_show_loading')
@patch('line_webhook.safe_reply')
@patch('line_webhook.generate_text')
def test_handle_text_message_error(mock_generate_text, mock_safe_reply, mock_safe_show_loading):
    event = MagicMock()
    event.source.user_id = "user123"
    event.message.text = "Hello!"
    event.reply_token = "reply_token_123"

    mock_generate_text.side_effect = Exception("error")

    line_webhook.handle_text_message(event)

    mock_safe_show_loading.assert_called_once_with("user123")
    mock_safe_reply.assert_called_once_with("reply_token_123", "ขออภัยค่ะ มีข้อผิดพลาดในการประมวลผลข้อความเมี๊ยว~")

@patch('line_webhook.safe_show_loading')
@patch('line_webhook.safe_reply')
@patch('line_webhook.image_understanding')
@patch('line_webhook.line_bot_blob_api')
def test_handle_image_message(mock_blob_api, mock_image_understanding, mock_safe_reply, mock_safe_show_loading):
    event = MagicMock()
    event.source.user_id = "user123"
    event.message.id = "msg123"
    event.reply_token = "reply_token_123"

    mock_blob_api.get_message_content.return_value = b"image_content"
    mock_image_understanding.return_value = "Image analysis"

    line_webhook.handle_image_message(event)

    mock_safe_show_loading.assert_called_once_with("user123")
    mock_blob_api.get_message_content.assert_called_once_with(message_id="msg123")
    mock_image_understanding.assert_called_once_with(b"image_content")
    mock_safe_reply.assert_called_once_with("reply_token_123", "Image analysis")

@patch('line_webhook.safe_show_loading')
@patch('line_webhook.safe_reply')
@patch('line_webhook.document_understanding')
@patch('line_webhook.line_bot_blob_api')
def test_handle_file_message(mock_blob_api, mock_doc_understanding, mock_safe_reply, mock_safe_show_loading):
    event = MagicMock()
    event.source.user_id = "user123"
    event.message.id = "msg123"
    event.reply_token = "reply_token_123"

    mock_blob_api.get_message_content.return_value = b"doc_content"
    mock_doc_understanding.return_value = "Doc summary"

    line_webhook.handle_file_message(event)

    mock_safe_show_loading.assert_called_once_with("user123")
    mock_blob_api.get_message_content.assert_called_once_with(message_id="msg123")
    mock_doc_understanding.assert_called_once_with(b"doc_content")
    mock_safe_reply.assert_called_once_with("reply_token_123", "Doc summary")

@patch('line_webhook.line_bot_api')
def test_safe_reply(mock_line_api):
    line_webhook.safe_reply("token", "message")
    mock_line_api.reply_message.assert_called_once()

@patch('line_webhook.line_bot_api')
def test_safe_show_loading(mock_line_api):
    line_webhook.safe_show_loading("user123")
    mock_line_api.show_loading_animation.assert_called_once()
