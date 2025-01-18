from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import ast
import inspect
import json
import logging
import re
from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader, Template

@dataclass
class DocItem:
    """Represents a documentation item"""
    name: str
    type: str  # 'class', 'function', 'module', 'component', 'api'
    description: str
    params: List[Dict[str, str]]
    returns: Optional[str] = None
    examples: List[str] = None
    notes: List[str] = None
    source: Optional[str] = None
    usage: Optional[str] = None

class DocumentationGenerator:
    """Generates comprehensive documentation for the project"""
    
    def __init__(self, project_root: Union[str, Path], output_dir: Union[str, Path]):
        self.project_root = Path(project_root)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup template environment
        templates_dir = self.project_root / "templates" / "docs"
        templates_dir.mkdir(parents=True, exist_ok=True)
        self.template_env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Initialize template files
        self._init_templates()
        
        logging.info(f"Documentation Generator initialized with output dir: {output_dir}")
        
    def _init_templates(self):
        """Initialize documentation templates"""
        templates = {
            'api.md.jinja2': '''
# {{name}} API Documentation

{{description}}

## Endpoints

{% for endpoint in endpoints %}
### {{endpoint.method}} {{endpoint.path}}

{{endpoint.description}}

{% if endpoint.params %}
#### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
{% for param in endpoint.params %}
| {{param.name}} | {{param.type}} | {{param.required}} | {{param.description}} |
{% endfor %}
{% endif %}

{% if endpoint.returns %}
#### Returns

{{endpoint.returns}}
{% endif %}

{% if endpoint.examples %}
#### Examples

{% for example in endpoint.examples %}
```{{example.language}}
{{example.code}}
```
{% endfor %}
{% endif %}

{% endfor %}
''',
            'component.md.jinja2': '''
# {{name}} Component

{{description}}

## Props

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
{% for prop in props %}
| {{prop.name}} | {{prop.type}} | {{prop.required}} | {{prop.default}} | {{prop.description}} |
{% endfor %}

{% if examples %}
## Examples

{% for example in examples %}
### {{example.name}}

{{example.description}}

```tsx
{{example.code}}
```
{% endfor %}
{% endif %}

{% if notes %}
## Notes

{% for note in notes %}
- {{note}}
{% endfor %}
{% endif %}
''',
            'module.md.jinja2': '''
# {{name}} Module

{{description}}

## Classes

{% for class in classes %}
### {{class.name}}

{{class.description}}

{% if class.methods %}
#### Methods

{% for method in class.methods %}
##### `{{method.signature}}`

{{method.description}}

{% if method.params %}
Parameters:
{% for param in method.params %}
- `{{param.name}}` ({{param.type}}): {{param.description}}
{% endfor %}
{% endif %}

{% if method.returns %}
Returns: {{method.returns}}
{% endif %}

{% if method.examples %}
Examples:
```python
{{method.examples[0]}}
```
{% endif %}

{% endfor %}
{% endif %}
{% endfor %}

## Functions

{% for function in functions %}
### `{{function.signature}}`

{{function.description}}

{% if function.params %}
Parameters:
{% for param in function.params %}
- `{{param.name}}` ({{param.type}}): {{param.description}}
{% endfor %}
{% endif %}

{% if function.returns %}
Returns: {{function.returns}}
{% endif %}

{% if function.examples %}
Examples:
```python
{{function.examples[0]}}
```
{% endif %}

{% endfor %}
''',
            'readme.md.jinja2': '''
# {{project_name}}

{{description}}

## Features

{% for feature in features %}
- {{feature}}
{% endfor %}

## Installation

```bash
{{installation}}
```

## Quick Start

```{{language}}
{{quickstart}}
```

## Documentation

{{documentation}}

## Contributing

{{contributing}}

## License

{{license}}
'''
        }
        
        templates_dir = self.project_root / "templates" / "docs"
        for name, content in templates.items():
            template_file = templates_dir / name
            if not template_file.exists():
                template_file.write_text(content)
                
    async def generate_api_docs(self, api_info: Dict[str, Any]) -> Path:
        """Generate API documentation"""
        try:
            template = self.template_env.get_template('api.md.jinja2')
            output_file = self.output_dir / 'api' / f"{api_info['name']}.md"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            content = template.render(**api_info)
            output_file.write_text(content)
            
            logging.info(f"Generated API documentation: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating API documentation: {str(e)}")
            raise
            
    async def generate_component_docs(self, component_info: Dict[str, Any]) -> Path:
        """Generate component documentation"""
        try:
            template = self.template_env.get_template('component.md.jinja2')
            output_file = self.output_dir / 'components' / f"{component_info['name']}.md"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            content = template.render(**component_info)
            output_file.write_text(content)
            
            logging.info(f"Generated component documentation: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating component documentation: {str(e)}")
            raise
            
    async def generate_module_docs(self, module_path: Union[str, Path]) -> Optional[Path]:
        """Generate documentation for a Python module"""
        try:
            module_path = Path(module_path)
            if not module_path.exists():
                raise FileNotFoundError(f"Module not found: {module_path}")
                
            # Parse module
            with open(module_path, 'r') as f:
                module_content = f.read()
                
            module_info = self._parse_module(module_content)
            
            # Generate documentation
            template = self.template_env.get_template('module.md.jinja2')
            output_file = self.output_dir / 'modules' / f"{module_path.stem}.md"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            content = template.render(**module_info)
            output_file.write_text(content)
            
            logging.info(f"Generated module documentation: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating module documentation: {str(e)}")
            return None
            
    async def generate_project_docs(self, project_info: Dict[str, Any]) -> Path:
        """Generate project-level documentation"""
        try:
            template = self.template_env.get_template('readme.md.jinja2')
            output_file = self.output_dir / 'README.md'
            
            content = template.render(**project_info)
            output_file.write_text(content)
            
            logging.info(f"Generated project documentation: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating project documentation: {str(e)}")
            raise
            
    def _parse_module(self, content: str) -> Dict[str, Any]:
        """Parse Python module content"""
        try:
            tree = ast.parse(content)
            
            module_info = {
                'name': '',
                'description': self._extract_docstring(tree),
                'classes': [],
                'functions': []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = self._parse_class(node)
                    module_info['classes'].append(class_info)
                elif isinstance(node, ast.FunctionDef):
                    if not node.name.startswith('_'):  # Skip private functions
                        function_info = self._parse_function(node)
                        module_info['functions'].append(function_info)
                        
            return module_info
            
        except Exception as e:
            logging.error(f"Error parsing module: {str(e)}")
            return {}
            
    def _parse_class(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Parse class definition"""
        class_info = {
            'name': node.name,
            'description': self._extract_docstring(node),
            'methods': []
        }
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                if not item.name.startswith('_'):  # Skip private methods
                    method_info = self._parse_function(item)
                    class_info['methods'].append(method_info)
                    
        return class_info
        
    def _parse_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Parse function definition"""
        docstring = self._extract_docstring(node)
        params = self._parse_params(node)
        returns = self._parse_returns(docstring)
        examples = self._parse_examples(docstring)
        
        return {
            'name': node.name,
            'signature': self._get_function_signature(node),
            'description': docstring,
            'params': params,
            'returns': returns,
            'examples': examples
        }
        
    def _extract_docstring(self, node: Union[ast.Module, ast.ClassDef, ast.FunctionDef]) -> str:
        """Extract docstring from AST node"""
        docstring = ast.get_docstring(node)
        return docstring if docstring else ""
        
    def _parse_params(self, node: ast.FunctionDef) -> List[Dict[str, str]]:
        """Parse function parameters"""
        params = []
        for arg in node.args.args:
            if arg.arg != 'self':
                param_info = {
                    'name': arg.arg,
                    'type': self._get_annotation_name(arg.annotation),
                    'description': ''  # Could be extracted from docstring
                }
                params.append(param_info)
        return params
        
    def _get_annotation_name(self, annotation: Optional[ast.AST]) -> str:
        """Get type annotation name"""
        if annotation is None:
            return 'Any'
        return ast.unparse(annotation)
        
    def _parse_returns(self, docstring: str) -> Optional[str]:
        """Parse return type from docstring"""
        if 'Returns:' in docstring:
            return docstring.split('Returns:')[1].strip().split('\n')[0]
        return None
        
    def _parse_examples(self, docstring: str) -> List[str]:
        """Parse examples from docstring"""
        examples = []
        if 'Examples:' in docstring:
            example_section = docstring.split('Examples:')[1].strip()
            # Extract code blocks
            code_blocks = re.findall(r'```.*?\n(.*?)```', example_section, re.DOTALL)
            examples.extend(code_blocks)
        return examples
        
    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Get function signature"""
        args = []
        for arg in node.args.args:
            if arg.arg != 'self':
                annotation = self._get_annotation_name(arg.annotation)
                args.append(f"{arg.arg}: {annotation}")
        return f"{node.name}({', '.join(args)})" 