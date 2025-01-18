from pathlib import Path
from typing import Dict, List
import os
import json
import shutil
import subprocess
import logging

class ProjectBuilder:
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.root_path.mkdir(parents=True, exist_ok=True)
        
    async def create_project(self, requirements: Dict) -> Path:
        """Create a new project with the specified requirements"""
        project_name = self._generate_project_name(requirements)
        project_dir = self.root_path / project_name
        
        try:
            # Create project using appropriate template
            project_type = requirements.get('project_type', 'next.js')
            if project_type == 'next.js':
                await self._create_nextjs_project(project_dir, requirements)
            else:
                await self._create_react_project(project_dir, requirements)
                
            # Setup project structure
            await self._setup_project_structure(project_dir, requirements)
            
            # Add styling configuration
            await self._setup_styling(project_dir, requirements.get('styling', {}))
            
            # Update package.json with dependencies
            await self._update_dependencies(project_dir, requirements.get('dependencies', {}))
            
            # Setup environment variables
            await self._setup_env_vars(project_dir, requirements)
            
            # Initialize git repository
            await self._initialize_git(project_dir)
            
            return project_dir
            
        except Exception as e:
            logging.error(f"Error creating project: {str(e)}")
            if project_dir.exists():
                shutil.rmtree(project_dir)
            raise
            
    def _generate_project_name(self, requirements: Dict) -> str:
        """Generate a suitable project name from requirements"""
        if 'name' in requirements:
            return requirements['name'].lower().replace(' ', '-')
            
        project_type = requirements.get('project_type', 'app')
        features = requirements.get('features', [])
        
        if 'api' in features:
            prefix = 'api'
        elif 'dashboard' in project_type:
            prefix = 'dashboard'
        elif 'static' in project_type:
            prefix = 'site'
        else:
            prefix = 'app'
            
        # Add a timestamp to ensure uniqueness
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        return f"{prefix}-{timestamp}"
            
    async def _create_nextjs_project(self, project_dir: Path, requirements: Dict):
        """Create a Next.js project"""
        try:
            # Create Next.js project with TypeScript and other features
            subprocess.run([
                'npx',
                'create-next-app@latest',
                str(project_dir),
                '--typescript',
                '--tailwind',
                '--eslint',
                '--app',
                '--src-dir',
                '--import-alias', '@/*'
            ], check=True)
            
            # Add additional configurations
            await self._setup_nextjs_config(project_dir, requirements)
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Error creating Next.js project: {str(e)}")
            raise
            
    async def _create_react_project(self, project_dir: Path, requirements: Dict):
        """Create a React project"""
        try:
            # Create React project with TypeScript
            subprocess.run([
                'npx',
                'create-react-app',
                str(project_dir),
                '--template', 'typescript'
            ], check=True)
            
            # Add additional configurations
            await self._setup_react_config(project_dir, requirements)
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Error creating React project: {str(e)}")
            raise
            
    async def _setup_project_structure(self, project_dir: Path, requirements: Dict):
        """Setup project directory structure"""
        # Create standard directories
        directories = [
            'src/components',
            'src/layouts',
            'src/hooks',
            'src/utils',
            'src/types',
            'src/styles',
            'src/assets',
            'src/constants',
            'public'
        ]
        
        # Add feature-specific directories
        features = requirements.get('features', [])
        if 'api' in features:
            directories.extend([
                'src/api',
                'src/services',
                'src/middleware'
            ])
            
        if 'authentication' in features:
            directories.extend([
                'src/auth',
                'src/context'
            ])
            
        if 'database' in features:
            directories.extend([
                'src/models',
                'src/migrations',
                'prisma'
            ])
            
        # Create all directories
        for directory in directories:
            (project_dir / directory).mkdir(parents=True, exist_ok=True)
            
        # Create necessary files
        await self._create_base_files(project_dir, requirements)
            
    async def _setup_styling(self, project_dir: Path, styling: Dict):
        """Setup styling configuration"""
        try:
            if styling.get('tailwind'):
                # Install and configure Tailwind CSS
                subprocess.run(['npm', 'install', '-D', 'tailwindcss', 'postcss', 'autoprefixer'],
                             cwd=project_dir, check=True)
                subprocess.run(['npx', 'tailwindcss', 'init', '-p'],
                             cwd=project_dir, check=True)
                
            if styling.get('styled_components'):
                # Install and configure styled-components
                subprocess.run(['npm', 'install', 'styled-components', '@types/styled-components'],
                             cwd=project_dir, check=True)
                
            if styling.get('sass'):
                # Install and configure Sass
                subprocess.run(['npm', 'install', '-D', 'sass'],
                             cwd=project_dir, check=True)
                
            # Create base styles
            await self._create_base_styles(project_dir, styling)
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Error setting up styling: {str(e)}")
            raise
            
    async def _update_dependencies(self, project_dir: Path, dependencies: Dict):
        """Update package.json with required dependencies"""
        try:
            package_json_path = project_dir / 'package.json'
            
            with open(package_json_path) as f:
                package_data = json.load(f)
                
            # Update dependencies
            package_data['dependencies'].update(dependencies)
            
            # Add development dependencies
            dev_dependencies = {
                '@typescript-eslint/eslint-plugin': '^5.0.0',
                '@typescript-eslint/parser': '^5.0.0',
                'eslint-config-prettier': '^8.0.0',
                'prettier': '^2.0.0',
                'husky': '^8.0.0',
                'lint-staged': '^13.0.0'
            }
            
            package_data.setdefault('devDependencies', {})
            package_data['devDependencies'].update(dev_dependencies)
            
            # Add scripts
            package_data.setdefault('scripts', {})
            package_data['scripts'].update({
                'format': 'prettier --write .',
                'lint': 'eslint . --ext .ts,.tsx',
                'type-check': 'tsc --noEmit',
                'prepare': 'husky install'
            })
            
            # Write updated package.json
            with open(package_json_path, 'w') as f:
                json.dump(package_data, f, indent=2)
                
            # Install dependencies
            subprocess.run(['npm', 'install'], cwd=project_dir, check=True)
            
        except Exception as e:
            logging.error(f"Error updating dependencies: {str(e)}")
            raise
            
    async def _setup_env_vars(self, project_dir: Path, requirements: Dict):
        """Setup environment variables"""
        try:
            env_vars = {
                'NEXT_PUBLIC_APP_URL': 'http://localhost:3000',
                'NODE_ENV': 'development'
            }
            
            # Add feature-specific env vars
            features = requirements.get('features', [])
            
            if 'database' in features:
                if 'mongodb' in requirements.get('database', '').lower():
                    env_vars['MONGODB_URI'] = 'mongodb://localhost:27017/dbname'
                else:
                    env_vars['DATABASE_URL'] = 'postgresql://user:password@localhost:5432/dbname'
                    
            if 'authentication' in features:
                env_vars.update({
                    'NEXTAUTH_URL': 'http://localhost:3000',
                    'NEXTAUTH_SECRET': 'your-secret-key-min-32-chars',
                    'JWT_SECRET': 'your-jwt-secret-key-min-32-chars'
                })
                
            # Write .env files
            env_content = '\n'.join(f'{k}={v}' for k, v in env_vars.items())
            
            (project_dir / '.env.example').write_text(env_content)
            (project_dir / '.env.local').write_text(env_content)
            (project_dir / '.env.development').write_text(env_content)
            
        except Exception as e:
            logging.error(f"Error setting up environment variables: {str(e)}")
            raise
            
    async def _initialize_git(self, project_dir: Path):
        """Initialize git repository"""
        try:
            # Initialize git
            subprocess.run(['git', 'init'], cwd=project_dir, check=True)
            
            # Create .gitignore
            gitignore_content = '''
# dependencies
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

# vercel
.vercel

# typescript
*.tsbuildinfo
next-env.d.ts
'''
            (project_dir / '.gitignore').write_text(gitignore_content)
            
            # Initial commit
            subprocess.run(['git', 'add', '.'], cwd=project_dir, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=project_dir, check=True)
            
        except subprocess.CalledProcessError as e:
            logging.error(f"Error initializing git: {str(e)}")
            raise
            
    async def _create_base_files(self, project_dir: Path, requirements: Dict):
        """Create base project files"""
        try:
            # Create README.md
            readme_content = f'''
# {project_dir.name}

{requirements.get('description', 'A Next.js project')}

## Features

{self._format_features(requirements.get('features', []))}

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set up environment variables:
   - Copy `.env.example` to `.env.local`
   - Update the variables as needed

3. Run the development server:
   ```bash
   npm run dev
   ```

Open [http://localhost:3000](http://localhost:3000) to view the app.
'''
            (project_dir / 'README.md').write_text(readme_content)
            
            # Create base components
            await self._create_base_components(project_dir, requirements)
            
        except Exception as e:
            logging.error(f"Error creating base files: {str(e)}")
            raise
            
    def _format_features(self, features: List[str]) -> str:
        """Format features list for README"""
        if not features:
            return "- Basic Next.js setup"
            
        return '\n'.join(f"- {feature.title()}" for feature in features)
            
    async def _create_base_components(self, project_dir: Path, requirements: Dict):
        """Create base component files"""
        # This will be handled by the ComponentBuilder
        pass
        
    async def _setup_nextjs_config(self, project_dir: Path, requirements: Dict):
        """Setup Next.js specific configuration"""
        try:
            config_content = '''
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: [],
  },
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,OPTIONS,PATCH,DELETE,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization' },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
'''
            (project_dir / 'next.config.js').write_text(config_content)
            
        except Exception as e:
            logging.error(f"Error setting up Next.js config: {str(e)}")
            raise
            
    async def _setup_react_config(self, project_dir: Path, requirements: Dict):
        """Setup React specific configuration"""
        try:
            # Add React specific configurations
            config_files = {
                'tsconfig.json': '''{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "baseUrl": "src"
  },
  "include": ["src"]
}''',
                '.eslintrc.json': '''{
  "extends": [
    "react-app",
    "react-app/jest",
    "plugin:@typescript-eslint/recommended",
    "prettier"
  ],
  "plugins": ["@typescript-eslint"],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "warn"
  }
}'''
            }
            
            for filename, content in config_files.items():
                (project_dir / filename).write_text(content)
                
        except Exception as e:
            logging.error(f"Error setting up React config: {str(e)}")
            raise
            
    async def setup_version_control(self):
        """Setup version control for the project"""
        # This is handled by _initialize_git
        pass
        
    async def cleanup(self):
        """Cleanup any temporary files"""
        try:
            temp_dir = self.root_path / 'temp'
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")
            raise 