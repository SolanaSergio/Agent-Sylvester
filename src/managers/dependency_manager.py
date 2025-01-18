import asyncio
import json
from pathlib import Path
from typing import Dict, List
from src.utils.types import ProjectConfig, DependencyInfo

class DependencyManager:
    async def setup_project_dependencies(self, config: ProjectConfig) -> None:
        """Set up project dependencies based on configuration"""
        project_dir = Path(config.name)
        
        # Create package.json
        package_json = await self._generate_package_json(config)
        project_dir.joinpath("package.json").write_text(json.dumps(package_json, indent=2))
        
        # Create other config files
        await self._create_config_files(project_dir, config)
        
        # Install dependencies (simulated for now)
        await self._install_dependencies(project_dir)

    async def update_dependencies(self) -> None:
        """Update project dependencies"""
        # Implementation for updating dependencies
        pass

    async def get_dependency_status(self) -> List[DependencyInfo]:
        """Get status of all project dependencies"""
        # Read package.json and return dependency info
        try:
            with open("package.json", "r") as f:
                package_data = json.load(f)
                
            dependencies = []
            
            # Add production dependencies
            for name, version in package_data.get("dependencies", {}).items():
                dependencies.append(DependencyInfo(name=name, version=version))
                
            # Add dev dependencies
            for name, version in package_data.get("devDependencies", {}).items():
                dependencies.append(DependencyInfo(name=name, version=version))
                
            return dependencies
            
        except FileNotFoundError:
            return []

    async def _generate_package_json(self, config: ProjectConfig) -> Dict:
        """Generate package.json content"""
        return {
            "name": config.name,
            "version": "0.1.0",
            "private": True,
            "description": config.description,
            "scripts": await self._get_scripts(config),
            "dependencies": await self._get_dependencies(config),
            "devDependencies": await self._get_dev_dependencies(config)
        }

    async def _create_config_files(self, project_dir: Path, config: ProjectConfig) -> None:
        """Create configuration files"""
        # Create tsconfig.json
        tsconfig = {
            "compilerOptions": {
                "target": "es5",
                "lib": ["dom", "dom.iterable", "esnext"],
                "allowJs": True,
                "skipLibCheck": True,
                "strict": True,
                "forceConsistentCasingInFileNames": True,
                "noEmit": True,
                "esModuleInterop": True,
                "module": "esnext",
                "moduleResolution": "node",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "preserve",
                "incremental": True
            },
            "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
            "exclude": ["node_modules"]
        }
        project_dir.joinpath("tsconfig.json").write_text(json.dumps(tsconfig, indent=2))

    async def _install_dependencies(self, project_dir: Path) -> None:
        """Install project dependencies"""
        # Simulate npm install (will be implemented with actual npm commands)
        await asyncio.sleep(2)

    async def _get_scripts(self, config: ProjectConfig) -> Dict[str, str]:
        """Get npm scripts based on configuration"""
        scripts = {
            "dev": "next dev" if config.framework == "Next.js" else "react-scripts start",
            "build": "next build" if config.framework == "Next.js" else "react-scripts build",
            "start": "next start" if config.framework == "Next.js" else "react-scripts start",
            "lint": "eslint .",
            "format": "prettier --write ."
        }
        
        if "Testing" in config.features:
            scripts["test"] = "jest"
            scripts["test:watch"] = "jest --watch"
            
        return scripts

    async def _get_dependencies(self, config: ProjectConfig) -> Dict[str, str]:
        """Get production dependencies based on configuration"""
        deps = {}
        
        # Framework dependencies
        if config.framework == "React":
            deps.update({
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            })
        elif config.framework == "Next.js":
            deps.update({
                "next": "^13.0.0",
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            })
        
        # Feature dependencies
        if "Authentication" in config.features:
            deps["next-auth"] = "^4.22.1"
        if "Database" in config.features:
            deps["prisma"] = "^4.14.0"
        
        return deps

    async def _get_dev_dependencies(self, config: ProjectConfig) -> Dict[str, str]:
        """Get development dependencies based on configuration"""
        dev_deps = {
            "typescript": "^5.0.0",
            "@types/react": "^18.2.0",
            "@types/node": "^18.0.0",
            "eslint": "^8.40.0",
            "prettier": "^2.8.8"
        }
        
        if "Testing" in config.features:
            dev_deps.update({
                "jest": "^29.5.0",
                "@testing-library/react": "^14.0.0",
                "@testing-library/jest-dom": "^5.16.5"
            })
            
        return dev_deps 