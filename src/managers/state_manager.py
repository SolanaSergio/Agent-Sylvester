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
    """Manages application state with persistence and synchronization"""
    
    def __init__(self, state_dir: Path, initial_state: Dict[str, Any] = None):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # Main state storage
        self._state: Dict[str, Any] = {}
        
        # State persistence
        self._persistence_file = self.state_dir / "state.json"
        self._history_file = self.state_dir / "state_history.pickle"
        
        # Change tracking
        self._change_history: List[StateChange] = []
        self._max_history_size = 1000
        
        # Subscribers
        self._subscribers: Dict[str, Set[Callable]] = {}
        self._global_subscribers: Set[Callable] = set()
        
        # Locks for thread safety
        self._state_lock = threading.Lock()
        self._history_lock = threading.Lock()
        
        # Thread pool for async operations
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize state
        self._load_state()
        if initial_state:
            self.batch_update(initial_state)
            
        logging.info("State Manager initialized")
        
    async def get(self, path: str, default: Any = None) -> Any:
        """Get value from state using dot notation path"""
        try:
            parts = path.split('.')
            current = self._state
            
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    return default
                    
            return current if current is not None else default
            
        except Exception as e:
            logging.error(f"Error getting state at {path}: {str(e)}")
            return default
            
    async def set(self, path: str, value: Any, metadata: Optional[Dict] = None) -> bool:
        """Set value in state using dot notation path"""
        try:
            with self._state_lock:
                parts = path.split('.')
                current = self._state
                
                # Navigate to the parent of the target
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                    
                # Set the value
                current[parts[-1]] = value
                
                # Record change
                change = StateChange(
                    type=StateChangeType.UPDATE,
                    path=parts,
                    value=value,
                    timestamp=datetime.now().timestamp(),
                    metadata=metadata
                )
                await self._record_change(change)
                
                # Notify subscribers
                await self._notify_subscribers(path, change)
                
                # Persist state
                await self._persist_state()
                
                return True
                
        except Exception as e:
            logging.error(f"Error setting state at {path}: {str(e)}")
            return False
            
    async def delete(self, path: str, metadata: Optional[Dict] = None) -> bool:
        """Delete value from state using dot notation path"""
        try:
            with self._state_lock:
                parts = path.split('.')
                current = self._state
                
                # Navigate to the parent of the target
                for part in parts[:-1]:
                    if part not in current:
                        return False
                    current = current[part]
                    
                # Delete the value if it exists
                if parts[-1] in current:
                    value = current[parts[-1]]
                    del current[parts[-1]]
                    
                    # Record change
                    change = StateChange(
                        type=StateChangeType.DELETE,
                        path=parts,
                        value=None,
                        timestamp=datetime.now().timestamp(),
                        metadata=metadata
                    )
                    await self._record_change(change)
                    
                    # Notify subscribers
                    await self._notify_subscribers(path, change)
                    
                    # Persist state
                    await self._persist_state()
                    
                    return True
                    
                return False
                
        except Exception as e:
            logging.error(f"Error deleting state at {path}: {str(e)}")
            return False
            
    async def batch_update(self, updates: Dict[str, Any], metadata: Optional[Dict] = None) -> bool:
        """Perform multiple state updates atomically"""
        try:
            with self._state_lock:
                timestamp = datetime.now().timestamp()
                changes = []
                
                # Apply all updates
                for path, value in updates.items():
                    parts = path.split('.')
                    current = self._state
                    
                    # Navigate to the parent of the target
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                        
                    # Set the value
                    current[parts[-1]] = value
                    
                    # Record change
                    changes.append(StateChange(
                        type=StateChangeType.UPDATE,
                        path=parts,
                        value=value,
                        timestamp=timestamp,
                        metadata=metadata
                    ))
                    
                # Record batch change
                batch_change = StateChange(
                    type=StateChangeType.BATCH,
                    path=[],
                    value=updates,
                    timestamp=timestamp,
                    metadata=metadata
                )
                await self._record_change(batch_change)
                
                # Notify subscribers for each change
                for path, _ in updates.items():
                    change = next(c for c in changes if '.'.join(c.path) == path)
                    await self._notify_subscribers(path, change)
                    
                # Notify global subscribers of batch change
                await self._notify_global_subscribers(batch_change)
                
                # Persist state
                await self._persist_state()
                
                return True
                
        except Exception as e:
            logging.error(f"Error in batch update: {str(e)}")
            return False
            
    def subscribe(self, callback: Callable[[StateChange], None], path: Optional[str] = None):
        """Subscribe to state changes, optionally for a specific path"""
        if path:
            if path not in self._subscribers:
                self._subscribers[path] = set()
            self._subscribers[path].add(callback)
        else:
            self._global_subscribers.add(callback)
            
    def unsubscribe(self, callback: Callable[[StateChange], None], path: Optional[str] = None):
        """Unsubscribe from state changes"""
        if path:
            if path in self._subscribers:
                self._subscribers[path].discard(callback)
        else:
            self._global_subscribers.discard(callback)
            
    async def get_history(self, path: Optional[str] = None) -> List[StateChange]:
        """Get state change history, optionally filtered by path"""
        with self._history_lock:
            if path:
                return [
                    change for change in self._change_history
                    if '.'.join(change.path).startswith(path)
                ]
            return self._change_history.copy()
            
    async def _record_change(self, change: StateChange):
        """Record a state change in history"""
        with self._history_lock:
            self._change_history.append(change)
            
            # Trim history if needed
            if len(self._change_history) > self._max_history_size:
                self._change_history = self._change_history[-self._max_history_size:]
                
            # Persist history
            await self._persist_history()
            
    async def _notify_subscribers(self, path: str, change: StateChange):
        """Notify subscribers of state changes"""
        # Notify path-specific subscribers
        parts = path.split('.')
        current_path = ""
        
        for part in parts:
            current_path = f"{current_path}.{part}" if current_path else part
            if current_path in self._subscribers:
                for callback in self._subscribers[current_path]:
                    try:
                        callback(change)
                    except Exception as e:
                        logging.error(f"Error in subscriber callback: {str(e)}")
                        
        # Notify global subscribers
        await self._notify_global_subscribers(change)
        
    async def _notify_global_subscribers(self, change: StateChange):
        """Notify global subscribers of state changes"""
        for callback in self._global_subscribers:
            try:
                callback(change)
            except Exception as e:
                logging.error(f"Error in global subscriber callback: {str(e)}")
                
    async def _persist_state(self):
        """Persist current state to disk"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._executor,
                self._write_state_to_disk
            )
        except Exception as e:
            logging.error(f"Error persisting state: {str(e)}")
            
    def _write_state_to_disk(self):
        """Write state to disk"""
        with open(self._persistence_file, 'w') as f:
            json.dump(self._state, f, indent=2)
            
    async def _persist_history(self):
        """Persist change history to disk"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._executor,
                self._write_history_to_disk
            )
        except Exception as e:
            logging.error(f"Error persisting history: {str(e)}")
            
    def _write_history_to_disk(self):
        """Write history to disk"""
        with open(self._history_file, 'wb') as f:
            pickle.dump(self._change_history, f)
            
    def _load_state(self):
        """Load state from disk"""
        try:
            if self._persistence_file.exists():
                with open(self._persistence_file, 'r') as f:
                    self._state = json.load(f)
                    
            if self._history_file.exists():
                with open(self._history_file, 'rb') as f:
                    self._change_history = pickle.load(f)
                    
        except Exception as e:
            logging.error(f"Error loading state: {str(e)}")
            self._state = {}
            self._change_history = []
            
    async def get_snapshot(self) -> Dict[str, Any]:
        """Get a snapshot of the current state"""
        with self._state_lock:
            return self._state.copy()
            
    async def restore_snapshot(self, snapshot: Dict[str, Any], metadata: Optional[Dict] = None) -> bool:
        """Restore state from a snapshot"""
        return await self.batch_update(snapshot, metadata=metadata)
        
    async def clear(self, metadata: Optional[Dict] = None) -> bool:
        """Clear all state"""
        try:
            with self._state_lock:
                old_state = self._state.copy()
                self._state = {}
                
                # Record change
                change = StateChange(
                    type=StateChangeType.DELETE,
                    path=[],
                    value=None,
                    timestamp=datetime.now().timestamp(),
                    metadata=metadata
                )
                await self._record_change(change)
                
                # Notify subscribers
                await self._notify_global_subscribers(change)
                
                # Persist empty state
                await self._persist_state()
                
                return True
                
        except Exception as e:
            logging.error(f"Error clearing state: {str(e)}")
            return False 