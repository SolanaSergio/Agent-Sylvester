from pathlib import Path
import json
import logging
from typing import Dict, List, Set
import subprocess

class DependencyManager:
    """Manages project dependencies and package installation"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.package_json_path = project_dir / "package.json"
        
    def setup_dependencies(self, requirements: Dict):
        """Setup and install project dependencies"""
        try:
            dependencies = self._determine_dependencies(requirements)
            dev_dependencies = self._determine_dev_dependencies(requirements)
            
            self._update_package_json(dependencies, dev_dependencies)
            self._install_dependencies()
            
        except Exception as e:
            logging.error(f"Error setting up dependencies: {str(e)}")
            
    def _determine_dependencies(self, requirements: Dict) -> Dict[str, str]:
        """Determine required dependencies based on project requirements"""
        deps = {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "next": "^13.4.0"
        }
        
        features = requirements.get('features', [])
        
        # Add feature-specific dependencies
        if 'authentication' in features:
            deps.update({
                "next-auth": "^4.22.1",
                "bcryptjs": "^2.4.3"
            })
            
        if 'database' in features:
            if 'mongodb' in requirements.get('database', '').lower():
                deps["mongoose"] = "^7.3.1"
            else:
                deps["@prisma/client"] = "^4.16.2"
                
        if 'api' in features:
            deps["axios"] = "^1.4.0"
            
        if 'forms' in features:
            deps.update({
                "react-hook-form": "^7.45.1",
                "zod": "^3.21.4"
            })
            
        return deps
        
    def _determine_dev_dependencies(self, requirements: Dict) -> Dict[str, str]:
        """Determine required development dependencies"""
        dev_deps = {
            "typescript": "^5.1.6",
            "@types/react": "^18.2.14",
            "@types/node": "^20.4.2",
            "eslint": "^8.44.0",
            "eslint-config-next": "^13.4.9",
            "prettier": "^3.0.0"
        }
        
        # Add testing dependencies if needed
        if requirements.get('testing', True):
            dev_deps.update({
                "jest": "^29.6.1",
                "@testing-library/react": "^14.0.0",
                "@testing-library/jest-dom": "^5.16.5"
            })
            
        return dev_deps
        
    def _update_package_json(self, dependencies: Dict[str, str], dev_dependencies: Dict[str, str]):
        """Update package.json with new dependencies"""
        if self.package_json_path.exists():
            with open(self.package_json_path, 'r') as f:
                package_data = json.load(f)
        else:
            package_data = {
                "name": self.project_dir.name,
                "version": "0.1.0",
                "private": True
            }
            
        package_data["dependencies"] = dependencies
        package_data["devDependencies"] = dev_dependencies
        
        with open(self.package_json_path, 'w') as f:
            json.dump(package_data, f, indent=2)
            
    def _install_dependencies(self):
        """Install all dependencies using npm"""
        try:
            subprocess.run(['npm', 'install'], cwd=str(self.project_dir), check=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Error installing dependencies: {str(e)}")
            raise 

    async def cleanup(self):
        """Cleanup any temporary dependency files"""
        try:
            # Remove node_modules if specified
            if self.project_dir.exists():
                node_modules = self.project_dir / "node_modules"
                if node_modules.exists():
                    import shutil
                    shutil.rmtree(node_modules)
        except Exception as e:
            logging.error(f"Error cleaning up dependency manager: {str(e)}") 