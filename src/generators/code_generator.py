from typing import Dict, List
from ..utils.types import ComponentInfo

class CodeGenerator:
    """Generates code for components and project structure."""
    
    @staticmethod
    def generate_component_code(component: ComponentInfo, structure: Dict) -> str:
        """Generate React component code."""
        template = CodeGenerator._get_component_template(structure)
        
        # Replace template placeholders
        code = template.replace("{{NAME}}", component.name)
        code = code.replace("{{PROPS}}", CodeGenerator._generate_props(structure))
        code = code.replace("{{CONTENT}}", CodeGenerator._generate_content(structure))
        
        return code
    
    @staticmethod
    def _get_component_template(structure: Dict) -> str:
        """Get appropriate component template based on structure."""
        if structure["interactive"]:
            return """
import React, { useState } from 'react';
import './{{NAME}}.css';

export const {{NAME}} = ({ {{PROPS}} }) => {
    const [state, setState] = useState(null);
    
    return (
        <div className="{{NAME}}">
            {{CONTENT}}
        </div>
    );
};
"""
        else:
            return """
import React from 'react';
import './{{NAME}}.css';

export const {{NAME}} = ({ {{PROPS}} }) => {
    return (
        <div className="{{NAME}}">
            {{CONTENT}}
        </div>
    );
};
"""
    
    @staticmethod
    def _generate_props(structure: Dict) -> str:
        """Generate component props based on structure."""
        props = ["children"]
        
        if structure["interactive"]:
            props.extend(["onChange", "onSubmit"])
        
        if structure.get("attributes", {}).get("src"):
            props.extend(["src", "alt"])
            
        return ", ".join(props)
    
    @staticmethod
    def _generate_content(structure: Dict) -> str:
        """Generate component content based on structure."""
        content = []
        
        for child in structure.get("children", []):
            if child in ["button", "a"]:
                content.append(f'<{child} className="{child}-class">{{text}}</{child}>')
            elif child in ["input", "textarea"]:
                content.append(f'<{child} className="{child}-class" {{...props}} />')
            else:
                content.append(f'<{child}>{{children}}</{child}>')
        
        return "\n            ".join(content) if content else "{children}" 