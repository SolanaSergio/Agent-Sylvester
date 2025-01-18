import asyncio
from pathlib import Path
from typing import Dict, List, Optional
import re
from bs4 import BeautifulSoup
from src.utils.types import ComponentInfo

class ComponentScraper:
    """Scrapes and analyzes React/Next.js components"""
    
    def __init__(self):
        self.component_cache: Dict[str, ComponentInfo] = {}
        self.pattern_cache: Dict[str, List[str]] = {}

    async def scrape_component(self, file_path: Path) -> Optional[ComponentInfo]:
        """Scrape and analyze a component file"""
        if str(file_path) in self.component_cache:
            return self.component_cache[str(file_path)]
            
        try:
            with open(file_path) as f:
                content = f.read()
                
            # Extract component information
            name = self._extract_component_name(file_path, content)
            props = self._extract_props(content)
            hooks = self._extract_hooks(content)
            dependencies = self._extract_dependencies(content)
            patterns = self._extract_patterns(content)
            jsx_structure = self._extract_jsx_structure(content)
            
            component = ComponentInfo(
                name=name,
                file_path=str(file_path),
                props=props,
                hooks=hooks,
                dependencies=dependencies,
                patterns=patterns,
                structure=jsx_structure
            )
            
            self.component_cache[str(file_path)] = component
            return component
            
        except Exception as e:
            print(f"Error scraping component {file_path}: {str(e)}")
            return None

    def _extract_component_name(self, file_path: Path, content: str) -> str:
        """Extract component name from file and content"""
        # Try to get name from export declaration
        export_pattern = r'export\s+(?:default\s+)?(?:function|const)\s+([A-Z][a-zA-Z0-9]+)'
        match = re.search(export_pattern, content)
        if match:
            return match.group(1)
            
        # Fallback to file name
        return file_path.stem

    def _extract_props(self, content: str) -> List[Dict]:
        """Extract component props"""
        props = []
        
        # Look for TypeScript interface/type definitions
        interface_pattern = r'interface\s+([A-Z][a-zA-Z0-9]*Props)\s*\{([^}]+)\}'
        type_pattern = r'type\s+([A-Z][a-zA-Z0-9]*Props)\s*=\s*\{([^}]+)\}'
        
        for pattern in [interface_pattern, type_pattern]:
            matches = re.finditer(pattern, content)
            for match in matches:
                prop_content = match.group(2)
                prop_lines = prop_content.split('\n')
                
                for line in prop_lines:
                    prop_match = re.match(r'\s*(\w+)(\?)?:\s*([^;]+)', line)
                    if prop_match:
                        name, optional, type_def = prop_match.groups()
                        props.append({
                            "name": name,
                            "type": type_def.strip(),
                            "required": not bool(optional)
                        })
                        
        return props

    def _extract_hooks(self, content: str) -> List[str]:
        """Extract React hooks"""
        hooks = set()
        
        # Look for hook usage
        hook_pattern = r'(?:const|let)\s+\[[^,\]]+,\s*[^\]]+\]\s*=\s*use([A-Z][a-zA-Z]+)'
        matches = re.finditer(hook_pattern, content)
        
        for match in matches:
            hooks.add(f"use{match.group(1)}")
            
        # Look for direct hook calls
        direct_pattern = r'use[A-Z][a-zA-Z]+\('
        matches = re.finditer(direct_pattern, content)
        
        for match in matches:
            hooks.add(match.group().rstrip('('))
            
        return list(hooks)

    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract component dependencies"""
        dependencies = set()
        
        # Find import statements
        import_pattern = r'import\s+.*?from\s+["\']([^"\']+)["\']'
        matches = re.finditer(import_pattern, content)
        
        for match in matches:
            package = match.group(1)
            # Only include external packages
            if not package.startswith('.'):
                dependencies.add(package.split('/')[0])
                
        return list(dependencies)

    def _extract_patterns(self, content: str) -> List[str]:
        """Extract component patterns"""
        if content in self.pattern_cache:
            return self.pattern_cache[content]
            
        patterns = set()
        
        # Check for common patterns
        pattern_indicators = {
            'container': r'className=["\'][^"\']*container[^"\']*["\']',
            'layout': r'className=["\'][^"\']*layout[^"\']*["\']',
            'form': r'<form',
            'list': r'\.map\(',
            'modal': r'className=["\'][^"\']*modal[^"\']*["\']',
            'card': r'className=["\'][^"\']*card[^"\']*["\']',
            'grid': r'className=["\'][^"\']*grid[^"\']*["\']',
            'flex': r'className=["\'][^"\']*flex[^"\']*["\']',
            'table': r'<table',
            'navigation': r'<nav',
            'button': r'<button',
            'input': r'<input',
            'dropdown': r'className=["\'][^"\']*dropdown[^"\']*["\']',
            'tabs': r'className=["\'][^"\']*tabs?[^"\']*["\']',
            'accordion': r'className=["\'][^"\']*accordion[^"\']*["\']',
            'slider': r'className=["\'][^"\']*slider[^"\']*["\']'
        }
        
        for pattern, indicator in pattern_indicators.items():
            if re.search(indicator, content):
                patterns.add(pattern)
                
        self.pattern_cache[content] = list(patterns)
        return list(patterns)

    def _extract_jsx_structure(self, content: str) -> Dict:
        """Extract JSX structure from component"""
        try:
            # Convert JSX to HTML-like structure for parsing
            jsx_content = re.sub(r'className=', 'class=', content)
            jsx_content = re.sub(r'{([^}]+)}', r'\1', jsx_content)
            
            soup = BeautifulSoup(jsx_content, 'html.parser')
            
            def process_element(element):
                if not hasattr(element, 'name'):
                    return None
                    
                return {
                    'tag': element.name,
                    'classes': element.get('class', []),
                    'attributes': {k:v for k,v in element.attrs.items() if k != 'class'},
                    'children': [
                        child for child in [
                            process_element(c) for c in element.children
                        ] if child is not None
                    ]
                }
                
            # Find the main component return statement
            return_pattern = r'return\s*\(\s*(<[^>]+>[\s\S]*</[^>]+>)\s*\)'
            match = re.search(return_pattern, content)
            
            if match:
                jsx_root = match.group(1)
                soup = BeautifulSoup(jsx_root, 'html.parser')
                return process_element(soup.find())
                
            return {}
            
        except Exception as e:
            print(f"Error extracting JSX structure: {str(e)}")
            return {}

    async def scrape_directory(self, directory: Path) -> List[ComponentInfo]:
        """Scrape all components in a directory"""
        components = []
        
        if not directory.exists():
            return components
            
        for file_path in directory.glob("**/*.{tsx,jsx}"):
            component = await self.scrape_component(file_path)
            if component:
                components.append(component)
                
        return components 