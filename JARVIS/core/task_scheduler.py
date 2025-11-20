"""
Task scheduling and persistence system
Schedule delayed tasks, recurring reminders, and complex workflows
"""
import time
import json
import logging
import threading
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import dateparser  # Natural language date parsing

from config.settings import DATA_DIR

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskType(Enum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    DELAYED = "delayed"

@dataclass
class ScheduledTask:
    """Represents a scheduled task"""
    task_id: str
    name: str
    command: str  # The actual command/prompt to execute
    task_type: TaskType
    scheduled_time: float  # Unix timestamp
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = None
    last_run: Optional[float] = None
    next_run: Optional[float] = None
    recurrence_rule: Optional[str] = None  # e.g., "daily", "every 2 hours"
    max_runs: Optional[int] = None
    run_count: int = 0
    callback: Optional[Callable] = None  # Not stored in DB
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.next_run is None:
            self.next_run = self.scheduled_time
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['task_type'] = self.task_type.value
        data['status'] = self.status.value
        data.pop('callback', None)  # Don't store callback
        return data


class TaskScheduler:
    """
    Comprehensive task scheduling system
    Supports:
    - One-time tasks ("remind me in 2 hours")
    - Recurring tasks ("every day at 9 AM")
    - Natural language parsing ("next Monday at 5 PM")
    """
    
    def __init__(self, gui_handler=None):
        self.gui_handler = gui_handler
        path_mgr = Path(DATA_DIR)
        path_mgr.mkdir(parents=True, exist_ok=True)
        self.db_path = path_mgr / "scheduled_tasks.db"
        
        self.lock = threading.RLock()
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        
        # Initialize database
        self._init_db()
        
        # Load existing tasks
        self._load_tasks()
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True,
            name="Task-Scheduler"
        )
        self.scheduler_thread.start()
        self.running = True
        
        logger.info(f"✅ Task scheduler initialized ({len(self.tasks)} tasks loaded)")
    
    def _init_db(self):
        """Initialize SQLite database"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    command TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    scheduled_time REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    last_run REAL,
                    next_run REAL,
                    recurrence_rule TEXT,
                    max_runs INTEGER,
                    run_count INTEGER DEFAULT 0
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_next_run ON tasks(next_run)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)")
    
    def _load_tasks(self):
        """Load tasks from database"""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM tasks WHERE status IN ('pending', 'running')"
                )
                
                for row in cursor:
                    task = ScheduledTask(
                        task_id=row['task_id'],
                        name=row['name'],
                        command=row['command'],
                        task_type=TaskType(row['task_type']),
                        scheduled_time=row['scheduled_time'],
                        status=TaskStatus(row['status']),
                        created_at=row['created_at'],
                        last_run=row['last_run'],
                        next_run=row['next_run'],
                        recurrence_rule=row['recurrence_rule'],
                        max_runs=row['max_runs'],
                        run_count=row['run_count']
                    )
                    self.tasks[task.task_id] = task
        
        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")
    
    def _save_task(self, task: ScheduledTask):
        """Save task to database"""
        try:
            data = task.to_dict()
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO tasks 
                    (task_id, name, command, task_type, scheduled_time, status,
                     created_at, last_run, next_run, recurrence_rule, max_runs, run_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['task_id'], data['name'], data['command'], 
                    data['task_type'], data['scheduled_time'], data['status'],
                    data['created_at'], data['last_run'], data['next_run'],
                    data['recurrence_rule'], data['max_runs'], data['run_count']
                ))
        except Exception as e:
            logger.error(f"Failed to save task: {e}")
    
    def schedule_task(
        self,
        command: str,
        when: str,
        name: Optional[str] = None,
        recurrence: Optional[str] = None,
        callback: Optional[Callable] = None
    ) -> str:
        """
        Schedule a task using natural language
        
        Args:
            command: The command/prompt to execute
            when: Natural language time ("in 2 hours", "tomorrow at 9 AM")
            name: Optional task name
            recurrence: Recurrence rule ("daily", "every 2 hours", "weekly")
            callback: Optional callback function
            
        Returns:
            task_id: Unique identifier for scheduled task
            
        Examples:
            schedule_task("send email to boss", "tomorrow at 9 AM")
            schedule_task("take break", "every 2 hours", recurrence="every 2 hours")
        """
        # Parse natural language time
        parsed_time = dateparser.parse(when, settings={
            'PREFER_DATES_FROM': 'future',
            'RETURN_AS_TIMEZONE_AWARE': False
        })
        
        if not parsed_time:
            raise ValueError(f"Could not parse time: {when}")
        
        scheduled_timestamp = parsed_time.timestamp()
        
        # Determine task type
        if recurrence:
            task_type = TaskType.RECURRING
        elif "in " in when.lower():
            task_type = TaskType.DELAYED
        else:
            task_type = TaskType.ONE_TIME
        
        # Create task
        task_id = f"task_{int(time.time() * 1000)}"
        task = ScheduledTask(
            task_id=task_id,
            name=name or f"Task: {command[:30]}",
            command=command,
            task_type=task_type,
            scheduled_time=scheduled_timestamp,
            next_run=scheduled_timestamp,
            recurrence_rule=recurrence,
            callback=callback
        )
        
        # Store task
        with self.lock:
            self.tasks[task_id] = task
            self._save_task(task)
        
        # Notify user
        time_str = parsed_time.strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"📅 Scheduled task '{task.name}' for {time_str}")
        
        if self.gui_handler:
            self.gui_handler.show_terminal_output(
                f"✅ Scheduled: {task.name} at {time_str}",
                color="green"
            )
        
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.CANCELLED
                self._save_task(task)
                del self.tasks[task_id]
                
                logger.info(f"❌ Cancelled task: {task.name}")
                return True
        return False
    
    def get_upcoming_tasks(self, limit: int = 10) -> list:
        """Get list of upcoming tasks"""
        with self.lock:
            pending_tasks = [
                t for t in self.tasks.values()
                if t.status == TaskStatus.PENDING
            ]
            pending_tasks.sort(key=lambda t: t.next_run or 0)
            return pending_tasks[:limit]
    
    def _scheduler_loop(self):
        """Main scheduler loop - checks for due tasks"""
        while self.running:
            try:
                current_time = time.time()
                
                with self.lock:
                    for task in list(self.tasks.values()):
                        if task.status != TaskStatus.PENDING:
                            continue
                        
                        # Check if task is due
                        if task.next_run and task.next_run <= current_time:
                            self._execute_task(task)
                
                # Sleep for 10 seconds
                time.sleep(10)
            
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                time.sleep(5)
    
    def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task"""
        logger.info(f"⚡ Executing task: {task.name}")
        
        task.status = TaskStatus.RUNNING
        task.last_run = time.time()
        task.run_count += 1
        self._save_task(task)
        
        try:
            # Execute the command
            from ai.instructions import generate_instructions
            
            if self.gui_handler:
                self.gui_handler.show_terminal_output(
                    f"⏰ Scheduled Task: {task.name}",
                    color="yellow"
                )
                
                generate_instructions(
                    task.command,
                    self.gui_handler.client,
                    self.gui_handler
                )
            
            # Execute callback
            if task.callback:
                task.callback(task)
            
            # Mark as completed
            task.status = TaskStatus.COMPLETED
            
            # Handle recurrence
            if task.task_type == TaskType.RECURRING:
                if task.recurrence_rule:
                    next_run = self._calculate_next_run(
                        task.recurrence_rule,
                        task.last_run
                    )
                    
                    if next_run:
                        # Check max_runs
                        if task.max_runs is None or task.run_count < task.max_runs:
                            task.next_run = next_run
                            task.status = TaskStatus.PENDING
                            logger.info(f"🔄 Rescheduled '{task.name}' for {datetime.fromtimestamp(next_run)}")
            
            self._save_task(task)
            
            # Remove if completed and not recurring
            if task.status == TaskStatus.COMPLETED and task.task_type != TaskType.RECURRING:
                with self.lock:
                    del self.tasks[task.task_id]
        
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task.status = TaskStatus.FAILED
            self._save_task(task)
    
    def _calculate_next_run(self, recurrence_rule: str, last_run: float) -> Optional[float]:
        """Calculate next run time based on recurrence rule"""
        try:
            last_dt = datetime.fromtimestamp(last_run)
            
            # Parse recurrence rule
            rule_lower = recurrence_rule.lower()
            
            if rule_lower == "daily":
                next_dt = last_dt + timedelta(days=1)
            elif rule_lower == "weekly":
                next_dt = last_dt + timedelta(weeks=1)
            elif rule_lower == "hourly":
                next_dt = last_dt + timedelta(hours=1)
            elif "every" in rule_lower:
                # Parse "every X hours/minutes/days"
                parts = rule_lower.split()
                if len(parts) >= 3:
                    try:
                        amount = int(parts[1])
                        unit = parts[2]
                        
                        if "hour" in unit:
                            next_dt = last_dt + timedelta(hours=amount)
                        elif "minute" in unit:
                            next_dt = last_dt + timedelta(minutes=amount)
                        elif "day" in unit:
                            next_dt = last_dt + timedelta(days=amount)
                        else:
                            return None
                    except ValueError:
                        return None
                else:
                    return None
            else:
                return None
            
            return next_dt.timestamp()
        
        except Exception as e:
            logger.error(f"Failed to calculate next run: {e}")
            return None
    
    def shutdown(self):
        """Shutdown scheduler"""
        logger.info("🛑 Shutting down task scheduler...")
        self.running = False
        
        if self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)


# Global scheduler instance
_scheduler = None

def get_task_scheduler(gui_handler=None) -> TaskScheduler:
    """Get or create global task scheduler"""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler(gui_handler=gui_handler)
    return _scheduler