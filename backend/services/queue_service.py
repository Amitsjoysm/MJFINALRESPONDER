import redis
from rq import Queue
import logging

from config import config

logger = logging.getLogger(__name__)

class QueueService:
    def __init__(self):
        try:
            self.redis_conn = redis.from_url(config.REDIS_URL)
            self.queue = Queue(connection=self.redis_conn)
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}")
            self.redis_conn = None
            self.queue = None
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        if not self.redis_conn:
            return False
        try:
            self.redis_conn.ping()
            return True
        except:
            return False
    
    def enqueue(self, func, *args, **kwargs):
        """Add job to queue"""
        if self.queue:
            try:
                job = self.queue.enqueue(func, *args, **kwargs)
                return job
            except Exception as e:
                logger.error(f"Error enqueueing job: {e}")
                return None
        return None
    
    def enqueue_in(self, time_delta, func, *args, **kwargs):
        """Schedule job for later"""
        if self.queue:
            try:
                job = self.queue.enqueue_in(time_delta, func, *args, **kwargs)
                return job
            except Exception as e:
                logger.error(f"Error scheduling job: {e}")
                return None
        return None

# Global queue service
queue_service = QueueService()
