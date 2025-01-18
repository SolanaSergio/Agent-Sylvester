import logging
from pathlib import Path
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProgressTracker:
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path
        self.current_status = "Initializing"
        self.details: Dict = {}
        
    async def update_status(self, status: str, details: Optional[Dict] = None) -> None:
        """Update the current status and log it"""
        self.current_status = status
        if details:
            self.details.update(details)
        logger.info(f"Progress: {status}")
        if details:
            logger.info(f"Details: {details}")
            
    def get_current_status(self) -> str:
        """Get the current status"""
        return self.current_status
        
    def get_details(self) -> Dict:
        """Get the current details"""
        return self.details.copy() 