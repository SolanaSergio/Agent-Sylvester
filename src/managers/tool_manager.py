from pathlib import Path
import logging
from typing import Dict, List, Optional
from ..builders.tool_builder import ToolBuilder

class ToolManager:
    """Manages custom tools needed by the agent"""
    
    def __init__(self, tools_dir: Path):
        self.tools_dir = tools_dir
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self.tool_builder = ToolBuilder(tools_dir)
        self.available_tools: Dict[str, Path] = {}
        
    def get_or_create_tool(self, tool_spec: Dict) -> Optional[Path]:
        """Get an existing tool or create a new one"""
        tool_name = tool_spec.get('name')
        
        if tool_name in self.available_tools:
            return self.available_tools[tool_name]
            
        tool_path = self.tool_builder.build_tool(tool_spec)
        if tool_path:
            self.available_tools[tool_name] = tool_path
            if self.tool_builder.install_dependencies(tool_path):
                return tool_path
                
        return None
        
    def determine_needed_tools(self, requirements: Dict) -> List[Dict]:
        """Determine which tools need to be created based on requirements"""
        needed_tools = []
        
        # Check if we need a scraper
        if any(url in str(requirements) for url in ['http://', 'https://']):
            needed_tools.append({
                'name': 'custom_scraper',
                'type': 'scraper',
                'dependencies': ['beautifulsoup4', 'aiohttp']
            })
            
        # Check if we need an API tool
        if 'api' in requirements.get('features', []):
            needed_tools.append({
                'name': 'api_handler',
                'type': 'api',
                'dependencies': ['fastapi', 'requests']
            })
            
        # Check if we need data processing
        if 'database' in requirements.get('features', []):
            needed_tools.append({
                'name': 'data_processor',
                'type': 'script',
                'imports': ['pandas', 'numpy'],
                'dependencies': ['pandas', 'numpy']
            })
            
        return needed_tools
        
    def cleanup_tools(self):
        """Clean up temporary tool files"""
        try:
            import shutil
            for tool_path in self.available_tools.values():
                if (tool_path / "temp").exists():
                    shutil.rmtree(tool_path / "temp")
        except Exception as e:
            logging.error(f"Error cleaning up tools: {str(e)}") 