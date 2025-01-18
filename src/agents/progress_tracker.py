from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class ProgressTracker:
    def __init__(self, project_dir: Optional[Path] = None):
        self.status_history: List[Dict] = []
        self.current_status: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.last_update: Optional[datetime] = None
        self.project_dir = project_dir
        self._lock = asyncio.Lock()
        
        if project_dir:
            # Create .agent directory if it doesn't exist
            agent_dir = project_dir / ".agent"
            agent_dir.mkdir(parents=True, exist_ok=True)
            self.history_file = agent_dir / "history.json"
        else:
            self.history_file = None

        # Load existing history if available
        self._load_history()

    async def update_status(self, status: str, metadata: Dict = None) -> None:
        """Update the current status and record it in history"""
        async with self._lock:
            self.current_status = status
            now = datetime.now()
            
            if not self.start_time:
                self.start_time = now
                
            self.last_update = now
            
            entry = {
                "status": status,
                "timestamp": now.isoformat(),
                "metadata": metadata or {}
            }
            
            self.status_history.append(entry)
            await self._save_history()
            logger.info(f"Status updated: {status}")

    def _load_history(self) -> None:
        """Load status history from file"""
        if not self.history_file or not self.history_file.exists():
            return
            
        try:
            # Ensure parent directory exists
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.history_file) as f:
                data = json.load(f)
                self.status_history = data.get("history", [])
                
                # Restore the most recent status
                if self.status_history:
                    self.current_status = self.status_history[-1]["status"]
                    self.last_update = datetime.fromisoformat(self.status_history[-1]["timestamp"])
                    self.start_time = datetime.fromisoformat(self.status_history[0]["timestamp"])
                    
        except Exception as e:
            logger.error(f"Failed to load status history: {str(e)}")

    async def _save_history(self) -> None:
        """Save status history to file"""
        if not self.history_file:
            return
            
        try:
            # Ensure parent directory exists
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Use async file operations to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._write_history_file)
        except Exception as e:
            logger.error(f"Failed to save status history: {str(e)}")

    def _write_history_file(self) -> None:
        """Write history to file (called in executor)"""
        with open(self.history_file, "w") as f:
            json.dump({
                "history": self.status_history
            }, f, indent=2)

    def get_duration(self) -> Optional[float]:
        """Get duration in seconds since start"""
        if not self.start_time:
            return None
            
        return (datetime.now() - self.start_time).total_seconds()

    def get_last_update_age(self) -> Optional[float]:
        """Get seconds since last update"""
        if not self.last_update:
            return None
            
        return (datetime.now() - self.last_update).total_seconds()

    def get_current_status(self) -> Optional[str]:
        """Get current status"""
        return self.current_status

    def get_history(self) -> List[Dict]:
        """Get complete status history"""
        return self.status_history.copy()  # Return a copy to prevent external modifications 