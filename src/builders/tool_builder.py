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
        
        if new_content != current_content:
            main_script.write_text(new_content)
            
        # Update helper modules
        if config.get('helpers'):
            helpers_dir = tool_dir / "helpers"
            helpers_dir.mkdir(exist_ok=True)
            
            # Get current helper files
            current_helpers = {f.stem: f for f in helpers_dir.glob("*.py")}
            
            # Update/create new helpers
            for helper in config['helpers']:
                helper_file = helpers_dir / f"{helper['name']}.py"
                if helper_file.exists():
                    current_content = helper_file.read_text()
                    if current_content != helper['content']:
                        helper_file.write_text(helper['content'])
                else:
                    helper_file.write_text(helper['content'])
                    
                # Remove from current_helpers dict to track obsolete files
                current_helpers.pop(helper['name'], None)
                
            # Remove obsolete helper files
            for obsolete_file in current_helpers.values():
                obsolete_file.unlink()

    def _get_tool_template(self, config: Dict) -> str:
        """Get the template for the main tool script"""
        template = [
            "#!/usr/bin/env python3",
            "import argparse",
            "import sys",
            "import json",
            "from pathlib import Path",
            ""
        ]
        
        # Add imports from helpers
        if config.get('helpers'):
            template.extend([
                "from helpers import *",
                ""
            ])
            
        # Add main class
        template.extend([
            f"class {config['name'].title()}Tool:",
            "    def __init__(self):",
            "        self.config = self._load_config()",
            "",
            "    def _load_config(self):",
            "        config_file = Path(__file__).parent / 'config.json'",
            "        if config_file.exists():",
            "            return json.loads(config_file.read_text())",
            "        return {}"
        ])
        
        # Add methods
        for method in config.get('methods', []):
            template.extend([
                "",
                f"    def {method['name']}(self, args):",
                f"        \"\"\"{method.get('description', '')}\"\"\""
            ])
            template.extend([f"        {line}" for line in method.get('implementation', [])])
            
        # Add main execution
        template.extend([
            "",
            "def main():",
            "    parser = argparse.ArgumentParser(description='" + config.get('description', '') + "')"
        ])
        
        # Add argument parsing
        if config.get('arguments'):
            template.append(self._generate_argument_parser(config['arguments']))
            
        template.extend([
            "    args = parser.parse_args()",
            f"    tool = {config['name'].title()}Tool()",
            "    # Execute requested command",
            "    if hasattr(args, 'func'):",
            "        args.func(args)",
            "    else:",
            "        parser.print_help()",
            "",
            "if __name__ == '__main__':",
            "    main()"
        ])
        
        return "\n".join(template)

    def _generate_argument_parser(self, arguments: List[Dict]) -> str:
        """Generate argument parser code for the tool"""
        parser_code = []
        
        # Add subparsers if we have multiple commands
        if len(arguments) > 1:
            parser_code.extend([
                "    subparsers = parser.add_subparsers(help='Available commands')"
            ])
            
            # Add each command's subparser
            for arg in arguments:
                name = arg['name']
                help_text = arg.get('help', '')
                parser_code.extend([
                    f"    {name}_parser = subparsers.add_parser('{name}', help='{help_text}')",
                ])
                
                # Add command-specific arguments
                for param in arg.get('parameters', []):
                    flags = [f"'-{param['short']}'"] if 'short' in param else []
                    flags.append(f"'--{param['name']}'")
                    
                    parser_code.append(
                        f"    {name}_parser.add_argument({', '.join(flags)}, "
                        f"type={param.get('type', 'str')}, "
                        f"help='{param.get('help', '')}')"
                    )
                    
                # Set the function to call for this command
                parser_code.append(f"    {name}_parser.set_defaults(func=tool.{name})")
                
        else:
            # Single command tool - add arguments directly to main parser
            for param in arguments[0].get('parameters', []):
                flags = [f"'-{param['short']}'"] if 'short' in param else []
                flags.append(f"'--{param['name']}'")
                
                parser_code.append(
                    f"    parser.add_argument({', '.join(flags)}, "
                    f"type={param.get('type', 'str')}, "
                    f"help='{param.get('help', '')}')"
                )
                
            # Set the function to call
            parser_code.append(f"    parser.set_defaults(func=tool.{arguments[0]['name']})")
            
        return "\n".join(parser_code) 