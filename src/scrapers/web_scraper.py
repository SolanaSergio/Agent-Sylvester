import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from pathlib import Path
import logging
import json
import re
from urllib.parse import urljoin
from src.utils.types import ComponentInfo

class WebScraper:
    """Scrapes web content for component analysis"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }
        self.rate_limit = asyncio.Semaphore(5)  # Limit concurrent requests
        self.visited_urls = set()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def scrape_components(self, url: str, max_depth: int = 2) -> List[ComponentInfo]:
        """Scrape components from a given URL and its linked pages"""
        if not self.session:
            raise RuntimeError("WebScraper must be used as an async context manager")
            
        self.visited_urls.clear()
        components = []
        
        async def scrape_url(current_url: str, depth: int):
            if depth > max_depth or current_url in self.visited_urls:
                return
                
            self.visited_urls.add(current_url)
            
            try:
                async with self.rate_limit:
                    async with self.session.get(current_url) as response:
                        if response.status == 200:
                            html = await response.text()
                            page_components = await self._extract_components(html, current_url)
                            components.extend(page_components)
                            
                            if depth < max_depth:
                                # Extract and follow links
                                soup = BeautifulSoup(html, 'html.parser')
                                links = [urljoin(current_url, a.get('href')) 
                                       for a in soup.find_all('a', href=True)]
                                
                                # Filter same-domain links
                                base_domain = current_url.split('/')[2]
                                links = [link for link in links 
                                       if link.split('/')[2] == base_domain]
                                
                                # Recursively scrape linked pages
                                tasks = [scrape_url(link, depth + 1) 
                                       for link in links 
                                       if link not in self.visited_urls]
                                await asyncio.gather(*tasks)
                        else:
                            logging.error(f"Failed to fetch {current_url}: {response.status}")
            except Exception as e:
                logging.error(f"Error scraping {current_url}: {str(e)}")
                
        await scrape_url(url, 0)
        return components

    async def _extract_components(self, html: str, source_url: str) -> List[ComponentInfo]:
        """Extract component information from HTML"""
        components = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for common component patterns
        selectors = [
            # UI Components
            '[class*="component"],[class*="card"],[class*="widget"]',
            # Layout Components
            'header,footer,nav,aside,main,section',
            # Interactive Components
            '[role="button"],[role="tab"],[role="dialog"]',
            # Form Components
            'form,[role="form"],[class*="form"]',
            # List Components
            '[class*="list"],[class*="grid"],[class*="menu"]'
        ]
        
        for selector in selectors:
            for element in soup.select(selector):
                if self._is_likely_component(element):
                    component = ComponentInfo(
                        name=self._generate_component_name(element),
                        html=str(element),
                        structure=self._analyze_structure(element),
                        source_url=source_url,
                        dependencies=self._extract_dependencies(element),
                        styles=self._extract_styles(element)
                    )
                    components.append(component)
                    
        return components

    def _is_likely_component(self, element) -> bool:
        """Determine if an element is likely a reusable component"""
        # Check for component indicators
        indicators = {
            'class': lambda x: any(word in x for word in [
                'component', 'card', 'widget', 'container', 'section',
                'modal', 'dialog', 'dropdown', 'menu', 'nav', 'form'
            ]),
            'id': lambda x: any(word in x for word in [
                'component', 'card', 'widget', 'container', 'section',
                'modal', 'dialog', 'dropdown', 'menu', 'nav', 'form'
            ]),
            'data-component': lambda x: bool(x),
            'role': lambda x: x in [
                'article', 'region', 'complementary', 'dialog',
                'tabpanel', 'tab', 'menu', 'menuitem', 'button'
            ]
        }
        
        # Check custom attributes
        custom_attrs = {
            'data-testid', 'data-cy', 'data-e2e',
            'data-component', 'data-widget', 'data-module'
        }
        
        return (
            any(attr in element.attrs and indicators[attr](element.attrs[attr])
                for attr in indicators if attr in element.attrs) or
            any(attr in element.attrs for attr in custom_attrs)
        )

    def _generate_component_name(self, element) -> str:
        """Generate a suitable name for the component"""
        # Try different attributes for name generation
        name_sources = [
            ('data-component', lambda x: x),
            ('data-testid', lambda x: x.replace('test-', '').replace('-test', '')),
            ('class', lambda x: x[0] if isinstance(x, list) else x),
            ('id', lambda x: x)
        ]
        
        for attr, processor in name_sources:
            if attr in element.attrs:
                value = processor(element.attrs[attr])
                if value:
                    # Convert to PascalCase
                    words = re.findall(r'[A-Za-z][a-z]*|[0-9]+', value)
                    return ''.join(word.capitalize() for word in words) + 'Component'
                    
        # Fallback to element type
        return element.name.capitalize() + 'Component'

    def _analyze_structure(self, element) -> Dict:
        """Analyze the structure of a component"""
        def process_element(el):
            structure = {
                'tag': el.name,
                'attributes': {k: v for k, v in el.attrs.items()},
                'children': []
            }
            
            # Process child elements
            for child in el.children:
                if child.name:  # Skip text nodes
                    structure['children'].append(process_element(child))
                    
            return structure
            
        return process_element(element)

    def _extract_dependencies(self, element) -> List[str]:
        """Extract potential dependencies from component"""
        dependencies = set()
        
        # UI Libraries
        if element.find_all('svg'):
            dependencies.add('@heroicons/react')
        
        # Animation Libraries
        if any('animate' in attr for attr in element.attrs.values()):
            dependencies.add('framer-motion')
        if any('transition' in attr for attr in element.attrs.values()):
            dependencies.add('react-transition-group')
            
        # Form Libraries
        if element.find('form') or element.name == 'form':
            dependencies.add('react-hook-form')
            
        # Component Libraries
        if any('mui' in attr for attr in element.attrs.values()):
            dependencies.add('@mui/material')
        if any('chakra' in attr for attr in element.attrs.values()):
            dependencies.add('@chakra-ui/react')
            
        return list(dependencies)

    def _extract_styles(self, element) -> Dict:
        """Extract styles from component"""
        styles = {
            'inline': {},
            'classes': [],
            'tailwind': [],
            'css_modules': [],
            'styled_components': []
        }
        
        # Extract inline styles
        if 'style' in element.attrs:
            styles['inline'] = self._parse_inline_styles(element['style'])
            
        # Extract classes
        if 'class' in element.attrs:
            classes = element['class'] if isinstance(element['class'], list) else element['class'].split()
            
            for cls in classes:
                if cls.startswith('css-'):  # Styled Components
                    styles['styled_components'].append(cls)
                elif re.match(r'[a-z0-9]+_[A-Za-z0-9_-]+', cls):  # CSS Modules
                    styles['css_modules'].append(cls)
                elif any(tw_prefix in cls for tw_prefix in ['text-', 'bg-', 'flex', 'grid', 'p-', 'm-']):
                    styles['tailwind'].append(cls)
                else:
                    styles['classes'].append(cls)
                    
        return {k: v for k, v in styles.items() if v}

    def _parse_inline_styles(self, style_string: str) -> Dict[str, str]:
        """Parse inline style string into a dictionary"""
        styles = {}
        for declaration in style_string.split(';'):
            if ':' in declaration:
                property, value = declaration.split(':', 1)
                styles[property.strip()] = value.strip()
        return styles

    async def save_component(self, component: ComponentInfo, project_path: Path) -> None:
        """Save scraped component to file"""
        try:
            component_dir = project_path / 'components' / component.name.lower()
            component_dir.mkdir(parents=True, exist_ok=True)
            
            # Save component HTML
            html_file = component_dir / 'component.html'
            html_file.write_text(component.html)
            
            # Save component metadata
            meta_file = component_dir / 'metadata.json'
            meta_data = {
                'name': component.name,
                'source_url': component.source_url,
                'dependencies': component.dependencies,
                'structure': component.structure,
                'styles': component.styles
            }
            meta_file.write_text(json.dumps(meta_data, indent=2))
            
            # Generate React component
            react_file = component_dir / f'{component.name}.tsx'
            react_content = await self._generate_react_component(component)
            react_file.write_text(react_content)
            
        except Exception as e:
            logging.error(f"Error saving component {component.name}: {str(e)}")

    async def _generate_react_component(self, component: ComponentInfo) -> str:
        """Generate React component from HTML"""
        # Basic React component template
        return f"""
import React from 'react';
{self._generate_dependency_imports(component.dependencies)}

interface {component.name}Props {{
    // Add props here
}}

export const {component.name}: React.FC<{component.name}Props> = (props) => {{
    return (
        {self._convert_html_to_jsx(component.html)}
    );
}};

export default {component.name};
"""

    def _generate_dependency_imports(self, dependencies: List[str]) -> str:
        """Generate import statements for dependencies"""
        imports = []
        for dep in dependencies:
            if dep == '@heroicons/react':
                imports.append("import { Icon } from '@heroicons/react/solid';")
            elif dep == 'framer-motion':
                imports.append("import { motion } from 'framer-motion';")
            elif dep == 'react-transition-group':
                imports.append("import { Transition } from 'react-transition-group';")
            elif dep == 'react-hook-form':
                imports.append("import { useForm } from 'react-hook-form';")
                
        return '\n'.join(imports)

    def _convert_html_to_jsx(self, html: str) -> str:
        """Convert HTML string to JSX"""
        # Basic conversion - would need more sophisticated parsing for production
        jsx = html.replace('class=', 'className=')
        jsx = re.sub(r'for=', 'htmlFor=', jsx)
        return jsx 