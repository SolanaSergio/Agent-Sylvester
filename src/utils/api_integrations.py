import aiohttp
import base64
from typing import List, Dict, Optional

class GitHubIntegration:
    """GitHub API integration for code pattern search and analysis."""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }

    async def search_code_patterns(self, query: str, language: str = "typescript") -> List[Dict]:
        """Search GitHub for code patterns matching query."""
        async with aiohttp.ClientSession() as session:
            search_url = f"{self.base_url}/search/code"
            params = {
                "q": f"{query} language:{language}",
                "per_page": 10
            }
            
            async with session.get(search_url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return await self._process_search_results(session, data['items'])
                return []

    async def _process_search_results(self, session: aiohttp.ClientSession, items: List[Dict]) -> List[Dict]:
        """Process and fetch actual content of found files."""
        processed_results = []
        
        for item in items:
            content = await self._fetch_file_content(session, item['url'])
            if content:
                processed_results.append({
                    'path': item['path'],
                    'url': item['html_url'],
                    'content': content
                })
                
        return processed_results

    async def _fetch_file_content(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """Fetch and decode file content."""
        async with session.get(url, headers=self.headers) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('content'):
                    return base64.b64decode(data['content']).decode('utf-8')
            return None

class RapidAPIIntegration:
    """Integration with various APIs through RapidAPI."""
    
    def __init__(self):
        self.headers = {
            "X-RapidAPI-Host": "RAPIDAPI_HOST",
            "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY"
        }

    async def search_npm_packages(self, query: str) -> List[Dict]:
        """Search for NPM packages and their details."""
        async with aiohttp.ClientSession() as session:
            url = "https://npm-registry-info.p.rapidapi.com/search"
            params = {"q": query}
            
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                return []

    async def get_package_details(self, package_name: str) -> Optional[Dict]:
        """Get detailed information about an NPM package."""
        async with aiohttp.ClientSession() as session:
            url = f"https://npm-registry-info.p.rapidapi.com/package/{package_name}"
            
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                return None

class OpenAPIIntegration:
    """Integration with OpenAPI specifications."""
    
    def __init__(self):
        self.api_directory_url = "https://api.apis.guru/v2/list.json"

    async def fetch_api_specs(self) -> Dict:
        """Fetch available API specifications."""
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_directory_url) as response:
                if response.status == 200:
                    return await response.json()
                return {}

    async def get_api_spec(self, api_name: str) -> Optional[Dict]:
        """Get OpenAPI specification for a specific API."""
        apis = await self.fetch_api_specs()
        if api_name in apis:
            spec_url = apis[api_name]['versions']['current']['swaggerUrl']
            async with aiohttp.ClientSession() as session:
                async with session.get(spec_url) as response:
                    if response.status == 200:
                        return await response.json()
        return None 