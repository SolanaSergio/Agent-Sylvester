import asyncio
from pathlib import Path
import subprocess
from typing import Dict, List, Optional
import json
import shutil
import logging
from src.utils.types import ProjectConfig
import os
from src.utils.api_manager import APIManager
import aiohttp
import re

# Set up logging
logger = logging.getLogger(__name__)

class ProjectBuilder:
    """Builds and manages project structure"""
    
    def __init__(self):
        self.config: Optional[ProjectConfig] = None
        self.requirements: Dict = {}
        self.api_manager = APIManager()

    async def initialize_project(self, config: ProjectConfig, requirements: dict, project_path: Path) -> None:
        """Initialize a new project with the given configuration"""
        try:
            # Create project structure based on requirements
            structure = requirements.get('structure', {})
            
            # Create base directories
            src_dir = project_path / 'src'
            src_dir.mkdir(exist_ok=True)
            
            # Create essential directories first
            essential_dirs = {
                'hooks': src_dir / 'hooks',
                'contexts': src_dir / 'contexts',
                'components': src_dir / 'components',
                'pages': src_dir / 'pages',
                'styles': src_dir / 'styles'
            }
            
            for dir_name, dir_path in essential_dirs.items():
                dir_path.mkdir(exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
            
            # Create configuration files first
            if 'configurations' in requirements:
                await self._create_config_files(project_path, config, requirements)
                logger.info("Created configuration files")
            
            # Create package.json
            await self._create_package_json(project_path, config, requirements)
            logger.info("Created package.json")
            
            # Create README.md
            await self._create_readme(project_path, config)
            logger.info("Created README.md")
            
            # Create core functionality first
            await self._create_auth_hook(project_path)
            logger.info("Created authentication hook")
            
            await self._create_theme_context(project_path)
            logger.info("Created theme context")
            
            # Verify core dependencies exist before creating components
            auth_hook_path = essential_dirs['hooks'] / 'useAuth.tsx'
            theme_context_path = essential_dirs['contexts'] / 'ThemeContext.tsx'
            
            if not auth_hook_path.exists() or not theme_context_path.exists():
                raise ValueError("Core dependencies missing. Failed to create auth hook or theme context.")
            
            # Now create components that depend on the core functionality
            await self._create_source_files(project_path, config)
            logger.info("Created source files and components")
            
            # Create additional directories if specified
            if structure.get('public', False):
                (project_path / 'public').mkdir(exist_ok=True)
            
            if structure.get('docs', False):
                (project_path / 'docs').mkdir(exist_ok=True)
            
            if structure.get('tests', False):
                (project_path / 'tests').mkdir(exist_ok=True)
            
            logger.info("Project initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize project structure: {str(e)}")
            # Add more context to the error
            if "useAuth" in str(e):
                raise ValueError("Failed to initialize project: Authentication hook not properly created")
            elif "ThemeContext" in str(e):
                raise ValueError("Failed to initialize project: Theme context not properly created")
            else:
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
        # Define core dependencies based on project type
        core_dependencies = {
            "next": "^14.0.0",
            "react": "^18.2.0",
            "react-dom": "^18.2.0"
        }
        
        # Define core dev dependencies
        core_dev_dependencies = {
            "typescript": "^5.0.0",
            "@types/node": "^20.0.0",
            "@types/react": "^18.2.0",
            "@types/react-dom": "^18.2.0",
            "eslint": "^8.0.0",
            "eslint-config-next": "^14.0.0"
        }
        
        # Add styling dependencies based on config
        if config.styling == "tailwind":
            core_dependencies.update({
                "tailwindcss": "^3.3.0",
                "autoprefixer": "^10.0.0",
                "postcss": "^8.0.0"
            })
        elif config.styling == "styled-components":
            core_dependencies["styled-components"] = "^6.0.0"
            core_dev_dependencies["@types/styled-components"] = "^6.0.0"
        
        # Handle additional dependencies from requirements
        if 'dependencies' in requirements:
            core_dependencies.update(requirements['dependencies'])
                
        if 'devDependencies' in requirements:
            core_dev_dependencies.update(requirements['devDependencies'])
        
        package_json = {
            "name": config.name,
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint"
            },
            "dependencies": core_dependencies,
            "devDependencies": core_dev_dependencies
        }
        
        # Write package.json with proper JSON formatting
        with open(project_path / 'package.json', 'w', encoding='utf-8') as f:
            json.dump(package_json, f, indent=2, ensure_ascii=False)

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

    def _get_app_layout_content(self, config: ProjectConfig) -> str:
        """Get content for app layout (_app.tsx)"""
        return """import type { AppProps } from 'next/app';
import { AuthProvider } from '@/hooks/useAuth';
import { ThemeProvider } from '@/contexts/ThemeContext';
import '@/styles/globals.css';

export default function App({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <ThemeProvider>
        <Component {...pageProps} />
      </ThemeProvider>
    </AuthProvider>
  );
}
"""

    async def _create_source_files(self, project_path: Path, config: ProjectConfig) -> None:
        """Create initial source files for the project with custom code based on requirements."""
        try:
            # Extract key features from config description
            description = config.description.lower()
            features = await self._analyze_requirements(description)
            
            # Create hooks directory
            hooks_dir = project_path / 'src' / 'hooks'
            hooks_dir.mkdir(parents=True, exist_ok=True)
            
            # Create custom hooks based on features
            for feature, details in features.items():
                if details['detected']:
                    await self._create_feature_hook(hooks_dir, feature, details['requirements'])
            
            # Create contexts directory
            contexts_dir = project_path / 'src' / 'contexts'
            contexts_dir.mkdir(parents=True, exist_ok=True)
            
            # Create custom contexts based on features
            for feature, details in features.items():
                if details['detected']:
                    await self._create_feature_context(contexts_dir, feature, details['requirements'])
            
            # Create components directory
            components_dir = project_path / 'src' / 'components'
            components_dir.mkdir(parents=True, exist_ok=True)
            
            # Create custom components based on features
            for feature, details in features.items():
                if details['detected']:
                    await self._create_component(
                        name=feature,
                        requirements=details['requirements'],
                        component_dir=components_dir
                    )
            
            # Create pages directory
            pages_dir = project_path / 'src' / 'pages'
            pages_dir.mkdir(parents=True, exist_ok=True)
            
            # Create custom pages based on features
            await self._create_index_page(pages_dir, features)
            await self._create_playlist_pages(pages_dir)
            await self._create_visualizer_page(pages_dir)
            
            logger.info("Created custom source files based on project requirements")
            
        except Exception as e:
            logger.error(f"Failed to create source files: {str(e)}")
            raise

    async def _analyze_requirements(self, description: str) -> dict:
        """Analyze project requirements from description."""
        features = {
            'audio': {
                'detected': any(word in description.lower() for word in ['audio', 'music', 'sound', 'player']),
                'requirements': []
            },
            'playlist': {
                'detected': 'playlist' in description.lower(),
                'requirements': []
            },
            'visualization': {
                'detected': any(word in description.lower() for word in ['visualization', 'visualizer', 'visual']),
                'requirements': []
            }
        }

        # Analyze specific requirements for each feature
        if features['audio']['detected']:
            if 'streaming' in description.lower():
                features['audio']['requirements'].append('streaming')
            if 'upload' in description.lower():
                features['audio']['requirements'].append('file_upload')
            if 'format' in description.lower():
                features['audio']['requirements'].append('format_conversion')

        if features['playlist']['detected']:
            if 'share' in description.lower():
                features['playlist']['requirements'].append('sharing')
            if 'collaborate' in description.lower():
                features['playlist']['requirements'].append('collaboration')
            if 'import' in description.lower():
                features['playlist']['requirements'].append('import')

        if features['visualization']['detected']:
            if 'spectrum' in description.lower():
                features['visualization']['requirements'].append('spectrum')
            if '3d' in description.lower():
                features['visualization']['requirements'].append('3d')
            if 'waveform' in description.lower():
                features['visualization']['requirements'].append('waveform')

        return features

    async def _create_feature_hook(self, hooks_dir: Path, feature: str, requirements: List[str]) -> None:
        """Create custom hook for a specific feature with dynamic implementation."""
        hook_name = f"use{feature.capitalize()}"
        imports = ['import { useState, useEffect }']
        state_vars = []
        effects = []
        methods = []
        
        # Dynamically build hook based on requirements
        for req in requirements:
            hook_details = self._get_hook_implementation(feature, req)
            imports.extend(hook_details.get('imports', []))
            state_vars.extend(hook_details.get('state', []))
            effects.extend(hook_details.get('effects', []))
            methods.extend(hook_details.get('methods', []))

        # Generate hook content
        hook_content = self._generate_hook_content(
            hook_name=hook_name,
            imports=imports,
            state_vars=state_vars,
            effects=effects,
            methods=methods
        )

        await self._write_file(
            os.path.join(hooks_dir, f"{hook_name}.ts"),
            hook_content
        )
        logger.info(f"Created {hook_name} hook")

    def _get_hook_implementation(self, feature: str, requirement: str) -> dict:
        """Get specific implementation details for a hook based on feature and requirement."""
        implementations = {
            'audio': {
                'streaming': {
                    'imports': ['import { useMediaStream } from "@/utils/media"'],
                    'state': [
                        'const [stream, setStream] = useState<MediaStream | null>(null)',
                        'const [error, setError] = useState<string | null>(null)'
                    ],
                    'effects': [
                        '''useEffect(() => {
                            const initStream = async () => {
                                try {
                                    const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                                    setStream(mediaStream);
                                } catch (err) {
                                    setError(err.message);
                                }
                            };
                            initStream();
                            return () => stream?.getTracks().forEach(track => track.stop());
                        }, [])'''
                    ],
                    'methods': []
                },
                'file_upload': {
                    'imports': ['import { uploadFile } from "@/utils/upload"'],
                    'state': ['const [progress, setProgress] = useState(0)'],
                    'methods': [
                        '''const handleUpload = async (file: File) => {
                            try {
                                await uploadFile(file, (progress) => setProgress(progress));
                                return true;
                            } catch (err) {
                                setError(err.message);
                                return false;
                            }
                        }'''
                    ]
                }
            },
            'playlist': {
                'sharing': {
                    'imports': ['import { sharePlaylist } from "@/utils/share"'],
                    'methods': [
                        '''const shareWithUsers = async (playlistId: string, userIds: string[]) => {
                            try {
                                await sharePlaylist(playlistId, userIds);
                                return true;
                            } catch (err) {
                                console.error(err);
                                return false;
                            }
                        }'''
                    ]
                }
            }
            # Add more implementations as needed
        }
        
        return implementations.get(feature, {}).get(requirement, {})

    def _generate_hook_content(self, hook_name: str, imports: List[str], 
                             state_vars: List[str], effects: List[str], 
                             methods: List[str]) -> str:
        """Generate the complete hook content."""
        return f"""// Generated {hook_name} hook
{chr(10).join(imports)}

export function {hook_name}() {{
    {chr(10).join(state_vars)}
    
    {chr(10).join(effects)}
    
    {chr(10).join(methods)}
    
    return {{
        {', '.join(self._extract_return_values(state_vars, methods))}
    }};
}}
"""

    def _extract_return_values(self, state_vars: List[str], methods: List[str]) -> List[str]:
        """Extract return values from state variables and methods."""
        return_values = []
        
        # Extract from state vars
        for var in state_vars:
            if 'useState' in var:
                var_name = var.split('[')[1].split(',')[0].strip()
                return_values.append(var_name)
        
        # Extract from methods
        for method in methods:
            if 'const' in method:
                method_name = method.split('const')[1].split('=')[0].strip()
                return_values.append(method_name)
        
        return return_values

    async def _create_feature_context(self, contexts_dir: Path, feature: str, requirements: List[str]) -> None:
        """Create custom context for a specific feature."""
        context_name = f"{feature.title()}Context"
        imports = ['import React, { createContext, useContext, useState, useCallback }']
        state_vars = []
        methods = []
        
        # Add feature-specific state and methods
        if feature == 'playlist':
            state_vars.append('const [playlists, setPlaylists] = useState<Playlist[]>([])')
            methods.extend([
                'const createPlaylist = useCallback((name: string) => {',
                '    const newPlaylist = { id: Date.now(), name, tracks: [] }',
                '    setPlaylists(prev => [...prev, newPlaylist])',
                '    return newPlaylist',
                '}, [])',
                '',
                'const addTrackToPlaylist = useCallback((playlistId: number, track: Track) => {',
                '    setPlaylists(prev => prev.map(playlist => {',
                '        if (playlist.id === playlistId) {',
                '            return { ...playlist, tracks: [...playlist.tracks, track] }',
                '        }',
                '        return playlist',
                '    }))',
                '}, [])'
            ])
            
        elif feature == 'theme':
            state_vars.append('const [theme, setTheme] = useState<Theme>("light")')
            methods.extend([
                'const toggleTheme = useCallback(() => {',
                '    setTheme(prev => prev === "light" ? "dark" : "light")',
                '}, [])'
            ])
            
        elif feature == 'auth':
            imports.append('import { User } from "@/types"')
            state_vars.extend([
                'const [user, setUser] = useState<User | null>(null)',
                'const [loading, setLoading] = useState(true)'
            ])
            methods.extend([
                'const login = useCallback(async (credentials: LoginCredentials) => {',
                '    setLoading(true)',
                '    try {',
                '        const user = await authService.login(credentials)',
                '        setUser(user)',
                '        return user',
                '    } finally {',
                '        setLoading(false)',
                '    }',
                '}, [])',
                '',
                'const logout = useCallback(async () => {',
                '    await authService.logout()',
                '    setUser(null)',
                '}, [])'
            ])
            
        # Generate context file content
        context_content = self._generate_context_content(
            context_name=context_name,
            imports=imports,
            state_vars=state_vars,
            methods=methods
        )
        
        # Write context file
        context_file = contexts_dir / f"{feature.lower()}_context.tsx"
        await self._write_file(str(context_file), context_content)

    async def _create_component(self, name: str, requirements: list, component_dir: Path) -> None:
        """Create a component based on specific requirements."""
        imports = ['import React']
        hooks = []
        props = []
        state = []
        effects = []
        jsx = []
        
        # Build component based on requirements
        for req in requirements:
            if req == 'streaming':
                imports.append('import { useAudioStream } from "@/hooks/useAudioStream"')
                hooks.append('const { stream, error } = useAudioStream()')
                jsx.append(self._generate_streaming_player())
            elif req == 'file_upload':
                imports.append('import { useFileUpload } from "@/hooks/useFileUpload"')
                hooks.append('const { uploadFile, progress } = useFileUpload()')
                jsx.append(self._generate_upload_interface())
            elif req == 'visualization':
                imports.append('import { useVisualizer } from "@/hooks/useVisualizer"')
                imports.append('import { Canvas } from "@/components/Canvas"')
                hooks.append('const { audioData, isPlaying } = useVisualizer()')
                jsx.append('''
                    <div className="visualizer-container">
                        <Canvas audioData={audioData} isPlaying={isPlaying} />
                    </div>
                '''.strip())
            elif req == 'playlist':
                imports.append('import { usePlaylist } from "@/hooks/usePlaylist"')
                imports.append('import { PlaylistItem } from "@/components/PlaylistItem"')
                hooks.append('const { playlists, currentTrack, addToPlaylist, removeFromPlaylist } = usePlaylist()')
                state.append('const [selectedPlaylist, setSelectedPlaylist] = useState<string | null>(null)')
                jsx.append('''
                    <div className="playlist-container">
                        {playlists.map(playlist => (
                            <PlaylistItem
                                key={playlist.id}
                                playlist={playlist}
                                currentTrack={currentTrack}
                                onAdd={addToPlaylist}
                                onRemove={removeFromPlaylist}
                                selected={selectedPlaylist === playlist.id}
                                onSelect={() => setSelectedPlaylist(playlist.id)}
                            />
                        ))}
                    </div>
                '''.strip())

        # Generate the initial component
        component_content = self._generate_component_content(
            name=name,
            imports=imports,
            hooks=hooks,
            props=props,
            state=state,
            effects=effects,
            jsx=jsx
        )

        # Try to enhance the component with scraped template
        enhanced_content = await self._enhance_component_with_template(
            name=name,
            requirements=requirements,
            base_content=component_content
        )

        # Write the final component
        await self._write_file(
            os.path.join(component_dir, f"{name}.tsx"),
            enhanced_content
        )

    async def _create_index_page(self, pages_dir: Path, features: dict) -> None:
        """Create index page based on project features."""
        imports = ['import React from "react"']
        components = []
        
        # Add feature-specific components
        if 'playlist' in features:
            imports.append('import { PlaylistGrid } from "@/components/playlist/PlaylistGrid"')
            components.append('<PlaylistGrid />')
            
        if 'visualizer' in features:
            imports.append('import { Visualizer } from "@/components/visualizer/Visualizer"')
            components.append('<Visualizer />')
            
        if 'upload' in features:
            imports.append('import { UploadZone } from "@/components/upload/UploadZone"')
            components.append('<UploadZone />')
            
        # Generate page content
        page_content = f"""
{self._format_imports(imports)}

export default function Home() {{
    return (
        <main className="flex min-h-screen flex-col items-center justify-between p-24">
            <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm">
                {' '.join(components)}
            </div>
        </main>
    )
}}
"""
        
        # Write page file
        page_file = pages_dir / "index.tsx"
        await self._write_file(str(page_file), page_content)

    async def _create_playlist_pages(self, pages_dir: Path) -> None:
        """Create playlist-related pages."""
        # Create playlists index page
        playlists_dir = pages_dir / "playlists"
        playlists_dir.mkdir(exist_ok=True)
        
        index_content = """
import React from 'react'
import { PlaylistGrid } from '@/components/playlist/PlaylistGrid'
import { CreatePlaylistButton } from '@/components/playlist/CreatePlaylistButton'

export default function PlaylistsPage() {
    return (
        <div className="container mx-auto px-4 py-8">
            <div className="flex justify-between items-center mb-8">
                <h1 className="text-3xl font-bold">Your Playlists</h1>
                <CreatePlaylistButton />
            </div>
            <PlaylistGrid />
        </div>
    )
}
"""
        await self._write_file(str(playlists_dir / "index.tsx"), index_content)
        
        # Create dynamic playlist page
        playlist_content = """
import React from 'react'
import { useRouter } from 'next/router'
import { usePlaylist } from '@/hooks/usePlaylist'
import { PlaylistDetails } from '@/components/playlist/PlaylistDetails'
import { TrackList } from '@/components/playlist/TrackList'

export default function PlaylistPage() {
    const router = useRouter()
    const { id } = router.query
    const { playlist, loading, error } = usePlaylist(id as string)
    
    if (loading) return <div>Loading...</div>
    if (error) return <div>Error: {error}</div>
    if (!playlist) return <div>Playlist not found</div>
    
    return (
        <div className="container mx-auto px-4 py-8">
            <PlaylistDetails playlist={playlist} />
            <TrackList tracks={playlist.tracks} />
        </div>
    )
}
"""
        await self._write_file(str(playlists_dir / "[id].tsx"), playlist_content)

    async def _create_visualizer_page(self, pages_dir: Path) -> None:
        """Create visualizer page."""
        visualizer_dir = pages_dir / "visualizer"
        visualizer_dir.mkdir(exist_ok=True)
        
        page_content = """
import React from 'react'
import { AudioVisualizer } from '@/components/visualizer/AudioVisualizer'
import { VisualizerControls } from '@/components/visualizer/VisualizerControls'
import { useAudioContext } from '@/hooks/useAudioContext'

export default function VisualizerPage() {
    const { audioContext, analyser } = useAudioContext()
    
    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold mb-8">Audio Visualizer</h1>
            <div className="grid grid-cols-1 gap-8">
                <AudioVisualizer analyser={analyser} />
                <VisualizerControls audioContext={audioContext} />
            </div>
        </div>
    )
}
"""
        await self._write_file(str(visualizer_dir / "index.tsx"), page_content)

    def _generate_context_content(self, context_name: str, imports: List[str], state_vars: List[str], methods: List[str]) -> str:
        """Generate context file content"""
        # Extract state and method names for context value
        state_names = []
        method_names = []
        
        for var in state_vars:
            if 'useState' in var:
                name = var.split('[')[1].split(',')[0].strip()
                state_names.append(name)
                
        for method in methods:
            if 'const' in method and '=' in method:
                name = method.split('const')[1].split('=')[0].strip()
                method_names.append(name)
                
        # Generate context value type
        value_type = ', '.join([
            *[f"{name}: {name.title()}" for name in state_names],
            *[f"{name}: {name.title()}" for name in method_names]
        ])
        
        return f"""
{self._format_imports(imports)}

type {context_name}Type = {{
    {value_type}
}}

const {context_name} = createContext<{context_name}Type | undefined>(undefined)

export function {context_name}Provider({{ children }}: {{ children: React.ReactNode }}) {{
    {self._format_content(state_vars)}
    
    {self._format_content(methods)}
    
    const value = {{
        {', '.join([*state_names, *method_names])}
    }}
    
    return (
        <{context_name}.Provider value={{value}}>
            {{children}}
        </{context_name}.Provider>
    )
}}

export function use{context_name}() {{
    const context = useContext({context_name})
    if (context === undefined) {{
        throw new Error('use{context_name} must be used within a {context_name}Provider')
    }}
    return context
}}
"""

    def _format_imports(self, imports: List[str]) -> str:
        """Format import statements."""
        # Remove duplicates and sort
        unique_imports = sorted(set(imports))
        
        # Group imports by type
        react_imports = []
        next_imports = []
        hook_imports = []
        component_imports = []
        other_imports = []
        
        for imp in unique_imports:
            if 'react' in imp.lower():
                react_imports.append(imp)
            elif 'next' in imp.lower():
                next_imports.append(imp)
            elif '/hooks/' in imp:
                hook_imports.append(imp)
            elif '/components/' in imp:
                component_imports.append(imp)
            else:
                other_imports.append(imp)
        
        # Join all groups with newlines between them
        formatted = []
        if react_imports:
            formatted.extend(react_imports)
        if next_imports:
            if formatted: formatted.append('')
            formatted.extend(next_imports)
        if hook_imports:
            if formatted: formatted.append('')
            formatted.extend(hook_imports)
        if component_imports:
            if formatted: formatted.append('')
            formatted.extend(component_imports)
        if other_imports:
            if formatted: formatted.append('')
            formatted.extend(other_imports)
            
        return '\n'.join(formatted)
        
    def _format_content(self, lines: List[str]) -> str:
        """Format content lines with proper indentation"""
        return '\n    '.join(lines)

    async def _create_auth_hook(self, project_path: Path) -> None:
        """Create authentication hook and context"""
        hooks_dir = project_path / 'src' / 'hooks'
        hooks_dir.mkdir(exist_ok=True)
        
        auth_hook_content = """import { createContext, useContext, useState, useEffect } from 'react';

type User = {
  id: string;
  name: string;
  email: string;
} | null;

type AuthContextType = {
  user: User;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User>(null);

  const login = async (email: string, password: string) => {
    // Implement your login logic here
    setUser({ id: '1', name: 'User', email });
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
"""
        
        auth_hook_path = hooks_dir / 'useAuth.tsx'
        auth_hook_path.write_text(auth_hook_content)

    async def _create_theme_context(self, project_path: Path) -> None:
        """Create theme context"""
        contexts_dir = project_path / 'src' / 'contexts'
        contexts_dir.mkdir(exist_ok=True)
        
        theme_context_content = """import { createContext, useContext, useState } from 'react';

type Theme = 'light' | 'dark';

type ThemeContextType = {
  theme: Theme;
  toggleTheme: () => void;
};

const ThemeContext = createContext<ThemeContextType>({} as ThemeContextType);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>('light');

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);
"""
        
        theme_context_path = contexts_dir / 'ThemeContext.tsx'
        theme_context_path.write_text(theme_context_content) 

    async def _create_playlist_components(self, components_dir: Path) -> None:
        """Create playlist-related components."""
        playlist_list_content = """import React from 'react';
import { usePlaylist } from '@/contexts/PlaylistContext';

export function PlaylistList() {
  const { playlists, removePlaylist } = usePlaylist();

  return (
    <div className="space-y-4">
      {playlists.map(playlist => (
        <div key={playlist.id} className="bg-gray-800 p-4 rounded-lg">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium">{playlist.name}</h3>
            <button
              onClick={() => removePlaylist(playlist.id)}
              className="text-red-500 hover:text-red-600"
            >
              Delete
            </button>
          </div>
          <p className="text-sm text-gray-400 mt-1">
            {playlist.songs.length} songs
          </p>
        </div>
      ))}
    </div>
  );
}"""

        playlist_form_content = """import React, { useState } from 'react';
import { usePlaylist } from '@/contexts/PlaylistContext';

export function PlaylistForm() {
  const [name, setName] = useState('');
  const { addPlaylist } = usePlaylist();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name.trim()) {
      addPlaylist({
        id: Date.now().toString(),
        name: name.trim(),
        songs: []
      });
      setName('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="playlist-name" className="block text-sm font-medium">
          Playlist Name
        </label>
        <input
          type="text"
          id="playlist-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          placeholder="Enter playlist name"
        />
      </div>
      <button
        type="submit"
        className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
      >
        Create Playlist
      </button>
    </form>
  );
}"""

        await self._write_file(os.path.join(components_dir, "PlaylistList.tsx"), playlist_list_content)
        await self._write_file(os.path.join(components_dir, "PlaylistForm.tsx"), playlist_form_content)
        logger.info("Created playlist components") 

    async def _create_visualizer_component(self, components_dir: Path) -> None:
        """Create audio visualizer component."""
        visualizer_content = """import React, { useEffect, useRef } from 'react';

interface AudioVisualizerProps {
  audioRef: React.RefObject<HTMLAudioElement>;
  isPlaying: boolean;
}

export function AudioVisualizer({ audioRef, isPlaying }: AudioVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const analyserRef = useRef<AnalyserNode>();

  useEffect(() => {
    if (!audioRef.current || !canvasRef.current) return;

    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const analyser = audioContext.createAnalyser();
    analyserRef.current = analyser;

    const source = audioContext.createMediaElementSource(audioRef.current);
    source.connect(analyser);
    analyser.connect(audioContext.destination);

    analyser.fftSize = 256;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d')!;

    const draw = () => {
      const WIDTH = canvas.width;
      const HEIGHT = canvas.height;

      analyser.getByteFrequencyData(dataArray);

      ctx.fillStyle = 'rgb(0, 0, 0)';
      ctx.fillRect(0, 0, WIDTH, HEIGHT);

      const barWidth = (WIDTH / bufferLength) * 2.5;
      let barHeight;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        barHeight = dataArray[i] / 2;

        const r = barHeight + (25 * (i / bufferLength));
        const g = 250 * (i / bufferLength);
        const b = 50;

        ctx.fillStyle = `rgb(${r},${g},${b})`;
        ctx.fillRect(x, HEIGHT - barHeight, barWidth, barHeight);

        x += barWidth + 1;
      }

      animationRef.current = requestAnimationFrame(draw);
    };

    if (isPlaying) {
      draw();
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      audioContext.close();
    };
  }, [audioRef, isPlaying]);

  return (
    <canvas
      ref={canvasRef}
      width={300}
      height={100}
      className="bg-black rounded-lg"
    />
  );
}"""

        await self._write_file(os.path.join(components_dir, "AudioVisualizer.tsx"), visualizer_content)
        logger.info("Created audio visualizer component") 

    async def _write_file(self, path: str, content: str) -> None:
        """Write content to a file, creating directories if needed."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Write the file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Failed to write file {path}: {str(e)}")
            raise 

    def _generate_streaming_player(self) -> str:
        """Generate streaming player JSX."""
        return """
        <div className="audio-player">
          {error && <div className="error">{error}</div>}
          {stream && (
            <audio
              controls
              src={stream}
              className="w-full"
            />
          )}
        </div>
        """

    def _generate_upload_interface(self) -> str:
        """Generate file upload interface JSX."""
        return """
        <div className="upload-interface">
          <input
            type="file"
            accept="audio/*"
            onChange={handleFileChange}
            className="hidden"
            id="audio-upload"
          />
          <label
            htmlFor="audio-upload"
            className="btn btn-primary"
          >
            Select Audio File
          </label>
          {progress > 0 && (
            <div className="progress-bar">
              <div
                className="progress"
                style={{ width: `${progress}%` }}
              />
            </div>
          )}
        </div>
        """ 

    async def build_project(self, config: ProjectConfig, requirements: dict) -> None:
        """Build project based on analyzed requirements."""
        try:
            project_path = Path(config.project_location) / config.name
            self.project_path = project_path  # Store for use in other methods
            
            # Analyze requirements from description
            features = await self._analyze_requirements(config.description)
            
            # Create project structure
            await self.initialize_project(config, requirements, project_path)
            
            # Create components based on analyzed features
            components_dir = project_path / 'src' / 'components'
            for feature, details in features.items():
                if details['detected']:
                    await self._create_component(
                        name=feature,
                        requirements=details['requirements'],
                        component_dir=components_dir
                    )

            # Install dependencies
            try:
                npm_path = r"C:\Program Files\nodejs\npm.cmd"
                subprocess.run([npm_path, 'install'], cwd=project_path, check=True)
                logger.info("Installed dependencies")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install dependencies: {str(e)}")
                raise ValueError("Failed to install dependencies")

            # Enhance project with API integrations
            enhancements = await self.api_manager.enhance_project_structure(
                config.description,
                features
            )

            # Update dependencies
            if 'dependencies' in requirements:
                requirements['dependencies'].update(enhancements['dependencies'])

            # Create API integration files
            await self._create_api_integrations(
                project_path,
                enhancements['apis']
            )

            # Apply code patterns
            await self._apply_code_patterns(
                project_path,
                enhancements['code_patterns']
            )

            logger.info(f"Successfully built project at {project_path}")

        except Exception as e:
            logger.error(f"Failed to build project: {str(e)}")
            raise ValueError(f"Failed to build project: {str(e)}") 

    async def _create_api_integrations(self, project_path: Path, apis: List[Dict]) -> None:
        """Create API integration files for the project."""
        try:
            api_dir = project_path / 'src' / 'api'
            api_dir.mkdir(exist_ok=True)

            for api in apis:
                # Create API client
                client_content = self._generate_api_client(api)
                await self._write_file(
                    os.path.join(api_dir, f"{api['name'].lower()}.ts"),
                    client_content
                )

                # Create API hooks
                hook_content = self._generate_api_hook(api)
                await self._write_file(
                    os.path.join(project_path / 'src' / 'hooks', f"use{api['name']}.ts"),
                    hook_content
                )

            logger.info(f"Created API integrations for {len(apis)} APIs")
        except Exception as e:
            logger.error(f"Failed to create API integrations: {str(e)}")
            raise

    def _generate_api_client(self, api: Dict) -> str:
        """Generate API client code based on OpenAPI spec."""
        endpoints = api['info'].get('endpoints', [])
        
        imports = [
            'import axios from "axios"',
            'import { API_CONFIG } from "@/config/api"'
        ]
        
        methods = []
        types = []
        
        for endpoint in endpoints:
            method_name = endpoint['operationId']
            response_type = endpoint.get('responseType', 'any')
            request_type = endpoint.get('requestType')
            
            # Generate TypeScript types
            if response_type != 'any':
                types.append(f"type {response_type} = {endpoint['responseSchema']}")
            if request_type:
                types.append(f"type {request_type} = {endpoint['requestSchema']}")
            
            # Generate method
            method = f"""
async function {method_name}({
    'params: ' + request_type if request_type else ''
}): Promise<{response_type}> {{
    const response = await axios.{endpoint['method']}(
        `${{API_CONFIG.baseUrl}}{endpoint['path']}`,
        {'{params}' if endpoint['method'] in ['post', 'put', 'patch'] else ''}
    );
    return response.data;
}}"""
            methods.append(method)
        
        return f"""// Generated API client for {api['name']}
{chr(10).join(imports)}

{chr(10).join(types)}

{chr(10).join(methods)}

export const {api['name']}Client = {{
    {','.join(endpoint['operationId'] for endpoint in endpoints)}
}};
"""

    def _generate_api_hook(self, api: Dict) -> str:
        """Generate React hook for API integration."""
        endpoints = api['info'].get('endpoints', [])
        
        imports = [
            'import { useState } from "react"',
            f'import {{ {api["name"]}Client }} from "@/api/{api["name"].lower()}"'
        ]
        
        hook_content = []
        for endpoint in endpoints:
            hook_content.append(f"""
const {endpoint['operationId']} = async ({
    'params: ' + endpoint.get('requestType', 'any') if endpoint.get('requestType') else ''
}) => {{
    try {{
        setLoading(true);
        const result = await {api['name']}Client.{endpoint['operationId']}({
            'params' if endpoint.get('requestType') else ''
        });
        setData(result);
        return result;
    }} catch (error) {{
        setError(error);
        throw error;
    }} finally {{
        setLoading(false);
    }}
}};""")
        
        return f"""// Generated hook for {api['name']} API
{chr(10).join(imports)}

export function use{api['name']}() {{
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);
    
    {chr(10).join(hook_content)}
    
    return {{
        data,
        loading,
        error,
        {','.join(endpoint['operationId'] for endpoint in endpoints)}
    }};
}}
"""

    async def _apply_code_patterns(self, project_path: Path, patterns: List[Dict]) -> None:
        """Apply discovered code patterns to the project."""
        try:
            for pattern in patterns:
                # Determine the appropriate location for the pattern
                target_path = self._determine_pattern_location(project_path, pattern)
                if target_path:
                    # Analyze and adapt the pattern
                    adapted_content = self._adapt_code_pattern(pattern['content'])
                    # Write the adapted pattern
                    await self._write_file(target_path, adapted_content)
                    logger.info(f"Applied code pattern to {target_path}")
        except Exception as e:
            logger.error(f"Failed to apply code patterns: {str(e)}")
            raise

    def _determine_pattern_location(self, project_path: Path, pattern: Dict) -> Optional[str]:
        """Determine where to place a code pattern in the project."""
        file_path = pattern['path']
        if 'components' in file_path.lower():
            return os.path.join(project_path, 'src', 'components', os.path.basename(file_path))
        elif 'hooks' in file_path.lower():
            return os.path.join(project_path, 'src', 'hooks', os.path.basename(file_path))
        elif 'utils' in file_path.lower():
            return os.path.join(project_path, 'src', 'utils', os.path.basename(file_path))
        return None

    def _adapt_code_pattern(self, content: str) -> str:
        """Adapt a code pattern to match project structure and conventions."""
        # Remove any project-specific imports
        lines = content.split('\n')
        adapted_lines = []
        
        for line in lines:
            # Adjust imports to match project structure
            if line.startswith('import'):
                line = self._adjust_import_path(line)
            # Remove project-specific comments
            if not line.strip().startswith('//') or 'eslint' in line:
                adapted_lines.append(line)
        
        return '\n'.join(adapted_lines)

    def _adjust_import_path(self, import_line: str) -> str:
        """Adjust import paths to match project structure."""
        if '@/' in import_line:
            return import_line
        
        # Convert relative imports to absolute
        if import_line.startswith('import') and ('./' in import_line or '../' in import_line):
            parts = import_line.split(' from ')
            if len(parts) == 2:
                path = parts[1].strip("'").strip('"')
                if path.endswith('.ts') or path.endswith('.tsx'):
                    path = path[:-3]
                return f"{parts[0]} from '@/{path}'"
        
        return import_line 

    async def _create_api_config(self, project_path: Path, apis: List[Dict]) -> None:
        """Create API configuration file."""
        config_dir = project_path / 'src' / 'config'
        config_dir.mkdir(exist_ok=True)
        
        config_content = """// API Configuration
export const API_CONFIG = {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api',
    endpoints: {
"""
        
        for api in apis:
            config_content += f"""        {api['name'].lower()}: {{
                baseUrl: process.env.NEXT_PUBLIC_{api['name'].upper()}_API_URL,
                apiKey: process.env.NEXT_PUBLIC_{api['name'].upper()}_API_KEY,
            }},
"""
        
        config_content += """    }
};
"""
        
        await self._write_file(
            os.path.join(config_dir, "api.ts"),
            config_content
        )
        logger.info("Created API configuration") 

    def _generate_component_content(
        self,
        name: str,
        imports: List[str],
        hooks: List[str],
        props: List[str],
        state: List[str],
        effects: List[str],
        jsx: List[str]
    ) -> str:
        """Generate the content for a React component."""
        # Format imports
        import_statements = self._format_imports(imports)
        
        # Generate props interface if needed
        props_interface = ""
        if props:
            props_interface = f"""
interface {name}Props {{
    {chr(10).join(props)}
}}
"""
        
        # Generate the component
        return f"""
{import_statements}

{props_interface}
export function {name}({f"props: {name}Props" if props else ""}) {{
    {chr(10).join(hooks)}
    
    {chr(10).join(state)}
    
    {chr(10).join(effects)}
    
    return (
        {chr(10).join(jsx) if jsx else "<div />"}
    );
}}
""" 

    async def _scrape_component_template(self, component_type: str) -> Optional[Dict[str, str]]:
        """Scrape component template from 21st.dev."""
        try:
            base_url = "https://21st.dev"
            component_map = {
                'audio': 'ui-elements/audio-player',
                'playlist': 'ui-elements/list',
                'visualization': 'ui-elements/canvas',
                'upload': 'ui-elements/file-upload',
                'player': 'ui-elements/media-player',
                'button': 'ui-elements/button',
                'card': 'ui-elements/card',
                'modal': 'ui-elements/dialog',
                'form': 'ui-elements/form',
                'input': 'ui-elements/input',
                'slider': 'ui-elements/slider',
                'spinner': 'ui-elements/spinner-loader',
            }

            if component_type not in component_map:
                return None

            async with aiohttp.ClientSession() as session:
                url = f"{base_url}/{component_map[component_type]}"
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._extract_component_code(html, component_type)
            return None
        except Exception as e:
            logger.warning(f"Failed to scrape component template: {str(e)}")
            return None

    def _extract_component_code(self, html: str, component_type: str) -> Dict[str, str]:
        """Extract component code, styles and types from HTML."""
        # Basic extraction - in real implementation would use proper HTML parsing
        component = {
            'tsx': '',
            'css': '',
            'types': '',
            'dependencies': []
        }

        try:
            # Extract TypeScript/TSX code
            tsx_start = html.find('```tsx')
            if tsx_start != -1:
                tsx_end = html.find('```', tsx_start + 6)
                if tsx_end != -1:
                    component['tsx'] = html[tsx_start + 6:tsx_end].strip()

            # Extract CSS/Tailwind classes
            css_start = html.find('```css')
            if css_start != -1:
                css_end = html.find('```', css_start + 6)
                if css_end != -1:
                    component['css'] = html[css_start + 6:css_end].strip()

            # Extract TypeScript types
            types_start = html.find('```ts')
            if types_start != -1:
                types_end = html.find('```', types_start + 5)
                if types_end != -1:
                    component['types'] = html[types_start + 5:types_end].strip()

            # Extract dependencies
            deps_start = html.find('### Dependencies')
            if deps_start != -1:
                deps_section = html[deps_start:html.find('#', deps_start + 1)].lower()
                component['dependencies'] = [
                    dep.strip() 
                    for dep in deps_section.split('\n') 
                    if dep.strip().startswith('- ')
                ]

        except Exception as e:
            logger.warning(f"Error extracting component code: {str(e)}")

        return component

    async def _enhance_component_with_template(self, name: str, requirements: List[str], base_content: str) -> str:
        """Enhance component content with scraped template if available."""
        enhanced_content = base_content

        for req in requirements:
            template = await self._scrape_component_template(req)
            if template:
                # Add any new imports
                if 'tsx' in template:
                    imports = self._extract_imports(template['tsx'])
                    enhanced_content = self._merge_imports(enhanced_content, imports)

                # Add any new types
                if template.get('types'):
                    enhanced_content = self._merge_types(enhanced_content, template['types'])

                # Add any new styles
                if template.get('css'):
                    enhanced_content = self._merge_styles(enhanced_content, template['css'])

                # Update dependencies if needed
                if template.get('dependencies'):
                    await self._update_project_dependencies(template['dependencies'])

        return enhanced_content

    def _extract_imports(self, code: str) -> List[str]:
        """Extract import statements from code."""
        imports = []
        for line in code.split('\n'):
            if line.strip().startswith('import '):
                imports.append(line.strip())
        return imports

    def _merge_imports(self, original: str, new_imports: List[str]) -> str:
        """Merge new imports into original code."""
        original_imports = self._extract_imports(original)
        all_imports = list(set(original_imports + new_imports))
        return original.replace(
            '\n'.join(original_imports),
            self._format_imports(all_imports)
        )

    def _merge_types(self, original: str, new_types: str) -> str:
        """Merge new types into original code."""
        # Find the position after imports
        import_end = original.rfind('import ')
        if import_end != -1:
            import_end = original.find('\n', import_end) + 1
        else:
            import_end = 0

        return f"{original[:import_end]}\n{new_types}\n{original[import_end:]}"

    def _merge_styles(self, original: str, new_styles: str) -> str:
        """Merge new styles into original code."""
        if 'className=' not in original:
            return original

        # Convert CSS to Tailwind classes if needed
        tailwind_classes = self._convert_css_to_tailwind(new_styles)
        
        # Add classes to existing className props
        def add_classes(match):
            existing = match.group(1)
            return f'className="{existing} {tailwind_classes}"'

        return re.sub(r'className="([^"]*)"', add_classes, original)

    def _convert_css_to_tailwind(self, css: str) -> str:
        """Convert CSS to Tailwind classes."""
        # This would be a more complex implementation
        # For now, just return basic mappings
        tailwind_map = {
            'display: flex': 'flex',
            'flex-direction: column': 'flex-col',
            'align-items: center': 'items-center',
            'justify-content: center': 'justify-center',
            'padding': 'p-4',
            'margin': 'm-4',
            'width: 100%': 'w-full',
            'height: 100%': 'h-full',
        }

        classes = []
        for css_prop, tw_class in tailwind_map.items():
            if css_prop in css:
                classes.append(tw_class)

        return ' '.join(classes)

    async def _update_project_dependencies(self, dependencies: List[str]) -> None:
        """Update project package.json with new dependencies."""
        try:
            package_json_path = self.project_path / 'package.json'
            if not package_json_path.exists():
                return

            with open(package_json_path, 'r') as f:
                package_json = json.load(f)

            modified = False
            for dep in dependencies:
                name = dep.split('@')[0].strip('- ')
                version = dep.split('@')[1] if '@' in dep else 'latest'
                
                if name not in package_json.get('dependencies', {}):
                    if 'dependencies' not in package_json:
                        package_json['dependencies'] = {}
                    package_json['dependencies'][name] = version
                    modified = True

            if modified:
                with open(package_json_path, 'w') as f:
                    json.dump(package_json, f, indent=2)

        except Exception as e:
            logger.warning(f"Failed to update dependencies: {str(e)}") 