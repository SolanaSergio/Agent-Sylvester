from typing import Dict, List, Optional
import json
from pathlib import Path
import logging
from difflib import SequenceMatcher
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

class PatternMatcher:
    def __init__(self):
        self.patterns_file = Path('src/data/patterns.json')
        self.patterns = self._load_patterns()
        self._ensure_nltk_data()
        
    def _ensure_nltk_data(self):
        """Ensure required NLTK data is downloaded"""
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')

    def _load_patterns(self) -> Dict:
        """Load patterns from file or create default"""
        if self.patterns_file.exists():
            with open(self.patterns_file, 'r') as f:
                return json.load(f)
        return self._create_default_patterns()

    async def match_pattern(self, description: str) -> Dict:
        """Match description to closest pattern or learn new one"""
        pattern = self._find_matching_pattern(description)
        
        if not pattern:
            pattern = self._check_pattern_cache(description)
            
            if not pattern:
                pattern = await self._learn_new_pattern(description)
                if pattern:
                    await self._save_pattern(pattern)
                else:
                    pattern = self._get_fallback_pattern(description)
        
        return pattern

    def _find_matching_pattern(self, description: str) -> Optional[Dict]:
        """Find the closest matching pattern"""
        keywords = self._extract_keywords(description)
        best_match = None
        best_score = 0

        for pattern_name, pattern in self.patterns.items():
            score = self._calculate_match_score(keywords, pattern['keywords'])
            if score > best_score and score > 0.6:  # Threshold for matching
                best_score = score
                best_match = pattern

        return best_match

    def _extract_keywords(self, description: str) -> List[str]:
        """Extract keywords from description"""
        stop_words = set(stopwords.words('english'))
        tokens = word_tokenize(description.lower())
        keywords = [word for word in tokens if word.isalnum() and word not in stop_words]
        return keywords

    def _calculate_match_score(self, keywords1: List[str], keywords2: List[str]) -> float:
        """Calculate similarity score between two sets of keywords"""
        if not keywords1 or not keywords2:
            return 0.0

        total_score = 0
        for word1 in keywords1:
            best_word_score = max(
                SequenceMatcher(None, word1, word2).ratio()
                for word2 in keywords2
            )
            total_score += best_word_score

        return total_score / len(keywords1)

    def _infer_pattern_type(self, description: str) -> str:
        """Infer the pattern type from description"""
        keywords = self._extract_keywords(description)
        
        type_indicators = {
            'component': ['component', 'ui', 'interface', 'view', 'display'],
            'hook': ['hook', 'use', 'state', 'effect', 'callback'],
            'context': ['context', 'provider', 'global', 'state', 'share'],
            'utility': ['utility', 'helper', 'function', 'tool', 'convert'],
            'api': ['api', 'endpoint', 'service', 'request', 'fetch']
        }
        
        best_type = 'utility'  # default type
        best_score = 0
        
        for pattern_type, indicators in type_indicators.items():
            score = self._calculate_match_score(keywords, indicators)
            if score > best_score:
                best_score = score
                best_type = pattern_type
        
        return best_type

    def _create_default_patterns(self) -> Dict:
        """Create default patterns"""
        return {
            'component': {
                'keywords': ['component', 'ui', 'render', 'display'],
                'required_methods': ['render'],
                'state_management': ['useState', 'useEffect'],
                'template_path': 'components/basic_component_template.tsx'
            },
            'hook': {
                'keywords': ['hook', 'state', 'effect', 'custom'],
                'required_methods': ['initialize', 'cleanup'],
                'state_management': ['useState'],
                'template_path': 'hooks/basic_hook_template.ts'
            },
            'context': {
                'keywords': ['context', 'provider', 'global', 'state'],
                'required_methods': ['provide', 'consume'],
                'state_management': ['createContext', 'useContext'],
                'template_path': 'contexts/basic_context_template.tsx'
            }
        }

    def _check_pattern_cache(self, description: str) -> Optional[Dict]:
        """Check for a cached pattern"""
        cache_file = Path('src/data/pattern_cache.json')
        if not cache_file.exists():
            return None
            
        with open(cache_file, 'r') as f:
            cache = json.load(f)
            
        keywords = self._extract_keywords(description)
        for pattern in cache.values():
            if self._calculate_match_score(keywords, pattern['keywords']) > 0.8:
                return pattern
                
        return None

    def _get_fallback_pattern(self, description: str) -> Dict:
        """Get a fallback basic pattern"""
        pattern_type = self._infer_pattern_type(description)
        keywords = self._extract_keywords(description)
        
        return {
            'type': pattern_type,
            'keywords': keywords,
            'required_methods': ['initialize', 'execute', 'cleanup'],
            'state_management': ['state', 'setState'],
            'template_path': f'{pattern_type}/basic_template.tsx'
        }

    async def _learn_new_pattern(self, description: str) -> Optional[Dict]:
        """Learn new implementation pattern from online sources"""
        keywords = self._extract_keywords(description)
        pattern_type = self._infer_pattern_type(description)
        
        # This would typically call the DataScraper to find implementations
        # For now, return None to use fallback pattern
        return None

    async def _save_pattern(self, pattern: Dict) -> None:
        """Save new pattern to patterns file"""
        self.patterns[pattern['type']] = pattern
        self.patterns_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.patterns_file, 'w') as f:
            json.dump(self.patterns, f, indent=2)