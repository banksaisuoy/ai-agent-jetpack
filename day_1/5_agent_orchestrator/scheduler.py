class RetryScheduler:
    def schedule_retry(self, task_id, attempt, max_retries, base_delay):
        if attempt >= max_retries:
            return None
        return base_delay * (2 ** attempt)