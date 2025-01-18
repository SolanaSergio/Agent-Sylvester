from pathlib import Path
import logging

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