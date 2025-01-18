from pathlib import Path
import json
import logging
from typing import Dict, Optional
import os

class ConfigManager:
    """Manages project configuration and environment setup"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.config_dir = project_dir / ".config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def setup_project_config(self, requirements: Dict):
        """Setup project configuration based on requirements"""
        try:
            # Create necessary config files
            self._create_env_files()
            self._create_tsconfig()
            self._create_eslint_config()
            self._create_prettier_config()
            
            # Setup environment variables
            self._setup_environment_vars(requirements)
            
        except Exception as e:
            logging.error(f"Error setting up project config: {str(e)}")
            
    def _create_env_files(self):
        """Create environment files"""
        env_template = """
# Application
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Authentication
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key

# API Keys
NEXT_PUBLIC_API_KEY=your-api-key
"""
        # Create .env.example
        with open(self.project_dir / ".env.example", 'w') as f:
            f.write(env_template)
            
        # Create .env.local if it doesn't exist
        env_local = self.project_dir / ".env.local"
        if not env_local.exists():
            with open(env_local, 'w') as f:
                f.write(env_template)
                
    def _create_tsconfig(self):
        """Create TypeScript configuration"""
        tsconfig = '''{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}'''
        with open(self.project_dir / "tsconfig.json", 'w') as f:
            f.write(tsconfig)
            
    def _create_eslint_config(self):
        """Create ESLint configuration"""
        eslint_config = '''{
  "extends": [
    "next/core-web-vitals",
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint"],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "warn",
    "no-console": ["warn", { "allow": ["warn", "error"] }]
  }
}'''
        with open(self.project_dir / ".eslintrc.json", 'w') as f:
            f.write(eslint_config)
            
    def _create_prettier_config(self):
        """Create Prettier configuration"""
        prettier_config = '''{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "tabWidth": 2,
  "useTabs": false
}'''
        with open(self.project_dir / ".prettierrc", 'w') as f:
            f.write(prettier_config)
            
    def _setup_environment_vars(self, requirements: Dict):
        """Setup environment variables"""
        env_template = """# Application
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Database
DATABASE_URL="postgresql://user:password@localhost:5432/dbname"

# Authentication
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key-at-least-32-chars
JWT_SECRET=your-jwt-secret-key-at-least-32-chars

# API Keys
NEXT_PUBLIC_API_KEY=your-api-key

# Email (optional)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Feature Flags
NEXT_PUBLIC_ENABLE_FEATURE_X=false
NEXT_PUBLIC_ENABLE_FEATURE_Y=false"""

        # Create .env.example
        with open(self.project_dir / ".env.example", 'w') as f:
            f.write(env_template)
            
        # Create .env.local if it doesn't exist
        env_local = self.project_dir / ".env.local"
        if not env_local.exists():
            with open(env_local, 'w') as f:
                f.write(env_template)
                
        # Create .env.test for testing environment
        env_test = """# Test Environment
DATABASE_URL="postgresql://user:password@localhost:5432/test_db"
JWT_SECRET=test-jwt-secret
NEXTAUTH_SECRET=test-nextauth-secret
NEXT_PUBLIC_API_URL=http://localhost:3000/api"""
        
        with open(self.project_dir / ".env.test", 'w') as f:
            f.write(env_test)
            
    def setup_build_config(self):
        """Setup build configuration"""
        # Create next.config.js
        next_config = '''/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  images: {
    domains: ['example.com'],
  },
  webpack: (config, { dev, isServer }) => {
    // Add custom webpack config here
    return config;
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

module.exports = nextConfig;'''
        
        with open(self.project_dir / "next.config.js", 'w') as f:
            f.write(next_config)
            
        # Create package.json scripts
        package_json = '''{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "format": "prettier --write .",
    "type-check": "tsc --noEmit",
    "prepare": "husky install"
  }
}'''
        
        # Update existing package.json or create new one
        try:
            with open(self.project_dir / "package.json", 'r') as f:
                existing_package = json.load(f)
                
            existing_package.setdefault('scripts', {})
            existing_package['scripts'].update(json.loads(package_json)['scripts'])
            
            with open(self.project_dir / "package.json", 'w') as f:
                json.dump(existing_package, f, indent=2)
        except FileNotFoundError:
            with open(self.project_dir / "package.json", 'w') as f:
                f.write(package_json)
                
    def setup_git_hooks(self):
        """Setup Git hooks for code quality"""
        # Create .husky directory
        husky_dir = self.project_dir / ".husky"
        husky_dir.mkdir(exist_ok=True)
        
        # Create pre-commit hook
        pre_commit = '''#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npm run lint
npm run type-check'''
        
        with open(husky_dir / "pre-commit", 'w') as f:
            f.write(pre_commit)
            
        # Make pre-commit hook executable
        import os
        os.chmod(husky_dir / "pre-commit", 0o755)
        
        # Create commit-msg hook for conventional commits
        commit_msg = '''#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

npx --no -- commitlint --edit $1'''
        
        with open(husky_dir / "commit-msg", 'w') as f:
            f.write(commit_msg)
            
        # Make commit-msg hook executable
        os.chmod(husky_dir / "commit-msg", 0o755)
        
        # Create commitlint config
        commitlint_config = '''module.exports = {
  extends: ['@commitlint/config-conventional'],
};'''
        
        with open(self.project_dir / "commitlint.config.js", 'w') as f:
            f.write(commitlint_config)

    async def cleanup(self):
        """Cleanup any temporary configuration files"""
        try:
            # Remove any temporary config files
            temp_config = self.config_dir / "temp"
            if temp_config.exists():
                import shutil
                shutil.rmtree(temp_config)
        except Exception as e:
            logging.error(f"Error cleaning up config manager: {str(e)}") 