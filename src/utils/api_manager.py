from typing import List, Dict, Optional
from .api_integrations import GitHubIntegration, RapidAPIIntegration, OpenAPIIntegration

class APIManager:
    """Manages and coordinates API integrations."""
    
    def __init__(self):
        self.github = GitHubIntegration()
        self.rapid_api = RapidAPIIntegration()
        self.openapi = OpenAPIIntegration()

    async def enhance_project_structure(self, description: str, features: Dict) -> Dict:
        """Enhance project structure with API integrations."""
        enhancements = {
            'dependencies': {},
            'apis': [],
            'code_patterns': [],
            'integrations': []
        }

        # Search for relevant code patterns
        patterns = await self.github.search_code_patterns(
            f"react {' '.join(features.keys())}"
        )
        enhancements['code_patterns'] = patterns

        # Find relevant npm packages
        packages = await self.rapid_api.search_npm_packages(
            f"react {' '.join(features.keys())}"
        )
        enhancements['dependencies'].update(
            {pkg['name']: pkg['version'] for pkg in packages[:5]}
        )

        # Discover relevant APIs
        apis = await self.openapi.fetch_api_specs()
        relevant_apis = self._filter_relevant_apis(apis, features)
        enhancements['apis'] = relevant_apis

        return enhancements

    def _filter_relevant_apis(self, apis: Dict, features: Dict) -> List[Dict]:
        """Filter APIs based on project features."""
        relevant = []
        feature_keywords = set(features.keys())
        
        for api_name, api_info in apis.items():
            api_keywords = set(api_info.get('keywords', []))
            if api_keywords & feature_keywords:
                relevant.append({
                    'name': api_name,
                    'info': api_info
                })
        
        return relevant[:5]  # Return top 5 most relevant APIs 