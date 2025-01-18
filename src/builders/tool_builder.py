import asyncio
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import shutil
import json

class ToolBuilder:
    """Builds and manages development tools and scripts"""
    
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.tools_dir = project_dir / "tools"
        self.tools_dir.mkdir(exist_ok=True)

    async def build_tool(self, tool_name: str, tool_config: Dict) -> None:
        """Build a development tool"""
        tool_dir = self.tools_dir / tool_name
        tool_dir.mkdir(exist_ok=True)
        
        # Generate tool files
        await self._generate_tool_files(tool_dir, tool_config)
        
        # Install dependencies
        await self._install_tool_dependencies(tool_dir, tool_config)
        
        # Set up tool configuration
        await self._setup_tool_config(tool_dir, tool_config)
        
        # Make tool executable
        await self._make_tool_executable(tool_dir, tool_name)

    async def update_tool(self, tool_name: str, tool_config: Dict) -> None:
        """Update an existing tool"""
        tool_dir = self.tools_dir / tool_name
        if not tool_dir.exists():
            raise ValueError(f"Tool {tool_name} does not exist")
            
        # Update tool files
        await self._update_tool_files(tool_dir, tool_config)
        
        # Update dependencies
        await self._install_tool_dependencies(tool_dir, tool_config)
        
        # Update configuration
        await self._setup_tool_config(tool_dir, tool_config)

    async def remove_tool(self, tool_name: str) -> None:
        """Remove a development tool"""
        tool_dir = self.tools_dir / tool_name
        if tool_dir.exists():
            shutil.rmtree(tool_dir)

    async def _generate_tool_files(self, tool_dir: Path, config: Dict) -> None:
        """Generate tool source files"""
        # Generate main tool script
        main_script = tool_dir / f"{config['name']}.py"
        main_script.write_text(self._get_tool_template(config))
        
        # Generate helper modules if needed
        if config.get('helpers'):
            helpers_dir = tool_dir / "helpers"
            helpers_dir.mkdir(exist_ok=True)
            
            for helper in config['helpers']:
                helper_file = helpers_dir / f"{helper['name']}.py"
                helper_file.write_text(helper['content'])

    async def _install_tool_dependencies(self, tool_dir: Path, config: Dict) -> None:
        """Install tool dependencies"""
        if 'dependencies' in config:
            requirements_file = tool_dir / "requirements.txt"
            requirements_file.write_text("\n".join(config['dependencies']))
            
            try:
                subprocess.run(
                    ["pip", "install", "-r", "requirements.txt"],
                    cwd=tool_dir,
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError as e:
                raise Exception(f"Failed to install tool dependencies: {e.stderr.decode()}")

    async def _setup_tool_config(self, tool_dir: Path, config: Dict) -> None:
        """Set up tool configuration"""
        if 'config' in config:
            config_file = tool_dir / "config.json"
            config_file.write_text(json.dumps(config['config'], indent=2))

    async def _make_tool_executable(self, tool_dir: Path, tool_name: str) -> None:
        """Make tool executable and add to PATH"""
        main_script = tool_dir / f"{tool_name}.py"
        
        # Make executable
        main_script.chmod(0o755)
        
        # Create symlink in .local/bin if on Unix
        if Path("/usr/local/bin").exists():
            symlink = Path("/usr/local/bin") / tool_name
            try:
                symlink.symlink_to(main_script)
            except FileExistsError:
                pass

    async def _update_tool_files(self, tool_dir: Path, config: Dict) -> None:
        """Update existing tool files"""
        # Update main script if changed
        main_script = tool_dir / f"{config['name']}.py"
        current_content = main_script.read_text() if main_script.exists() else ""
        new_content = self._get_tool_template(config)
        
        if current_content != new_content:
            main_script.write_text(new_content)
            
        # Update helpers
        if config.get('helpers'):
            helpers_dir = tool_dir / "helpers"
            helpers_dir.mkdir(exist_ok=True)
            
            # Remove old helpers
            for helper_file in helpers_dir.glob("*.py"):
                if helper_file.stem not in [h['name'] for h in config['helpers']]:
                    helper_file.unlink()
                    
            # Update/create new helpers
            for helper in config['helpers']:
                helper_file = helpers_dir / f"{helper['name']}.py"
                helper_file.write_text(helper['content'])

    def _get_tool_template(self, config: Dict) -> str:
        """Get tool script template"""
        return f"""#!/usr/bin/env python3
import sys
import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="{config.get('description', '')}")
    
    # Add arguments
    {self._generate_argument_parser(config.get('arguments', []))}
    
    args = parser.parse_args()
    
    # Load configuration
    config_file = Path(__file__).parent / "config.json"
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
    else:
        config = {{}}
        
    # Tool implementation
    try:
        {config.get('implementation', 'pass')}
    except Exception as e:
        print(f"Error: {{str(e)}}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
"""

    def _generate_argument_parser(self, arguments: List[Dict]) -> str:
        """Generate argument parser code"""
        lines = []
        for arg in arguments:
            flags = [f"'-{arg['short']}'"] if 'short' in arg else []
            flags.append(f"'--{arg['name']}'")
            
            kwargs = [f"help='{arg.get('help', '')}'"]
            if arg.get('required'):
                kwargs.append("required=True")
            if 'default' in arg:
                kwargs.append(f"default='{arg['default']}'")
            if arg.get('type'):
                kwargs.append(f"type={arg['type']}")
                
            lines.append(f"parser.add_argument({', '.join(flags)}, {', '.join(kwargs)})")
            
        return "\n    ".join(lines) 