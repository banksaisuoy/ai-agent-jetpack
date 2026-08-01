# Import libraries ที่ใช้
import os
import json
import functions_framework
from flask import send_file, Response
from dotenv import load_dotenv

# LINE SDK
# import ฟังก์ชันจาก service ที่เรียก Gemini API
from gemini_service import generate_text, image_understanding, document_understanding

# Function สำหรับรับ webhook จาก LINE หรือ HTTP UI
@functions_framework.http
def webhook_listening(request):
    # เช็คว่ารันบน local/development หรือไม่
    is_development = os.environ.get("FLASK_ENV") == "development" or os.environ.get("ENVIRONMENT") == "development" or request.host.startswith("localhost") or request.host.startswith("127.0.0.1")

    # จัดการ GET request สำหรับ UI (เฉพาะ dev)
    if request.method == "GET":
        if is_development:
            return send_file("chat_ui.html")
        return "Not Found", 404

    # จัดการ POST request จาก UI (simulation, เฉพาะ dev)
    if request.method == "POST" and request.path == "/api/chat":
        if not is_development:
            return Response(json.dumps({"error": "Not Found"}), status=404, mimetype="application/json")
        
        data = request.get_json(silent=True) or {}
        text = data.get("text", "")
        if text:
            reply = generate_text(text)
            return Response(json.dumps({"reply": reply}), mimetype="application/json")
        return Response(json.dumps({"error": "No text provided"}), status=400, mimetype="application/json")

    # จัดการ POST request จาก LINE (Webhook ปกติ)
    if request.method == "POST":
        # ดึงค่า Signature จาก header
        signature = request.headers.get("X-Line-Signature")
        if not signature:
            return "Missing Signature", 400

        # แปลง request body เป็น text
        body = request.get_data(as_text=True)
        print("Request body: " + body)

        # ตรวจสอบและส่งให้ handler จาก LINE SDK จัดการ
        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            print("Invalid signature. Please check your channel access token/channel secret.")

        return "OK"

# กรณีข้อความเป็นประเภท Text
@handler.add(MessageEvent, message=TextMessageContent)
