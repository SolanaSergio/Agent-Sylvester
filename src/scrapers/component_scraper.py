from typing import List, Optional
from bs4 import BeautifulSoup
from ..utils.types import ComponentInfo
from ..utils.constants import COMPONENT_PATTERNS
import re
import logging

class ComponentScraper:
    """Scrapes and identifies reusable components from HTML"""
    
    async def extract_components(self, html: str, source_url: str) -> List[ComponentInfo]:
        """Extract reusable components from HTML content"""
        if not html:
            logging.warning(f"No HTML content provided from {source_url}")
            return []
        
        try:
            components = []
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract components based on patterns
            for component_type, patterns in COMPONENT_PATTERNS.items():
                try:
                    for pattern in patterns:
                        matches = self._find_pattern_matches(soup, pattern)
                        new_components = self._create_components(matches, component_type, source_url)
                        components.extend(new_components)
                        
                except Exception as e:
                    logging.error(f"Error processing pattern {pattern}: {str(e)}")
                    continue
                    
            return components
            
        except Exception as e:
            logging.error(f"Error extracting components from {source_url}: {str(e)}")
            return []
        
    def _find_pattern_matches(self, soup: BeautifulSoup, pattern: str) -> List:
        """Find elements matching a specific pattern"""
        try:
            if pattern.startswith('class='):
                class_name = re.findall(r"class=['\"](.+?)['\"]", pattern)[0]
                return soup.find_all(class_=re.compile(class_name))
            elif pattern.startswith('<'):
                tag = pattern[1:].split()[0].strip('>')
                return soup.find_all(tag)
            else:
                return soup.find_all(attrs={'class': re.compile(pattern)})
        except Exception as e:
            logging.error(f"Error matching pattern {pattern}: {str(e)}")
            return []
            
    def _create_components(self, elements: List, component_type: str, source_url: str) -> List[ComponentInfo]:
        """Create ComponentInfo objects from matched elements"""
        components = []
        
        for i, element in enumerate(elements):
            try:
                name = f"{component_type}_{i + 1}"
                structure = {
                    'type': component_type,
                    'tag': element.name,
                    'classes': element.get('class', []),
                    'attributes': {k:v for k,v in element.attrs.items() if k != 'class'},
                    'children': [child.name for child in element.children if hasattr(child, 'name')]
                }
                
                components.append(ComponentInfo(
                    name=name,
                    html=str(element),
                    structure=structure,
                    source_url=source_url
                ))
                
            except Exception as e:
                logging.error(f"Error creating component from element: {str(e)}")
                continue
                
        return components 