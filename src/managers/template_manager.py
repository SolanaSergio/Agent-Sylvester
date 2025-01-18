from pathlib import Path
import json
import logging
from typing import Dict, Optional
import shutil
import os

class TemplateManager:
    """Manages project templates and boilerplate code"""
    
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._initialize_templates()
        
    def _initialize_templates(self):
        """Initialize basic project templates"""
        templates = {
            'next-app': self._create_next_template,
            'react-app': self._create_react_template,
            'static-site': self._create_static_template
        }
        
        for template_name, creator_func in templates.items():
            template_dir = self.templates_dir / template_name
            if not template_dir.exists():
                creator_func(template_dir)
                
    def get_template(self, project_type: str, requirements: Dict) -> Optional[Path]:
        """Get the appropriate template based on requirements"""
        template_dir = self.templates_dir / project_type
        if not template_dir.exists():
            logging.error(f"Template not found for project type: {project_type}")
            return None
            
        return template_dir
        
    def _create_next_template(self, template_dir: Path):
        """Create Next.js template"""
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # Create directory structure
        (template_dir / "src").mkdir()
        (template_dir / "public").mkdir()
        (template_dir / "styles").mkdir()
        
        # Create base files
        self._create_next_config(template_dir)
        self._create_tsconfig(template_dir)
        self._create_package_json(template_dir, "next-app")
        
    def _create_react_template(self, template_dir: Path):
        """Create React template"""
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # Create directory structure
        (template_dir / "src").mkdir()
        (template_dir / "public").mkdir()
        
        # Create base files
        self._create_react_config(template_dir)
        self._create_tsconfig(template_dir)
        self._create_package_json(template_dir, "react-app")
        
    def _create_static_template(self, template_dir: Path):
        """Create static site template"""
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # Create directory structure
        (template_dir / "src").mkdir()
        (template_dir / "public").mkdir()
        (template_dir / "assets").mkdir()
        
        # Create base files
        self._create_vite_config(template_dir)
        self._create_package_json(template_dir, "static-site")
        
    def _create_next_config(self, template_dir: Path):
        """Create Next.js configuration"""
        config = '''
/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    swcMinify: true,
}

module.exports = nextConfig
'''
        with open(template_dir / "next.config.js", 'w') as f:
            f.write(config)
            
    def _create_react_config(self, template_dir: Path):
        """Create React configuration"""
        config = {
            "name": "react-app",
            "version": "0.1.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            }
        }
        
        with open(template_dir / "package.json", 'w') as f:
            json.dump(config, f, indent=2)
            
    def _create_vite_config(self, template_dir: Path):
        """Create Vite configuration"""
        config = '''
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    server: {
        port: 3000
    }
})
'''
        with open(template_dir / "vite.config.ts", 'w') as f:
            f.write(config)
            
    def _create_package_json(self, template_dir: Path, template_type: str):
        """Create package.json based on template type"""
        base_config = {
            "name": template_type,
            "version": "0.1.0",
            "private": True
        }
        
        if template_type == "next-app":
            base_config.update({
                "scripts": {
                    "dev": "next dev",
                    "build": "next build",
                    "start": "next start",
                    "lint": "next lint"
                }
            })
        elif template_type == "static-site":
            base_config.update({
                "scripts": {
                    "dev": "vite",
                    "build": "vite build",
                    "preview": "vite preview"
                }
            })
            
        with open(template_dir / "package.json", 'w') as f:
            json.dump(base_config, f, indent=2) 