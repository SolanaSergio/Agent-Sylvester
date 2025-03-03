from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import re
from src.utils.types import ProjectConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RequirementAnalyzer:
    """Analyzes project requirements and dependencies"""
    
    def __init__(self):
        self.project_dir: Optional[Path] = None

    async def analyze_project_requirements(self, config: ProjectConfig, project_path: Optional[Path] = None) -> Dict:
        """Analyze project requirements based on configuration"""
        if not config.name:
            raise ValueError("Project name is required")

        logger.info(f"Analyzing requirements for {config.name}")
        
        if project_path:
            self.project_dir = project_path
        else:
            # Create a safe directory name from the project name
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in config.name)
            self.project_dir = Path(safe_name)
            
        logger.info(f"Using project directory: {self.project_dir}")
        
        try:
            # First, analyze the project description to extract additional requirements
            description_requirements = await self.analyze_user_request(config.description) if config.description else {}
            
            # Merge description-based requirements with explicit configuration
            requirements = {
                "dependencies": await self._get_dependencies(config),
                "devDependencies": await self._get_dev_dependencies(config),
                "scripts": await self._get_scripts(config),
                "configurations": await self._get_configurations(config),
                "features": await self._analyze_features(config),
                "structure": await self._analyze_structure(config)
            }

            # Add features detected from description
            if description_requirements.get("features"):
                for feature in description_requirements["features"]:
                    if feature not in config.features:
                        config.features.append(feature)
                        logger.info(f"Added feature from description: {feature}")

            # Add API endpoints if detected in description
            if description_requirements.get("api_endpoints"):
                requirements["api_endpoints"] = description_requirements["api_endpoints"]
                if "api" not in config.features:
                    config.features.append("api")
                    logger.info("Added API feature based on description")

            # Add database requirements if detected in description
            if description_requirements.get("database", {}).get("needed"):
                requirements["database"] = description_requirements["database"]
                if "database" not in config.features:
                    config.features.append("database")
                    logger.info("Added database feature based on description")

            # Add UI components if detected in description
            if description_requirements.get("components"):
                requirements["components"] = description_requirements["components"]
                if "ui" not in config.features:
                    config.features.append("ui")
                    logger.info("Added UI feature based on description")

            # Update dependencies based on new features
            requirements["dependencies"] = await self._get_dependencies(config)
            requirements["devDependencies"] = await self._get_dev_dependencies(config)

            logger.info("Requirements analysis complete")
            return requirements
        except Exception as e:
            logger.error(f"Error analyzing requirements: {str(e)}")
            raise

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

    async def analyze_user_request(self, description: str) -> Dict[str, Any]:
        """Analyze user request to determine required updates and code generation needs"""
        logger.info(f"Analyzing user request: {description}")
        
        # Initialize requirements dictionary
        requirements = {
            "components": [],
            "dependencies": [],
            "features": [],
            "styles": [],
            "api_endpoints": [],
            "code_changes": {
                "files_to_modify": [],
                "files_to_create": [],
                "code_blocks": []
            },
            "database": {
                "needed": False,
                "type": None,
                "models": []
            }
        }
        
        # Convert to lowercase for easier matching
        description = description.lower()
        
        # Analyze for code generation requirements
        code_patterns = [
            (r"(?:create|add|implement)\s+(?:a|an|the)?\s*(\w+)\s+(?:function|method|class|interface)", "code_blocks"),
            (r"(?:update|modify|change)\s+(?:the)?\s*(\w+)\s+(?:in|at|of)\s+([^\s]+)", "files_to_modify"),
            (r"(?:create|add)\s+(?:a|an|the)?\s*(?:new)?\s*(\w+)\s+(?:file|module)\s+(?:in|at)?\s*([^\s]+)?", "files_to_create")
        ]
        
        for pattern, key in code_patterns:
            matches = re.finditer(pattern, description)
            for match in matches:
                if match.groups():
                    if key == "code_blocks":
                        requirements["code_changes"]["code_blocks"].append({
                            "type": match.group(1),
                            "name": match.group(1),
                            "description": description
                        })
                    elif key == "files_to_modify":
                        requirements["code_changes"]["files_to_modify"].append({
                            "name": match.group(2),
                            "element": match.group(1),
                            "description": description
                        })
                    elif key == "files_to_create":
                        requirements["code_changes"]["files_to_create"].append({
                            "name": match.group(1),
                            "path": match.group(2) if match.group(2) else None,
                            "description": description
                        })

        # Analyze for UI components
        ui_patterns = [
            (r"(?:add|create|build|implement)\s+(?:a|an|the)?\s*(\w+)\s+(?:component|page|screen|view)", "components"),
            (r"(?:need|want)\s+(?:a|an|the)?\s*(\w+)\s+(?:component|page|screen|view)", "components"),
            (r"(?:dashboard|landing page|home page|profile page)", "components")
        ]
        
        for pattern, key in ui_patterns:
            matches = re.finditer(pattern, description)
            for match in matches:
                if match.groups():
                    requirements["components"].append({
                        "name": match.group(1),
                        "type": "component",
                        "description": description
                    })
        
        # Analyze for features
        feature_patterns = {
            "authentication": ["login", "auth", "sign up", "register", "user account"],
            "database": ["database", "store data", "save", "persist"],
            "api": ["api", "endpoint", "backend", "server", "fetch"],
            "real-time": ["real-time", "live", "socket", "update automatically"],
            "payment": ["payment", "stripe", "checkout", "billing"],
            "search": ["search", "filter", "find"],
            "file-upload": ["upload", "file", "image", "media"]
        }
        
        for feature, keywords in feature_patterns.items():
            if any(keyword in description for keyword in keywords):
                requirements["features"].append(feature)
                
        # Analyze for styling requirements
        style_patterns = {
            "tailwind": ["tailwind", "utility classes"],
            "styled-components": ["styled components", "css-in-js"],
            "sass": ["sass", "scss"],
            "css-modules": ["css modules"],
            "material-ui": ["material ui", "mui"],
            "chakra-ui": ["chakra"]
        }
        
        for style, keywords in style_patterns.items():
            if any(keyword in description for keyword in keywords):
                requirements["styles"].append(style)
                
        # Analyze for API endpoints
        api_patterns = [
            r"(?:create|add|implement)\s+(?:an?)?\s*api\s+(?:for|to)\s+([^,.]+)",
            r"(?:need|want)\s+(?:an?)?\s*api\s+(?:for|to)\s+([^,.]+)",
            r"endpoint\s+(?:for|to)\s+([^,.]+)"
        ]
        
        for pattern in api_patterns:
            matches = re.finditer(pattern, description)
            for match in matches:
                if match.groups():
                    requirements["api_endpoints"].append(match.group(1).strip())
                    
        # Analyze for database requirements
        db_patterns = {
            "mongodb": ["mongodb", "mongo", "nosql"],
            "postgresql": ["postgresql", "postgres", "sql"],
            "mysql": ["mysql", "mariadb"],
            "sqlite": ["sqlite", "local database"]
        }
        
        for db, keywords in db_patterns.items():
            if any(keyword in description for keyword in keywords):
                requirements["database"]["needed"] = True
                requirements["database"]["type"] = db
                break
                
        # If database is needed, try to identify models
        if requirements["database"]["needed"]:
            model_pattern = r"(?:store|save|model|table|collection)\s+(?:for|of)?\s*(\w+)"
            matches = re.finditer(model_pattern, description)
            for match in matches:
                if match.groups():
                    requirements["database"]["models"].append(match.group(1))
                    
        logger.info(f"Analysis results: {requirements}")
        return requirements

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
        try:
            features = {}
            
            for feature in config.features:
                if feature == "Authentication":
                    features["auth"] = {
                        "type": "next-auth" if config.framework == "Next.js" else "auth0",
                        "requires": ["API", "Database"],
                        "optional": ["Testing"],
                        "config_files": [".env", "auth.config.ts"],
                        "dependencies": self._get_auth_dependencies(config.framework)
                    }
                elif feature == "Database":
                    features["database"] = {
                        "type": "prisma",
                        "requires": [],
                        "optional": ["API", "Testing"],
                        "config_files": ["prisma/schema.prisma", ".env"],
                        "dependencies": {
                            "prisma": "^4.14.0",
                            "@prisma/client": "^4.14.0"
                        }
                    }
                elif feature == "API":
                    features["api"] = {
                        "type": "rest",
                        "requires": [],
                        "optional": ["Testing", "Database"],
                        "config_files": ["api.config.ts"],
                        "dependencies": {
                            "axios": "^1.4.0",
                            "swr": "^2.1.5"
                        }
                    }
                elif feature == "Testing":
                    features["testing"] = {
                        "type": "jest",
                        "requires": [],
                        "optional": [],
                        "config_files": ["jest.config.js", "jest.setup.js"],
                        "dependencies": self._get_testing_dependencies(config.framework)
                    }
                    
            # Validate feature dependencies
            self._validate_feature_dependencies(features)
                    
            return features
        except Exception as e:
            logger.error(f"Error analyzing features: {str(e)}")
            raise

    def _get_auth_dependencies(self, framework: str) -> Dict[str, str]:
        """Get authentication dependencies based on framework"""
        if framework == "Next.js":
            return {
                "next-auth": "^4.22.1",
                "bcryptjs": "^2.4.3",
                "jsonwebtoken": "^9.0.0"
            }
        else:
            return {
                "@auth0/auth0-react": "^2.0.0",
                "jwt-decode": "^3.1.2"
            }

    def _get_testing_dependencies(self, framework: str) -> Dict[str, str]:
        """Get testing dependencies based on framework"""
        deps = {
            "jest": "^29.5.0",
            "@types/jest": "^29.5.0"
        }
        
        if framework in ["React", "Next.js"]:
            deps.update({
                "@testing-library/react": "^14.0.0",
                "@testing-library/jest-dom": "^5.16.5",
                "@testing-library/user-event": "^14.4.3"
            })
        elif framework == "Vue":
            deps.update({
                "@vue/test-utils": "^2.3.0",
                "@vue/cli-plugin-unit-jest": "^5.0.8"
            })
        elif framework == "Angular":
            deps.update({
                "@angular/cli": "^16.0.0",
                "@angular/compiler-cli": "^16.0.0",
                "karma": "^6.4.0",
                "karma-chrome-launcher": "^3.2.0",
                "karma-coverage": "^2.2.0",
                "karma-jasmine": "^5.1.0"
            })
            
        return deps

    def _validate_feature_dependencies(self, features: Dict) -> None:
        """Validate feature dependencies and detect conflicts"""
        # Check required dependencies
        for feature_name, feature in features.items():
            for required in feature.get("requires", []):
                if required not in features:
                    raise ValueError(f"Feature '{feature_name}' requires '{required}' but it's not enabled")
                    
        # Check for circular dependencies
        visited = set()
        path = []
        
        def check_circular(feature_name: str) -> None:
            if feature_name in path:
                cycle = path[path.index(feature_name):] + [feature_name]
                raise ValueError(f"Circular dependency detected: {' -> '.join(cycle)}")
                
            if feature_name in visited:
                return
                
            visited.add(feature_name)
            path.append(feature_name)
            
            for required in features[feature_name].get("requires", []):
                if required in features:
                    check_circular(required)
                    
            path.pop()
            
        for feature_name in features:
            check_circular(feature_name)

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

    async def analyze_requirements(self, project_path: Path, description: str) -> dict:
        """Analyze project requirements based on description and path"""
        try:
            # Initialize requirements structure
            requirements = {
                'structure': {
                    'src': {
                        'components': True,
                        'pages': True,
                        'hooks': True,
                        'contexts': True,
                        'styles': True,
                        'utils': True,
                        'services': True,
                        'types': True
                    },
                    'public': True,
                    'tests': True
                },
                'dependencies': {
                    'dependencies': {
                        'next': 'latest',
                        'react': 'latest',
                        'react-dom': 'latest'
                    },
                    'devDependencies': {
                        'typescript': 'latest',
                        '@types/react': 'latest',
                        '@types/node': 'latest',
                        'eslint': 'latest',
                        'eslint-config-next': 'latest'
                    }
                },
                'configurations': {
                    'tsconfig.json': True,
                    '.eslintrc.js': True,
                    '.prettierrc': True,
                    '.gitignore': True,
                    '.env.example': True,
                    'next.config.js': True
                },
                'features': self._analyze_features(description),
                'styles': ['tailwind'],
                'api_endpoints': self._analyze_api_requirements(description),
                'database': self._analyze_database_requirements(description)
            }

            # Add feature-specific requirements
            if 'authentication' in requirements['features']:
                requirements['dependencies']['dependencies']['next-auth'] = 'latest'

            if 'api' in requirements['features']:
                requirements['dependencies']['dependencies']['axios'] = 'latest'

            if 'form' in requirements['features']:
                requirements['dependencies']['dependencies']['react-hook-form'] = 'latest'
                requirements['dependencies']['dependencies']['zod'] = 'latest'

            if 'database' in requirements['features']:
                requirements['dependencies']['dependencies']['prisma'] = 'latest'
                requirements['dependencies']['devDependencies']['@prisma/client'] = 'latest'

            return requirements

        except Exception as e:
            logger.error(f"Failed to analyze requirements: {str(e)}")
            raise

    def _analyze_features(self, description: str) -> List[str]:
        """Analyze description to determine required features"""
        features = []
        
        # Common feature keywords
        feature_patterns = {
            'authentication': ['auth', 'login', 'signup', 'user account'],
            'api': ['api', 'endpoint', 'backend', 'server'],
            'database': ['database', 'storage', 'persist', 'save'],
            'form': ['form', 'input', 'submit', 'validation'],
            'routing': ['route', 'navigation', 'pages'],
            'seo': ['seo', 'meta', 'head'],
            'analytics': ['analytics', 'tracking', 'metrics']
        }
        
        description_lower = description.lower()
        for feature, patterns in feature_patterns.items():
            if any(pattern in description_lower for pattern in patterns):
                features.append(feature)
        
        return features

    def _analyze_api_requirements(self, description: str) -> List[dict]:
        """Analyze description to determine required API endpoints"""
        endpoints = []
        
        # Common API patterns
        api_patterns = {
            'auth': {
                'patterns': ['auth', 'login', 'signup'],
                'endpoints': [
                    {'path': '/api/auth/login', 'method': 'POST'},
                    {'path': '/api/auth/signup', 'method': 'POST'},
                    {'path': '/api/auth/logout', 'method': 'POST'}
                ]
            },
            'user': {
                'patterns': ['user', 'profile', 'account'],
                'endpoints': [
                    {'path': '/api/user/profile', 'method': 'GET'},
                    {'path': '/api/user/update', 'method': 'PUT'}
                ]
            }
        }
        
        description_lower = description.lower()
        for category, info in api_patterns.items():
            if any(pattern in description_lower for pattern in info['patterns']):
                endpoints.extend(info['endpoints'])
        
        return endpoints

    def _analyze_database_requirements(self, description: str) -> dict:
        """Analyze description to determine database requirements"""
        database_req = {
            'needed': False,
            'type': None,
            'models': []
        }
        
        # Check if database is needed
        db_indicators = ['database', 'storage', 'persist', 'save', 'data']
        if any(indicator in description.lower() for indicator in db_indicators):
            database_req['needed'] = True
            database_req['type'] = 'prisma'  # Default to Prisma for Next.js projects
            
            # Analyze potential models
            model_patterns = {
                'user': ['user', 'account', 'profile'],
                'post': ['post', 'article', 'content'],
                'comment': ['comment', 'reply', 'response']
            }
            
            for model, patterns in model_patterns.items():
                if any(pattern in description.lower() for pattern in patterns):
                    database_req['models'].append(model)
        
        return database_req 