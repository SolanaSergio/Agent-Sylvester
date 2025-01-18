from datetime import datetime
from ..utils.types import AgentStatus

class ProgressTracker:
    """Tracks progress of agent operations."""
    def __init__(self):
        self.status = AgentStatus.IDLE
        self.current_task = ""
        self.progress = 0
        self.tasks_completed = []
        self.start_time = datetime.now()
    
    def update(self, status: AgentStatus, task: str, progress: float = None):
        self.status = status
        self.current_task = task
        if progress is not None:
            self.progress = progress 