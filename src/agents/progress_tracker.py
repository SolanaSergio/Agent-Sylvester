from datetime import datetime
from typing import Dict, List, Optional
import json
from pathlib import Path

class ProgressTracker:
    """Tracks progress of agent operations with persistent storage"""
    
    def __init__(self, project_dir: Optional[Path] = None):
        self.status_history: List[Dict] = []
        self.current_status: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.last_update: Optional[datetime] = None
        self.project_dir = project_dir
        self.history_file = self.project_dir / ".agent/history.json" if project_dir else None
        
        # Load existing history if available
        self._load_history()

    def update_status(self, status: str, details: Optional[Dict] = None) -> None:
        """Update the current status and record it in history"""
        now = datetime.now()
        
        if not self.start_time:
            self.start_time = now
            
        self.current_status = status
        self.last_update = now
        
        entry = {
            "status": status,
            "timestamp": now.isoformat(),
            "elapsed": (now - self.start_time).total_seconds(),
            "details": details or {}
        }
        
        self.status_history.append(entry)
        self._save_history()

    def get_current_status(self) -> Optional[str]:
        """Get the current status"""
        return self.current_status

    def get_status_history(self) -> List[Dict]:
        """Get the complete status history"""
        return self.status_history

    def get_elapsed_time(self) -> float:
        """Get total elapsed time in seconds"""
        if not self.start_time:
            return 0.0
        return (datetime.now() - self.start_time).total_seconds()

    def get_last_update(self) -> Optional[datetime]:
        """Get timestamp of last status update"""
        return self.last_update

    def get_completion_percentage(self) -> float:
        """Calculate completion percentage based on completed steps"""
        if not self.status_history:
            return 0.0
            
        total_steps = len(set(entry["status"] for entry in self.status_history))
        completed_steps = len([entry for entry in self.status_history 
                             if entry["status"].lower().startswith("complete")])
        
        return (completed_steps / total_steps) * 100 if total_steps > 0 else 0.0

    def get_step_duration(self, step: str) -> Optional[float]:
        """Get duration of a specific step"""
        step_entries = [entry for entry in self.status_history 
                       if entry["status"].startswith(step)]
        
        if not step_entries:
            return None
            
        start = datetime.fromisoformat(step_entries[0]["timestamp"])
        end = datetime.fromisoformat(step_entries[-1]["timestamp"])
        
        return (end - start).total_seconds()

    def get_summary(self) -> Dict:
        """Get a summary of the progress"""
        if not self.status_history:
            return {
                "status": "Not started",
                "completion": 0.0,
                "elapsed_time": 0.0,
                "steps_completed": 0,
                "current_step": None
            }
            
        return {
            "status": self.current_status,
            "completion": self.get_completion_percentage(),
            "elapsed_time": self.get_elapsed_time(),
            "steps_completed": len(set(entry["status"] for entry in self.status_history 
                                    if entry["status"].lower().startswith("complete"))),
            "current_step": self.current_status,
            "last_update": self.last_update.isoformat() if self.last_update else None
        }

    def _load_history(self) -> None:
        """Load progress history from file"""
        if not self.history_file or not self.history_file.exists():
            return
            
        try:
            with open(self.history_file) as f:
                data = json.load(f)
                self.status_history = data.get("history", [])
                
                if self.status_history:
                    last_entry = self.status_history[-1]
                    self.current_status = last_entry["status"]
                    self.last_update = datetime.fromisoformat(last_entry["timestamp"])
                    self.start_time = datetime.fromisoformat(self.status_history[0]["timestamp"])
        except Exception as e:
            print(f"Error loading progress history: {str(e)}")

    def _save_history(self) -> None:
        """Save progress history to file"""
        if not self.history_file:
            return
            
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump({
                    "history": self.status_history,
                    "last_update": self.last_update.isoformat() if self.last_update else None,
                    "start_time": self.start_time.isoformat() if self.start_time else None
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving progress history: {str(e)}") 