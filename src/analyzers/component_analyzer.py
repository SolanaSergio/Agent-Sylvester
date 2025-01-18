from typing import Dict, Optional
from bs4 import BeautifulSoup, Tag
from ..utils.types import ComponentInfo

class ComponentAnalyzer:
    @staticmethod
    def extract_component_info(element: Tag, source_url: str) -> Optional[ComponentInfo]:
        """Extract information about a component from an HTML element"""
        if not isinstance(element, Tag):
            return None
            
        # Get component name
        name = ComponentAnalyzer._get_component_name(element)
        if not name:
            return None
            
        # Analyze structure
        structure = ComponentAnalyzer._analyze_structure(element)
        
        return ComponentInfo(
            name=name,
            html=str(element),
            structure=structure,
            source_url=source_url
        )
        
    @staticmethod
    def _get_component_name(element: Tag) -> Optional[str]:
        """Try to determine a component name from the element"""
        # Try to get name from ID
        if element.get('id'):
            return element['id'].replace('-', '_')
            
        # Try to get name from class
        if element.get('class'):
            return element['class'][0].replace('-', '_')
            
        # Use tag name as fallback
        return element.name
        
    @staticmethod
    def _analyze_structure(element: Tag) -> Dict:
        """Analyze the structure of an HTML element"""
        return {
            'tag': element.name,
            'classes': element.get('class', []),
            'attributes': {k:v for k,v in element.attrs.items() if k != 'class'},
            'children': [child.name for child in element.children if isinstance(child, Tag)],
            'text_content': bool(element.text.strip())
        } 