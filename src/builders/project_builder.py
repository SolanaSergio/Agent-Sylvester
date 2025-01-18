import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from src.utils.types import ProjectConfig

class ProjectBuilder:
    def __init__(self):
        self.config: Optional[ProjectConfig] = None
        self.requirements: Dict = {}

    async def initialize_project(self, config: ProjectConfig, requirements: Dict) -> None:
        """Initialize a new project with the given configuration"""
        self.config = config
        self.requirements = requirements
        
        # Create project directory
        project_dir = Path(config.name)
        project_dir.mkdir(exist_ok=True)
        
        # Initialize git repository
        await self._init_git(project_dir)
        
        # Create initial project files
        await self._create_initial_files(project_dir)

    async def generate_structure(self) -> None:
        """Generate the project's directory structure"""
        if not self.config:
            raise ValueError("Project not initialized")
            
        project_dir = Path(self.config.name)
        
        # Create standard directories
        directories = [
            "src",
            "src/components",
            "src/pages",
            "src/styles",
            "src/utils",
            "src/hooks",
            "src/contexts",
            "src/services",
            "public",
            "tests",
            "docs"
        ]
        
        for directory in directories:
            project_dir.joinpath(directory).mkdir(parents=True, exist_ok=True)

    async def generate_components(self) -> None:
        """Generate initial project components"""
        if not self.config:
            raise ValueError("Project not initialized")
            
        project_dir = Path(self.config.name)
        components_dir = project_dir / "src/components"
        
        # Generate basic components
        basic_components = {
            "Layout": self._get_layout_template(),
            "Header": self._get_header_template(),
            "Footer": self._get_footer_template(),
            "Button": self._get_button_template(),
            "Card": self._get_card_template()
        }
        
        for name, template in basic_components.items():
            component_file = components_dir / f"{name}.tsx"
            component_file.write_text(template)

    async def _init_git(self, project_dir: Path) -> None:
        """Initialize git repository"""
        try:
            subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
            
            # Create .gitignore
            gitignore_content = """
node_modules/
.next/
build/
dist/
.env
.env.local
*.log
.DS_Store
coverage/
"""
            project_dir.joinpath(".gitignore").write_text(gitignore_content.strip())
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to initialize git repository: {e.stderr.decode()}")

    def _get_layout_template(self) -> str:
        return """
import { ReactNode } from 'react';
import Header from './Header';
import Footer from './Footer';

interface LayoutProps {
    children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
    return (
        <div className="min-h-screen flex flex-col">
            <Header />
            <main className="flex-grow container mx-auto px-4 py-8">
                {children}
            </main>
            <Footer />
        </div>
    );
}
"""

    def _get_header_template(self) -> str:
        return """
export default function Header() {
    return (
        <header className="bg-white shadow">
            <div className="container mx-auto px-4 py-6">
                <h1 className="text-2xl font-bold">Your App Name</h1>
            </div>
        </header>
    );
}
"""

    def _get_footer_template(self) -> str:
        return """
export default function Footer() {
    return (
        <footer className="bg-gray-100">
            <div className="container mx-auto px-4 py-6">
                <p className="text-center text-gray-600">
                    © {new Date().getFullYear()} Your App Name. All rights reserved.
                </p>
            </div>
        </footer>
    );
}
"""

    def _get_button_template(self) -> str:
        return """
import { ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'outline';
}

export default function Button({ 
    children, 
    variant = 'primary', 
    className = '', 
    ...props 
}: ButtonProps) {
    const baseStyles = 'px-4 py-2 rounded font-medium focus:outline-none focus:ring-2';
    const variantStyles = {
        primary: 'bg-blue-500 text-white hover:bg-blue-600',
        secondary: 'bg-gray-500 text-white hover:bg-gray-600',
        outline: 'border-2 border-blue-500 text-blue-500 hover:bg-blue-50'
    };

    return (
        <button 
            className={`${baseStyles} ${variantStyles[variant]} ${className}`}
            {...props}
        >
            {children}
        </button>
    );
}
"""

    def _get_card_template(self) -> str:
        return """
import { ReactNode } from 'react';

interface CardProps {
    title?: string;
    children: ReactNode;
    className?: string;
}

export default function Card({ title, children, className = '' }: CardProps) {
    return (
        <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
            {title && <h2 className="text-xl font-semibold mb-4">{title}</h2>}
            {children}
        </div>
    );
}
""" 