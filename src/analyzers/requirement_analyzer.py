from typing import Dict, List
import re
import logging
from ..utils.constants import FEATURE_KEYWORDS

class RequirementAnalyzer:
    def analyze_requirements(self, text: str) -> Dict:
        """Analyze text to extract detailed project requirements"""
        requirements = {
            'project_type': self._determine_project_type(text),
            'features': self._extract_features(text),
            'components': self._extract_components(text),
            'styling': self._determine_styling_approach(text),
            'dependencies': self._determine_dependencies(text),
            'deployment': self._extract_deployment_requirements(text),
            'ai_integration': self._detect_ai_requirements(text),
            'security': self._analyze_security_requirements(text),
            'performance': self._analyze_performance_requirements(text)
        }
        
        # Enhance requirements based on dependencies
        self._enhance_requirements(requirements)
        
        logging.debug(f"Analyzed requirements: {requirements}")
        return requirements
        
    def _determine_project_type(self, text: str) -> str:
        """Determine the type of project needed"""
        text = text.lower()
        
        # Framework detection
        frameworks = {
            'next.js': ['next.js', 'nextjs', 'next'],
            'react': ['react', 'create-react-app', 'cra'],
            'vue': ['vue', 'vuejs', 'vue.js', 'nuxt'],
            'angular': ['angular', 'ng'],
            'svelte': ['svelte', 'sveltekit'],
        }
        
        for framework, keywords in frameworks.items():
            if any(keyword in text for keyword in keywords):
                return framework
                
        # Project type detection
        if 'static' in text:
            return 'static-site'
        elif 'mobile' in text or 'app' in text:
            return 'progressive-web-app'
        elif 'dashboard' in text or 'admin' in text:
            return 'admin-dashboard'
        elif 'api' in text or 'backend' in text:
            return 'api-service'
            
        return 'next.js'  # Default to Next.js for best features
        
    def _extract_features(self, text: str) -> List[str]:
        """Extract required features from text"""
        features = []
        text = text.lower()
        
        # Core features
        feature_patterns = {
            'authentication': [r'auth\w*', r'login', r'signin', r'signup', r'user.?account'],
            'database': [r'database', r'db', r'data.?storage', r'persist\w*'],
            'api': [r'api', r'endpoint', r'rest', r'graphql'],
            'real-time': [r'real.?time', r'live', r'socket', r'stream'],
            'file-upload': [r'upload', r'file.?handling', r'storage'],
            'search': [r'search', r'filter', r'find'],
            'analytics': [r'analytic', r'track', r'monitor', r'metric'],
            'notifications': [r'notif\w*', r'alert', r'message'],
            'payments': [r'payment', r'stripe', r'checkout', r'subscription'],
            'email': [r'email', r'smtp', r'mail'],
            'seo': [r'seo', r'meta.?tag', r'sitemap'],
            'i18n': [r'i18n', r'translation', r'language', r'localization'],
            'accessibility': [r'a11y', r'accessibility', r'wcag'],
            'dark-mode': [r'dark.?mode', r'theme', r'color.?scheme']
        }
        
        for feature, patterns in feature_patterns.items():
            if any(re.search(pattern, text) for pattern in patterns):
                features.append(feature)
                
        return features
        
    def _extract_components(self, text: str) -> List[str]:
        """Extract required UI components"""
        components = []
        
        # Component patterns with variations
        component_patterns = [
            (r'(?:need|want|require|include|add|with)\s+(?:a|an|the)?\s*(\w+(?:\s+\w+)*?)\s+(?:component|section|element|part)', 1),
            (r'should\s+have\s+(?:a|an|the)?\s*(\w+(?:\s+\w+)*?)\s+(?:component|section|element|part)', 1),
            (r'include\s+(?:a|an|the)?\s*(\w+(?:\s+\w+)*?)\s+functionality', 1)
        ]
        
        # Common components to detect
        common_components = {
            'header': [r'header', r'nav\w*', r'top.?bar'],
            'footer': [r'footer', r'bottom'],
            'sidebar': [r'sidebar', r'side.?nav'],
            'modal': [r'modal', r'dialog', r'popup'],
            'form': [r'form', r'input'],
            'table': [r'table', r'grid', r'data.?view'],
            'card': [r'card', r'tile'],
            'button': [r'button', r'cta'],
            'dropdown': [r'dropdown', r'select'],
            'tabs': [r'tab', r'panel'],
            'carousel': [r'carousel', r'slider', r'gallery']
        }
        
        # Extract explicit component requirements
        for pattern, group in component_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            components.extend(match.group(group).strip() for match in matches)
            
        # Detect common components
        for component, patterns in common_components.items():
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                components.append(component)
                
        return list(set(components))  # Remove duplicates
        
    def _determine_styling_approach(self, text: str) -> Dict[str, bool]:
        """Determine the styling approach to use"""
        text = text.lower()
        
        approaches = {
            'tailwind': bool(re.search(r'tailwind', text)),
            'css_modules': bool(re.search(r'css.?modules?', text)),
            'styled_components': bool(re.search(r'styled.?components?', text)),
            'sass': bool(re.search(r'sass|scss', text)),
            'material_ui': bool(re.search(r'material.?ui|mui', text)),
            'chakra_ui': bool(re.search(r'chakra', text)),
            'bootstrap': bool(re.search(r'bootstrap', text))
        }
        
        # If no specific approach mentioned, recommend modern stack
        if not any(approaches.values()):
            approaches['tailwind'] = True
            
        return approaches
        
    def _determine_dependencies(self, text: str) -> Dict[str, str]:
        """Determine required dependencies and their versions"""
        dependencies = {
            'react': '^18.2.0',
            'react-dom': '^18.2.0',
            'next': '^13.4.0',
            'typescript': '^5.0.0',
            '@types/react': '^18.2.0',
            '@types/node': '^18.0.0',
        }
        
        features = self._extract_features(text)
        
        # Add feature-specific dependencies
        if 'authentication' in features:
            dependencies.update({
                'next-auth': '^4.22.1',
                'bcryptjs': '^2.4.3',
                '@types/bcryptjs': '^2.4.2'
            })
            
        if 'database' in features:
            if 'mongodb' in text.lower():
                dependencies['mongoose'] = '^7.3.1'
            else:
                dependencies['@prisma/client'] = '^4.16.2'
                
        if 'real-time' in features:
            dependencies.update({
                'socket.io': '^4.7.0',
                'socket.io-client': '^4.7.0'
            })
            
        return dependencies
        
    def _detect_ai_requirements(self, text: str) -> Dict[str, bool]:
        """Detect AI-related requirements"""
        text = text.lower()
        
        return {
            'openai': bool(re.search(r'gpt|openai|chatgpt|dalle', text)),
            'tensorflow': bool(re.search(r'tensorflow|machine.?learning|ml', text)),
            'huggingface': bool(re.search(r'hugg\w*|transform\w*|bert|nlp', text)),
            'langchain': bool(re.search(r'langchain|llm|agent', text))
        }
        
    def _analyze_security_requirements(self, text: str) -> Dict[str, bool]:
        """Analyze security requirements"""
        text = text.lower()
        
        return {
            'authentication': bool(re.search(r'auth\w*|login|secure', text)),
            'authorization': bool(re.search(r'role|permission|access.?control', text)),
            'encryption': bool(re.search(r'encrypt|hash|secure', text)),
            'rate_limiting': bool(re.search(r'rate.?limit|throttle', text)),
            'csrf': bool(re.search(r'csrf|xsrf|cross.?site', text)),
            'helmet': bool(re.search(r'helmet|header|security.?header', text))
        }
        
    def _analyze_performance_requirements(self, text: str) -> Dict[str, bool]:
        """Analyze performance requirements"""
        text = text.lower()
        
        return {
            'ssr': bool(re.search(r'ssr|server.?side.?render', text)),
            'ssg': bool(re.search(r'ssg|static.?site|static.?generation', text)),
            'isr': bool(re.search(r'isr|incremental|static.?regen', text)),
            'caching': bool(re.search(r'cache|redis|memory', text)),
            'code_splitting': bool(re.search(r'code.?split|lazy|dynamic', text)),
            'image_optimization': bool(re.search(r'image|optimize|compress', text))
        }
        
    def _enhance_requirements(self, requirements: Dict):
        """Enhance requirements based on detected features"""
        features = requirements['features']
        
        # Add necessary security features
        if 'authentication' in features or 'payments' in features:
            requirements['security'] = self._analyze_security_requirements('auth secure csrf')
            
        # Add performance optimizations for specific project types
        if requirements['project_type'] in ['next.js', 'static-site']:
            requirements['performance'] = self._analyze_performance_requirements('ssr ssg image')
            
        # Add real-time features if needed
        if 'notifications' in features or 'chat' in features:
            features.append('real-time')
            
        # Ensure proper styling for component-heavy projects
        if len(requirements['components']) > 5:
            requirements['styling']['tailwind'] = True 