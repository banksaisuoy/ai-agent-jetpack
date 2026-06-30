# Import libraries ที่ใช้
import os
import traceback
import functions_framework
from dotenv import load_dotenv

# LINE SDK
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3 import WebhookHandler
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent,
    FileMessageContent,
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    TextMessage,
    ShowLoadingAnimationRequest,
)

# โหลด .env สำหรับตั้งค่าคีย์ลับจากไฟล์
load_dotenv("../.env", override=True)

# ดึงค่าจาก environment
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "dummy_token")
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "dummy_secret")

# เตรียม configuration สำหรับ LINE Messaging API
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)
line_bot_blob_api = MessagingApiBlob(api_client)

# import ฟังก์ชันจาก service ที่เรียก Gemini API
from gemini_service import generate_text, image_understanding, document_understanding

def safe_reply(reply_token: str, message: str):
    """Safely send a reply back to LINE"""
    try:
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=message)],
            )
        )
    except Exception as e:
        print(f"Error replying message: {e}")

def safe_show_loading(chat_id: str):
    try:
        line_bot_api.show_loading_animation(
            ShowLoadingAnimationRequest(chat_id=chat_id)
        )
    except Exception as e:
        print(f"Error showing loading animation: {e}")

# Function สำหรับรับ webhook จาก LINE
@functions_framework.http
def webhook_listening(request):
    # ดึงค่า Signature จาก header
    signature = request.headers.get("X-Line-Signature")
    if not signature:
        return ("Missing Signature", 400)

    # แปลง request body เป็น text
    body = request.get_data(as_text=True)
    print("Request body: " + body)

    # ตรวจสอบและส่งให้ handler จาก LINE SDK จัดการ
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        return ("Invalid signature", 400)
    except Exception as e:
        print(f"Webhook processing error: {e}")
        traceback.print_exc()

    return "OK"

# กรณีข้อความเป็นประเภท Text
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    user_id = event.source.user_id

    # แสดง loading animation ระหว่างประมวลผล
    safe_show_loading(user_id)

    try:
        # ส่งข้อความไปให้ Gemini ประมวลผล พร้อมกับ user_id
        gemini_response = generate_text(event.message.text, user_id=user_id)
    except Exception as e:
        print(f"Text handling error: {e}")
        gemini_response = "ขออภัยค่ะ มีข้อผิดพลาดในการประมวลผลข้อความเมี๊ยว~"

    # ตอบกลับข้อความที่ได้จาก Gemini
    safe_reply(event.reply_token, gemini_response)

# กรณีข้อความเป็นรูปภาพ
@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    user_id = event.source.user_id

    # แสดง loading animation ระหว่างประมวลผล
    safe_show_loading(user_id)

    try:
        # ดึง binary ของภาพจาก LINE server
        message_content = line_bot_blob_api.get_message_content(message_id=event.message.id)

        # ส่งไปให้ Gemini วิเคราะห์ภาพ
        gemini_response = image_understanding(message_content)
    except Exception as e:
        print(f"Image handling error: {e}")
        gemini_response = "ขออภัยค่ะ มีข้อผิดพลาดในการโหลดรูปภาพเมี๊ยว~"

    # ตอบกลับผลลัพธ์จาก Gemini
    safe_reply(event.reply_token, gemini_response)

# กรณีข้อความเป็นไฟล์เอกสาร
@handler.add(MessageEvent, message=FileMessageContent)
def handle_file_message(event):
    user_id = event.source.user_id

    safe_show_loading(user_id)

    try:
        # ดึง binary ของไฟล์จาก LINE server
        doc_content = line_bot_blob_api.get_message_content(message_id=event.message.id)

        # ส่งไปให้ Gemini วิเคราะห์เนื้อหาในเอกสาร
        gemini_response = document_understanding(doc_content)
    except Exception as e:
        print(f"File handling error: {e}")
        gemini_response = "ขออภัยค่ะ มีข้อผิดพลาดในการโหลดไฟล์เมี๊ยว~"

    # ตอบกลับผลลัพธ์จาก Gemini
    safe_reply(event.reply_token, gemini_response)
