import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from src.utils.types import ProjectConfig, ProjectStatus, ComponentStatus, DependencyInfo
# Import managers only when needed in methods to avoid circular imports
import logging
from src.agents.progress_tracker import ProgressTracker
import datetime
from src.builders.project_builder import ProjectBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetaAgent:
    def __init__(self):
        self._initialize_managers()
        self.current_project: Optional[ProjectConfig] = None
        self.project_path: Optional[Path] = None
        self.agent_root = Path(__file__).parent.parent.parent  # Points to Auto Agent root
        self.progress_tracker: Optional[ProgressTracker] = None  # Initialize as None
        
        # Define supported frameworks and their requirements
        self.supported_frameworks = {
            "Next.js": {
                "features": ["routing", "server-side-rendering"],
                "dependencies": ["next", "react", "react-dom"],
                "styles": ["tailwind", "styled-components", "sass", "css-modules"]
            },
            "React": {
                "features": ["client-side-routing"],
                "dependencies": ["react", "react-dom", "react-router-dom"],
                "styles": ["styled-components", "tailwind", "sass", "css-modules"]
            },
            "Node": {
                "features": ["api", "routing"],
                "dependencies": ["express", "cors", "helmet"],
                "database": {"needed": True, "type": "mongodb"}
            }
        }

    def _initialize_managers(self):
        # Lazy imports to avoid circular dependencies
        from src.managers.dependency_manager import DependencyManager
        from src.generators.documentation_generator import DocumentationGenerator
        from src.analyzers.requirement_analyzer import RequirementAnalyzer
        from src.analyzers.pattern_analyzer import PatternAnalyzer
        from src.builders.project_builder import ProjectBuilder
        from src.scrapers.web_scraper import WebScraper

        self.dependency_manager = DependencyManager()
        self.documentation_generator = DocumentationGenerator()
        self.requirement_analyzer = RequirementAnalyzer()
        self.pattern_analyzer = PatternAnalyzer()
        self.project_builder = ProjectBuilder()
        self.web_scraper = WebScraper()

    async def _check_permissions(self) -> None:
        """Check if we have necessary permissions to create and modify the project"""
        try:
            if not self.project_path:
                raise ValueError("Project path not set")

            # Check if parent directory exists
            parent_dir = self.project_path.parent
            if not parent_dir.exists():
                raise ValueError(f"Parent directory does not exist: {parent_dir}")

            # Try to create a temporary file to test write permissions
            test_file = parent_dir / f".test_{self.project_path.name}"
            try:
                test_file.touch()
                test_file.unlink()  # Remove the test file
                logger.info("Write permission test passed")
            except (PermissionError, OSError) as e:
                logger.error(f"Permission test failed: {str(e)}")
                raise ValueError(f"No write permission in directory: {parent_dir}\nError: {str(e)}")

        except Exception as e:
            logger.error(f"Permission check failed: {str(e)}")
            raise ValueError(f"Permission check failed: {str(e)}")

    async def _create_project_directory(self) -> None:
        """Create or verify project directory"""
        try:
            # First, try to create the directory
            try:
                self.project_path.mkdir(parents=True)
                logger.info("Project directory created successfully")
            except FileExistsError:
                # If directory exists, check if it's empty or only contains our test files
                contents = list(self.project_path.iterdir())
                # Filter out hidden files and our test files
                real_contents = [f for f in contents if not f.name.startswith('.')]
                
                if real_contents:
                    logger.info(f"Directory exists with contents: {[f.name for f in real_contents]}")
                    raise ValueError(f"Directory already exists and is not empty: {self.project_path}")
                else:
                    logger.info("Directory exists but is empty or contains only temporary files, proceeding")

        except Exception as e:
            logger.error(f"Directory creation failed: {str(e)}")
            raise ValueError(f"Failed to create project directory: {str(e)}")

    async def initialize_project(self, config: ProjectConfig) -> None:
        """Initialize a new project"""
        try:
            # Initialize progress tracker if not already initialized
            if not self.progress_tracker:
                self.progress_tracker = ProgressTracker(self.project_path)
                
            await self.progress_tracker.update_status("Starting project initialization")
            
            # Set up project path
            self.project_path = Path(config.project_location) / config.name
            self.current_project = config  # Store current project config
            
            # Check permissions
            await self.progress_tracker.update_status("Checking permissions...")
            await self._check_permissions()
            
            # Create project directory
            await self.progress_tracker.update_status("Creating project directory...")
            await self._create_project_directory()
            
            # Set up project structure
            await self.progress_tracker.update_status("Setting up project structure...")
            await self.progress_tracker.update_status("Creating initial structure")
            
            # Determine framework and features
            if not config.framework:
                if config.project_type == "backend":
                    config.framework = "Node"
                else:
                    config.framework = "Next.js"
            logger.info(f"Using framework: {config.framework}")
            
            # Analyze requirements with enhanced feature detection
            await self.progress_tracker.update_status("Analyzing project requirements")
            requirements = await self.requirement_analyzer.analyze_project_requirements(config, self.project_path)
            
            # Use existing project builder instance
            await self.project_builder.build_project(config, requirements)
            
            # Set up dependencies
            await self.progress_tracker.update_status("Setting up dependencies")
            await self.dependency_manager.setup_project_dependencies(config, self.project_path)
            
            await self.progress_tracker.update_status("Project initialization complete")
            logger.info("Project initialization completed successfully")
            
        except Exception as e:
            await self.progress_tracker.update_status("Project initialization failed")
            raise Exception(f"Project initialization failed: {str(e)}")

    async def _extract_project_config(self) -> ProjectConfig:
        """Extract project configuration from an existing project"""
        try:
            # Check for package.json
            package_json = self.project_path / "package.json"
            if package_json.exists():
                with open(package_json) as f:
                    import json
                    data = json.load(f)
                    
                    # Determine project type and framework from dependencies
                    dependencies = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    
                    if "next" in dependencies:
                        project_type = "fullstack"
                        framework = "Next.js"
                    elif "react" in dependencies and not "next" in dependencies:
                        project_type = "frontend"
                        framework = "React"
                    elif "express" in dependencies:
                        project_type = "backend"
                        framework = "Node"
                    else:
                        project_type = "unknown"
                        framework = None
                    
                    # Determine styling from dependencies
                    styling = None
                    if "tailwindcss" in dependencies:
                        styling = "tailwind"
                    elif "styled-components" in dependencies:
                        styling = "styled-components"
                    elif "sass" in dependencies:
                        styling = "sass"
                    
                    # Extract features based on dependencies
                    features = []
                    if "next-auth" in dependencies or "@auth0/nextjs-auth0" in dependencies:
                        features.append("auth")
                    if "mongoose" in dependencies or "prisma" in dependencies:
                        features.append("database")
                    if "react-query" in dependencies or "swr" in dependencies:
                        features.append("api")
                    if "chart.js" in dependencies or "@nivo/core" in dependencies:
                        features.append("charts")
                    
                    return ProjectConfig(
                        name=self.project_path.name,
                        project_type=project_type,
                        framework=framework,
                        features=features,
                        styling=styling,
                        project_location=str(self.project_path.parent),
                        description=data.get("description", ""),
                        version=data.get("version", "0.1.0"),
                        author=data.get("author", None),
                        license=data.get("license", "MIT")
                    )
            
            # If no package.json, try to infer from directory structure
            if (self.project_path / "pages").exists() or (self.project_path / "app").exists():
                return ProjectConfig(
                    name=self.project_path.name,
                    project_type="fullstack",
                    framework="Next.js",
                    features=[],
                    styling=None,
                    project_location=str(self.project_path.parent)
                )
            
            raise ValueError("Could not determine project configuration")
            
        except Exception as e:
            logger.error(f"Failed to extract project configuration: {str(e)}")
            raise ValueError(f"Failed to extract project configuration: {str(e)}")

    def _validate_framework_requirements(self, framework: str, requirements: dict) -> None:
        """Validate that framework requirements are supported"""
        if framework not in self.supported_frameworks:
            raise ValueError(f"Unsupported framework: {framework}")
            
        framework_reqs = self.supported_frameworks[framework]
        
        # Validate styling
        if "styles" in requirements and requirements["styles"]:
            if not any(style in framework_reqs["styles"] for style in requirements["styles"]):
                raise ValueError(f"Unsupported styling for {framework}: {requirements['styles']}")
        
        # Validate features
        if "features" in requirements and requirements["features"]:
            if not all(feature in framework_reqs["features"] for feature in requirements["features"]):
                raise ValueError(f"Some features are not supported by {framework}")

    async def import_project(self, project_path: str) -> None:
        """Import and analyze an existing project"""
        try:
            self.project_path = Path(project_path)
            if not self.project_path.exists():
                raise FileNotFoundError(f"Project path does not exist: {project_path}")
            
            # Initialize progress tracker
            self.progress_tracker = ProgressTracker(self.project_path)
            await self.progress_tracker.update_status("Starting project import")
            
            try:
                # Analyze project structure
                await self.progress_tracker.update_status("Analyzing project structure")
                structure = await self.pattern_analyzer.analyze_project_structure(self.project_path)
                
                # Analyze patterns
                await self.progress_tracker.update_status("Analyzing patterns")
                patterns = await self.pattern_analyzer.analyze_patterns(self.project_path)
                
                # Extract project configuration
                await self.progress_tracker.update_status("Extracting project configuration")
                config = await self._extract_project_config()
                self.current_project = config
                
                # Analyze requirements
                await self.progress_tracker.update_status("Analyzing requirements")
                requirements = await self.requirement_analyzer.analyze_project_requirements(config, self.project_path)
                
                # Validate framework requirements
                if config.framework:
                    self._validate_framework_requirements(config.framework, requirements)
                
                await self.progress_tracker.update_status("Project import complete")
                
            except Exception as e:
                await self.progress_tracker.update_status("Project import failed", {"error": str(e)})
                raise
                
        except Exception as e:
            if self.progress_tracker:
                await self.progress_tracker.update_status("Project import failed", {"error": str(e)})
            raise ValueError(f"Project import failed: {str(e)}")

    async def update_project(self) -> None:
        """Update the current project"""
        if not self.current_project or not self.project_path:
            raise ValueError("No project is currently active")
            
        if not self.progress_tracker:
            self.progress_tracker = ProgressTracker(self.project_path)
            
        self.progress_tracker.update_status("Starting project update")
        
        try:
            # Analyze current state
            self.progress_tracker.update_status("Analyzing current state")
            current_state = await self.requirement_analyzer.analyze_current_state()
            
            # Update dependencies
            self.progress_tracker.update_status("Updating dependencies")
            await self.dependency_manager.update_dependencies()
            
            # Update components
            self.progress_tracker.update_status("Updating components")
            await self.project_builder.update_components()
            
            # Update documentation
            self.progress_tracker.update_status("Updating documentation")
            await self.documentation_generator.update_documentation()
            
            self.progress_tracker.update_status("Project update complete")
            
        except Exception as e:
            self.progress_tracker.update_status("Project update failed", {"error": str(e)})
            raise

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

    async def process_user_input(self, description: str) -> None:
        """Process user input for project modifications"""
        if not self.current_project or not self.project_path:
            raise ValueError("No active project")

        if not self.progress_tracker:
            self.progress_tracker = ProgressTracker(self.project_path)

        await self.progress_tracker.update_status(f"Processing request: {description}")

        try:
            # Analyze the request
            await self.progress_tracker.update_status("Analyzing request")
            requirements = await self.requirement_analyzer.analyze_user_request(description)
            
            # Handle code changes first
            if requirements.get("code_changes"):
                await self.progress_tracker.update_status("Processing code changes")
                code_changes = requirements["code_changes"]
                
                # Handle new files
                for file_info in code_changes.get("files_to_create", []):
                    await self.progress_tracker.update_status(f"Creating file: {file_info['name']}")
                    file_path = file_info["path"] or self._determine_file_path(file_info["name"])
                    await self.project_builder.create_file(file_path, file_info["description"])
                
                # Handle file modifications
                for file_info in code_changes.get("files_to_modify", []):
                    await self.progress_tracker.update_status(f"Modifying file: {file_info['name']}")
                    await self.project_builder.modify_file(file_info["name"], file_info["element"], file_info["description"])
                
                # Handle code block generation
                for block_info in code_changes.get("code_blocks", []):
                    await self.progress_tracker.update_status(f"Generating {block_info['type']}: {block_info['name']}")
                    await self.project_builder.generate_code_block(block_info)

            # Handle component updates
            if requirements.get("components"):
                await self.progress_tracker.update_status("Updating components")
                for component in requirements["components"]:
                    await self.progress_tracker.update_status(f"Creating component: {component['name']}")
                    await self.project_builder.create_component(component)

            # Handle dependency updates
            if requirements.get("dependencies"):
                await self.progress_tracker.update_status("Updating dependencies")
                await self.dependency_manager.update_dependencies(requirements["dependencies"])

            # Handle API endpoints
            if requirements.get("api_endpoints"):
                await self.progress_tracker.update_status("Creating API endpoints")
                for endpoint in requirements["api_endpoints"]:
                    await self.project_builder.create_api_endpoint(endpoint)

            # Handle database changes
            if requirements.get("database", {}).get("needed"):
                await self.progress_tracker.update_status("Setting up database")
                db_info = requirements["database"]
                await self.project_builder.setup_database(db_info)

            await self.progress_tracker.update_status("Request processed successfully")

        except Exception as e:
            error_msg = str(e)
            await self.progress_tracker.update_status("Failed to process request", {"error": error_msg})
            raise Exception(f"Failed to process request: {error_msg}")

    def _determine_file_path(self, filename: str) -> str:
        """Determine the appropriate path for a new file based on its name and type"""
        if filename.endswith(('.component.tsx', '.component.jsx')):
            return f"src/components/{filename}"
        elif filename.endswith(('.page.tsx', '.page.jsx')):
            return f"src/pages/{filename}"
        elif filename.endswith(('.api.ts', '.api.js')):
            return f"src/api/{filename}"
        elif filename.endswith(('.util.ts', '.util.js')):
            return f"src/utils/{filename}"
        elif filename.endswith(('.hook.ts', '.hook.js')):
            return f"src/hooks/{filename}"
        elif filename.endswith(('.context.tsx', '.context.jsx')):
            return f"src/contexts/{filename}"
        elif filename.endswith(('.model.ts', '.model.js')):
            return f"src/models/{filename}"
        elif filename.endswith(('.test.ts', '.test.js')):
            return f"tests/{filename}"
        else:
            return f"src/{filename}"

    async def cleanup(self) -> None:
        """Clean up any resources or temporary files"""
        try:
            if self.project_path and self.project_path.exists():
                # Clean up any temporary files
                temp_files = list(self.project_path.glob(".test_*"))
                for temp_file in temp_files:
                    try:
                        temp_file.unlink()
                    except Exception as e:
                        logger.warning(f"Failed to clean up temporary file {temp_file}: {str(e)}")
                        
            if self.progress_tracker:
                await self.progress_tracker.update_status("Cleanup complete")
                
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
            if self.progress_tracker:
                await self.progress_tracker.update_status("Cleanup failed", {"error": str(e)}) 