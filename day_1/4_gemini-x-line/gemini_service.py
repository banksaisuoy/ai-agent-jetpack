# -------------------- Import Libraries --------------------
from google import genai                          # Gemini API client
from google.genai import types                   # สำหรับสร้างประเภทข้อมูล (เช่น PDF, image)
from google.genai.errors import APIError
import os, io
import PIL
from PIL import Image as PILImage                # ใช้แปลง binary content เป็นภาพ
from dotenv import load_dotenv                   # โหลดไฟล์ .env

# -------------------- โหลด environment variable จากไฟล์ .env --------------------
load_dotenv(".env")

# -------------------- ตั้งค่า Gemini Client --------------------
_api_key = os.getenv("GEMINI_API_KEY")
if not _api_key:
    # Not raising an exception immediately to allow tests to run,
    # but the client initialization will fail if not mocked
    print("Warning: GEMINI_API_KEY environment variable not set.")

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

# -------------------- สร้าง session สำหรับ chat  --------------------
chat = client.chats.create(
    model=MODEL_ID,
    config={
        "system_instruction": AI_INSTRUCTION_PROMPT,   # ตั้ง instruction ที่ AI ต้องทำตาม
    }
)

# -------------------- ฟังก์ชันส่งข้อความเข้า Gemini และรับผลลัพธ์ --------------------
def generate_text(text):
    try:
        response = chat.send_message(text)                 # ส่งข้อความไปยัง chat session
        print(f"Gemini response: {response.text}")         # log คำตอบจาก Gemini
        return response.text                               # ส่งข้อความกลับไปยังผู้ใช้งาน
    except APIError as e:
        print(f"Gemini API Error in generate_text: {e}")
        return "ขออภัยค่ะ ฉันไม่สามารถประมวลผลได้ในขณะนี้ เมี๊ยว~"
    except Exception as e:
        print(f"Unexpected error in generate_text: {e}")
        return "ขออภัยค่ะ ฉันไม่สามารถประมวลผลได้ในขณะนี้ เมี๊ยว~"

# -------------------- ฟังก์ชันวิเคราะห์ภาพ --------------------
def image_understanding(image_content):
    try:
        image_data = PILImage.open(io.BytesIO(image_content))  # แปลง binary image เป็น object ที่อ่านได้
        # Verify image is valid
        image_data.verify()
        # Re-open after verify as verify closes the file
        image_data = PILImage.open(io.BytesIO(image_content))
    except PIL.UnidentifiedImageError:
        print("Error: Unidentified image format")
        return "ขออภัยค่ะ ฉันไม่สามารถเปิดรูปภาพนี้ได้ เมี๊ยว~"
    except Exception as e:
        print(f"Error opening image: {e}")
        return "ขออภัยค่ะ มีปัญหาในการเปิดรูปภาพนี้ เมี๊ยว~"

    try:
        prompt = "What is shown in this image in Thai?"        # คำสั่งให้ Gemini อธิบายภาพเป็นภาษาไทย
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[prompt, image_data],                     # ส่ง prompt และภาพให้ Gemini
            config=types.GenerateContentConfig(
                max_output_tokens=200,                         # จำกัดความยาวของข้อความตอบกลับ
            ),
        )
        print(f"Gemini response: {response.text}")             # log คำตอบจาก Gemini
        return response.text
    except APIError as e:
        print(f"Gemini API Error in image_understanding: {e}")
        return "ขออภัยค่ะ ฉันไม่สามารถวิเคราะห์รูปภาพได้ในขณะนี้ เมี๊ยว~"
    except Exception as e:
        print(f"Unexpected error in image_understanding: {e}")
        return "ขออภัยค่ะ ฉันไม่สามารถวิเคราะห์รูปภาพได้ในขณะนี้ เมี๊ยว~"

# -------------------- ฟังก์ชันวิเคราะห์ไฟล์เอกสาร (PDF) --------------------
def document_understanding(file_content):
    try:
        prompt = "Summarize this document in Thai"             # คำสั่งให้สรุปเอกสารเป็นภาษาไทย
        pdf_data = types.Part.from_bytes(data=file_content, mime_type="application/pdf")  # เตรียมข้อมูล PDF

        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[pdf_data, prompt],                       # ใส่ PDF ก่อน แล้วค่อยใส่ prompt
            config=types.GenerateContentConfig(
                max_output_tokens=200,
            ),
        )
        print(f"Gemini response: {response.text}")
        return response.text
    except APIError as e:
        print(f"Gemini API Error in document_understanding: {e}")
        return "ขออภัยค่ะ ฉันไม่สามารถวิเคราะห์เอกสารได้ในขณะนี้ เมี๊ยว~"
    except Exception as e:
        print(f"Unexpected error in document_understanding: {e}")
        return "ขออภัยค่ะ ฉันไม่สามารถวิเคราะห์เอกสารได้ในขณะนี้ เมี๊ยว~"
