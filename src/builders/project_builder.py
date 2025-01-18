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
            
            # Create source files
            await self._create_source_files(project_path, config)
            
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
            with open(project_path / 'tsconfig.json', 'w', encoding='utf-8') as f:
                json.dump(tsconfig, f, indent=2)
        
        if configs.get('.eslintrc.js'):
            eslint_config = """module.exports = {
  extends: ['next/core-web-vitals', 'prettier'],
  rules: {
    // Add custom rules here
  },
};
"""
            with open(project_path / '.eslintrc.js', 'w', encoding='utf-8') as f:
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
            with open(project_path / '.prettierrc', 'w', encoding='utf-8') as f:
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
            with open(project_path / '.gitignore', 'w', encoding='utf-8') as f:
                f.write(gitignore_content)
        
        if configs.get('.env.example'):
            env_example = """# Environment variables
NEXT_PUBLIC_API_URL=http://localhost:3000/api
"""
            with open(project_path / '.env.example', 'w', encoding='utf-8') as f:
                f.write(env_example)
        
        if configs.get('next.config.js'):
            next_config = """/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Add custom config here
}

module.exports = nextConfig
"""
            with open(project_path / 'next.config.js', 'w', encoding='utf-8') as f:
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
        
        with open(project_path / 'package.json', 'w', encoding='utf-8') as f:
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
        
        with open(project_path / 'README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content) 

    async def _create_source_files(self, project_path: Path, config: ProjectConfig) -> None:
        """Create source files for the project"""
        src_dir = project_path / "src"
        src_dir.mkdir(exist_ok=True)
        
        # Create types directory and base types
        types_dir = src_dir / "types"
        types_dir.mkdir(exist_ok=True)
        
        # Create base types
        base_types = """// Common types used across the application
export interface User {
  id: string;
  name: string;
  email: string;
  image?: string;
  role: 'user' | 'admin';
}

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: 'success' | 'error';
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  total: number;
  page: number;
  pageSize: number;
}

export interface Theme {
  mode: 'light' | 'dark';
  primary: string;
  secondary: string;
  background: string;
  text: string;
}
"""
        with open(types_dir / "index.ts", 'w') as f:
            f.write(base_types)
        
        # Create utils directory with helper functions
        utils_dir = src_dir / "utils"
        utils_dir.mkdir(exist_ok=True)
        
        # API client utility
        api_client = """import axios from 'axios';
import { ApiResponse } from '@/types';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for authentication
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const api = {
  get: async <T>(url: string): Promise<ApiResponse<T>> => {
    try {
      const response = await apiClient.get<ApiResponse<T>>(url);
      return response.data;
    } catch (error) {
      return { status: 'error', error: error.message };
    }
  },
  
  post: async <T>(url: string, data: any): Promise<ApiResponse<T>> => {
    try {
      const response = await apiClient.post<ApiResponse<T>>(url, data);
      return response.data;
    } catch (error) {
      return { status: 'error', error: error.message };
    }
  },
  
  // Add other methods as needed
};

export default api;
"""
        with open(utils_dir / "api.ts", 'w') as f:
            f.write(api_client)
        
        # Create hooks directory with custom hooks
        hooks_dir = src_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)
        
        use_auth = """import { useState, useEffect } from 'react';
import { User } from '@/types';
import api from '@/utils/api';

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const response = await api.get<User>('/api/auth/user');
      if (response.status === 'success' && response.data) {
        setUser(response.data);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    try {
      const response = await api.post<{ token: string; user: User }>('/api/auth/login', {
        email,
        password,
      });
      
      if (response.status === 'success' && response.data) {
        localStorage.setItem('token', response.data.token);
        setUser(response.data.user);
      }
      
      return response;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return { user, loading, error, login, logout };
}
"""
        with open(hooks_dir / "useAuth.ts", 'w') as f:
            f.write(use_auth)
        
        # Create components with proper structure
        components_dir = src_dir / "components"
        components_dir.mkdir(exist_ok=True)
        
        # Layout components
        layout_dir = components_dir / "layout"
        layout_dir.mkdir(exist_ok=True)
        
        layout_component = """import { ReactNode } from 'react';
import { Navbar } from './Navbar';
import { Footer } from './Footer';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>
      <Footer />
    </div>
  );
}
"""
        with open(layout_dir / "Layout.tsx", 'w') as f:
            f.write(layout_component)
        
        # Create Navbar component
        navbar_component = """import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { useTheme } from '@/contexts/ThemeContext';

export function Navbar() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  return (
    <nav className="bg-white dark:bg-gray-800 shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="text-xl font-bold text-gray-800 dark:text-white">
            {config.name}
          </Link>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700"
              aria-label="Toggle theme"
            >
              {theme.mode === 'light' ? 'Dark' : 'Light'}
            </button>
            
            {user ? (
              <div className="flex items-center space-x-4">
                <span className="text-gray-600 dark:text-gray-300">{user.name}</span>
                <button
                  onClick={logout}
                  className="btn-secondary"
                >
                  Logout
                </button>
              </div>
            ) : (
              <Link href="/login" className="btn-primary">
                Login
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
"""
        with open(layout_dir / "Navbar.tsx", 'w', encoding='utf-8') as f:
            f.write(navbar_component)

        # Create Footer component
        footer_component = """export function Footer() {
  return (
    <footer className="bg-white dark:bg-gray-800 shadow-md mt-8">
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-between items-center">
          <p className="text-gray-600 dark:text-gray-300">
            © {new Date().getFullYear()} {config.name}. All rights reserved.
          </p>
          <div className="flex space-x-4">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white"
            >
              GitHub
            </a>
            <a
              href="/docs"
              className="text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-white"
            >
              Documentation
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
"""
        with open(layout_dir / "Footer.tsx", 'w', encoding='utf-8') as f:
            f.write(footer_component)

        # Create pages directory and files
        pages_dir = src_dir / "pages"
        pages_dir.mkdir(exist_ok=True)
        
        # Enhanced _app.tsx with proper setup
        app_content = """import '@/styles/globals.css';
import type { AppProps } from 'next/app';
import { Layout } from '@/components/layout/Layout';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { AuthProvider } from '@/contexts/AuthContext';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Layout>
          <Component {...pageProps} />
        </Layout>
      </AuthProvider>
    </ThemeProvider>
  );
}
"""
        with open(pages_dir / "_app.tsx", 'w') as f:
            f.write(app_content)
        
        # Enhanced index page
        index_content = """import { NextPage } from 'next';
import Head from 'next/head';
import { useAuth } from '@/hooks/useAuth';
import styles from '@/styles/Home.module.css';

const Home: NextPage = () => {
  const { user } = useAuth();

  return (
    <>
      <Head>
        <title>{config.name}</title>
        <meta name="description" content="Generated by Auto Agent" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <main className={styles.main}>
        <h1 className="text-4xl font-bold mb-8">
          Welcome to {config.name}
          {user && <span className="text-2xl ml-2">👋 {user.name}</span>}
        </h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Add your content here */}
        </div>
      </main>
    </>
  );
};

export default Home;
"""
        with open(pages_dir / "index.tsx", 'w') as f:
            f.write(index_content)
        
        # Create API routes with proper error handling
        api_dir = pages_dir / "api"
        api_dir.mkdir(exist_ok=True)
        
        # Add more sophisticated API endpoint
        api_utils = """import { NextApiRequest, NextApiResponse } from 'next';
import { ApiResponse } from '@/types';

export function withErrorHandler(
  handler: (req: NextApiRequest, res: NextApiResponse<ApiResponse>) => Promise<void>
) {
  return async (req: NextApiRequest, res: NextApiResponse<ApiResponse>) => {
    try {
      await handler(req, res);
    } catch (error) {
      console.error(error);
      res.status(500).json({
        status: 'error',
        error: 'Internal server error',
      });
    }
  };
}

export function withAuth(
  handler: (req: NextApiRequest, res: NextApiResponse<ApiResponse>) => Promise<void>
) {
  return async (req: NextApiRequest, res: NextApiResponse<ApiResponse>) => {
    const token = req.headers.authorization?.split(' ')[1];
    
    if (!token) {
      return res.status(401).json({
        status: 'error',
        error: 'Unauthorized',
      });
    }
    
    try {
      // Verify token here
      await handler(req, res);
    } catch (error) {
      console.error(error);
      res.status(500).json({
        status: 'error',
        error: 'Internal server error',
      });
    }
  };
}
"""
        with open(api_dir / "_utils.ts", 'w') as f:
            f.write(api_utils)
        
        # Create styles with Tailwind configuration
        styles_dir = src_dir / "styles"
        styles_dir.mkdir(exist_ok=True)
        
        globals_css = """@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --foreground-rgb: 0, 0, 0;
  --background-start-rgb: 214, 219, 220;
  --background-end-rgb: 255, 255, 255;
}

@media (prefers-color-scheme: dark) {
  :root {
    --foreground-rgb: 255, 255, 255;
    --background-start-rgb: 0, 0, 0;
    --background-end-rgb: 0, 0, 0;
  }
}

@layer base {
  body {
    @apply text-gray-900 dark:text-gray-100;
    background: linear-gradient(
      to bottom,
      transparent,
      rgb(var(--background-end-rgb))
    )
    rgb(var(--background-start-rgb));
  }
  
  h1 {
    @apply text-4xl font-bold mb-4;
  }
  
  h2 {
    @apply text-3xl font-semibold mb-3;
  }
  
  h3 {
    @apply text-2xl font-medium mb-2;
  }
}

@layer components {
  .btn {
    @apply px-4 py-2 rounded-md font-medium transition-colors;
  }
  
  .btn-primary {
    @apply btn bg-blue-600 text-white hover:bg-blue-700;
  }
  
  .btn-secondary {
    @apply btn bg-gray-200 text-gray-800 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-200;
  }
  
  .input {
    @apply px-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:border-gray-700;
  }
}
"""
        with open(styles_dir / "globals.css", 'w') as f:
            f.write(globals_css)

        # Create Home.module.css
        home_styles = """.main {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: center;
  padding: 6rem;
  min-height: 100vh;
}

.description {
  display: inherit;
  justify-content: inherit;
  align-items: inherit;
  font-size: 0.85rem;
  max-width: var(--max-width);
  width: 100%;
  z-index: 2;
  font-family: var(--font-mono);
}

.grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(25%, auto));
  max-width: 100%;
  width: var(--max-width);
}

.card {
  padding: 1rem 1.2rem;
  border-radius: var(--border-radius);
  background: rgba(var(--card-rgb), 0);
  border: 1px solid rgba(var(--card-border-rgb), 0);
  transition: background 200ms, border 200ms;
}

.card span {
  display: inline-block;
  transition: transform 200ms;
}

.card h2 {
  font-weight: 600;
  margin-bottom: 0.7rem;
}

.card p {
  margin: 0;
  opacity: 0.6;
  font-size: 0.9rem;
  line-height: 1.5;
  max-width: 30ch;
}
"""
        with open(styles_dir / "Home.module.css", 'w') as f:
            f.write(home_styles)

        # Create contexts directory for state management
        contexts_dir = src_dir / "contexts"
        contexts_dir.mkdir(exist_ok=True)
        
        # Create ThemeContext
        theme_context = """import { createContext, useContext, useState, ReactNode } from 'react';
import { Theme } from '@/types';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const lightTheme: Theme = {
  mode: 'light',
  primary: '#3B82F6',
  secondary: '#6B7280',
  background: '#FFFFFF',
  text: '#111827',
};

const darkTheme: Theme = {
  mode: 'dark',
  primary: '#60A5FA',
  secondary: '#9CA3AF',
  background: '#111827',
  text: '#FFFFFF',
};

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(lightTheme);

  const toggleTheme = () => {
    setTheme(theme.mode === 'light' ? darkTheme : lightTheme);
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
"""
        with open(contexts_dir / "ThemeContext.tsx", 'w') as f:
            f.write(theme_context)
        
        # Create services directory for API calls
        services_dir = src_dir / "services"
        services_dir.mkdir(exist_ok=True)
        
        # Create public directory for assets
        public_dir = project_path / "public"
        public_dir.mkdir(exist_ok=True)
        
        # Create tests directory
        tests_dir = project_path / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        # Create Jest setup
        jest_setup = """import '@testing-library/jest-dom';
"""
        with open(tests_dir / "jest.setup.ts", 'w') as f:
            f.write(jest_setup) 

    async def create_file(self, file_path: str, description: str) -> None:
        """Create a new file with generated code based on description"""
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate code based on file type and description
            code = await self._generate_code_for_file(file_path, description)
            
            with open(file_path, 'w') as f:
                f.write(code)
                
            logger.info(f"Created file: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to create file {file_path}: {str(e)}")
            raise ValueError(f"Failed to create file: {str(e)}")

    async def modify_file(self, file_path: str, element: str, description: str) -> None:
        """Modify an existing file based on description"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise ValueError(f"File does not exist: {file_path}")
            
            # Read existing content
            with open(file_path) as f:
                content = f.read()
            
            # Generate and apply modifications
            modified_content = await self._modify_code(content, element, description)
            
            # Write back to file
            with open(file_path, 'w') as f:
                f.write(modified_content)
                
            logger.info(f"Modified file: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to modify file {file_path}: {str(e)}")
            raise ValueError(f"Failed to modify file: {str(e)}")

    async def generate_code_block(self, block_info: dict) -> str:
        """Generate a code block based on description"""
        try:
            block_type = block_info["type"]
            name = block_info["name"]
            description = block_info["description"]
            
            # Generate code based on block type
            if block_type == "function":
                return await self._generate_function(name, description)
            elif block_type == "class":
                return await self._generate_class(name, description)
            elif block_type == "interface":
                return await self._generate_interface(name, description)
            else:
                raise ValueError(f"Unsupported block type: {block_type}")
                
        except Exception as e:
            logger.error(f"Failed to generate code block: {str(e)}")
            raise ValueError(f"Failed to generate code block: {str(e)}")

    async def create_component(self, component_info: dict) -> None:
        """Create a new component based on description"""
        try:
            name = component_info["name"]
            description = component_info["description"]
            
            # Determine component type and path
            component_path = self._get_component_path(name)
            
            # Generate component code
            code = await self._generate_component_code(name, description)
            
            # Create component file
            component_path.parent.mkdir(parents=True, exist_ok=True)
            with open(component_path, 'w') as f:
                f.write(code)
                
            # Create associated test file
            test_code = await self._generate_component_test(name)
            test_path = Path(str(component_path).replace('/src/', '/tests/'))
            test_path.parent.mkdir(parents=True, exist_ok=True)
            with open(test_path, 'w') as f:
                f.write(test_code)
                
            logger.info(f"Created component: {component_path}")
            
        except Exception as e:
            logger.error(f"Failed to create component: {str(e)}")
            raise ValueError(f"Failed to create component: {str(e)}")

    async def create_api_endpoint(self, endpoint_info: str) -> None:
        """Create a new API endpoint based on description"""
        try:
            # Parse endpoint information
            endpoint_path = self._get_api_path(endpoint_info)
            
            # Generate API code
            code = await self._generate_api_code(endpoint_info)
            
            # Create API file
            endpoint_path.parent.mkdir(parents=True, exist_ok=True)
            with open(endpoint_path, 'w') as f:
                f.write(code)
                
            logger.info(f"Created API endpoint: {endpoint_path}")
            
        except Exception as e:
            logger.error(f"Failed to create API endpoint: {str(e)}")
            raise ValueError(f"Failed to create API endpoint: {str(e)}")

    async def setup_database(self, db_info: dict) -> None:
        """Set up database configuration and models"""
        try:
            db_type = db_info["type"]
            models = db_info.get("models", [])
            
            # Create database configuration
            config_code = await self._generate_db_config(db_type)
            config_path = Path("src/config/database.ts")
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w') as f:
                f.write(config_code)
            
            # Create models
            for model in models:
                model_code = await self._generate_model(model, db_type)
                model_path = Path(f"src/models/{model}.ts")
                model_path.parent.mkdir(parents=True, exist_ok=True)
                with open(model_path, 'w') as f:
                    f.write(model_code)
                
            logger.info(f"Set up database with type: {db_type}")
            
        except Exception as e:
            logger.error(f"Failed to set up database: {str(e)}")
            raise ValueError(f"Failed to set up database: {str(e)}")

    def _get_component_path(self, name: str) -> Path:
        """Determine the appropriate path for a component"""
        # Convert name to PascalCase for component
        component_name = "".join(word.capitalize() for word in name.split("-"))
        return Path(f"src/components/{component_name}/{component_name}.tsx")

    def _get_api_path(self, endpoint: str) -> Path:
        """Determine the appropriate path for an API endpoint"""
        # Convert endpoint description to path
        endpoint_path = endpoint.lower().replace(" ", "-")
        return Path(f"src/pages/api/{endpoint_path}.ts")

    async def _generate_code_for_file(self, file_path: Path, description: str) -> str:
        """Generate code for a new file based on its type and description"""
        file_type = file_path.suffix
        
        if file_type in ['.tsx', '.jsx']:
            return await self._generate_react_code(file_path.stem, description)
        elif file_type == '.ts':
            return await self._generate_typescript_code(file_path.stem, description)
        elif file_type == '.js':
            return await self._generate_javascript_code(file_path.stem, description)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    async def _modify_code(self, content: str, element: str, description: str) -> str:
        """Modify existing code based on description"""
        # This would be where you implement the logic to modify existing code
        # For now, we'll raise an error
        raise NotImplementedError("Code modification not yet implemented")

    async def _generate_function(self, name: str, description: str) -> str:
        """Generate a function based on description"""
        # This would be where you implement the logic to generate function code
        # For now, we'll raise an error
        raise NotImplementedError("Function generation not yet implemented")

    async def _generate_class(self, name: str, description: str) -> str:
        """Generate a class based on description"""
        # This would be where you implement the logic to generate class code
        # For now, we'll raise an error
        raise NotImplementedError("Class generation not yet implemented")

    async def _generate_interface(self, name: str, description: str) -> str:
        """Generate an interface based on description"""
        # This would be where you implement the logic to generate interface code
        # For now, we'll raise an error
        raise NotImplementedError("Interface generation not yet implemented")

    async def _generate_component_code(self, name: str, description: str) -> str:
        """Generate React component code based on description"""
        # Convert name to PascalCase for component
        component_name = "".join(word.capitalize() for word in name.split("-"))
        
        # Analyze description for features
        has_state = any(word in description.lower() for word in ["state", "data", "value", "counter", "toggle"])
        has_effects = any(word in description.lower() for word in ["fetch", "load", "update", "subscribe"])
        has_router = any(word in description.lower() for word in ["route", "navigation", "link", "redirect"])
        has_form = "form" in description.lower()
        
        # Generate imports
        imports = ['import React from "react"']
        if has_state:
            imports.append('import { useState } from "react"')
        if has_effects:
            imports.append('import { useEffect } from "react"')
        if has_router:
            imports.append('import { useRouter } from "next/router"')
            imports.append(f'import styles from "./{component_name}.module.css"')
        
        # Join imports with newlines before the f-string
        imports_text = "\n".join(imports)
        code = f"""// {component_name} Component
{imports_text}

interface {component_name}Props {{
  title?: string;
  className?: string;
  children?: React.ReactNode;
}}

export function {component_name}({{ title, className, children }}: {component_name}Props) {{
"""

        # Add state if needed
        if has_state:
            code += """  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

"""

        # Add effects if needed
        if has_effects:
            code += """  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Add fetch logic here
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

"""

        # Add form handlers if needed
        if has_form:
            code += """  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    // Add form submission logic here
  };

"""

        # Generate JSX
        code += """  return (
    <div className={`${styles.container} ${className || ''}`}>
"""

        if "title" in description.lower():
            code += "      <h1 className={styles.title}>{title}</h1>\n"

        if has_state:
            code += """      {loading && <div className={styles.loading}>Loading...</div>}
      {error && <div className={styles.error}>{error}</div>}
      {data && (
        <div className={styles.content}>
          {/* Add data rendering logic here */}
        </div>
      )}
"""

        if has_form:
            code += """      <form onSubmit={handleSubmit} className={styles.form}>
        <input
          type="text"
          className={styles.input}
          // Add form fields here
        />
        <button type="submit" className={styles.button}>
          Submit
        </button>
      </form>
"""

        code += """      {children}
    </div>
  );
}
"""

        return code

    async def build_project(self, config: ProjectConfig, requirements: dict) -> None:
        """Build a new project with the given configuration and requirements"""
        try:
            # Create project directory path from project_location and name
            project_path = Path(config.project_location) / config.name
            
            # Initialize project structure
            await self.initialize_project(config, requirements, project_path)
            
            # Initialize git repository
            try:
                subprocess.run(['git', 'init'], cwd=project_path, check=True)
                logger.info("Initialized git repository")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to initialize git repository: {str(e)}")
            
            # Install dependencies
            try:
                subprocess.run(['npm', 'install'], cwd=project_path, check=True)
                logger.info("Installed dependencies")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install dependencies: {str(e)}")
                raise ValueError("Failed to install dependencies")
            
            # Create initial commit
            try:
                subprocess.run(['git', 'add', '.'], cwd=project_path, check=True)
                subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=project_path, check=True)
                logger.info("Created initial commit")
            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to create initial commit: {str(e)}")
            
            logger.info(f"Successfully built project at {project_path}")
            
        except Exception as e:
            logger.error(f"Failed to build project: {str(e)}")
            raise ValueError(f"Failed to build project: {str(e)}") 