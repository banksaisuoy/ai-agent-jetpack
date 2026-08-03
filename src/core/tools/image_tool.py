import os
from typing import Any, Dict, Optional
import logging
from src.core.tool import BaseTool
import linebot.v3.messaging
from google import genai
from google.genai import types

def get_mime_type(data: bytes) -> Optional[str]:
    if data.startswith(b'\xff\xd8'):
        return 'image/jpeg'
    elif data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    elif data.startswith(b'GIF87a') or data.startswith(b'GIF89a'):
        return 'image/gif'
    return None

logger = logging.getLogger(__name__)

class ImageProcessingTool(BaseTool):
    def __init__(self, line_access_token: Optional[str] = None):
        # Allow passing token or reading from environment variable
        self.line_access_token = line_access_token or os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
        self.genai_client = genai.Client()
        self.model = "gemini-2.5-flash"
        self.max_size_bytes = 10 * 1024 * 1024  # 10 MB

    @property
    def name(self) -> str:
        return "process_image"

    @property
    def description(self) -> str:
        return "Downloads an image from LINE using a message_id and analyzes it using Google Gemini."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "The LINE message ID of the image to download."
                },
                "prompt": {
                    "type": "string",
                    "description": "An optional prompt to guide the image analysis."
                }
            },
            "required": ["message_id"]
        }

    def execute(self, message_id: str, prompt: str = "Analyze this image in detail.", **kwargs) -> Any:
        if not self.line_access_token:
            return "Error: LINE_CHANNEL_ACCESS_TOKEN is not configured."
        
        try:
            # 1. Download image from LINE
            configuration = linebot.v3.messaging.Configuration(access_token=self.line_access_token)
            with linebot.v3.messaging.ApiClient(configuration) as api_client:
                blob_api = linebot.v3.messaging.MessagingApiBlob(api_client)
                image_content = blob_api.get_message_content(message_id)
                
                # In Python SDK v3, blob_api.get_message_content returns bytes
                if isinstance(image_content, bytes):
                    image_data = image_content
                else:
                    image_data = image_content.read()

            # 2. Check file size
            if len(image_data) > self.max_size_bytes:
                return "Error: Image size exceeds 10MB limit."

            # 2.5 Check supported formats
            mime_type = get_mime_type(image_data)
            if not mime_type:
                return "Error: Unsupported image format. Only JPEG, PNG, and GIF are supported."

            # 3. Process with Gemini
            image_part = types.Part.from_bytes(data=image_data, mime_type=mime_type)
            
            response = self.genai_client.models.generate_content(
                model=self.model,
                contents=[prompt, image_part]
            )
            
            return response.text

        except Exception as e:
            logger.error(f"Error processing image {message_id}: {e}")
            return f"Error processing image: {e}"