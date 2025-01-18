from typing import Dict, List, Optional, Union, Any
from pathlib import Path
import json
import yaml
import logging
from dataclasses import dataclass, field
from enum import Enum
from jinja2 import Environment, FileSystemLoader

class DataType(Enum):
    """Supported data types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    UUID = "uuid"
    ENUM = "enum"
    ARRAY = "array"
    OBJECT = "object"
    
@dataclass
class FieldDefinition:
    """Defines a schema field"""
    name: str
    type: DataType
    required: bool = True
    unique: bool = False
    default: Any = None
    description: str = ""
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    enum_values: Optional[List[str]] = None
    foreign_key: Optional[str] = None
    nested_schema: Optional[Dict[str, Any]] = None
    array_type: Optional[DataType] = None
    validators: List[str] = field(default_factory=list)

@dataclass
class SchemaDefinition:
    """Defines a complete schema"""
    name: str
    fields: List[FieldDefinition]
    description: str = ""
    timestamps: bool = True
    soft_delete: bool = True
    indexes: List[Dict[str, Any]] = field(default_factory=list)
    unique_constraints: List[List[str]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)

class SchemaGenerator:
    """Generates database schemas, types, and validation rules"""
    
    def __init__(self, output_dir: Union[str, Path]):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup template environment
        templates_dir = self.output_dir / "templates" / "schemas"
        templates_dir.mkdir(parents=True, exist_ok=True)
        self.template_env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Initialize templates
        self._init_templates()
        
        logging.info(f"Schema Generator initialized with output dir: {output_dir}")
        
    def _init_templates(self):
        """Initialize schema templates"""
        templates = {
            'prisma.schema.jinja2': '''
// {{schema.name}} Schema
/// {{schema.description}}
model {{schema.name}} {
  {% for field in schema.fields %}
  {{field.name}} {{self._get_prisma_type(field)}}{% if field.required %} @required{% endif %}{% if field.unique %} @unique{% endif %}{% if field.default %} @default({{field.default}}){% endif %}
  {% endfor %}
  
  {% if schema.timestamps %}
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  {% endif %}
  
  {% if schema.soft_delete %}
  deletedAt DateTime?
  {% endif %}
  
  {% for index in schema.indexes %}
  @@index([{{index.fields|join(', ')}}])
  {% endfor %}
  
  {% for constraint in schema.unique_constraints %}
  @@unique([{{constraint|join(', ')}}])
  {% endfor %}
  
  {% for relation in schema.relationships %}
  {{relation.name}} {{relation.type}} @relation(fields: [{{relation.fields|join(', ')}}], references: [{{relation.references|join(', ')}}])
  {% endfor %}
}
''',
            'typescript.types.jinja2': '''
// {{schema.name}} Type Definitions

{% for field in schema.fields %}
{% if field.type == DataType.ENUM and field.enum_values %}
export enum {{schema.name}}{{field.name|capitalize}} {
  {% for value in field.enum_values %}
  {{value}} = "{{value}}",
  {% endfor %}
}
{% endif %}
{% endfor %}

export interface {{schema.name}} {
  {% for field in schema.fields %}
  {{field.name}}{% if not field.required %}?{% endif %}: {{self._get_typescript_type(field)}};
  {% endfor %}
  
  {% if schema.timestamps %}
  createdAt: Date;
  updatedAt: Date;
  {% endif %}
  
  {% if schema.soft_delete %}
  deletedAt?: Date;
  {% endif %}
}
''',
            'zod.schema.jinja2': '''
import { z } from 'zod';

{% for field in schema.fields %}
{% if field.type == DataType.ENUM and field.enum_values %}
export const {{schema.name}}{{field.name|capitalize}}Schema = z.enum([
  {% for value in field.enum_values %}
  "{{value}}",
  {% endfor %}
]);
{% endif %}
{% endfor %}

export const {{schema.name}}Schema = z.object({
  {% for field in schema.fields %}
  {{field.name}}: {{self._get_zod_validator(field)}},
  {% endfor %}
  
  {% if schema.timestamps %}
  createdAt: z.date(),
  updatedAt: z.date(),
  {% endif %}
  
  {% if schema.soft_delete %}
  deletedAt: z.date().nullable(),
  {% endif %}
});

export type {{schema.name}}Type = z.infer<typeof {{schema.name}}Schema>;
''',
            'mongoose.schema.jinja2': '''
import { Schema, model } from 'mongoose';

const {{schema.name}}Schema = new Schema({
  {% for field in schema.fields %}
  {{field.name}}: { 
    type: {{self._get_mongoose_type(field)}},
    required: {{field.required|lower}},
    {% if field.unique %}unique: true,{% endif %}
    {% if field.default %}default: {{field.default}},{% endif %}
    {% if field.description %}description: "{{field.description}}",{% endif %}
    {% if field.min_length %}minLength: {{field.min_length}},{% endif %}
    {% if field.max_length %}maxLength: {{field.max_length}},{% endif %}
    {% if field.min_value %}min: {{field.min_value}},{% endif %}
    {% if field.max_value %}max: {{field.max_value}},{% endif %}
    {% if field.pattern %}match: /{{field.pattern}}/,{% endif %}
    {% if field.enum_values %}enum: [{% for value in field.enum_values %}"{{value}}"{% if not loop.last %}, {% endif %}{% endfor %}],{% endif %}
  },
  {% endfor %}
  
  {% if schema.timestamps %}
  createdAt: { type: Date, default: Date.now },
  updatedAt: { type: Date, default: Date.now },
  {% endif %}
  
  {% if schema.soft_delete %}
  deletedAt: { type: Date, default: null },
  {% endif %}
}, {
  timestamps: {{schema.timestamps|lower}},
  {% if schema.indexes %}
  indexes: [
    {% for index in schema.indexes %}
    { {% for field, direction in index.fields.items() %}{{field}}: {{direction}}{% if not loop.last %}, {% endif %}{% endfor %} },
    {% endfor %}
  ],
  {% endif %}
});

export const {{schema.name}} = model('{{schema.name}}', {{schema.name}}Schema);
'''
        }
        
        templates_dir = self.output_dir / "templates" / "schemas"
        for name, content in templates.items():
            template_file = templates_dir / name
            if not template_file.exists():
                template_file.write_text(content)
                
    async def generate_schema(self, schema: SchemaDefinition, output_formats: List[str]) -> Dict[str, Path]:
        """Generate schema files in specified formats"""
        results = {}
        
        try:
            for format in output_formats:
                if format == 'prisma':
                    results['prisma'] = await self._generate_prisma_schema(schema)
                elif format == 'typescript':
                    results['typescript'] = await self._generate_typescript_types(schema)
                elif format == 'zod':
                    results['zod'] = await self._generate_zod_schema(schema)
                elif format == 'mongoose':
                    results['mongoose'] = await self._generate_mongoose_schema(schema)
                    
            return results
            
        except Exception as e:
            logging.error(f"Error generating schema: {str(e)}")
            raise
            
    async def _generate_prisma_schema(self, schema: SchemaDefinition) -> Path:
        """Generate Prisma schema"""
        try:
            template = self.template_env.get_template('prisma.schema.jinja2')
            output_file = self.output_dir / 'prisma' / f"{schema.name}.prisma"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            content = template.render(schema=schema)
            output_file.write_text(content)
            
            logging.info(f"Generated Prisma schema: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating Prisma schema: {str(e)}")
            raise
            
    async def _generate_typescript_types(self, schema: SchemaDefinition) -> Path:
        """Generate TypeScript type definitions"""
        try:
            template = self.template_env.get_template('typescript.types.jinja2')
            output_file = self.output_dir / 'typescript' / f"{schema.name}.types.ts"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            content = template.render(schema=schema)
            output_file.write_text(content)
            
            logging.info(f"Generated TypeScript types: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating TypeScript types: {str(e)}")
            raise
            
    async def _generate_zod_schema(self, schema: SchemaDefinition) -> Path:
        """Generate Zod validation schema"""
        try:
            template = self.template_env.get_template('zod.schema.jinja2')
            output_file = self.output_dir / 'zod' / f"{schema.name}.schema.ts"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            content = template.render(schema=schema)
            output_file.write_text(content)
            
            logging.info(f"Generated Zod schema: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating Zod schema: {str(e)}")
            raise
            
    async def _generate_mongoose_schema(self, schema: SchemaDefinition) -> Path:
        """Generate Mongoose schema"""
        try:
            template = self.template_env.get_template('mongoose.schema.jinja2')
            output_file = self.output_dir / 'mongoose' / f"{schema.name}.schema.ts"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            content = template.render(schema=schema)
            output_file.write_text(content)
            
            logging.info(f"Generated Mongoose schema: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating Mongoose schema: {str(e)}")
            raise
            
    def _get_prisma_type(self, field: FieldDefinition) -> str:
        """Convert field type to Prisma type"""
        type_mapping = {
            DataType.STRING: "String",
            DataType.INTEGER: "Int",
            DataType.FLOAT: "Float",
            DataType.BOOLEAN: "Boolean",
            DataType.DATE: "DateTime",
            DataType.DATETIME: "DateTime",
            DataType.JSON: "Json",
            DataType.UUID: "String @id @default(uuid())",
            DataType.ENUM: f"Enum{field.enum_values}",
            DataType.ARRAY: "Json",
            DataType.OBJECT: "Json"
        }
        return type_mapping.get(field.type, "String")
        
    def _get_typescript_type(self, field: FieldDefinition) -> str:
        """Convert field type to TypeScript type"""
        type_mapping = {
            DataType.STRING: "string",
            DataType.INTEGER: "number",
            DataType.FLOAT: "number",
            DataType.BOOLEAN: "boolean",
            DataType.DATE: "Date",
            DataType.DATETIME: "Date",
            DataType.JSON: "any",
            DataType.UUID: "string",
            DataType.ENUM: f"{field.name}Enum",
            DataType.ARRAY: f"Array<{self._get_typescript_type(FieldDefinition('', field.array_type))}>",
            DataType.OBJECT: "Record<string, any>"
        }
        return type_mapping.get(field.type, "string")
        
    def _get_zod_validator(self, field: FieldDefinition) -> str:
        """Convert field type to Zod validator"""
        base_type = {
            DataType.STRING: "z.string()",
            DataType.INTEGER: "z.number().int()",
            DataType.FLOAT: "z.number()",
            DataType.BOOLEAN: "z.boolean()",
            DataType.DATE: "z.date()",
            DataType.DATETIME: "z.date()",
            DataType.JSON: "z.any()",
            DataType.UUID: "z.string().uuid()",
            DataType.ENUM: f"{field.name}Schema",
            DataType.ARRAY: f"z.array({self._get_zod_validator(FieldDefinition('', field.array_type))})",
            DataType.OBJECT: "z.record(z.string(), z.any())"
        }.get(field.type, "z.string()")
        
        # Add validators
        validators = []
        if not field.required:
            validators.append("optional()")
        if field.min_length:
            validators.append(f"min({field.min_length})")
        if field.max_length:
            validators.append(f"max({field.max_length})")
        if field.pattern:
            validators.append(f"regex(/{field.pattern}/)")
            
        return f"{base_type}" + "".join(f".{v}" for v in validators)
        
    def _get_mongoose_type(self, field: FieldDefinition) -> str:
        """Convert field type to Mongoose type"""
        type_mapping = {
            DataType.STRING: "String",
            DataType.INTEGER: "Number",
            DataType.FLOAT: "Number",
            DataType.BOOLEAN: "Boolean",
            DataType.DATE: "Date",
            DataType.DATETIME: "Date",
            DataType.JSON: "Mixed",
            DataType.UUID: "String",
            DataType.ENUM: "String",
            DataType.ARRAY: f"[{self._get_mongoose_type(FieldDefinition('', field.array_type))}]",
            DataType.OBJECT: "Mixed"
        }
        return type_mapping.get(field.type, "String") 