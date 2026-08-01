"""
To test locally, set the following environment variables:
export LINE_CHANNEL_SECRET='your_line_channel_secret'
export LINE_CHANNEL_ACCESS_TOKEN='your_line_channel_access_token'
export GEMINI_API_KEY='your_gemini_api_key'

Then run the script:
python line_webhook.py
"""

# Import libraries ที่ใช้
import os
import json
import hashlib
import hmac
import base64
import requests
import functions_framework
from flask import send_file, Response, Flask, request as flask_request
from dotenv import load_dotenv

load_dotenv()

# import ฟังก์ชันจาก service ที่เรียก Gemini API
from gemini_service import generate_text, image_understanding, document_understanding

LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = 'gemini-pro'

def verify_signature(body: bytes, signature: str) -> bool:
    if not LINE_CHANNEL_SECRET or not signature:
        return False
    hash_val = hmac.new(LINE_CHANNEL_SECRET.encode('utf-8'), body, hashlib.sha256).digest()
    expected_signature = base64.b64encode(hash_val).decode('utf-8')
    return expected_signature == signature

# Function สำหรับรับ webhook จาก LINE หรือ HTTP UI
@functions_framework.http
def webhook_listening(request):
    # จัดการ GET request สำหรับ UI (เฉพาะ dev)
    if request.method == "GET":
        if is_development:
            try:
                return send_file("chat_ui.html")
            except Exception:
                return "Not Found", 404
        return "Not Found", 404

    # จัดการ POST request จาก UI (simulation, เฉพาะ dev)
        if not signature:
            return "Missing Signature", 400

        body = request.get_data()
        try:
            print("Request body: " + body.decode('utf-8'))
        except Exception:
            pass

        if not verify_signature(request.data, signature):
            print("Invalid signature.")
            return "Invalid Signature", 400

        try:
            payload = json.loads(request.data)
            events = payload.get('events', [])
            for event in events:
                try:
                    if event.get('type') == 'message' and event.get('message', {}).get('type') == 'text':
                        user_id = event['source']['userId']
                        text = event['message']['text']
                        
                        # Call Gemini API
                        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
                        gemini_payload = {
                            "contents": [
                                {
                                    "parts": [
                                        {"text": text}
                                    ]
                                }
                            ]
                        }
                        gemini_resp = requests.post(gemini_url, json=gemini_payload)
                        gemini_resp.raise_for_status()
                        gemini_data = gemini_resp.json()
                        reply_text = gemini_data['candidates'][0]['content']['parts'][0]['text']

                        # Send reply via LINE
                        line_url = "https://api.line.me/v2/bot/message/push"
                        line_headers = {
                            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
                            "Content-Type": "application/json"
                        }
                        line_payload = {
                            "to": user_id,
                            "messages": [
                                {"type": "text", "text": reply_text}
                            ]
                        }
                        requests.post(line_url, headers=line_headers, json=line_payload)
                except Exception as e:
                    print(f"Error processing event: {e}")
        except Exception as e:
            print(f"Error processing payload: {e}")

        # Always return 200 OK to LINE to avoid retries
        return "OK", 200

    return "Method Not Allowed", 405

if __name__ == '__main__':
    app = Flask(__name__)
    
    @app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
    @app.route('/<path:path>', methods=['GET', 'POST'])
    def catch_all(path):
        return webhook_listening(flask_request)
        
    app.run(port=9999)