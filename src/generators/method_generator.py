from typing import Dict, List, Any
import logging
from pathlib import Path
from src.utils.pattern_matcher import PatternMatcher
from src.utils.data_scraper import DataScraper

logger = logging.getLogger(__name__)

class MethodGenerator:
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
        self.scraper = DataScraper()
        self.templates_dir = Path('src/templates')
        
    async def generate_method(self, method_name: str, class_context: Dict) -> str:
        """Generate missing method implementation"""
        # Extract pattern from method name and context
        pattern = await self.pattern_matcher.match_pattern(method_name)
        
        if pattern:
            return await self._generate_from_pattern(pattern, class_context)
        
        # If no pattern found, search and learn
        implementations = await self.scraper.search_implementations(
            self._extract_type(method_name),
            self._extract_keywords(method_name)
        )
        
        if implementations:
            new_pattern = self.pattern_matcher._analyze_implementations(
                implementations, method_name
            )
            await self.pattern_matcher._save_pattern(new_pattern)
            return await self._generate_from_pattern(new_pattern, class_context)
        
        # Fallback to basic implementation
        return await self._generate_basic_method(method_name)

    async def _generate_from_pattern(self, pattern: Dict, context: Dict) -> str:
        """Generate implementation from matched pattern"""
        template_path = self.templates_dir / pattern['template_path']
        
        if template_path.exists():
            template = template_path.read_text()
            return self._fill_template(template, pattern, context)
        
        # Generate from pattern directly
        return self._generate_from_structure(pattern, context)

    async def _generate_basic_method(self, method_name: str) -> str:
        """Generate a basic method implementation based on the method name"""
        # Extract verb and subject from method name
        words = method_name.split('_')
        verb = words[0].lower()
        subject = '_'.join(words[1:]) if len(words) > 1 else ''
        
        # Common verb patterns
        if verb in ['get', 'fetch', 'retrieve']:
            return f"""
    def {method_name}(self) -> Any:
        \"\"\"Get the {subject.replace('_', ' ')}\"\"\"
        # TODO: Implement {method_name}
        return None"""
            
        elif verb in ['set', 'update', 'modify']:
            return f"""
    def {method_name}(self, value: Any) -> None:
        \"\"\"Set the {subject.replace('_', ' ')}\"\"\"
        # TODO: Implement {method_name}
        self._{subject} = value"""
            
        elif verb in ['create', 'add', 'insert']:
            return f"""
    def {method_name}(self, data: Dict[str, Any]) -> Any:
        \"\"\"Create a new {subject.replace('_', ' ')}\"\"\"
        # TODO: Implement {method_name}
        return None"""
            
        elif verb in ['delete', 'remove']:
            return f"""
    def {method_name}(self, id: str) -> bool:
        \"\"\"Delete the specified {subject.replace('_', ' ')}\"\"\"
        # TODO: Implement {method_name}
        return True"""
            
        # Default implementation
        return f"""
    def {method_name}(self) -> None:
        \"\"\"Implementation for {method_name}\"\"\"
        # TODO: Implement {method_name}
        pass"""

    def _extract_type(self, method_name: str) -> str:
        """Extract the type/category of the method from its name"""
        # Common prefixes that indicate method type
        type_prefixes = {
            'get': 'getter',
            'set': 'setter',
            'create': 'creator',
            'delete': 'deletion',
            'update': 'updater',
            'validate': 'validation',
            'convert': 'conversion',
            'parse': 'parser',
            'format': 'formatter',
            'calculate': 'calculation',
            'process': 'processor',
            'handle': 'handler'
        }
        
        # Check for type prefix
        for prefix, type_name in type_prefixes.items():
            if method_name.lower().startswith(prefix):
                return type_name
                
        # Check for common patterns
        if '_to_' in method_name:
            return 'converter'
        if 'is_' in method_name or 'has_' in method_name:
            return 'predicate'
        if '_callback' in method_name:
            return 'callback'
            
        return 'general'

    def _extract_keywords(self, method_name: str) -> List[str]:
        """Extract relevant keywords from the method name"""
        # Split the method name into words
        words = method_name.split('_')
        keywords = []
        
        # Common words to filter out
        stop_words = {'get', 'set', 'create', 'delete', 'update', 'the', 'and', 'or', 'to', 'from', 'by', 'with'}
        
        # Process each word
        for word in words:
            word = word.lower()
            if word not in stop_words:
                # Add the word itself
                keywords.append(word)
                
                # Add related terms (you could expand this with a proper thesaurus)
                if word in ['user', 'users']:
                    keywords.extend(['account', 'profile'])
                elif word in ['file', 'files']:
                    keywords.extend(['document', 'storage'])
                elif word in ['data']:
                    keywords.extend(['information', 'content'])
                    
        return list(set(keywords))  # Remove duplicates

    def _fill_template(self, template: str, pattern: Dict, context: Dict) -> str:
        """Fill a template with pattern and context values"""
        # Replace pattern placeholders
        for key, value in pattern.items():
            if isinstance(value, str):
                placeholder = f"{{pattern.{key}}}"
                template = template.replace(placeholder, value)
                
        # Replace context placeholders
        for key, value in context.items():
            if isinstance(value, str):
                placeholder = f"{{context.{key}}}"
                template = template.replace(placeholder, value)
                
            elif isinstance(value, dict):
                # Handle nested context
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, str):
                        placeholder = f"{{context.{key}.{nested_key}}}"
                        template = template.replace(placeholder, nested_value)
                        
        return template

    def _generate_from_structure(self, pattern: Dict, context: Dict) -> str:
        """Generate method implementation from pattern structure"""
        method_name = pattern.get('name', '')
        params = pattern.get('params', [])
        return_type = pattern.get('return_type', 'Any')
        body = pattern.get('body', [])
        
        # Generate method signature
        params_str = ', '.join([f"{p['name']}: {p['type']}" for p in params])
        signature = f"def {method_name}(self{', ' + params_str if params else ''}) -> {return_type}:"
        
        # Generate docstring
        docstring = f'    """'
        if pattern.get('description'):
            docstring += f"\n    {pattern['description']}"
        for param in params:
            docstring += f"\n    Args:\n        {param['name']}: {param.get('description', '')}"
        if return_type != 'None':
            docstring += f"\n    Returns:\n        {return_type}: {pattern.get('return_description', '')}"
        docstring += '\n    """'
        
        # Generate method body
        body_lines = []
        for line in body:
            # Replace context variables
            for key, value in context.items():
                if isinstance(value, str):
                    line = line.replace(f"{{context.{key}}}", value)
            body_lines.append(f"    {line}")
            
        # Combine all parts
        return f"{signature}\n{docstring}\n" + "\n".join(body_lines) 