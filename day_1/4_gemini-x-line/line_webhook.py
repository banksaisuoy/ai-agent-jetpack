import json
import os
import hmac
import hashlib
import base64
import requests
from flask import send_file

from gemini_service import generate_text, image_understanding

LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

def verify_signature(body, signature):
    if not LINE_CHANNEL_SECRET:
        return False
    hash_val = hmac.new(LINE_CHANNEL_SECRET.encode('utf-8'), body, hashlib.sha256).digest()
    expected_signature = base64.b64encode(hash_val).decode('utf-8')
    return hmac.compare_digest(expected_signature, signature)

def webhook_listening(request):
    # จัดการ GET request สำหรับ UI (เฉพาะ dev)
    if request.method == "GET":
            return "Not Found", 404

    if request.method == "POST":
        # Handle chat API for web UI
        if request.path == "/api/chat":
            try:
                data = request.get_json()
                text = data.get("text", "")
                if text:
                    reply = generate_text(text)
                    return json.dumps({"reply": reply}), 200, {"Content-Type": "application/json"}
                return json.dumps({"error": "Bad Request"}), 400, {"Content-Type": "application/json"}
            except Exception as e:
                print(f"Error in /api/chat: {e}")
                return json.dumps({"error": "Internal Server Error"}), 500, {"Content-Type": "application/json"}

        # Handle image API for web UI
        if request.path == "/api/chat/image":
            try:
                if 'image' not in request.files:
                    return json.dumps({"error": "No image provided"}), 400, {"Content-Type": "application/json"}
                
                image_file = request.files['image']
                image_content = image_file.read()
                
                # Currently gemini_service.image_understanding doesn't take text, 
                # but we can optionally process the text here if needed.
                text = request.form.get('text', '')
                
                reply = image_understanding(image_content)
                if text:
                     reply = f"[Image Processed] {reply}\n\n[User Text] {text}"
                
                return json.dumps({"reply": reply}), 200, {"Content-Type": "application/json"}
            except Exception as e:
                print(f"Error in /api/chat/image: {e}")
                return json.dumps({"error": "Internal Server Error"}), 500, {"Content-Type": "application/json"}

        signature = request.headers.get("x-line-signature")
        if not signature:
            return "Missing Signature", 400

        body = request.get_data()

        if not verify_signature(body, signature):
            print("Invalid signature.")
            return "Invalid Signature", 401

        try:
            payload = json.loads(body)
            events = payload.get('events', [])
            for event in events:
                try:
                    resp.raise_for_status()
                except Exception as e:
                    print(f"Error processing event: {e}")
            return "OK", 200
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            return "Internal Server Error", 500

    return "Method Not Allowed", 405
