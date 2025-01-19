import logging
from pathlib import Path
from typing import Dict, Optional
import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProgressTracker:
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path
        self.current_status = "Initializing"
        self.details: Dict = {}
        self.history = []
        self.progress = 0
        self.callbacks = []
        self.progress_weights = {
            "Initializing": 5,
            "Creating project structure": 10,
            "Setting up configuration files": 15,
            "Creating core files": 20,
            "Setting up dependencies": 25,
            "Creating components": 15,
            "Setting up styling": 5,
            "Finalizing project": 5
        }
        
    def register_callback(self, callback) -> None:
        """Register a callback for progress updates"""
        self.callbacks.append(callback)
        
    def unregister_callback(self, callback) -> None:
        """Unregister a progress callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            
    async def update_status(self, status: str, details: Optional[Dict] = None) -> None:
        """Update the current status and log it"""
        self.current_status = status
        if details:
            self.details.update(details)
            
        # Calculate progress based on predefined weights
        if status in self.progress_weights:
            self.progress += self.progress_weights[status]
            
        # Notify all registered callbacks
        for callback in self.callbacks:
            try:
                callback(status, self.progress)
            except Exception as e:
                logger.error(f"Error in progress callback: {str(e)}")
                
        logger.info(f"Progress: {status}")
        if details:
            logger.info(f"Details: {details}")
            
    def get_current_status(self) -> str:
        """Get the current status"""
        return self.current_status
        
    def get_details(self) -> Dict:
        """Get the current details"""
        return self.details.copy() 

    async def start_tracking(self) -> None:
        """Start tracking progress"""
        try:
            self.start_time = datetime.datetime.now()
            self.status = "Started"
            self.progress = 0
            self.history.append({
                'timestamp': self.start_time.isoformat(),
                'status': self.status,
                'progress': self.progress
            })
            
            # Notify callbacks of start
            for callback in self.callbacks:
                try:
                    callback("Starting project initialization", 0)
                except Exception as e:
                    logger.error(f"Error in progress callback: {str(e)}")
                    
            logger.info("Progress tracking started")
        except Exception as e:
            logger.error(f"Failed to start progress tracking: {str(e)}")
            raise

    async def update_progress(self, status: str, details: dict = None) -> None:
        """Update progress status"""
        try:
            self.status = status
            self.last_update = datetime.datetime.now()
            
            entry = {
                'timestamp': self.last_update.isoformat(),
                'status': status,
                'progress': self.progress
            }
            
            if details:
                entry['details'] = details
                
            self.history.append(entry)
            
            # Notify callbacks
            for callback in self.callbacks:
                try:
                    callback(status, self.progress)
                except Exception as e:
                    logger.error(f"Error in progress callback: {str(e)}")
                    
            logger.info(f"Progress updated: {status}")
            
        except Exception as e:
            logger.error(f"Failed to update progress: {str(e)}")
            raise 