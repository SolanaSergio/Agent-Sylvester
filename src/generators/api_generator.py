from typing import Dict, List, Optional, Union, Any, Callable
from pathlib import Path
import json
import yaml
import logging
from dataclasses import dataclass, field
from enum import Enum
from jinja2 import Environment, FileSystemLoader

class HttpMethod(Enum):
    """Supported HTTP methods"""
    GET = "get"
    POST = "post"
    PUT = "put"
    PATCH = "patch"
    DELETE = "delete"

@dataclass
class EndpointParameter:
    """Defines an API endpoint parameter"""
    name: str
    type: str
    required: bool = True
    description: str = ""
    location: str = "body"  # body, query, path, header
    schema: Optional[Dict[str, Any]] = None
    example: Optional[Any] = None

@dataclass
class EndpointResponse:
    """Defines an API endpoint response"""
    status_code: int
    description: str
    content_type: str = "application/json"
    schema: Optional[Dict[str, Any]] = None
    example: Optional[Any] = None

@dataclass
class EndpointDefinition:
    """Defines a complete API endpoint"""
    path: str
    method: HttpMethod
    summary: str
    description: str = ""
    parameters: List[EndpointParameter] = field(default_factory=list)
    request_body: Optional[EndpointParameter] = None
    responses: Dict[int, EndpointResponse] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    security: List[Dict[str, List[str]]] = field(default_factory=list)
    middleware: List[str] = field(default_factory=list)

class ApiGenerator:
    """Generates API endpoints, documentation, and type definitions"""
    
    def __init__(self, output_dir: Union[str, Path]):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup template environment
        templates_dir = self.output_dir / "templates" / "api"
        templates_dir.mkdir(parents=True, exist_ok=True)
        self.template_env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Initialize templates
        self._init_templates()
        
        logging.info(f"API Generator initialized with output dir: {output_dir}")
        
    def _init_templates(self):
        """Initialize API templates"""
        templates = {
            'express.route.jinja2': '''
import { Router } from 'express';
import { z } from 'zod';
{% if endpoint.middleware %}
import { {{endpoint.middleware|join(', ')}} } from '../middleware';
{% endif %}

const router = Router();

{% if endpoint.request_body and endpoint.request_body.schema %}
const {{endpoint.path|replace('/', '_')|trim('_')}}Schema = z.object({{endpoint.request_body.schema|tojson}});
{% endif %}

/**
 * @swagger
 * {{endpoint.path}}:
 *   {{endpoint.method.value}}:
 *     summary: {{endpoint.summary}}
 *     description: {{endpoint.description}}
 *     tags: {{endpoint.tags|tojson}}
 *     {% if endpoint.parameters %}
 *     parameters:
 *       {% for param in endpoint.parameters %}
 *       - name: {{param.name}}
 *         in: {{param.location}}
 *         description: {{param.description}}
 *         required: {{param.required|lower}}
 *         schema:
 *           type: {{param.type}}
 *       {% endfor %}
 *     {% endif %}
 *     {% if endpoint.request_body %}
 *     requestBody:
 *       required: {{endpoint.request_body.required|lower}}
 *       content:
 *         application/json:
 *           schema: {{endpoint.request_body.schema|tojson}}
 *     {% endif %}
 *     responses:
 *       {% for status, response in endpoint.responses.items() %}
 *       '{{status}}':
 *         description: {{response.description}}
 *         content:
 *           {{response.content_type}}:
 *             schema: {{response.schema|tojson}}
 *       {% endfor %}
 */
router.{{endpoint.method.value}}('{{endpoint.path}}', 
  {% if endpoint.middleware %}[{{endpoint.middleware|join(', ')}}],{% endif %}
  async (req, res) => {
    try {
      {% if endpoint.request_body and endpoint.request_body.schema %}
      const data = {{endpoint.path|replace('/', '_')|trim('_')}}Schema.parse(req.body);
      {% endif %}
      
      // TODO: Implement endpoint logic
      
      {% for status, response in endpoint.responses.items() %}
      {% if status == 200 or status == 201 %}
      return res.status({{status}}).json({{response.example|tojson if response.example else '{ success: true }'}});
      {% endif %}
      {% endfor %}
      
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({ error: error.errors });
      }
      return res.status(500).json({ error: 'Internal server error' });
    }
});

export default router;
''',
            'fastapi.route.jinja2': '''
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter()

{% if endpoint.request_body and endpoint.request_body.schema %}
class {{endpoint.path|replace('/', '_')|trim('_')}}Request(BaseModel):
    {% for field_name, field_schema in endpoint.request_body.schema.items() %}
    {{field_name}}: {{field_schema.type}}{% if not field_schema.required %} = None{% endif %}
    {% endfor %}
{% endif %}

{% for status, response in endpoint.responses.items() %}
{% if response.schema %}
class {{endpoint.path|replace('/', '_')|trim('_')}}Response{{status}}(BaseModel):
    {% for field_name, field_schema in response.schema.items() %}
    {{field_name}}: {{field_schema.type}}{% if not field_schema.required %} = None{% endif %}
    {% endfor %}
{% endif %}
{% endfor %}

@router.{{endpoint.method.value}}(
    "{{endpoint.path}}",
    response_model={{endpoint.path|replace('/', '_')|trim('_')}}Response200,
    summary="{{endpoint.summary}}",
    description="""{{endpoint.description}}""",
    tags={{endpoint.tags|tojson}},
)
{% if endpoint.middleware %}
{% for mw in endpoint.middleware %}
@{{mw}}
{% endfor %}
{% endif %}
async def {{endpoint.path|replace('/', '_')|trim('_')}}(
    {% for param in endpoint.parameters %}
    {{param.name}}: {{param.type}}{% if not param.required %} = None{% endif %},
    {% endfor %}
    {% if endpoint.request_body %}
    request: {{endpoint.path|replace('/', '_')|trim('_')}}Request,
    {% endif %}
):
    try:
        # TODO: Implement endpoint logic
        
        {% for status, response in endpoint.responses.items() %}
        {% if status == 200 or status == 201 %}
        return {{response.example|tojson if response.example else '{"success": True}'}}
        {% endif %}
        {% endfor %}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
''',
            'openapi.yaml.jinja2': '''
openapi: 3.0.0
info:
  title: {{api_info.title}}
  version: {{api_info.version}}
  description: {{api_info.description}}

paths:
  {% for endpoint in endpoints %}
  {{endpoint.path}}:
    {{endpoint.method.value}}:
      summary: {{endpoint.summary}}
      description: {{endpoint.description}}
      tags: {{endpoint.tags|tojson}}
      {% if endpoint.parameters %}
      parameters:
        {% for param in endpoint.parameters %}
        - name: {{param.name}}
          in: {{param.location}}
          description: {{param.description}}
          required: {{param.required|lower}}
          schema:
            type: {{param.type}}
        {% endfor %}
      {% endif %}
      {% if endpoint.request_body %}
      requestBody:
        required: {{endpoint.request_body.required|lower}}
        content:
          application/json:
            schema: {{endpoint.request_body.schema|tojson}}
      {% endif %}
      responses:
        {% for status, response in endpoint.responses.items() %}
        '{{status}}':
          description: {{response.description}}
          content:
            {{response.content_type}}:
              schema: {{response.schema|tojson}}
        {% endfor %}
      {% if endpoint.security %}
      security: {{endpoint.security|tojson}}
      {% endif %}
  {% endfor %}

components:
  securitySchemes:
    {{security_schemes|tojson}}
'''
        }
        
        templates_dir = self.output_dir / "templates" / "api"
        for name, content in templates.items():
            template_file = templates_dir / name
            if not template_file.exists():
                template_file.write_text(content)
                
    async def generate_endpoint(self, endpoint: EndpointDefinition, framework: str = 'fastapi') -> Path:
        """Generate API endpoint code for specified framework"""
        try:
            if framework == 'fastapi':
                return await self._generate_fastapi_endpoint(endpoint)
            elif framework == 'express':
                return await self._generate_express_endpoint(endpoint)
            else:
                raise ValueError(f"Unsupported framework: {framework}")
                
        except Exception as e:
            logging.error(f"Error generating endpoint: {str(e)}")
            raise
            
    async def _generate_fastapi_endpoint(self, endpoint: EndpointDefinition) -> Path:
        """Generate FastAPI endpoint"""
        try:
            template = self.template_env.get_template('fastapi.route.jinja2')
            output_file = self.output_dir / 'fastapi' / 'routes' / f"{endpoint.path.lstrip('/')}.py"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            content = template.render(endpoint=endpoint)
            output_file.write_text(content)
            
            logging.info(f"Generated FastAPI endpoint: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating FastAPI endpoint: {str(e)}")
            raise
            
    async def _generate_express_endpoint(self, endpoint: EndpointDefinition) -> Path:
        """Generate Express.js endpoint"""
        try:
            template = self.template_env.get_template('express.route.jinja2')
            output_file = self.output_dir / 'express' / 'routes' / f"{endpoint.path.lstrip('/')}.ts"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            content = template.render(endpoint=endpoint)
            output_file.write_text(content)
            
            logging.info(f"Generated Express endpoint: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating Express endpoint: {str(e)}")
            raise
            
    async def generate_openapi_spec(self, 
        endpoints: List[EndpointDefinition],
        api_info: Dict[str, str],
        security_schemes: Dict[str, Any]
    ) -> Path:
        """Generate OpenAPI specification"""
        try:
            template = self.template_env.get_template('openapi.yaml.jinja2')
            output_file = self.output_dir / 'openapi.yaml'
            
            content = template.render(
                endpoints=endpoints,
                api_info=api_info,
                security_schemes=security_schemes
            )
            output_file.write_text(content)
            
            logging.info(f"Generated OpenAPI spec: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating OpenAPI spec: {str(e)}")
            raise 