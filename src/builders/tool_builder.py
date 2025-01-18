from pathlib import Path
import subprocess
import logging
from typing import Dict, List, Optional
import json
import shutil

class ToolBuilder:
    """Builds custom tools needed by the agent"""
    
    def __init__(self, tools_dir: Path):
        self.tools_dir = tools_dir
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        
    def build_tool(self, tool_spec: Dict) -> Optional[Path]:
        """Build a custom tool based on specifications"""
        try:
            tool_type = tool_spec.get('type', 'script')
            tool_name = tool_spec.get('name', 'custom_tool')
            
            if tool_type == 'script':
                return self._build_script_tool(tool_name, tool_spec)
            elif tool_type == 'api':
                return self._build_api_tool(tool_name, tool_spec)
            elif tool_type == 'scraper':
                return self._build_scraper_tool(tool_name, tool_spec)
            else:
                logging.error(f"Unknown tool type: {tool_type}")
                return None
                
        except Exception as e:
            logging.error(f"Error building tool {tool_spec.get('name')}: {str(e)}")
            return None
            
    def _build_script_tool(self, name: str, spec: Dict) -> Optional[Path]:
        """Build a Python script tool"""
        tool_dir = self.tools_dir / name
        tool_dir.mkdir(exist_ok=True)
        
        # Create main script
        script_content = self._generate_script_content(spec)
        script_path = tool_dir / f"{name}.py"
        
        with open(script_path, 'w') as f:
            f.write(script_content)
            
        # Create requirements.txt if needed
        if spec.get('dependencies'):
            with open(tool_dir / "requirements.txt", 'w') as f:
                f.write("\n".join(spec['dependencies']))
                
        return tool_dir
        
    def _build_api_tool(self, name: str, spec: Dict) -> Optional[Path]:
        """Build an API-based tool"""
        tool_dir = self.tools_dir / name
        tool_dir.mkdir(exist_ok=True)
        
        # Create FastAPI app
        app_content = self._generate_api_content(spec)
        app_path = tool_dir / "app.py"
        
        with open(app_path, 'w') as f:
            f.write(app_content)
            
        # Create requirements
        with open(tool_dir / "requirements.txt", 'w') as f:
            f.write("fastapi\nuvicorn\n")
            if spec.get('dependencies'):
                f.write("\n".join(spec['dependencies']))
                
        return tool_dir
        
    def _build_scraper_tool(self, name: str, spec: Dict) -> Optional[Path]:
        """Build a web scraper tool"""
        tool_dir = self.tools_dir / name
        tool_dir.mkdir(exist_ok=True)
        
        # Create scraper script
        scraper_content = self._generate_scraper_content(spec)
        scraper_path = tool_dir / f"{name}_scraper.py"
        
        with open(scraper_path, 'w') as f:
            f.write(scraper_content)
            
        # Create requirements
        with open(tool_dir / "requirements.txt", 'w') as f:
            f.write("beautifulsoup4\nrequests\naiohttp\n")
            if spec.get('dependencies'):
                f.write("\n".join(spec['dependencies']))
                
        return tool_dir
        
    def _generate_script_content(self, spec: Dict) -> str:
        """Generate Python script content"""
        imports = spec.get('imports', [])
        functions = spec.get('functions', [])
        
        content = []
        
        # Add imports
        for imp in imports:
            content.append(f"import {imp}")
            
        content.append("\n")
        
        # Add functions
        for func in functions:
            content.append(func)
            content.append("\n")
            
        # Add main block
        content.append("if __name__ == '__main__':")
        content.append("    main()")
        
        return "\n".join(content)
        
    def _generate_api_content(self, spec: Dict) -> str:
        """Generate FastAPI app content"""
        return f'''
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="{spec.get('name', 'Custom Tool')}")

{self._generate_api_models(spec.get('models', []))}

{self._generate_api_routes(spec.get('routes', []))}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
        
    def _generate_scraper_content(self, spec: Dict) -> str:
        """Generate web scraper content"""
        return '''
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import logging

class {0}:
    async def scrape_url(self, url: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    html = await response.text()
                    return self._parse_html(html)
                
        except Exception as e:
            logging.error(f"Error scraping {{url}}: {{str(e)}}")
            return None
            
    def _parse_html(self, html: str):
        soup = BeautifulSoup(html, 'html.parser')
        # Add custom parsing logic here
        return {{"status": "success"}}
'''.format(spec.get('name', 'CustomScraper'))
        
    def install_dependencies(self, tool_dir: Path) -> bool:
        """Install tool dependencies"""
        requirements_file = tool_dir / "requirements.txt"
        if not requirements_file.exists():
            return True
            
        try:
            subprocess.run(
                ['pip', 'install', '-r', str(requirements_file)],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Error installing dependencies: {e.stderr.decode()}")
            return False 