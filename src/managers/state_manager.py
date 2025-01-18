from typing import Any, Dict, List, Optional, Callable, Set
from pathlib import Path
import json
import asyncio
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import threading
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

class StateChangeType(Enum):
    """Types of state changes"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    BATCH = "batch"

@dataclass
class StateChange:
    """Represents a change in state"""
    type: StateChangeType
    path: List[str]
    value: Any
    timestamp: float
    metadata: Optional[Dict] = None

class StateManager:
    """Manages application state with persistence and event handling"""
    
    def __init__(self, project_dir: Optional[Path] = None):
        self.state: Dict = {}
        self.observers: Dict[str, Set[callable]] = defaultdict(set)
        self.history: List[Dict] = []
        self.lock = threading.Lock()
        self.project_dir = project_dir
        self.state_file = self.project_dir / ".agent/state.json" if project_dir else None
        
        # Load existing state if available
        self._load_state()

    async def set_state(self, path: str, value: Any, metadata: Optional[Dict] = None) -> None:
        """Set state value at path"""
        with self.lock:
            current = self.state
            parts = path.split('.')
            
            # Navigate to the correct nested level
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
                
            # Set the value
            current[parts[-1]] = value
            
            # Record change in history
            self.history.append({
                "path": path,
                "value": value,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            })
            
            # Save state
            self._save_state()
            
            # Notify observers
            await self._notify_observers(path, value)

    async def get_state(self, path: str, default: Any = None) -> Any:
        """Get state value at path"""
        with self.lock:
            current = self.state
            try:
                for part in path.split('.'):
                    current = current[part]
                return current
            except (KeyError, TypeError):
                return default

    async def update_state(self, updates: Dict[str, Any], metadata: Optional[Dict] = None) -> None:
        """Batch update multiple state values"""
        with self.lock:
            for path, value in updates.items():
                await self.set_state(path, value, metadata)

    async def delete_state(self, path: str) -> None:
        """Delete state at path"""
        with self.lock:
            current = self.state
            parts = path.split('.')
            
            # Navigate to parent
            for part in parts[:-1]:
                if part not in current:
                    return
                current = current[part]
                
            # Delete the value
            if parts[-1] in current:
                del current[parts[-1]]
                
                # Record deletion in history
                self.history.append({
                    "path": path,
                    "value": None,
                    "timestamp": datetime.now().isoformat(),
                    "action": "delete"
                })
                
                # Save state
                self._save_state()
                
                # Notify observers
                await self._notify_observers(path, None)

    def subscribe(self, path: str, callback: callable) -> None:
        """Subscribe to state changes at path"""
        with self.lock:
            self.observers[path].add(callback)

    def unsubscribe(self, path: str, callback: callable) -> None:
        """Unsubscribe from state changes at path"""
        with self.lock:
            if path in self.observers and callback in self.observers[path]:
                self.observers[path].remove(callback)

    async def get_history(self, path: Optional[str] = None) -> List[Dict]:
        """Get state change history, optionally filtered by path"""
        with self.lock:
            if path:
                return [
                    entry for entry in self.history 
                    if entry["path"].startswith(path)
                ]
            return self.history

    async def create_snapshot(self) -> str:
        """Create a snapshot of current state"""
        with self.lock:
            snapshot = {
                "state": self.state.copy(),
                "timestamp": datetime.now().isoformat()
            }
            
            if self.project_dir:
                snapshots_dir = self.project_dir / ".agent/snapshots"
                snapshots_dir.mkdir(parents=True, exist_ok=True)
                
                snapshot_file = snapshots_dir / f"snapshot_{snapshot['timestamp']}.json"
                snapshot_file.write_text(json.dumps(snapshot, indent=2))
                
            return snapshot["timestamp"]

    async def restore_snapshot(self, timestamp: str) -> bool:
        """Restore state from a snapshot"""
        if not self.project_dir:
            return False
            
        snapshot_file = self.project_dir / ".agent/snapshots" / f"snapshot_{timestamp}.json"
        
        try:
            with open(snapshot_file) as f:
                snapshot = json.load(f)
                
            with self.lock:
                self.state = snapshot["state"]
                self._save_state()
                
                # Record restoration in history
                self.history.append({
                    "action": "restore_snapshot",
                    "timestamp": datetime.now().isoformat(),
                    "snapshot_timestamp": timestamp
                })
                
                # Notify all observers
                for path in self.observers.keys():
                    value = await self.get_state(path)
                    await self._notify_observers(path, value)
                    
            return True
            
        except Exception as e:
            print(f"Error restoring snapshot: {str(e)}")
            return False

    def _load_state(self) -> None:
        """Load state from file"""
        if not self.state_file or not self.state_file.exists():
            return
            
        try:
            with open(self.state_file) as f:
                data = json.load(f)
                self.state = data.get("state", {})
                self.history = data.get("history", [])
        except Exception as e:
            print(f"Error loading state: {str(e)}")

    def _save_state(self) -> None:
        """Save state to file"""
        if not self.state_file:
            return
            
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump({
                    "state": self.state,
                    "history": self.history
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {str(e)}")

    async def _notify_observers(self, path: str, value: Any) -> None:
        """Notify all observers of a state change"""
        # Get all observers for this path and parent paths
        parts = path.split('.')
        paths_to_notify = [
            '.'.join(parts[:i+1])
            for i in range(len(parts))
        ]
        
        # Notify observers asynchronously
        tasks = []
        for notify_path in paths_to_notify:
            if notify_path in self.observers:
                for callback in self.observers[notify_path]:
                    tasks.append(
                        asyncio.create_task(
                            callback(path, value)
                        )
                    )
                    
        if tasks:
            await asyncio.gather(*tasks) 