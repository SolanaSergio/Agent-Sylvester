import asyncio
from pathlib import Path
from typing import Dict, List, Optional
import json
import subprocess
import re
from packaging import version
import networkx as nx
import logging
from src.utils.types import ProjectConfig, DependencyInfo
import os
import platform

logger = logging.getLogger(__name__)

class DependencyManager:
    """Manages project dependencies and package versions"""
    
    def __init__(self):
        self.project_dir: Optional[Path] = None
        self.dependency_graph = nx.DiGraph()
        self.version_cache: Dict[str, List[str]] = {}
        self.npm_path = self._find_npm()
        
    def _find_npm(self) -> str:
        """Find npm executable in common locations"""
        # First try PATH
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['where', 'npm'], capture_output=True, text=True)
            else:
                result = subprocess.run(['which', 'npm'], capture_output=True, text=True)
            if result.returncode == 0:
                npm_path = result.stdout.strip().split('\n')[0]  # Take first path if multiple found
                if platform.system() == "Windows" and not npm_path.endswith('.cmd'):
                    npm_path = npm_path + '.cmd'
                logger.info(f"Found npm in PATH: {npm_path}")
                return npm_path
        except Exception as e:
            logger.debug(f"Could not find npm in PATH: {str(e)}")

        # Check common Windows locations
        if platform.system() == "Windows":
            common_paths = [
                r"C:\Program Files\nodejs\npm.cmd",
                r"C:\Program Files (x86)\nodejs\npm.cmd",
                str(Path.home() / "AppData" / "Roaming" / "npm" / "npm.cmd"),
                str(Path.home() / "AppData" / "Local" / "Programs" / "nodejs" / "npm.cmd")
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    logger.info(f"Found npm at: {path}")
                    return path
                    
        raise Exception("npm not found in PATH or common locations. Please ensure Node.js is installed correctly.")

    async def setup_project_dependencies(self, config: ProjectConfig, project_path: Path) -> None:
        """Set up project dependencies based on configuration"""
        self.project_dir = project_path
        
        # Initialize package.json
        await self._initialize_package_json(config)
        
        # Install dependencies
        await self._install_dependencies()
        
        # Generate dependency graph
        await self._build_dependency_graph()
        
        # Check for conflicts
        conflicts = await self._check_version_conflicts()
        if conflicts:
            await self._resolve_conflicts(conflicts)

    async def get_dependency_status(self) -> List[DependencyInfo]:
        """Get status of all project dependencies"""
        if not self.project_dir:
            return []
            
        package_json = self.project_dir / "package.json"
        if not package_json.exists():
            return []
            
        with open(package_json) as f:
            data = json.load(f)
            
        dependencies = []
        all_deps = {
            **data.get("dependencies", {}),
            **data.get("devDependencies", {})
        }
        
        for name, version_req in all_deps.items():
            installed_version = await self._get_installed_version(name)
            latest_version = await self._get_latest_version(name)
            
            dependencies.append(DependencyInfo(
                name=name,
                required_version=version_req,
                installed_version=installed_version,
                latest_version=latest_version,
                status=self._get_version_status(version_req, installed_version, latest_version)
            ))
            
        return dependencies

    async def update_dependencies(self, dependencies: List[str] = None) -> None:
        """Update project dependencies"""
        if not self.project_dir:
            raise ValueError("No project directory set")
            
        if dependencies:
            # Update specific dependencies
            for dep in dependencies:
                try:
                    subprocess.run(
                        ["npm", "update", dep],
                        cwd=self.project_dir,
                        check=True,
                        capture_output=True
                    )
                except subprocess.CalledProcessError as e:
                    raise Exception(f"Failed to update {dep}: {e.stderr.decode()}")
        else:
            # Update all dependencies
            try:
                subprocess.run(
                    ["npm", "update"],
                    cwd=self.project_dir,
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError as e:
                raise Exception(f"Failed to update dependencies: {e.stderr.decode()}")
                
        # Rebuild dependency graph
        await self._build_dependency_graph()

    async def add_dependency(self, name: str, version: str = "latest", dev: bool = False) -> None:
        """Add a new dependency"""
        if not self.project_dir:
            raise ValueError("No project directory set")
            
        try:
            cmd = ["npm", "install"]
            if dev:
                cmd.append("--save-dev")
            cmd.append(f"{name}@{version}")
            
            subprocess.run(
                cmd,
                cwd=self.project_dir,
                check=True,
                capture_output=True
            )
            
            # Update dependency graph
            await self._build_dependency_graph()
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to add dependency {name}: {e.stderr.decode()}")

    async def remove_dependency(self, name: str) -> None:
        """Remove a dependency"""
        if not self.project_dir:
            raise ValueError("No project directory set")
            
        try:
            subprocess.run(
                ["npm", "uninstall", name],
                cwd=self.project_dir,
                check=True,
                capture_output=True
            )
            
            # Update dependency graph
            self.dependency_graph.remove_node(name)
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to remove dependency {name}: {e.stderr.decode()}")

    async def _initialize_package_json(self, config: ProjectConfig) -> None:
        """Initialize package.json with project configuration"""
        package_data = {
            "name": config.name,
            "version": "0.1.0",
            "private": True,
            "description": config.description,
            "scripts": await self._get_scripts(config),
            "dependencies": {},
            "devDependencies": {}
        }
        
        package_json = self.project_dir / "package.json"
        package_json.write_text(json.dumps(package_data, indent=2))

    async def _install_dependencies(self) -> None:
        """Install project dependencies using npm"""
        if not self.project_dir:
            raise ValueError("Project directory not set")

        try:
            # Check npm version using found path
            logger.info("Checking npm version...")
            logger.info(f"Using npm path: {self.npm_path}")
            npm_version = subprocess.run(
                [self.npm_path, '-v'],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.project_dir  # Set working directory
            )
            logger.info(f"Using npm version: {npm_version.stdout.strip()}")

            # Install dependencies using found path
            logger.info("Installing dependencies...")
            result = subprocess.run(
                [self.npm_path, 'install'],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.project_dir  # Set working directory
            )
            logger.info("Dependencies installed successfully")
            return result.stdout

        except subprocess.CalledProcessError as e:
            error_msg = f"npm command failed: {e.stderr}"
            logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to install dependencies: {error_msg}")
            raise Exception(error_msg)

    async def _build_dependency_graph(self) -> None:
        """Build dependency graph from package-lock.json"""
        package_lock = self.project_dir / "package-lock.json"
        if not package_lock.exists():
            return
            
        with open(package_lock) as f:
            data = json.load(f)
            
        self.dependency_graph.clear()
        
        def process_dependencies(deps: Dict, parent: Optional[str] = None):
            for name, info in deps.items():
                if isinstance(info, dict) and "dependencies" in info:
                    self.dependency_graph.add_node(name, version=info.get("version"))
                    if parent:
                        self.dependency_graph.add_edge(parent, name)
                    process_dependencies(info["dependencies"], name)
                    
        if "dependencies" in data:
            process_dependencies(data["dependencies"])

    async def _check_version_conflicts(self) -> List[Dict]:
        """Check for version conflicts in dependency graph"""
        conflicts = []
        
        for node in self.dependency_graph.nodes():
            versions = set()
            for path in nx.all_simple_paths(self.dependency_graph, node, node):
                for n in path:
                    if n != node:
                        continue
                    v = self.dependency_graph.nodes[n].get("version")
                    if v:
                        versions.add(v)
                        
            if len(versions) > 1:
                conflicts.append({
                    "package": node,
                    "versions": list(versions)
                })
                
        return conflicts

    async def _resolve_conflicts(self, conflicts: List[Dict]) -> None:
        """Resolve version conflicts"""
        for conflict in conflicts:
            # Get the highest compatible version
            versions = [version.parse(v) for v in conflict["versions"]]
            highest = str(max(versions))
            
            # Update package to highest version
            await self.add_dependency(conflict["package"], highest)

    async def _get_installed_version(self, package: str) -> Optional[str]:
        """Get installed version of a package"""
        try:
            result = subprocess.run(
                ["npm", "list", package, "--depth=0"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            match = re.search(rf"{package}@([\d\.]+)", result.stdout)
            return match.group(1) if match else None
        except subprocess.CalledProcessError:
            return None

    async def _get_latest_version(self, package: str) -> Optional[str]:
        """Get latest version of a package from npm registry"""
        if package in self.version_cache:
            return self.version_cache[package][-1]
            
        try:
            result = subprocess.run(
                ["npm", "view", package, "versions", "--json"],
                capture_output=True,
                text=True
            )
            versions = json.loads(result.stdout)
            self.version_cache[package] = versions
            return versions[-1]
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return None

    def _get_version_status(
        self, 
        required: str, 
        installed: Optional[str], 
        latest: Optional[str]
    ) -> str:
        """Get dependency status based on versions"""
        if not installed:
            return "missing"
            
        if not latest:
            return "unknown"
            
        try:
            if version.parse(installed) < version.parse(latest):
                return "outdated"
            elif version.parse(installed) > version.parse(latest):
                return "ahead"
            else:
                return "current"
        except version.InvalidVersion:
            return "unknown"

    async def _get_scripts(self, config: ProjectConfig) -> Dict[str, str]:
        """Get npm scripts based on project configuration"""
        scripts = {
            "start": "next start" if config.framework == "Next.js" else "react-scripts start",
            "build": "next build" if config.framework == "Next.js" else "react-scripts build",
            "test": "jest",
            "lint": "eslint .",
            "format": "prettier --write ."
        }
        
        if config.framework == "Next.js":
            scripts["dev"] = "next dev"
            
        return scripts 