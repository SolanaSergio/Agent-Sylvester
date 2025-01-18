import subprocess
import shutil
import logging
from typing import List, Dict
import platform

class SystemChecker:
    """Checks system requirements and tool availability"""
    
    @staticmethod
    def check_requirements() -> Dict[str, bool]:
        """Check if all required tools are installed"""
        requirements = {
            'node': False,
            'npm': False,
            'git': False,
            'python': False
        }
        
        try:
            # Check Node.js
            node_version = subprocess.run(['node', '--version'], 
                                       capture_output=True, text=True)
            requirements['node'] = node_version.returncode == 0
            
            # Check npm
            npm_version = subprocess.run(['npm', '--version'], 
                                      capture_output=True, text=True)
            requirements['npm'] = npm_version.returncode == 0
            
            # Check Git
            git_version = subprocess.run(['git', '--version'], 
                                      capture_output=True, text=True)
            requirements['git'] = git_version.returncode == 0
            
            # Check Python version
            requirements['python'] = platform.python_version_tuple()[0] == '3'
            
        except Exception as e:
            logging.error(f"Error checking system requirements: {str(e)}")
            
        return requirements
        
    @staticmethod
    def verify_npm_packages(required_packages: List[str]) -> List[str]:
        """Verify if required npm packages are installed globally"""
        missing_packages = []
        
        for package in required_packages:
            try:
                result = subprocess.run(['npm', 'list', '-g', package], 
                                     capture_output=True, text=True)
                if result.returncode != 0:
                    missing_packages.append(package)
            except Exception as e:
                logging.error(f"Error checking npm package {package}: {str(e)}")
                missing_packages.append(package)
                
        return missing_packages
        
    @staticmethod
    def install_missing_packages(packages: List[str]) -> bool:
        """Install missing npm packages globally"""
        if not packages:
            return True
            
        try:
            for package in packages:
                subprocess.run(['npm', 'install', '-g', package], check=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Error installing npm packages: {str(e)}")
            return False 