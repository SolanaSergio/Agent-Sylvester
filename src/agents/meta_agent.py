from typing import Dict, List, Optional
from pathlib import Path
import asyncio
import json
import re
import logging
from datetime import datetime

from ..analyzers.requirement_analyzer import RequirementAnalyzer
from ..analyzers.pattern_analyzer import PatternAnalyzer
from ..scrapers.web_scraper import WebScraper
from ..scrapers.component_scraper import ComponentScraper
from ..builders.project_builder import ProjectBuilder
from ..builders.component_builder import ComponentBuilder
from ..utils.types import AgentStatus, ComponentInfo
from ..utils.project_structure import ProjectStructure
from ..managers.ui_manager import UIManager
from ..managers.config_manager import ConfigManager
from ..managers.dependency_manager import DependencyManager
from ..managers.api_manager import APIManager
from ..managers.db_manager import DatabaseManager
from .progress_tracker import ProgressTracker
from ..utils.system_checker import SystemChecker
from ..managers.template_manager import TemplateManager
from ..managers.tool_manager import ToolManager

class MetaAgent:
    """Core agent that orchestrates website analysis and building."""
    
    def __init__(self, goal: str):
        self.goal = goal
        self.progress = ProgressTracker()
        self.ui = UIManager()
        self.project_structure = ProjectStructure(".")
        
        # State management
        self.state = {
            'initialized': False,
            'current_task': None,
            'requirements': None,
            'components': [],
            'errors': [],
            'warnings': []
        }
        
        # Initialize analyzers
        self.requirement_analyzer = RequirementAnalyzer()
        self.pattern_analyzer = PatternAnalyzer()
        
        # Initialize scrapers
        self.web_scraper = WebScraper()
        self.component_scraper = ComponentScraper()
        
        # Initialize builders with workspace
        self.project_builder = ProjectBuilder("./projects")
        self.component_builder = ComponentBuilder("./components")
        
        # System checks
        self.system_checker = SystemChecker()
        
        # Initialize managers (will be fully setup during project creation)
        self.config_manager = None
        self.dependency_manager = None
        self.api_manager = None
        self.db_manager = None
        self.template_manager = None
        self.tool_manager = None
        
    async def initialize(self):
        """Initialize the agent and perform system checks"""
        try:
            # Check system requirements
            await self.system_checker.check_requirements()
            
            # Create necessary directories
            self.project_structure.create_base_structure()
            
            # Initialize managers
            self.config_manager = ConfigManager(self.project_structure.root)
            self.dependency_manager = DependencyManager(self.project_structure.root)
            self.api_manager = APIManager(self.project_structure.root)
            self.db_manager = DatabaseManager(self.project_structure.root)
            self.template_manager = TemplateManager(self.project_structure.root)
            self.tool_manager = ToolManager(self.project_structure.root)
            
            self.state['initialized'] = True
            logging.info("Agent initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize agent: {str(e)}")
            self.state['errors'].append(str(e))
            raise
            
    async def process_user_input(self, user_input: str):
        """Process user input and orchestrate the response"""
        try:
            self.state['current_task'] = 'analyzing_requirements'
            
            # Analyze requirements
            requirements = self.requirement_analyzer.analyze_requirements(user_input)
            self.state['requirements'] = requirements
            
            # Validate and enhance requirements
            self._validate_requirements(requirements)
            
            # Setup project structure
            await self._setup_project(requirements)
            
            # Generate components
            await self._generate_components(requirements)
            
            # Setup infrastructure
            await self._setup_infrastructure(requirements)
            
            # Final checks and cleanup
            await self._perform_final_checks()
            
        except Exception as e:
            logging.error(f"Error processing user input: {str(e)}")
            self.state['errors'].append(str(e))
            raise
            
    async def _setup_project(self, requirements: Dict):
        """Setup the project based on requirements"""
        self.state['current_task'] = 'setting_up_project'
        
        try:
            # Initialize project structure
            await self.project_builder.create_project(requirements)
            
            # Setup configuration
            self.config_manager.setup_project_config(requirements)
            
            # Setup dependencies
            await self.dependency_manager.setup_dependencies(requirements)
            
            # Setup version control
            await self.project_builder.setup_version_control()
            
        except Exception as e:
            logging.error(f"Project setup failed: {str(e)}")
            self.state['errors'].append(str(e))
            raise
            
    async def _generate_components(self, requirements: Dict):
        """Generate required components"""
        self.state['current_task'] = 'generating_components'
        
        try:
            # Extract components from requirements
            components = requirements.get('components', [])
            
            # Generate each component
            for component in components:
                try:
                    component_info = await self.component_builder.create_component(component, requirements)
                    self.state['components'].append(component_info)
                except Exception as e:
                    logging.warning(f"Failed to generate component {component}: {str(e)}")
                    self.state['warnings'].append(f"Component generation warning: {str(e)}")
                    
        except Exception as e:
            logging.error(f"Component generation failed: {str(e)}")
            self.state['errors'].append(str(e))
            raise
            
    async def _setup_infrastructure(self, requirements: Dict):
        """Setup project infrastructure"""
        self.state['current_task'] = 'setting_up_infrastructure'
        
        try:
            # Setup API layer if needed
            if 'api' in requirements.get('features', []):
                await self.api_manager.setup_api_layer(requirements)
                
            # Setup database if needed
            if 'database' in requirements.get('features', []):
                await self.db_manager.setup_database(requirements)
                
            # Setup authentication if needed
            if 'authentication' in requirements.get('features', []):
                await self._setup_authentication(requirements)
                
        except Exception as e:
            logging.error(f"Infrastructure setup failed: {str(e)}")
            self.state['errors'].append(str(e))
            raise
            
    def _validate_requirements(self, requirements: Dict):
        """Validate and enhance requirements"""
        # Check for conflicting requirements
        if 'static-site' in requirements['project_type'] and 'real-time' in requirements.get('features', []):
            self.state['warnings'].append("Static sites may not fully support real-time features")
            
        # Ensure necessary security features
        if 'payments' in requirements.get('features', []):
            if 'authentication' not in requirements.get('features', []):
                requirements['features'].append('authentication')
                self.state['warnings'].append("Added authentication requirement for payment features")
                
        # Validate technical requirements
        if requirements.get('ai_integration', {}).get('openai') and 'API_KEY' not in requirements.get('deployment', {}):
            self.state['warnings'].append("OpenAI integration requires API key configuration")
            
    async def _setup_authentication(self, requirements: Dict):
        """Setup authentication system"""
        auth_type = requirements.get('security', {}).get('authentication_type', 'jwt')
        
        if auth_type == 'jwt':
            await self._setup_jwt_auth()
        elif auth_type == 'oauth':
            await self._setup_oauth()
        else:
            await self._setup_default_auth()
            
    async def _perform_final_checks(self):
        """Perform final checks and validations"""
        try:
            # Check for security vulnerabilities
            security_issues = await self.system_checker.check_security()
            if security_issues:
                self.state['warnings'].extend(security_issues)
                
            # Check for performance issues
            performance_issues = await self.system_checker.check_performance()
            if performance_issues:
                self.state['warnings'].extend(performance_issues)
                
            # Validate project structure
            structure_issues = self.project_structure.validate()
            if structure_issues:
                self.state['warnings'].extend(structure_issues)
                
        except Exception as e:
            logging.error(f"Final checks failed: {str(e)}")
            self.state['errors'].append(str(e))
            
    async def cleanup(self):
        """Cleanup resources and perform final tasks"""
        try:
            # Cleanup temporary files
            await self.project_builder.cleanup()
            
            # Save project state
            self._save_state()
            
            # Generate documentation
            await self._generate_documentation()
            
        except Exception as e:
            logging.error(f"Cleanup failed: {str(e)}")
            self.state['errors'].append(str(e))
            
    def _save_state(self):
        """Save the current state for recovery"""
        try:
            state_file = self.project_structure.root / ".agent-state.json"
            with open(state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save state: {str(e)}")
            
    async def _generate_documentation(self):
        """Generate project documentation"""
        try:
            docs_dir = self.project_structure.root / "docs"
            docs_dir.mkdir(exist_ok=True)
            
            # Generate README
            readme_content = self.template_manager.generate_readme(
                self.state['requirements'],
                self.state['components']
            )
            with open(self.project_structure.root / "README.md", 'w') as f:
                f.write(readme_content)
                
            # Generate API documentation if needed
            if 'api' in self.state['requirements'].get('features', []):
                await self.api_manager.generate_documentation()
                
        except Exception as e:
            logging.error(f"Documentation generation failed: {str(e)}")
            self.state['errors'].append(str(e)) 