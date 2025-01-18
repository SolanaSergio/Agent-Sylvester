import asyncio
from pathlib import Path
import subprocess
from typing import Dict, List, Optional
import json
import shutil
import logging
from src.utils.types import ProjectConfig

# Set up logging
logger = logging.getLogger(__name__)

class ProjectBuilder:
    """Builds and manages project structure"""
    
    def __init__(self):
        self.config: Optional[ProjectConfig] = None
        self.requirements: Dict = {}

    async def initialize_project(self, config: ProjectConfig, requirements: dict, project_path: Path) -> None:
        """Initialize a new project with the given configuration"""
        try:
            # Create project structure based on requirements
            structure = requirements.get('structure', {})
            
            # Create src directory and its subdirectories
            if 'src' in structure:
                src_dir = project_path / 'src'
                src_dir.mkdir(exist_ok=True)
                
                # Create component directories
                if 'components' in structure['src']:
                    components_dir = src_dir / 'components'
                    components_dir.mkdir(exist_ok=True)
                    
                    # Create component subdirectories
                    for component_type in structure['src']['components']:
                        (components_dir / component_type).mkdir(exist_ok=True)
                
                # Create other src subdirectories
                for dirname in ['pages', 'styles', 'utils', 'hooks', 'services', 'types']:
                    if structure['src'].get(dirname, False):
                        (src_dir / dirname).mkdir(exist_ok=True)
            
            # Create public directory
            if structure.get('public', False):
                (project_path / 'public').mkdir(exist_ok=True)
            
            # Create docs directory
            if structure.get('docs', False):
                (project_path / 'docs').mkdir(exist_ok=True)
            
            # Create tests directory
            if structure.get('tests', False):
                (project_path / 'tests').mkdir(exist_ok=True)
            
            # Create configuration files
            if 'configurations' in requirements:
                await self._create_config_files(project_path, config, requirements)
            
            # Create package.json
            await self._create_package_json(project_path, config, requirements)
            
            # Create README.md
            await self._create_readme(project_path, config)
            
        except Exception as e:
            logger.error(f"Failed to initialize project structure: {str(e)}")
            raise ValueError(f"Failed to initialize project structure: {str(e)}")

    async def _create_config_files(self, project_path: Path, config: ProjectConfig, requirements: dict) -> None:
        """Create configuration files for the project"""
        configs = requirements.get('configurations', {})
        
        if configs.get('tsconfig.json'):
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
                    "incremental": True,
                    "baseUrl": ".",
                    "paths": {
                        "@/*": ["./src/*"]
                    }
                },
                "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
                "exclude": ["node_modules"]
            }
            with open(project_path / 'tsconfig.json', 'w') as f:
                json.dump(tsconfig, f, indent=2)
        
        if configs.get('.eslintrc.js'):
            eslint_config = """module.exports = {
  extends: ['next/core-web-vitals', 'prettier'],
  rules: {
    // Add custom rules here
  },
};
"""
            with open(project_path / '.eslintrc.js', 'w') as f:
                f.write(eslint_config)
        
        if configs.get('.prettierrc'):
            prettier_config = {
                "semi": True,
                "trailingComma": "es5",
                "singleQuote": True,
                "printWidth": 100,
                "tabWidth": 2,
                "useTabs": False
            }
            with open(project_path / '.prettierrc', 'w') as f:
                json.dump(prettier_config, f, indent=2)
        
        if configs.get('.gitignore'):
            gitignore_content = """# dependencies
/node_modules
/.pnp
.pnp.js

# testing
/coverage

# next.js
/.next/
/out/

# production
/build

# misc
.DS_Store
*.pem

# debug
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# local env files
.env*.local
.env

# vercel
.vercel

# typescript
*.tsbuildinfo
next-env.d.ts
"""
            with open(project_path / '.gitignore', 'w') as f:
                f.write(gitignore_content)
        
        if configs.get('.env.example'):
            env_example = """# Environment variables
NEXT_PUBLIC_API_URL=http://localhost:3000/api
"""
            with open(project_path / '.env.example', 'w') as f:
                f.write(env_example)
        
        if configs.get('next.config.js'):
            next_config = """/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Add custom config here
}

module.exports = nextConfig
"""
            with open(project_path / 'next.config.js', 'w') as f:
                f.write(next_config)

    async def _create_package_json(self, project_path: Path, config: ProjectConfig, requirements: dict) -> None:
        """Create package.json file"""
        package_json = {
            "name": config.name,
            "version": "0.1.0",
            "private": True,
            "scripts": requirements.get('scripts', {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint"
            }),
            "dependencies": requirements.get('dependencies', {}),
            "devDependencies": requirements.get('devDependencies', {})
        }
        
        with open(project_path / 'package.json', 'w') as f:
            json.dump(package_json, f, indent=2)

    async def _create_readme(self, project_path: Path, config: ProjectConfig) -> None:
        """Create README.md file"""
        readme_content = f"""# {config.name}

This is a {config.project_type} project using {config.framework}.

## Getting Started

First, install the dependencies:

```bash
npm install
# or
yarn install
```

Then, run the development server:

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Features

{', '.join(config.features)}

## Learn More

To learn more about the technologies used in this project, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://reactjs.org/docs)
"""
        
        with open(project_path / 'README.md', 'w') as f:
            f.write(readme_content) 