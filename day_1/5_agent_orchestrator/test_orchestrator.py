
from main import app, verify_signature
from config import settings
from scheduler import RetryScheduler

client = TestClient(app)

    
    mock_process_message.assert_not_called()
    mock_reply.assert_called_once_with("test_reply_token", "I can only process text messages for now.")

def test_retry_scheduler_values():
    scheduler = RetryScheduler()
    # attempt 0 -> 1 * 2**0 = 1
    assert scheduler.schedule_retry("task_1", 0, max_retries=3, base_delay=1) == 1
    # attempt 1 -> 1 * 2**1 = 2
    assert scheduler.schedule_retry("task_1", 1, max_retries=3, base_delay=1) == 2
    # attempt 2 -> 1 * 2**2 = 4
    assert scheduler.schedule_retry("task_1", 2, max_retries=3, base_delay=1) == 4
    # attempt 3 -> >= max_retries (3) -> None
    assert scheduler.schedule_retry("task_1", 3, max_retries=3, base_delay=1) is None

@patch('main.process_message')
@patch('main.reply_message')
@patch('asyncio.sleep')
def test_webhook_retries_on_failure(mock_sleep, mock_reply, mock_process_message):
    mock_process_message.side_effect = Exception("Simulated failure")
    
    payload = {
        "events": [
            {
                "type": "message",
                "replyToken": "test_reply_token",
                "source": {"userId": "test_user"},
                "message": {"type": "text", "text": "Fail me", "id": "test_msg_id"}
            }
        ]
    }
    body = json.dumps(payload).encode('utf-8')
    
    hash_val = hmac.new('test_secret'.encode('utf-8'), body, hashlib.sha256).digest()
    signature = base64.b64encode(hash_val).decode('utf-8')
    headers = {'x-line-signature': signature}
    
    response = client.post("/webhook/line", headers=headers, content=body)
    
    assert response.status_code == 200
    assert response.text == "OK"
    
    # Process message should be called 4 times: initial + 3 retries
    assert mock_process_message.call_count == 4
    # Sleep should be called 3 times (for attempts 0, 1, 2)
    assert mock_sleep.call_count == 3
    # Check the delays were 1, 2, 4
    mock_sleep.assert_any_call(1)
    mock_sleep.assert_any_call(2)
    mock_sleep.assert_any_call(4)
