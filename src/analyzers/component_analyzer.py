from typing import Dict, List, Optional
from pathlib import Path
import ast
import re
from src.utils.types import ComponentInfo

class ComponentAnalyzer:
    """Analyzes React/Next.js components for patterns and structure"""
    
    def __init__(self):
        self.component_cache: Dict[str, ComponentInfo] = {}

    async def analyze_component(self, file_path: Path) -> ComponentInfo:
        """Analyze a single component file"""
        if str(file_path) in self.component_cache:
            return self.component_cache[str(file_path)]
            
        try:
            with open(file_path) as f:
                content = f.read()
                
            # Parse the component
            tree = ast.parse(content)
            
            # Extract component information
            name = self._extract_component_name(file_path, tree)
            props = self._extract_props(tree)
            hooks = self._extract_hooks(tree)
            dependencies = self._extract_dependencies(content)
            patterns = self._extract_patterns(content)
            
            component = ComponentInfo(
                name=name,
                file_path=str(file_path),
                props=props,
                hooks=hooks,
                dependencies=dependencies,
                patterns=patterns
            )
            
            self.component_cache[str(file_path)] = component
            return component
            
        except Exception as e:
            raise Exception(f"Error analyzing component {file_path}: {str(e)}")

    def _extract_component_name(self, file_path: Path, tree: ast.AST) -> str:
        """Extract component name from file and AST"""
        # Try to get name from export declaration
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node.name
                
        # Fallback to file name
        return file_path.stem

    def _extract_props(self, tree: ast.AST) -> List[Dict]:
        """Extract component props"""
        props = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for arg in node.args.args:
                    if arg.annotation:
                        props.append({
                            "name": arg.arg,
                            "type": self._get_type_annotation(arg.annotation),
                            "required": True
                        })
                        
        return props

    def _extract_hooks(self, tree: ast.AST) -> List[str]:
        """Extract React hooks used in component"""
        hooks = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                    if name.startswith('use'):
                        hooks.add(name)
                        
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
            'flex': r'className=["\'][^"\']*flex[^"\']*["\']'
        }
        
        for pattern, indicator in pattern_indicators.items():
            if re.search(indicator, content):
                patterns.add(pattern)
                
        return list(patterns)

    def _get_type_annotation(self, node: ast.AST) -> str:
        """Convert AST type annotation to string"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Subscript):
            value = self._get_type_annotation(node.value)
            slice = self._get_type_annotation(node.slice)
            return f"{value}[{slice}]"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return "any"

    async def analyze_directory(self, directory: Path) -> List[ComponentInfo]:
        """Analyze all components in a directory"""
        components = []
        
        if not directory.exists():
            return components
            
        for file_path in directory.glob("**/*.{tsx,jsx}"):
            try:
                component = await self.analyze_component(file_path)
                components.append(component)
            except Exception as e:
                print(f"Error analyzing {file_path}: {str(e)}")
                continue
                
        return components 