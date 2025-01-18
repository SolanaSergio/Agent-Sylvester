from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path
import json
import yaml
import logging
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import hashlib

class MigrationType(Enum):
    """Types of database migrations"""
    CREATE_TABLE = "create_table"
    ALTER_TABLE = "alter_table"
    DROP_TABLE = "drop_table"
    ADD_COLUMN = "add_column"
    ALTER_COLUMN = "alter_column"
    DROP_COLUMN = "drop_column"
    ADD_INDEX = "add_index"
    DROP_INDEX = "drop_index"
    ADD_CONSTRAINT = "add_constraint"
    DROP_CONSTRAINT = "drop_constraint"
    DATA_MIGRATION = "data_migration"

@dataclass
class MigrationStep:
    """Defines a single migration step"""
    type: MigrationType
    name: str
    description: str
    up_sql: str
    down_sql: str
    dependencies: List[str] = field(default_factory=list)
    data_transformations: Optional[Dict[str, Any]] = None
    checksum: Optional[str] = None

@dataclass
class Migration:
    """Defines a complete database migration"""
    version: str
    name: str
    description: str
    steps: List[MigrationStep]
    created_at: datetime = field(default_factory=datetime.now)
    applied: bool = False
    checksum: Optional[str] = None

class MigrationGenerator:
    """Generates database migrations and handles schema evolution"""
    
    def __init__(self, output_dir: Union[str, Path]):
        self.output_dir = Path(output_dir)
        self.migrations_dir = self.output_dir / "migrations"
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup template environment
        templates_dir = self.output_dir / "templates" / "migrations"
        templates_dir.mkdir(parents=True, exist_ok=True)
        self.template_env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Initialize templates
        self._init_templates()
        
        # Load migration history
        self.migration_history: List[Migration] = []
        self._load_migration_history()
        
        logging.info(f"Migration Generator initialized with output dir: {output_dir}")
        
    def _init_templates(self):
        """Initialize migration templates"""
        templates = {
            'migration.sql.jinja2': '''
-- Migration: {{migration.name}}
-- Version: {{migration.version}}
-- Description: {{migration.description}}
-- Created At: {{migration.created_at}}

-- Up Migration
{% for step in migration.steps %}
-- Step: {{step.name}}
-- Type: {{step.type.value}}
-- Description: {{step.description}}

{{step.up_sql}}

{% endfor %}

-- Down Migration
{% for step in migration.steps|reverse %}
-- Step: {{step.name}}
-- Type: {{step.type.value}}
-- Description: {{step.description}}

{{step.down_sql}}

{% endfor %}
''',
            'migration.ts.jinja2': '''
import { MigrationInterface, QueryRunner } from "typeorm";

export class {{migration.name|pascal_case}}{{migration.version}} implements MigrationInterface {
    name = '{{migration.name}}_{{migration.version}}';

    public async up(queryRunner: QueryRunner): Promise<void> {
        {% for step in migration.steps %}
        // {{step.description}}
        await queryRunner.query(`{{step.up_sql|replace('`', '\\`')}}`);
        {% endfor %}
    }

    public async down(queryRunner: QueryRunner): Promise<void> {
        {% for step in migration.steps|reverse %}
        // {{step.description}}
        await queryRunner.query(`{{step.down_sql|replace('`', '\\`')}}`);
        {% endfor %}
    }
}
''',
            'migration.py.jinja2': '''
"""
Migration: {{migration.name}}
Version: {{migration.version}}
Description: {{migration.description}}
Created At: {{migration.created_at}}
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '{{migration.version}}'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    {% for step in migration.steps %}
    # {{step.description}}
    {% if step.type == MigrationType.CREATE_TABLE %}
    {{step.up_sql}}
    {% elif step.type == MigrationType.ALTER_TABLE %}
    {{step.up_sql}}
    {% elif step.type == MigrationType.DATA_MIGRATION %}
    # Data migration code
    {{step.up_sql}}
    {% else %}
    op.execute("""
    {{step.up_sql}}
    """)
    {% endif %}
    {% endfor %}

def downgrade():
    {% for step in migration.steps|reverse %}
    # {{step.description}}
    {% if step.type == MigrationType.CREATE_TABLE %}
    {{step.down_sql}}
    {% elif step.type == MigrationType.ALTER_TABLE %}
    {{step.down_sql}}
    {% elif step.type == MigrationType.DATA_MIGRATION %}
    # Data migration code
    {{step.down_sql}}
    {% else %}
    op.execute("""
    {{step.down_sql}}
    """)
    {% endif %}
    {% endfor %}
'''
        }
        
        templates_dir = self.output_dir / "templates" / "migrations"
        for name, content in templates.items():
            template_file = templates_dir / name
            if not template_file.exists():
                template_file.write_text(content)
                
    def _load_migration_history(self):
        """Load migration history from disk"""
        history_file = self.migrations_dir / "migration_history.json"
        if history_file.exists():
            try:
                history_data = json.loads(history_file.read_text())
                self.migration_history = [
                    Migration(**migration_data)
                    for migration_data in history_data
                ]
                logging.info(f"Loaded {len(self.migration_history)} migrations from history")
            except Exception as e:
                logging.error(f"Error loading migration history: {str(e)}")
                self.migration_history = []
                
    def _save_migration_history(self):
        """Save migration history to disk"""
        history_file = self.migrations_dir / "migration_history.json"
        try:
            history_data = [
                {
                    "version": m.version,
                    "name": m.name,
                    "description": m.description,
                    "steps": [vars(step) for step in m.steps],
                    "created_at": m.created_at.isoformat(),
                    "applied": m.applied,
                    "checksum": m.checksum
                }
                for m in self.migration_history
            ]
            history_file.write_text(json.dumps(history_data, indent=2))
            logging.info(f"Saved {len(self.migration_history)} migrations to history")
        except Exception as e:
            logging.error(f"Error saving migration history: {str(e)}")
            
    def _generate_version(self) -> str:
        """Generate a unique version identifier"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{timestamp}"
        
    def _calculate_checksum(self, migration: Migration) -> str:
        """Calculate checksum for migration content"""
        content = f"{migration.version}{migration.name}"
        for step in migration.steps:
            content += f"{step.type.value}{step.name}{step.up_sql}{step.down_sql}"
        return hashlib.sha256(content.encode()).hexdigest()
        
    async def create_migration(self, 
        name: str,
        description: str,
        steps: List[MigrationStep],
        framework: str = 'sql'
    ) -> Tuple[Migration, Path]:
        """Create a new migration"""
        try:
            # Create migration object
            version = self._generate_version()
            migration = Migration(
                version=version,
                name=name,
                description=description,
                steps=steps
            )
            migration.checksum = self._calculate_checksum(migration)
            
            # Generate migration file
            if framework == 'sql':
                output_file = await self._generate_sql_migration(migration)
            elif framework == 'typeorm':
                output_file = await self._generate_typeorm_migration(migration)
            elif framework == 'alembic':
                output_file = await self._generate_alembic_migration(migration)
            else:
                raise ValueError(f"Unsupported framework: {framework}")
                
            # Update history
            self.migration_history.append(migration)
            self._save_migration_history()
            
            return migration, output_file
            
        except Exception as e:
            logging.error(f"Error creating migration: {str(e)}")
            raise
            
    async def _generate_sql_migration(self, migration: Migration) -> Path:
        """Generate SQL migration file"""
        try:
            template = self.template_env.get_template('migration.sql.jinja2')
            output_file = self.migrations_dir / f"{migration.version}_{migration.name}.sql"
            
            content = template.render(migration=migration)
            output_file.write_text(content)
            
            logging.info(f"Generated SQL migration: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating SQL migration: {str(e)}")
            raise
            
    async def _generate_typeorm_migration(self, migration: Migration) -> Path:
        """Generate TypeORM migration file"""
        try:
            template = self.template_env.get_template('migration.ts.jinja2')
            output_file = self.migrations_dir / f"{migration.version}_{migration.name}.ts"
            
            content = template.render(migration=migration)
            output_file.write_text(content)
            
            logging.info(f"Generated TypeORM migration: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating TypeORM migration: {str(e)}")
            raise
            
    async def _generate_alembic_migration(self, migration: Migration) -> Path:
        """Generate Alembic migration file"""
        try:
            template = self.template_env.get_template('migration.py.jinja2')
            output_file = self.migrations_dir / f"{migration.version}_{migration.name}.py"
            
            content = template.render(migration=migration)
            output_file.write_text(content)
            
            logging.info(f"Generated Alembic migration: {output_file}")
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating Alembic migration: {str(e)}")
            raise
            
    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations"""
        return [m for m in self.migration_history if not m.applied]
        
    def get_applied_migrations(self) -> List[Migration]:
        """Get list of applied migrations"""
        return [m for m in self.migration_history if m.applied]
        
    def mark_migration_applied(self, version: str):
        """Mark a migration as applied"""
        for migration in self.migration_history:
            if migration.version == version:
                migration.applied = True
                self._save_migration_history()
                logging.info(f"Marked migration {version} as applied")
                break 