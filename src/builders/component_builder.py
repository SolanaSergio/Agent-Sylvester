from pathlib import Path
from typing import Dict, Optional, List
from ..generators.component_generator import ComponentGenerator
from ..utils.types import ComponentInfo, Pattern
from ..scrapers.component_scraper import ComponentScraper
import logging
import json
import shutil

class ComponentBuilder:
    """Builds and manages React components with template support"""
    
    def __init__(self, components_dir: str):
        self.components_dir = Path(components_dir)
        self.components_dir.mkdir(parents=True, exist_ok=True)
        self.generator = ComponentGenerator(self.components_dir)
        self.scraper = ComponentScraper()
        
        # Initialize template directories
        self.template_dir = self.components_dir / "templates"
        self.template_dir.mkdir(exist_ok=True)
        
        # Cache for component patterns
        self.pattern_cache = {}
        
    async def create_component(self, component: ComponentInfo, patterns: Optional[List[Pattern]] = None) -> Optional[Path]:
        """Create a new React component with template support"""
        try:
            # Find best matching template
            template = await self._find_best_template(component, patterns)
            
            # Generate the component
            component_dir = await self.generator.generate_component(component, template)
            
            if component_dir:
                # Generate variants if needed
                if component.variants:
                    await self._generate_variants(component_dir, component)
                    
                # Generate tests
                await self._generate_tests(component_dir, component)
                
                # Generate documentation
                await self._generate_documentation(component_dir, component)
                
                # Cache component patterns
                self._cache_component_patterns(component, patterns)
                
                logging.info(f"Successfully created component: {component.name}")
                return component_dir
            else:
                logging.error(f"Failed to create component: {component.name}")
                return None
                
        except Exception as e:
            logging.error(f"Error creating component {component.name}: {str(e)}")
            return None
            
    async def update_component(self, component: ComponentInfo, patterns: Optional[List[Pattern]] = None) -> bool:
        """Update an existing component"""
        try:
            component_dir = self.components_dir / component.name
            
            if not component_dir.exists():
                logging.warning(f"Component {component.name} doesn't exist, creating new")
                return bool(await self.create_component(component, patterns))
                
            # Backup existing component
            backup_dir = self._create_backup(component_dir)
            
            try:
                # Update component with new template if available
                template = await self._find_best_template(component, patterns)
                success = await self.generator.generate_component(component, template)
                
                if success:
                    # Update variants
                    if component.variants:
                        await self._generate_variants(component_dir, component)
                        
                    # Update tests
                    await self._generate_tests(component_dir, component)
                    
                    # Update documentation
                    await self._generate_documentation(component_dir, component)
                    
                    # Update pattern cache
                    self._cache_component_patterns(component, patterns)
                    
                    # Remove backup if successful
                    shutil.rmtree(backup_dir)
                    return True
                else:
                    # Restore from backup
                    self._restore_from_backup(backup_dir, component_dir)
                    return False
                    
            except Exception as e:
                # Restore from backup on error
                self._restore_from_backup(backup_dir, component_dir)
                raise
                
        except Exception as e:
            logging.error(f"Error updating component {component.name}: {str(e)}")
            return False
            
    async def _find_best_template(self, component: ComponentInfo, patterns: Optional[List[Pattern]] = None) -> Optional[Dict]:
        """Find the best matching template for a component"""
        try:
            # Check cache first
            cache_key = f"{component.name}:{component.structure}"
            if cache_key in self.pattern_cache:
                return self.pattern_cache[cache_key]
                
            # Load available templates
            templates = await self._load_templates()
            
            if not templates:
                return None
                
            # Score each template
            template_scores = []
            for template in templates:
                score = self._calculate_template_score(template, component, patterns)
                template_scores.append((score, template))
                
            # Return best matching template
            if template_scores:
                best_template = max(template_scores, key=lambda x: x[0])[1]
                return best_template
                
            return None
            
        except Exception as e:
            logging.error(f"Error finding template for {component.name}: {str(e)}")
            return None
            
    async def _generate_variants(self, component_dir: Path, component: ComponentInfo):
        """Generate component variants"""
        try:
            variants_dir = component_dir / "variants"
            variants_dir.mkdir(exist_ok=True)
            
            for variant in component.variants:
                await self.generator.generate_variant(variants_dir, component, variant)
                
        except Exception as e:
            logging.error(f"Error generating variants for {component.name}: {str(e)}")
            
    async def _generate_tests(self, component_dir: Path, component: ComponentInfo):
        """Generate component tests"""
        try:
            tests_dir = component_dir / "__tests__"
            tests_dir.mkdir(exist_ok=True)
            
            # Generate unit tests
            await self.generator.generate_unit_tests(tests_dir, component)
            
            # Generate integration tests if component has dependencies
            if component.dependencies:
                await self.generator.generate_integration_tests(tests_dir, component)
                
        except Exception as e:
            logging.error(f"Error generating tests for {component.name}: {str(e)}")
            
    async def _generate_documentation(self, component_dir: Path, component: ComponentInfo):
        """Generate component documentation"""
        try:
            docs_dir = component_dir / "docs"
            docs_dir.mkdir(exist_ok=True)
            
            # Generate README
            await self.generator.generate_readme(docs_dir, component)
            
            # Generate Storybook stories
            await self.generator.generate_stories(docs_dir, component)
            
            # Generate API documentation
            await self.generator.generate_api_docs(docs_dir, component)
            
        except Exception as e:
            logging.error(f"Error generating documentation for {component.name}: {str(e)}")
            
    def _create_backup(self, component_dir: Path) -> Path:
        """Create a backup of an existing component"""
        backup_dir = component_dir.parent / f"{component_dir.name}_backup"
        shutil.copytree(component_dir, backup_dir)
        return backup_dir
        
    def _restore_from_backup(self, backup_dir: Path, component_dir: Path):
        """Restore component from backup"""
        shutil.rmtree(component_dir)
        shutil.move(backup_dir, component_dir)
        
    def _cache_component_patterns(self, component: ComponentInfo, patterns: Optional[List[Pattern]]):
        """Cache component patterns for future use"""
        if patterns:
            cache_key = f"{component.name}:{component.structure}"
            self.pattern_cache[cache_key] = patterns
            
    async def _load_templates(self) -> List[Dict]:
        """Load available component templates"""
        try:
            templates = []
            for template_file in self.template_dir.glob("*.json"):
                with open(template_file) as f:
                    template = json.load(f)
                    templates.append(template)
            return templates
        except Exception as e:
            logging.error(f"Error loading templates: {str(e)}")
            return []
            
    def _calculate_template_score(self, template: Dict, component: ComponentInfo, patterns: Optional[List[Pattern]]) -> float:
        """Calculate how well a template matches a component"""
        score = 0.0
        
        # Match structure
        if template.get('structure') == component.structure:
            score += 1.0
            
        # Match patterns
        if patterns:
            template_patterns = set(template.get('patterns', []))
            component_patterns = set(p.name for p in patterns)
            pattern_match = len(template_patterns & component_patterns) / len(template_patterns | component_patterns)
            score += pattern_match
            
        # Match dependencies
        if component.dependencies:
            template_deps = set(template.get('dependencies', []))
            component_deps = set(component.dependencies)
            dep_match = len(template_deps & component_deps) / len(template_deps | component_deps)
            score += dep_match
            
        return score 