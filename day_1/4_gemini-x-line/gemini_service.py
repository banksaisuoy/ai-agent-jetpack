# -------------------- Import Libraries --------------------
from google import genai                          # Gemini API client
from google.genai import types                   # สำหรับสร้างประเภทข้อมูล (เช่น PDF, image)
from google.genai.errors import APIError
import os
import io
import hashlib
from PIL import Image as PILImage                # ใช้แปลง binary content เป็นภาพ
from dotenv import load_dotenv                   # โหลดไฟล์ .env
from cachetools import TTLCache, LRUCache        # Caching

# -------------------- โหลด environment variable จากไฟล์ .env --------------------
load_dotenv(".env")

# -------------------- ตั้งค่า Gemini Client --------------------
_api_key = os.environ.get("GEMINI_API_KEY", "dummy_key_for_tests")
client = genai.Client(api_key=_api_key)   # สร้าง client เพื่อเรียกใช้ Gemini
MODEL_ID = "gemini-2.0-flash"                                  # ใช้โมเดล Gemini Flash (เร็ว ประหยัด)

# -------------------- กำหนดคำสั่งระบบให้ AI มีบทบาทเป็นผู้ช่วยร้านอาหาร --------------------
AI_INSTRUCTION_PROMPT = """
คุณคือผู้ช่วยร้านอาหารชื่อ 'เนโกะ' 🐱
คุณพูดจาน่ารัก สุภาพ ใช้คำลงท้ายว่า 'เมี๊ยว~'
หน้าที่ของคุณคือช่วยลูกค้าร้านหาร
เมื่อลูกค้าถามถึงเมนู ให้ดููข้อมูลจากระบบเพื่อตอบ ถ้าไม่รู้ ให้ตอบอย่างสุภาพว่าไม่รู้
เมื่อลูกค้าต้องการของคิว เช็กคิวว่างจากระบบเพื่อจองโต๊ะให้ลูกค้า ถ้าไม่รู้ว่ามีคิวว่าเวลาไหนบ้าง ให้ตอบอย่างสุภาพว่าไม่รู้
"""

# -------------------- Caches --------------------
# Cache sessions for up to 1 hour (3600 seconds) to avoid memory leak and separate users
chat_sessions = TTLCache(maxsize=1000, ttl=3600)

# LRU cache for image and document understanding to boost performance and reduce API calls
image_cache = LRUCache(maxsize=100)
doc_cache = LRUCache(maxsize=100)


def get_or_create_chat(user_id: str):
    """Retreive an existing chat session or create a new one for the user"""
    if user_id not in chat_sessions:
        chat_sessions[user_id] = client.chats.create(
            model=MODEL_ID,
            config={
                "system_instruction": AI_INSTRUCTION_PROMPT,
            }
        )
    return chat_sessions[user_id]


# -------------------- ฟังก์ชันส่งข้อความเข้า Gemini และรับผลลัพธ์ --------------------
def generate_text(text: str, user_id: str = "default_user") -> str:
    if not text or not text.strip():
        return "ขออภัยค่ะ ฉันไม่ได้รับข้อความใดๆ เลยเมี๊ยว~"

    try:
        chat = get_or_create_chat(user_id)
        response = chat.send_message(text)
        print(f"Gemini response for user {user_id}: {response.text}")
        return response.text
    except Exception as e:
        print(f"Error generating text: {e}")
        return "ขออภัยค่ะ ตอนนี้ระบบขัดข้องชั่วคราว ลองใหม่อีกครั้งนะคะเมี๊ยว~"


# -------------------- ฟังก์ชันวิเคราะห์ภาพ --------------------
def image_understanding(image_content: bytes) -> str:
    if not image_content:
        return "ขออภัยค่ะ รูปภาพว่างเปล่าเมี๊ยว~"

    # Compute hash of the image content for caching
    image_hash = hashlib.md5(image_content).hexdigest()
    if image_hash in image_cache:
        print("Returning cached image response.")
        return image_cache[image_hash]

    try:
        image_data = PILImage.open(io.BytesIO(image_content))
    except Exception as e:
        print(f"Error parsing image: {e}")
        return "ขออภัยค่ะ รูปภาพนี้มีปัญหา ไม่สามารถเปิดได้เมี๊ยว~"

    prompt = "What is shown in this image in Thai?"

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[prompt, image_data],
            config=types.GenerateContentConfig(
                max_output_tokens=200,
            ),
        )
        print(f"Gemini response: {response.text}")

        # Cache the result
        image_cache[image_hash] = response.text
        return response.text
    except Exception as e:
        print(f"Error generating image content: {e}")
        return "ขออภัยค่ะ ตอนนี้ระบบอ่านรูปภาพขัดข้องชั่วคราว ลองใหม่อีกครั้งนะคะเมี๊ยว~"


# -------------------- ฟังก์ชันวิเคราะห์ไฟล์เอกสาร (PDF) --------------------
def document_understanding(file_content: bytes) -> str:
    if not file_content:
        return "ขออภัยค่ะ ไฟล์เอกสารว่างเปล่าเมี๊ยว~"

    doc_hash = hashlib.md5(file_content).hexdigest()
    if doc_hash in doc_cache:
        print("Returning cached document response.")
        return doc_cache[doc_hash]

    prompt = "Summarize this document in Thai"

    try:
        pdf_data = types.Part.from_bytes(data=file_content, mime_type="application/pdf")
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[pdf_data, prompt],
            config=types.GenerateContentConfig(
                max_output_tokens=200,
            ),
        )
        print(f"Gemini response: {response.text}")

        # Cache the result
        doc_cache[doc_hash] = response.text
        return response.text
    except Exception as e:
        print(f"Error generating doc content: {e}")
        return "ขออภัยค่ะ ตอนนี้ระบบอ่านเอกสารขัดข้องชั่วคราว ลองใหม่อีกครั้งนะคะเมี๊ยว~"

