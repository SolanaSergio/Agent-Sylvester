from typing import Dict, List, Optional
from pathlib import Path
import json
import re
from src.utils.types import ProjectConfig

class RequirementAnalyzer:
    """Analyzes project requirements and dependencies"""
    
    def __init__(self):
        self.project_dir: Optional[Path] = None

    async def analyze_project_requirements(self, config: ProjectConfig) -> Dict:
        """Analyze project requirements based on configuration"""
        self.project_dir = Path(config.name)
        
        requirements = {
            "dependencies": await self._get_dependencies(config),
            "devDependencies": await self._get_dev_dependencies(config),
            "scripts": await self._get_scripts(config),
            "configurations": await self._get_configurations(config),
            "features": await self._analyze_features(config),
            "structure": await self._analyze_structure(config)
        }
        return requirements

    async def analyze_current_state(self) -> Dict:
        """Analyze current project state"""
        if not self.project_dir or not self.project_dir.exists():
            raise ValueError("No project directory found")
            
        package_json = self.project_dir / "package.json"
        if not package_json.exists():
            return {
                "status": "incomplete",
                "missing": ["package.json"],
                "completedSteps": [],
                "pendingSteps": ["initialization", "dependencies", "components"]
            }
            
        with open(package_json) as f:
            package_data = json.load(f)
            
        completed_steps = ["initialization"]
        pending_steps = []
        
        # Check dependencies
        if package_data.get("dependencies"):
            completed_steps.append("dependencies")
        else:
            pending_steps.append("dependencies")
            
        # Check components
        if (self.project_dir / "src/components").exists():
            completed_steps.append("components")
        else:
            pending_steps.append("components")
            
        # Check tests
        if (self.project_dir / "tests").exists():
            completed_steps.append("testing")
        else:
            pending_steps.append("testing")
            
        # Check documentation
        if (self.project_dir / "docs").exists():
            completed_steps.append("documentation")
        else:
            pending_steps.append("documentation")
            
        return {
            "status": "in_progress" if pending_steps else "complete",
            "completedSteps": completed_steps,
            "pendingSteps": pending_steps
        }

    async def _get_dependencies(self, config: ProjectConfig) -> Dict[str, str]:
        """Get required dependencies based on framework and features"""
        deps = {}
        
        # Framework dependencies
        if config.framework == "React":
            deps.update({
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-scripts": "5.0.1"
            })
        elif config.framework == "Next.js":
            deps.update({
                "next": "^13.0.0",
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            })
        elif config.framework == "Vue":
            deps.update({
                "vue": "^3.3.0",
                "vue-router": "^4.2.0",
                "pinia": "^2.1.0"
            })
        elif config.framework == "Angular":
            deps.update({
                "@angular/core": "^16.0.0",
                "@angular/common": "^16.0.0",
                "@angular/router": "^16.0.0"
            })
        
        # Feature dependencies
        if "Authentication" in config.features:
            if config.framework == "Next.js":
                deps["next-auth"] = "^4.22.1"
            else:
                deps["@auth0/auth0-react"] = "^2.0.0"
                
        if "Database" in config.features:
            deps.update({
                "prisma": "^4.14.0",
                "@prisma/client": "^4.14.0"
            })
            
        if "API" in config.features:
            deps.update({
                "axios": "^1.4.0",
                "swr": "^2.1.5"
            })
            
        return deps

    async def _get_dev_dependencies(self, config: ProjectConfig) -> Dict[str, str]:
        """Get required dev dependencies"""
        dev_deps = {
            "typescript": "^5.0.0",
            "eslint": "^8.40.0",
            "prettier": "^2.8.8",
            "@types/node": "^18.0.0"
        }
        
        # Framework-specific dev dependencies
        if config.framework in ["React", "Next.js"]:
            dev_deps.update({
                "@types/react": "^18.2.0",
                "@types/react-dom": "^18.2.0",
                "eslint-config-next": "^13.0.0"
            })
        elif config.framework == "Vue":
            dev_deps.update({
                "@vitejs/plugin-vue": "^4.2.0",
                "vue-tsc": "^1.6.0"
            })
        elif config.framework == "Angular":
            dev_deps.update({
                "@angular-devkit/build-angular": "^16.0.0",
                "@angular/cli": "^16.0.0"
            })
            
        # Feature-specific dev dependencies
        if "Testing" in config.features:
            dev_deps.update({
                "jest": "^29.5.0",
                "@testing-library/react": "^14.0.0",
                "@testing-library/jest-dom": "^5.16.5",
                "@types/jest": "^29.5.0"
            })
            
        if "Database" in config.features:
            dev_deps["prisma-cli"] = "^4.14.0"
            
        return dev_deps

    async def _get_scripts(self, config: ProjectConfig) -> Dict[str, str]:
        """Get required npm scripts"""
        scripts = {
            "lint": "eslint .",
            "format": "prettier --write .",
            "type-check": "tsc --noEmit"
        }
        
        # Framework-specific scripts
        if config.framework == "Next.js":
            scripts.update({
                "dev": "next dev",
                "build": "next build",
                "start": "next start"
            })
        elif config.framework == "React":
            scripts.update({
                "dev": "react-scripts start",
                "build": "react-scripts build",
                "start": "react-scripts start"
            })
        elif config.framework == "Vue":
            scripts.update({
                "dev": "vite",
                "build": "vue-tsc && vite build",
                "preview": "vite preview"
            })
        elif config.framework == "Angular":
            scripts.update({
                "dev": "ng serve",
                "build": "ng build",
                "watch": "ng build --watch"
            })
            
        # Feature-specific scripts
        if "Testing" in config.features:
            scripts.update({
                "test": "jest",
                "test:watch": "jest --watch",
                "test:coverage": "jest --coverage"
            })
            
        if "Database" in config.features:
            scripts.update({
                "db:migrate": "prisma migrate deploy",
                "db:generate": "prisma generate",
                "db:studio": "prisma studio"
            })
            
        return scripts

    async def _get_configurations(self, config: ProjectConfig) -> Dict:
        """Get required configuration files"""
        configs = {
            "tsconfig.json": True,
            ".eslintrc.js": True,
            ".prettierrc": True,
            ".gitignore": True,
            ".env.example": True
        }
        
        # Framework-specific configs
        if config.framework == "Next.js":
            configs["next.config.js"] = True
        elif config.framework == "Vue":
            configs["vite.config.ts"] = True
        elif config.framework == "Angular":
            configs["angular.json"] = True
            
        # Feature-specific configs
        if "Testing" in config.features:
            configs["jest.config.js"] = True
            configs["jest.setup.js"] = True
            
        if "Database" in config.features:
            configs["prisma/schema.prisma"] = True
            
        return configs

    async def _analyze_features(self, config: ProjectConfig) -> Dict:
        """Analyze required features and their dependencies"""
        features = {}
        
        for feature in config.features:
            if feature == "Authentication":
                features["auth"] = {
                    "type": "next-auth" if config.framework == "Next.js" else "auth0",
                    "requires": ["API", "Database"],
                    "optional": ["Testing"]
                }
            elif feature == "Database":
                features["database"] = {
                    "type": "prisma",
                    "requires": [],
                    "optional": ["API", "Testing"]
                }
            elif feature == "API":
                features["api"] = {
                    "type": "rest",
                    "requires": [],
                    "optional": ["Testing", "Database"]
                }
            elif feature == "Testing":
                features["testing"] = {
                    "type": "jest",
                    "requires": [],
                    "optional": []
                }
                
        return features

    async def _analyze_structure(self, config: ProjectConfig) -> Dict:
        """Analyze required project structure"""
        structure = {
            "src": {
                "components": ["layout", "shared", "features"],
                "pages": config.framework in ["Next.js", "Vue", "Angular"],
                "styles": True,
                "utils": True,
                "hooks": config.framework in ["React", "Next.js"],
                "services": True,
                "types": True
            },
            "public": True,
            "tests": "Testing" in config.features,
            "docs": True
        }
        
        if "API" in config.features:
            structure["src"]["api"] = ["client", "server"]
            
        if "Database" in config.features:
            structure["prisma"] = True
            
        return structure 