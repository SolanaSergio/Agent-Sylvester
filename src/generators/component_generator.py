from pathlib import Path
from typing import Dict, Optional, List
from ..utils.types import ComponentInfo
import logging
import json
from jinja2 import Environment, FileSystemLoader, Template

class ComponentGenerator:
    """Generates React components from templates"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.template_env = Environment(
            loader=FileSystemLoader(str(output_dir / "templates")),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Load base templates
        self._load_base_templates()
        
    async def generate_component(self, component: ComponentInfo, template: Optional[Dict] = None) -> Optional[Path]:
        """Generate a React component from template"""
        try:
            component_dir = self.output_dir / component.name
            component_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate component files
            await self._generate_component_files(component_dir, component, template)
            
            # Generate styles
            await self._generate_styles(component_dir, component)
            
            # Generate types
            await self._generate_types(component_dir, component)
            
            # Generate index file
            await self._generate_index(component_dir, component)
            
            return component_dir
            
        except Exception as e:
            logging.error(f"Error generating component {component.name}: {str(e)}")
            return None
            
    async def generate_variant(self, variants_dir: Path, component: ComponentInfo, variant: Dict):
        """Generate a component variant"""
        try:
            variant_name = variant['name']
            variant_dir = variants_dir / variant_name
            variant_dir.mkdir(parents=True, exist_ok=True)
            
            # Create variant component
            variant_component = ComponentInfo(
                name=variant_name,
                html=variant.get('html', component.html),
                structure=variant.get('structure', component.structure),
                dependencies=component.dependencies,
                styles=variant.get('styles', component.styles)
            )
            
            # Generate variant files
            await self._generate_component_files(variant_dir, variant_component)
            await self._generate_styles(variant_dir, variant_component)
            
        except Exception as e:
            logging.error(f"Error generating variant {variant['name']} for {component.name}: {str(e)}")
            
    async def generate_unit_tests(self, tests_dir: Path, component: ComponentInfo):
        """Generate unit tests for a component"""
        try:
            test_file = tests_dir / f"{component.name}.test.tsx"
            
            template = self.template_env.get_template('unit-test.tsx.jinja2')
            content = template.render(
                component=component,
                test_cases=self._generate_test_cases(component)
            )
            
            test_file.write_text(content)
            
        except Exception as e:
            logging.error(f"Error generating unit tests for {component.name}: {str(e)}")
            
    async def generate_integration_tests(self, tests_dir: Path, component: ComponentInfo):
        """Generate integration tests for a component"""
        try:
            test_file = tests_dir / f"{component.name}.integration.test.tsx"
            
            template = self.template_env.get_template('integration-test.tsx.jinja2')
            content = template.render(
                component=component,
                dependencies=component.dependencies,
                test_cases=self._generate_integration_test_cases(component)
            )
            
            test_file.write_text(content)
            
        except Exception as e:
            logging.error(f"Error generating integration tests for {component.name}: {str(e)}")
            
    async def generate_stories(self, docs_dir: Path, component: ComponentInfo):
        """Generate Storybook stories for a component"""
        try:
            stories_file = docs_dir / f"{component.name}.stories.tsx"
            
            template = self.template_env.get_template('stories.tsx.jinja2')
            content = template.render(
                component=component,
                variants=component.variants
            )
            
            stories_file.write_text(content)
            
        except Exception as e:
            logging.error(f"Error generating stories for {component.name}: {str(e)}")
            
    async def generate_api_docs(self, docs_dir: Path, component: ComponentInfo):
        """Generate API documentation for a component"""
        try:
            api_file = docs_dir / "API.md"
            
            template = self.template_env.get_template('api-docs.md.jinja2')
            content = template.render(
                component=component,
                props=self._extract_props(component)
            )
            
            api_file.write_text(content)
            
        except Exception as e:
            logging.error(f"Error generating API docs for {component.name}: {str(e)}")
            
    async def _generate_component_files(self, component_dir: Path, component: ComponentInfo, template: Optional[Dict] = None):
        """Generate the main component files"""
        try:
            # Generate main component file
            component_file = component_dir / f"{component.name}.tsx"
            
            if template:
                # Use provided template
                content = self._render_template(template['content'], component)
            else:
                # Use base template
                template = self.template_env.get_template('component.tsx.jinja2')
                content = template.render(component=component)
                
            component_file.write_text(content)
            
        except Exception as e:
            logging.error(f"Error generating files for {component.name}: {str(e)}")
            
    async def _generate_styles(self, component_dir: Path, component: ComponentInfo):
        """Generate component styles"""
        try:
            if component.styles:
                styles_file = component_dir / f"{component.name}.styles.ts"
                
                template = self.template_env.get_template('styles.ts.jinja2')
                content = template.render(
                    component=component,
                    styles=component.styles
                )
                
                styles_file.write_text(content)
                
        except Exception as e:
            logging.error(f"Error generating styles for {component.name}: {str(e)}")
            
    async def _generate_types(self, component_dir: Path, component: ComponentInfo):
        """Generate component type definitions"""
        try:
            types_file = component_dir / f"{component.name}.types.ts"
            
            template = self.template_env.get_template('types.ts.jinja2')
            content = template.render(
                component=component,
                props=self._extract_props(component)
            )
            
            types_file.write_text(content)
            
        except Exception as e:
            logging.error(f"Error generating types for {component.name}: {str(e)}")
            
    async def _generate_index(self, component_dir: Path, component: ComponentInfo):
        """Generate index file for the component"""
        try:
            index_file = component_dir / "index.ts"
            
            template = self.template_env.get_template('index.ts.jinja2')
            content = template.render(component=component)
            
            index_file.write_text(content)
            
        except Exception as e:
            logging.error(f"Error generating index for {component.name}: {str(e)}")
            
    def _load_base_templates(self):
        """Load base component templates"""
        templates_dir = self.output_dir / "templates"
        if not templates_dir.exists():
            templates_dir.mkdir(parents=True)
            
            # Create base templates
            self._create_base_template('component.tsx.jinja2')
            self._create_base_template('styles.ts.jinja2')
            self._create_base_template('types.ts.jinja2')
            self._create_base_template('index.ts.jinja2')
            self._create_base_template('unit-test.tsx.jinja2')
            self._create_base_template('integration-test.tsx.jinja2')
            self._create_base_template('stories.tsx.jinja2')
            self._create_base_template('api-docs.md.jinja2')
            
    def _create_base_template(self, template_name: str):
        """Create a base template file"""
        template_file = self.output_dir / "templates" / template_name
        
        if not template_file.exists():
            with open(template_file, 'w') as f:
                f.write(self._get_base_template_content(template_name))
                
    def _get_base_template_content(self, template_name: str) -> str:
        """Get content for base templates"""
        if template_name == 'component.tsx.jinja2':
            return '''
import React from 'react';
import { {{ component.name }}Props } from './{{ component.name }}.types';
{% if component.styles %}
import { {{ component.name }}Styles } from './{{ component.name }}.styles';
{% endif %}

export const {{ component.name }}: React.FC<{{ component.name }}Props> = ({
    {% for prop in props %}
    {{ prop.name }}{% if prop.default %} = {{ prop.default }}{% endif %},
    {% endfor %}
}) => {
    return (
        {{ component.html | safe }}
    );
};
'''
        elif template_name == 'styles.ts.jinja2':
            return '''
import styled from 'styled-components';

{% for style in styles %}
export const {{ style.name }} = styled.{{ style.element }}`
    {{ style.css | safe }}
`;
{% endfor %}
'''
        elif template_name == 'types.ts.jinja2':
            return '''
export interface {{ component.name }}Props {
    {% for prop in props %}
    {{ prop.name }}{% if not prop.required %}?{% endif %}: {{ prop.type }};
    {% endfor %}
}
'''
        elif template_name == 'index.ts.jinja2':
            return '''
export * from './{{ component.name }}';
export * from './{{ component.name }}.types';
{% if component.styles %}
export * from './{{ component.name }}.styles';
{% endif %}
'''
        elif template_name == 'unit-test.tsx.jinja2':
            return '''
import React from 'react';
import { render, screen } from '@testing-library/react';
import { {{ component.name }} } from './{{ component.name }}';

describe('{{ component.name }}', () => {
    {% for test in test_cases %}
    it('{{ test.description }}', () => {
        {{ test.code | safe }}
    });
    {% endfor %}
});
'''
        elif template_name == 'integration-test.tsx.jinja2':
            return '''
import React from 'react';
import { render, screen } from '@testing-library/react';
import { {{ component.name }} } from './{{ component.name }}';
{% for dep in dependencies %}
import { {{ dep }} } from '{{ dep }}';
{% endfor %}

describe('{{ component.name }} Integration', () => {
    {% for test in test_cases %}
    it('{{ test.description }}', () => {
        {{ test.code | safe }}
    });
    {% endfor %}
});
'''
        elif template_name == 'stories.tsx.jinja2':
            return '''
import React from 'react';
import { Story, Meta } from '@storybook/react';
import { {{ component.name }} } from './{{ component.name }}';
import { {{ component.name }}Props } from './{{ component.name }}.types';

export default {
    title: 'Components/{{ component.name }}',
    component: {{ component.name }},
} as Meta;

const Template: Story<{{ component.name }}Props> = (args) => <{{ component.name }} {...args} />;

export const Default = Template.bind({});
Default.args = {
    {% for prop in props %}
    {{ prop.name }}: {{ prop.default }},
    {% endfor %}
};

{% for variant in variants %}
export const {{ variant.name }} = Template.bind({});
{{ variant.name }}.args = {
    {% for prop in variant.props %}
    {{ prop.name }}: {{ prop.value }},
    {% endfor %}
};
{% endfor %}
'''
        elif template_name == 'api-docs.md.jinja2':
            return '''
# {{ component.name }}

{{ component.description }}

## Props

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
{% for prop in props %}
| {{ prop.name }} | `{{ prop.type }}` | {{ prop.required }} | {{ prop.default }} | {{ prop.description }} |
{% endfor %}

## Examples

```tsx
import { {{ component.name }} } from './{{ component.name }}';

// Basic usage
<{{ component.name }} />

// With props
<{{ component.name }}
    {% for prop in props %}
    {{ prop.name }}={{ prop.example }}
    {% endfor %}
/>
```
'''
            
    def _extract_props(self, component: ComponentInfo) -> List[Dict]:
        """Extract component props from structure"""
        props = []
        if component.structure and 'props' in component.structure:
            for prop_name, prop_info in component.structure['props'].items():
                props.append({
                    'name': prop_name,
                    'type': prop_info.get('type', 'any'),
                    'required': prop_info.get('required', False),
                    'default': prop_info.get('default'),
                    'description': prop_info.get('description', ''),
                    'example': prop_info.get('example')
                })
        return props
        
    def _generate_test_cases(self, component: ComponentInfo) -> List[Dict]:
        """Generate test cases for the component"""
        test_cases = []
        
        # Basic render test
        test_cases.append({
            'description': 'renders without crashing',
            'code': '''
                render(<{{ component.name }} />);
                expect(screen.getByTestId('{{ component.name }}')).toBeInTheDocument();
            '''
        })
        
        # Props tests
        for prop in self._extract_props(component):
            if prop['required']:
                test_cases.append({
                    'description': f'renders with required prop {prop["name"]}',
                    'code': f'''
                        render(<{{ component.name }} {prop['name']}={prop['example']} />);
                        expect(screen.getByTestId('{{ component.name }}')).toHaveAttribute('{prop['name']}', '{prop['example']}');
                    '''
                })
                
        return test_cases
        
    def _generate_integration_test_cases(self, component: ComponentInfo) -> List[Dict]:
        """Generate integration test cases"""
        test_cases = []
        
        # Test interaction with dependencies
        for dep in component.dependencies or []:
            test_cases.append({
                'description': f'integrates with {dep}',
                'code': f'''
                    render(
                        <{dep}>
                            <{{ component.name }} />
                        </{dep}>
                    );
                    expect(screen.getByTestId('{{ component.name }}')).toBeInTheDocument();
                '''
            })
            
        return test_cases
        
    def _render_template(self, template_str: str, component: ComponentInfo) -> str:
        """Render a template string with component data"""
        template = Template(template_str)
        return template.render(
            component=component,
            props=self._extract_props(component)
        ) 