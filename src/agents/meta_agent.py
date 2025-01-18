import asyncio
from pathlib import Path
from typing import List, Optional
from src.utils.types import ProjectConfig, ProjectStatus, ComponentStatus, DependencyInfo
from src.managers.dependency_manager import DependencyManager
from src.generators.documentation_generator import DocumentationGenerator
from src.analyzers.requirement_analyzer import RequirementAnalyzer
from src.analyzers.pattern_analyzer import PatternAnalyzer
from src.builders.project_builder import ProjectBuilder
from src.agents.progress_tracker import ProgressTracker
from src.scrapers.web_scraper import WebScraper

class MetaAgent:
    def __init__(self):
        self.dependency_manager = DependencyManager()
        self.documentation_generator = DocumentationGenerator()
        self.requirement_analyzer = RequirementAnalyzer()
        self.pattern_analyzer = PatternAnalyzer()
        self.project_builder = ProjectBuilder()
        self.progress_tracker = ProgressTracker()
        self.web_scraper = WebScraper()
        self.current_project: Optional[ProjectConfig] = None
        self.project_path: Optional[Path] = None

    async def initialize_project(self, config: ProjectConfig) -> None:
        """Initialize a new project with the given configuration"""
        self.current_project = config
        self.project_path = Path(config.name)
        
        # Analyze requirements based on config
        requirements = await self.requirement_analyzer.analyze_project_requirements(config)
        
        # Initialize project structure
        await self.project_builder.initialize_project(config, requirements)
        
        # Set up dependencies
        await self.dependency_manager.setup_project_dependencies(config)
        
        # Generate project structure
        await self.project_builder.generate_structure()
        
        # Generate initial components
        await self.project_builder.generate_components()
        
        # Generate documentation
        await self.documentation_generator.generate_project_documentation(config)
        
        self.progress_tracker.update_status("Project initialized")

    async def import_project(self, project_path: str) -> None:
        """Import and analyze an existing project"""
        self.project_path = Path(project_path)
        if not self.project_path.exists():
            raise FileNotFoundError(f"Project path does not exist: {project_path}")
        
        # Analyze project structure
        structure = await self.pattern_analyzer.analyze_project_structure(self.project_path)
        
        # Analyze patterns
        patterns = await self.pattern_analyzer.analyze_patterns()
        
        # Extract project configuration
        config = await self._extract_project_config()
        self.current_project = config
        
        # Analyze requirements
        requirements = await self.requirement_analyzer.analyze_project_requirements(config)
        
        # Update project status
        self.progress_tracker.update_status("Project imported")

    async def update_project(self) -> None:
        """Update the current project"""
        if not self.current_project or not self.project_path:
            raise ValueError("No project is currently active")
        
        # Analyze current state
        current_state = await self.requirement_analyzer.analyze_current_state()
        
        # Update dependencies
        await self.dependency_manager.update_dependencies()
        
        # Update components
        await self.project_builder.update_components()
        
        # Update documentation
        await self.documentation_generator.update_documentation()
        
        self.progress_tracker.update_status("Project updated")

    async def _extract_project_config(self) -> ProjectConfig:
        """Extract configuration from existing project"""
        try:
            # Try to read package.json
            package_json = self.project_path / "package.json"
            if package_json.exists():
                import json
                with open(package_json) as f:
                    data = json.load(f)
                    
                # Determine framework from dependencies
                framework = "Next.js" if "next" in data.get("dependencies", {}) else "React"
                if "vue" in data.get("dependencies", {}):
                    framework = "Vue"
                elif "@angular/core" in data.get("dependencies", {}):
                    framework = "Angular"
                
                return ProjectConfig(
                    name=data.get("name", self.project_path.name),
                    description=data.get("description", ""),
                    framework=framework,
                    features=[]  # Will be determined by analysis
                )
            else:
                # Fallback to directory name and basic config
                return ProjectConfig(
                    name=self.project_path.name,
                    description="",
                    framework="React",  # Default to React
                    features=[]
                )
        except Exception as e:
            raise Exception(f"Failed to extract project configuration: {str(e)}")

    async def generate_project_structure(self) -> None:
        """Generate the project's directory structure and base files"""
        if not self.current_project:
            raise ValueError("No project initialized")
            
        await self.project_builder.generate_structure()
        self.progress_tracker.update_status("Project structure generated")

    async def setup_dependencies(self) -> None:
        """Set up project dependencies based on requirements"""
        if not self.current_project:
            raise ValueError("No project initialized")
            
        await self.dependency_manager.setup_project_dependencies(self.current_project)
        self.progress_tracker.update_status("Dependencies set up")

    async def generate_components(self) -> None:
        """Generate initial project components"""
        if not self.current_project:
            raise ValueError("No project initialized")
            
        await self.project_builder.generate_components()
        self.progress_tracker.update_status("Components generated")

    async def generate_documentation(self) -> None:
        """Generate project documentation"""
        if not self.current_project:
            raise ValueError("No project initialized")
            
        await self.documentation_generator.generate_project_documentation(self.current_project)
        self.progress_tracker.update_status("Documentation generated")

    async def analyze_project(self) -> ProjectStatus:
        """Analyze current project status"""
        if not self.current_project:
            raise ValueError("No project initialized")
            
        patterns = await self.pattern_analyzer.analyze_patterns()
        requirements = await self.requirement_analyzer.analyze_current_state()
        
        return ProjectStatus(
            components=await self._get_component_status(),
            dependencies=await self._get_dependency_status(),
            issues=await self._get_project_issues()
        )

    async def update_components(self) -> None:
        """Update project components based on current state"""
        if not self.current_project:
            raise ValueError("No project initialized")
            
        await self.project_builder.update_components()
        self.progress_tracker.update_status("Components updated")

    async def update_dependencies(self) -> None:
        """Update project dependencies"""
        if not self.current_project:
            raise ValueError("No project initialized")
            
        await self.dependency_manager.update_dependencies()
        self.progress_tracker.update_status("Dependencies updated")

    async def update_documentation(self) -> None:
        """Update project documentation"""
        if not self.current_project:
            raise ValueError("No project initialized")
            
        await self.documentation_generator.update_documentation()
        self.progress_tracker.update_status("Documentation updated")

    async def get_project_status(self) -> ProjectStatus:
        """Get detailed project status"""
        if not self.current_project:
            raise ValueError("No project initialized")
            
        return ProjectStatus(
            components=await self._get_component_status(),
            dependencies=await self._get_dependency_status(),
            issues=await self._get_project_issues()
        )

    async def _get_component_status(self) -> List[ComponentStatus]:
        """Get status of all project components"""
        if not self.project_path:
            return []
            
        components = []
        components_dir = self.project_path / "src/components"
        
        if components_dir.exists():
            for component_file in components_dir.glob("**/*.{tsx,jsx}"):
                # Analyze component status
                with open(component_file) as f:
                    content = f.read()
                    status = "Ready" if "export" in content else "Incomplete"
                components.append(ComponentStatus(
                    name=component_file.stem,
                    status=status
                ))
        
        return components

    async def _get_dependency_status(self) -> List[DependencyInfo]:
        """Get status of all project dependencies"""
        return await self.dependency_manager.get_dependency_status()

    async def _get_project_issues(self) -> List[str]:
        """Get list of current project issues"""
        if not self.project_path:
            return []
            
        issues = []
        
        # Check for common issues
        if not (self.project_path / "tsconfig.json").exists():
            issues.append("Missing TypeScript configuration")
        
        if not (self.project_path / "package.json").exists():
            issues.append("Missing package.json")
            
        if not (self.project_path / "src/components").exists():
            issues.append("Missing components directory")
            
        if not (self.project_path / "tests").exists():
            issues.append("Missing tests directory")
            
        # Check for empty directories
        for dir_name in ["src", "public", "tests"]:
            dir_path = self.project_path / dir_name
            if dir_path.exists() and not any(dir_path.iterdir()):
                issues.append(f"Empty {dir_name} directory")
                
        return issues 