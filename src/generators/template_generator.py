from pathlib import Path
from typing import Dict
import json

class TemplateGenerator:
    """Generates project template files and structures."""
    
    @staticmethod
    def generate_project_files(root_path: Path, requirements: Dict):
        """Generate initial project files."""
        TemplateGenerator._create_package_json(root_path, requirements)
        TemplateGenerator._create_index_html(root_path)
        TemplateGenerator._create_app_file(root_path)
        TemplateGenerator._create_styles(root_path)
    
    @staticmethod
    def _create_package_json(root_path: Path, requirements: Dict):
        """Create package.json with required dependencies."""
        package_json = {
            "name": root_path.name,
            "version": "1.0.0",
            "private": True,
            "dependencies": TemplateGenerator._get_dependencies(requirements),
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview",
                "test": "vitest"
            }
        }
        
        with open(root_path / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
    
    @staticmethod
    def _get_dependencies(requirements: Dict) -> Dict[str, str]:
        """Get required dependencies based on project requirements."""
        deps = {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "vite": "^4.4.9"
        }
        
        feature_deps = {
            "authentication": {"@auth0/auth0-react": "^2.0.0"},
            "database": {"@prisma/client": "^4.0.0"},
            "realtime": {"socket.io-client": "^4.0.0"},
            "forms": {"react-hook-form": "^7.0.0"}
        }
        
        for feature, enabled in requirements["features"].items():
            if enabled and feature in feature_deps:
                deps.update(feature_deps[feature])
        
        return deps 