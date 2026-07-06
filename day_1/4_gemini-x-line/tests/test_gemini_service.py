import pytest
from unittest.mock import MagicMock, patch
import io
from google.genai.errors import APIError
from PIL import UnidentifiedImageError

# Set environment variable before importing module
import os
os.environ["GEMINI_API_KEY"] = "fake-api-key"

from gemini_service import generate_text, image_understanding, document_understanding

def test_generate_text_success(mocker):
    # Mock the chat.send_message method
    mock_response = MagicMock()
    mock_response.text = "Hello there!"
    mocker.patch("gemini_service.chat.send_message", return_value=mock_response)

    result = generate_text("Hi")
    assert result == "Hello there!"

def test_generate_text_api_error(mocker):
    # Mock to raise APIError
    mocker.patch("gemini_service.chat.send_message", side_effect=APIError(429, {"error": "Rate limit exceeded"}))

    result = generate_text("Hi")
    assert result == "ขออภัยค่ะ ฉันไม่สามารถประมวลผลได้ในขณะนี้ เมี๊ยว~"

def test_generate_text_generic_error(mocker):
    # Mock to raise generic Exception
    mocker.patch("gemini_service.chat.send_message", side_effect=Exception("Unknown error"))

    result = generate_text("Hi")
    assert result == "ขออภัยค่ะ ฉันไม่สามารถประมวลผลได้ในขณะนี้ เมี๊ยว~"

def test_image_understanding_success(mocker):
    # Create a valid dummy image
    import PIL.Image
    img = PIL.Image.new('RGB', (10, 10))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    dummy_image_bytes = img_byte_arr.getvalue()

    mock_response = MagicMock()
    mock_response.text = "This is a cat."
    mocker.patch("gemini_service.client.models.generate_content", return_value=mock_response)

    result = image_understanding(dummy_image_bytes)
    assert result == "This is a cat."

def test_image_understanding_invalid_image(mocker):
    # Pass invalid bytes
    dummy_invalid_bytes = b"not an image"

    result = image_understanding(dummy_invalid_bytes)
    assert result == "ขออภัยค่ะ ฉันไม่สามารถเปิดรูปภาพนี้ได้ เมี๊ยว~"

def test_image_understanding_api_error(mocker):
    import PIL.Image
    img = PIL.Image.new('RGB', (10, 10))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    dummy_image_bytes = img_byte_arr.getvalue()

    # Mock to raise APIError
    mocker.patch("gemini_service.client.models.generate_content", side_effect=APIError(429, {"error": "Rate limit exceeded"}))

    result = image_understanding(dummy_image_bytes)
    assert result == "ขออภัยค่ะ ฉันไม่สามารถวิเคราะห์รูปภาพได้ในขณะนี้ เมี๊ยว~"

def test_document_understanding_success(mocker):
    dummy_pdf_bytes = b"%PDF-1.4 dummy content"

    mock_response = MagicMock()
    mock_response.text = "Summary of document."
    mocker.patch("gemini_service.client.models.generate_content", return_value=mock_response)

    result = document_understanding(dummy_pdf_bytes)
    assert result == "Summary of document."

def test_document_understanding_api_error(mocker):
    dummy_pdf_bytes = b"%PDF-1.4 dummy content"

    mocker.patch("gemini_service.client.models.generate_content", side_effect=APIError(429, {"error": "Rate limit exceeded"}))

    result = document_understanding(dummy_pdf_bytes)
    assert result == "ขออภัยค่ะ ฉันไม่สามารถวิเคราะห์เอกสารได้ในขณะนี้ เมี๊ยว~"
