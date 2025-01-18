import subprocess
import shutil
import logging
from typing import List, Dict
import platform
import sys

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
            try:
                node_version = subprocess.run(['node', '--version'], 
                                           capture_output=True, text=True,
                                           shell=True)
                requirements['node'] = node_version.returncode == 0
            except Exception:
                requirements['node'] = False
            
            # Check npm
            try:
                npm_version = subprocess.run(['npm', '--version'], 
                                          capture_output=True, text=True,
                                          shell=True)
                requirements['npm'] = npm_version.returncode == 0
            except Exception:
                requirements['npm'] = False
            
            # Check Git
            try:
                git_version = subprocess.run(['git', '--version'], 
                                          capture_output=True, text=True,
                                          shell=True)
                requirements['git'] = git_version.returncode == 0
            except Exception:
                requirements['git'] = False
            
            # Check Python version (3.6 or higher)
            python_version = sys.version_info
            requirements['python'] = python_version.major == 3 and python_version.minor >= 6
            
        except Exception as e:
            logging.error(f"Error checking system requirements: {str(e)}")
            raise RuntimeError(f"Failed to check system requirements: {str(e)}")
            
        return requirements
        
    @staticmethod
    def verify_npm_packages(required_packages: List[str]) -> List[str]:
        """Verify if required npm packages are installed globally"""
        missing_packages = []
        
        for package in required_packages:
            try:
                result = subprocess.run(['npm', 'list', '-g', package], 
                                     capture_output=True, text=True,
                                     shell=True)
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
                subprocess.run(['npm', 'install', '-g', package], 
                             check=True, shell=True)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Error installing npm packages: {str(e)}")
            return False 