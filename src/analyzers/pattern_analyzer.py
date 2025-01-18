from typing import Dict, List, Optional
from pathlib import Path
import ast
import re
from src.utils.types import Pattern, StylePattern, LayoutPattern, AccessibilityPattern, InteractionPattern, ResponsivePattern

class PatternAnalyzer:
    """Analyzes project patterns and structures"""
    
    def __init__(self):
        self.project_dir: Optional[Path] = None

    async def analyze_patterns(self, project_path: Optional[Path] = None) -> Dict:
        """Analyze all patterns in the project"""
        if project_path:
            self.project_dir = project_path
        elif not self.project_dir:
            raise ValueError("Project directory not set")

        if not self.project_dir.exists():
            raise ValueError(f"Project directory {self.project_dir} does not exist")

        try:
            return {
                "components": await self._analyze_component_patterns(),
                "styles": await self._analyze_style_patterns(),
                "layout": await self._analyze_layout_patterns(),
                "accessibility": await self._analyze_accessibility_patterns(),
                "interaction": await self._analyze_interaction_patterns(),
                "responsive": await self._analyze_responsive_patterns()
            }
        except Exception as e:
            raise Exception(f"Error analyzing patterns: {str(e)}")

    async def _analyze_component_patterns(self) -> List[Pattern]:
        """Analyze component patterns"""
        patterns = []
        components_dir = self.project_dir / "src/components"
        
        if not components_dir.exists():
            return patterns
            
        # Analyze component files
        for file_path in components_dir.glob("**/*.{tsx,jsx}"):
            try:
                with open(file_path) as f:
                    content = f.read()
                    
                # Parse the component
                tree = ast.parse(content)
                
                # Extract component elements and attributes
                elements = self._extract_elements(content)
                attributes = self._extract_attributes(content)
                
                # Calculate frequency and confidence
                frequency = len(elements)
                confidence = self._calculate_pattern_confidence(elements, attributes)
                
                patterns.append(Pattern(
                    type="component",
                    name=file_path.stem,
                    frequency=frequency,
                    confidence=confidence,
                    elements=elements,
                    attributes=attributes
                ))
            except Exception as e:
                # Log error but continue with other components
                import logging
                logging.error(f"Error analyzing component {file_path}: {str(e)}")
                continue
                
        return patterns

    async def _analyze_style_patterns(self) -> List[StylePattern]:
        """Analyze style patterns"""
        patterns = []
        styles_dir = self.project_dir / "src/styles"
        
        if not styles_dir.exists():
            return patterns
            
        # Analyze style files
        for file_path in styles_dir.glob("**/*.{css,scss}"):
            try:
                with open(file_path) as f:
                    content = f.read()
                    
                # Extract colors
                colors = re.findall(r'#[0-9a-fA-F]{3,6}|rgb\([^)]+\)|rgba\([^)]+\)', content)
                if colors:
                    patterns.append(StylePattern(
                        type="color",
                        values=list(set(colors)),
                        frequency=len(colors),
                        context=file_path.stem
                    ))
                    
                # Extract spacing patterns
                spacing_patterns = re.findall(r'margin|padding|gap|space-[xy]', content)
                if spacing_patterns:
                    patterns.append(StylePattern(
                        type="spacing",
                        values=list(set(spacing_patterns)),
                        frequency=len(spacing_patterns),
                        context=file_path.stem
                    ))
                    
                # Extract typography patterns
                typography_patterns = re.findall(r'font-(?:family|size|weight)|line-height|letter-spacing', content)
                if typography_patterns:
                    patterns.append(StylePattern(
                        type="typography",
                        values=list(set(typography_patterns)),
                        frequency=len(typography_patterns),
                        context=file_path.stem
                    ))
            except Exception as e:
                import logging
                logging.error(f"Error analyzing styles in {file_path}: {str(e)}")
                continue
                
        return patterns

    def _extract_elements(self, content: str) -> List[str]:
        """Extract HTML/JSX elements from component content"""
        # Simple regex for element extraction - could be improved with a proper parser
        element_pattern = r"<([a-zA-Z][a-zA-Z0-9]*)"
        return [match.group(1) for match in re.finditer(element_pattern, content)]

    def _extract_attributes(self, content: str) -> Dict[str, str]:
        """Extract element attributes from component content"""
        # Simple regex for attribute extraction - could be improved with a proper parser
        attr_pattern = r'([a-zA-Z][a-zA-Z0-9]*)=["\'](.*?)["\']'
        return {match.group(1): match.group(2) for match in re.finditer(attr_pattern, content)}

    def _calculate_pattern_confidence(self, elements: List[str], attributes: Dict[str, str]) -> float:
        """Calculate confidence score for a pattern"""
        if not elements:
            return 0.0
            
        # Simple confidence calculation based on number of elements and attributes
        base_confidence = min(len(elements) / 10.0, 1.0)  # More elements = higher confidence, up to 1.0
        attr_bonus = min(len(attributes) / 20.0, 0.5)     # More attributes = bonus confidence, up to 0.5
        
        return min(base_confidence + attr_bonus, 1.0)      # Total confidence capped at 1.0

    async def _analyze_layout_patterns(self) -> List[LayoutPattern]:
        """Analyze layout patterns"""
        patterns = []
        components_dir = self.project_dir / "src/components"
        
        if not components_dir.exists():
            return patterns
            
        # Analyze layout files
        layout_files = list(components_dir.glob("**/Layout*.{tsx,jsx}"))
        layout_files.extend(components_dir.glob("**/Page*.{tsx,jsx}"))
        
        for file_path in layout_files:
            try:
                with open(file_path) as f:
                    content = f.read()
                    
                # Extract structure
                structure = self._extract_layout_structure(content)
                nesting_level = self._calculate_nesting_level(content)
                grid_system = self._detect_grid_system(content)
                breakpoints = self._extract_breakpoints(content)
                
                patterns.append(LayoutPattern(
                    type=self._determine_layout_type(structure),
                    structure=structure,
                    nesting_level=nesting_level,
                    grid_system=grid_system,
                    breakpoints=breakpoints
                ))
            except Exception as e:
                import logging
                logging.error(f"Error analyzing layout in {file_path}: {str(e)}")
                continue
                
        return patterns

    async def _analyze_accessibility_patterns(self) -> List[AccessibilityPattern]:
        """Analyze accessibility patterns"""
        patterns = []
        components_dir = Path("src/components")
        
        if not components_dir.exists():
            return patterns
            
        # Analyze all component files
        for file_path in components_dir.glob("**/*.{tsx,jsx}"):
            with open(file_path) as f:
                content = f.read()
                
            # Extract accessibility information
            aria_roles = re.findall(r'role=["\']([^"\']+)["\']', content)
            aria_attrs = self._extract_aria_attributes(content)
            semantic_elements = self._extract_semantic_elements(content)
            
            if aria_roles or aria_attrs or semantic_elements:
                patterns.append(AccessibilityPattern(
                    type=self._determine_accessibility_type(aria_roles, semantic_elements),
                    aria_roles=list(set(aria_roles)),
                    aria_attributes=aria_attrs,
                    semantic_elements=list(set(semantic_elements))
                ))
                
        return patterns

    async def _analyze_interaction_patterns(self) -> List[InteractionPattern]:
        """Analyze interaction patterns"""
        patterns = []
        components_dir = Path("src/components")
        
        if not components_dir.exists():
            return patterns
            
        # Analyze all component files
        for file_path in components_dir.glob("**/*.{tsx,jsx}"):
            with open(file_path) as f:
                content = f.read()
                
            # Extract interaction patterns
            events = self._extract_events(content)
            states = self._extract_states(content)
            animations = self._extract_animations(content)
            transitions = self._extract_transitions(content)
            
            if events or states or animations or transitions:
                patterns.append(InteractionPattern(
                    type=self._determine_interaction_type(events, states),
                    events=list(set(events)),
                    states=list(set(states)),
                    animations=list(set(animations)),
                    transitions=list(set(transitions))
                ))
                
        return patterns

    def _extract_layout_structure(self, content: str) -> Dict[str, List[str]]:
        """Extract layout structure from component content"""
        structure = {}
        
        # Find main sections
        sections = re.findall(r'<([a-zA-Z]+)[^>]*className=["\'][^"\']*(?:header|footer|main|sidebar|content)[^"\']*["\'][^>]*>', content)
        
        for section in sections:
            # Find children of each section
            section_content = re.findall(rf'<{section}[^>]*>(.*?)</{section}>', content, re.DOTALL)
            if section_content:
                children = re.findall(r'<([a-zA-Z]+)[^>]*>', section_content[0])
                structure[section.lower()] = list(set(children))
                
        return structure

    def _calculate_nesting_level(self, content: str) -> int:
        """Calculate maximum nesting level in component"""
        max_level = 0
        current_level = 0
        
        for char in content:
            if char == '<':
                current_level += 1
                max_level = max(max_level, current_level)
            elif char == '>':
                current_level -= 1
                
        return max_level

    def _detect_grid_system(self, content: str) -> Optional[str]:
        """Detect grid system used in component"""
        if 'grid' in content.lower():
            return 'grid'
        elif 'flex' in content.lower():
            return 'flex'
        return None

    def _extract_breakpoints(self, content: str) -> List[str]:
        """Extract breakpoint definitions from component"""
        breakpoints = set()
        
        # Look for Tailwind breakpoints
        tailwind_matches = re.findall(r'(sm|md|lg|xl|2xl):', content)
        if tailwind_matches:
            breakpoints.update(tailwind_matches)
            
        # Look for media queries
        media_matches = re.findall(r'@media[^{]+\(([^)]+)\)', content)
        if media_matches:
            breakpoints.update(media_matches)
            
        return list(breakpoints)

    def _determine_layout_type(self, structure: Dict[str, List[str]]) -> str:
        """Determine layout type based on structure"""
        if 'sidebar' in structure and 'main' in structure:
            return 'DASHBOARD'
        elif len(structure) == 1 and 'main' in structure:
            return 'SINGLE_PAGE'
        elif 'header' in structure and 'footer' in structure:
            return 'STANDARD'
        return 'CUSTOM'

    def _extract_aria_attributes(self, content: str) -> Dict[str, str]:
        """Extract ARIA attributes from component"""
        aria_attrs = {}
        matches = re.findall(r'aria-([a-zA-Z]+)=["\']([^"\']+)["\']', content)
        for attr, value in matches:
            aria_attrs[f"aria-{attr}"] = value
        return aria_attrs

    def _extract_semantic_elements(self, content: str) -> List[str]:
        """Extract semantic HTML elements from component"""
        semantic_elements = {'header', 'main', 'footer', 'nav', 'article', 'section', 'aside'}
        matches = re.findall(r'<([a-zA-Z]+)[^>]*>', content)
        return [elem for elem in matches if elem in semantic_elements]

    def _determine_accessibility_type(self, roles: List[str], elements: List[str]) -> str:
        """Determine accessibility pattern type"""
        if 'navigation' in roles or 'nav' in elements:
            return 'navigation'
        elif 'form' in roles or 'form' in elements:
            return 'form'
        elif 'button' in roles or 'button' in elements:
            return 'interactive'
        return 'content'

    def _extract_events(self, content: str) -> List[str]:
        """Extract event handlers from component"""
        events = set()
        matches = re.findall(r'on([A-Z][a-zA-Z]+)=["\']', content)
        for match in matches:
            events.add(match.lower())
        return list(events)

    def _extract_states(self, content: str) -> List[str]:
        """Extract state definitions from component"""
        states = set()
        state_patterns = [
            r'(?:hover|focus|active|disabled|selected|checked|loading|error|success)',
            r'(?:useState|state\.)[a-zA-Z]+'
        ]
        
        for pattern in state_patterns:
            matches = re.findall(pattern, content)
            states.update(matches)
            
        return list(states)

    def _extract_animations(self, content: str) -> List[str]:
        """Extract animation definitions from component"""
        animations = set()
        
        # Look for CSS animations
        css_matches = re.findall(r'animation(?:-name)?:\s*([^;]+);', content)
        animations.update(css_matches)
        
        # Look for Framer Motion animations
        if 'framer-motion' in content:
            motion_matches = re.findall(r'animate=\{([^}]+)\}', content)
            animations.update(motion_matches)
            
        return list(animations)

    def _extract_transitions(self, content: str) -> List[str]:
        """Extract transition definitions from component"""
        transitions = set()
        
        # Look for CSS transitions
        css_matches = re.findall(r'transition(?:-property)?:\s*([^;]+);', content)
        for match in css_matches:
            transitions.update(prop.strip() for prop in match.split(','))
            
        return list(transitions)

    def _determine_interaction_type(self, events: List[str], states: List[str]) -> str:
        """Determine interaction pattern type"""
        if 'click' in events or 'button' in str(states):
            return 'button'
        elif 'change' in events or 'input' in events:
            return 'form'
        elif 'hover' in events or 'hover' in str(states):
            return 'hover'
        return 'custom'

    async def _analyze_responsive_patterns(self) -> List[ResponsivePattern]:
        """Analyze responsive design patterns"""
        patterns = []
        components_dir = Path("src/components")
        styles_dir = Path("src/styles")
        
        # Analyze component files
        if components_dir.exists():
            for file_path in components_dir.glob("**/*.{tsx,jsx}"):
                with open(file_path) as f:
                    content = f.read()
                    
                # Extract breakpoints and rules
                breakpoints = self._extract_breakpoints(content)
                rules = self._extract_responsive_rules(content)
                mobile_first = self._is_mobile_first(content)
                container_queries = self._has_container_queries(content)
                
                if breakpoints or rules:
                    patterns.append(ResponsivePattern(
                        breakpoints=breakpoints,
                        rules=rules,
                        mobile_first=mobile_first,
                        container_queries=container_queries
                    ))
                    
        # Analyze style files
        if styles_dir.exists():
            for file_path in styles_dir.glob("**/*.{css,scss}"):
                with open(file_path) as f:
                    content = f.read()
                    
                breakpoints = self._extract_breakpoints(content)
                rules = self._extract_responsive_rules(content)
                mobile_first = self._is_mobile_first(content)
                container_queries = self._has_container_queries(content)
                
                if breakpoints or rules:
                    patterns.append(ResponsivePattern(
                        breakpoints=breakpoints,
                        rules=rules,
                        mobile_first=mobile_first,
                        container_queries=container_queries
                    ))
                    
        return patterns

    def _extract_responsive_rules(self, content: str) -> Dict[str, List[str]]:
        """Extract responsive design rules from content"""
        rules = {
            "layout": [],
            "visibility": [],
            "typography": [],
            "spacing": []
        }
        
        # Extract layout rules
        layout_patterns = [
            r'flex(?:-[a-z]+)?',
            r'grid(?:-[a-z]+)?',
            r'block|inline|none'
        ]
        
        for pattern in layout_patterns:
            matches = re.findall(pattern, content)
            if matches:
                rules["layout"].extend(matches)
                
        # Extract visibility rules
        visibility_matches = re.findall(r'hidden|visible|invisible', content)
        rules["visibility"].extend(visibility_matches)
        
        # Extract typography rules
        typography_matches = re.findall(r'text-(?:sm|base|lg|xl|2xl)', content)
        rules["typography"].extend(typography_matches)
        
        # Extract spacing rules
        spacing_matches = re.findall(r'(?:m|p)[xy]?-[0-9]+', content)
        rules["spacing"].extend(spacing_matches)
        
        # Remove duplicates and empty lists
        return {k: list(set(v)) for k, v in rules.items() if v}

    def _is_mobile_first(self, content: str) -> bool:
        """Determine if the design approach is mobile-first"""
        # Check for min-width queries (mobile-first approach)
        min_width_count = len(re.findall(r'min-width', content))
        max_width_count = len(re.findall(r'max-width', content))
        
        # If there are more min-width queries, it's likely mobile-first
        return min_width_count > max_width_count

    def _has_container_queries(self, content: str) -> bool:
        """Check if container queries are used"""
        container_patterns = [
            r'@container',
            r'container-type:',
            r'container:\s*[a-z]+',
        ]
        
        return any(re.search(pattern, content) for pattern in container_patterns)

    async def analyze_project_structure(self, project_dir: Path) -> Dict:
        """Analyze project directory structure"""
        try:
            structure = {
                "components": self._scan_directory(project_dir / "src/components"),
                "pages": self._scan_directory(project_dir / "src/pages"),
                "styles": self._scan_directory(project_dir / "src/styles"),
                "public": self._scan_directory(project_dir / "public")
            }
            return structure
        except Exception as e:
            raise Exception(f"Error analyzing project structure: {str(e)}")

    def _scan_directory(self, directory: Path) -> Dict:
        """Scan directory and return file structure"""
        if not directory.exists():
            return {}
            
        structure = {}
        for item in directory.iterdir():
            if item.is_file():
                structure[item.name] = "file"
            elif item.is_dir():
                structure[item.name] = self._scan_directory(item)
        return structure 