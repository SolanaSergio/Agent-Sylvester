from pathlib import Path
import logging
import shutil
from typing import List, Dict, Optional

class ProjectStructure:
    """Manages project structure and directory operations"""
    
    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.scanner = ProjectStructureScanner()
        
    def create_base_structure(self):
        """Create the base project structure"""
        try:
            # Create main directories
            directories = [
                "src",
                "src/components",
                "src/pages",
                "src/styles",
                "src/utils",
                "src/api",
                "src/hooks",
                "src/types",
                "src/assets",
                "public",
                "tests",
                "docs"
            ]
            
            for directory in directories:
                (self.root / directory).mkdir(parents=True, exist_ok=True)
                
            # Create basic files
            self._create_base_files()
            
        except Exception as e:
            logging.error(f"Error creating project structure: {str(e)}")
            raise
            
    def _create_base_files(self):
        """Create basic project files"""
        try:
            # Create README.md
            readme = self.root / "README.md"
            if not readme.exists():
                readme.write_text("# Project\n\nDescription of your project goes here.")
                
            # Create .gitignore
            gitignore = self.root / ".gitignore"
            if not gitignore.exists():
                gitignore.write_text("node_modules\n.next\n.env\n.env.local\ndist\nbuild")
                
        except Exception as e:
            logging.error(f"Error creating base files: {str(e)}")
            raise
            
    def validate(self) -> List[str]:
        """Validate project structure and return any issues"""
        issues = []
        required_dirs = ["src", "public", "tests"]
        
        for dir_name in required_dirs:
            if not (self.root / dir_name).exists():
                issues.append(f"Missing required directory: {dir_name}")
                
        return issues
        
    def get_structure(self) -> Dict:
        """Get current project structure"""
        return self.scanner.scan_directory(str(self.root))
        
    def cleanup(self):
        """Clean up temporary files and directories"""
        try:
            temp_dirs = ["node_modules", ".next", "dist", "build"]
            for dir_name in temp_dirs:
                temp_dir = self.root / dir_name
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")
            raise

class ProjectStructureScanner:
    """Scans and validates project structure"""
    
    @staticmethod
    def scan_directory(path: str) -> dict:
        """Scan directory and return structure"""
        root = Path(path)
        return {
            "directories": ProjectStructureScanner._get_directories(root),
            "files": ProjectStructureScanner._get_files(root)
        }
        
    @staticmethod
    def _get_directories(path: Path) -> list:
        """Get all directories recursively"""
        dirs = []
        try:
            for item in path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    dirs.append({
                        "name": item.name,
                        "path": str(item),
                        "subdirs": ProjectStructureScanner._get_directories(item)
                    })
        except Exception as e:
            logging.error(f"Error scanning directories: {str(e)}")
        return dirs
        
    @staticmethod
    def _get_files(path: Path) -> list:
        """Get all files recursively"""
        files = []
        try:
            for item in path.iterdir():
                if item.is_file() and not item.name.startswith('.'):
                    files.append({
                        "name": item.name,
                        "path": str(item)
                    })
        except Exception as e:
            logging.error(f"Error scanning files: {str(e)}")
        return files 