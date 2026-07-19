import pytest
from unittest.mock import MagicMock, patch
import io
from PIL import Image

import os
os.environ["GEMINI_API_KEY"] = "test_key"

import gemini_service

@pytest.fixture(autouse=True)
def clear_caches():
    gemini_service.chat_sessions.clear()
    gemini_service.image_cache.clear()
    gemini_service.doc_cache.clear()
    yield

def test_generate_text_success(mocker):
    # Mock the chat session and its send_message response
    mock_chat = MagicMock()
    mock_chat.send_message.return_value.text = "Hello meow~"

    mocker.patch('gemini_service.get_or_create_chat', return_value=mock_chat)

    result = gemini_service.generate_text("Hi", "user1")
    assert result == "Hello meow~"
    mock_chat.send_message.assert_called_once_with("Hi")

def test_generate_text_empty_input():
    result = gemini_service.generate_text("   ", "user1")
    assert result == "ขออภัยค่ะ ฉันไม่ได้รับข้อความใดๆ เลยเมี๊ยว~"

def test_generate_text_exception(mocker):
    mock_chat = MagicMock()
    mock_chat.send_message.side_effect = Exception("API failure")

    mocker.patch('gemini_service.get_or_create_chat', return_value=mock_chat)

    result = gemini_service.generate_text("Hi", "user1")
    assert result == "ขออภัยค่ะ ตอนนี้ระบบขัดข้องชั่วคราว ลองใหม่อีกครั้งนะคะเมี๊ยว~"


def create_dummy_image_bytes():
    image = Image.new('RGB', (10, 10))
    byte_io = io.BytesIO()
    image.save(byte_io, 'JPEG')
    return byte_io.getvalue()

def test_image_understanding_success(mocker):
    mock_response = MagicMock()
    mock_response.text = "This is a dummy image"

    mocker.patch('gemini_service.client.models.generate_content', return_value=mock_response)

    dummy_image = create_dummy_image_bytes()
    result = gemini_service.image_understanding(dummy_image)

    assert result == "This is a dummy image"
    assert len(gemini_service.image_cache) == 1

def test_image_understanding_cached(mocker):
    mock_generate = mocker.patch('gemini_service.client.models.generate_content')

    dummy_image = create_dummy_image_bytes()

    gemini_service.image_cache.clear()

    import hashlib
    img_hash = hashlib.md5(dummy_image).hexdigest()
    gemini_service.image_cache[img_hash] = "Cached response"

    result = gemini_service.image_understanding(dummy_image)

    assert result == "Cached response"
    mock_generate.assert_not_called()

def test_image_understanding_empty_input():
    assert gemini_service.image_understanding(b"") == "ขออภัยค่ะ รูปภาพว่างเปล่าเมี๊ยว~"

def test_image_understanding_invalid_image():
    assert gemini_service.image_understanding(b"not an image") == "ขออภัยค่ะ รูปภาพนี้มีปัญหา ไม่สามารถเปิดได้เมี๊ยว~"

def test_document_understanding_success(mocker):
    mock_response = MagicMock()
    mock_response.text = "This is a dummy doc"

    mocker.patch('gemini_service.client.models.generate_content', return_value=mock_response)

    dummy_pdf = b"%PDF-1.4\n%EOF"
    result = gemini_service.document_understanding(dummy_pdf)

    assert result == "This is a dummy doc"

def test_document_understanding_cached(mocker):
    mock_generate = mocker.patch('gemini_service.client.models.generate_content')

    dummy_pdf = b"%PDF-1.4\n%EOF"
    import hashlib
    doc_hash = hashlib.md5(dummy_pdf).hexdigest()
    gemini_service.doc_cache[doc_hash] = "Cached doc response"

    result = gemini_service.document_understanding(dummy_pdf)
    assert result == "Cached doc response"
    mock_generate.assert_not_called()

def test_document_understanding_empty_input():
    assert gemini_service.document_understanding(b"") == "ขออภัยค่ะ ไฟล์เอกสารว่างเปล่าเมี๊ยว~"
