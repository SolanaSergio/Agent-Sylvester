import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import json
import re

logger = logging.getLogger(__name__)

class DataScraper:
    """Utility for scraping and analyzing implementation patterns"""
    
    def __init__(self):
        self.sources = {
            'github': 'https://api.github.com/search/code',
            'npm': 'https://registry.npmjs.org/-/v1/search',
            'mdn': 'https://developer.mozilla.org/api/v1/search',
            'stackoverflow': 'https://api.stackexchange.com/2.3/search'
        }
        
    async def search_implementations(self, pattern_type: str, keywords: List[str]) -> List[Dict]:
        """Search for implementation patterns across multiple sources"""
        results = []
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._search_github(session, pattern_type, keywords),
                self._search_npm(session, pattern_type, keywords),
                self._search_docs(session, pattern_type, keywords)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [r for r in results if not isinstance(r, Exception)]

    async def _search_github(self, session: aiohttp.ClientSession, 
                           pattern_type: str, keywords: List[str]) -> Dict:
        """Search GitHub for code implementations"""
        query = f"{pattern_type} {' '.join(keywords)} language:typescript language:javascript"
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': f'token {self._get_github_token()}'
        }
        
        try:
            async with session.get(
                self.sources['github'],
                params={'q': query, 'sort': 'stars'},
                headers=headers
            ) as response:
                if response.status == 403:
                    logger.warning("GitHub API rate limit exceeded")
                    return {}
                data = await response.json()
                return self._parse_github_results(data)
        except Exception as e:
            logger.error(f"GitHub search failed: {str(e)}")
            return {}

    async def _search_npm(self, session: aiohttp.ClientSession,
                         pattern_type: str, keywords: List[str]) -> Dict:
        """Search NPM for relevant packages and their implementations"""
        query = f"{pattern_type} {' '.join(keywords)}"
        
        try:
            async with session.get(
                self.sources['npm'],
                params={'text': query, 'size': 10}
            ) as response:
                data = await response.json()
                return self._parse_npm_results(data)
        except Exception as e:
            logger.error(f"NPM search failed: {str(e)}")
            return {}

    def _parse_github_results(self, data: Dict) -> Dict:
        """Parse and extract relevant patterns from GitHub results"""
        patterns = {}
        for item in data.get('items', []):
            try:
                if item.get('name', '').endswith(('.tsx', '.ts', '.jsx', '.js')):
                    patterns[item['name']] = {
                        'url': item['html_url'],
                        'path': item['path'],
                        'repo': item['repository']['full_name'],
                        'stars': item['repository'].get('stargazers_count', 0)
                    }
            except Exception as e:
                logger.warning(f"Failed to parse GitHub item: {str(e)}")
        return patterns

    def analyze_pattern(self, code: str, pattern_type: str) -> Dict:
        """Analyze code to extract implementation patterns"""
        analysis = {
            'imports': self._extract_imports(code),
            'interfaces': self._extract_interfaces(code),
            'methods': self._extract_methods(code),
            'hooks': self._extract_hooks(code),
            'state': self._extract_state_management(code)
        }
        return analysis

    def _extract_imports(self, code: str) -> List[str]:
        """Extract import statements"""
        import_pattern = r'import\s+{?\s*[\w\s,]+}?\s+from\s+[\'"][@\w\-\/]+[\'"]'
        return re.findall(import_pattern, code)

    def _extract_interfaces(self, code: str) -> List[str]:
        """Extract TypeScript interfaces"""
        interface_pattern = r'interface\s+\w+\s*{[^}]+}'
        return re.findall(interface_pattern, code)

    def _extract_methods(self, code: str) -> List[str]:
        """Extract method implementations"""
        method_pattern = r'(async\s+)?[\w]+\s*\([^)]*\)\s*{[^}]+}'
        return re.findall(method_pattern, code) 