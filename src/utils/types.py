from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass

class AgentStatus(Enum):
    INITIALIZING = "initializing"
    ANALYZING = "analyzing"
    BUILDING = "building"
    ERROR = "error"
    COMPLETE = "complete"

class LayoutType(Enum):
    STANDARD = "standard"
    DASHBOARD = "dashboard"
    SINGLE_PAGE = "single-page"
    LANDING = "landing"
    CUSTOM = "custom"

@dataclass
class ComponentInfo:
    name: str
    html: str
    structure: Dict
    source_url: Optional[str] = None
    dependencies: List[str] = None
    styles: Dict = None
    
@dataclass
class Pattern:
    type: str
    name: str
    frequency: int
    confidence: float
    elements: List[str]
    attributes: Dict[str, str]
    
@dataclass
class StylePattern:
    type: str
    values: List[str]
    frequency: int
    context: str
    
@dataclass
class LayoutPattern:
    type: LayoutType
    structure: Dict[str, List[str]]
    nesting_level: int
    grid_system: Optional[str]
    breakpoints: List[str]
    
@dataclass
class AccessibilityPattern:
    type: str
    aria_roles: List[str]
    aria_attributes: Dict[str, str]
    semantic_elements: List[str]
    
@dataclass
class InteractionPattern:
    type: str
    events: List[str]
    states: List[str]
    animations: List[str]
    transitions: List[str]
    
@dataclass
class ResponsivePattern:
    breakpoints: List[str]
    rules: Dict[str, List[str]]
    mobile_first: bool
    container_queries: bool 

@dataclass
class ProjectConfig:
    name: str
    description: str
    framework: str
    features: List[str]

@dataclass
class ComponentStatus:
    name: str
    status: str

@dataclass
class DependencyInfo:
    name: str
    required_version: str
    installed_version: Optional[str]
    latest_version: Optional[str]
    status: str  # 'missing', 'outdated', 'current', 'ahead', or 'unknown'

@dataclass
class ProjectStatus:
    components: List[ComponentStatus]
    dependencies: List[DependencyInfo]
    issues: List[str] 