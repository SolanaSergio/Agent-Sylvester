import asyncio
from pathlib import Path
from typing import Dict, List, Optional
import json
from jinja2 import Environment, FileSystemLoader
from src.utils.types import ProjectConfig
from src.analyzers.pattern_analyzer import PatternAnalyzer
from src.analyzers.requirement_analyzer import RequirementAnalyzer
import logging

class DocumentationGenerator:
    """Generates project documentation"""
    
    def __init__(self):
        self.pattern_analyzer = PatternAnalyzer()
        self.requirement_analyzer = RequirementAnalyzer()
        
        # Set up template environment
        template_dir = Path(__file__).parent / "templates"
        if not template_dir.exists():
            template_dir.mkdir(parents=True)
            self._create_default_templates(template_dir)
            
        self.template_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True  # Enable autoescaping for security
        )

    def _create_default_templates(self, template_dir: Path) -> None:
        """Create default documentation templates"""
        templates = {
            "readme.md.j2": """# {{ project.name }}

{{ project.description }}

## Features

{% for feature in features %}
- {{ feature }}
{% endfor %}

## Getting Started

{% for step in setup_steps %}
{{ loop.index }}. {{ step }}
{% endfor %}

## Documentation

For more detailed documentation, please see the [docs](./docs) directory.
""",
            "api.md.j2": """# API Documentation

{% for endpoint in endpoints %}
## {{ endpoint.name }}

{{ endpoint.description }}

**Method:** {{ endpoint.method }}
**Path:** {{ endpoint.path }}

{% if endpoint.parameters %}
### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
{% for param in endpoint.parameters %}
| {{ param.name }} | {{ param.type }} | {{ param.required }} | {{ param.description }} |
{% endfor %}
{% endif %}

{% if endpoint.responses %}
### Responses

{% for response in endpoint.responses %}
#### {{ response.code }}

{{ response.description }}

{% if response.example %}
```json
{{ response.example }}
```
{% endif %}
{% endfor %}
{% endif %}

{% endfor %}
""",
            "components.md.j2": """# Components

{% for component in components %}
## {{ component.name }}

{{ component.description }}

{% if component.props %}
### Props

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
{% for prop in component.props %}
| {{ prop.name }} | {{ prop.type }} | {{ prop.required }} | {{ prop.default }} | {{ prop.description }} |
{% endfor %}
{% endif %}

{% if component.example %}
### Example

```tsx
{{ component.example }}
```
{% endif %}

{% endfor %}
"""
        }
        
        for name, content in templates.items():
            template_path = template_dir / name
            template_path.write_text(content)

    async def generate_project_documentation(self, config: ProjectConfig, project_path: Path) -> None:
        """Generate complete project documentation"""
        if not project_path.exists():
            raise ValueError(f"Project directory {project_path} does not exist")
            
        docs_dir = project_path / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        try:
            # Analyze project
            patterns = await self.pattern_analyzer.analyze_patterns(project_path)
            requirements = await self.requirement_analyzer.analyze_project_requirements(config, project_path)
            
            # Generate documentation files
            await asyncio.gather(
                self._generate_readme(project_path, config, patterns, requirements),
                self._generate_api_docs(docs_dir, patterns.get("components", [])),
                self._generate_component_docs(docs_dir, patterns.get("components", [])),
                self._generate_architecture_docs(docs_dir, patterns, requirements),
                self._generate_setup_docs(docs_dir, config, requirements)
            )
        except Exception as e:
            raise Exception(f"Failed to generate documentation: {str(e)}")

    async def update_documentation(self, project_dir: Path) -> None:
        """Update existing documentation"""
        if not project_dir.exists():
            raise ValueError(f"Project directory {project_dir} does not exist")
            
        docs_dir = project_dir / "docs"
        if not docs_dir.exists():
            raise FileNotFoundError("Documentation directory not found")
            
        try:
            # Re-analyze project
            patterns = await self.pattern_analyzer.analyze_patterns(project_dir)
            
            # Update documentation files
            await asyncio.gather(
                self._update_api_docs(docs_dir, patterns.get("components", [])),
                self._update_component_docs(docs_dir, patterns.get("components", [])),
                self._update_architecture_docs(docs_dir, patterns)
            )
        except Exception as e:
            raise Exception(f"Failed to update documentation: {str(e)}")

    async def _generate_readme(
        self, 
        project_dir: Path, 
        config: ProjectConfig, 
        patterns: Dict, 
        requirements: Dict
    ) -> None:
        """Generate project README"""
        try:
            template = self.template_env.get_template("readme.md.j2")
            
            content = template.render(
                project=config,  # Pass the entire config object
                features=config.features,
                setup_steps=self._get_setup_steps(config, requirements),
                usage_examples=self._get_usage_examples(patterns),
                component_list=self._get_component_list(patterns),
                dependencies=requirements.get("dependencies", {}),
                dev_dependencies=requirements.get("devDependencies", {})
            )
            
            readme_file = project_dir / "README.md"
            readme_file.write_text(content)
        except Exception as e:
            raise Exception(f"Failed to generate README: {str(e)}")

    async def _generate_api_docs(self, docs_dir: Path, components: List[Dict]) -> None:
        """Generate API documentation"""
        try:
            api_dir = docs_dir / "api"
            api_dir.mkdir(exist_ok=True)
            
            template = self.template_env.get_template("api.md.j2")
            
            for component in components:
                if component.get("type") == "api":
                    content = template.render(
                        component_name=component["name"],
                        endpoints=self._extract_endpoints(component),
                        params=self._extract_params(component),
                        responses=self._extract_responses(component)
                    )
                    
                    doc_file = api_dir / f"{component['name'].lower()}.md"
                    doc_file.write_text(content)
        except Exception as e:
            raise Exception(f"Failed to generate API documentation: {str(e)}")

    async def _generate_component_docs(self, docs_dir: Path, components: List[Dict]) -> None:
        """Generate component documentation"""
        try:
            components_dir = docs_dir / "components"
            components_dir.mkdir(exist_ok=True)
            
            template = self.template_env.get_template("components.md.j2")
            
            for component in components:
                try:
                    content = template.render(
                        component_name=component["name"],
                        description=self._get_component_description(component),
                        props=self._extract_props(component),
                        examples=self._get_component_examples(component),
                        dependencies=component.get("dependencies", []),
                        patterns=component.get("patterns", [])
                    )
                    
                    doc_file = components_dir / f"{component['name'].lower()}.md"
                    doc_file.write_text(content)
                except Exception as e:
                    logging.error(f"Failed to generate documentation for component {component['name']}: {str(e)}")
                    continue
        except Exception as e:
            raise Exception(f"Failed to generate component documentation: {str(e)}")

    async def _generate_architecture_docs(
        self, 
        docs_dir: Path, 
        patterns: Dict,
        requirements: Dict
    ) -> None:
        """Generate architecture documentation"""
        template = self.template_env.get_template("architecture.md.j2")
        
        content = template.render(
            patterns=patterns,
            requirements=requirements,
            component_structure=self._get_component_structure(patterns),
            data_flow=self._get_data_flow(patterns),
            state_management=self._get_state_management(patterns)
        )
        
        arch_file = docs_dir / "architecture.md"
        arch_file.write_text(content)

    async def _generate_setup_docs(
        self, 
        docs_dir: Path, 
        config: ProjectConfig,
        requirements: Dict
    ) -> None:
        """Generate setup documentation"""
        template = self.template_env.get_template("setup.md.j2")
        
        content = template.render(
            project_name=config.name,
            framework=config.framework,
            dependencies=requirements.get("dependencies", {}),
            dev_dependencies=requirements.get("devDependencies", {}),
            scripts=requirements.get("scripts", {}),
            env_vars=self._get_required_env_vars(requirements),
            setup_steps=self._get_setup_steps(config, requirements)
        )
        
        setup_file = docs_dir / "setup.md"
        setup_file.write_text(content)

    def _get_setup_steps(self, config: ProjectConfig, requirements: Dict) -> List[str]:
        """Get project setup steps"""
        steps = [
            f"1. Clone the repository: `git clone <repository-url>`",
            f"2. Install dependencies: `npm install`"
        ]
        
        # Add framework-specific steps
        if config.framework == "Next.js":
            steps.append("3. Run the development server: `npm run dev`")
        elif config.framework == "React":
            steps.append("3. Start the development server: `npm start`")
        elif config.framework == "Vue":
            steps.append("3. Run the development server: `npm run serve`")
        elif config.framework == "Angular":
            steps.append("3. Start the development server: `ng serve`")
            
        # Add feature-specific steps
        if "Database" in config.features:
            steps.extend([
                "4. Set up the database:",
                "   - Copy `.env.example` to `.env`",
                "   - Update database credentials in `.env`",
                "   - Run migrations: `npm run db:migrate`"
            ])
            
        if "Testing" in config.features:
            steps.append("5. Run tests: `npm test`")
            
        return steps

    def _get_usage_examples(self, patterns: Dict) -> List[Dict[str, str]]:
        """Get component usage examples"""
        examples = []
        
        for component in patterns.get("components", []):
            if component.get("examples"):
                examples.append({
                    "name": component["name"],
                    "code": component["examples"][0]  # Get first example
                })
                
        return examples

    def _get_component_list(self, patterns: Dict) -> List[Dict[str, str]]:
        """Get list of components with descriptions"""
        return [{
            "name": component["name"],
            "description": self._get_component_description(component)
        } for component in patterns.get("components", [])]

    def _get_component_description(self, component: Dict) -> str:
        """Generate component description"""
        try:
            description = f"A {component.get('type', 'component')} component"
            
            if component.get("patterns"):
                patterns = ", ".join(component["patterns"])
                description += f" implementing {patterns} patterns"
                
            if component.get("dependencies"):
                deps = ", ".join(component["dependencies"])
                description += f". Depends on: {deps}"
                
            return description
        except Exception as e:
            logging.warning(f"Failed to generate component description: {str(e)}")
            return "A component"  # Fallback description

    def _extract_props(self, component: Dict) -> List[Dict]:
        """Extract component props"""
        props = []
        
        if "attributes" in component:
            for name, details in component["attributes"].items():
                props.append({
                    "name": name,
                    "type": details.get("type", "any"),
                    "required": details.get("required", False),
                    "description": details.get("description", ""),
                    "default": details.get("default")
                })
                
        return props

    def _get_component_examples(self, component: Dict) -> List[str]:
        """Get component usage examples"""
        return component.get("examples", [])

    def _get_component_structure(self, patterns: Dict) -> Dict:
        """Get component hierarchy and relationships"""
        structure = {}
        
        for component in patterns.get("components", []):
            structure[component["name"]] = {
                "children": component.get("children", []),
                "parents": component.get("parents", []),
                "dependencies": component.get("dependencies", [])
            }
            
        return structure

    def _get_data_flow(self, patterns: Dict) -> List[Dict]:
        """Get data flow between components"""
        flows = []
        
        for component in patterns.get("components", []):
            if "dataFlow" in component:
                flows.extend(component["dataFlow"])
                
        return flows

    def _get_state_management(self, patterns: Dict) -> Dict:
        """Get state management patterns"""
        state_patterns = {}
        
        for component in patterns.get("components", []):
            if "state" in component:
                state_patterns[component["name"]] = component["state"]
                
        return state_patterns

    def _get_required_env_vars(self, requirements: Dict) -> List[Dict]:
        """Get required environment variables"""
        env_vars = []
        
        if "configurations" in requirements:
            for config in requirements["configurations"]:
                if config.get("type") == "env":
                    env_vars.append({
                        "name": config["name"],
                        "description": config.get("description", ""),
                        "required": config.get("required", True),
                        "default": config.get("default")
                    })
                    
        return env_vars

    def _extract_endpoints(self, component: Dict) -> List[Dict]:
        """Extract API endpoints from component"""
        endpoints = []
        
        if "api" in component:
            for endpoint in component["api"]:
                endpoints.append({
                    "path": endpoint["path"],
                    "method": endpoint["method"],
                    "description": endpoint.get("description", ""),
                    "auth": endpoint.get("auth", False)
                })
                
        return endpoints

    def _extract_params(self, component: Dict) -> Dict[str, List[Dict]]:
        """Extract API parameters from component"""
        params = {
            "query": [],
            "path": [],
            "body": []
        }
        
        if "api" in component:
            for endpoint in component["api"]:
                if "params" in endpoint:
                    for param_type, param_list in endpoint["params"].items():
                        params[param_type].extend(param_list)
                        
        return params

    def _extract_responses(self, component: Dict) -> Dict[str, Dict]:
        """Extract API responses from component"""
        responses = {}
        
        if "api" in component:
            for endpoint in component["api"]:
                if "responses" in endpoint:
                    for status, response in endpoint["responses"].items():
                        responses[status] = response
                        
        return responses 