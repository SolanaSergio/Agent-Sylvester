from typing import Dict, List
import re
from bs4 import BeautifulSoup
from ..utils.types import Pattern, LayoutType

class PatternAnalyzer:
    @staticmethod
    def extract_patterns(html: str) -> Dict[str, List[str]]:
        """Extract UI patterns from HTML content"""
        patterns = {
            'layout': [],
            'components': [],
            'styles': [],
            'responsive': [],
            'accessibility': [],
            'interaction': []
        }
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract patterns
        patterns['layout'].extend(PatternAnalyzer._find_layout_patterns(soup))
        patterns['components'].extend(PatternAnalyzer._find_component_patterns(soup))
        patterns['styles'].extend(PatternAnalyzer._find_style_patterns(soup))
        patterns['responsive'].extend(PatternAnalyzer._find_responsive_patterns(soup))
        patterns['accessibility'].extend(PatternAnalyzer._find_accessibility_patterns(soup))
        patterns['interaction'].extend(PatternAnalyzer._find_interaction_patterns(soup))
        
        return patterns
        
    @staticmethod
    def _find_layout_patterns(soup: BeautifulSoup) -> List[str]:
        """Find common layout patterns"""
        patterns = []
        
        # Grid layouts
        if soup.select('[class*="grid"]'):
            patterns.append('grid-layout')
            
        # Flexbox layouts
        if soup.select('[class*="flex"]'):
            patterns.append('flexbox-layout')
            
        # Container patterns
        containers = soup.select('.container, [class*="container"]')
        if containers:
            patterns.append('container-based')
            
        # Column layouts
        if soup.select('[class*="col-"], [class*="column"]'):
            patterns.append('column-based')
            
        # Sidebar layouts
        if soup.select('aside, [class*="sidebar"], [class*="side-"]'):
            patterns.append('sidebar-layout')
            
        # Card layouts
        if soup.select('[class*="card"], [class*="tile"]'):
            patterns.append('card-layout')
            
        # List layouts
        if soup.select('ul, ol'):
            patterns.append('list-layout')
            
        return patterns
        
    @staticmethod
    def _find_component_patterns(soup: BeautifulSoup) -> List[str]:
        """Find common component patterns"""
        patterns = []
        
        # Navigation components
        if soup.select('nav, [role="navigation"]'):
            patterns.append('navigation')
            
        # Form components
        if soup.select('form'):
            patterns.append('form')
            if soup.select('form [class*="group"]'):
                patterns.append('form-group')
                
        # Button components
        if soup.select('button, [class*="btn"], [role="button"]'):
            patterns.append('button')
            
        # Card components
        if soup.select('[class*="card"]'):
            patterns.append('card')
            
        # Modal/Dialog components
        if soup.select('[role="dialog"], [class*="modal"]'):
            patterns.append('modal')
            
        # Tab components
        if soup.select('[role="tablist"], [class*="tab"]'):
            patterns.append('tabs')
            
        # Alert/Notification components
        if soup.select('[role="alert"], [class*="alert"], [class*="notification"]'):
            patterns.append('alert')
            
        # Dropdown components
        if soup.select('select, [class*="dropdown"]'):
            patterns.append('dropdown')
            
        return patterns
        
    @staticmethod
    def _find_style_patterns(soup: BeautifulSoup) -> List[str]:
        """Find common style patterns"""
        patterns = []
        
        # Color schemes
        classes = ' '.join([tag.get('class', []) for tag in soup.find_all()])
        if re.search(r'dark|light|theme', classes):
            patterns.append('theme-switching')
            
        # Typography patterns
        if soup.select('[class*="text-"], [class*="font-"]'):
            patterns.append('typography-system')
            
        # Spacing patterns
        if soup.select('[class*="space-"], [class*="gap-"], [class*="margin-"], [class*="padding-"]'):
            patterns.append('spacing-system')
            
        # Border patterns
        if soup.select('[class*="border-"], [class*="rounded-"]'):
            patterns.append('border-system')
            
        # Shadow patterns
        if soup.select('[class*="shadow-"]'):
            patterns.append('shadow-system')
            
        return patterns
        
    @staticmethod
    def _find_responsive_patterns(soup: BeautifulSoup) -> List[str]:
        """Find responsive design patterns"""
        patterns = []
        
        # Media query patterns
        classes = ' '.join([tag.get('class', []) for tag in soup.find_all()])
        breakpoints = ['sm', 'md', 'lg', 'xl', '2xl']
        
        for breakpoint in breakpoints:
            if re.search(fr'{breakpoint}:', classes):
                patterns.append(f'responsive-{breakpoint}')
                
        # Mobile-first patterns
        if soup.select('[class*="mobile-"], [class*="sm:"]'):
            patterns.append('mobile-first')
            
        # Container queries
        if soup.select('[class*="container-"]'):
            patterns.append('container-queries')
            
        return patterns
        
    @staticmethod
    def _find_accessibility_patterns(soup: BeautifulSoup) -> List[str]:
        """Find accessibility patterns"""
        patterns = []
        
        # ARIA roles
        if soup.select('[role]'):
            patterns.append('aria-roles')
            
        # ARIA labels
        if soup.select('[aria-label], [aria-labelledby]'):
            patterns.append('aria-labels')
            
        # Focus management
        if soup.select('[tabindex]'):
            patterns.append('focus-management')
            
        # Skip links
        if soup.select('a[href="#main"], a[href="#content"]'):
            patterns.append('skip-links')
            
        # Form labels
        if soup.select('label[for]'):
            patterns.append('form-labels')
            
        return patterns
        
    @staticmethod
    def _find_interaction_patterns(soup: BeautifulSoup) -> List[str]:
        """Find user interaction patterns"""
        patterns = []
        
        # Click handlers
        if soup.select('[onclick], [class*="click"]'):
            patterns.append('click-handlers')
            
        # Hover effects
        if soup.select('[class*="hover:"]'):
            patterns.append('hover-effects')
            
        # Focus states
        if soup.select('[class*="focus:"]'):
            patterns.append('focus-states')
            
        # Active states
        if soup.select('[class*="active:"]'):
            patterns.append('active-states')
            
        # Disabled states
        if soup.select('[disabled], [class*="disabled:"]'):
            patterns.append('disabled-states')
            
        # Loading states
        if soup.select('[class*="loading"], [aria-busy="true"]'):
            patterns.append('loading-states')
            
        return patterns
        
    @staticmethod
    def analyze_layout_structure(soup: BeautifulSoup) -> LayoutType:
        """Analyze and determine the overall layout structure"""
        # Check for common layout structures
        if soup.select('body > header ~ main ~ footer'):
            return LayoutType.STANDARD
        elif soup.select('body > header ~ aside ~ main ~ footer'):
            return LayoutType.DASHBOARD
        elif soup.select('body > main:only-child'):
            return LayoutType.SINGLE_PAGE
        elif soup.select('body > [class*="landing"]'):
            return LayoutType.LANDING
        else:
            return LayoutType.CUSTOM 