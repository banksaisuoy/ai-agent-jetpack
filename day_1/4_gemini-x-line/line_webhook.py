def webhook_listening(request):
    # จัดการ GET request สำหรับ UI (เฉพาะ dev)
    if request.method == "GET":
        try:
            return send_file("chat_ui.html")
        except Exception:
            return "Not Found", 404

    if request.method == "POST":
        signature = request.headers.get("x-line-signature")
        if not signature:
            return "Missing Signature", 400

        except Exception:
            pass

        if not verify_signature(body, signature):
            print("Invalid signature.")
            return "Invalid Signature", 401

        try:
            payload = json.loads(request.data)
            events = payload.get('events', [])
            for event in events:
                try:
                    reply_token = event.get('replyToken')
                    if not reply_token:
                        continue
                        
                    event_type = event.get('type')
                    reply_text = ""
                    
                    if event_type == 'message':
                        message_type = event.get('message', {}).get('type')
                        if message_type == 'text':
                            text = event['message']['text']
                            try:
                                reply_text = generate_text(text)
                            except Exception as e:
                                print(f"Error calling Gemini: {e}")
                                reply_text = f"Received: {text}"
                        else:
                            reply_text = "I can only process text messages for now."
                    elif event_type == 'postback':
                        postback_data = event.get('postback', {}).get('data', '')
                        reply_text = f"Received postback: {postback_data}"
                    else:
                        print(f"Ignoring event type: {event_type}")
                        continue

                    # Send reply via LINE
                    line_url = "https://api.line.me/v2/bot/message/reply"
                    line_headers = {
                        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
                        "Content-Type": "application/json"
                    }
                    line_payload = {
                        "replyToken": reply_token,
                        "messages": [
                            {"type": "text", "text": reply_text}
                        ]
                    }
                    resp = requests.post(line_url, headers=line_headers, json=line_payload)
                    resp.raise_for_status()
                except Exception as e:
                    print(f"Error processing event: {e}")
        except Exception as e: