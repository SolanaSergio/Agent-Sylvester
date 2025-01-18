from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ProjectConfig:
    """Configuration for a project"""
    name: str
    project_type: str
    features: List[str]
    styling: str
    project_location: str
    description: Optional[str] = ""
    framework: Optional[str] = None
    requirements: Optional[str] = None
    version: str = "0.1.0"
    author: Optional[str] = None
    license: str = "MIT" 