"""
Parallel AI task processing
Multiple commands can be processed simultaneously
"""
import threading
import queue
import logging
import time
from typing import Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3

@dataclass
class AITask:
    """Represents a task to be processed"""
    task_id: str
    prompt: str
    callback: Callable
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
    
    def __lt__(self, other):
        # For priority queue - higher priority first
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value
        return self.created_at < other.created_at


class ParallelAIProcessor:
    """
    Process multiple AI tasks in parallel
    Uses thread pool for concurrent execution
    """
    
    def __init__(self, max_workers: int = 3, client=None, gui_handler=None):
        """
        Args:
            max_workers: Maximum concurrent AI calls
            client: AI client instance
            gui_handler: GUI handler for output
        """
        self.max_workers = max_workers
        self.client = client
        self.gui_handler = gui_handler
        
        # Task queue (priority-based)
        self.task_queue = queue.PriorityQueue()
        
        # Worker threads
        self.workers = []
        self.shutdown_flag = threading.Event()
        
        # Statistics
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'active_tasks': 0
        }
        self.stats_lock = threading.Lock()
        
        # Start workers
        self._start_workers()
    
    def _start_workers(self):
        """Start worker threads"""
        for i in range(self.max_workers):
            worker = threading.Thread(
                target=self._worker_loop,
                daemon=True,
                name=f"AI-Worker-{i+1}"
            )
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"✅ Started {self.max_workers} AI worker threads")
    
    def _worker_loop(self):
        """Worker thread main loop"""
        while not self.shutdown_flag.is_set():
            try:
                # Get task from queue (blocks with timeout)
                priority_task = self.task_queue.get(timeout=1)
                task = priority_task[1] if isinstance(priority_task, tuple) else priority_task
                
                # Update stats
                with self.stats_lock:
                    self.stats['active_tasks'] += 1
                
                # Process task
                self._process_task(task)
                
                # Update stats
                with self.stats_lock:
                    self.stats['active_tasks'] -= 1
                    self.stats['completed_tasks'] += 1
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
                with self.stats_lock:
                    self.stats['failed_tasks'] += 1
    
    def _process_task(self, task: AITask):
        """Process a single AI task"""
        try:
            logger.info(f"🔄 Processing task: {task.task_id}")
            
            # Show in GUI
            if self.gui_handler:
                self.gui_handler.show_terminal_output(
                    f"⚙️ Processing: {task.prompt[:50]}...",
                    color="cyan"
                )
            
            # Call AI
            from ai.instructions import generate_instructions
            generate_instructions(
                task.prompt,
                self.client,
                self.gui_handler
            )
            
            # Execute callback
            if task.callback:
                task.callback(task.task_id, success=True)
            
            logger.info(f"✅ Completed task: {task.task_id}")
            
        except Exception as e:
            logger.error(f"❌ Task failed {task.task_id}: {e}")
            
            if self.gui_handler:
                self.gui_handler.show_terminal_output(
                    f"❌ Task failed: {str(e)}",
                    color="red"
                )
            
            if task.callback:
                task.callback(task.task_id, success=False, error=str(e))
    
    def submit_task(
        self,
        prompt: str,
        callback: Optional[Callable] = None,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """
        Submit a task for processing
        
        Returns:
            task_id: Unique identifier for this task
        """
        # Generate task ID
        task_id = f"task_{int(time.time() * 1000)}"
        
        # Create task
        task = AITask(
            task_id=task_id,
            prompt=prompt,
            callback=callback,
            priority=priority
        )
        
        # Add to queue
        self.task_queue.put((priority.value, task))
        
        with self.stats_lock:
            self.stats['total_tasks'] += 1
        
        logger.info(f"📥 Queued task: {task_id} (priority: {priority.name})")
        return task_id
    
    def get_stats(self) -> dict:
        """Get processing statistics"""
        with self.stats_lock:
            return self.stats.copy()
    
    def shutdown(self):
        """Shutdown processor"""
        logger.info("🛑 Shutting down AI processor...")
        self.shutdown_flag.set()
        
        # Wait for workers
        for worker in self.workers:
            worker.join(timeout=5)
        
        logger.info("✅ AI processor shutdown complete")


# Global processor instance
_processor = None

def get_processor(client=None, gui_handler=None) -> ParallelAIProcessor:
    """Get or create global processor"""
    global _processor
    if _processor is None:
        _processor = ParallelAIProcessor(
            max_workers=3,
            client=client,
            gui_handler=gui_handler
        )
    return _processor