from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import json
import yaml
import logging
from dataclasses import dataclass, field
from enum import Enum
from jinja2 import Environment, FileSystemLoader

class Framework(Enum):
    """Supported frontend frameworks"""
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    SVELTE = "svelte"

@dataclass
class ComponentConfig:
    """Configuration for component generation"""
    name: str
    description: str = ""
    props: List[Dict[str, Any]] = field(default_factory=list)
    state: List[Dict[str, Any]] = field(default_factory=list)
    styles: Optional[Dict[str, Any]] = None
    events: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    lifecycle_hooks: List[str] = field(default_factory=list)

class FrameworkGenerator:
    """Generates framework-specific components and project structures"""
    
    def __init__(self, output_dir: Union[str, Path]):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup template environment
        templates_dir = self.output_dir / "templates" / "frameworks"
        templates_dir.mkdir(parents=True, exist_ok=True)
        self.template_env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Initialize templates
        self._init_templates()
        
        logging.info(f"Framework Generator initialized with output dir: {output_dir}")
        
    def _init_templates(self):
        """Initialize framework templates"""
        templates = {
            'vue.component.jinja2': '''
<template>
  <div class="{{component.name|kebab_case}}">
    {% if component.props %}
    <!-- Props -->
    {% for prop in component.props %}
    <div class="prop-{{prop.name}}">{{ {{prop.name}} }}</div>
    {% endfor %}
    {% endif %}
    
    {% if component.state %}
    <!-- State -->
    {% for state in component.state %}
    <div class="state-{{state.name}}">{{ {{state.name}} }}</div>
    {% endfor %}
    {% endif %}
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
{% if component.dependencies %}
{% for dep in component.dependencies %}
import { {{dep}} } from '@/components'
{% endfor %}
{% endif %}

export default defineComponent({
  name: '{{component.name}}',
  
  {% if component.props %}
  props: {
    {% for prop in component.props %}
    {{prop.name}}: {
      type: {{prop.type}},
      required: {{prop.required|default(false)|lower}},
      {% if prop.default %}default: {{prop.default|tojson}},{% endif %}
    },
    {% endfor %}
  },
  {% endif %}
  
  {% if component.state %}
  data() {
    return {
      {% for state in component.state %}
      {{state.name}}: {{state.initial|default('null')}},
      {% endfor %}
    }
  },
  {% endif %}
  
  {% if component.lifecycle_hooks %}
  {% for hook in component.lifecycle_hooks %}
  {{hook}}() {
    // TODO: Implement {{hook}} logic
  },
  {% endfor %}
  {% endif %}
  
  {% if component.events %}
  methods: {
    {% for event in component.events %}
    {{event.name}}({% if event.params %}{{ event.params|join(', ') }}{% endif %}) {
      // TODO: Implement {{event.name}} logic
      this.$emit('{{event.name}}', {% if event.params %}{{ event.params|join(', ') }}{% endif %})
    },
    {% endfor %}
  },
  {% endif %}
})
</script>

{% if component.styles %}
<style lang="scss" scoped>
.{{component.name|kebab_case}} {
  {% for selector, rules in component.styles.items() %}
  {{selector}} {
    {% for property, value in rules.items() %}
    {{property}}: {{value}};
    {% endfor %}
  }
  {% endfor %}
}
</style>
{% endif %}
''',
            'angular.component.jinja2': '''
import { Component, Input, Output, EventEmitter{% if component.lifecycle_hooks %}, {{component.lifecycle_hooks|join(', ')}}{% endif %} } from '@angular/core';
{% if component.dependencies %}
{% for dep in component.dependencies %}
import { {{dep}} } from '@/components';
{% endfor %}
{% endif %}

@Component({
  selector: 'app-{{component.name|kebab_case}}',
  template: `
    <div class="{{component.name|kebab_case}}">
      {% if component.props %}
      <!-- Props -->
      {% for prop in component.props %}
      <div class="prop-{{prop.name}}">{{ {{prop.name}} }}</div>
      {% endfor %}
      {% endif %}
      
      {% if component.state %}
      <!-- State -->
      {% for state in component.state %}
      <div class="state-{{state.name}}">{{ {{state.name}} }}</div>
      {% endfor %}
      {% endif %}
    </div>
  `,
  {% if component.styles %}
  styles: [`
    .{{component.name|kebab_case}} {
      {% for selector, rules in component.styles.items() %}
      {{selector}} {
        {% for property, value in rules.items() %}
        {{property}}: {{value}};
        {% endfor %}
      }
      {% endfor %}
    }
  `]
  {% endif %}
})
export class {{component.name}}Component {
  {% if component.props %}
  // Props
  {% for prop in component.props %}
  @Input() {{prop.name}}: {{prop.type}}{% if prop.default %} = {{prop.default}}{% endif %};
  {% endfor %}
  {% endif %}
  
  {% if component.state %}
  // State
  {% for state in component.state %}
  {{state.name}} = {{state.initial|default('null')}};
  {% endfor %}
  {% endif %}
  
  {% if component.events %}
  // Events
  {% for event in component.events %}
  @Output() {{event.name}} = new EventEmitter<{{event.type|default('void')}}>();
  {% endfor %}
  {% endif %}
  
  constructor() {}
  
  {% if component.lifecycle_hooks %}
  {% for hook in component.lifecycle_hooks %}
  {{hook}}() {
    // TODO: Implement {{hook}} logic
  }
  {% endfor %}
  {% endif %}
  
  {% if component.events %}
  // Event handlers
  {% for event in component.events %}
  {{event.name}}Handler({% if event.params %}{{ event.params|join(', ') }}{% endif %}) {
    // TODO: Implement {{event.name}} logic
    this.{{event.name}}.emit({% if event.params %}{{ event.params|join(', ') }}{% endif %});
  }
  {% endfor %}
  {% endif %}
}
''',
            'svelte.component.jinja2': '''
<script lang="ts">
{% if component.dependencies %}
{% for dep in component.dependencies %}
import { {{dep}} } from '@/components'
{% endfor %}
{% endif %}

{% if component.props %}
// Props
{% for prop in component.props %}
export let {{prop.name}}: {{prop.type}}{% if prop.default %} = {{prop.default}}{% endif %};
{% endfor %}
{% endif %}

{% if component.state %}
// State
{% for state in component.state %}
let {{state.name}} = {{state.initial|default('null')}};
{% endfor %}
{% endif %}

{% if component.lifecycle_hooks %}
// Lifecycle hooks
{% for hook in component.lifecycle_hooks %}
{{hook}}(() => {
  // TODO: Implement {{hook}} logic
});
{% endfor %}
{% endif %}

{% if component.events %}
// Event handlers
{% for event in component.events %}
function {{event.name}}Handler({% if event.params %}{{ event.params|join(', ') }}{% endif %}) {
  // TODO: Implement {{event.name}} logic
}
{% endfor %}
{% endif %}
</script>

<div class="{{component.name|kebab_case}}">
  {% if component.props %}
  <!-- Props -->
  {% for prop in component.props %}
  <div class="prop-{{prop.name}}">{{{prop.name}}}</div>
  {% endfor %}
  {% endif %}
  
  {% if component.state %}
  <!-- State -->
  {% for state in component.state %}
  <div class="state-{{state.name}}">{{{state.name}}}</div>
  {% endfor %}
  {% endif %}
  
  {% if component.events %}
  <!-- Events -->
  {% for event in component.events %}
  <button on:click={{{event.name}}Handler}>{{event.name}}</button>
  {% endfor %}
  {% endif %}
</div>

{% if component.styles %}
<style lang="scss">
.{{component.name|kebab_case}} {
  {% for selector, rules in component.styles.items() %}
  {{selector}} {
    {% for property, value in rules.items() %}
    {{property}}: {{value}};
    {% endfor %}
  }
  {% endfor %}
}
</style>
{% endif %}
'''
        }
        
        templates_dir = self.output_dir / "templates" / "frameworks"
        for name, content in templates.items():
            template_file = templates_dir / name
            if not template_file.exists():
                template_file.write_text(content)
                
    async def generate_component(self, 
        framework: Framework,
        config: ComponentConfig,
        output_subdir: Optional[str] = None
    ) -> Path:
        """Generate a framework-specific component"""
        try:
            if framework == Framework.VUE:
                return await self._generate_vue_component(config, output_subdir)
            elif framework == Framework.ANGULAR:
                return await self._generate_angular_component(config, output_subdir)
            elif framework == Framework.SVELTE:
                return await self._generate_svelte_component(config, output_subdir)
            else:
                raise ValueError(f"Unsupported framework: {framework}")
                
        except Exception as e:
            logging.error(f"Error generating component: {str(e)}")
            raise
            
    async def _generate_vue_component(self, config: ComponentConfig, output_subdir: Optional[str] = None) -> Path:
        """Generate Vue.js component"""
        try:
            template = self.template_env.get_template('vue.component.jinja2')
            
            output_dir = self.output_dir / 'vue'
            if output_subdir:
                output_dir = output_dir / output_subdir
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / f"{config.name}.vue"
            content = template.render(component=config)
            output_file.write_text(content)
            
            logging.info(f"Generated Vue component: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating Vue component: {str(e)}")
            raise
            
    async def _generate_angular_component(self, config: ComponentConfig, output_subdir: Optional[str] = None) -> Path:
        """Generate Angular component"""
        try:
            template = self.template_env.get_template('angular.component.jinja2')
            
            output_dir = self.output_dir / 'angular'
            if output_subdir:
                output_dir = output_dir / output_subdir
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / f"{config.name}.component.ts"
            content = template.render(component=config)
            output_file.write_text(content)
            
            logging.info(f"Generated Angular component: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating Angular component: {str(e)}")
            raise
            
    async def _generate_svelte_component(self, config: ComponentConfig, output_subdir: Optional[str] = None) -> Path:
        """Generate Svelte component"""
        try:
            template = self.template_env.get_template('svelte.component.jinja2')
            
            output_dir = self.output_dir / 'svelte'
            if output_subdir:
                output_dir = output_dir / output_subdir
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / f"{config.name}.svelte"
            content = template.render(component=config)
            output_file.write_text(content)
            
            logging.info(f"Generated Svelte component: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating Svelte component: {str(e)}")
            raise 