import hmac
import hashlib
import base64
import asyncio
from config import settings
from agent_core import process_message
from line_client import reply_message
from scheduler import RetryScheduler
import logging

logging.basicConfig(level=logging.INFO)
        payload = json.loads(body.decode('utf-8'))
        events = payload.get('events', [])
        
        tasks = [{'event': event, 'attempt': 0} for event in events]
        scheduler = RetryScheduler()
        
        while tasks:
            task = tasks.pop(0)
            event = task['event']
            attempt = task['attempt']
            
            reply_token = event.get('replyToken')
            if not reply_token:
                continue
                        reply_message(reply_token, reply_text)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        task_id = event.get('message', {}).get('id', 'unknown_task')
                        delay = scheduler.schedule_retry(task_id, attempt, max_retries=3, base_delay=1)
                        if delay is not None:
                            logger.info(f"Retrying task {task_id} in {delay} seconds (attempt {attempt + 1})")
                            await asyncio.sleep(delay)
                            tasks.append({'event': event, 'attempt': attempt + 1})
                else:
                    reply_message(reply_token, "I can only process text messages for now.")
            else: