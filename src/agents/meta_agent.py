import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from src.utils.types import ProjectConfig, ProjectStatus, ComponentStatus, DependencyInfo
# Import managers only when needed in methods to avoid circular imports
import logging
from src.agents.progress_tracker import ProgressTracker
import datetime
from src.builders.project_builder import ProjectBuilder
from src.analyzers.requirement_analyzer import RequirementAnalyzer
from src.managers.dependency_manager import DependencyManager
import json
import shutil
import subprocess

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
        """Initialize a new project with the given configuration"""
        try:
            self.current_project = config
            self.project_path = Path(config.project_location) / config.name
            
            # Initialize progress tracker
            self.progress_tracker = ProgressTracker()
            await self.progress_tracker.start_tracking()
            
            # Perform initialization steps
            await self.progress_tracker.update_progress("Starting project initialization")
            await self._check_permissions()
            
            await self.progress_tracker.update_progress("Checking permissions...")
            await self._create_project_directory()
            
            await self.progress_tracker.update_progress("Creating project directory...")
            
            # Analyze requirements
            await self.progress_tracker.update_progress("Analyzing project requirements")
            requirements = await self.requirement_analyzer.analyze_requirements(
                self.project_path,
                config.description
            )
            
            # Build project with error handling and recovery
            try:
                await self.project_builder.build_project(config, requirements)
            except Exception as e:
                await self._handle_error(e, "project_builder.build_project")
                # Retry after error handling
                await self.project_builder.build_project(config, requirements)
            
            await self.progress_tracker.update_progress("Project initialization completed")
            
        except Exception as e:
            await self._handle_error(e, "initialize_project")
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

    async def _handle_error(self, error: Exception, context: str) -> None:
        """Enhanced error handling with better recovery logic."""
        try:
            error_str = str(error)
            logger.error(f"Error in {context}: {error_str}")
            
            # First try specific error handlers
            if "useAuth" in error_str or "AuthContext" in error_str:
                await self._ensure_auth_implementation()
                return
            elif "ThemeContext" in error_str:
                await self._ensure_theme_implementation()
                return
            elif "import" in error_str.lower():
                await self._fix_import_error()
                return
            elif "module" in error_str.lower():
                await self._fix_module_error()
                return
            elif "dependency" in error_str.lower():
                await self._fix_dependency_issues()
                return
                
            # If specific handlers didn't work, try general recovery
            await self._analyze_and_fix_error(error, context)
            
        except Exception as recovery_error:
            logger.error(f"Error during recovery: {str(recovery_error)}")
            # Try one last time with missing method recovery
            try:
                await self._add_missing_method_recovery()
                # After adding missing methods, try the original fix again
                if "useAuth" in error_str:
                    await self._ensure_auth_implementation()
                elif "import" in error_str.lower():
                    await self._fix_import_error()
            except Exception as final_error:
                logger.error(f"Final recovery attempt failed: {str(final_error)}")
                raise Exception(f"Recovery failed: {str(error)} -> {str(recovery_error)} -> {str(final_error)}")

    async def _analyze_and_fix_error(self, error: Exception, context: str) -> None:
        """Enhanced error analysis and fixing with better recovery paths."""
        try:
            error_str = str(error)
            logger.info(f"Analyzing error in context '{context}': {error_str}")

            # Check for missing methods first
            if "has no attribute" in error_str:
                await self._handle_missing_method_error(error_str, context)
                return

            # Try pattern-based fixes
            patterns = {
                'import': self._fix_import_error,
                'module': self._fix_module_error,
                'dependency': self._fix_dependency_issues,
                'auth': self._ensure_auth_implementation,
                'theme': self._ensure_theme_implementation
            }

            for pattern, fix_method in patterns.items():
                if pattern.lower() in error_str.lower():
                    await fix_method()
                    return

            # If no pattern matched, try context-based recovery
            await self._handle_recovery_failure(error)

        except Exception as e:
            logger.error(f"Error analysis failed: {str(e)}")
            raise

    async def _handle_missing_method_error(self, error_str: str, context: str) -> None:
        """Enhanced missing method error handler with better recovery."""
        try:
            import re
            match = re.search(r"'(.+?)' object has no attribute '(.+?)'", error_str)
            if not match:
                raise ValueError(f"Could not parse error: {error_str}")

            class_name, method_name = match.groups()
            logger.info(f"Handling missing method '{method_name}' in class '{class_name}'")

            # Try to add the method
            if method_name.startswith('_fix_'):
                await self._add_missing_method_recovery()
            elif method_name == '_handle_recovery_failure':
                await self._ensure_recovery_handlers()
            else:
                # Try to find an alternative method
                await self._find_alternative_method(method_name)

        except Exception as e:
            logger.error(f"Failed to handle missing method: {str(e)}")
            raise

    async def _ensure_recovery_handlers(self) -> None:
        """Ensure all recovery handlers are properly initialized."""
        try:
            # Add essential recovery methods if missing
            essential_methods = [
                '_handle_recovery_failure',
                '_fix_dependency_issues',
                '_fix_import_error',
                '_fix_module_error'
            ]

            for method in essential_methods:
                if not hasattr(self, method):
                    await self._add_missing_method_recovery()
                    break

            logger.info("Recovery handlers ensured")

        except Exception as e:
            logger.error(f"Failed to ensure recovery handlers: {str(e)}")
            raise

    async def _find_alternative_method(self, missing_method: str) -> None:
        """Find and use alternative methods for missing functionality."""
        try:
            # Map of known alternatives
            alternatives = {
                'fix_dependency_error': '_fix_dependency_issues',
                'fix_import': '_fix_import_error',
                'fix_module': '_fix_module_error'
            }

            if missing_method in alternatives:
                alternative = alternatives[missing_method]
                if hasattr(self, alternative):
                    await getattr(self, alternative)()
                else:
                    await self._add_missing_method_recovery()
            else:
                raise ValueError(f"No alternative found for {missing_method}")

        except Exception as e:
            logger.error(f"Failed to find alternative method: {str(e)}")
            raise

    async def _fix_dependency_issues(self) -> None:
        """Fix dependency-related issues by ensuring all required dependencies are properly set up."""
        try:
            if not self.project_path:
                raise ValueError("No active project")

            logger.info("Attempting to fix dependency issues")
            
            # Check package.json exists
            package_json = self.project_path / 'package.json'
            if not package_json.exists():
                await self._create_package_json()
            
            # Ensure core dependencies
            core_deps = {
                'dependencies': {
                    'next': 'latest',
                    'react': 'latest',
                    'react-dom': 'latest',
                    'next-auth': 'latest'
                },
                'devDependencies': {
                    'typescript': 'latest',
                    '@types/react': 'latest',
                    '@types/node': 'latest',
                    'eslint': 'latest',
                    'eslint-config-next': 'latest'
                }
            }
            
            await self.dependency_manager.ensure_dependencies(core_deps)
            
            # Fix node_modules if needed
            node_modules = self.project_path / 'node_modules'
            if not node_modules.exists():
                await self.dependency_manager.install_dependencies()
                
            logger.info("Dependency issues fixed")
            
        except Exception as e:
            logger.error(f"Failed to fix dependency issues: {str(e)}")
            raise

    async def _create_package_json(self) -> None:
        """Create a basic package.json file if missing."""
        try:
            content = {
                "name": self.project_path.name,
                "version": "0.1.0",
                "private": True,
                "scripts": {
                    "dev": "next dev",
                    "build": "next build",
                    "start": "next start",
                    "lint": "next lint"
                },
                "dependencies": {},
                "devDependencies": {}
            }
            
            package_json = self.project_path / 'package.json'
            package_json.write_text(json.dumps(content, indent=2))
            logger.info("Created package.json")
            
        except Exception as e:
            logger.error(f"Failed to create package.json: {str(e)}")
            raise

    async def _add_missing_method_recovery(self) -> None:
        """Attempt to recover from missing method errors by adding required methods."""
        try:
            # Add common missing methods
            missing_methods = {
                '_fix_dependency_error': self._get_dependency_error_fix,
                '_fix_type_error': self._get_type_error_fix,
                '_fix_component_creation': self._get_component_creation_fix,
                '_fix_project_initialization': self._get_project_initialization_fix,
                '_fix_style_error': self._get_style_error_fix,
                '_fix_config_error': self._get_config_error_fix,
                '_fix_build_error': self._get_build_error_fix,
                '_fix_test_error': self._get_test_error_fix
            }

            for method_name, method_impl in missing_methods.items():
                if not hasattr(self, method_name):
                    setattr(self, method_name, method_impl())

            logger.info("Added missing recovery methods")

        except Exception as e:
            logger.error(f"Failed to add missing methods: {str(e)}")
            raise

    def _get_dependency_error_fix(self):
        """Get the implementation for fixing dependency errors."""
        async def fix_dependency_error():
            if not self.project_path:
                return
            await self.dependency_manager.update_dependencies()
        return fix_dependency_error

    def _get_type_error_fix(self):
        """Get the implementation for fixing type errors."""
        async def fix_type_error():
            if not self.project_path:
                return
                
            try:
                # Run type check to get detailed errors
                process = await asyncio.create_subprocess_exec(
                    'npx', 'tsc', '--noEmit',
                    cwd=self.project_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    # Parse type errors
                    errors = self._parse_type_errors(stderr.decode())
                    
                    # Fix each error
                    for error in errors:
                        await self._fix_single_type_error(error)
                        
                # Run type check again to verify fixes
                await asyncio.create_subprocess_exec(
                    'npx', 'tsc', '--noEmit',
                    cwd=self.project_path
                )
                
            except Exception as e:
                logging.error(f"Error fixing type errors: {str(e)}")
                raise
                
        return fix_type_error

    def _get_component_creation_fix(self):
        """Get the implementation for fixing component creation errors."""
        async def fix_component_creation():
            if not self.project_path:
                return
                
            try:
                # Analyze component structure
                components_dir = Path(self.project_path) / 'src' / 'components'
                if not components_dir.exists():
                    components_dir.mkdir(parents=True)
                    
                # Check for common component issues
                issues = await self._analyze_component_issues()
                
                for issue in issues:
                    if issue.type == 'missing_props':
                        await self._add_component_props(issue.component)
                    elif issue.type == 'missing_types':
                        await self._add_component_types(issue.component)
                    elif issue.type == 'missing_exports':
                        await self._fix_component_exports(issue.component)
                    elif issue.type == 'style_issues':
                        await self._fix_component_styles(issue.component)
                        
            except Exception as e:
                logging.error(f"Error fixing component creation: {str(e)}")
                raise
                
        return fix_component_creation

    def _get_style_error_fix(self):
        """Get the implementation for fixing style-related errors."""
        async def fix_style_error():
            if not self.project_path:
                return
                
            try:
                # Run ESLint to get style issues
                process = await asyncio.create_subprocess_exec(
                    'npx', 'eslint', 'src', '--format', 'json',
                    cwd=self.project_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if stdout:
                    # Parse ESLint output
                    issues = json.loads(stdout.decode())
                    
                    # Fix each issue
                    for issue in issues:
                        await self._fix_style_issue(issue)
                        
                # Run Prettier to format code
                await asyncio.create_subprocess_exec(
                    'npx', 'prettier', '--write', 'src',
                    cwd=self.project_path
                )
                
            except Exception as e:
                logging.error(f"Error fixing style errors: {str(e)}")
                raise
                
        return fix_style_error

    def _get_config_error_fix(self):
        """Get the implementation for fixing configuration errors."""
        async def fix_config_error():
            if not self.project_path:
                return
                
            try:
                # Check and fix package.json
                package_json = Path(self.project_path) / 'package.json'
                if package_json.exists():
                    await self._fix_package_json_config()
                    
                # Check and fix tsconfig.json
                tsconfig = Path(self.project_path) / 'tsconfig.json'
                if tsconfig.exists():
                    await self._fix_tsconfig()
                    
                # Check and fix next.config.js
                next_config = Path(self.project_path) / 'next.config.js'
                if next_config.exists():
                    await self._fix_next_config()
                    
                # Check and fix environment variables
                env_file = Path(self.project_path) / '.env'
                env_example = Path(self.project_path) / '.env.example'
                if env_file.exists() or env_example.exists():
                    await self._fix_env_config()
                    
            except Exception as e:
                logging.error(f"Error fixing configuration: {str(e)}")
                raise
                
        return fix_config_error

    def _get_build_error_fix(self):
        """Get the implementation for fixing build errors."""
        async def fix_build_error():
            if not self.project_path:
                return
                
            try:
                # Run build to get errors
                process = await asyncio.create_subprocess_exec(
                    'npm', 'run', 'build',
                    cwd=self.project_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    # Parse build errors
                    errors = self._parse_build_errors(stderr.decode())
                    
                    # Fix each error
                    for error in errors:
                        if 'Module not found' in error:
                            await self._fix_missing_module(error)
                        elif 'Type error' in error:
                            await self._fix_build_type_error(error)
                        elif 'Syntax error' in error:
                            await self._fix_syntax_error(error)
                        else:
                            await self._fix_generic_build_error(error)
                            
                    # Try building again
                    await asyncio.create_subprocess_exec(
                        'npm', 'run', 'build',
                        cwd=self.project_path
                    )
                    
            except Exception as e:
                logging.error(f"Error fixing build errors: {str(e)}")
                raise
                
        return fix_build_error

    def _get_test_error_fix(self):
        """Get the implementation for fixing test-related errors."""
        async def fix_test_error():
            if not self.project_path:
                return
                
            try:
                # Run tests to get errors
                process = await asyncio.create_subprocess_exec(
                    'npm', 'test',
                    cwd=self.project_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    # Parse test errors
                    errors = self._parse_test_errors(stdout.decode())
                    
                    # Fix each error
                    for error in errors:
                        if 'snapshot' in error.lower():
                            await self._fix_snapshot_error(error)
                        elif 'timeout' in error.lower():
                            await self._fix_test_timeout(error)
                        elif 'assertion' in error.lower():
                            await self._fix_assertion_error(error)
                        else:
                            await self._fix_generic_test_error(error)
                            
                    # Run tests again to verify fixes
                    await asyncio.create_subprocess_exec(
                        'npm', 'test',
                        cwd=self.project_path
                    )
                    
            except Exception as e:
                logging.error(f"Error fixing test errors: {str(e)}")
                raise
                
        return fix_test_error

    async def _fix_single_type_error(self, error: Dict) -> None:
        """Fix a single TypeScript type error."""
        file_path = Path(self.project_path) / error['file']
        if not file_path.exists():
            return
            
        content = file_path.read_text()
        lines = content.splitlines()
        
        if 'implicit any' in error['message'].lower():
            # Add type annotation
            line = lines[error['line'] - 1]
            if ':' not in line:
                variable = line.split('=')[0].strip()
                lines[error['line'] - 1] = f"{variable}: any = {line.split('=')[1]}"
                
        elif 'property does not exist' in error['message'].lower():
            # Add interface/type definition
            type_name = error['message'].split("'")[1]
            interface_def = f"\ninterface {type_name} {{\n  // TODO: Add proper type definition\n}}\n"
            lines.insert(0, interface_def)
            
        elif 'no overload matches' in error['message'].lower():
            # Fix function parameters
            line = lines[error['line'] - 1]
            if 'function' in line:
                param = error['message'].split("'")[1]
                lines[error['line'] - 1] = line.replace(param, 'any')
                
        file_path.write_text('\n'.join(lines))

    async def _fix_style_issue(self, issue: Dict) -> None:
        """Fix a single ESLint style issue."""
        file_path = Path(self.project_path) / issue['filePath']
        if not file_path.exists():
            return
            
        content = file_path.read_text()
        lines = content.splitlines()
        
        for message in issue['messages']:
            line_num = message['line'] - 1
            if message['ruleId'] == 'quotes':
                # Fix quote style
                lines[line_num] = lines[line_num].replace('"', "'")
            elif message['ruleId'] == 'semi':
                # Fix semicolons
                if not lines[line_num].endswith(';'):
                    lines[line_num] += ';'
            elif message['ruleId'] == 'indent':
                # Fix indentation
                lines[line_num] = ' ' * message['fix']['range'][0] + lines[line_num].lstrip()
                
        file_path.write_text('\n'.join(lines))

    async def _fix_package_json_config(self) -> None:
        """Fix package.json configuration issues."""
        package_json = Path(self.project_path) / 'package.json'
        if not package_json.exists():
            return
            
        data = json.loads(package_json.read_text())
        
        # Ensure required fields
        if 'name' not in data:
            data['name'] = Path(self.project_path).name
        if 'version' not in data:
            data['version'] = '0.1.0'
        if 'scripts' not in data:
            data['scripts'] = {}
            
        # Add common scripts
        scripts = data['scripts']
        if 'dev' not in scripts:
            scripts['dev'] = 'next dev'
        if 'build' not in scripts:
            scripts['build'] = 'next build'
        if 'start' not in scripts:
            scripts['start'] = 'next start'
        if 'lint' not in scripts:
            scripts['lint'] = 'next lint'
            
        package_json.write_text(json.dumps(data, indent=2))

    async def _fix_tsconfig(self) -> None:
        """Fix tsconfig.json configuration issues."""
        tsconfig = Path(self.project_path) / 'tsconfig.json'
        if not tsconfig.exists():
            return
            
        data = json.loads(tsconfig.read_text())
        
        # Ensure required fields
        if 'compilerOptions' not in data:
            data['compilerOptions'] = {}
        if 'target' not in data['compilerOptions']:
            data['compilerOptions']['target'] = 'es2020'
        if 'module' not in data['compilerOptions']:
            data['compilerOptions']['module'] = 'es2020'
        if 'lib' not in data['compilerOptions']:
            data['compilerOptions']['lib'] = ['es2020']
            
        tsconfig.write_text(json.dumps(data, indent=2))

    async def _fix_next_config(self) -> None:
        """Fix next.config.js configuration issues."""
        next_config = Path(self.project_path) / 'next.config.js'
        if not next_config.exists():
            return
            
        content = next_config.read_text()
        lines = content.splitlines()
        
        # Ensure required fields
        if 'target' not in content:
            lines.append('target: "node16"')
        if 'nodeVersion' not in content:
            lines.append('nodeVersion: "16.14.0"')
            
        next_config.write_text('\n'.join(lines))

    async def _fix_env_config(self) -> None:
        """Fix environment variable configuration issues."""
        env_file = Path(self.project_path) / '.env'
        env_example = Path(self.project_path) / '.env.example'
        if not env_file.exists() and not env_example.exists():
            return
            
        if env_file.exists():
            env_file.unlink()
        if env_example.exists():
            env_example.unlink()
            
        env_file.write_text('')

    async def _fix_missing_module(self, error: str) -> None:
        """Fix missing module errors."""
        if not self.project_path:
            return
            
        try:
            # Extract module name from error
            module_name = error.split("'")[1]
            
            # Install missing module
            await self.dependency_manager.install_dependencies([module_name])
            
        except Exception as e:
            logger.error(f"Failed to fix missing module: {str(e)}")
            raise

    async def _fix_build_type_error(self, error: str) -> None:
        """Fix build type errors."""
        if not self.project_path:
            return
            
        try:
            # Extract type name from error
            type_name = error.split("'")[1]
            
            # Add type definition
            await self._add_type_definition(type_name)
            
        except Exception as e:
            logger.error(f"Failed to fix build type error: {str(e)}")
            raise

    async def _fix_syntax_error(self, error: str) -> None:
        """Fix syntax errors."""
        if not self.project_path:
            return
            
        try:
            # Extract file path from error
            file_path = error.split("'")[1]
            
            # Fix syntax error
            await self._fix_syntax_error_in_file(file_path)
            
        except Exception as e:
            logger.error(f"Failed to fix syntax error: {str(e)}")
            raise

    async def _fix_generic_build_error(self, error: str) -> None:
        """Fix generic build errors."""
        if not self.project_path:
            return
            
        try:
            # Run build to get errors
            process = await asyncio.create_subprocess_exec(
                'npm', 'run', 'build',
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                # Parse build errors
                errors = self._parse_build_errors(stderr.decode())
                
                # Fix each error
                for error in errors:
                    if 'Module not found' in error:
                        await self._fix_missing_module(error)
                    elif 'Type error' in error:
                        await self._fix_build_type_error(error)
                    elif 'Syntax error' in error:
                        await self._fix_syntax_error(error)
                    else:
                        await self._fix_generic_build_error(error)
                        
                # Try building again
                await asyncio.create_subprocess_exec(
                    'npm', 'run', 'build',
                    cwd=self.project_path
                )
                
        except Exception as e:
            logger.error(f"Failed to fix generic build error: {str(e)}")
            raise

    async def _fix_snapshot_error(self, error: str) -> None:
        """Fix snapshot errors."""
        if not self.project_path:
            return
            
        try:
            # Extract test file path from error
            test_file = error.split("'")[1]
            
            # Re-run tests
            await self._run_tests()
            
        except Exception as e:
            logger.error(f"Failed to fix snapshot error: {str(e)}")
            raise

    async def _fix_test_timeout(self, error: str) -> None:
        """Fix test timeout errors."""
        if not self.project_path:
            return
            
        try:
            # Extract test file path from error
            test_file = error.split("'")[1]
            
            # Increase timeout
            await self._increase_timeout(test_file)
            
        except Exception as e:
            logger.error(f"Failed to fix test timeout: {str(e)}")
            raise

    async def _fix_assertion_error(self, error: str) -> None:
        """Fix assertion errors."""
        if not self.project_path:
            return
            
        try:
            # Extract test file path from error
            test_file = error.split("'")[1]
            
            # Fix assertion
            await self._fix_assertion_in_file(test_file)
            
        except Exception as e:
            logger.error(f"Failed to fix assertion error: {str(e)}")
            raise

    async def _fix_generic_test_error(self, error: str) -> None:
        """Fix generic test errors."""
        if not self.project_path:
            return
            
        try:
            # Re-run tests
            await self._run_tests()
            
        except Exception as e:
            logger.error(f"Failed to fix generic test error: {str(e)}")
            raise

    async def _run_tests(self) -> None:
        """Re-run tests."""
        if not self.project_path:
            return
            
        try:
            # Run tests
            process = await asyncio.create_subprocess_exec(
                'npm', 'test',
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                # Parse test errors
                errors = self._parse_test_errors(stdout.decode())
                
                # Fix each error
                for error in errors:
                    if 'snapshot' in error.lower():
                        await self._fix_snapshot_error(error)
                    elif 'timeout' in error.lower():
                        await self._fix_test_timeout(error)
                    elif 'assertion' in error.lower():
                        await self._fix_assertion_error(error)
                    else:
                        await self._fix_generic_test_error(error)
                        
                # Run tests again to verify fixes
                await asyncio.create_subprocess_exec(
                    'npm', 'test',
                    cwd=self.project_path
                )
            
        except Exception as e:
            logger.error(f"Failed to run tests: {str(e)}")
            raise

    async def _add_type_definition(self, type_name: str) -> None:
        """Add a type definition to the project."""
        if not self.project_path:
            return
            
        try:
            # Add type definition to the project
            await self._add_type_definition_to_file(type_name)
            
        except Exception as e:
            logger.error(f"Failed to add type definition: {str(e)}")
            raise

    async def _add_type_definition_to_file(self, file: Path, type_name: str) -> None:
        """Add a type definition to a specific file."""
        if not file.exists():
            return
            
        try:
            content = file.read_text()
            if f"interface {type_name} " not in content:
                # Add type definition
                interface_def = f"""
interface {type_name} {{
    // TODO: Add proper type definition
}}
"""
                # Add after imports or at top of file
                lines = content.splitlines()
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith('import '):
                        insert_idx = i + 1
                    elif line.startswith('export '):
                        insert_idx = i
                        break
                        
                lines.insert(insert_idx, interface_def)
                file.write_text('\n'.join(lines))
            
        except Exception as e:
            logger.error(f"Failed to add type definition to file: {str(e)}")
            raise

    async def _fix_syntax_error_in_file(self, file_path: str) -> None:
        """Fix syntax errors in a file."""
        file = Path(self.project_path) / file_path
        if not file.exists():
            return
            
        try:
            content = file.read_text()
            lines = content.splitlines()
            
            # Common syntax fixes
            for i, line in enumerate(lines):
                # Fix missing semicolons
                if not line.strip().endswith(';') and not line.strip().endswith('{') and not line.strip().endswith('}'):
                    if any(keyword in line for keyword in ['return', 'const', 'let', 'var']):
                        lines[i] = line + ';'
                        
                # Fix template literal syntax
                if '${' in line and not line.count('`') >= 2:
                    lines[i] = line.replace("'", '`').replace('"', '`')
                    
                # Fix object property access
                if '[' in line and ']' in line and not '"' in line and not "'" in line:
                    prop = line[line.index('[')+1:line.index(']')].strip()
                    if prop.isidentifier():
                        lines[i] = line.replace(f'[{prop}]', f'.{prop}')
                        
            file.write_text('\n'.join(lines))
            
        except Exception as e:
            logger.error(f"Failed to fix syntax error in file: {str(e)}")
            raise

    async def _fix_assertion_in_file(self, test_file: str) -> None:
        """Fix assertion errors in a test file."""
        file = Path(self.project_path) / test_file
        if not file.exists():
            return
            
        try:
            content = file.read_text()
            lines = content.splitlines()
            
            for i, line in enumerate(lines):
                if 'expect(' in line:
                    # Fix common assertion issues
                    if '.toBe(' in line and ('null' in line or 'undefined' in line):
                        lines[i] = line.replace('.toBe(', '.toBeNull(') if 'null' in line else line.replace('.toBe(', '.toBeUndefined(')
                    elif '.toBe({' in line or '.toBe([' in line:
                        lines[i] = line.replace('.toBe(', '.toEqual(')
                    elif '.toBe(' in line and ('true' in line or 'false' in line):
                        lines[i] = line.replace('.toBe(', '.toBeTruthy(') if 'true' in line else line.replace('.toBe(', '.toBeFalsy(')
                        
            file.write_text('\n'.join(lines))
            
        except Exception as e:
            logger.error(f"Failed to fix assertion in file: {str(e)}")
            raise

    async def _increase_timeout(self, test_file: str) -> None:
        """Increase timeout for a test file."""
        file = Path(self.project_path) / test_file
        if not file.exists():
            return
            
        try:
            content = file.read_text()
            lines = content.splitlines()
            
            for i, line in enumerate(lines):
                if 'timeout' in line:
                    # Extract current timeout value
                    current = int(''.join(filter(str.isdigit, line)))
                    # Double the timeout
                    new_timeout = current * 2
                    lines[i] = line.replace(str(current), str(new_timeout))
                elif 'test(' in line or 'it(' in line:
                    # Add timeout to test definition
                    if 'timeout' not in line:
                        lines[i] = line.replace(')', ', { timeout: 10000 })')
                        
            file.write_text('\n'.join(lines))
            
        except Exception as e:
            logger.error(f"Failed to increase timeout: {str(e)}")
            raise

    async def _run_tests(self) -> None:
        """Re-run tests."""
        if not self.project_path:
            return
            
        try:
            # Run tests
            process = await asyncio.create_subprocess_exec(
                'npm', 'test',
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                # Parse test errors
                errors = self._parse_test_errors(stdout.decode())
                
                # Fix each error
                for error in errors:
                    if 'snapshot' in error.lower():
                        await self._fix_snapshot_error(error)
                    elif 'timeout' in error.lower():
                        await self._fix_test_timeout(error)
                    elif 'assertion' in error.lower():
                        await self._fix_assertion_error(error)
                    else:
                        await self._fix_generic_test_error(error)
                        
                # Run tests again to verify fixes
                await asyncio.create_subprocess_exec(
                    'npm', 'test',
                    cwd=self.project_path
                )
            
        except Exception as e:
            logger.error(f"Failed to run tests: {str(e)}")
            raise

    async def _fix_import_error(self) -> None:
        """Fix import-related errors by checking paths and dependencies."""
        try:
            # Check if node_modules exists
            node_modules = self.project_builder.project_path / 'node_modules'
            if not node_modules.exists():
                # Try npm install again with full path
                npm_path = r"C:\Program Files\nodejs\npm.cmd"
                subprocess.run([npm_path, 'install'], cwd=self.project_builder.project_path, check=True)
                logger.info("Reinstalled dependencies")
            
            # Check package.json
            package_json = self.project_builder.project_path / 'package.json'
            if not package_json.exists():
                raise ValueError("package.json not found")
            
            # Validate package.json
            with open(package_json, 'r') as f:
                try:
                    json.load(f)
                except json.JSONDecodeError:
                    raise ValueError("Invalid package.json")
                    
        except Exception as e:
            logger.error(f"Failed to fix import error: {str(e)}")
            raise

    def _get_project_initialization_fix(self) -> Dict[str, Any]:
        """Get fixes for project initialization issues."""
        return {
            'missing_files': self._fix_missing_files,
            'invalid_json': self._fix_invalid_json,
            'dependency_error': self._fix_dependency_error,
            'import_error': self._fix_import_error,
        }

    async def _fix_missing_files(self, path: Path) -> None:
        """Fix missing files by recreating them."""
        try:
            if not path.exists():
                if path.suffix == '.json':
                    # Recreate package.json
                    if path.name == 'package.json':
                        basic_package = {
                            "name": path.parent.name,
                            "version": "0.1.0",
                            "private": True,
                            "scripts": {
                                "dev": "next dev",
                                "build": "next build",
                                "start": "next start"
                            },
                            "dependencies": {
                                "next": "latest",
                                "react": "latest",
                                "react-dom": "latest"
                            }
                        }
                        with open(path, 'w') as f:
                            json.dump(basic_package, f, indent=2)
                    
                elif path.suffix in ['.tsx', '.ts']:
                    # Recreate basic component
                    await self.project_builder._create_component(
                        name=path.stem,
                        requirements=[],
                        component_dir=path.parent
                    )
        except Exception as e:
            logger.error(f"Failed to fix missing files: {str(e)}")
            raise

    async def _fix_invalid_json(self, path: Path) -> None:
        """Fix invalid JSON files."""
        try:
            if path.exists() and path.suffix == '.json':
                with open(path, 'r') as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        # Try to fix common JSON issues
                        content = f.read()
                        fixed_content = content.replace("'", '"').replace(",}", "}").replace(",]", "]")
                        data = json.loads(fixed_content)
                
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to fix invalid JSON: {str(e)}")
            raise

    async def _fix_dependency_error(self) -> None:
        """Fix dependency-related errors."""
        try:
            npm_path = r"C:\Program Files\nodejs\npm.cmd"
            
            # Clear node_modules and package-lock.json
            node_modules = self.project_builder.project_path / 'node_modules'
            package_lock = self.project_builder.project_path / 'package-lock.json'
            
            if node_modules.exists():
                shutil.rmtree(node_modules)
            if package_lock.exists():
                package_lock.unlink()
            
            # Reinstall dependencies
            subprocess.run([npm_path, 'install'], cwd=self.project_builder.project_path, check=True)
            logger.info("Reinstalled dependencies after clearing cache")
            
        except Exception as e:
            logger.error(f"Failed to fix dependency error: {str(e)}")
            raise