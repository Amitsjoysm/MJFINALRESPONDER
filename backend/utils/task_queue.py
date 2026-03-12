"""
Task Queue Manager with Redis for reliable background job processing
Provides retry logic, dead letter queue, and error tracking
"""
import redis
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from config import config

logger = logging.getLogger(__name__)


class TaskQueue:
    """Redis-based task queue with retry and error handling"""
    
    def __init__(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                config.REDIS_URL,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("✓ Task Queue connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def enqueue_task(self, task_type: str, task_data: Dict[str, Any], priority: int = 5) -> Optional[str]:
        """
        Enqueue a task for background processing
        
        Args:
            task_type: Type of task (e.g., 'process_email', 'send_campaign')
            task_data: Task data as dictionary
            priority: Priority level (1-10, higher = more urgent)
            
        Returns:
            Task ID if successful, None otherwise
        """
        if not self.redis_client:
            logger.warning(f"Redis not available, task {task_type} will be processed synchronously")
            return None
        
        try:
            task_id = f"{task_type}:{datetime.now(timezone.utc).timestamp()}:{task_data.get('id', 'unknown')}"
            
            task_payload = {
                'task_id': task_id,
                'task_type': task_type,
                'task_data': task_data,
                'priority': priority,
                'enqueued_at': datetime.now(timezone.utc).isoformat(),
                'retry_count': 0,
                'max_retries': 3,
                'status': 'pending'
            }
            
            # Add to priority queue
            queue_name = f"task_queue:{task_type}"
            self.redis_client.zadd(queue_name, {json.dumps(task_payload): priority})
            
            # Track in active tasks
            self.redis_client.hset('active_tasks', task_id, json.dumps(task_payload))
            
            logger.info(f"✓ Enqueued task {task_id} with priority {priority}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to enqueue task {task_type}: {e}")
            return None
    
    def dequeue_task(self, task_type: str) -> Optional[Dict[str, Any]]:
        """
        Dequeue highest priority task of given type
        
        Args:
            task_type: Type of task to dequeue
            
        Returns:
            Task payload if available, None otherwise
        """
        if not self.redis_client:
            return None
        
        try:
            queue_name = f"task_queue:{task_type}"
            
            # Get highest priority task (ZPOPMAX returns highest score)
            result = self.redis_client.zpopmax(queue_name)
            
            if not result or not result[0]:
                return None
            
            task_json, priority = result[0]
            task_payload = json.loads(task_json)
            
            # Update status
            task_payload['status'] = 'processing'
            task_payload['started_at'] = datetime.now(timezone.utc).isoformat()
            
            task_id = task_payload['task_id']
            self.redis_client.hset('active_tasks', task_id, json.dumps(task_payload))
            
            return task_payload
            
        except Exception as e:
            logger.error(f"Failed to dequeue task {task_type}: {e}")
            return None
    
    def mark_task_complete(self, task_id: str) -> bool:
        """Mark task as successfully completed"""
        if not self.redis_client:
            return True
        
        try:
            # Get task data
            task_json = self.redis_client.hget('active_tasks', task_id)
            if task_json:
                task = json.loads(task_json)
                task['status'] = 'completed'
                task['completed_at'] = datetime.now(timezone.utc).isoformat()
                
                # Move to completed tasks (with 24h expiry)
                self.redis_client.hset('completed_tasks', task_id, json.dumps(task))
                self.redis_client.expire('completed_tasks', 86400)  # 24 hours
                
                # Remove from active
                self.redis_client.hdel('active_tasks', task_id)
                
                logger.info(f"✓ Task {task_id} completed")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to mark task complete {task_id}: {e}")
            return False
    
    def mark_task_failed(self, task_id: str, error: str, retry: bool = True) -> bool:
        """
        Mark task as failed and optionally retry
        
        Args:
            task_id: Task ID
            error: Error message
            retry: Whether to retry the task
            
        Returns:
            True if successfully handled, False otherwise
        """
        if not self.redis_client:
            return True
        
        try:
            # Get task data
            task_json = self.redis_client.hget('active_tasks', task_id)
            if not task_json:
                logger.warning(f"Task {task_id} not found in active tasks")
                return False
            
            task = json.loads(task_json)
            task['retry_count'] = task.get('retry_count', 0) + 1
            task['last_error'] = error
            task['last_failure_at'] = datetime.now(timezone.utc).isoformat()
            
            # Check if should retry
            if retry and task['retry_count'] < task.get('max_retries', 3):
                # Re-enqueue with exponential backoff
                delay = min(300, 2 ** task['retry_count'] * 10)  # Max 5 min delay
                task['status'] = 'retrying'
                task['retry_at'] = (datetime.now(timezone.utc) + timedelta(seconds=delay)).isoformat()
                
                # Add back to queue with lower priority
                queue_name = f"task_queue:{task['task_type']}"
                priority = max(1, task.get('priority', 5) - task['retry_count'])
                self.redis_client.zadd(queue_name, {json.dumps(task): priority})
                
                logger.warning(f"Task {task_id} failed (attempt {task['retry_count']}), will retry in {delay}s")
                
                # Update active tasks
                self.redis_client.hset('active_tasks', task_id, json.dumps(task))
                return True
            
            else:
                # Max retries reached - move to dead letter queue
                task['status'] = 'failed'
                task['failed_at'] = datetime.now(timezone.utc).isoformat()
                
                # Add to dead letter queue
                self.redis_client.hset('dead_letter_queue', task_id, json.dumps(task))
                
                # Remove from active
                self.redis_client.hdel('active_tasks', task_id)
                
                # Track failure metrics
                self.redis_client.hincrby('task_failures', task['task_type'], 1)
                
                logger.error(f"Task {task_id} failed permanently after {task['retry_count']} attempts: {error}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to mark task failed {task_id}: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a task"""
        if not self.redis_client:
            return None
        
        try:
            # Check active tasks
            task_json = self.redis_client.hget('active_tasks', task_id)
            if task_json:
                return json.loads(task_json)
            
            # Check completed tasks
            task_json = self.redis_client.hget('completed_tasks', task_id)
            if task_json:
                return json.loads(task_json)
            
            # Check dead letter queue
            task_json = self.redis_client.hget('dead_letter_queue', task_id)
            if task_json:
                return json.loads(task_json)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get task status {task_id}: {e}")
            return None
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics about task queues"""
        if not self.redis_client:
            return {}
        
        try:
            stats = {
                'active_tasks': self.redis_client.hlen('active_tasks'),
                'completed_tasks': self.redis_client.hlen('completed_tasks'),
                'dead_letter_queue': self.redis_client.hlen('dead_letter_queue'),
                'task_queues': {},
                'failure_counts': {}
            }
            
            # Get counts for each queue type
            for key in self.redis_client.scan_iter('task_queue:*'):
                task_type = key.split(':', 1)[1]
                count = self.redis_client.zcard(key)
                stats['task_queues'][task_type] = count
            
            # Get failure counts
            failures = self.redis_client.hgetall('task_failures')
            stats['failure_counts'] = {k: int(v) for k, v in failures.items()}
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {}
    
    def cleanup_old_tasks(self, days: int = 7) -> int:
        """Clean up old completed and failed tasks"""
        if not self.redis_client:
            return 0
        
        try:
            cleaned = 0
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Clean completed tasks
            for task_id, task_json in self.redis_client.hgetall('completed_tasks').items():
                task = json.loads(task_json)
                completed_at = datetime.fromisoformat(task.get('completed_at', ''))
                if completed_at < cutoff:
                    self.redis_client.hdel('completed_tasks', task_id)
                    cleaned += 1
            
            # Clean dead letter queue
            for task_id, task_json in self.redis_client.hgetall('dead_letter_queue').items():
                task = json.loads(task_json)
                failed_at = datetime.fromisoformat(task.get('failed_at', ''))
                if failed_at < cutoff:
                    self.redis_client.hdel('dead_letter_queue', task_id)
                    cleaned += 1
            
            logger.info(f"Cleaned up {cleaned} old tasks")
            return cleaned
            
        except Exception as e:
            logger.error(f"Failed to cleanup old tasks: {e}")
            return 0


# Singleton instance
task_queue = TaskQueue()
